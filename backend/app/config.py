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
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

# Offline & Edge Execution
AIR_GAPPED_MODE = True
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "llama3.2:1b")
DEFAULT_VISION_MODEL = os.getenv("DEFAULT_VISION_MODEL", "llama3.2-vision")
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "nomic-embed-text:latest")

# Retrieval & Thresholds
TOP_K_CHUNKS = 4
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.32"))  # Calibrated relevance threshold for evidence
MAX_CHUNK_SIZE = 600  # Words/tokens per chunk
CHUNK_OVERLAP = 100

# Standardized Groundedness Messages
INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I could not find sufficient supporting information in the local knowledge base "
    "to answer this question reliably."
)

# Server config
HOST = "0.0.0.0"
PORT = 8000
