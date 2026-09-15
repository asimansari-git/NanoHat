"""
tools.py — Function calling declarations and JSON schemas for fuge-nanohat.
Formatted according to the standard OpenAI / Ollama tool specification.
"""

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform mathematical calculations and arithmetic expressions.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The exact mathematical expression to evaluate (e.g. 7+7*18)."
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
        "description": "Check Linux operating system metrics: RAM usage, CPU utilization, or battery status.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metric to query: 'ram' for RAM or memory usage, 'cpu' for CPU utilization, 'battery' for battery status, or 'all'. Defaults to 'all'."
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

TOGGLE_WIFI_TOOL = {
    "type": "function",
    "function": {
        "name": "toggle_wifi",
        "description": "Check Wi-Fi radio status or turn Wi-Fi on, off, or toggle.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "Action: 'status' (to check status), 'on', 'off', or 'toggle'. Defaults to 'status'."
                }
            },
            "required": []
        }
    }
}

TOGGLE_BLUETOOTH_TOOL = {
    "type": "function",
    "function": {
        "name": "toggle_bluetooth",
        "description": "Check Bluetooth radio status or turn Bluetooth on, off, or toggle.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "Action: 'status' (to check status), 'on', 'off', or 'toggle'. Defaults to 'status'."
                }
            },
            "required": []
        }
    }
}

SERVICE_STATUS_TOOL = {
    "type": "function",
    "function": {
        "name": "service_status",
        "description": "Check the status or running state of a service, daemon, server, or program (e.g. ollama, pipewire, tailscale).",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service, daemon, or server to check (e.g. ollama, pipewire, tailscale)."
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
                    "description": "Name of the service to restart (e.g. pipewire, wireplumber)."
                }
            },
            "required": ["service_name"]
        }
    }
}

MEMORY_SET_TOOL = {
    "type": "function",
    "function": {
        "name": "memory_set",
        "description": "Save a key-value memory, user name, preference, or note to persistent memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The memory key or label (e.g. 'name', 'favorite_distro', 'editor')."
                },
                "value": {
                    "type": "string",
                    "description": "The value or information to remember (e.g. 'Asim', 'Fedora Workstation')."
                }
            },
            "required": ["key", "value"]
        }
    }
}

MEMORY_GET_TOOL = {
    "type": "function",
    "function": {
        "name": "memory_get",
        "description": "Retrieve stored user data, name, identity, settings, or preferences from memory by key.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Key to look up in memory (e.g. 'name', 'favorite_distro', 'shell', 'editor')."
                }
            },
            "required": ["key"]
        }
    }
}

MEMORY_LIST_TOOL = {
    "type": "function",
    "function": {
        "name": "memory_list",
        "description": "List all stored user memories, preferences, and saved notes.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

MEMORY_DELETE_TOOL = {
    "type": "function",
    "function": {
        "name": "memory_delete",
        "description": "Delete or forget a saved memory by key.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key of the memory to delete."
                }
            },
            "required": ["key"]
        }
    }
}

TASK_ADD_TOOL = {
    "type": "function",
    "function": {
        "name": "task_add",
        "description": "Schedule a task, reminder, or to-do item with a title and optional due time.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The task title, alert, or reminder description."
                },
                "due_time": {
                    "type": "string",
                    "description": "When the task is due (e.g. '5pm', 'tomorrow at 10am', 'Friday'). Defaults to 'today'."
                }
            },
            "required": ["title"]
        }
    }
}

TASK_LIST_TOOL = {
    "type": "function",
    "function": {
        "name": "task_list",
        "description": "List scheduled tasks (filter by 'pending', 'completed', 'cancelled', or 'all').",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Status filter: 'pending', 'completed', 'cancelled', or 'all'. Defaults to 'pending'."
                }
            },
            "required": []
        }
    }
}

TASK_CANCEL_TOOL = {
    "type": "function",
    "function": {
        "name": "task_cancel",
        "description": "Cancel a scheduled task or reminder by its integer task ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The integer ID of the task to cancel."
                }
            },
            "required": ["task_id"]
        }
    }
}

# Master tools catalog
ALL_TOOLS = [
    CALCULATOR_TOOL,
    SYSTEM_HEALTH_TOOL,
    POWER_PROFILE_TOOL,
    GET_DATETIME_TOOL,
    EMPTY_TRASH_TOOL,
    TOGGLE_WIFI_TOOL,
    TOGGLE_BLUETOOTH_TOOL,
    SERVICE_STATUS_TOOL,
    RESTART_SERVICE_TOOL,
    MEMORY_SET_TOOL,
    MEMORY_GET_TOOL,
    MEMORY_LIST_TOOL,
    MEMORY_DELETE_TOOL,
    TASK_ADD_TOOL,
    TASK_LIST_TOOL,
    TASK_CANCEL_TOOL
]



