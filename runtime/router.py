"""
router.py — High-speed deterministic intent router and dynamic tool gater.
Filters the active tool catalog down to 2-3 relevant schemas per turn to prevent
cognitive context saturation and attention diffusion on sub-1B models like FunctionGemma 270M.
"""

import re
from typing import List, Dict, Any

# Compiled regex patterns for intent clusters
RE_DATETIME = re.compile(r"\b(time|date|today|clock|hour|minute|day|month|year|timezone|now)\b", re.IGNORECASE)
RE_SERVICE_EXPLICIT = re.compile(r"\b(service|systemd|daemon|unit)\b", re.IGNORECASE)
RE_SERVICE_ACTION = re.compile(r"\b(status of|is|check|restart|reload)\s+([a-zA-Z0-9_\-\.]+)\b", re.IGNORECASE)
RE_NETWORK = re.compile(r"\b(wifi|wi-fi|bluetooth|bt|radio|ssid|network)\b", re.IGNORECASE)
RE_BATTERY_METRICS = re.compile(r"\b(battery|cpu|ram|memory|health|charge)\b", re.IGNORECASE)
RE_POWER_PROFILES = re.compile(r"\b(power|profile|saver|performance)\b", re.IGNORECASE)
RE_TRASH = re.compile(r"\b(trash|recycle|empty\s+trash|clear\s+trash|bin)\b", re.IGNORECASE)
RE_MATH_WORDS = re.compile(r"\b(calculate|calc|math|arithmetic|eval|evaluate)\b", re.IGNORECASE)
RE_MATH_EXPR = re.compile(r"\d+\s*[\+\-\*\/]\s*\d+")

STOPWORDS = {
    "the", "a", "an", "my", "your", "this", "that", "today", "now",
    "current", "it", "there", "date", "time", "clock", "battery",
    "wifi", "bluetooth", "trash", "cpu", "ram"
}

# Fallback default tools when no specific intent is detected (capped to 3)
FALLBACK_TOOL_NAMES = ["system_health", "get_datetime", "calculator"]


def _is_service_query(q: str) -> bool:
    """Detects if query targets a Linux systemd user service without hardcoding service names."""
    if RE_SERVICE_EXPLICIT.search(q):
        return True
    m = RE_SERVICE_ACTION.search(q)
    if m:
        action = m.group(1).lower()
        target = m.group(2).lower()
        if target not in STOPWORDS and not target.isdigit():
            if action in ["restart", "reload", "status of"]:
                return True
            if re.search(r"\b(running|active|failed|dead|up|down|status)\b", q, re.IGNORECASE):
                return True
    return False


def route_tools(query: str, all_tools: List[Dict[str, Any]], max_tools: int = 4) -> List[Dict[str, Any]]:
    """
    Selects a small subset of relevant tool schemas based on the user's intent.
    Guarantees that FunctionGemma 270M receives no more than max_tools schemas.
    """
    q = query.strip()
    tools_by_name = {t.get("function", {}).get("name"): t for t in all_tools}
    selected_names: List[str] = []

    def _add(name: str):
        if name in tools_by_name and name not in selected_names:
            selected_names.append(name)

    is_math = bool(RE_MATH_WORDS.search(q) or RE_MATH_EXPR.search(q))
    is_datetime = bool(RE_DATETIME.search(q))

    # 1. Math / Calculation (If pure math, isolate to calculator)
    if is_math:
        _add("calculator")
        # If query is purely math, return calculator immediately to prevent interference
        if not (RE_NETWORK.search(q) or RE_BATTERY_METRICS.search(q) or RE_SERVICE_EXPLICIT.search(q)):
            return [tools_by_name["calculator"]]

    # 2. Date & Time
    if is_datetime:
        _add("get_datetime")

    # 3. Network Radios (Wi-Fi & Bluetooth)
    if RE_NETWORK.search(q):
        has_wifi = bool(re.search(r"\b(wifi|wi-fi|ssid|network)\b", q, re.IGNORECASE))
        has_bt = bool(re.search(r"\b(bluetooth|bt)\b", q, re.IGNORECASE))
        if has_wifi and not has_bt:
            _add("toggle_wifi")
        elif has_bt and not has_wifi:
            _add("toggle_bluetooth")
        else:
            _add("toggle_wifi")
            _add("toggle_bluetooth")

    # 4. Systemd Services & Daemons (Skip if math or purely network query)
    if not is_math and _is_service_query(q):
        if re.search(r"\b(restart|reload|reboot)\b", q, re.IGNORECASE):
            _add("restart_service")
            _add("service_status")
        else:
            _add("service_status")
            _add("restart_service")

    # 5. Hardware, Power & Health Metrics
    has_metrics = bool(RE_BATTERY_METRICS.search(q))
    has_power = bool(RE_POWER_PROFILES.search(q))
    if has_metrics or has_power:
        if has_power and not has_metrics:
            _add("power_profile")
            _add("system_health")
        else:
            _add("system_health")
            _add("power_profile")

    # 6. Trash & Housekeeping
    if RE_TRASH.search(q):
        _add("empty_trash")

    # Fallback if no specific cluster matched
    if not selected_names:
        for name in FALLBACK_TOOL_NAMES:
            _add(name)

    # Cap to max_tools to preserve 270M attention budget
    selected_names = selected_names[:max_tools]
    return [tools_by_name[name] for name in selected_names if name in tools_by_name]
