"""
prompts.py — Dynamic and versioned system prompts for fuge-nanohat.
Decouples tool instructions into modular snippets so the system prompt only presents
active tools to FunctionGemma 270M, preventing context bloat and inactive tool hallucinations.
"""

from typing import List, Optional

BASE_SYSTEM_PROMPT = (
    "You are NanoHat, an autonomous Linux OS assistant running on Fedora Workstation.\n"
    "You must use the provided tools to answer user queries:\n"
)

TOOL_SNIPPETS = {
    "calculator": "- Use calculator for all mathematical calculations and expressions (e.g. 7+7, 7+7*18). Pass the exact full expression to calculator without dropping terms.",
    "system_health": "- Use system_health to check CPU, RAM, and battery metrics (battery level, battery status, health).",
    "power_profile": "- Use power_profile to inspect ('get') or switch ('set') power profiles.",
    "get_datetime": "- Use get_datetime for any date, time, or day of the week queries. Call get_datetime immediately without asking questions.",
    "empty_trash": "- Use empty_trash to permanently empty or clear the Linux trash bin.",
    "toggle_wifi": "- Use toggle_wifi to check Wi-Fi status, turn Wi-Fi on or off, or toggle Wi-Fi.",
    "toggle_bluetooth": "- Use toggle_bluetooth to check Bluetooth status, turn Bluetooth on or off, or toggle Bluetooth.",
    "service_status": "- Use service_status to check the status or running state of any service or application (e.g. ollama, pipewire).",
    "restart_service": "- Use restart_service to restart an allowlisted systemd user service (e.g. pipewire, wireplumber)."
}

PROMPTS = {
    "v1": BASE_SYSTEM_PROMPT,
    "v2": BASE_SYSTEM_PROMPT
}

DEFAULT_VERSION = "v1"


def get_dynamic_prompt(active_tool_names: List[str], version: str = DEFAULT_VERSION) -> str:
    """
    Dynamically builds an ultra-lean system prompt containing instructions ONLY for active tools.
    """
    base = PROMPTS.get(version, BASE_SYSTEM_PROMPT)
    snippets = [TOOL_SNIPPETS[name] for name in active_tool_names if name in TOOL_SNIPPETS]
    
    if snippets:
        return f"{base}\n" + "\n".join(snippets) + "\nAlways invoke the appropriate tool."
    return f"{base}\nAlways invoke the appropriate tool."


def get_system_prompt(version: str = DEFAULT_VERSION, active_tool_names: Optional[List[str]] = None) -> str:
    """Retrieve system prompt. If active_tool_names is provided, returns dynamic prompt."""
    if active_tool_names is not None:
        return get_dynamic_prompt(active_tool_names, version=version)
    # Default fallback includes all registered tool snippets
    return get_dynamic_prompt(list(TOOL_SNIPPETS.keys()), version=version)
