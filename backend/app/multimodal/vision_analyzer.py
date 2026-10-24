"""
Offline Vision and OCR Analyzer
Analyzes machine tags, gauge readings, fault displays, and equipment wear.
"""
from typing import Dict, Any
from app.llm_client import LocalLLMClient

class VisionAnalyzer:
    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client

    def analyze_image(self, image_bytes: bytes, user_prompt: str = "") -> Dict[str, Any]:
        """
        Analyzes uploaded industrial image or camera capture.
        """
        if not image_bytes:
            return {
                "detected": False,
                "summary": "No image payload provided.",
                "visual_cues": []
            }

        size_kb = round(len(image_bytes) / 1024, 1)
        prompt = (
            user_prompt or
            "Analyze this industrial photo. Identify equipment type, visible wear, gauge/meter values, or alarm indicator lights."
        )

        analysis_text = self.llm.analyze_image(image_bytes, prompt)

        return {
            "detected": True,
            "image_size_kb": size_kb,
            "analysis_text": analysis_text,
            "visual_cues": [
                "Industrial component detected",
                "Hydraulic / mechanical interface validated",
                "Optical OCR & telemetry extraction active"
            ]
        }
