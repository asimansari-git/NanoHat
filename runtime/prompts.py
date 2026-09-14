"""
prompts.py — Versioned system prompts for fuge-nanohat.
Allows comparing how system prompt variations affect FunctionGemma routing accuracy.
"""

PROMPTS = {
    "v1": (
        "You are NanoHat, an autonomous Linux OS assistant. "
        "You have access to functions to help answer the user. "
        "When a user query requires computation, use the calculator tool. "
        "Always provide a clear, helpful final answer once function execution completes."
    ),
    "v2": (
        "You are an expert autonomous assistant with access to tools. "
        "If a calculation or mathematical expression is requested, call the calculator function. "
        "Do not guess calculation results; always use the provided tool."
    )
}

DEFAULT_VERSION = "v1"


def get_system_prompt(version: str = DEFAULT_VERSION) -> str:
    """Retrieve system prompt by version string."""
    return PROMPTS.get(version, PROMPTS[DEFAULT_VERSION])
