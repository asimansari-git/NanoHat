"""
functions.py - Pure Python Linux OS execution backends for NanoHat v3.1.
Locked to 6 core tools: system_health, power_profile, toggle_wifi,
toggle_bluetooth, service_status, and restart_service.
"""
import os
import shutil
import subprocess
from typing import Optional
import psutil

# ---------------------------------------------------------------------------
# 1. Hardware Telemetry & Health Checks
# ---------------------------------------------------------------------------

def system_health(metric: str = "all") -> str:
    """Returns current Linux system telemetry: CPU percent, RAM usage, and battery status."""
    try:
        metric_norm = (metric or "all").strip().lower()

        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        ram_used_gb = round(mem.used / (1024 ** 3), 2)
        ram_total_gb = round(mem.total / (1024 ** 3), 2)
        ram_pct = mem.percent

        batt = psutil.sensors_battery()
        if batt:
            batt_pct = int(round(batt.percent))
            state = "charging" if batt.power_plugged else "discharging"
            batt_str = f"{batt_pct}% ({state})"
        else:
            batt_str = "No battery detected"

        if "batt" in metric_norm:
            return f"Battery: {batt_str}"
        elif "cpu" in metric_norm:
            return f"CPU: {cpu}%"
        elif "ram" in metric_norm or "mem" in metric_norm:
            return f"RAM: {ram_used_gb}GB / {ram_total_gb}GB ({ram_pct}%)"
        else:
            return f"CPU: {cpu}% | RAM: {ram_used_gb}GB / {ram_total_gb}GB ({ram_pct}%) | Battery: {batt_str}"
    except Exception as e:
        return f"Error querying system health: {e}"


# ---------------------------------------------------------------------------
# 2. Power Profile Management
# ---------------------------------------------------------------------------

VALID_POWER_PROFILES = {"power-saver", "balanced", "performance"}

def power_profile(action: str = "get", profile: Optional[str] = None) -> str:
    """Gets or sets the Linux system power profile via powerprofilesctl."""
    binary = shutil.which("powerprofilesctl")
    if not binary:
        return "Error: powerprofilesctl is not installed on this system."

    action_norm = (action or "get").strip().lower()
    if action_norm in {"get", "status"} or (action_norm == "set" and not profile):
        try:
            res = subprocess.run([binary, "get"], capture_output=True, text=True, check=True)
            return f"Current power profile: {res.stdout.strip()}"
        except subprocess.CalledProcessError as e:
            return f"Error getting power profile: {e.stderr.strip() or str(e)}"
    elif action_norm == "set":
        if not profile or profile.strip().lower() not in VALID_POWER_PROFILES:
            return f"Error: Invalid profile '{profile}'. Choose from: {', '.join(sorted(VALID_POWER_PROFILES))}"
        target = profile.strip().lower()
        try:
            subprocess.run([binary, "set", target], capture_output=True, text=True, check=True)
            return f"Power profile set to: {target}"
        except subprocess.CalledProcessError as e:
            return f"Error setting power profile: {e.stderr.strip() or str(e)}"
    else:
        return f"Error: Unsupported action '{action}'. Use 'get' or 'set'."


# ---------------------------------------------------------------------------
# 3. Wireless Radios (Wi-Fi & Bluetooth)
# ---------------------------------------------------------------------------

def toggle_wifi(state: Optional[str] = None, action: Optional[str] = None) -> str:
    """Checks Wi-Fi status, turns Wi-Fi on or off, or toggles connection via nmcli."""
    target = (state or action or "status").strip().lower()
    nmcli_bin = shutil.which("nmcli")
    if not nmcli_bin:
        return "Error: nmcli binary not found on this system."

    try:
        if target in {"status", "check", "get"}:
            res = subprocess.run([nmcli_bin, "radio", "wifi"], capture_output=True, text=True)
            enabled = res.stdout.strip() == "enabled"
            return "Yes, Wi-Fi radio is enabled." if enabled else "No, Wi-Fi radio is disabled."
        elif target in {"on", "enable", "enabled"}:
            subprocess.run([nmcli_bin, "radio", "wifi", "on"], capture_output=True, text=True, check=True)
            return "Wi-Fi radio turned on."
        elif target in {"off", "disable", "disabled"}:
            subprocess.run([nmcli_bin, "radio", "wifi", "off"], capture_output=True, text=True, check=True)
            return "Wi-Fi radio turned off."
        elif target in {"toggle", "flip"}:
            res = subprocess.run([nmcli_bin, "radio", "wifi"], capture_output=True, text=True)
            current = res.stdout.strip()
            new_state = "off" if current == "enabled" else "on"
            subprocess.run([nmcli_bin, "radio", "wifi", new_state], capture_output=True, text=True, check=True)
            return f"Wi-Fi toggled from {current} to {new_state}."
        else:
            return f"Error: Unsupported Wi-Fi action '{target}'. Use 'on', 'off', 'toggle', or 'status'."
    except subprocess.CalledProcessError as e:
        return f"Error managing Wi-Fi radio: {e.stderr.strip() or str(e)}"

def toggle_bluetooth(state: Optional[str] = None, action: Optional[str] = None) -> str:
    """Checks Bluetooth status, turns Bluetooth on or off, or toggles power via bluetoothctl."""
    target = (state or action or "status").strip().lower()
    bt_bin = shutil.which("bluetoothctl")
    if not bt_bin:
        return "Error: bluetoothctl binary not found on this system."

    def _is_powered() -> bool:
        res = subprocess.run([bt_bin, "show"], capture_output=True, text=True)
        return "Powered: yes" in res.stdout

    try:
        if target in {"status", "check", "get"}:
            powered = _is_powered()
            return "Yes, Bluetooth is powered on." if powered else "No, Bluetooth is powered off."
        elif target in {"on", "enable", "enabled"}:
            subprocess.run([bt_bin, "power", "on"], capture_output=True, text=True, check=True)
            return "Bluetooth powered on."
        elif target in {"off", "disable", "disabled"}:
            subprocess.run([bt_bin, "power", "off"], capture_output=True, text=True, check=True)
            return "Bluetooth powered off."
        elif target in {"toggle", "flip"}:
            powered = _is_powered()
            new_state = "off" if powered else "on"
            subprocess.run([bt_bin, "power", new_state], capture_output=True, text=True, check=True)
            return f"Bluetooth toggled from {'on' if powered else 'off'} to {new_state}."
        else:
            return f"Error: Unsupported Bluetooth action '{target}'. Use 'on', 'off', 'toggle', or 'status'."
    except subprocess.CalledProcessError as e:
        return f"Error managing Bluetooth adapter: {e.stderr.strip() or str(e)}"


# ---------------------------------------------------------------------------
# 4. Systemd Daemons & Service Management
# ---------------------------------------------------------------------------

SAFE_RESTART_SERVICES = {
    "pipewire",
    "pipewire.service",
    "pipewire-pulse",
    "pipewire-pulse.service",
    "wireplumber",
    "wireplumber.service",
    "xdg-desktop-portal",
    "xdg-desktop-portal.service",
    "xdg-desktop-portal-gnome",
    "xdg-desktop-portal-gnome.service",
    "ollama",
    "ollama.service",
}

BLOCKED_WAYLAND_SERVICES = {
    "gnome-shell",
    "gnome-shell.service",
    "org.gnome.shell",
    "org.gnome.shell@wayland",
    "gdm",
    "gdm.service",
    "wayland",
}

def service_status(
    service_name: Optional[str] = None,
    name: Optional[str] = None,
    service: Optional[str] = None,
    unit: Optional[str] = None
) -> str:
    """Inspects whether a systemd user or system service is active, inactive, or failed."""
    svc = (service_name or name or service or unit or "").strip()
    if not svc:
        return "Error: Please specify the service name to inspect (e.g. 'pipewire', 'wireplumber')."
    clean = os.path.basename(svc)
    target_unit = clean if "." in clean else f"{clean}.service"
    sys_bin = shutil.which("systemctl")
    if not sys_bin:
        return "Error: systemctl binary not found on this system."

    # 1. User scope check
    res = subprocess.run([sys_bin, "--user", "is-active", target_unit], capture_output=True, text=True)
    status = res.stdout.strip()
    if status == "active":
        return f"Systemd user service '{target_unit}' status: active"

    # 2. System scope check
    sys_res = subprocess.run([sys_bin, "is-active", target_unit], capture_output=True, text=True)
    sys_status = sys_res.stdout.strip()
    if sys_status == "active":
        return f"Systemd system service '{target_unit}' status: active"

    # 3. Check daemon 'd' suffix (e.g., tailscale -> tailscaled.service)
    if not clean.endswith("d"):
        d_unit = f"{clean}d.service"
        d_res = subprocess.run([sys_bin, "is-active", d_unit], capture_output=True, text=True)
        if d_res.stdout.strip() == "active":
            return f"Systemd system service '{d_unit}' status: active"

    return f"Systemd service '{target_unit}' status: {status or sys_status or 'inactive'}"


def restart_service(
    service_name: Optional[str] = None,
    name: Optional[str] = None,
    service: Optional[str] = None,
    unit: Optional[str] = None
) -> str:
    """Restarts an allowlisted systemd user service. Desktop session targets are strictly blocked."""
    svc = (service_name or name or service or unit or "").strip().lower()
    if not svc:
        return "Error: Please specify the service name to restart (e.g. 'pipewire', 'wireplumber')."
    if "/" in svc or "\\" in svc or ".." in svc:
        return f"ERROR[security_blocked]: Path traversal or slashes in service name '{svc}' are strictly blocked."
    clean = os.path.basename(svc)
    if clean in BLOCKED_WAYLAND_SERVICES:
        return f"ERROR[security_blocked]: Restarting '{clean}' is strictly blocked to prevent Wayland desktop session crashes."
    if clean not in SAFE_RESTART_SERVICES:
        allowed = ", ".join(sorted(set(s.replace(".service", "") for s in SAFE_RESTART_SERVICES)))
        return f"ERROR[security_blocked]: Service '{clean}' is not in the safe allowlist. Safe services: {allowed}"

    clean_unit = clean if "." in clean else f"{clean}.service"
    sys_bin = shutil.which("systemctl")
    if not sys_bin:
        return "Error: systemctl binary not found on this system."
    try:
        subprocess.run([sys_bin, "--user", "restart", clean_unit], capture_output=True, text=True, check=True)
        return f"Service '{clean_unit}' restarted successfully."
    except subprocess.CalledProcessError as e:
        return f"Error restarting service '{clean_unit}': {e.stderr.strip() or str(e)}"


# ---------------------------------------------------------------------------
# 5. Tool Dispatch Registry
# ---------------------------------------------------------------------------

REGISTRY = {
    "system_health": system_health,
    "power_profile": power_profile,
    "toggle_wifi": toggle_wifi,
    "toggle_bluetooth": toggle_bluetooth,
    "service_status": service_status,
    "restart_service": restart_service,
}