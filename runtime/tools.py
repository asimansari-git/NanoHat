"""
tools.py - Hardened 6-tool catalog with negative constraints and strict parameter boundaries.
"""

SYSTEM_HEALTH_TOOL = {
    "type": "function",
    "function": {
        "name": "system_health",
        "description": "Check Linux telemetry: CPU load/utilization percentage, RAM/memory usage, or battery level/percentage. Use for questions about how much battery, RAM, or CPU load remains.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["battery", "ram", "cpu", "all"],
                    "description": "Specific telemetry metric: 'battery', 'ram', 'cpu', or 'all'."
                }
            },
            "required": ["metric"]
        }
    }
}

POWER_PROFILE_TOOL = {
    "type": "function",
    "function": {
        "name": "power_profile",
        "description": "Switch or inspect the system energy profile (power-saver, balanced, performance) using powerprofilesctl. Do NOT use for CPU load, RAM usage, or battery percentage.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set"],
                    "description": "Use 'get' to check active profile; use 'set' to switch profiles."
                },
                "profile": {
                    "type": "string",
                    "enum": ["power-saver", "balanced", "performance"],
                    "description": "Required when action is 'set': 'power-saver', 'balanced', or 'performance'."
                }
            },
            "required": ["action"]
        }
    }
}

TOGGLE_WIFI_TOOL = {
    "type": "function",
    "function": {
        "name": "toggle_wifi",
        "description": "Inspect or toggle Wi-Fi radio status via nmcli. For questions like 'Is Wi-Fi on?', state MUST be 'status'.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["status", "on", "off", "toggle"],
                    "description": "'status' to inspect if enabled; 'on' to enable; 'off' to disable; 'toggle' to flip."
                }
            },
            "required": ["state"]
        }
    }
}

TOGGLE_BLUETOOTH_TOOL = {
    "type": "function",
    "function": {
        "name": "toggle_bluetooth",
        "description": "Inspect or toggle Bluetooth adapter status via bluetoothctl. For questions like 'Is Bluetooth on?', state MUST be 'status'.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["status", "on", "off", "toggle"],
                    "description": "'status' to inspect if enabled; 'on' to enable; 'off' to disable; 'toggle' to flip."
                }
            },
            "required": ["state"]
        }
    }
}

SERVICE_STATUS_TOOL = {
    "type": "function",
    "function": {
        "name": "service_status",
        "description": "Check if a systemd service or daemon is active, inactive, or failed (e.g. 'pipewire', 'wireplumber', 'ollama').",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Exact name of the service (e.g. 'pipewire', 'wireplumber', 'ollama')."
                }
            },
            "required": ["service_name"]
        }
    }
}

RESTART_SERVICE_TOOL = {
    "type": "function",
    "function": {
        "name": "restart_service",
        "description": "Restart an allowlisted systemd user service (pipewire, wireplumber, xdg-desktop-portal, ollama).",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to restart (e.g. 'pipewire', 'wireplumber')."
                }
            },
            "required": ["service_name"]
        }
    }
}

ALL_TOOLS = [
    SYSTEM_HEALTH_TOOL,
    POWER_PROFILE_TOOL,
    TOGGLE_WIFI_TOOL,
    TOGGLE_BLUETOOTH_TOOL,
    SERVICE_STATUS_TOOL,
    RESTART_SERVICE_TOOL,
]