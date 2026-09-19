"""
test_router.py — Unit tests for the deterministic intent router and dynamic tool gater.
Verifies that user queries map accurately to cluster tools without cognitive overload (<= 4 tools).
100% standalone, zero hardware commands.
"""

import unittest
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools
from runtime.prompts import get_dynamic_prompt, BASE_SYSTEM_PROMPT, TOOL_SNIPPETS


class TestRouter(unittest.TestCase):
    def test_datetime_routing(self):
        queries = [
            "What is the date?",
            "What is current time?",
            "What day is it today?",
            "What is my timezone?",
            "What is the time right now?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("get_datetime", names, f"Query '{q}' failed to route to get_datetime. Got {names}")
            self.assertLessEqual(len(tools), 3, f"Query '{q}' returned too many tools: {names}")

    def test_service_routing(self):
        queries = [
            "What is ollama status?",
            "Is pipewire running?",
            "Check service status for wireplumber",
            "Restart pipewire",
            "Is docker daemon active?",
            "Check systemd unit ollama",
            "What is the status of java?",
            "What is the status of postgresql?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertTrue(
                "service_status" in names or "restart_service" in names,
                f"Query '{q}' failed to route to service tools. Got {names}"
            )
            # Must NOT route to toggle_bluetooth or toggle_wifi solely because of word 'status'
            if "wifi" not in q.lower() and "bluetooth" not in q.lower():
                self.assertNotIn("toggle_bluetooth", names, f"False activation of bluetooth on '{q}'")
                self.assertNotIn("toggle_wifi", names, f"False activation of wifi on '{q}'")

    def test_network_routing(self):
        # Wi-Fi specific
        wifi_tools = route_tools("What is wifi status?", ALL_TOOLS)
        wifi_names = [t["function"]["name"] for t in wifi_tools]
        self.assertIn("toggle_wifi", wifi_names)
        self.assertNotIn("toggle_bluetooth", wifi_names)

        # Bluetooth specific
        bt_tools = route_tools("Turn off bluetooth", ALL_TOOLS)
        bt_names = [t["function"]["name"] for t in bt_tools]
        self.assertIn("toggle_bluetooth", bt_names)
        self.assertNotIn("toggle_wifi", bt_names)

    def test_hardware_routing(self):
        # Battery / Health
        health_tools = route_tools("What is my battery level?", ALL_TOOLS)
        health_names = [t["function"]["name"] for t in health_tools]
        self.assertIn("system_health", health_names)

        # Power profile
        pwr_tools = route_tools("Switch power profile to performance", ALL_TOOLS)
        pwr_names = [t["function"]["name"] for t in pwr_tools]
        self.assertIn("power_profile", pwr_names)

        # RAM and CPU isolation: must NOT include power_profile to prevent 270M confusion
        for ram_q in ["What is the RAM status?", "What is the RAM usage?", "What is my current RAM usage?", "What is CPU usage?"]:
            r_tools = route_tools(ram_q, ALL_TOOLS)
            r_names = [t["function"]["name"] for t in r_tools]
            self.assertIn("system_health", r_names, f"Query '{ram_q}' failed to route to system_health")
            self.assertNotIn("power_profile", r_names, f"Query '{ram_q}' incorrectly included power_profile")

    def test_memory_intent_refinements(self):
        # Identity statement routing to memory_set
        set_cases = [
            "My name is Milo?",
            "My name is Milo",
            "My pet name is Nimo?",
            "Mah pet name is Nimo?",
            "Remeber myy favorite editor is Neovim?",
            "Remember that my favorite distro is Fedora",
            "I prefer python over rust"
        ]
        for q in set_cases:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("memory_set", names, f"Query '{q}' failed to route to memory_set. Got {names}")

        # Identity query routing to memory_get
        get_cases = [
            "What is my name?",
            "What is my favorite distro?",
            "What is my pet name?",
            "Who am I?",
            "Do you recall my editor?"
        ]
        for q in get_cases:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("memory_get", names, f"Query '{q}' failed to route to memory_get. Got {names}")

        # Ensure RAM queries do NOT route to memory tools despite the word 'memory'
        ram_mem_tools = route_tools("What is my memory usage?", ALL_TOOLS)
        ram_mem_names = [t["function"]["name"] for t in ram_mem_tools]
        self.assertIn("system_health", ram_mem_names)
        self.assertNotIn("memory_get", ram_mem_names)

    def test_math_routing(self):
        queries = [
            "Calculate 7+7*18",
            "What is 45 * 12?",
            "100 / 4"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("calculator", names, f"Query '{q}' failed to route to calculator")

    def test_trash_routing(self):
        tools = route_tools("Empty the trash bin", ALL_TOOLS)
        names = [t["function"]["name"] for t in tools]
        self.assertIn("empty_trash", names)

    def test_fallback_unmatched_query(self):
        tools = route_tools("Hello there!", ALL_TOOLS)
        self.assertTrue(len(tools) > 0)
        self.assertLessEqual(len(tools), 4)

    def test_dynamic_prompt_assembly(self):
        # Only active tools should have snippets in prompt
        prompt = get_dynamic_prompt(["get_datetime"])
        self.assertIn("- Use get_datetime", prompt)
        self.assertNotIn("- Use calculator", prompt)
        self.assertNotIn("- Use toggle_bluetooth", prompt)
        self.assertNotIn("- Use service_status", prompt)

        prompt_svc = get_dynamic_prompt(["service_status", "restart_service"])
        self.assertIn("- Use service_status", prompt_svc)
        self.assertIn("- Use restart_service", prompt_svc)
        self.assertNotIn("- Use empty_trash", prompt_svc)


if __name__ == "__main__":
    unittest.main()
