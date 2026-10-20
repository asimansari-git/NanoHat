"""
client.py — Official Ollama Python SDK client optimized for Qwen3-0.6B tool dispatch.
"""

import os
from typing import List, Dict, Any, Optional
import ollama

DEFAULT_HOST = os.environ.get("NANOHAT_OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("NANOHAT_MODEL", "asimansari-o/nanohat")


class OllamaClient:
    def __init__(self, host: str = DEFAULT_HOST, model: str = DEFAULT_MODEL, timeout: float = 60.0):
        self.host = host.rstrip("/")
        self.model = model
        self.client = ollama.Client(host=self.host, timeout=timeout)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.6,
        top_p: float = 0.95,
        top_k: int = 20,
        think: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Send a chat completion request to Ollama with tools schema."""
        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "num_predict": 2048,
                },
            }
            if think is not None:
                kwargs["think"] = think
            elif "qwen3" in self.model.lower():
                env_think = os.environ.get("NANOHAT_THINK", "0").strip().lower()
                kwargs["think"] = env_think in {"1", "true", "yes"}

            response = self.client.chat(**kwargs)
            if hasattr(response, "model_dump"):
                return response.model_dump()
            return dict(response)
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with Ollama at {self.host}: {e}")