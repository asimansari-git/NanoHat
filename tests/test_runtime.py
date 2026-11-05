"""
test_v4_runtime.py — Exhaustive unit tests for NanoHat v4.1 (10-Tool Hardened Core).
Validates sandbox safety invariants, schema normalization, and prompt directives.
"""

import os
import unittest
from runtime.client import OllamaClient
from runtime.engine import AgentEngine
from runtime.functions import REGISTRY
from runtime.prompts import get_system_prompt
from runtime.tools import ALL_TOOLS


class TestNanoHatV41Runtime(unittest.TestCase):
    def setUp(self):
        os.environ["NANOHAT_SANDBOX"] = "1"
        self.client = OllamaClient()
        self.engine = AgentEngine(self.client, verbose=False)

    def test_strict_10_tool_catalog(self):
        """Ensure exactly the 10 core tools are registered and exported."""
        self.assertEqual(len(ALL_TOOLS), 10, "ALL_TOOLS must contain exactly 10 tool schemas")
        self.assertEqual(len(REGISTRY), 10, "REGISTRY must map exactly 10 executable functions")

        expected_tools = {
            "system_health",
            "power_profile",
            "toggle_wifi",
            "toggle_bluetooth",
            "service_status",
            "restart_service",
            "audio_control",
            "desktop_appearance",
            "disk_usage",
            "package_manager",
        }
        schema_names = {t["function"]["name"] for t in ALL_TOOLS}
        self.assertEqual(schema_names, expected_tools)
        self.assertEqual(set(REGISTRY.keys()), expected_tools)

    def test_system_prompt_structure_and_directives(self):
        """Verify the system prompt contains all 10 tools and core safety invariants."""
        prompt = get_system_prompt()

        # Operational directives
        self.assertIn("1. SYSTEM TOOL MODE (Emit <tool_call>):", prompt)
        self.assertIn("2. READ-ONLY SAFETY MANDATE:", prompt)
        self.assertIn("3. CONVERSATIONAL & CONCEPTUAL MODE (No Tools):", prompt)
        self.assertIn("4. REFUSAL & OUT-OF-SCOPE BOUNDARIES (No Tools):", prompt)
        self.assertIn("5. OPERATIONAL NEGATIONS & EXCLUSION BOUNDARIES:", prompt)

        # All 10 tools present in prompt bullets
        for tool_name in (
            "system_health", "power_profile", "toggle_wifi", "toggle_bluetooth",
            "service_status", "restart_service", "audio_control",
            "desktop_appearance", "disk_usage", "package_manager"
        ):
            self.assertIn(tool_name, prompt)

    def test_all_10_functions_execute_safely_in_sandbox(self):
        """Verify every tool returns simulated outputs without OS mutations in sandbox mode."""
        # 1. system_health
        health_all = REGISTRY["system_health"](metric="all")
        self.assertIn("CPU:", health_all)
        self.assertIn("RAM:", health_all)
        self.assertIn("Battery:", health_all)
        self.assertIn("GPU", health_all)

        health_cpu = REGISTRY["system_health"](metric="cpu")
        self.assertIn("CPU: 14%", health_cpu)

        health_gpu = REGISTRY["system_health"](metric="gpu")
        self.assertIn("GPU 0 (Intel Integrated): Active", health_gpu)

        # 2. power_profile
        prof_get = REGISTRY["power_profile"](action="get")
        self.assertIn("balanced", prof_get)
        prof_set = REGISTRY["power_profile"](action="set", profile="power-saver")
        self.assertIn("power-saver", prof_set)

        # 3. toggle_wifi
        wifi_stat = REGISTRY["toggle_wifi"](state="status")
        self.assertIn("enabled", wifi_stat)
        wifi_off = REGISTRY["toggle_wifi"](state="off")
        self.assertIn("turned off", wifi_off)

        # 4. toggle_bluetooth
        bt_stat = REGISTRY["toggle_bluetooth"](state="status")
        self.assertIn("powered on", bt_stat)
        bt_off = REGISTRY["toggle_bluetooth"](state="off")
        self.assertIn("powered off", bt_off)

        # 5. service_status
        svc_stat = REGISTRY["service_status"](service_name="pipewire")
        self.assertIn("pipewire.service' status: active", svc_stat)

        # 6. restart_service
        svc_restart = REGISTRY["restart_service"](service_name="pipewire")
        self.assertIn("restarted successfully", svc_restart)
        svc_blocked = REGISTRY["restart_service"](service_name="gnome-shell")
        self.assertIn("ERROR[security_blocked]", svc_blocked)
        svc_disallowed = REGISTRY["restart_service"](service_name="sshd")
        self.assertIn("ERROR[security_blocked]", svc_disallowed)

        # 7. audio_control
        aud_stat = REGISTRY["audio_control"](action="status")
        self.assertIn("Audio sink status", aud_stat)
        aud_mute = REGISTRY["audio_control"](action="mute")
        self.assertIn("muted", aud_mute)
        aud_vol = REGISTRY["audio_control"](action="set_volume", level=80)
        self.assertIn("80%", aud_vol)

        # 8. desktop_appearance
        theme_stat = REGISTRY["desktop_appearance"](setting="theme", value="status")
        self.assertIn("default", theme_stat)
        theme_set = REGISTRY["desktop_appearance"](setting="theme", value="dark")
        self.assertIn("Dark mode", theme_set)
        nl_set = REGISTRY["desktop_appearance"](setting="night_light", value="on")
        self.assertIn("Night Light turned on", nl_set)

        # 9. disk_usage
        disk = REGISTRY["disk_usage"](path="/")
        self.assertIn("Disk (/):", disk)

        # 10. package_manager
        pkg_inst = REGISTRY["package_manager"](action="is_installed", package_name="vlc")
        self.assertIn("installed", pkg_inst)
        pkg_search = REGISTRY["package_manager"](action="search", package_name="python3")
        self.assertIn("python3", pkg_search)
        pkg_cmd = REGISTRY["package_manager"](action="install_cmd", package_name="htop")
        self.assertIn("sudo dnf install -y htop", pkg_cmd)

    def test_engine_schema_normalization(self):
        """Test parameter alias remapping and default value fallback in engine."""
        # Alias: action -> state
        tool, args = self.engine.normalize_call("toggle_wifi", {"action": "off"})
        self.assertEqual(args.get("state"), "off")

        # Fallback: power_profile action defaults to get
        tool, args = self.engine.normalize_call("power_profile", {})
        self.assertEqual(args.get("action"), "get")

        # Fallback: system_health metric defaults to all
        tool, args = self.engine.normalize_call("system_health", {})
        self.assertEqual(args.get("metric"), "all")

        # Alias: directory -> path
        tool, args = self.engine.normalize_call("disk_usage", {"directory": "/home"})
        self.assertEqual(args.get("path"), "/home")

        # Direct execution via engine
        out = self.engine.execute_tool("toggle_bluetooth", {"action": "off"})
        self.assertIn("powered off", out)

    def test_fallback_tool_call_tag_extraction(self):
        """Test extraction of <tool_call> tags embedded in plain-text output."""
        raw_text = "Checking status... <tool_call>{\"name\": \"toggle_wifi\", \"arguments\": {\"state\": \"status\"}}</tool_call>"
        calls = self.engine._extract_fallback_tool_calls(raw_text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "toggle_wifi")
        self.assertEqual(calls[0]["function"]["arguments"]["state"], "status")


if __name__ == "__main__":
    unittest.main()
