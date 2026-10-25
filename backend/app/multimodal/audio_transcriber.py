"""
Offline Audio Transcriber (Whisper STT)
Transcribes technician voice input locally without cloud connectivity.
"""
import io
import os
import tempfile
from pathlib import Path
from typing import Optional

class AudioTranscriber:
    def __init__(self):
        self.whisper_model = None
        self._init_local_whisper()

    def _init_local_whisper(self):
        """Attempts to load faster-whisper or openai-whisper locally."""
        try:
            # 'tiny' runs fast on CPU with low memory
            print("[ORION-AUDIO] Loading faster-whisper (tiny model on CPU)...")
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            print("[ORION-AUDIO] faster-whisper initialized successfully.")
        except Exception as e:
            try:
                import whisper
                print("[ORION-AUDIO] Loading openai-whisper (base model)...")
                self.whisper_model = whisper.load_model("base")
                print("[ORION-AUDIO] openai-whisper initialized successfully.")
            except Exception as e2:
                print(f"[ORION-AUDIO] Local Whisper model not loaded ({e2}). Install faster-whisper for local STT.")
                self.whisper_model = None

    def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribes incoming audio bytes (WAV, WEBM, MP3).
        Falls back gracefully if whisper is not installed on the system.
        """
        if not audio_bytes:
            return ""

        suffix = Path(filename).suffix.lower() if filename else ".webm"
        if suffix not in [".wav", ".webm", ".mp3", ".ogg", ".m4a"]:
            suffix = ".webm"

        temp_audio_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_bytes)
                temp_audio_path = f.name

            # 1. Faster Whisper
            if self.whisper_model and hasattr(self.whisper_model, "transcribe"):
                try:
                    segments, info = self.whisper_model.transcribe(temp_audio_path, beam_size=2)
                    text = " ".join([segment.text for segment in segments]).strip()
                    if text:
                        return text
                except Exception as ex:
                    print(f"[ORION-AUDIO] Whisper transcription error: {ex}")

        except Exception as e:
            print(f"[ORION-AUDIO] Audio temp file error: {e}")
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass

        # 2. Return empty if Whisper model is not installed or transcription failed
        return ""
