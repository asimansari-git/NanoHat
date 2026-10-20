"""
tools.py - 10-tool Fedora Workstation onboarding catalog with strict JSON schemas.
"""

SYSTEM_HEALTH_TOOL = {
    "type": "function",
    "function": {
        "name": "system_health",
        "description": "Check Linux hardware telemetry: CPU load percentage, RAM usage, or battery charge level.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["battery", "ram", "cpu", "all"],
                    "description": "Telemetry metric to inspect: 'battery', 'ram', 'cpu', or 'all'."
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
        "description": "Inspect or switch the system energy profile (power-saver, balanced, performance). Do NOT use for battery percentage or CPU load.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set"],
                    "description": "'get' to check active profile; 'set' to change profile."
                },
                "profile": {
                    "type": "string",
                    "enum": ["power-saver", "balanced", "performance"],
                    "description": "Target profile when action is 'set'."
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
        "description": "Inspect or toggle Wi-Fi radio status via NetworkManager. Use state='status' for questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["status", "on", "off", "toggle"],
                    "description": "'status' to check if enabled; 'on' to enable; 'off' to disable; 'toggle' to flip."
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
        "description": "Inspect or toggle Bluetooth adapter power via BlueZ. Use state='status' for questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["status", "on", "off", "toggle"],
                    "description": "'status' to check if enabled; 'on' to enable; 'off' to disable; 'toggle' to flip."
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
        "description": "Check if a systemd user or system service is active, inactive, or failed (e.g. 'pipewire', 'wireplumber', 'ollama', 'sshd').",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the systemd service unit."
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
                    "description": "Name of the allowlisted user service to restart."
                }
            },
            "required": ["service_name"]
        }
    }
}

AUDIO_CONTROL_TOOL = {
    "type": "function",
    "function": {
        "name": "audio_control",
        "description": "Inspect or control PipeWire audio volume and mute state via wpctl.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["status", "mute", "unmute", "set_volume"],
                    "description": "'status' to get volume; 'mute'/'unmute' to toggle audio; 'set_volume' to set percentage."
                },
                "level": {
                    "type": "integer",
                    "description": "Volume percentage (0 to 100) when action is 'set_volume'."
                }
            },
            "required": ["action"]
        }
    }
}

DESKTOP_APPEARANCE_TOOL = {
    "type": "function",
    "function": {
        "name": "desktop_appearance",
        "description": "Inspect or change Fedora GNOME desktop color scheme (dark/light mode) or night light.",
        "parameters": {
            "type": "object",
            "properties": {
                "setting": {
                    "type": "string",
                    "enum": ["theme", "night_light"],
                    "description": "'theme' for dark/light mode; 'night_light' for blue-light filter."
                },
                "value": {
                    "type": "string",
                    "enum": ["status", "dark", "light", "on", "off"],
                    "description": "'status' to inspect; 'dark'/'light' for theme; 'on'/'off' for night_light."
                }
            },
            "required": ["setting", "value"]
        }
    }
}

DISK_USAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "disk_usage",
        "description": "Check free and used disk storage space on a filesystem path (e.g. '/' or '/home').",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Mount point or directory path to inspect (defaults to '/')."
                }
            },
            "required": ["path"]
        }
    }
}

PACKAGE_MANAGER_TOOL = {
    "type": "function",
    "function": {
        "name": "package_manager",
        "description": "Search for, check installed status, or stage installation of software packages on Fedora using dnf or flatpak.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "is_installed", "install_cmd"],
                    "description": "'search' to find packages; 'is_installed' to verify if installed; 'install_cmd' to prepare installation."
                },
                "package_name": {
                    "type": "string",
                    "description": "Name of the application or package (e.g. 'vlc', 'htop', 'code')."
                },
                "provider": {
                    "type": "string",
                    "enum": ["dnf", "flatpak"],
                    "description": "Package manager backend ('dnf' for system RPMs, 'flatpak' for desktop GUI apps)."
                }
            },
            "required": ["action", "package_name"]
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
    AUDIO_CONTROL_TOOL,
    DESKTOP_APPEARANCE_TOOL,
    DISK_USAGE_TOOL,
    PACKAGE_MANAGER_TOOL,
]