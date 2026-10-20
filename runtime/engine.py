"""
engine.py - Pure Direct-Dispatch Runtime Engine for NanoHat v4.0.
Decoupled from prompt-inspection heuristics; 100% driven by fine-tuned model tool calls.
"""
import json
import re
from typing import List, Dict, Any, Tuple

try:
    from runtime.client import OllamaClient
    from runtime.functions import REGISTRY
    from runtime.tools import ALL_TOOLS
    from runtime.prompts import get_system_prompt
except (ImportError, ModuleNotFoundError):
    from client import OllamaClient
    from functions import REGISTRY
    from tools import ALL_TOOLS
    from prompts import get_system_prompt

ARG_ALIASES = {
    "system_health": {"type": "metric", "target": "metric"},
    "service_status": {"service": "service_name", "unit": "service_name", "name": "service_name"},
    "restart_service": {"service": "service_name", "unit": "service_name", "name": "service_name"},
    "toggle_wifi": {"action": "state"},
    "toggle_bluetooth": {"action": "state"},
    "disk_usage": {"directory": "path", "folder": "path", "mount": "path"},
}

DEFAULT_ARG_FALLBACKS = {
    "system_health": {"metric": "all"},
    "power_profile": {"action": "get"},
    "toggle_wifi": {"state": "status"},
    "toggle_bluetooth": {"state": "status"},
    "disk_usage": {"path": "/"},
    "desktop_appearance": {"action": "status"},
    "audio_control": {"action": "status"},
}


class AgentEngine:
    def __init__(
        self,
        client: OllamaClient,
        verbose: bool = False,
    ):
        self.client = client
        self.verbose = verbose
        self.history: List[Dict[str, Any]] = []

    def _log(self, prefix: str, message: str):
        if self.verbose:
            print(f"[\033[94m{prefix}\033[0m] {message}")

    def normalize_call(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Pure schema normalization: maps parameter aliases and applies default fallbacks
        if required parameters are omitted. Never inspects user prompt strings or keywords.
        """
        if not isinstance(args, dict):
            args = {}

        # 1. Parameter key alias remapping
        aliases = ARG_ALIASES.get(tool_name, {})
        normalized = {aliases.get(k, k): v for k, v in args.items()}

        # 2. Sensible default fallback if required key is omitted
        defaults = DEFAULT_ARG_FALLBACKS.get(tool_name, {})
        for default_key, default_val in defaults.items():
            if default_key not in normalized or normalized[default_key] is None:
                normalized[default_key] = default_val

        return tool_name, normalized

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Executes a normalized tool call against the local Fedora execution registry."""
        actual_tool, clean_args = self.normalize_call(tool_name, arguments)
        func = REGISTRY.get(actual_tool)
        if not func:
            err = f"Tool '{actual_tool}' not found in registry."
            self._log("ERROR", err)
            return err
        try:
            self._log("TOOL_CALL", f"Invoking {actual_tool}({clean_args})")
            result = func(**clean_args)
            self._log("TOOL_RESULT", f"{actual_tool} returned: {result}")
            return str(result)
        except Exception as e:
            err = f"Error executing {actual_tool}: {e}"
            self._log("TOOL_ERROR", err)
            return err

    def _extract_fallback_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """
        Catches tool calls when an SLM outputs raw <tool_call> tags inside message['content']
        rather than through Ollama's structured tool_calls array.
        """
        if not content:
            return []
        extracted = []

        # Find explicit <tool_call>{...}</tool_call> tags
        for match in re.finditer(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", content, re.DOTALL):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict) and "name" in data:
                    raw_args = data.get("arguments", data.get("parameters", {}))
                    extracted.append({
                        "function": {
                            "name": data["name"],
                            "arguments": raw_args if isinstance(raw_args, dict) else {},
                        }
                    })
            except Exception:
                continue

        # If no explicit tags, check for isolated JSON block
        if not extracted:
            cleaned = content.strip()
            if cleaned.startswith("{") and cleaned.endswith("}"):
                try:
                    data = json.loads(cleaned)
                    if isinstance(data, dict) and "name" in data:
                        raw_args = data.get("arguments", data.get("parameters", {}))
                        extracted.append({
                            "function": {
                                "name": data["name"],
                                "arguments": raw_args if isinstance(raw_args, dict) else {},
                            }
                        })
                except Exception:
                    pass

        return extracted

    def run(self, user_query: str) -> str:
        """
        Primary execution entrypoint:
        1. Submits system prompt + user query to Ollama client.
        2. Dispatches structured tool calls directly to Fedora functions.
        3. Returns plain-text responses directly for math, definitions, and chat.
        """
        system_prompt = get_system_prompt()
        self._log("USER_PROMPT", user_query)
        self._log("SYSTEM_PROMPT", system_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        response = self.client.chat(messages=messages, tools=ALL_TOOLS)
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])

        # Fallback to content extraction if Ollama didn't parse structured tool_calls
        if not tool_calls:
            tool_calls = self._extract_fallback_tool_calls(message.get("content", ""))

        # Conversational / Math / Refusal / Plain-Text response (Zero tools emitted)
        if not tool_calls:
            content = (message.get("content") or "").strip()
            # Clean think tags for final user presentation if model emitted them
            clean_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            final_text = clean_content or content or "No operation was requested."
            self.history.append({"role": "user", "content": user_query})
            self.history.append({"role": "assistant", "content": final_text})
            return final_text

        # Tool execution branch
        self.history.append({"role": "user", "content": user_query})
        self.history.append(message)

        outputs = []
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            output = self.execute_tool(name, args)
            outputs.append(output)
            self.history.append({"role": "tool", "name": name, "content": output})

        return "\n".join(outputs)