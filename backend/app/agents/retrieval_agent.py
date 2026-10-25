"""
Retrieval Agent
Specialized agent for searching, ranking, and synthesizing evidence from ChromaDB/heterogeneous docs.
"""
from typing import List, Dict, Any, Optional
from app.rag.vector_store import VectorStore
from app.config import TOP_K_CHUNKS

class RetrievalAgent:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K_CHUNKS,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes semantic retrieval across indexed industrial documentation.
        Returns retrieved chunks, source metadata, and execution metrics.
        """
        chunks = self.vector_store.query(
            query_text=query,
            top_k=top_k,
            metadata_filter=metadata_filter
        )

        sources = []
        for c in chunks:
            meta = c.get("metadata", {})
            sources.append({
                "chunk_id": c.get("id"),
                "doc_id": meta.get("doc_id", "DOC"),
                "file_name": meta.get("file_name", "unknown"),
                "title": meta.get("title", "Document"),
                "section": meta.get("section", "General"),
                "page": meta.get("page"),
                "equipment_type": meta.get("equipment_type", "Industrial Equipment"),
                "safety_level": meta.get("safety_level", "Standard"),
                "similarity_score": c.get("similarity_score", 0.0),
                "snippet": c.get("text", "")[:320] + "..."
            })

        has_adequate_evidence = len(chunks) > 0

        return {
            "status": "COMPLETED" if has_adequate_evidence else "NO_EVIDENCE_FOUND",
            "adequate_evidence": has_adequate_evidence,
            "query": query,
            "total_retrieved": len(chunks),
            "chunks": chunks,
            "sources": sources
        }
