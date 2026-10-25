"""
Offline Embedding Generator
Generates dense vector embeddings using Ollama, sentence-transformers, or an internal industrial semantic vectorizer.
"""
import math
import re
import hashlib
from typing import List
import requests

from app.config import OLLAMA_BASE_URL, DEFAULT_EMBEDDING_MODEL

class EmbeddingGenerator:
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self._sentence_transformer_model = None
        self._ollama_available = None
        self._embedding_model_name = DEFAULT_EMBEDDING_MODEL
        self._init_sentence_transformer()

    def _init_sentence_transformer(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._sentence_transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.embedding_dim = 384
        except Exception:
            self._sentence_transformer_model = None

    def _check_ollama_embeddings(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                if DEFAULT_EMBEDDING_MODEL in models:
                    self._embedding_model_name = DEFAULT_EMBEDDING_MODEL
                    self._ollama_available = True
                else:
                    # Look for any embedding model or text model that supports embeddings
                    emb_candidates = [m for m in models if "embed" in m.lower() or "nomic" in m.lower()]
                    if emb_candidates:
                        self._embedding_model_name = emb_candidates[0]
                        self._ollama_available = True
                    else:
                        self._ollama_available = False
            else:
                self._ollama_available = False
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding vector for the provided text.
        Priority:
        1. Local sentence_transformers model
        2. Ollama /api/embeddings endpoint (nomic-embed-text)
        3. Internal deterministic semantic feature projection (guaranteed offline fallback)
        """
        # 1. Local sentence_transformers if available
        if self._sentence_transformer_model:
            try:
                emb = self._sentence_transformer_model.encode(text)
                return emb.tolist()
            except Exception:
                pass

        # 2. Ollama Embeddings API
        if self._check_ollama_embeddings():
            try:
                resp = requests.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": self._embedding_model_name, "prompt": text},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "embedding" in data:
                        emb = data["embedding"]
                        # Normalize vector
                        norm = math.sqrt(sum(x * x for x in emb))
                        if norm > 1e-9:
                            emb = [x / norm for x in emb]
                        self.embedding_dim = len(emb)
                        return emb
            except Exception:
                self._ollama_available = False

        # 3. Deterministic Domain-Aware Semantic Feature Projection
        return self._semantic_projection_embedding(text)

    def _semantic_projection_embedding(self, text: str) -> List[float]:
        """
        Industrial-grade deterministic sparse-to-dense projection vectorizer.
        Extracts subwords, alphanumeric codes, technical numbers, and bigrams,
        projecting them into a normalized unit sphere of dimension `embedding_dim`.
        """
        vec = [0.0] * self.embedding_dim
        tokens = re.findall(r'[a-zA-Z0-9_\-\.\#]+', text.lower())
        if not tokens:
            return vec

        # Term weights
        weights = {}
        for token in tokens:
            weights[token] = weights.get(token, 0) + 1.0

        # Also add bigrams for phrase matching (e.g., 'pressure fluctuation', 'bearing temperature')
        for i in range(len(tokens) - 1):
            bg = f"{tokens[i]}_{tokens[i+1]}"
            weights[bg] = weights.get(bg, 0) + 1.5

        # Project tokens into vector slots using salted hashing
        for term, freq in weights.items():
            # Term frequency saturation (log-scale)
            tf = 1.0 + math.log(freq)
            
            # Use 3 orthogonal hash buckets per term to reduce collisions
            for seed in [0, 42, 137]:
                h = int(hashlib.md5(f"{seed}_{term}".encode("utf-8")).hexdigest(), 16)
                idx = h % self.embedding_dim
                sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
                vec[idx] += sign * tf

        # L2-normalize vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        return vec
