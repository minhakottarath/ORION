"""
Reasoning Agent
Synthesizes root-cause analyses, step-by-step troubleshooting, and safety protocols from retrieved context.
"""
from typing import List, Dict, Any
from app.llm_client import LocalLLMClient

REASONING_SYSTEM_PROMPT = """You are ORION Reasoning Agent, an expert industrial plant diagnostic system.
Your mission is to provide rigorous, actionable, and safety-compliant decision support to field technicians.

INSTRUCTIONS:
1. Base your diagnostic strictly on the provided RETRIEVED INDUSTRIAL CONTEXT.
2. Structure your response into 3 standard sections:
   - Root Cause Analysis (RCA): Explain physical failure mechanism.
   - Actionable Diagnostic Sequence: Numbered step-by-step actions with exact tool specs, tolerances, and part numbers.
   - Safety Precautions: OSHA/LOTO requirements and critical hazards.
3. Explicitly cite document IDs (e.g. [SOP-702], [MAN-T800], [INC-2024-88]).
4. Maintain a decisive, clear, and safety-first industrial tone.
"""

class ReasoningAgent:
    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client

    def reason(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        vision_summary: str = ""
    ) -> Dict[str, Any]:
        """
        Executes diagnostic reasoning using local LLM over retrieved industrial chunks.
        """
        # Format context for prompt
        context_blocks = []
        for i, chunk in enumerate(retrieved_chunks):
            meta = chunk.get("metadata", {})
            context_blocks.append(
                f"--- SOURCE [{meta.get('doc_id', 'DOC')}] {meta.get('title')} ({meta.get('section')}) ---\n"
                f"{chunk.get('text')}\n"
            )
        formatted_context = "\n".join(context_blocks)

        prompt = (
            f"TECHNICIAN QUERY:\n{query}\n\n"
        )
        if vision_summary:
            prompt += f"VISUAL / OCR OBSERVATIONS:\n{vision_summary}\n\n"

        prompt += (
            f"RETRIEVED INDUSTRIAL CONTEXT:\n{formatted_context}\n\n"
            f"Please synthesize your diagnostic reasoning now."
        )

        response_text = self.llm.generate(
            prompt=prompt,
            system_prompt=REASONING_SYSTEM_PROMPT,
            retrieved_chunks=retrieved_chunks
        )

        return {
            "status": "COMPLETED",
            "reasoning_output": response_text,
            "context_chunks_used": len(retrieved_chunks)
        }
