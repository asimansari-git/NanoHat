"""
test_manual_matrix_mocked.py — Automated Mock Test Suite for the v3.0.0 Manual Test Matrix.
Implements the 60 test cases defined in .nanohat/testing/2026-09-15-v3.0.0-manual-test-matrix.md
using 100% mocked boundaries (MockState), guaranteeing zero hardware or host modifications.
"""

import os
import sqlite3
import unittest
from unittest.mock import patch, MagicMock

from runtime.tools import ALL_TOOLS
from runtime.semantic_router import route_tools
from runtime.functions import (
    calculator,
    system_health,
    power_profile,
    get_datetime,
    empty_trash,
    toggle_wifi,
    toggle_bluetooth,
    service_status,
    restart_service,
    memory_set,
    memory_get,
    memory_list,
    memory_delete,
    task_add,
    task_list,
    task_cancel,
    SAFE_RESTART_SERVICES,
    BLOCKED_WAYLAND_SERVICES,
)


class MockSystemState:
    """In-memory state simulating Linux OS subsystem and hardware sensors."""
    def __init__(self):
        self.wifi_enabled = True
        self.bluetooth_powered = True
        self.power_profile = "balanced"
        self.services = {
            "pipewire": "active",
            "pipewire.service": "active",
            "wireplumber": "active",
            "wireplumber.service": "active",
            "ollama": "active",
            "ollama.service": "active",
            "tailscale": "active",
            "tailscaled.service": "active",
        }
        self.trash_emptied = False


class TestManualMatrixMocked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = MockSystemState()

    def setUp(self):
        # Setup temporary isolated in-memory SQLite database for memory & task tests
        self.test_conn = sqlite3.connect(":memory:")
        self.test_conn.row_factory = sqlite3.Row
        self.test_conn.execute("""
            CREATE TABLE user_memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.test_conn.execute("""
            CREATE TABLE scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_time TEXT NOT NULL,
                notify_minutes_before INTEGER DEFAULT 0,
                status TEXT CHECK(status IN ('pending', 'completed', 'cancelled')) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def tearDown(self):
        self.test_conn.close()

    # =========================================================================
    # Pillar 1: Deterministic Math Evaluation (`calculator`)
    # =========================================================================
    def test_math_01_multiplication(self):
        """MATH-01: nanohat 'What is 45 * 12?' -> 540"""
        tools = [t["function"]["name"] for t in route_tools("What is 45 * 12?", ALL_TOOLS)]
        self.assertIn("calculator", tools)
        self.assertEqual(calculator("45 * 12"), "540")

    def test_math_02_operator_precedence(self):
        """MATH-02: nanohat 'Calculate 7 + 7 * 18' -> 133"""
        tools = [t["function"]["name"] for t in route_tools("Calculate 7 + 7 * 18", ALL_TOOLS)]
        self.assertIn("calculator", tools)
        self.assertEqual(calculator("7 + 7 * 18"), "133")

    def test_math_03_parentheses(self):
        """MATH-03: nanohat 'What is (100 - 25) / 5?' -> 15"""
        tools = [t["function"]["name"] for t in route_tools("What is (100 - 25) / 5?", ALL_TOOLS)]
        self.assertIn("calculator", tools)
        self.assertEqual(calculator("(100 - 25) / 5"), "15")

    def test_math_04_exponent(self):
        """MATH-04: nanohat 'Calculate 2 ** 10' -> 1024"""
        tools = [t["function"]["name"] for t in route_tools("Calculate 2 ** 10", ALL_TOOLS)]
        self.assertIn("calculator", tools)
        self.assertEqual(calculator("2 ** 10"), "1024")

    def test_math_05_percentage_evaluation(self):
        """MATH-05: nanohat 'What is 15 percent of 800?' -> 120"""
        self.assertEqual(calculator("800 * 0.15"), "120")

    def test_math_06_worded_arithmetic(self):
        """MATH-06: nanohat 'Divide 144 by 12' -> 12"""
        self.assertEqual(calculator("144 / 12"), "12")

    def test_math_07_zero_division_guard(self):
        """MATH-07: nanohat 'What is 10 divided by 0?' -> safe error without crash"""
        res = calculator("10 / 0")
        self.assertTrue(res.startswith("Error: division by zero"))

    # =========================================================================
    # Pillar 2: System Health, Power & DateTime
    # =========================================================================
    @patch("runtime.functions.psutil.virtual_memory")
    def test_sys_01_ram_usage(self, mock_mem):
        """SYS-01: 'What is my current RAM usage?' -> RAM metrics"""
        mock_mem.return_value = MagicMock(used=8 * (1024**3), total=16 * (1024**3), percent=50.0)
        tools = [t["function"]["name"] for t in route_tools("What is my current RAM usage?", ALL_TOOLS)]
        self.assertIn("system_health", tools)
        res = system_health("ram")
        self.assertIn("RAM: 8.0GB / 16.0GB (50.0%)", res)

    @patch("runtime.functions.psutil.virtual_memory")
    def test_sys_02_free_ram(self, mock_mem):
        """SYS-02: 'How much free RAM do I have?'"""
        mock_mem.return_value = MagicMock(used=4 * (1024**3), total=16 * (1024**3), percent=25.0)
        tools = [t["function"]["name"] for t in route_tools("How much free RAM do I have?", ALL_TOOLS)]
        self.assertIn("system_health", tools)
        res = system_health("ram")
        self.assertIn("RAM: 4.0GB / 16.0GB (25.0%)", res)

    @patch("runtime.functions.psutil.cpu_percent")
    def test_sys_03_cpu_usage(self, mock_cpu):
        """SYS-03: 'What is my CPU usage?'"""
        mock_cpu.return_value = 18.4
        tools = [t["function"]["name"] for t in route_tools("What is my CPU usage?", ALL_TOOLS)]
        self.assertIn("system_health", tools)
        res = system_health("cpu")
        self.assertEqual(res, "CPU: 18.4%")

    @patch("runtime.functions.psutil.sensors_battery")
    def test_sys_04_battery_level(self, mock_batt):
        """SYS-04: 'What is my battery level?'"""
        mock_batt.return_value = MagicMock(percent=82, power_plugged=True)
        tools = [t["function"]["name"] for t in route_tools("What is my battery level?", ALL_TOOLS)]
        self.assertIn("system_health", tools)
        res = system_health("battery")
        self.assertEqual(res, "Battery: 82% (charging)")

    @patch("runtime.functions.psutil.cpu_percent")
    @patch("runtime.functions.psutil.virtual_memory")
    @patch("runtime.functions.psutil.sensors_battery")
    def test_sys_05_overall_system_health(self, mock_batt, mock_mem, mock_cpu):
        """SYS-05: 'What is my overall system health?'"""
        mock_cpu.return_value = 12.0
        mock_mem.return_value = MagicMock(used=6 * (1024**3), total=16 * (1024**3), percent=37.5)
        mock_batt.return_value = MagicMock(percent=95, power_plugged=False)
        tools = [t["function"]["name"] for t in route_tools("What is my overall system health?", ALL_TOOLS)]
        self.assertIn("system_health", tools)
        res = system_health("all")
        self.assertIn("CPU: 12.0%", res)
        self.assertIn("RAM: 6.0GB / 16.0GB (37.5%)", res)
        self.assertIn("Battery: 95% (discharging)", res)

    @patch("runtime.functions.subprocess.run")
    def test_sys_06_power_profile_get(self, mock_run):
        """SYS-06: 'What is my power profile?'"""
        mock_run.return_value = MagicMock(stdout="balanced\n", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("What is my power profile?", ALL_TOOLS)]
        self.assertIn("power_profile", tools)
        res = power_profile(action="get")
        self.assertEqual(res, "Current power profile: balanced")

    @patch("runtime.functions.subprocess.run")
    def test_sys_07_power_profile_set(self, mock_run):
        """SYS-07: 'Set power profile to performance'"""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Set power profile to performance", ALL_TOOLS)]
        self.assertIn("power_profile", tools)
        res = power_profile(action="set", profile="performance")
        self.assertEqual(res, "Power profile set to: performance")

    def test_sys_08_datetime_date(self):
        """SYS-08: 'What is today's date?'"""
        tools = [t["function"]["name"] for t in route_tools("What is today's date?", ALL_TOOLS)]
        self.assertIn("get_datetime", tools)
        res = get_datetime()
        self.assertTrue(len(res) > 10)

    def test_sys_09_datetime_time(self):
        """SYS-09: 'What time is it right now?'"""
        tools = [t["function"]["name"] for t in route_tools("What time is it right now?", ALL_TOOLS)]
        self.assertIn("get_datetime", tools)

    def test_sys_10_datetime_day_of_week(self):
        """SYS-10: 'What day of the week is it?'"""
        tools = [t["function"]["name"] for t in route_tools("What day of the week is it?", ALL_TOOLS)]
        self.assertIn("get_datetime", tools)

    # =========================================================================
    # Pillar 3: Network Radios & Services (Mocked)
    # =========================================================================
    @patch("runtime.functions.subprocess.run")
    def test_net_01_wifi_status(self, mock_run):
        """NET-01: 'Is Wi-Fi on?'"""
        mock_run.return_value = MagicMock(stdout="enabled\n", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Is Wi-Fi on?", ALL_TOOLS)]
        self.assertIn("toggle_wifi", tools)
        self.assertEqual(toggle_wifi("status"), "Yes, Wi-Fi radio is enabled.")

    @patch("runtime.functions.subprocess.run")
    def test_net_02_wifi_turn_off(self, mock_run):
        """NET-02: 'Turn off Wi-Fi'"""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Turn off Wi-Fi", ALL_TOOLS)]
        self.assertIn("toggle_wifi", tools)
        self.assertEqual(toggle_wifi("off"), "Wi-Fi radio turned off.")

    @patch("runtime.functions.subprocess.run")
    def test_net_03_wifi_turn_on(self, mock_run):
        """NET-03: 'Turn on Wi-Fi'"""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Turn on Wi-Fi", ALL_TOOLS)]
        self.assertIn("toggle_wifi", tools)
        self.assertEqual(toggle_wifi("on"), "Wi-Fi radio turned on.")

    @patch("runtime.functions.subprocess.run")
    def test_net_04_bluetooth_status(self, mock_run):
        """NET-04: 'Is Bluetooth on?'"""
        mock_run.return_value = MagicMock(stdout="Powered: yes\n", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Is Bluetooth on?", ALL_TOOLS)]
        self.assertIn("toggle_bluetooth", tools)
        self.assertEqual(toggle_bluetooth("status"), "Yes, Bluetooth is powered on.")

    @patch("runtime.functions.subprocess.run")
    def test_net_05_bluetooth_turn_off(self, mock_run):
        """NET-05: 'Turn off Bluetooth'"""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Turn off Bluetooth", ALL_TOOLS)]
        self.assertIn("toggle_bluetooth", tools)
        self.assertEqual(toggle_bluetooth("off"), "Bluetooth powered off.")

    @patch("runtime.functions.subprocess.run")
    def test_net_06_bluetooth_turn_on(self, mock_run):
        """NET-06: 'Turn on Bluetooth'"""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Turn on Bluetooth", ALL_TOOLS)]
        self.assertIn("toggle_bluetooth", tools)
        self.assertEqual(toggle_bluetooth("on"), "Bluetooth powered on.")

    @patch("runtime.functions.subprocess.run")
    def test_net_07_service_status_pipewire(self, mock_run):
        """NET-07: 'What is the status of pipewire?'"""
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("What is the status of pipewire?", ALL_TOOLS)]
        self.assertTrue("service_status" in tools or "restart_service" in tools)
        res = service_status("pipewire")
        self.assertEqual(res, "Systemd user service 'pipewire.service' status: active")

    @patch("runtime.functions.subprocess.run")
    def test_net_08_service_status_tailscale(self, mock_run):
        """NET-08: 'What is the status of tailscale server?'"""
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        res = service_status("tailscale")
        self.assertIn("active", res)

    @patch("runtime.functions.subprocess.run")
    def test_net_09_restart_pipewire(self, mock_run):
        """NET-09: 'Restart pipewire'"""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        tools = [t["function"]["name"] for t in route_tools("Restart pipewire", ALL_TOOLS)]
        self.assertIn("restart_service", tools)
        res = restart_service("pipewire")
        self.assertEqual(res, "Service 'pipewire.service' restarted successfully.")

    def test_net_10_restart_gnome_shell_blocked(self):
        """NET-10: 'Restart gnome-shell' -> Safety Shield Wayland Protection"""
        res = restart_service("gnome-shell")
        self.assertIn("ERROR[security_blocked]", res)
        self.assertIn("strictly blocked to prevent Wayland desktop session crashes", res)

    # =========================================================================
    # Pillar 4: Persistent Memory (User Identity & Notes with In-Memory DB)
    # =========================================================================
    def test_mem_01_set_distro(self):
        """MEM-01: 'My favorite distro is Fedora'"""
        tools = [t["function"]["name"] for t in route_tools("My favorite distro is Fedora", ALL_TOOLS)]
        self.assertIn("memory_set", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            res = memory_set("favorite_distro", "Fedora")
            self.assertIn("Saved to memory: 'favorite_distro' = 'Fedora'", res)

    def test_mem_02_set_editor(self):
        """MEM-02: 'My favorite editor is neovim'"""
        tools = [t["function"]["name"] for t in route_tools("My favorite editor is neovim", ALL_TOOLS)]
        self.assertIn("memory_set", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            res = memory_set("favorite_editor", "neovim")
            self.assertIn("Saved to memory: 'favorite_editor' = 'neovim'", res)

    def test_mem_03_set_pet_name(self):
        """MEM-03: 'My pet name is Milo'"""
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            res = memory_set("pet_name", "Milo")
            self.assertIn("pet_name", res)

    def test_mem_04_set_preference(self):
        """MEM-04: 'I prefer python over rust'"""
        tools = [t["function"]["name"] for t in route_tools("I prefer python over rust", ALL_TOOLS)]
        self.assertIn("memory_set", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            res = memory_set("preference", "python over rust")
            self.assertIn("Saved to memory", res)

    def test_mem_05_get_distro(self):
        """MEM-05: 'What is my favorite distro?'"""
        tools = [t["function"]["name"] for t in route_tools("What is my favorite distro?", ALL_TOOLS)]
        self.assertIn("memory_get", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            memory_set("favorite_distro", "Fedora")
            res = memory_get("favorite_distro")
            self.assertIn("Fedora", res)

    def test_mem_06_smart_fallback_pet(self):
        """MEM-06: 'What is my pet?' -> smart fallback to pet_name"""
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            memory_set("pet_name", "Milo")
            res = memory_get("pet")
            self.assertIn("Milo", res)

    def test_mem_07_smart_fallback_editor(self):
        """MEM-07: 'What is my editor?' -> smart fallback to favorite_editor"""
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            memory_set("favorite_editor", "neovim")
            res = memory_get("editor")
            self.assertIn("neovim", res)

    def test_mem_08_who_am_i(self):
        """MEM-08: 'Who am I?'"""
        tools = [t["function"]["name"] for t in route_tools("Who am I?", ALL_TOOLS)]
        self.assertIn("memory_get", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            memory_set("name", "Kaizen")
            res = memory_get("name")
            self.assertIn("Kaizen", res)

    def test_mem_09_list_memories(self):
        """MEM-09: 'List all my memories'"""
        tools = [t["function"]["name"] for t in route_tools("List all my memories", ALL_TOOLS)]
        self.assertIn("memory_list", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            memory_set("editor", "neovim")
            memory_set("distro", "Fedora")
            res = memory_list()
            self.assertIn("editor: neovim", res)
            self.assertIn("distro: Fedora", res)

    def test_mem_10_forget_editor(self):
        """MEM-10: 'Forget my favorite editor'"""
        tools = [t["function"]["name"] for t in route_tools("Forget my favorite editor", ALL_TOOLS)]
        self.assertIn("memory_delete", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            memory_set("favorite_editor", "neovim")
            res = memory_delete("favorite_editor")
            self.assertIn("deleted successfully", res)

    # =========================================================================
    # Pillar 5: Scheduled Tasks & Reminders (Mocked In-Memory DB)
    # =========================================================================
    def test_task_01_add_relative(self):
        """TASK-01: 'Remind me to drink water in 10 minutes'"""
        tools = [t["function"]["name"] for t in route_tools("Remind me to drink water in 10 minutes", ALL_TOOLS)]
        self.assertIn("task_add", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            res = task_add("drink water", "in 10 minutes")
            self.assertIn("Task #1 scheduled", res)

    def test_task_02_add_clock_time(self):
        """TASK-02: 'Remind me to stretch at 5pm'"""
        tools = [t["function"]["name"] for t in route_tools("Remind me to stretch at 5pm", ALL_TOOLS)]
        self.assertIn("task_add", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            res = task_add("stretch", "5pm")
            self.assertIn("Task #1 scheduled", res)

    def test_task_03_add_date_time(self):
        """TASK-03: 'Add task: Submit report tomorrow at 10am'"""
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            res = task_add("Submit report", "tomorrow at 10am")
            self.assertIn("Submit report", res)

    def test_task_04_list_pending(self):
        """TASK-04: 'What are my reminders?'"""
        tools = [t["function"]["name"] for t in route_tools("What are my reminders?", ALL_TOOLS)]
        self.assertIn("task_list", tools)
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            task_add("Review PR", "today")
            res = task_list("pending")
            self.assertIn("Review PR", res)

    def test_task_05_list_all(self):
        """TASK-05: 'Show all my tasks including completed'"""
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            task_add("Completed Task", "yesterday")
            res = task_list("all")
            self.assertIn("Completed Task", res)

    def test_task_06_cancel_task(self):
        """TASK-06: 'Cancel task 1'"""
        with patch("runtime.functions.get_connection", return_value=self.test_conn), \
             patch("runtime.functions.init_db"):
            task_add("Temporary Task", "today")
            res = task_cancel(1)
            self.assertEqual(res, "Task #1 has been cancelled.")

    # =========================================================================
    # Pillar 6: Trash Safety Gate (Mocked)
    # =========================================================================
    @patch.dict(os.environ, {"NANOHAT_AUTO_APPROVE_DESTRUCTIVE": "0"}, clear=False)
    @patch("runtime.functions.sys.stdin.isatty", return_value=False)
    def test_trash_01_headless_gate(self, mock_isatty):
        """TRASH-01: 'Empty the trash' -> Headless safety gate check"""
        tools = [t["function"]["name"] for t in route_tools("Empty the trash", ALL_TOOLS)]
        self.assertIn("empty_trash", tools)
        res = empty_trash()
        self.assertIn("ERROR[aborted]: Destructive action 'empty_trash' requires an interactive TTY", res)

    @patch.dict(os.environ, {"NANOHAT_AUTO_APPROVE_DESTRUCTIVE": "1"}, clear=False)
    @patch("runtime.functions.subprocess.run")
    def test_trash_02_auto_approve(self, mock_run):
        """TRASH-02: Auto-approved empty trash mock"""
        mock_run.return_value = MagicMock(returncode=0)
        res = empty_trash()
        self.assertIn("Trash emptied successfully (auto-approved)", res)

    # =========================================================================
    # Pillar 7: Typos, Slang & Colloquial Phrasings
    # =========================================================================
    def test_slang_01_mah_pet_name(self):
        """SLANG-01: 'Mah pet name is Nimo' -> memory_set"""
        tools = [t["function"]["name"] for t in route_tools("Mah pet name is Nimo", ALL_TOOLS)]
        self.assertIn("memory_set", tools)

    def test_slang_02_remeber_typo(self):
        """SLANG-02: 'Remeber my favorite city is Tokyo' -> memory_set"""
        tools = [t["function"]["name"] for t in route_tools("Remeber my favorite city is Tokyo", ALL_TOOLS)]
        self.assertIn("memory_set", tools)

    def test_slang_03_yo_what_day(self):
        """SLANG-03: 'Yo what day is it?' -> get_datetime"""
        tools = [t["function"]["name"] for t in route_tools("Yo what day is it?", ALL_TOOLS)]
        self.assertIn("get_datetime", tools)

    def test_slang_04_bluetooth_fired_up(self):
        """SLANG-04: 'Is bluetooth fired up?' -> toggle_bluetooth"""
        tools = [t["function"]["name"] for t in route_tools("Is bluetooth fired up?", ALL_TOOLS)]
        self.assertIn("toggle_bluetooth", tools)

    def test_slang_05_battery_juice(self):
        """SLANG-05: 'How much juice is left in my battery?' -> system_health"""
        tools = [t["function"]["name"] for t in route_tools("How much juice is left in my battery?", ALL_TOOLS)]
        self.assertIn("system_health", tools)

    def test_slang_06_currnt_time_typo(self):
        """SLANG-06: 'Whats the currnt time?' -> get_datetime"""
        tools = [t["function"]["name"] for t in route_tools("Whats the currnt time?", ALL_TOOLS)]
        self.assertIn("get_datetime", tools)

    def test_slang_07_status_ollama_daemon(self):
        """SLANG-07: 'Status of ollama daemon' -> service_status"""
        tools = [t["function"]["name"] for t in route_tools("Status of ollama daemon", ALL_TOOLS)]
        self.assertTrue("service_status" in tools or "restart_service" in tools)

    def test_slang_08_worded_calculate(self):
        """SLANG-08: 'Can you calculate 120 times 3?' -> 360"""
        self.assertEqual(calculator("120 * 3"), "360")

    # =========================================================================
    # Pillar 8: Excluded Tools & Adversarial Distractors (ADR-007 Verification)
    # =========================================================================
    def test_adr_01_screenshot_excluded(self):
        """ADR-01: 'Take a screenshot of my screen' -> no screenshot tool in catalog"""
        tools = [t["function"]["name"] for t in route_tools("Take a screenshot of my screen", ALL_TOOLS)]
        self.assertNotIn("screenshot", tools)

    def test_adr_02_lock_screen_excluded(self):
        """ADR-02: 'Lock my screen right now' -> no screen lock tool in catalog"""
        tools = [t["function"]["name"] for t in route_tools("Lock my screen right now", ALL_TOOLS)]
        self.assertNotIn("lock_screen", tools)

    def test_adr_03_kill_process_excluded(self):
        """ADR-03: 'Kill process with PID 1234' -> does not falsely invoke restart_service"""
        tools = [t["function"]["name"] for t in route_tools("Kill process with PID 1234", ALL_TOOLS)]
        self.assertNotIn("restart_service", tools)

    def test_adr_04_open_firefox(self):
        """ADR-04: 'Open Firefox browser' -> launch_app (v3.1.0)"""
        tools = [t["function"]["name"] for t in route_tools("Open Firefox browser", ALL_TOOLS)]
        self.assertIn("launch_app", tools)

    def test_adr_05_google_search_excluded(self):
        """ADR-05: 'Search Google for latest Fedora news' -> offline only, no web_search"""
        tools = [t["function"]["name"] for t in route_tools("Search Google for latest Fedora news", ALL_TOOLS)]
        self.assertNotIn("web_search", tools)

    def test_adr_06_delete_home_dir_safety(self):
        """ADR-06: 'Delete my entire home directory' -> must NOT route to empty_trash"""
        tools = [t["function"]["name"] for t in route_tools("Delete my entire home directory", ALL_TOOLS)]
        self.assertNotIn("empty_trash", tools)

    def test_adr_07_chit_chat_no_tools(self):
        """ADR-07: 'Tell me a programming joke' -> fallback defaults capped at <= 4"""
        tools = [t["function"]["name"] for t in route_tools("Tell me a programming joke", ALL_TOOLS)]
        self.assertLessEqual(len(tools), 4)


if __name__ == "__main__":
    unittest.main()
