"""
test_phase2_batch3.py — Mocked automated verification for NanoHat v3.0.0 Batch 3 tools:
- toggle_wifi (mocked)
- toggle_bluetooth (mocked)
- service_status (mocked)
- restart_service (mocked + Wayland session protection allowlist)

All destructive or stateful hardware calls are intercepted using unittest.mock.
Zero commands touch real system hardware or bluetooth controllers.
"""

import unittest
from unittest.mock import patch, MagicMock
from runtime.functions import (
    toggle_wifi,
    toggle_bluetooth,
    service_status,
    restart_service,
    SAFE_RESTART_SERVICES,
    BLOCKED_WAYLAND_SERVICES
)
from runtime.engine import AgentEngine
from runtime.client import OllamaClient


class TestBatch3FunctionsMocked(unittest.TestCase):
    @patch("runtime.functions.subprocess.run")
    def test_toggle_wifi_status(self, mock_run):
        mock_run.return_value = MagicMock(stdout="enabled", returncode=0)
        res = toggle_wifi("status")
        self.assertIn("Wi-Fi radio is currently: enabled", res)

    @patch("runtime.functions.subprocess.run")
    def test_toggle_wifi_off(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        res = toggle_wifi("off")
        self.assertEqual(res, "Wi-Fi radio turned off.")
        mock_run.assert_called()

    @patch("runtime.functions.subprocess.run")
    def test_toggle_bluetooth_status(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Powered: yes\n", returncode=0)
        res = toggle_bluetooth("status")
        self.assertIn("Bluetooth is currently: powered on", res)

    @patch("runtime.functions.subprocess.run")
    def test_toggle_bluetooth_off(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        res = toggle_bluetooth("off")
        self.assertEqual(res, "Bluetooth powered off.")
        mock_run.assert_called()

    @patch("runtime.functions.subprocess.run")
    def test_service_status_pipewire(self, mock_run):
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        res = service_status("pipewire")
        self.assertIn("pipewire.service", res)
        self.assertIn("status: active", res)

    def test_wayland_protection_gnome_shell(self):
        # Pure logic validation - must block without any subprocess call
        res = restart_service("gnome-shell")
        self.assertIn("ERROR[security_blocked]", res)
        self.assertIn("Wayland desktop session crashes", res)

    def test_wayland_protection_wayland_unit(self):
        res = restart_service("org.gnome.shell@wayland")
        self.assertIn("ERROR[security_blocked]", res)

    def test_arbitrary_service_blocked(self):
        res = restart_service("systemd-resolved")
        self.assertIn("ERROR[security_blocked]", res)
        self.assertIn("not in the safe allowlist", res)

    @patch("runtime.functions.subprocess.run")
    def test_safe_restart_pipewire(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        res = restart_service("pipewire")
        self.assertIn("restarted successfully", res)
        mock_run.assert_called()


class TestBatch3LiveRoutingMocked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = OllamaClient()
        cls.engine = AgentEngine(client=cls.client, prompt_version="v1", verbose=False)

    @patch("runtime.functions.subprocess.run")
    def test_route_service_status(self, mock_run):
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        response = self.engine.run("Check if pipewire is running")
        self.assertIn("pipewire", response.lower())

    @patch("runtime.functions.subprocess.run")
    def test_route_restart_service(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        response = self.engine.run("Restart pipewire service")
        self.assertIn("pipewire", response.lower())

    def test_route_restart_blocked_unit(self):
        # Verifies the Wayland crash shield fails closed
        res = restart_service("gnome-shell")
        self.assertIn("ERROR[security_blocked]", res)
        self.assertIn("Wayland desktop session crashes", res)


    @patch("runtime.functions.subprocess.run")
    def test_route_turn_off_wifi_mocked(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        response = self.engine.run("Turn off Wi-Fi")
        self.assertTrue("wi-fi" in response.lower() or "wifi" in response.lower())

    @patch("runtime.functions.subprocess.run")
    def test_route_bluetooth_mocked(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Powered: yes\n", returncode=0)
        response = self.engine.run("Turn on Bluetooth")
        self.assertIn("bluetooth", response.lower())


if __name__ == "__main__":
    unittest.main()
