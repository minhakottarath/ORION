"""
Offline Audio Transcriber (Local faster-whisper STT with Vosk Fallback)
Transcribes technician voice input 100% locally without cloud connectivity.
"""
import io
import os
import json
import wave
import tempfile
from pathlib import Path
from typing import Optional

from app.config import VOSK_MODEL_DIR, WHISPER_MODEL_SIZE

class AudioTranscriber:
    def __init__(self):
        self.whisper_model = None
        self.vosk_model = None
        self._init_local_whisper()
        self._init_local_vosk()

    def _init_local_whisper(self):
        """Initializes offline faster-whisper model."""
        try:
            from faster_whisper import WhisperModel
            print(f"[ORION-AUDIO] Initializing local faster-whisper ({WHISPER_MODEL_SIZE} model on CPU)...")
            try:
                # First attempt 100% offline from local cache
                self.whisper_model = WhisperModel(
                    WHISPER_MODEL_SIZE,
                    device="cpu",
                    compute_type="int8",
                    local_files_only=True
                )
            except Exception:
                # If not cached yet, allow download once to cache permanently
                self.whisper_model = WhisperModel(
                    WHISPER_MODEL_SIZE,
                    device="cpu",
                    compute_type="int8",
                    local_files_only=False
                )
            print(f"[ORION-AUDIO] Local faster-whisper ({WHISPER_MODEL_SIZE}) initialized successfully.")
        except Exception as e:
            print(f"[ORION-AUDIO] faster-whisper initialization note: {e}")
            self.whisper_model = None

    def _init_local_vosk(self):
        """Initializes offline Vosk speech recognition model as secondary fallback."""
        try:
            if VOSK_MODEL_DIR.exists():
                import vosk
                vosk.SetLogLevel(-1)  # Quiet Kaldi logs in production
                print(f"[ORION-AUDIO] Loading offline Vosk fallback model from {VOSK_MODEL_DIR.name}...")
                self.vosk_model = vosk.Model(str(VOSK_MODEL_DIR))
                print("[ORION-AUDIO] Offline Vosk STT initialized successfully.")
            else:
                print(f"[ORION-AUDIO] Vosk model directory not found at {VOSK_MODEL_DIR}.")
        except Exception as e:
            print(f"[ORION-AUDIO] Vosk initialization note: {e}")
            self.vosk_model = None

    def get_status(self) -> dict:
        """Returns diagnostic status of local offline speech engines."""
        return {
            "whisper_loaded": self.whisper_model is not None,
            "whisper_model": WHISPER_MODEL_SIZE,
            "vosk_loaded": self.vosk_model is not None,
            "primary_engine": f"faster-whisper ({WHISPER_MODEL_SIZE})" if self.whisper_model else ("Vosk (Local Offline)" if self.vosk_model else "None"),
            "offline_ready": (self.whisper_model is not None or self.vosk_model is not None)
        }

    def _normalize_pcm16(self, pcm_bytes: bytes, target_peak: int = 24000) -> bytes:
        """
        Applies linear digital gain normalization to quiet 16-bit PCM audio.
        Significantly improves phoneme recognition accuracy on built-in laptop microphones.
        """
        if not pcm_bytes or len(pcm_bytes) < 4:
            return pcm_bytes
        try:
            import struct
            sample_count = len(pcm_bytes) // 2
            samples = list(struct.unpack(f"<{sample_count}h", pcm_bytes))
            if not samples:
                return pcm_bytes
            max_val = max(abs(s) for s in samples)
            # Only boost if signal is quiet (between 500 and 18000 peak)
            if 500 < max_val < 18000:
                gain = min(5.0, target_peak / float(max_val))
                norm_samples = [max(-32768, min(32767, int(s * gain))) for s in samples]
                return struct.pack(f"<{sample_count}h", *norm_samples)
        except Exception:
            pass
        return pcm_bytes

    def _decode_to_pcm16(self, audio_bytes: bytes) -> Optional[bytes]:
        """
        Decodes incoming WAV, WEBM, MP3, or OGG audio bytes into 16kHz 16-bit mono PCM.
        First attempts zero-overhead direct WAV parsing; falls back to PyAV with resampler flushing.
        """
        # 1. Fast Path: Direct WAV extraction if incoming audio is standard 16kHz mono WAV
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                if channels == 1 and sampwidth == 2 and framerate == 16000:
                    raw_frames = wf.readframes(wf.getnframes())
                    return self._normalize_pcm16(raw_frames)
        except Exception:
            pass

        # 2. General Path: PyAV container decoding & 16kHz mono resampling
        try:
            import av
            input_container = av.open(io.BytesIO(audio_bytes))
            if not input_container.streams.audio:
                return None
            resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
            pcm_chunks = []
            for frame in input_container.decode(audio=0):
                resampled = resampler.resample(frame)
                for rf in resampled:
                    pcm_chunks.append(bytes(rf.planes[0]))
            # CRITICAL: Flush remaining buffered samples from resampler (prevents cutting off tail of words)
            flushed = resampler.resample(None)
            for rf in flushed:
                pcm_chunks.append(bytes(rf.planes[0]))

            full_pcm = b"".join(pcm_chunks)
            return self._normalize_pcm16(full_pcm)
        except Exception as e:
            print(f"[ORION-AUDIO] Audio decoding note: {e}")
            return None

    def transcribe_whisper(self, pcm_data: bytes) -> str:
        """Transcribes 16kHz mono 16-bit PCM bytes using faster-whisper in-memory."""
        if not self.whisper_model or not pcm_data:
            return ""
        try:
            import numpy as np
            # Convert 16-bit PCM to float32 normalized [-1.0, 1.0] for whisper
            audio_array = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Check for pure silence
            if np.max(np.abs(audio_array)) < 0.005:
                return ""

            segments, _ = self.whisper_model.transcribe(
                audio_array,
                beam_size=1,
                language="en",
                vad_filter=True
            )
            text = " ".join([segment.text.strip() for segment in segments]).strip()
            return text
        except Exception as ex:
            print(f"[ORION-AUDIO] faster-whisper error: {ex}")
            return ""

    def transcribe_vosk(self, pcm_data: bytes) -> str:
        """Transcribes 16kHz mono 16-bit PCM bytes using offline Vosk Kaldi STT."""
        if not self.vosk_model or not pcm_data:
            return ""
        try:
            import vosk
            recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
            recognizer.SetWords(True)

            transcripts = []
            chunk_size = 4000  # Feed in 125ms (4000 byte) frames
            for i in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[i:i + chunk_size]
                if recognizer.AcceptWaveform(chunk):
                    res = json.loads(recognizer.Result())
                    part = res.get("text", "").strip()
                    if part:
                        transcripts.append(part)

            final_res = json.loads(recognizer.FinalResult())
            part = final_res.get("text", "").strip()
            if part:
                transcripts.append(part)

            return " ".join(transcripts).strip()
        except Exception as ex:
            print(f"[ORION-AUDIO] Vosk recognition error: {ex}")
            return ""

    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        engine: Optional[str] = None
    ) -> str:
        """
        Transcribes incoming audio bytes completely offline.
        Uses faster-whisper ('base' model) as primary engine with Vosk as offline fallback.
        Never invokes cloud speech APIs or simulated fallbacks.
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return ""

        pcm_data = self._decode_to_pcm16(audio_bytes)
        if not pcm_data or len(pcm_data) == 0:
            return ""

        # Specific engine requested
        if engine == "vosk":
            return self.transcribe_vosk(pcm_data)
        if engine == "whisper":
            return self.transcribe_whisper(pcm_data)

        # 1. Primary Engine: faster-whisper
        if self.whisper_model:
            text = self.transcribe_whisper(pcm_data)
            if text:
                return text

        # 2. Secondary Engine: Offline Vosk Speech Recognition Fallback
        if self.vosk_model:
            text = self.transcribe_vosk(pcm_data)
            if text:
                return text

        # Return empty if no speech recognized or engine failed
        return ""
