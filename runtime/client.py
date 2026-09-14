"""
client.py — Zero-dependency HTTP client for Ollama API chat completions.
Uses standard library urllib to avoid external bloat.
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "functiongemma:latest"


class OllamaClient:
    def __init__(self, host: str = DEFAULT_HOST, model: str = DEFAULT_MODEL):
        self.host = host.rstrip("/")
        self.model = model
        self.endpoint = f"{self.host}/api/chat"

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.0, timeout: float = 30.0) -> Dict[str, Any]:
        """Send a chat completion request to Ollama with optional tools schema."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if tools:
            payload["tools"] = tools

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to communicate with Ollama at {self.endpoint}: {e}")

