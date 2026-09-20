import unittest
from unittest.mock import patch
import os
import pytest
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools
from runtime.functions import (
    calculator, system_health, power_profile, get_datetime, empty_trash,
    toggle_wifi, toggle_bluetooth, service_status, restart_service,
    memory_set, memory_get, memory_list, memory_delete, task_add,
    task_list, task_cancel
)

# Global store for test results to generate the final markdown report
TEST_RESULTS = []

@pytest.fixture(scope="session", autouse=True)
def generate_report():
    yield
    # Teardown logic
    os.makedirs("reports", exist_ok=True)
    with open("reports/sysadmin_power_user_report.md", "w") as f:
        f.write("# NanoHat v3.0.0 Stress Test Report: Linux Sysadmin Power User\n\n")
        f.write("## Persona Profile & Test Vector\n")
        f.write("- **Persona**: Linux Sysadmin / Power User\n")
        f.write("- **Characteristics**: Uses deep Linux terminal patterns, regexes, signal handling, environment variables, POSIX flags.\n")
        f.write("- **Objective**: Test robust routing and execution layers under edge-case arguments and terminal abstractions.\n\n")

        total = len(TEST_RESULTS)
        passed = sum(1 for r in TEST_RESULTS if r["result"] == "OK")
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        f.write("## Executive Summary\n")
        f.write(f"- **Total Queries/Cases**: {total}\n")
        f.write(f"- **Passed**: {passed}\n")
        f.write(f"- **Failed**: {failed}\n")
        f.write(f"- **Pass Rate**: {pass_rate:.2f}%\n")
        f.write(f"- **Fail-Closed Security Rate**: Evaluated via explicit execution boundary tests.\n\n")

        f.write("## Detailed Case Matrix\n")
        f.write("| Case | Query/Args | Target Tool | Result | Notes |\n")
        f.write("|---|---|---|---|---|\n")
        for r in TEST_RESULTS:
            f.write(f"| {r['case']} | `{r['query']}` | `{r['target_tool']}` | **{r['result']}** | {r['notes']} |\n")

        f.write("\n## Critical Edge Cases & Failures Discovered\n")
        f.write("Failures and unexpected behaviors discovered during the fuzzing iteration are detailed in the matrix above.\n")

        f.write("\n## Recommended Hardening Patches\n")
        f.write("1. Augment regex patterns in `router.py` to match more sysadmin terms (e.g. ps, grep, killall).\n")
        f.write("2. Enhance parameter sanitization in systemd functions.\n")

def record_result(case_name, query, tool, result, notes):
    TEST_RESULTS.append({
        "case": case_name,
        "query": query,
        "target_tool": tool,
        "result": result,
        "notes": notes
    })

class TestPersonaSysadminPowerUserRouting(unittest.TestCase):
    def check_routing(self, query, expected_tool, test_name, notes=""):
        try:
            tools = route_tools(query, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
        except Exception as e:
            record_result(test_name, query, expected_tool, "ERROR", f"Exception: {e}")
            raise

        if expected_tool in names:
            record_result(test_name, query, expected_tool, "OK", notes)
        else:
            record_result(test_name, query, expected_tool, "ERROR", f"Expected {expected_tool} but got {names}")
        self.assertIn(expected_tool, names, f"Query '{query}' failed to route to {expected_tool}")

    # 1. Pipes and redirections
    def test_routing_pipe_systemctl(self):
        self.check_routing("systemctl --user restart audio.service | grep 'success'", "restart_service", "Pipe Restart Service", "Pipes shouldn't break regex")

    def test_routing_env_var_launch(self):
        self.check_routing("launch terminal with env VAR=1 and check ram", "system_health", "Env Var RAM Check", "RAM words should map to system_health")

    def test_routing_grep_top_5(self):
        self.check_routing("check memory and grep top 5 processes", "system_health", "Grep Top 5", "Focus on memory -> system_health")

    def test_routing_systemctl_user_status(self):
        self.check_routing("systemctl --user status docker.service", "service_status", "Systemctl Status", "Service explicit status")

    def test_routing_systemctl_daemon_reload(self):
        self.check_routing("systemctl --user daemon-reload", "restart_service", "Systemctl Daemon Reload", "daemon-reload matches restart/reload regex")

    def test_routing_calculator_large_pow(self):
        self.check_routing("calculator 2**16", "calculator", "Calc Pow", "Math detection")

    def test_routing_calculator_hex(self):
        self.check_routing("evaluate 0xff + 0x1a", "calculator", "Calc Hex", "Math word 'evaluate'")

    def test_routing_trash_force(self):
        self.check_routing("empty trash -f --no-preserve-root", "empty_trash", "Empty Trash Force", "Trash args")

    def test_routing_wifi_rfkill(self):
        self.check_routing("rfkill unblock wifi && nmcli radio wifi on", "toggle_wifi", "Wifi rfkill", "wifi words")

    def test_routing_bluetooth_rfkill(self):
        self.check_routing("rfkill block bluetooth", "toggle_bluetooth", "Bluetooth rfkill", "bluetooth words")

    def test_routing_power_profile_daemon(self):
        self.check_routing("restart power-profiles-daemon", "restart_service", "Power Profile Daemon Restart", "restart service over power profile")

    def test_routing_power_profile_set(self):
        self.check_routing("set power profile to power-saver", "power_profile", "Power Profile Set", "power profile explicitly")

    def test_routing_battery_cat(self):
        self.check_routing("cat /sys/class/power_supply/BAT0/capacity", "system_health", "Battery Sysfs", "battery words fallback")

    def test_routing_cpu_proc(self):
        self.check_routing("cat /proc/cpuinfo | grep 'model name'", "system_health", "CPU Proc", "cpu word")

    def test_routing_memory_free(self):
        self.check_routing("free -h", "system_health", "Memory Free", "Could fallback, or not match. Will rely on fallback if needed. But 'free' isn't in cpu/ram regex. Let's test 'check ram with free -h'")
        self.check_routing("check ram with free -h", "system_health", "Memory Free Explicit", "ram word")

    def test_routing_memory_set_dotfiles(self):
        self.check_routing("remember my dotfiles are in ~/.config", "memory_set", "Memory Set Dotfiles", "remember word")

    def test_routing_memory_get_editor(self):
        self.check_routing("what is my editor $EDITOR", "memory_get", "Memory Get Editor", "what is my editor")

    def test_routing_task_crontab(self):
        self.check_routing("schedule task in crontab for tomorrow", "task_add", "Task Add Crontab", "schedule task")

    def test_routing_task_kill(self):
        self.check_routing("cancel task 1; kill -9 1", "task_cancel", "Task Cancel Kill", "cancel task")

    def test_routing_task_ps_aux(self):
        self.check_routing("list all tasks like ps aux", "task_list", "Task List ps aux", "list all tasks")

    def test_routing_date_unix(self):
        self.check_routing("date +%s", "get_datetime", "Date Unix", "date word")

    def test_routing_systemd_analyze(self):
        self.check_routing("systemd-analyze blame", "service_status", "Systemd Analyze", "systemd word")

    def test_routing_ps_aux_grep(self):
        self.check_routing("ps aux | grep tailscaled", "service_status", "ps aux grep", "process grep")

    def test_routing_killall(self):
        self.check_routing("killall -9 pipewire", "restart_service", "killall pipewire", "restart/reload logic")

    def test_routing_journalctl(self):
        self.check_routing("journalctl -u ollama.service --no-pager", "service_status", "journalctl", "service log checking")

    def test_routing_math_bash_expr(self):
        self.check_routing("echo $(( 100 * 20 ))", "calculator", "Bash Expr Math", "math eval")

    def test_routing_trash_rm_rf(self):
        self.check_routing("rm -rf ~/.local/share/Trash/files/*", "empty_trash", "rm -rf Trash", "trash keyword")

    def test_routing_power_turbostat(self):
        self.check_routing("turbostat --Summary", "power_profile", "Turbostat", "power profile or system health? actually power keyword")

    def test_routing_bluetoothctl_devices(self):
        self.check_routing("bluetoothctl devices", "toggle_bluetooth", "bluetoothctl devices", "bluetooth keyword")

    def test_routing_wifi_iwconfig(self):
        self.check_routing("iwconfig wlan0 power on", "toggle_wifi", "iwconfig power", "wifi and power keywords")

    def test_routing_task_at_command(self):
        self.check_routing("echo 'notify-send hello' | at now + 5 minutes", "task_add", "at command", "schedule task maybe? wait, it just has 'time/minutes', might route to get_datetime. Let's see.")

class TestPersonaSysadminPowerUserExecution(unittest.TestCase):
    def check_execution(self, tool_func, kwargs, expected_substr, test_name, notes=""):
        try:
            result = tool_func(**kwargs)
        except Exception as e:
            record_result(test_name, str(kwargs), tool_func.__name__, "ERROR", f"Exception: {e}")
            raise

        if expected_substr.lower() in str(result).lower():
            record_result(test_name, str(kwargs), tool_func.__name__, "OK", notes)
        else:
            record_result(test_name, str(kwargs), tool_func.__name__, "ERROR", f"Expected '{expected_substr}' in '{result}'")
        self.assertIn(expected_substr.lower(), str(result).lower())

    def test_exec_calculator_large_pow(self):
        # 2**16
        self.check_execution(calculator, {"expression": "2**16"}, "65536", "Calc Pow Exec")

    def test_exec_calculator_injection_attempt(self):
        # eval('__import__("os").system("echo hacked")') -> AST should block
        res = calculator("__import__('os').system('echo hacked')")
        record_result("Calc Injection", "__import__('os').system('echo hacked')", "calculator", "OK" if "error" in res.lower() else "ERROR", "AST should block")
        self.assertIn("error", res.lower())

    def test_exec_calculator_bash_expr(self):
        res = calculator("$(( 100 * 20 ))")
        record_result("Calc Bash Expr", "$(( 100 * 20 ))", "calculator", "OK" if "error" in res.lower() else "ERROR", "AST should reject bash syntax")
        self.assertIn("error", res.lower())

    @patch("runtime.functions.subprocess.run")
    def test_exec_restart_service_wayland_block(self, mock_run):
        # Blocking Wayland components
        res = restart_service(service_name="gdm")
        record_result("Restart Wayland Block", "gdm", "restart_service", "OK" if "security_blocked" in res.lower() else "ERROR", "Block gdm")
        self.assertIn("security_blocked", res.lower())

    @patch("runtime.functions.subprocess.run")
    def test_exec_restart_service_pipewire(self, mock_run):
        # Allowed service
        self.check_execution(restart_service, {"service_name": "pipewire"}, "success", "Restart Pipewire", "Allow pipewire")

    @patch("runtime.functions.subprocess.run")
    def test_exec_empty_trash_tty_guard(self, mock_run):
        # TTY check should block empty_trash in headless mode
        with patch("runtime.functions.check_interactive_tty", return_value=False):
            res = empty_trash()
            record_result("Empty Trash TTY", "empty_trash", "empty_trash", "OK" if "aborted" in res.lower() else "ERROR", "Headless block")
            self.assertIn("aborted", res.lower())

    @patch("runtime.functions.subprocess.run")
    def test_exec_empty_trash_auto_approve(self, mock_run):
        # Auto approve should pass
        with patch.dict(os.environ, {"NANOHAT_AUTO_APPROVE_DESTRUCTIVE": "1"}):
            self.check_execution(empty_trash, {}, "success", "Empty Trash Auto Approve", "Auto approve env var")

    @patch("runtime.functions.subprocess.run")
    @patch("runtime.functions.shutil.which", return_value="/usr/bin/powerprofilesctl")
    def test_exec_power_profile_invalid(self, mock_which, mock_run):
        # invalid profile
        res = power_profile(action="set", profile="super-performance-mode-9000")
        record_result("Power Profile Invalid", "super-performance-mode-9000", "power_profile", "OK" if "invalid profile" in res.lower() else "ERROR", "Invalid profile")
        self.assertIn("invalid profile", res.lower())

    @patch("runtime.functions.subprocess.run")
    @patch("runtime.functions.shutil.which", return_value="/usr/bin/systemctl")
    def test_exec_service_status_systemctl_mock(self, mock_which, mock_run):
        # Mock active status
        mock_run.return_value.stdout = "active\n"
        self.check_execution(service_status, {"service_name": "docker"}, "active", "Service Status Active")

    @patch("runtime.functions.subprocess.run")
    @patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
    def test_exec_toggle_wifi_mock(self, mock_which, mock_run):
        mock_run.return_value.stdout = "enabled\n"
        self.check_execution(toggle_wifi, {"state": "status"}, "enabled", "Toggle Wifi Mock")

    @patch("runtime.functions.subprocess.run")
    @patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
    def test_exec_toggle_bluetooth_mock(self, mock_which, mock_run):
        mock_run.return_value.stdout = "Powered: yes\n"
        self.check_execution(toggle_bluetooth, {"state": "status"}, "powered on", "Toggle Bluetooth Mock")
