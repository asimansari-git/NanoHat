"""
engine.py — Execution orchestrator for fuge-nanohat.
Handles dynamic tool gating, dynamic system prompt assembly, function calling dispatch,
tool logging, and multi-step resolution.
"""

import json
from typing import List, Dict, Any
try:
    from .client import OllamaClient
    from .functions import REGISTRY
    from .tools import ALL_TOOLS
    from .prompts import get_dynamic_prompt, get_system_prompt
    from .router import route_tools
except (ImportError, ValueError):
    from client import OllamaClient
    from functions import REGISTRY
    from tools import ALL_TOOLS
    from prompts import get_dynamic_prompt, get_system_prompt
    from router import route_tools


class AgentEngine:
    def __init__(self, client: OllamaClient, prompt_version: str = "v1", verbose: bool = False):
        self.client = client
        self.prompt_version = prompt_version
        self.system_prompt = get_system_prompt(prompt_version)
        self.verbose = verbose

    def _log(self, prefix: str, message: str):
        if self.verbose:
            print(f"[\033[94m{prefix}\033[0m] {message}")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Finds and executes the registered tool with sub-1B alias fallback."""
        func = REGISTRY.get(tool_name)
        resolved_name = tool_name

        if not func:
            norm = (tool_name or "").replace("_", "").lower()
            if "battery" in norm:
                func = REGISTRY.get("system_health")
                resolved_name = "system_health"
            elif "wifi" in norm:
                func = REGISTRY.get("toggle_wifi")
                resolved_name = "toggle_wifi"
            elif "blue" in norm:
                func = REGISTRY.get("toggle_bluetooth")
                resolved_name = "toggle_bluetooth"
            elif any(k in norm for k in ["time", "clock", "date"]):
                func = REGISTRY.get("get_datetime")
                resolved_name = "get_datetime"
            elif "trash" in norm:
                func = REGISTRY.get("empty_trash")
                resolved_name = "empty_trash"
            elif any(k in norm for k in ["calc", "math"]):
                func = REGISTRY.get("calculator")
                resolved_name = "calculator"
            elif "power" in norm:
                func = REGISTRY.get("power_profile")
                resolved_name = "power_profile"
            elif "restart" in norm:
                func = REGISTRY.get("restart_service")
                resolved_name = "restart_service"
            elif "status" in norm or "service" in norm:
                func = REGISTRY.get("service_status")
                resolved_name = "service_status"

        if not func:
            err = f"Tool '{tool_name}' not found in registry."
            self._log("ERROR", err)
            return err

        try:
            self._log("TOOL_CALL", f"Invoking {resolved_name}({arguments})")
            args = arguments if isinstance(arguments, dict) else {}
            try:
                result = func(**args)
            except TypeError:
                result = func()
            self._log("TOOL_RESULT", f"{resolved_name} returned: {result}")
            return str(result)
        except Exception as e:
            err = f"Error executing {resolved_name}: {e}"
            self._log("TOOL_ERROR", err)
            return err

    def run(self, user_query: str) -> str:
        """Run full turn: dynamic route -> dynamic prompt -> model -> tool calls -> response."""
        # Step 0: Dynamic tool gating and dynamic prompt assembly
        active_tools = route_tools(user_query, ALL_TOOLS)
        active_tool_names = [t.get("function", {}).get("name") for t in active_tools]
        turn_system_prompt = get_dynamic_prompt(active_tool_names, version=self.prompt_version)

        self._log("USER_PROMPT", user_query)
        self._log("TOOL_ROUTER", f"Active tools ({len(active_tools)}): {active_tool_names}")
        self._log("SYSTEM_PROMPT", turn_system_prompt)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": turn_system_prompt},
            {"role": "user", "content": user_query}
        ]

        # Step 1: Initial call to model with gated tools
        response = self.client.chat(messages=messages, tools=active_tools)
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])

        # Step 2: Check if model emitted tool calls
        if not tool_calls:
            content = message.get("content", "")
            self._log("DIRECT_RESPONSE", "Model responded without tool call.")
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
        final_response = self.client.chat(messages=messages, tools=active_tools)
        final_content = final_response.get("message", {}).get("content", "")

        return final_content
