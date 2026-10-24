"""
Feedback Manager & Continuous Learning Engine
Captures technician field resolutions and incrementally re-indexes verified solutions into ChromaDB.
"""
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any

from app.config import FEEDBACK_DIR, KNOWLEDGE_BASE_DIR
from app.rag.chunker import IndustrialChunker
from app.rag.vector_store import VectorStore

class FeedbackManager:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.chunker = IndustrialChunker()
        self.feedback_dir = FEEDBACK_DIR
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def submit_feedback(
        self,
        query: str,
        answer: str,
        verdict: str,  # 'confirmed', 'disputed', 'modified'
        technician_notes: str,
        equipment_id: str = "GEN-ASSET",
        technician_name: str = "Field Technician"
    ) -> Dict[str, Any]:
        """
        Stores technician field feedback and triggers validated knowledge base update if approved.
        """
        feedback_id = f"FB-{uuid.uuid4().hex[:8].upper()}"
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        record = {
            "feedback_id": feedback_id,
            "timestamp": timestamp,
            "technician_name": technician_name,
            "equipment_id": equipment_id,
            "original_query": query,
            "original_answer": answer,
            "verdict": verdict,
            "technician_notes": technician_notes,
            "status": "VALIDATED" if verdict in ["confirmed", "modified"] else "PENDING_REVIEW"
        }

        file_path = self.feedback_dir / f"{feedback_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        # If resolution is validated, immediately update knowledge base & re-index
        reindexed_chunks = 0
        if record["status"] == "VALIDATED":
            reindexed_chunks = self._reindex_feedback_as_knowledge(record)

        return {
            "status": "SUCCESS",
            "feedback_id": feedback_id,
            "verdict": verdict,
            "knowledge_updated": reindexed_chunks > 0,
            "reindexed_chunks": reindexed_chunks,
            "message": f"Feedback {feedback_id} recorded. Knowledge base updated with {reindexed_chunks} new chunks."
        }

    def _reindex_feedback_as_knowledge(self, record: Dict[str, Any]) -> int:
        """
        Converts validated technician feedback into a high-priority RAG knowledge chunk.
        """
        doc_id = f"VAL-{record['feedback_id']}"
        notes = record.get("technician_notes", "").strip() or "Standard diagnostic confirmed by technician."
        
        content = (
            f"# Field-Validated Resolution: {record.get('equipment_id', 'Asset')}\n"
            f"**Validation Source:** Lead Technician Field Resolution ({record.get('technician_name')})\n"
            f"**Verified Date:** {record.get('timestamp')}\n"
            f"**Equipment ID:** {record.get('equipment_id')}\n\n"
            f"## Issue Observed\n{record.get('original_query')}\n\n"
            f"## Verified Field Corrective Action\n{notes}\n\n"
            f"## Status\nField tested and confirmed operational."
        )

        metadata = {
            "doc_id": doc_id,
            "title": f"Field-Validated Resolution ({record.get('equipment_id')})",
            "file_name": f"{record['feedback_id']}.md",
            "source_type": "Validated Technician Feedback",
            "equipment_type": record.get("equipment_id", "General Asset"),
            "safety_level": "Field-Verified"
        }

        chunks = self.chunker.chunk_document(content, metadata)
        return self.vector_store.add_chunks(chunks)

    def list_feedback(self) -> List[Dict[str, Any]]:
        """Returns all recorded feedback entries."""
        records = []
        for file in sorted(self.feedback_dir.glob("*.json"), reverse=True):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    records.append(json.load(f))
            except Exception:
                pass
        return records
