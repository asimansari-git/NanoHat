"""
engine.py — Execution orchestrator for fuge-nanohat.
Handles function calling dispatch, tool logging, and multi-step resolution.
"""

import json
from typing import List, Dict, Any
try:
    from .client import OllamaClient
    from .functions import REGISTRY
    from .tools import ALL_TOOLS
    from .prompts import get_system_prompt
except (ImportError, ValueError):
    from client import OllamaClient
    from functions import REGISTRY
    from tools import ALL_TOOLS
    from prompts import get_system_prompt



class AgentEngine:
    def __init__(self, client: OllamaClient, prompt_version: str = "v1", verbose: bool = False):
        self.client = client
        self.system_prompt = get_system_prompt(prompt_version)
        self.verbose = verbose

    def _log(self, prefix: str, message: str):
        if self.verbose:
            print(f"[\033[94m{prefix}\033[0m] {message}")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Finds and executes the registered tool."""
        if tool_name not in REGISTRY:
            err = f"Tool '{tool_name}' not found in registry."
            self._log("ERROR", err)
            return err

        func = REGISTRY[tool_name]
        try:
            self._log("TOOL_CALL", f"Invoking {tool_name}({arguments})")
            result = func(**arguments)
            self._log("TOOL_RESULT", f"{tool_name} returned: {result}")
            return str(result)
        except Exception as e:
            err = f"Error executing {tool_name}: {e}"
            self._log("TOOL_ERROR", err)
            return err

    def run(self, user_query: str) -> str:
        """Run full turn: prompt -> model -> optional tool calls -> response."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]

        self._log("USER_PROMPT", user_query)
        self._log("SYSTEM_PROMPT", self.system_prompt)

        # Step 1: Initial call to model with tools
        response = self.client.chat(messages=messages, tools=ALL_TOOLS)
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])

        # Step 2: Check if model emitted tool calls
        if not tool_calls:
            content = message.get("content", "")
            self._log("DIRECT_RESPONSE", content)
            return content

        # Append assistant message with tool calls
        messages.append(message)

        # Step 3: Execute tool calls and collect responses
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass

            output = self.execute_tool(name, args)
            messages.append({
                "role": "tool",
                "name": name,
                "content": output
            })

        # Step 4: Final synthesis step
        self._log("SYNTHESIS", "Sending tool results back to model for final synthesis...")
        final_response = self.client.chat(messages=messages, tools=ALL_TOOLS)
        final_content = final_response.get("message", {}).get("content", "")
        self._log("FINAL_RESPONSE", final_content)

        return final_content
