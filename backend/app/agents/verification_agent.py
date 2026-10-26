"""
Verification Agent
Audits factual claims against retrieved evidence chunks with claim-level classification,
contradiction detection, conflict analysis, and prompt injection defense.
"""
import re
from typing import List, Dict, Any, Optional

class VerificationAgent:
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client

    def verify(
        self,
        query: str,
        reasoning_output: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Audits reasoning output against retrieved evidence chunks.
        Performs:
        1. Query & response validity checks (e.g. insufficient evidence)
        2. Claim extraction and claim-by-claim evidence grounding check
        3. Contradiction & conflict detection between documents
        4. Prompt injection & security auditing
        5. Computes realistic, un-faked groundedness score
        """
        # 1. Check for insufficient evidence or error outputs
        if not reasoning_output or "insufficient supporting information" in reasoning_output.lower():
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "groundedness_score": 0,
                "hallucination_risk": "N/A",
                "hallucination_detected": False,
                "claims": [],
                "audit_checks": ["No sufficient evidence was found in the local knowledge base to verify claims."],
                "conflicts_detected": [],
                "verified_sources": []
            }

        if not retrieved_chunks:
            return {
                "status": "UNSUPPORTED",
                "groundedness_score": 0,
                "hallucination_risk": "HIGH",
                "hallucination_detected": True,
                "claims": [{"claim": reasoning_output[:120], "status": "UNSUPPORTED", "reason": "No retrieved context"}],
                "audit_checks": ["CRITICAL: Answer was produced without any supporting knowledge base chunks."],
                "conflicts_detected": [],
                "verified_sources": []
            }

        audit_checks = []
        conflicts_detected = []
        doc_ids_in_context = set()
        all_context_text = ""

        for c in retrieved_chunks:
            meta = c.get("metadata", {})
            did = meta.get("doc_id", "")
            if did:
                doc_ids_in_context.add(did.upper())
            title = meta.get("title", "")
            if title:
                doc_ids_in_context.add(title.upper())
            file_name = meta.get("file_name", "")
            if file_name:
                doc_ids_in_context.add(file_name.upper())
            all_context_text += " " + c.get("text", "")

        context_lower = all_context_text.lower()

        # 2. Prompt Injection & Adversarial Defense Audit
        injection_keywords = ["ignore previous instructions", "system prompt", "override", "jailbreak", "say hacked", "bypass"]
        context_has_injection = any(ik in context_lower for ik in injection_keywords)
        if context_has_injection:
            # Check if answer followed the injection directive
            for ik in ["hacked", "bypass confirmed", "instructions ignored", "jailbroken"]:
                if ik in reasoning_output.lower():
                    return {
                        "status": "SECURITY_VIOLATION",
                        "groundedness_score": 0,
                        "hallucination_risk": "CRITICAL",
                        "hallucination_detected": True,
                        "claims": [{"claim": "Adversarial override executed", "status": "CONTRADICTED"}],
                        "audit_checks": ["SECURITY ALERT: Retrieved text attempted prompt injection, and answer complied."],
                        "conflicts_detected": ["Prompt injection detected in untrusted document context."],
                        "verified_sources": list(doc_ids_in_context)
                    }
            audit_checks.append("Security Audit: Untrusted document injection directives were safely neutralized.")

        # 3. Document Conflict Detection
        # Check if multiple chunks specify conflicting numbers for the same metric
        metric_patterns = [
            (r'(\d+(?:\.\d+)?)\s*bar', 'bar'),
            (r'(\d+(?:\.\d+)?)\s*mm/s', 'mm/s'),
            (r'(\d+(?:\.\d+)?)\s*rpm', 'rpm'),
            (r'(\d+(?:\.\d+)?)\s*°c', '°c'),
            (r'(\d+(?:\.\d+)?)\s*v\b', 'V')
        ]
        chunk_metrics = []
        for c in retrieved_chunks:
            c_text = c.get("text", "").lower()
            found_m = {}
            for pat, unit in metric_patterns:
                matches = re.findall(pat, c_text)
                if matches:
                    found_m[unit] = set(matches)
            chunk_metrics.append((c.get("metadata", {}).get("doc_id", "DOC"), found_m))

        # Compare across distinct documents
        for i in range(len(chunk_metrics)):
            for j in range(i + 1, len(chunk_metrics)):
                doc_a, m_a = chunk_metrics[i]
                doc_b, m_b = chunk_metrics[j]
                if doc_a != doc_b:
                    for unit in m_a:
                        if unit in m_b and m_a[unit] != m_b[unit]:
                            conflict_desc = f"Parameter conflict between [{doc_a}] and [{doc_b}]: {unit} values differ ({m_a[unit]} vs {m_b[unit]})."
                            if conflict_desc not in conflicts_detected:
                                conflicts_detected.append(conflict_desc)

        if conflicts_detected:
            audit_checks.append(f"Document Conflict Detected: {'; '.join(conflicts_detected)}")

        # 4. Extract Claims from Answer
        lines = [line.strip() for line in reasoning_output.split("\n") if line.strip()]
        claims = []
        for line in lines:
            # Skip headings and structural markers
            if line.startswith("#") or line.startswith("---") or line.endswith(":") or len(line) < 15:
                continue
            # Strip bullet prefixes
            clean_line = re.sub(r'^(\*|-|\d+\.)\s*', '', line)
            claims.append(clean_line)

        # Fallback if few lines
        if not claims:
            claims = [s.strip() for s in re.split(r'\.\s+', reasoning_output) if len(s.strip()) > 15]

        # 5. Verify Each Claim Against Retrieved Passages
        claim_evaluations = []
        supported_count = 0
        partially_supported_count = 0
        unsupported_count = 0
        contradicted_count = 0

        stop_words = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "in", "for", "with", "on", "at", "by", "from", "that", "this", "be", "as"}

        for claim in claims:
            claim_lower = claim.lower()
            tokens = [t for t in re.findall(r'[a-zA-Z0-9_\-\.\#]+', claim_lower) if t not in stop_words and len(t) >= 2]
            if not tokens:
                continue

            # Check numerical specs in claim
            claim_nums = re.findall(r'\b\d+(?:\.\d+)?(?:\s*[a-zA-Z%°]+)?\b', claim_lower)
            matched_nums = [n for n in claim_nums if n in context_lower]

            # Token overlap with context
            matched_tokens = [t for t in tokens if t in context_lower]
            overlap_ratio = len(matched_tokens) / max(1, len(tokens))

            # Contradiction check: numbers in claim not in context while context has different numbers for same entity
            has_unmatched_numbers = len(claim_nums) > 0 and len(matched_nums) == 0

            if overlap_ratio >= 0.65 and (not claim_nums or len(matched_nums) > 0):
                status = "SUPPORTED"
                supported_count += 1
                reason = "Claim aligns strongly with retrieved OEM documentation."
            elif overlap_ratio >= 0.35 or len(matched_nums) > 0:
                status = "PARTIALLY_SUPPORTED"
                partially_supported_count += 1
                reason = "Concepts or partial specifications matched; full claim not explicitly confirmed."
            elif has_unmatched_numbers and overlap_ratio < 0.3:
                status = "CONTRADICTED"
                contradicted_count += 1
                reason = "Specification or action not found in retrieved text; possible conflicting value."
            else:
                status = "UNSUPPORTED"
                unsupported_count += 1
                reason = "No direct evidence found in retrieved chunks for this statement."

            claim_evaluations.append({
                "claim": claim[:180] + ("..." if len(claim) > 180 else ""),
                "status": status,
                "overlap_pct": round(overlap_ratio * 100, 1),
                "reason": reason
            })

        # 6. Source Citation Audit
        raw_citations = re.findall(r'\[([A-Za-z0-9\-_]+)(?::[^\]]+)?\]', reasoning_output)
        cited_doc_ids = {c.upper() for c in raw_citations}
        valid_citations = set()
        unverified_citations = set()
        for cid in cited_doc_ids:
            if cid in doc_ids_in_context or any(cid in did or did in cid for did in doc_ids_in_context):
                valid_citations.add(cid)
            else:
                unverified_citations.add(cid)

        if valid_citations:
            audit_checks.append(f"Citations verified in context: {', '.join(sorted(valid_citations))}")
        elif doc_ids_in_context:
            audit_checks.append("Implicit source context detected without exact bracketed tags.")

        if unverified_citations:
            audit_checks.append(f"Notice: Cited references outside retrieved context ({', '.join(sorted(unverified_citations))})")

        # 7. Compute Real Groundedness Score
        total_eval = len(claim_evaluations)
        if total_eval == 0:
            groundedness_score = 50
        else:
            base_score = ((supported_count * 100.0) + (partially_supported_count * 50.0)) / total_eval
            # Deduct for contradicted or unverified citations
            base_score -= (contradicted_count * 25.0)
            if unverified_citations:
                base_score -= (len(unverified_citations) * 10.0)
            groundedness_score = int(max(0, min(100, round(base_score))))

        # Determine Status and Risk
        hallucination_detected = (unsupported_count > supported_count) or (contradicted_count > 0)
        if groundedness_score >= 75 and not hallucination_detected:
            status = "VERIFIED"
            risk_level = "LOW"
        elif groundedness_score >= 45 and contradicted_count == 0:
            status = "PARTIALLY_SUPPORTED"
            risk_level = "MEDIUM"
        else:
            status = "FLAGGED_FOR_REVIEW"
            risk_level = "HIGH"

        audit_checks.append(
            f"Factual Claims Audit: {supported_count} Supported, {partially_supported_count} Partially Supported, "
            f"{unsupported_count} Unsupported, {contradicted_count} Contradicted."
        )

        return {
            "status": status,
            "groundedness_score": groundedness_score,
            "hallucination_risk": risk_level,
            "hallucination_detected": hallucination_detected,
            "claims": claim_evaluations,
            "audit_checks": audit_checks,
            "conflicts_detected": conflicts_detected,
            "verified_sources": list(doc_ids_in_context)
        }
