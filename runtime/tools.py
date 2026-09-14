"""
tools.py — Function calling declarations and JSON schemas for fuge-nanohat.
Formatted according to the standard OpenAI / Ollama tool specification.
"""

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform mathematical calculations, arithmetic, and expressions.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate."
                }
            },
            "required": ["expression"]
        }
    }
}

SYSTEM_HEALTH_TOOL = {
    "type": "function",
    "function": {
        "name": "system_health",
        "description": "Check Linux operating system metrics: battery status, battery level, CPU utilization, and RAM usage.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Optional specific metric: 'battery', 'cpu', 'ram', or 'all'. Defaults to 'all'."
                }
            },
            "required": []
        }
    }
}

POWER_PROFILE_TOOL = {
    "type": "function",
    "function": {
        "name": "power_profile",
        "description": "Get or set the Linux system power profile (power-saver, balanced, performance) using powerprofilesctl.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'get' to view the active power profile, or 'set' to change it. Defaults to 'get'."
                },
                "profile": {
                    "type": "string",
                    "description": "Target profile when action is 'set': 'power-saver', 'balanced', or 'performance'."
                }
            },
            "required": ["action"]
        }
    }
}

GET_DATETIME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_datetime",
        "description": "Get current system date, time, day of the week, and timezone on Linux.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

EMPTY_TRASH_TOOL = {
    "type": "function",
    "function": {
        "name": "empty_trash",
        "description": "Permanently empty and clear the user trash bin on Linux. Requires user confirmation.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

# Master tools catalog
ALL_TOOLS = [
    CALCULATOR_TOOL,
    SYSTEM_HEALTH_TOOL,
    POWER_PROFILE_TOOL,
    GET_DATETIME_TOOL,
    EMPTY_TRASH_TOOL
]


