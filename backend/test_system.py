"""
ORION System Self-Test & Verification Suite
Verifies offline RAG ingestion, retrieval accuracy, multi-agent orchestration, and feedback re-indexing.
"""
import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.rag.document_loader import DocumentLoader
from app.rag.chunker import IndustrialChunker
from app.rag.vector_store import VectorStore
from app.llm_client import LocalLLMClient
from app.agents.orchestrator import AgentOrchestrator
from app.feedback.feedback_manager import FeedbackManager
from app.config import KNOWLEDGE_BASE_DIR

def run_tests():
    print("=" * 65)
    print("  ORION INDUSTRIAL MULTI-AGENT RAG - SYSTEM VERIFICATION SUITE")
    print("=" * 65)

    # 1. Document Loading & Chunker Test
    print("\n[TEST 1] Loading Heterogeneous Knowledge Base...")
    chunker = IndustrialChunker()
    vector_store = VectorStore()
    vector_store.reset()  # Start with a clean state
    
    total_chunks = 0
    for doc_path in KNOWLEDGE_BASE_DIR.glob("*.*"):
        if doc_path.suffix.lower() in [".md", ".txt", ".json", ".csv"]:
            text, meta = DocumentLoader.load_file(doc_path)
            chunks = chunker.chunk_document(text, meta)
            added = vector_store.add_chunks(chunks)
            total_chunks += added
            print(f"  ✓ Ingested {doc_path.name} -> {len(chunks)} semantic chunks")

    stats = vector_store.get_stats()
    print(f"  -> Vector Store Stats: {stats['total_chunks']} chunks across {stats['total_documents']} documents ({stats['engine']})")
    assert stats['total_chunks'] > 0, "Vector store should contain indexed chunks!"

    # 2. Retrieval Accuracy Test
    print("\n[TEST 2] Testing Semantic Retrieval...")
    test_query = "Hydraulic pressure oscillation and proportional relief valve"
    retrieved = vector_store.query(test_query, top_k=2)
    print(f"  Query: '{test_query}'")
    for idx, r in enumerate(retrieved):
        print(f"  Hit #{idx+1}: [{r['metadata'].get('doc_id')}] {r['metadata'].get('title')} (Score: {r['similarity_score']})")
    assert len(retrieved) > 0, "Retrieval should return matching chunks!"
    assert "SOP" in retrieved[0]['metadata'].get('doc_id', ''), "Top result should be the hydraulic SOP!"
    print("  ✓ Retrieval accuracy validated!")

    # 3. Multi-Agent Orchestration Test
    print("\n[TEST 3] Testing Multi-Agent Orchestration (Retrieval -> Reasoning -> Verification)...")
    llm_client = LocalLLMClient()
    orchestrator = AgentOrchestrator(vector_store, llm_client)

    result = orchestrator.process_query(
        query="Turbine generator T800 high vibration 1X RPM dominant peak observed during load test"
    )

    print(f"  Query Latency: {result['total_latency_ms']} ms")
    print(f"  Agent Pipeline Steps Executed: {len(result['agent_steps'])}")
    for step in result['agent_steps']:
        print(f"    - {step['agent']}: {step['status']} ({step['summary']})")

    verif = result['verification']
    print(f"  Verification Result: {verif['status']} | Groundedness: {verif['groundedness_score']}% | Risk: {verif['hallucination_risk']}")
    assert verif['groundedness_score'] >= 75, "Groundedness score should meet verification threshold!"
    print("  ✓ Multi-agent pipeline validated successfully!")

    # 4. Technician Feedback & Continuous Learning Loop Test
    print("\n[TEST 4] Testing Feedback Submission & Continuous Re-indexing Loop...")
    feedback_mgr = FeedbackManager(vector_store)
    fb_res = feedback_mgr.submit_feedback(
        query="Hydraulic pressure fluctuation on HPU Unit 4",
        answer=result['verified_answer'],
        verdict="confirmed",
        technician_notes="Replaced Schrader valve seal on accumulator ACC-1 and torqued PRV-12 flange. Pressure stabilized at 180 bar.",
        equipment_id="HPU-SERIES-900",
        technician_name="Senior Technician J. Miller"
    )
    print(f"  Feedback Logged: {fb_res['feedback_id']} | Status: {fb_res['status']}")
    print(f"  Knowledge Base Re-indexed: {fb_res['knowledge_updated']} ({fb_res['reindexed_chunks']} new chunk)")

    # Verify that the newly logged feedback is retrievable
    validation_query = "Schrader valve seal on accumulator ACC-1"
    subsequent_search = vector_store.query(validation_query, top_k=5)
    found_feedback = any("VAL-" in r['metadata'].get('doc_id', '') for r in subsequent_search)
    print(f"  Query: '{validation_query}'")
    print(f"  Found Field-Validated Solution in ChromaDB: {found_feedback}")
    assert found_feedback, "Newly submitted technician feedback must be indexed and retrievable!"
    print("  ✓ Continuous learning loop validated successfully!")

    print("\n" + "=" * 65)
    print("  ALL 4 SYSTEM VERIFICATION TESTS PASSED SUCCESSFULLY (100% OFFLINE)")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
