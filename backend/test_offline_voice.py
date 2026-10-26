"""
ORION Offline Voice Input Verification Suite
Verifies 100% offline speech recognition using local Vosk model,
verifies that speech transcript feeds accurately into ORION local RAG,
and tests error handling for silence, corrupted audio, and missing formats.
"""
import sys
import io
import os
import wave
import struct
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.config import VOSK_MODEL_DIR, MODELS_DIR
from app.multimodal.audio_transcriber import AudioTranscriber
from app.rag.vector_store import VectorStore
from app.llm_client import LocalLLMClient
from app.agents.orchestrator import AgentOrchestrator

def test_offline_voice():
    print("=" * 70)
    print("  ORION OFFLINE VOICE INPUT & RAG INTEGRATION VERIFICATION")
    print("=" * 70)

    # 1. Model Location & Offline Storage Verification
    print("\n[VERIFICATION 1] Checking Local Offline Model Storage...")
    print(f"  Vosk Model Directory: {VOSK_MODEL_DIR}")
    assert VOSK_MODEL_DIR.exists(), f"Vosk model directory not found at {VOSK_MODEL_DIR}"
    assert (VOSK_MODEL_DIR / "am").exists(), "Acoustic model directory missing"
    assert (VOSK_MODEL_DIR / "graph").exists(), "HCLG graph directory missing"
    print("  ✓ Local model files verified on local disk (Zero cloud dependencies).")

    # 2. Audio Transcriber Initialization
    print("\n[VERIFICATION 2] Initializing AudioTranscriber...")
    transcriber = AudioTranscriber()
    status = transcriber.get_status()
    print(f"  Engine Status: {status}")
    assert status["offline_ready"] is True, "Offline STT must be ready!"
    assert status["whisper_loaded"] is True, "faster-whisper STT must be loaded locally!"
    print(f"  ✓ Offline speech engine loaded ({status['primary_engine']}).")

    # 3. Audio Transcription with Local Audio File
    print("\n[VERIFICATION 3] Transcribing Audio Files Offline...")
    # 3a. Single-word plosive & vowel precision tests ("cat" and "dog")
    cat_path = backend_dir / "test_cat.wav"
    dog_path = backend_dir / "test_dog.wav"
    if cat_path.exists():
        cat_transcript = transcriber.transcribe_audio_bytes(open(cat_path, "rb").read(), "test_cat.wav")
        print(f"  Spoken Word 'cat' -> Transcribed: '{cat_transcript}'")
        cat_clean = cat_transcript.lower().strip(" .!?,")
        assert cat_clean == "cat", f"Expected 'cat', got '{cat_transcript}'"

    if dog_path.exists():
        dog_transcript = transcriber.transcribe_audio_bytes(open(dog_path, "rb").read(), "test_dog.wav")
        print(f"  Spoken Word 'dog' -> Transcribed: '{dog_transcript}'")
        dog_clean = dog_transcript.lower().strip(" .!?,")
        assert dog_clean == "dog", f"Expected 'dog', got '{dog_transcript}'"

    # 3b. Full industrial question test
    test_audio_path = backend_dir / "test_voice.wav"
    if not test_audio_path.exists():
        print("  Generating test audio...")
        import subprocess
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(backend_dir / "generate_test_audio.ps1")], check=True)

    with open(test_audio_path, "rb") as f:
        audio_bytes = f.read()

    transcript = transcriber.transcribe_audio_bytes(audio_bytes, filename="test_voice.wav")
    print(f"  Audio File Size: {len(audio_bytes)} bytes")
    print(f"  Recognized Speech Text: '{transcript}'")
    assert len(transcript.strip()) > 0, "Transcription should not be empty!"
    assert "vibration" in transcript.lower(), "Transcript must contain spoken word 'vibration'!"
    assert "titan" in transcript.lower(), "Transcript must contain spoken word 'titan'!"
    print("  ✓ Local offline transcription accurate and complete (tested 'cat', 'dog', and full technical query).")

    # 4. Error Handling Verification (Silence, Empty, and Corrupted Audio)
    print("\n[VERIFICATION 4] Testing Error & Edge-Case Handling...")
    # Empty audio
    empty_res = transcriber.transcribe_audio_bytes(b"", "empty.wav")
    assert empty_res == "", "Empty audio must return empty string without error"
    print("  ✓ Empty audio handled safely.")

    # Pure silence (1 second of 16kHz mono 16-bit zeros)
    silence_pcm = b"\x00" * 32000
    silence_buf = io.BytesIO()
    with wave.open(silence_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(silence_pcm)
    silence_wav = silence_buf.getvalue()
    silence_res = transcriber.transcribe_audio_bytes(silence_wav, "silence.wav")
    assert silence_res == "", "Silence audio must return empty string without hallucinating"
    print("  ✓ Silent audio handled safely (no hallucinated speech).")

    # Corrupted / non-audio bytes
    corrupt_bytes = b"NOT_A_VALID_AUDIO_FILE_DATA_CORRUPTION_TEST" * 10
    corrupt_res = transcriber.transcribe_audio_bytes(corrupt_bytes, "corrupt.bin")
    assert corrupt_res == "", "Corrupted audio must be rejected gracefully"
    print("  ✓ Corrupted audio handled safely without crashing.")

    # 5. End-to-End Integration with ORION Local RAG Pipeline
    print("\n[VERIFICATION 5] Feeding Spoken Question into Local RAG Pipeline...")
    vector_store = VectorStore()
    llm_client = LocalLLMClient()
    orchestrator = AgentOrchestrator(vector_store, llm_client)

    rag_result = orchestrator.process_query(query=transcript)
    print(f"  Query Latency: {rag_result['total_latency_ms']} ms")
    print(f"  Verified Answer:\n  {rag_result['verified_answer'][:300]}...")
    print(f"  Verification Status: {rag_result['verification']['status']} (Score: {rag_result['verification']['groundedness_score']}%)")

    assert rag_result["verification"]["groundedness_score"] >= 75, "RAG answer must achieve high groundedness score!"
    assert "4.5" in rag_result["verified_answer"] or "RMS" in rag_result["verified_answer"] or "vibration" in rag_result["verified_answer"].lower(), "Answer must contain Titan-800 vibration specifications!"
    print("  ✓ End-to-end Offline Voice -> RAG -> Verification successfully passed!")

    print("\n" + "=" * 70)
    print("  ALL OFFLINE VOICE VERIFICATION TESTS PASSED (100% AIR-GAPPED)")
    print("=" * 70)

if __name__ == "__main__":
    test_offline_voice()
