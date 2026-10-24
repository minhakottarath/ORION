# ORION: Fully Offline Industrial Multi-Agent RAG Assistant

ORION is an air-gapped, privacy-preserving, and intelligent multi-agent Retrieval-Augmented Generation (RAG) framework designed for industrial decision support. It operates **100% offline** on edge hardware without external cloud dependencies, ensuring complete data sovereignty and operational security in mission-critical environments (e.g., power plants, manufacturing facilities, offshore platforms, and defense installations).

```
                    ┌───────────────────────────────┐
                    │          ORION USER           │
                    │       Technician / User       │
                    └───────────────┬───────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          ┌────────────┐     ┌────────────┐     ┌────────────┐
          │    Text    │     │   Voice    │     │   Image    │
          │   Input    │     │   Input    │     │   Input    │
          └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
                │                  │                  │
                │                  ▼                  ▼
                │            ┌────────────┐    ┌────────────┐
                │            │   Whisper  │    │ OCR/Vision │
                │            │    STT     │    │   Model    │
                │            └─────┬──────┘    └─────┬──────┘
                │                  │                  │
                └──────────────────┼──────────────────┘
                                   ▼
                     ┌─────────────────────────┐
                     │    Query Processing     │
                     │  & Agent Orchestrator   │
                     └────────────┬────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
        ┌────────────────┐ ┌───────────────┐ ┌────────────────┐
        │ Retrieval      │ │ Reasoning     │ │ Verification   │
        │ Agent          │ │ Agent         │ │ Agent          │
        └───────┬────────┘ └───────┬───────┘ └───────┬────────┘
                │                  │                 │
                └──────────────────┼─────────────────┘
                                   ▼
                       ┌───────────────────────┐
                       │     Local LLM         │
                       │      (Ollama)         │
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Verified Final Answer │
                       │ + Sources + Evidence  │
                       └───────────┬───────────┘
                                   │
                                   ▼
                            ┌────────────┐
                            │ Technician │
                            │ Feedback   │
                            └─────┬──────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Validated Update │
                         │  Knowledge Base  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Re-index / Update│
                         │     RAG DB       │
                         └──────────────────┘

        ─────────────── LOCAL / OFFLINE ENVIRONMENT ───────────────

        ┌─────────────────────────────────────────────────────────┐
        │                  INDUSTRIAL KNOWLEDGE BASE              │
        │                                                         │
        │  PDFs │ SOPs │ Manuals │ Incident Reports │ Logs       │
        │                                                         │
        └───────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Document         │
                       │ Processing       │
                       └────────┬─────────┘
                                ▼
                       ┌──────────────────┐
                       │ Embedding Model  │
                       └────────┬─────────┘
                                ▼
                       ┌──────────────────┐
                       │ Vector Database  │
                       │    ChromaDB      │
                       └──────────────────┘
```

---

## Key Features

1. **Multimodal Interaction**:
   - **Text**: Diagnostic queries, error code investigations, equipment status lookups.
   - **Voice (Whisper STT)**: Live microphone audio recording with HTML5 real-time waveform visualizer.
   - **Image (Vision/OCR)**: Drag-and-drop equipment photos, nameplates, analog gauge dials, or error screens.

2. **Specialized Multi-Agent Pipeline**:
   - **Retrieval Agent**: Hybrid semantic + keyword retrieval over industrial SOPs, equipment manuals, incident investigations, and telemetry logs with metadata filtering.
   - **Reasoning Agent**: Chain-of-thought Root Cause Analysis (RCA), step-by-step Standard Operating Procedure (SOP) instructions, and OSHA/LOTO safety hazard warnings.
   - **Verification Agent**: Groundedness audit, hallucination scoring, and cross-referencing of every claim and part number against OEM sources.

3. **Local LLM Engine (Ollama / Embedded)**:
   - Connects to local Ollama at `http://localhost:11434` (`llama3.2`, `mistral`, `llava`).
   - Includes a built-in Air-Gapped Industrial Diagnostic Engine so the entire platform runs immediately out of the box with zero external dependencies.

4. **Continuous Learning via Validated Technician Feedback**:
   - Technicians can sign off on field solutions, record what physical fix was applied, and immediately trigger incremental re-indexing into ChromaDB.
   - Newly logged solutions are immediately retrievable for future plant incidents.

5. **Industrial Operator Console**:
   - High-contrast, tactical cyber-industrial HUD with real-time multi-agent execution timeline, source citation drawers, and knowledge base document manager.

---

## Directory Structure

```
Main project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                 # Offline configuration & paths
│   │   ├── main.py                   # FastAPI application & REST endpoints
│   │   ├── llm_client.py             # Ollama API adapter + offline fallback
│   │   ├── mock_engine.py            # Grounded diagnostic engine fallback
│   │   ├── agents/
│   │   │   ├── orchestrator.py       # Multi-Agent State Machine
│   │   │   ├── retrieval_agent.py    # Vector store query & hybrid reranker
│   │   │   ├── reasoning_agent.py    # RCA & SOP diagnostic synthesizer
│   │   │   └── verification_agent.py # Hallucination auditor & citation verifier
│   │   ├── rag/
│   │   │   ├── chunker.py            # Industrial semantic chunker
│   │   │   ├── document_loader.py    # Heterogeneous file loader (MD, TXT, JSON, CSV, PDF)
│   │   │   ├── embeddings.py         # Offline embeddings (Ollama / projection)
│   │   │   └── vector_store.py       # ChromaDB + SQLite persistence
│   │   ├── multimodal/
│   │   │   ├── audio_transcriber.py  # Local Whisper STT handler
│   │   │   └── vision_analyzer.py    # Industrial vision & OCR analyzer
│   │   └── feedback/
│   │       └── feedback_manager.py   # Validated feedback queue & re-indexer
│   ├── data/
│   │   ├── knowledge_base/           # Ingested SOPs, manuals, incident reports, logs
│   │   │   ├── sop_hydraulic_system.md
│   │   │   ├── manual_turbine_generator_t800.md
│   │   │   ├── incident_report_pump_cavitation.md
│   │   │   └── logs_motor_telemetry_sample.json
│   │   ├── feedback_records/         # Field feedback records
│   │   └── chromadb/                 # Persistent vector store database
│   ├── test_system.py                # Self-contained verification suite
│   └── requirements.txt              # Python dependencies
├── frontend/
│   ├── index.html                    # Industrial Operator Console UI
│   ├── css/
│   │   └── style.css                 # Tactical dark-mode styling & HUD components
│   └── js/
│       ├── app.js                    # Master application logic & tabs
│       ├── audio_recorder.js         # Audio recording & waveform visualizer
│       ├── vision_handler.js         # Image dropzone & OCR inspector
│       └── agent_stream.js           # Multi-agent timeline & markdown renderer
└── README.md
```

---

## Quickstart Guide

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```
*(Note: If running on a minimal system without all packages, ORION automatically runs with its built-in SQLite vector store and offline diagnostic engine.)*

### 2. Run Self-Test & Verification Suite
To verify the vector store ingestion, semantic retrieval accuracy, multi-agent pipeline, and feedback re-indexing loop:
```bash
python backend/test_system.py
```

### 3. Launch ORION Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open the Operator Console
Open your web browser and navigate to:
```
http://localhost:8000
```

---

## Verification & Usage Flow

1. **Operator Console**:
   - Click one of the quick incident presets (e.g. **`SOP-702` HPU Pressure Fluctuation** or **`MAN-T800` Turbine Vibration Alert**).
   - Click **`DISPATCH MULTI-AGENT PIPELINE`**.
   - Watch the 3-stage agent timeline light up:
     1. **Retrieval Agent**: Searches ChromaDB and extracts matching SOP chunks.
     2. **Reasoning Agent**: Synthesizes Root Cause Analysis, step-by-step diagnostic actions, and OSHA/LOTO safety requirements.
     3. **Verification Agent**: Audits citations, checks numeric tolerances, and provides a Groundedness Confidence Score (e.g. 96%).
2. **Multimodal Testing**:
   - **Voice**: Click `RECORD NOTE` to capture voice dictation with real-time waveform animation.
   - **Vision**: Drag and drop any equipment photo or dial image to extract visual features.
3. **Continuous Learning Loop**:
   - Click **`CONFIRM & LOG RESOLUTION`** to document field actions.
   - The feedback manager saves the validation record and automatically chunks, embeds, and re-indexes it into ChromaDB.
   - Subsequent queries for that asset will immediately pull up this field-verified resolution!
4. **Knowledge Base Manager**:
   - Switch to the **KNOWLEDGE BASE & SOPS** tab to view indexed documents or ingest new PDF/Markdown/JSON files.
