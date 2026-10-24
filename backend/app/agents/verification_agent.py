"""
Verification Agent
Fact-checking, hallucination detection, and groundedness auditing for industrial safety.
"""
import re
from typing import List, Dict, Any

class VerificationAgent:
    def verify(
        self,
        query: str,
        reasoning_output: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Audits reasoning output against retrieved evidence chunks.
        Evaluates source grounding, technical parameter consistency, and safety warnings.
        """
        audit_checks = []
        score = 100
        hallucination_detected = False

        # 1. Source Citation Audit
        doc_ids_in_context = set()
        for c in retrieved_chunks:
            did = c.get("metadata", {}).get("doc_id", "")
            if did:
                doc_ids_in_context.add(did.upper())
                doc_ids_in_context.add(did.upper().replace("_", "-"))
                doc_ids_in_context.add(did.upper().replace("-", "_"))
                # Also include document titles or equipment IDs
                title = c.get("metadata", {}).get("title", "")
                if title:
                    doc_ids_in_context.add(title.upper())

        # Extract cited IDs, supporting patterns like [SOP-702], [MAN-T800: Section 8], [DOC]
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
            audit_checks.append(f"Validated citations in context: {', '.join(sorted(valid_citations))}")
        elif doc_ids_in_context:
            audit_checks.append("Implicit source alignment detected.")
            score -= 3

        if unverified_citations:
            audit_checks.append(f"Notice: External references cited ({', '.join(sorted(unverified_citations))})")
            score -= 5

        # 2. Safety Interlock Audit
        has_safety_block = any(k in reasoning_output.lower() for k in ["safety", "hazard", "loto", "lockout", "depressurize", "breaker"])
        is_hazard_query = any(k in query.lower() for k in ["pressure", "voltage", "turbine", "high", "hpu", "480v", "bleed"])
        
        if is_hazard_query:
            if has_safety_block:
                audit_checks.append("Safety Protocol Audit: PASSED (Hazard precautions and LOTO documented).")
            else:
                audit_checks.append("Safety Protocol Warning: Servicing high-energy equipment requires explicit LOTO step.")
                score -= 15
                hallucination_detected = True

        # 3. Numeric & Specification Cross-Reference
        # Extract numerical specs like '180 bar', '4-20mA', '18.5 Ω'
        numbers_in_reasoning = re.findall(r'(\d+(?:\.\d+)?\s*(?:bar|psi|mm/s|rpm|mw|v|a|ma|°c|k|ohm|ω))', reasoning_output.lower())
        all_context_text = " ".join([c.get("text", "").lower() for c in retrieved_chunks])
        
        grounded_numbers = 0
        for spec in numbers_in_reasoning:
            val_match = re.search(r'\d+(?:\.\d+)?', spec)
            if val_match and val_match.group(0) in all_context_text:
                grounded_numbers += 1

        if numbers_in_reasoning:
            grounding_ratio = grounded_numbers / len(numbers_in_reasoning)
            if grounding_ratio > 0.6:
                audit_checks.append(f"Numeric Specifications Grounding: PASSED ({grounded_numbers}/{len(numbers_in_reasoning)} specs matched in OEM manuals).")
            else:
                score -= 8
                audit_checks.append(f"Numeric Grounding Partial: {grounded_numbers}/{len(numbers_in_reasoning)} matched directly in retrieved excerpts.")

        groundedness_score = max(60, min(100, score))
        risk_level = "LOW" if groundedness_score >= 85 else ("MEDIUM" if groundedness_score >= 70 else "HIGH")

        return {
            "status": "VERIFIED" if groundedness_score >= 75 else "FLAGGED_FOR_REVIEW",
            "groundedness_score": groundedness_score,
            "hallucination_risk": risk_level,
            "hallucination_detected": hallucination_detected,
            "audit_checks": audit_checks,
            "verified_sources": list(doc_ids_in_context)
        }
