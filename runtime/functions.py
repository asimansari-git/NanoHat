import ast
import operator
import math
import os
import sys
import shutil
import subprocess
from datetime import datetime
import re
from typing import Any
import psutil
from typing import Any


_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[node.id]
        raise ValueError(f"Unsupported variable: {node.id}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        if op_type is ast.Pow and (right > 1000 or left > 1e10):
            raise ValueError("Exponent too large")
        return _SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_ast(node.operand)
        return _SAFE_OPERATORS[op_type](operand)
    else:
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")


def check_interactive_tty() -> bool:
    """Returns True if running in an interactive TTY or auto-approved via env var."""
    return sys.stdin.isatty() or os.environ.get("NANOHAT_AUTO_APPROVE_DESTRUCTIVE") == "1"


def calculator(expression: str) -> str:
    """Safely evaluates a mathematical expression using AST parsing."""
    try:
        expr_clean = expression.strip()
        tree = ast.parse(expr_clean, mode="eval")
        result = _eval_ast(tree)
        if isinstance(result, float):
            if result.is_integer() and abs(result) < 1e15:
                result = int(result)
            elif abs(result) >= 1e15 or (result != 0 and abs(result) < 1e-4):
                # Format scientific notation compactly for large/small numbers
                return f"{result:g}"
        elif isinstance(result, int):
            if abs(result) >= 1e15:
                return f"{float(result):g}"
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def system_health(metric: str = "all") -> str:
    """Returns current system health: CPU percent, RAM usage, and battery."""
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


VALID_POWER_PROFILES = {"power-saver", "balanced", "performance"}


def power_profile(action: str = "get", profile: str = None) -> str:
    """Gets or sets the Linux system power profile via powerprofilesctl."""
    binary = shutil.which("powerprofilesctl")
    if not binary:
        return "Error: powerprofilesctl is not installed on this system."

    action_norm = (action or "get").strip().lower()
    if action_norm == "get" or (action_norm == "set" and not profile):
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


def get_datetime() -> str:
    """Returns current system date, time, day of week, and timezone."""
    now = datetime.now().astimezone()
    return now.strftime("%A, %B %d, %Y, %I:%M:%S %p %Z")


def toggle_wifi(state: str = None, action: str = None) -> str:
    """Checks Wi-Fi status, turns Wi-Fi on or off, or toggles connection via nmcli."""
    target = (state or action or "status").strip().lower()
    nmcli_bin = shutil.which("nmcli")
    if not nmcli_bin:
        return "Error: nmcli binary not found on this system."

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


def toggle_bluetooth(state: str = None, action: str = None) -> str:
    """Checks Bluetooth status, turns Bluetooth on or off, or toggles power via bluetoothctl."""
    target = (state or action or "status").strip().lower()
    bt_bin = shutil.which("bluetoothctl")
    if not bt_bin:
        return "Error: bluetoothctl binary not found on this system."

    def _is_powered() -> bool:
        res = subprocess.run([bt_bin, "show"], capture_output=True, text=True)
        return "Powered: yes" in res.stdout

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


def service_status(service_name: str = None, name: str = None, service: str = None, unit: str = None) -> str:
    """Inspects whether a systemd user or system service is active, inactive, or failed."""
    svc = (service_name or name or service or unit or "").strip()
    if not svc:
        return "Error: Please specify the service name to inspect (e.g. 'pipewire', 'wireplumber')."
    clean = os.path.basename(svc)
    target_unit = clean if "." in clean else f"{clean}.service"
    sys_bin = shutil.which("systemctl")
    if not sys_bin:
        return "Error: systemctl binary not found on this system."

    res = subprocess.run([sys_bin, "--user", "is-active", target_unit], capture_output=True, text=True)
    status = res.stdout.strip()
    if status == "active":
        return f"Systemd user service '{target_unit}' status: active"

    sys_res = subprocess.run([sys_bin, "is-active", target_unit], capture_output=True, text=True)
    sys_status = sys_res.stdout.strip()
    if sys_status == "active":
        return f"Systemd system service '{target_unit}' status: active"

    if not clean.endswith("d"):
        d_unit = f"{clean}d.service"
        d_res = subprocess.run([sys_bin, "is-active", d_unit], capture_output=True, text=True)
        if d_res.stdout.strip() == "active":
            return f"Systemd system service '{d_unit}' status: active"

    return f"Systemd service '{target_unit}' status: {status or sys_status or 'inactive'}"

def restart_service(service_name: str = None, name: str = None, service: str = None, unit: str = None) -> str:
    """Restarts an allowlisted systemd user service."""
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


def task_add(title: str = None, due_time: str = None, task: str = None, time: str = None, notify_minutes_before: int = 0) -> str:
    """Schedules a new task or reminder."""
    t = (title or task or "").strip()
    due = (due_time or time or "unspecified").strip()
    if not t:
        return "Error: Please specify the task title or description."
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO scheduled_tasks (title, due_time, notify_minutes_before, status) VALUES (?, ?, ?, 'pending');",
            (t, due, int(notify_minutes_before or 0))
        )
        task_id = cursor.lastrowid
        conn.commit()
    return f"Task #{task_id} scheduled: '{t}' (Due: {due})."


def task_list(status: str = "pending") -> str:
    """Lists scheduled tasks filtered by status ('pending', 'completed', 'cancelled', or 'all')."""
    s = (status or "pending").strip().lower()
    init_db()
    with get_connection() as conn:
        if s == "all":
            cursor = conn.execute("SELECT id, title, due_time, status FROM scheduled_tasks ORDER BY id ASC;")
        else:
            cursor = conn.execute("SELECT id, title, due_time, status FROM scheduled_tasks WHERE LOWER(status) = ? ORDER BY id ASC;", (s,))
        rows = cursor.fetchall()
        if not rows:
            return f"No {s} tasks found."
        lines = [f"- Task #{row['id']}: '{row['title']}' (Due: {row['due_time']}, Status: {row['status']})" for row in rows]
        return f"Scheduled Tasks ({s}):\n" + "\n".join(lines)


def task_cancel(task_id: Any = None, id: Any = None) -> str:
    """Cancels a scheduled task by ID."""
    raw_id = task_id if task_id is not None else id
    if raw_id is None:
        return "Error: Please specify the task_id to cancel."
    try:
        tid = int(raw_id)
    except (ValueError, TypeError):
        return f"Error: Invalid task ID '{raw_id}'. Must be an integer."
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("UPDATE scheduled_tasks SET status = 'cancelled' WHERE id = ?;", (tid,))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Task #{tid} has been cancelled."
        return f"Task #{tid} not found."


# Tool dispatch registry (1:1 canonical mapping)
REGISTRY = {
    "calculator": calculator,
    "system_health": system_health,
    "power_profile": power_profile,
    "get_datetime": get_datetime,
    "toggle_wifi": toggle_wifi,
    "toggle_bluetooth": toggle_bluetooth,
    "service_status": service_status,
    "restart_service": restart_service,
    "task_add": task_add,
    "task_list": task_list,
    "task_cancel": task_cancel,
}



