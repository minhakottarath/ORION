"""
LLM Client Interface
Connects to local Ollama instance with zero external dependencies.
Processes all industrial reasoning dynamically using local models.
"""
import base64
import requests
from typing import List, Dict, Any, Optional

from app.config import OLLAMA_BASE_URL, DEFAULT_LLM_MODEL, DEFAULT_VISION_MODEL

class LocalLLMClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip('/')

    def get_available_models(self) -> List[str]:
        """Fetches list of model names currently loaded in Ollama."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [m.get("name") for m in models if m.get("name")]
        except Exception:
            pass
        return []

    def check_health(self) -> Dict[str, Any]:
        """Checks if local Ollama daemon is responsive and retrieves available models."""
        available = self.get_available_models()
        if available:
            selected = DEFAULT_LLM_MODEL if DEFAULT_LLM_MODEL in available else available[0]
            return {
                "online": True,
                "provider": "Ollama (Local Offline Server)",
                "endpoint": self.base_url,
                "available_models": available,
                "selected_model": selected
            }

        return {
            "online": False,
            "provider": "Local LLM Server (Disconnected)",
            "endpoint": self.base_url,
            "available_models": [],
            "selected_model": "None (LLM Server Offline)"
        }

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        temperature: float = 0.1,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Sends generation request to local Ollama.
        Executes dynamically with zero hardcoded canned responses.
        Raises RuntimeError if local LLM is unavailable.
        """
        model_name = model or DEFAULT_LLM_MODEL
        
        # Verify if model is available, or pick best matching local model
        available = self.get_available_models()
        if available and model_name not in available:
            # Try to find a model matching the prefix, e.g. "llama3.2" -> "llama3.2:1b"
            matching = [m for m in available if model_name.split(':')[0] in m]
            if matching:
                model_name = matching[0]
            else:
                model_name = available[0]

        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 350
            }
        }

        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=90.0)
            if resp.status_code == 200:
                result = resp.json()
                if "response" in result and result["response"].strip():
                    return result["response"].strip()
                else:
                    raise RuntimeError("Local LLM returned an empty response.")
            else:
                error_msg = resp.text
                try:
                    error_msg = resp.json().get("error", resp.text)
                except Exception:
                    pass
                raise RuntimeError(f"Local LLM returned HTTP {resp.status_code}: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to connect to local LLM at {self.base_url}: {e}")

    def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        """
        Sends image + prompt to local vision model (e.g. llama3.2-vision).
        Returns clear notice if vision model is unavailable.
        """
        available = self.get_available_models()
        vision_model = DEFAULT_VISION_MODEL if DEFAULT_VISION_MODEL in available else None
        if not vision_model:
            # Check if any vision model is available
            vision_candidates = [m for m in available if "vision" in m.lower() or "llava" in m.lower()]
            if vision_candidates:
                vision_model = vision_candidates[0]

        if not vision_model:
            return (
                f"Visual processing note: Local vision model ({DEFAULT_VISION_MODEL}) is not installed in Ollama. "
                f"Payload received ({round(len(image_bytes)/1024, 1)} KB). Text reasoning proceeding without image features."
            )

        try:
            b64_img = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "model": vision_model,
                "prompt": prompt or "Analyze this industrial component, gauge reading, or error display.",
                "images": [b64_img],
                "stream": False
            }
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=30.0)
            if resp.status_code == 200:
                res = resp.json().get("response")
                if res:
                    return res.strip()
        except Exception as e:
            return f"Vision analysis failed: {e}"

        return "Vision analysis returned no detections."
