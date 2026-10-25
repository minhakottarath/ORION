"""
Offline Audio Transcriber (Whisper STT)
Transcribes technician voice input locally without cloud connectivity.
"""
import io
import wave
from typing import Optional

class AudioTranscriber:
    def __init__(self):
        self.whisper_model = None
        self._init_local_whisper()

    def _init_local_whisper(self):
        """Attempts to load faster-whisper or openai-whisper locally."""
        try:
            from faster_whisper import WhisperModel
            # 'tiny' or 'base' run comfortably on standard CPU
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        except Exception:
            try:
                import whisper
                self.whisper_model = whisper.load_model("base")
            except Exception:
                self.whisper_model = None

    def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribes incoming audio bytes (WAV, WEBM, MP3).
        Falls back gracefully if whisper is not installed on the system.
        """
        if not audio_bytes:
            return ""

        # 1. Faster Whisper
        if self.whisper_model and hasattr(self.whisper_model, "transcribe"):
            try:
                audio_file = io.BytesIO(audio_bytes)
                segments, info = self.whisper_model.transcribe(audio_file, beam_size=2)
                text = " ".join([segment.text for segment in segments]).strip()
                if text:
                    return text
            except Exception:
                pass

        # 2. If Whisper is not installed or loaded, report honestly without fabricating text
        return "[Voice transcription unavailable: local Whisper STT engine is not loaded on this node.]"
