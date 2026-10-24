"""
ORION FastAPI Backend Server
Offline, Air-gapped Multi-Agent Industrial RAG Framework.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import (
    KNOWLEDGE_BASE_DIR,
    FRONTEND_DIR,
    AIR_GAPPED_MODE
)
from app.rag.vector_store import VectorStore
from app.rag.document_loader import DocumentLoader
from app.rag.chunker import IndustrialChunker
from app.llm_client import LocalLLMClient
from app.multimodal.audio_transcriber import AudioTranscriber
from app.multimodal.vision_analyzer import VisionAnalyzer
from app.agents.orchestrator import AgentOrchestrator
from app.feedback.feedback_manager import FeedbackManager

# Initialize Core Services
vector_store = VectorStore()
llm_client = LocalLLMClient()
chunker = IndustrialChunker()
audio_transcriber = AudioTranscriber()
vision_analyzer = VisionAnalyzer(llm_client)
orchestrator = AgentOrchestrator(vector_store, llm_client)
feedback_manager = FeedbackManager(vector_store)

def index_initial_documents():
    """Ensures knowledge base documents are chunked and indexed on startup."""
    stats = vector_store.get_stats()
    if stats["total_chunks"] == 0:
        print("[ORION-INIT] Initializing knowledge base indexing from data/knowledge_base/...")
        for file in KNOWLEDGE_BASE_DIR.glob("*.*"):
            if file.suffix.lower() in [".md", ".txt", ".json", ".csv", ".pdf"]:
                try:
                    text, meta = DocumentLoader.load_file(file)
                    chunks = chunker.chunk_document(text, meta)
                    vector_store.add_chunks(chunks)
                    print(f"[ORION-INIT] Indexed {len(chunks)} chunks from {file.name}")
                except Exception as e:
                    print(f"[ORION-INIT] Error indexing {file.name}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure documents are indexed
    index_initial_documents()
    yield
    # Shutdown

app = FastAPI(
    title="ORION Industrial Multi-Agent RAG",
    description="Offline, Air-Gapped Industrial Decision Support Framework",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local client development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request Models -----------------

class ChatRequest(BaseModel):
    query: Optional[str] = ""
    voice_transcript: Optional[str] = None
    equipment_id: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    query: str
    answer: str
    verdict: str  # 'confirmed', 'disputed', 'modified'
    technician_notes: str
    equipment_id: Optional[str] = "GEN-ASSET"
    technician_name: Optional[str] = "Field Technician"

# ----------------- API Endpoints -----------------

@app.get("/api/system/status")
def get_system_status():
    """Returns local system diagnostics, Ollama health, and Vector DB status."""
    llm_health = llm_client.check_health()
    vs_stats = vector_store.get_stats()
    return {
        "status": "OPERATIONAL",
        "air_gapped": AIR_GAPPED_MODE,
        "llm": llm_health,
        "vector_store": vs_stats
    }

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Processes technician text/voice query through the multi-agent orchestrator."""
    query_text = (req.query or "").strip()
    voice_text = (req.voice_transcript or "").strip()
    
    if not query_text and not voice_text:
        raise HTTPException(status_code=400, detail="Query or voice transcript must be provided.")

    meta_filter = req.metadata_filter or {}
    if req.equipment_id and req.equipment_id.strip() and req.equipment_id.strip() != "GEN-ASSET":
        meta_filter["equipment_type"] = req.equipment_id.strip()

    result = orchestrator.process_query(
        query=query_text,
        voice_transcript=voice_text,
        metadata_filter=meta_filter if meta_filter else None
    )
    return result

@app.post("/api/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """Transcribes technician speech audio using local Whisper STT."""
    contents = await audio_file.read()
    transcript = audio_transcriber.transcribe_audio_bytes(contents, filename=audio_file.filename)
    return {
        "status": "SUCCESS",
        "filename": audio_file.filename,
        "transcript": transcript
    }

@app.post("/api/vision/analyze")
async def analyze_vision(
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(None)
):
    """Analyzes equipment photo or gauge reading using local vision model/OCR."""
    image_bytes = await image.read()
    result = vision_analyzer.analyze_image(image_bytes, user_prompt=prompt or "")
    return result

@app.post("/api/multimodal/query")
async def multimodal_query(
    query: str = Form(...),
    voice_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    equipment_id: Optional[str] = Form(None)
):
    """Unified endpoint accepting text, voice audio, and equipment photos simultaneously."""
    voice_transcript = ""
    if voice_file:
        v_bytes = await voice_file.read()
        voice_transcript = audio_transcriber.transcribe_audio_bytes(v_bytes, filename=voice_file.filename)

    vision_data = None
    if image_file:
        i_bytes = await image_file.read()
        vision_data = vision_analyzer.analyze_image(i_bytes, user_prompt=query)

    meta_filter = {"equipment_type": equipment_id} if equipment_id else None

    result = orchestrator.process_query(
        query=query,
        voice_transcript=voice_transcript,
        vision_data=vision_data,
        metadata_filter=meta_filter
    )
    return result

@app.get("/api/documents")
def list_documents():
    """Lists indexed industrial SOPs, manuals, incident reports, and logs."""
    return vector_store.get_stats()

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads and indexes a new industrial document into the offline vector store."""
    dest_path = KNOWLEDGE_BASE_DIR / file.filename
    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    text, meta = DocumentLoader.load_file(dest_path)
    chunks = chunker.chunk_document(text, meta)
    indexed_count = vector_store.add_chunks(chunks)

    return {
        "status": "SUCCESS",
        "file_name": file.filename,
        "indexed_chunks": indexed_count,
        "message": f"Successfully ingested and indexed {file.filename} into ChromaDB."
    }

@app.post("/api/documents/reindex")
def reindex_all():
    """Wipes and re-indexes all documents in data/knowledge_base/."""
    vector_store.reset()
    indexed_files = []
    total_chunks = 0
    for file in KNOWLEDGE_BASE_DIR.glob("*.*"):
        if file.suffix.lower() in [".md", ".txt", ".json", ".csv", ".pdf"]:
            try:
                text, meta = DocumentLoader.load_file(file)
                chunks = chunker.chunk_document(text, meta)
                cnt = vector_store.add_chunks(chunks)
                total_chunks += cnt
                indexed_files.append({"file": file.name, "chunks": cnt})
            except Exception as e:
                print(f"Error indexing {file.name}: {e}")

    return {
        "status": "SUCCESS",
        "total_chunks_indexed": total_chunks,
        "files": indexed_files
    }

@app.post("/api/feedback")
def submit_feedback_endpoint(req: FeedbackRequest):
    """Captures technician field validation and automatically updates RAG knowledge."""
    res = feedback_manager.submit_feedback(
        query=req.query,
        answer=req.answer,
        verdict=req.verdict,
        technician_notes=req.technician_notes,
        equipment_id=req.equipment_id or "GEN-ASSET",
        technician_name=req.technician_name or "Field Technician"
    )
    return res

@app.get("/api/feedback")
def list_feedback_endpoint():
    """Retrieves all technician feedback records."""
    return {"feedback_records": feedback_manager.list_feedback()}

# Mount Static Frontend
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
