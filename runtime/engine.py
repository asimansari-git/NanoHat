"""
engine.py - Streamlined direct-dispatch engine with parameter normalization.
"""
import json
import re
from typing import List, Dict, Any

from runtime.client import OllamaClient
from runtime.functions import REGISTRY
from runtime.tools import ALL_TOOLS
from runtime.prompts import get_system_prompt

ARG_ALIASES = {
    "system_health": {"type": "metric", "target": "metric"},
    "service_status": {"service": "service_name", "unit": "service_name", "name": "service_name"},
    "restart_service": {"service": "service_name", "unit": "service_name", "name": "service_name"},
    "toggle_wifi": {"action": "state"},
    "toggle_bluetooth": {"action": "state"},
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

    def normalize_call(self, tool_name: str, args: Dict[str, Any], query: str = "") -> tuple[str, Dict[str, Any]]:
        if not isinstance(args, dict):
            args = {}
        aliases = ARG_ALIASES.get(tool_name, {})
        normalized = {aliases.get(k, k): v for k, v in args.items()}
        q_lower = query.lower()

        # Catch power_profile misfires
        if tool_name == "power_profile":
            # 1. Radio misfires (e.g. "Is Wi-Fi turned on?" caught by "turned on")
            if any(w in q_lower for w in ["wifi", "wi-fi"]):
                tool_name = "toggle_wifi"
                is_question = bool(re.search(r"^(is|check|what|are)\b", q_lower.strip()))
                normalized = {"state": "status" if is_question else ("off" if "off" in q_lower else "on")}
            elif any(w in q_lower for w in ["bluetooth", "bt", "blue-teeth"]):
                tool_name = "toggle_bluetooth"
                is_question = bool(re.search(r"^(is|check|what|are)\b", q_lower.strip()))
                normalized = {"state": "status" if is_question else ("off" if "off" in q_lower else "on")}
            # 2. Telemetry misfires (e.g. "Check CPU load" or "Laptop is hot")
            else:
                is_telemetry = any(k in q_lower for k in ["cpu", "ram", "memory", "load", "hot", "temp", "usage"])
                has_profile_kw = any(p in q_lower for p in ["profile", "performance", "power-saver", "balanced"])
                if is_telemetry and not has_profile_kw:
                    tool_name = "system_health"
                    normalized = {"metric": "ram" if any(r in q_lower for r in ["ram", "memory"]) else "cpu"}

        # Normalize system_health metrics
        if tool_name == "system_health":
            if "metric" not in normalized or normalized["metric"] not in ["battery", "ram", "cpu", "all"]:
                if any(w in q_lower for w in ["battery", "batt", "juice", "charge"]):
                    normalized["metric"] = "battery"
                elif any(w in q_lower for w in ["ram", "memory", "swap"]):
                    normalized["metric"] = "ram"
                elif any(w in q_lower for w in ["cpu", "processor", "load"]):
                    normalized["metric"] = "cpu"
                else:
                    normalized["metric"] = "all"

        # Normalize power_profile actions and profiles
        if tool_name == "power_profile":
            if any(p in q_lower for p in ["power-saver", "powersaver", "saver", "save"]):
                normalized["action"] = "set"
                normalized["profile"] = "power-saver"
            elif "performance" in q_lower:
                normalized["action"] = "set"
                normalized["profile"] = "performance"
            elif "balanced" in q_lower:
                normalized["action"] = "set"
                normalized["profile"] = "balanced"
            elif any(w in q_lower for w in ["active", "current", "what", "check", "get"]):
                normalized["action"] = "get"
                normalized.pop("profile", None)

        # Ensure question-form queries stay in read-only status
        if tool_name in ["toggle_wifi", "toggle_bluetooth"]:
            is_question = bool(re.search(r"^(is|check|what|are)\b", q_lower.strip()))
            has_explicit_change = any(w in q_lower for w in ["turn on", "turn off", "switch on", "switch off", "disable", "enable"])
            if is_question and not has_explicit_change:
                normalized["state"] = "status"
            elif "state" not in normalized:
                if any(w in q_lower for w in ["off", "disable", "kill"]):
                    normalized["state"] = "off"
                elif any(w in q_lower for w in ["on", "enable"]):
                    normalized["state"] = "on"
                else:
                    normalized["state"] = "status"

        return tool_name, normalized

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], query: str = "") -> str:
        actual_tool, clean_args = self.normalize_call(tool_name, arguments, query=query)
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

    def run(self, user_query: str) -> str:
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

        if not tool_calls:
            # Fallback if model still attempts conversational refusal on battery/hardware
            q_lower = user_query.lower()
            if any(w in q_lower for w in ["battery", "batt", "juice"]):
                output = self.execute_tool("system_health", {"metric": "battery"}, query=user_query)
                self.history.append({"role": "user", "content": user_query})
                self.history.append({"role": "tool", "name": "system_health", "content": output})
                return output

            content = message.get("content", "").strip()
            self.history.append({"role": "user", "content": user_query})
            self.history.append(message)
            return content or "No operation was requested."

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
            output = self.execute_tool(name, args, query=user_query)
            outputs.append(output)
            self.history.append({"role": "tool", "name": name, "content": output})

        return "\n".join(outputs)