"""
test_semantic_router.py — Unit tests for the BGE semantic tool router in NanoHat v3.1.0.

Tests accuracy across direct intents, typo resilience, mathematical fast-paths,
hardware telemetry, and graceful fallback. Standalone, zero host side-effects.
"""

import unittest
from runtime.tools import ALL_TOOLS
from runtime.semantic_router import route_tools, get_semantic_router, SemanticToolRouter


class TestSemanticRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = get_semantic_router()

    def test_math_fast_path(self):
        queries = [
            "Calculate 7+7*18",
            "What is 45 * 12?",
            "100 / 4",
            "eval 256 * 14"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("calculator", names, f"Query '{q}' failed to route to calculator")
            self.assertLessEqual(len(tools), 4)

    def test_datetime_routing(self):
        queries = [
            "What is the date?",
            "What is current time?",
            "What day is it today?",
            "What is my timezone?",
            "What time is it right now?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("get_datetime", names, f"Query '{q}' failed to route to get_datetime. Got {names}")
            self.assertLessEqual(len(tools), 4)

    def test_battery_and_hardware_routing(self):
        # Direct and typo battery queries
        queries = [
            "What is my battery level?",
            "Check battery status",
            "What is my betery status?",
            "bttry status",
            "How much battery charge is left?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("system_health", names, f"Battery query '{q}' failed to include system_health: {names}")

        # Thermals and RAM
        hot_tools = route_tools("Why is my laptop heating up?", ALL_TOOLS)
        hot_names = [t["function"]["name"] for t in hot_tools]
        self.assertIn("system_health", hot_names)

        ram_tools = route_tools("What is my current RAM usage?", ALL_TOOLS)
        ram_names = [t["function"]["name"] for t in ram_tools]
        self.assertIn("system_health", ram_names)

    def test_power_profile_routing(self):
        tools = route_tools("Switch power profile to performance", ALL_TOOLS)
        names = [t["function"]["name"] for t in tools]
        self.assertIn("power_profile", names)

    def test_network_routing(self):
        wifi_tools = route_tools("What is wifi status?", ALL_TOOLS)
        wifi_names = [t["function"]["name"] for t in wifi_tools]
        self.assertIn("toggle_wifi", wifi_names)

        bt_tools = route_tools("Turn off bluetooth", ALL_TOOLS)
        bt_names = [t["function"]["name"] for t in bt_tools]
        self.assertIn("toggle_bluetooth", bt_names)

    def test_service_routing(self):
        queries = [
            "Is pipewire running?",
            "Check service status for wireplumber",
            "Restart pipewire",
            "Is ollama daemon active?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertTrue(
                "service_status" in names or "restart_service" in names,
                f"Query '{q}' failed to route to service tools: {names}"
            )

    def test_memory_routing(self):
        # Store
        set_tools = route_tools("Remember that my favorite editor is neovim", ALL_TOOLS)
        set_names = [t["function"]["name"] for t in set_tools]
        self.assertIn("memory_set", set_names)

        # Retrieve
        get_tools = route_tools("What is my favorite editor?", ALL_TOOLS)
        get_names = [t["function"]["name"] for t in get_tools]
        self.assertIn("memory_get", get_names)

    def test_task_routing(self):
        add_tools = route_tools("Remind me to stretch at 5pm", ALL_TOOLS)
        add_names = [t["function"]["name"] for t in add_tools]
        self.assertIn("task_add", add_names)

        list_tools = route_tools("What are my tasks for today?", ALL_TOOLS)
        list_names = [t["function"]["name"] for t in list_tools]
        self.assertIn("task_list", list_names)

    def test_trash_routing(self):
        tools = route_tools("Empty the trash bin", ALL_TOOLS)
        names = [t["function"]["name"] for t in tools]
        self.assertIn("empty_trash", names)

    def test_app_launch_routing(self):
        tools = route_tools("Launch firefox browser", ALL_TOOLS)
        names = [t["function"]["name"] for t in tools]
        self.assertIn("launch_app", names)

    def test_schema_contract(self):
        tools = route_tools("What is the time?", ALL_TOOLS)
        self.assertIsInstance(tools, list)
        self.assertTrue(len(tools) > 0)
        for t in tools:
            self.assertIn("type", t)
            self.assertEqual(t["type"], "function")
            self.assertIn("function", t)
            self.assertIn("name", t["function"])
            self.assertIn("description", t["function"])


if __name__ == "__main__":
    unittest.main()
