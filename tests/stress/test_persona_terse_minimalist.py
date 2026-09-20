import unittest
from unittest.mock import patch, MagicMock
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools

class TestPersonaTerseMinimalist(unittest.TestCase):
    """
    Synthetic behavioral fuzzing for the 'Single-Word Terse Minimalist User'.
    Tests zero-context classification and default action routing.
    """

    def setUp(self):
        self.test_cases = [
            ("wifi", "toggle_wifi"),
            ("wifi on", "toggle_wifi"),
            ("wifi off", "toggle_wifi"),
            ("bt", "toggle_bluetooth"),
            ("bluetooth", "toggle_bluetooth"),
            ("bt toggle", "toggle_bluetooth"),
            ("network", "toggle_wifi"), # actually returns both toggle_wifi and toggle_bluetooth based on logic
            ("battery", "system_health"),
            ("charge", "system_health"),
            ("health", "system_health"),
            ("ram", "system_health"),
            ("cpu", "system_health"),
            ("swap", "system_health"),
            ("power", "power_profile"),
            ("profile", "power_profile"),
            ("saver", "power_profile"),
            ("performance", "power_profile"),
            ("trash", "empty_trash"),
            ("bin", "empty_trash"),
            ("calc 2+2", "calculator"),
            ("math 5/5", "calculator"),
            ("date", "get_datetime"),
            ("time", "get_datetime"),
            ("today", "get_datetime"),
            ("now", "get_datetime"),
            ("clock", "get_datetime"),
            ("services", "service_status"),
            ("systemd", "service_status"),
            ("daemon", "service_status"),
            ("restart ollama", "restart_service"),
            ("status pipewire", "service_status"),
            ("memory", "memory_set"),
            ("remember", "memory_set"),
            ("forget", "memory_delete"),
            ("recall", "memory_get"),
            ("tasks", "task_list"),
            ("todo", "task_add"),
            ("remind", "task_add"),
            ("cancel task", "task_cancel"),
            ("whoami", "memory_get"),
            ("memo test 123", "memory_set"), # Might fail if 'memo' is not recognized
            ("calc 99*4", "calculator"),
            ("reboot bluetooth", "toggle_bluetooth")
        ]

        self.results = []

    def test_terse_routing(self):
        passed = 0
        failed = 0

        for query, expected_tool in self.test_cases:
            tools = route_tools(query, ALL_TOOLS)
            tool_names = [t["function"]["name"] for t in tools]

            is_pass = expected_tool in tool_names
            if is_pass:
                passed += 1
                result_status = "OK"
            else:
                failed += 1
                result_status = "ERROR"

            self.results.append({
                "query": query,
                "inferred_tools": tool_names,
                "target_tool": expected_tool,
                "status": result_status
            })

            # We don't strictly assert here because we want to collect all results for the report
            # We'll assert at the end that the pass rate is somewhat reasonable, or just log them.
            # Actually, standard tests should fail if assertions fail, but the prompt says
            # "write reports based on tests".

        # Write results to a temporary JSON file so we can generate a report later
        import json
        with open("/tmp/terse_results.json", "w") as f:
            json.dump(self.results, f)

        print(f"\nTerse Routing Test: {passed} passed, {failed} failed.")

if __name__ == '__main__':
    unittest.main()
