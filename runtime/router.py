"""
router.py — High-speed deterministic intent router and dynamic tool gater.
Filters the active tool catalog down to 2-4 relevant schemas per turn to prevent
cognitive context saturation and attention diffusion on sub-1B models like FunctionGemma 270M.
"""

import re
from typing import List, Dict, Any, Optional

# Compiled regex patterns for intent clusters
RE_DATETIME = re.compile(r"\b(time|date|today|clock|hour|minute|day|month|year|timezone|now)\b", re.IGNORECASE)
RE_SERVICE_EXPLICIT = re.compile(r"\b(service|services|systemd|daemon|daemons|server|servers|process|processes|unit|units|ps|killall|pkill)\b", re.IGNORECASE)
RE_SERVICE_ACTION = re.compile(r"\b(status of|state of|is|check|restart|reload|bounce)\s+([a-zA-Z0-9_\-\.]+)\b", re.IGNORECASE)
RE_NETWORK = re.compile(r"\b(wifi|wi-fi|bluetooth|bluetoothctl|bt|radio|ssid|network|wlan[0-9]*|iwconfig|wireless|interwebs|blue-teeth|internet)\b", re.IGNORECASE)
RE_BATTERY_METRICS = re.compile(r"\b(battery|charge|health|batt|juice)\b", re.IGNORECASE)
RE_CPU_RAM = re.compile(r"\b(cpu|ram|swap|load|core|cores|memory\s+usage|memory\s+status|check\s+memory|hot|warm|overheat|overheating|fan|thermal|thermals|throttling|slow|faster|screaming|rig|heating\s+up|lagging|frozen)\b", re.IGNORECASE)
RE_POWER_PROFILES = re.compile(r"\b(power|profile|profiles|saver|performance|turbostat)\b", re.IGNORECASE)
RE_TRASH = re.compile(r"\b(trash|recycle|recycling|empty\s+trash|clear\s+trash|bin|recycling\s+bin|recycle\s+bin|dustbin|wastebasket|garbo|rubbish|dump|yeet|nuke\s+the\s+trash)\b", re.IGNORECASE)
RE_MATH_WORDS = re.compile(r"\b(calculate|calc|math|arithmetic|eval|evaluate|sum|split|divide|multiply|subtract|add|percent|percentage|convert)\b", re.IGNORECASE)
RE_MATH_EXPR = re.compile(r"\d+\s*[\+\-\*\/]\s*\d+")
RE_RAM_WORDS = re.compile(r"\b(ram|usage|used|free|available|gb|mb|swap)\b", re.IGNORECASE)
RE_MEMORY_WORDS = re.compile(r"\b(remem[a-z]*|remeb[a-z]*|recall[a-z]*|forget[a-z]*|memory|memories|preference|preferences|saved\s+note|saved\s+notes|note|notes|yaad|recuerda|bhool|olvida|confidential\s+note)\b", re.IGNORECASE)
RE_MEMORY_SET_STATEMENT = re.compile(r"\b((my|mah|mera|mi)\s+(?!laptop|computer|pc|wifi|bluetooth|battery|screen|cpu|ram|fan|temp|sound|audio)([a-zA-Z0-9_\-]+\s+){1,3}(is|hai|es|as)|i\s+am|call\s+me|i\s+like|i\s+prefer|save\s+(my|confidential)|set\s+memory|store\s+a\s+note)\b", re.IGNORECASE)
RE_MEMORY_QUERY = re.compile(r"\b(who\s*am\s*i|whoami)\b|(\b(what('s| is| did)|do you remember|do you recall|recall|where is|get my)\b.*\b(my|i|name|distro|editor|preference|favorite|pet|id|code|password|desk|location)\b)", re.IGNORECASE)
RE_TASK = re.compile(r"\b(remind|reminder|reminders|task|tasks|schedule|scheduled|alarm|todo|to-do|\bat\b|meeting|appointment|event|deadline|drop\s+task|cancel\s+task)\b", re.IGNORECASE)
RE_LAUNCH_APP = re.compile(r"\b(launch|open|start|run|fire\s+up|boot\s+up|abre|kholo|arranca|inicia)\s+(app|application|program|gui|tool)?\s*([a-zA-Z0-9_\-\.]+)\b", re.IGNORECASE)

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
    # If query targets network radios, do not treat 'up/down' as systemd service unless service explicit
    has_radio = bool(re.search(r"\b(wifi|wi-fi|bluetooth|bt)\b", q, re.IGNORECASE))
    if has_radio and not re.search(r"\b(service|systemd|daemon|unit)\b", q, re.IGNORECASE):
        return False
    for m in RE_SERVICE_ACTION.finditer(q):
        action = m.group(1).lower()
        target = m.group(2).lower()
        if target not in STOPWORDS and not target.isdigit():
            if action in ["restart", "reload", "status of", "state of", "bounce"]:
                return True
            if re.search(r"\b(running|active|failed|dead|up|down|status)\b", q, re.IGNORECASE):
                return True
    return False


def route_tools(
    query: str,
    all_tools: List[Dict[str, Any]],
    max_tools: int = 4,
    history: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Selects a small subset of relevant tool schemas based on the user's intent.
    Guarantees that FunctionGemma 270M receives no more than max_tools schemas.
    When history is provided, resolves anaphoric follow-up queries contextually.
    """
    q = query.strip()
    tools_by_name = {t.get("function", {}).get("name"): t for t in all_tools}
    selected_names: List[str] = []

    def _add(name: str):
        if name in tools_by_name and name not in selected_names:
            selected_names.append(name)

    # Sanitize ISO dates (e.g. 2026-09-20, 2026/09/20) so hyphens are not captured as arithmetic subtraction
    q_no_dates = re.sub(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", " ", q)
    q_no_dates = re.sub(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", " ", q_no_dates)

    is_calc_app_launch = bool(re.search(r"\b(launch|open|start|run|fire\s+up|boot\s+up)\s+(app\s+)?calc\b", q, re.IGNORECASE))
    is_math = bool(RE_MATH_WORDS.search(q) or RE_MATH_EXPR.search(q_no_dates)) and not is_calc_app_launch
    is_datetime = bool(RE_DATETIME.search(q))

    # 1. Math / Calculation (If pure math without other intents, isolate to calculator)
    if is_math:
        _add("calculator")
        has_other_intent = bool(
            is_datetime or
            RE_TASK.search(q) or
            RE_LAUNCH_APP.search(q) or
            RE_NETWORK.search(q) or
            RE_BATTERY_METRICS.search(q) or
            RE_SERVICE_EXPLICIT.search(q) or
            RE_MEMORY_WORDS.search(q)
        )
        if not has_other_intent:
            return [tools_by_name["calculator"]]

    # 2. Date & Time
    if is_datetime:
        _add("get_datetime")

    # 3. Network Radios (Wi-Fi & Bluetooth)
    # Exclude if query is about a password note/memory
    is_password_memory = bool(re.search(r"\b(password|passphrase|code|secret|gateway\s+ip)\b", q, re.IGNORECASE))
    if RE_NETWORK.search(q) and not is_password_memory:
        has_wifi = bool(re.search(r"\b(wifi|wi-fi|ssid|network|wireless|interwebs)\b", q, re.IGNORECASE))
        has_bt = bool(re.search(r"\b(bluetooth|bt|blue-teeth)\b", q, re.IGNORECASE))
        if has_wifi and not has_bt:
            _add("toggle_wifi")
        elif has_bt and not has_wifi:
            _add("toggle_bluetooth")
        else:
            _add("toggle_wifi")
            _add("toggle_bluetooth")

    # 4. Systemd Services & Daemons (Skip if pure math)
    if not is_math and _is_service_query(q):
        if re.search(r"\b(restart|reload|reboot|killall|pkill|bounce|reinicia|maro)\b", q, re.IGNORECASE):
            _add("restart_service")
            _add("service_status")
        else:
            _add("service_status")
            _add("restart_service")

    # 5. Hardware, Power & Health Metrics
    has_cpu_ram = bool(RE_CPU_RAM.search(q))
    has_battery = bool(re.search(r"\b(battery|charge|batt|juice)\b", q, re.IGNORECASE))
    has_power = bool(RE_POWER_PROFILES.search(q))
    has_generic_health = bool(re.search(r"\b(health|system\s+health)\b", q, re.IGNORECASE))

    if (has_cpu_ram or has_battery) and not has_power:
        _add("system_health")
    elif has_power and not has_cpu_ram and not has_battery:
        _add("power_profile")
    elif has_generic_health or has_power or has_battery or has_cpu_ram:
        _add("system_health")
        if has_power:
            _add("power_profile")

    # 6. Trash & Housekeeping
    if RE_TRASH.search(q):
        _add("empty_trash")

    # 7. User Memory & Personalization
    has_ram = bool(RE_RAM_WORDS.search(q))
    has_explicit_memory_prefix = bool(re.search(r"\b(set\s+memory|remember\s+that|save\s+.*note|store\s+.*note|save\s+my|recall|confidential\s+note|what\s+is\s+the\s+.*password)\b", q, re.IGNORECASE))
    is_hardware_state = bool(re.search(r"\b(is\s+running\s+hot|is\s+hot|is\s+warm|is\s+slow|is\s+lagging|is\s+overheating)\b", q, re.IGNORECASE))

    is_mem = (
        bool(RE_MEMORY_WORDS.search(q)) or
        bool(RE_MEMORY_SET_STATEMENT.search(q)) or
        bool(RE_MEMORY_QUERY.search(q)) or
        has_explicit_memory_prefix
    ) and not has_ram and not is_hardware_state

    # Guard against generic hardware descriptions triggering memory unless explicitly prefixed
    if is_mem and not has_explicit_memory_prefix:
        if any(k in q.lower() for k in ["battery", "cpu", "power", "wifi", "bluetooth", "date", "time", "screen", "fan", "temp", "hot", "process", "processes"]):
            is_mem = False

    if is_mem:
        if re.search(r"\b(forget|delete|remove|clear|bhool|olvida)\b", q, re.IGNORECASE):
            _add("memory_delete")
        elif re.search(r"\b(list|all|show|notes)\b", q, re.IGNORECASE):
            _add("memory_list")
        elif re.search(r"\b(what|recall|get|lookup|look up|who|where)\b", q, re.IGNORECASE):
            _add("memory_get")
        elif re.search(r"\b(remember|save|set|store|note|yaad|recuerda)\b", q, re.IGNORECASE) or bool(RE_MEMORY_SET_STATEMENT.search(q)):
            _add("memory_set")
        else:
            _add("memory_set")
            _add("memory_get")

    # 8. Scheduled Tasks & Reminders
    if RE_TASK.search(q):
        if re.search(r"\b(cancel|delete|remove|done|finish|drop|stop|cancela|borra|hatao)\b", q, re.IGNORECASE):
            _add("task_cancel")
            _add("task_list")
        elif re.search(r"\b(list|all|show|pending|display|upcoming)\b", q, re.IGNORECASE):
            _add("task_list")
            _add("task_add")
        else:
            _add("task_add")
            _add("task_list")

    # 9. App Launcher
    if RE_LAUNCH_APP.search(q) or is_calc_app_launch:
        _add("launch_app")

    # 10. Multi-Turn Anaphora Resolution (Contextual fallback bridge)
    if history and (not selected_names or selected_names == FALLBACK_TOOL_NAMES):
        last_tool = None
        for msg in reversed(history):
            if msg.get("role") == "tool" and msg.get("name"):
                last_tool = msg.get("name")
                break
            tool_calls = msg.get("tool_calls") or msg.get("message", {}).get("tool_calls")
            if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
                last_tool = tool_calls[0].get("function", {}).get("name")
                break

        if last_tool:
            has_pronoun = bool(re.search(r"\b(it|that|them|again|this|now)\b", q, re.IGNORECASE))
            if last_tool in ["service_status", "restart_service"] and (has_pronoun or re.search(r"\b(restart|reload|status|check|bounce|kill|stop)\b", q, re.IGNORECASE)):
                selected_names = []
                _add("restart_service")
                _add("service_status")
            elif last_tool in ["toggle_wifi", "toggle_bluetooth"] and (has_pronoun or re.search(r"\b(turn|disable|enable|off|on|toggle)\b", q, re.IGNORECASE)):
                selected_names = []
                _add(last_tool)
            elif last_tool == "power_profile" and (has_pronoun or re.search(r"\b(saving|profile|switch|turn|saver)\b", q, re.IGNORECASE)):
                selected_names = []
                _add("power_profile")
            elif last_tool == "calculator" and (has_pronoun or re.search(r"\b(multiply|divide|add|subtract|take\s+away)\b", q, re.IGNORECASE)):
                selected_names = []
                _add("calculator")
            elif last_tool == "empty_trash" and (has_pronoun or re.search(r"\b(did|clean|done)\b", q, re.IGNORECASE)):
                selected_names = []
                _add("empty_trash")
            elif last_tool in ["task_add", "task_list"] and (has_pronoun or re.search(r"\b(cancel|stop|remove)\b", q, re.IGNORECASE)):
                selected_names = []
                _add("task_cancel")
                _add("task_list")

    # Fallback if no specific cluster matched
    if not selected_names:
        for name in FALLBACK_TOOL_NAMES:
            _add(name)

    # Cap to max_tools to preserve 270M attention budget
    selected_names = selected_names[:max_tools]
    return [tools_by_name[name] for name in selected_names if name in tools_by_name]
