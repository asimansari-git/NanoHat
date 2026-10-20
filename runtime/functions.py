"""
functions.py - Pure Python Linux OS execution backends for NanoHat v4.0 (Fedora Workstation).
"""
import os
import re
import shutil
import subprocess
from typing import Optional, Dict
import psutil

def _clean_env() -> Dict[str, str]:
    """Ensure English/POSIX stdout across all locales for reliable CLI parsing."""
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    return env

def _is_sandbox() -> bool:
    """When NANOHAT_SANDBOX=1, execute read-only checks live but dry-run state-mutating OS commands."""
    return os.environ.get("NANOHAT_SANDBOX", "0").strip() in {"1", "true", "yes"}

# ---------------------------------------------------------------------------
# 1. Hardware Telemetry & Health Checks
# ---------------------------------------------------------------------------

def system_health(metric: str = "all") -> str:
    """Returns current Linux system telemetry: CPU percent (+ temp), RAM usage, and battery status."""
    try:
        metric_norm = (metric or "all").strip().lower()

        def _get_cpu_str() -> str:
            cpu = psutil.cpu_percent(interval=0.1)
            temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
            for sensor_name in ("coretemp", "k10temp", "acpitz", "cpu_thermal"):
                if sensor_name in temps and temps[sensor_name]:
                    current_temp = temps[sensor_name][0].current
                    return f"CPU: {cpu}% ({current_temp:.1f}°C)"
            return f"CPU: {cpu}%"

        if "batt" in metric_norm:
            batt = psutil.sensors_battery()
            if not batt:
                return "Battery: No battery detected"
            state = "charging" if batt.power_plugged else "discharging"
            return f"Battery: {int(round(batt.percent))}% ({state})"

        if "cpu" in metric_norm:
            return _get_cpu_str()

        if "ram" in metric_norm or "mem" in metric_norm:
            mem = psutil.virtual_memory()
            return f"RAM: {round(mem.used / (1024 ** 3), 2)}GB / {round(mem.total / (1024 ** 3), 2)}GB ({mem.percent}%)"

        mem = psutil.virtual_memory()
        batt = psutil.sensors_battery()
        batt_str = f"{int(round(batt.percent))}% ({'charging' if batt.power_plugged else 'discharging'})" if batt else "No battery detected"
        return f"{_get_cpu_str()} | RAM: {round(mem.used / (1024 ** 3), 2)}GB / {round(mem.total / (1024 ** 3), 2)}GB ({mem.percent}%) | Battery: {batt_str}"
    except Exception as e:
        return f"Error querying system health: {e}"

# ---------------------------------------------------------------------------
# 2. Power Profile Management
# ---------------------------------------------------------------------------

VALID_POWER_PROFILES = {"power-saver", "balanced", "performance"}

def power_profile(action: str = "get", profile: Optional[str] = None) -> str:
    """Gets or sets the Linux system power profile via powerprofilesctl."""
    binary = shutil.which("powerprofilesctl")
    if not binary and not _is_sandbox():
        return "Error: powerprofilesctl is not installed on this system."

    action_norm = (action or "get").strip().lower()
    if action_norm in {"get", "status"} or (action_norm == "set" and not profile):
        if not binary:
            return "Current power profile: balanced"
        try:
            res = subprocess.run([binary, "get"], capture_output=True, text=True, check=True, env=_clean_env())
            return f"Current power profile: {res.stdout.strip()}"
        except subprocess.CalledProcessError as e:
            return f"Error getting power profile: {e.stderr.strip() or str(e)}"
    elif action_norm == "set":
        if not profile or profile.strip().lower() not in VALID_POWER_PROFILES:
            return f"Error: Invalid profile '{profile}'. Choose from: {', '.join(sorted(VALID_POWER_PROFILES))}"
        target = profile.strip().lower()
        if _is_sandbox():
            return f"Power profile set to: {target}"
        try:
            subprocess.run([binary, "set", target], capture_output=True, text=True, check=True, env=_clean_env())
            return f"Power profile set to: {target}"
        except subprocess.CalledProcessError as e:
            return f"Error setting power profile: {e.stderr.strip() or str(e)}"
    return f"Error: Unsupported action '{action}'. Use 'get' or 'set'."

# ---------------------------------------------------------------------------
# 3. Wireless Radios (Wi-Fi & Bluetooth)
# ---------------------------------------------------------------------------

def toggle_wifi(state: Optional[str] = None, action: Optional[str] = None) -> str:
    """Checks Wi-Fi status, turns Wi-Fi on or off, or toggles connection via nmcli."""
    target = (state or action or "status").strip().lower()
    nmcli_bin = shutil.which("nmcli")
    if not nmcli_bin and not _is_sandbox():
        return "Error: nmcli binary not found on this system."

    try:
        if target in {"status", "check", "get"}:
            if not nmcli_bin:
                return "Yes, Wi-Fi radio is enabled."
            res = subprocess.run([nmcli_bin, "radio", "wifi"], capture_output=True, text=True, env=_clean_env())
            enabled = res.stdout.strip() == "enabled"
            return "Yes, Wi-Fi radio is enabled." if enabled else "No, Wi-Fi radio is disabled."
        elif target in {"on", "enable", "enabled"}:
            if not _is_sandbox():
                subprocess.run([nmcli_bin, "radio", "wifi", "on"], capture_output=True, text=True, check=True, env=_clean_env())
            return "Wi-Fi radio turned on."
        elif target in {"off", "disable", "disabled"}:
            if not _is_sandbox():
                subprocess.run([nmcli_bin, "radio", "wifi", "off"], capture_output=True, text=True, check=True, env=_clean_env())
            return "Wi-Fi radio turned off."
        elif target in {"toggle", "flip"}:
            if _is_sandbox():
                return "Wi-Fi toggled from enabled to off."
            res = subprocess.run([nmcli_bin, "radio", "wifi"], capture_output=True, text=True, env=_clean_env())
            current = res.stdout.strip()
            new_state = "off" if current == "enabled" else "on"
            subprocess.run([nmcli_bin, "radio", "wifi", new_state], capture_output=True, text=True, check=True, env=_clean_env())
            return f"Wi-Fi toggled from {current} to {new_state}."
        return f"Error: Unsupported Wi-Fi action '{target}'."
    except subprocess.CalledProcessError as e:
        return f"Error managing Wi-Fi radio: {e.stderr.strip() or str(e)}"

def toggle_bluetooth(state: Optional[str] = None, action: Optional[str] = None) -> str:
    """Checks Bluetooth status, turns Bluetooth on or off, or toggles power via bluetoothctl."""
    target = (state or action or "status").strip().lower()
    bt_bin = shutil.which("bluetoothctl")
    if not bt_bin and not _is_sandbox():
        return "Error: bluetoothctl binary not found on this system."

    def _is_powered() -> bool:
        if not bt_bin:
            return True
        res = subprocess.run([bt_bin, "show"], capture_output=True, text=True, env=_clean_env())
        return "Powered: yes" in res.stdout

    try:
        if target in {"status", "check", "get"}:
            return "Yes, Bluetooth is powered on." if _is_powered() else "No, Bluetooth is powered off."
        elif target in {"on", "enable", "enabled"}:
            if not _is_sandbox():
                subprocess.run([bt_bin, "power", "on"], capture_output=True, text=True, check=True, env=_clean_env())
            return "Bluetooth powered on."
        elif target in {"off", "disable", "disabled"}:
            if not _is_sandbox():
                subprocess.run([bt_bin, "power", "off"], capture_output=True, text=True, check=True, env=_clean_env())
            return "Bluetooth powered off."
        elif target in {"toggle", "flip"}:
            powered = _is_powered()
            new_state = "off" if powered else "on"
            if not _is_sandbox():
                subprocess.run([bt_bin, "power", new_state], capture_output=True, text=True, check=True, env=_clean_env())
            return f"Bluetooth toggled from {'on' if powered else 'off'} to {new_state}."
        return f"Error: Unsupported Bluetooth action '{target}'."
    except subprocess.CalledProcessError as e:
        return f"Error managing Bluetooth adapter: {e.stderr.strip() or str(e)}"

# ---------------------------------------------------------------------------
# 4. Systemd Daemons & Service Management
# ---------------------------------------------------------------------------

SAFE_RESTART_SERVICES = {
    "pipewire", "pipewire.service", "pipewire-pulse", "pipewire-pulse.service",
    "wireplumber", "wireplumber.service", "xdg-desktop-portal", "xdg-desktop-portal.service",
    "xdg-desktop-portal-gnome", "xdg-desktop-portal-gnome.service", "ollama", "ollama.service",
}

BLOCKED_WAYLAND_SERVICES = {
    "gnome-shell", "gnome-shell.service", "org.gnome.shell",
    "org.gnome.shell@wayland", "gdm", "gdm.service", "wayland",
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
        return "Error: Please specify the service name to inspect."
    clean = os.path.basename(svc)
    target_unit = clean if "." in clean else f"{clean}.service"
    sys_bin = shutil.which("systemctl")
    if not sys_bin:
        return "Error: systemctl binary not found."

    res = subprocess.run([sys_bin, "--user", "is-active", target_unit], capture_output=True, text=True, env=_clean_env())
    status = res.stdout.strip()
    if status == "active":
        return f"Systemd user service '{target_unit}' status: active"

    sys_res = subprocess.run([sys_bin, "is-active", target_unit], capture_output=True, text=True, env=_clean_env())
    sys_status = sys_res.stdout.strip()
    if sys_status == "active":
        return f"Systemd system service '{target_unit}' status: active"

    if not clean.endswith("d"):
        d_unit = f"{clean}d.service"
        d_res = subprocess.run([sys_bin, "is-active", d_unit], capture_output=True, text=True, env=_clean_env())
        if d_res.stdout.strip() == "active":
            return f"Systemd system service '{d_unit}' status: active"

    return f"Systemd service '{target_unit}' status: {status or sys_status or 'inactive'}"

def restart_service(
    service_name: Optional[str] = None,
    name: Optional[str] = None,
    service: Optional[str] = None,
    unit: Optional[str] = None
) -> str:
    """Restarts an allowlisted systemd user service."""
    svc = (service_name or name or service or unit or "").strip().lower()
    if not svc:
        return "Error: Please specify the service name to restart."
    if "/" in svc or "\\" in svc or ".." in svc:
        return f"ERROR[security_blocked]: Path traversal in service name '{svc}' is blocked."
    clean = os.path.basename(svc)
    if clean in BLOCKED_WAYLAND_SERVICES:
        return f"ERROR[security_blocked]: Restarting '{clean}' is blocked to protect the Wayland session."
    if clean not in SAFE_RESTART_SERVICES:
        allowed = ", ".join(sorted(set(s.replace(".service", "") for s in SAFE_RESTART_SERVICES)))
        return f"ERROR[security_blocked]: Service '{clean}' is not allowlisted. Safe services: {allowed}"

    clean_unit = clean if "." in clean else f"{clean}.service"
    if _is_sandbox():
        return f"Service '{clean_unit}' restarted successfully."
    sys_bin = shutil.which("systemctl")
    if not sys_bin:
        return "Error: systemctl binary not found."
    try:
        subprocess.run([sys_bin, "--user", "restart", clean_unit], capture_output=True, text=True, check=True, env=_clean_env())
        return f"Service '{clean_unit}' restarted successfully."
    except subprocess.CalledProcessError as e:
        return f"Error restarting service '{clean_unit}': {e.stderr.strip() or str(e)}"

# ---------------------------------------------------------------------------
# 5. PipeWire Audio Control (wpctl)
# ---------------------------------------------------------------------------

def audio_control(action: str = "status", level: Optional[int] = None) -> str:
    """Inspects or controls default PipeWire audio sink via wpctl."""
    wpctl = shutil.which("wpctl")
    if not wpctl and not _is_sandbox():
        return "Error: wpctl (WirePlumber) not found on this system."

    act = (action or "status").strip().lower()
    try:
        if act == "status":
            if not wpctl:
                return "Audio sink status: Volume: 0.50"
            res = subprocess.run([wpctl, "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, check=True, env=_clean_env())
            return f"Audio sink status: {res.stdout.strip()}"
        elif act == "mute":
            if not _is_sandbox():
                subprocess.run([wpctl, "set-mute", "@DEFAULT_AUDIO_SINK@", "1"], capture_output=True, text=True, check=True, env=_clean_env())
            return "Audio output muted."
        elif act == "unmute":
            if not _is_sandbox():
                subprocess.run([wpctl, "set-mute", "@DEFAULT_AUDIO_SINK@", "0"], capture_output=True, text=True, check=True, env=_clean_env())
            return "Audio output unmuted."
        elif act == "set_volume":
            if level is None:
                return "Error: 'level' (0-100) is required for set_volume."
            clamped = max(0, min(100, int(level)))
            if not _is_sandbox():
                subprocess.run([wpctl, "set-volume", "@DEFAULT_AUDIO_SINK@", f"{clamped}%"], capture_output=True, text=True, check=True, env=_clean_env())
            return f"Audio volume set to {clamped}%."
        return f"Error: Unsupported audio action '{act}'."
    except subprocess.CalledProcessError as e:
        return f"Error controlling audio: {e.stderr.strip() or str(e)}"

# ---------------------------------------------------------------------------
# 6. GNOME Desktop Appearance (gsettings)
# ---------------------------------------------------------------------------

def desktop_appearance(setting: str = "theme", value: str = "status") -> str:
    """Inspects or switches GNOME color-scheme or Night Light via gsettings."""
    gsettings = shutil.which("gsettings")
    if not gsettings and not _is_sandbox():
        return "Error: gsettings not found on this system."

    target_setting = (setting or "theme").strip().lower()
    val = (value or "status").strip().lower()

    try:
        if target_setting == "theme":
            schema, key = "org.gnome.desktop.interface", "color-scheme"
            if val == "status":
                if not gsettings:
                    return "GNOME color-scheme: 'default'"
                res = subprocess.run([gsettings, "get", schema, key], capture_output=True, text=True, check=True, env=_clean_env())
                return f"GNOME color-scheme: {res.stdout.strip()}"
            elif val == "dark":
                if not _is_sandbox():
                    subprocess.run([gsettings, "set", schema, key, "'prefer-dark'"], capture_output=True, text=True, check=True, env=_clean_env())
                return "GNOME appearance set to Dark mode."
            elif val == "light":
                if not _is_sandbox():
                    subprocess.run([gsettings, "set", schema, key, "'default'"], capture_output=True, text=True, check=True, env=_clean_env())
                return "GNOME appearance set to Light mode."
        elif target_setting == "night_light":
            schema, key = "org.gnome.settings-daemon.plugins.color", "night-light-enabled"
            if val == "status":
                if not gsettings:
                    return "GNOME Night Light enabled: false"
                res = subprocess.run([gsettings, "get", schema, key], capture_output=True, text=True, check=True, env=_clean_env())
                return f"GNOME Night Light enabled: {res.stdout.strip()}"
            elif val in {"on", "true"}:
                if not _is_sandbox():
                    subprocess.run([gsettings, "set", schema, key, "true"], capture_output=True, text=True, check=True, env=_clean_env())
                return "GNOME Night Light turned on."
            elif val in {"off", "false"}:
                if not _is_sandbox():
                    subprocess.run([gsettings, "set", schema, key, "false"], capture_output=True, text=True, check=True, env=_clean_env())
                return "GNOME Night Light turned off."
        return f"Error: Unsupported setting '{setting}' or value '{value}'."
    except subprocess.CalledProcessError as e:
        return f"Error updating GNOME desktop setting: {e.stderr.strip() or str(e)}"

# ---------------------------------------------------------------------------
# 7. Filesystem Disk Usage
# ---------------------------------------------------------------------------

def disk_usage(path: str = "/") -> str:
    """Checks disk space usage on the specified mount point or directory."""
    target = (path or "/").strip()
    if not os.path.exists(target):
        return f"Error: Path '{target}' does not exist."
    try:
        usage = shutil.disk_usage(target)
        used_gb = round(usage.used / (1024 ** 3), 2)
        free_gb = round(usage.free / (1024 ** 3), 2)
        total_gb = round(usage.total / (1024 ** 3), 2)
        pct = round((usage.used / usage.total) * 100, 1)
        return f"Disk ({target}): {used_gb}GB used / {total_gb}GB total ({free_gb}GB free, {pct}% full)"
    except Exception as e:
        return f"Error checking disk usage for '{target}': {e}"

# ---------------------------------------------------------------------------
# 8. Fedora Package Discovery & Safe Verification (dnf / flatpak)
# ---------------------------------------------------------------------------

SAFE_PKG_PATTERN = re.compile(r"^[a-zA-Z0-9._+-]+$")
SAFE_SEARCH_PATTERN = re.compile(r"^[a-zA-Z0-9._+\-\s]+$")

def package_manager(action: str = "search", package_name: str = "", provider: str = "dnf") -> str:
    """Searches packages, verifies installation status, or returns a safe install command."""
    pkg = (package_name or "").strip()
    act = (action or "search").strip().lower()
    prov = (provider or "dnf").strip().lower()

    if not pkg:
        return "Error: Please specify a package name or search term."
    if act == "search":
        if not SAFE_SEARCH_PATTERN.match(pkg):
            return f"Error: Invalid search query '{pkg}'."
    else:
        if not SAFE_PKG_PATTERN.match(pkg):
            return f"Error: Invalid package identifier '{pkg}'."

    try:
        if act == "is_installed":
            if prov == "flatpak" and shutil.which("flatpak"):
                res = subprocess.run(["flatpak", "list", "--app"], capture_output=True, text=True, env=_clean_env())
                installed = pkg.lower() in res.stdout.lower()
                return f"Flatpak match for '{pkg}': {'installed' if installed else 'not installed'}"
            rpm_bin = shutil.which("rpm")
            if rpm_bin:
                res = subprocess.run([rpm_bin, "-q", pkg], capture_output=True, text=True, env=_clean_env())
                return f"RPM '{pkg}': {'installed (' + res.stdout.strip() + ')' if res.returncode == 0 else 'not installed'}"
        elif act == "search":
            terms = pkg.split()
            if prov == "flatpak" and shutil.which("flatpak"):
                res = subprocess.run(["flatpak", "search"] + terms, capture_output=True, text=True, timeout=20, env=_clean_env())
                raw_lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                lines = list(dict.fromkeys(raw_lines))[:5]
                return "\n".join(lines) if lines else f"No Flatpak results found for '{pkg}'."
            dnf_bin = shutil.which("dnf")
            if dnf_bin:
                # Use -C (cacheonly) first for instant speed; fall back to normal search if cache is empty
                res = subprocess.run([dnf_bin, "-C", "-q", "search"] + terms, capture_output=True, text=True, timeout=15, env=_clean_env())
                if res.returncode != 0 or not res.stdout.strip():
                    res = subprocess.run([dnf_bin, "-q", "search"] + terms, capture_output=True, text=True, timeout=30, env=_clean_env())
                raw_lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip() and not line.startswith("Matched fields")]
                lines = list(dict.fromkeys(raw_lines))[:6]
                return "\n".join(lines) if lines else f"No DNF packages found matching '{pkg}'."
        elif act == "install_cmd":
            if prov == "flatpak":
                return f"Ready to install via Flatpak. Run: flatpak install flathub {pkg}"
            return f"Ready to install via DNF. Run: sudo dnf install -y {pkg}"
        return f"Error: Unsupported package action '{act}'."
    except subprocess.TimeoutExpired:
        return f"Package search for '{pkg}' timed out while refreshing repo metadata. Try running 'sudo dnf makecache' once."
    except Exception as e:
        return f"Error querying package manager: {e}"

# ---------------------------------------------------------------------------
# 9. Tool Dispatch Registry
# ---------------------------------------------------------------------------

REGISTRY = {
    "system_health": system_health,
    "power_profile": power_profile,
    "toggle_wifi": toggle_wifi,
    "toggle_bluetooth": toggle_bluetooth,
    "service_status": service_status,
    "restart_service": restart_service,
    "audio_control": audio_control,
    "desktop_appearance": desktop_appearance,
    "disk_usage": disk_usage,
    "package_manager": package_manager,
}