"""
ORION System Configuration
Fully offline, air-gapped industrial decision support configuration.
"""
import os
from pathlib import Path

# Base Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
FEEDBACK_DIR = DATA_DIR / "feedback_records"
CHROMADB_DIR = DATA_DIR / "chromadb"
MODELS_DIR = DATA_DIR / "models"
VOSK_MODEL_DIR = MODELS_DIR / "vosk-model-small-en-us-0.15"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Offline & Edge Execution
AIR_GAPPED_MODE = True
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "tinyllama")
DEFAULT_VISION_MODEL = os.getenv("DEFAULT_VISION_MODEL", "llama3.2-vision")
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "all-minilm")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# Retrieval & Thresholds
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "4"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.30"))  # Minimum cosine similarity for relevance
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "400"))  # Words/tokens per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "60"))

# Server config
HOST = "0.0.0.0"
PORT = 8000
