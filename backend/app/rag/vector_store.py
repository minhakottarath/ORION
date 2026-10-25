"""
Vector Store Engine
Provides ChromaDB persistent storage with an embedded SQLite vector fallback for 100% offline environments.
"""
import sqlite3
import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import CHROMADB_DIR, TOP_K_CHUNKS, SIMILARITY_THRESHOLD
from app.rag.embeddings import EmbeddingGenerator

class VectorStore:
    def __init__(self, persist_dir: Path = CHROMADB_DIR):
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedder = EmbeddingGenerator()
        
        self.chroma_client = None
        self.chroma_collection = None
        self._init_chromadb()
        
        # SQLite persistent fallback
        self.db_path = self.persist_dir / "vector_store.db"
        self._init_sqlite_db()

    def _init_chromadb(self):
        try:
            import chromadb
            from chromadb.config import Settings
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="orion_industrial_knowledge",
                metadata={"description": "Industrial SOPs, Manuals, and Incident Reports"}
            )
        except Exception:
            self.chroma_client = None
            self.chroma_collection = None

    def _init_sqlite_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    doc_id TEXT,
                    text TEXT,
                    metadata_json TEXT,
                    embedding_json TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON document_chunks(doc_id)")
            conn.commit()

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Adds or updates document chunks in both ChromaDB (if available) and SQLite.
        """
        if not chunks:
            return 0

        # Generate embeddings if not already attached
        for chunk in chunks:
            if "embedding" not in chunk:
                chunk["embedding"] = self.embedder.get_embedding(chunk["text"])

        # 1. ChromaDB Ingestion
        if self.chroma_collection:
            try:
                ids = [c["id"] for c in chunks]
                texts = [c["text"] for c in chunks]
                embeddings = [c["embedding"] for c in chunks]
                metadatas = [c["metadata"] for c in chunks]
                self.chroma_collection.upsert(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            except Exception:
                pass

        # 2. SQLite Ingestion
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                cursor.execute("""
                    INSERT OR REPLACE INTO document_chunks (id, doc_id, text, metadata_json, embedding_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    chunk["id"],
                    chunk["metadata"].get("doc_id", "DOC"),
                    chunk["text"],
                    json.dumps(chunk["metadata"]),
                    json.dumps(chunk["embedding"])
                ))
            conn.commit()

        return len(chunks)

    def query(
        self,
        query_text: str,
        top_k: int = TOP_K_CHUNKS,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant chunks for the query using hybrid cosine similarity and keyword matching.
        Applies a strict relevance threshold: only chunks meeting min_threshold are returned.
        """
        threshold = SIMILARITY_THRESHOLD if min_threshold is None else min_threshold
        query_text = (query_text or "").strip()
        if not query_text:
            return []

        query_emb = self.embedder.get_embedding(query_text)
        
        # 1. Try ChromaDB
        if self.chroma_collection:
            try:
                chroma_res = self.chroma_collection.query(
                    query_embeddings=[query_emb],
                    n_results=top_k * 2,
                    where=metadata_filter if metadata_filter else None
                )
                results = []
                if chroma_res and chroma_res["documents"] and len(chroma_res["documents"][0]) > 0:
                    for i in range(len(chroma_res["documents"][0])):
                        dist = chroma_res["distances"][0][i] if "distances" in chroma_res and chroma_res["distances"] else 0.5
                        sim = max(0.0, 1.0 - (dist / 2.0))
                        
                        doc_text = chroma_res["documents"][0][i]
                        # Keyword overlap boost
                        q_words = set(re.findall(r'\b[a-zA-Z0-9_\-]+\b', query_text.lower()))
                        t_words = set(re.findall(r'\b[a-zA-Z0-9_\-]+\b', doc_text.lower()))
                        overlap = len(q_words.intersection(t_words)) / max(1, len(q_words)) if q_words else 0
                        final_score = round(0.75 * sim + 0.25 * overlap, 3)

                        if final_score >= threshold:
                            results.append({
                                "id": chroma_res["ids"][0][i],
                                "text": doc_text,
                                "metadata": chroma_res["metadatas"][0][i],
                                "similarity_score": final_score
                            })
                    results.sort(key=lambda x: x["similarity_score"], reverse=True)
                    return results[:top_k]
            except Exception:
                pass

        # 2. SQLite Cosine Similarity Search
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, text, metadata_json, embedding_json FROM document_chunks")
            rows = cursor.fetchall()

        if not rows:
            return []

        scored_chunks = []
        q_words = set(re.findall(r'\b[a-zA-Z0-9_\-]+\b', query_text.lower()))

        for row_id, text, meta_str, emb_str in rows:
            meta = json.loads(meta_str)
            
            # Apply metadata filter if provided
            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if not v or v == "GEN-ASSET":
                        continue
                    val = str(meta.get(k, "")).lower()
                    target = str(v).lower()
                    alt_key = "equipment_id" if k == "equipment_type" else "equipment_type"
                    alt_val = str(meta.get(alt_key, "")).lower()
                    
                    if target not in val and val not in target and target not in alt_val and alt_val not in target:
                        match = False
                        break
                if not match:
                    continue

            emb = json.loads(emb_str)
            sim = self._cosine_similarity(query_emb, emb)
            
            # Hybrid keyword overlap boost
            t_words = set(re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower()))
            overlap_ratio = len(q_words.intersection(t_words)) / max(1, len(q_words)) if q_words else 0
            
            # Exact technical code match bonus (e.g. PRV-12, ACC-1, T800, BFP-02B, 180 bar)
            code_matches = sum(1 for w in q_words if len(w) > 3 and ('-' in w or any(c.isdigit() for c in w)) and w in text.lower())
            code_bonus = min(0.15, code_matches * 0.05)

            final_score = round(min(1.0, 0.70 * sim + 0.30 * overlap_ratio + code_bonus), 3)

            # Strict relevance cutoff: Do not return irrelevant chunks
            if final_score >= threshold:
                scored_chunks.append({
                    "id": row_id,
                    "text": text,
                    "metadata": meta,
                    "similarity_score": final_score
                })

        # If metadata filter returned 0 results, retry without filter to check if evidence exists
        if not scored_chunks and metadata_filter:
            return self.query(query_text=query_text, top_k=top_k, metadata_filter=None, min_threshold=threshold)

        # Sort by similarity descending
        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:top_k]

    def reset(self):
        """Wipes all indexed chunks in both ChromaDB and SQLite."""
        if self.chroma_client and self.chroma_collection:
            try:
                self.chroma_client.delete_collection("orion_industrial_knowledge")
                self.chroma_collection = self.chroma_client.create_collection(
                    name="orion_industrial_knowledge",
                    metadata={"description": "Industrial SOPs, Manuals, and Incident Reports"}
                )
            except Exception:
                pass

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_chunks")
            conn.commit()

    def delete_document(self, doc_id: str) -> int:
        """Removes all chunks associated with a document ID."""
        if self.chroma_collection:
            try:
                self.chroma_collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_chunks WHERE doc_id = ?", (doc_id,))
            deleted = cursor.rowcount
            conn.commit()
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        """Returns knowledge base indexing statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT doc_id) FROM document_chunks")
            total_chunks, total_docs = cursor.fetchone()
            
            cursor.execute("SELECT DISTINCT doc_id, metadata_json FROM document_chunks GROUP BY doc_id")
            docs_info = []
            for doc_id, meta_json in cursor.fetchall():
                meta = json.loads(meta_json)
                docs_info.append({
                    "doc_id": doc_id,
                    "title": meta.get("title", doc_id),
                    "file_name": meta.get("file_name", "unknown"),
                    "source_type": meta.get("source_type", "Document"),
                    "equipment_type": meta.get("equipment_type", "General")
                })

        return {
            "total_chunks": total_chunks,
            "total_documents": total_docs,
            "documents": docs_info,
            "engine": "ChromaDB + SQLite Fallback" if self.chroma_collection else "SQLite Local Embedded Vector Store"
        }

    def check_dimension_compatibility(self) -> bool:
        """Checks if stored embeddings match current embedding model dimension."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT embedding_json FROM document_chunks LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return True
            try:
                stored_emb = json.loads(row[0])
                test_emb = self.embedder.get_embedding("dimension check")
                return len(stored_emb) == len(test_emb)
            except Exception:
                return True

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a < 1e-9 or norm_b < 1e-9:
            return 0.0
        return dot / (norm_a * norm_b)
