"""
Agent Orchestrator
Coordinates multi-agent RAG workflow across Retrieval, Reasoning, and Verification agents.
"""
import time
from typing import Dict, Any, Optional

from app.rag.vector_store import VectorStore
from app.llm_client import LocalLLMClient
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.verification_agent import VerificationAgent

class AgentOrchestrator:
    def __init__(self, vector_store: VectorStore, llm_client: LocalLLMClient):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.retrieval_agent = RetrievalAgent(vector_store)
        self.reasoning_agent = ReasoningAgent(llm_client)
        self.verification_agent = VerificationAgent(llm_client)

    def process_query(
        self,
        query: str,
        voice_transcript: Optional[str] = None,
        vision_data: Optional[Dict[str, Any]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_similarity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes the full offline multi-agent industrial pipeline.
        Returns final verified answer, sources, evidence, and step-by-step agent telemetry.
        """
        start_time = time.time()
        agent_steps = []

        # 0. Multimodal Ingestion & Query Synthesis
        effective_query = query.strip()
        if voice_transcript and voice_transcript.strip():
            if not effective_query:
                effective_query = voice_transcript.strip()
            else:
                effective_query = f"{effective_query} (Voice note: {voice_transcript.strip()})"

        vision_summary = ""
        if vision_data and vision_data.get("detected"):
            vision_summary = vision_data.get("analysis_text", "")
            agent_steps.append({
                "agent": "Vision / OCR Preprocessor",
                "status": "COMPLETED",
                "summary": f"Analyzed image input ({vision_data.get('image_size_kb', 0)} KB). Visual features extracted.",
                "details": vision_summary
            })

        # 1. Retrieval Agent Step
        retrieval_start = time.time()
        retrieval_res = self.retrieval_agent.retrieve(
            query=effective_query,
            top_k=4,
            metadata_filter=metadata_filter,
            min_similarity=min_similarity
        )
        retrieval_duration = round((time.time() - retrieval_start) * 1000, 1)

        chunks_found = retrieval_res.get("chunks", [])
        retrieval_status = retrieval_res.get("status", "COMPLETED")

        agent_steps.append({
            "agent": "Retrieval Agent",
            "status": retrieval_status,
            "latency_ms": retrieval_duration,
            "summary": (
                f"Retrieved {len(chunks_found)} relevant industrial chunks from vector store."
                if len(chunks_found) > 0
                else "No relevant industrial documentation matched above similarity threshold."
            ),
            "sources_found": [s["title"] for s in retrieval_res.get("sources", [])]
        })

        # 2. Reasoning Agent Step
        reasoning_start = time.time()
        reasoning_res = self.reasoning_agent.reason(
            query=effective_query,
            retrieved_chunks=chunks_found,
            vision_summary=vision_summary
        )
        reasoning_duration = round((time.time() - reasoning_start) * 1000, 1)

        agent_steps.append({
            "agent": "Reasoning Agent",
            "status": reasoning_res["status"],
            "latency_ms": reasoning_duration,
            "summary": (
                f"Evidence-grounded synthesis complete using {len(chunks_found)} chunks."
                if len(chunks_found) > 0
                else "Insufficient evidence: Refused to fabricate an unsupported answer."
            ),
            "chunks_synthesized": reasoning_res.get("context_chunks_used", 0)
        })

        # 3. Verification Agent Step
        verification_start = time.time()
        verification_res = self.verification_agent.verify(
            query=effective_query,
            reasoning_output=reasoning_res["reasoning_output"],
            retrieved_chunks=chunks_found
        )
        verification_duration = round((time.time() - verification_start) * 1000, 1)

        agent_steps.append({
            "agent": "Verification Agent",
            "status": verification_res["status"],
            "latency_ms": verification_duration,
            "summary": (
                f"Claim audit complete. Groundedness Score: {verification_res['groundedness_score']}% (Hallucination Risk: {verification_res['hallucination_risk']})."
                if len(chunks_found) > 0
                else "Audit confirmed: No unsupported claims presented."
            ),
            "audit_checks": verification_res["audit_checks"]
        })

        total_latency = round((time.time() - start_time) * 1000, 1)

        final_answer = reasoning_res["reasoning_output"]
        if verification_res.get("status") == "SECURITY_VIOLATION":
            final_answer = "⚠️ SECURITY INTERVENTION: The response was blocked due to an untrusted prompt injection attempt in retrieved document content."

        return {
            "query": effective_query,
            "verified_answer": final_answer,
            "sources": retrieval_res["sources"],
            "verification": verification_res,
            "agent_steps": agent_steps,
            "total_latency_ms": total_latency,
            "offline_mode": True
        }
