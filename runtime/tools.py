"""
tools.py — Function calling declarations and JSON schemas for fuge-nanohat.
Formatted according to the standard OpenAI / Ollama tool specification.
"""

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform mathematical calculations, arithmetic, and expressions (e.g. 15 * 800, (45 + 10) / 2, 2**8).",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate, e.g. '15 * 800' or '2 ** 10'."
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
        "description": "Get current Linux system metrics including CPU utilization, RAM usage, and battery state.",
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
    SYSTEM_HEALTH_TOOL
]
