"""
client.py — Official Ollama Python SDK client for chat completions.
Uses the official `ollama` Python library for local LLM inference.
"""

from typing import List, Dict, Any, Optional
import ollama

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "functiongemma:latest"


class OllamaClient:
    def __init__(self, host: str = DEFAULT_HOST, model: str = DEFAULT_MODEL):
        self.host = host.rstrip("/")
        self.model = model
        self.client = ollama.Client(host=self.host)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Send a chat completion request to Ollama with optional tools schema via official SDK."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                options={"temperature": temperature},
            )
            if hasattr(response, "model_dump"):
                return response.model_dump()
            return dict(response)
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with Ollama at {self.host}: {e}")

