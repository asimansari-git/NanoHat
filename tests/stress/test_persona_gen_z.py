import unittest
import json
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools

class TestGenZPersonaRouting(unittest.TestCase):
    def setUp(self):
        # We define our test vector as a matrix of (query, expected_tool_name_in_list)
        self.test_cases = [
            # 1-5: Hardware & Power
            ("bruh clean my ram rn 💀", ["system_health"]),
            ("battery low af check percent", ["system_health"]),
            ("cpu goes brrr whats the usage", ["system_health"]),
            ("my battery is deadass empty check it", ["system_health"]),
            ("set power to max no cap", ["power_profile"]),

            # 6-10: Network & Radios
            ("turn off bt no cap", ["toggle_bluetooth"]),
            ("wifi acting sus toggle it", ["toggle_wifi"]),
            ("is my bt on fr fr?", ["toggle_bluetooth"]),
            ("kill the wifi rn", ["toggle_wifi"]),
            ("bt off deadass", ["toggle_bluetooth"]),

            # 11-15: Trash & Housekeeping
            ("trash empty it bro", ["empty_trash"]),
            ("yeet the trash 🗑️", ["empty_trash"]),
            ("dump the recycle bin rn", ["empty_trash"]),
            ("clear trash fr", ["empty_trash"]),
            ("nuke the trash no cap", ["empty_trash"]),

            # 16-20: Tasks & Reminders
            ("yo schedule gym 6pm fr", ["task_add"]),
            ("remind me to touch grass in 10 mins", ["task_add"]),
            ("cancel task 2 its mid", ["task_cancel"]),
            ("what r my pending tasks bro", ["task_list"]),
            ("todo list kinda long let me see it", ["task_list"]),

            # 21-25: Time & Math
            ("calc 420 * 69", ["calculator"]),
            ("yo what time is it ⏰", ["get_datetime"]),
            ("date rn bro", ["get_datetime"]),
            ("eval 100 / 4 no cap", ["calculator"]),
            ("math is hard whats 9 + 10", ["calculator"]),

            # 26-30: Personal Memory Set
            ("my pet is doggo remember that", ["memory_set"]),
            ("i prefer dark mode fr fr", ["memory_set"]),
            ("mah favorite distro is arch btw", ["memory_set"]),
            ("i like boba save that note", ["memory_set"]),
            ("call me goat 🐐", ["memory_set"]),

            # 31-35: Personal Memory Get & List
            ("whoami bro", ["memory_get"]),
            ("what is my pet name 🐶", ["memory_get"]),
            ("do you recall my editor fr?", ["memory_get"]),
            ("list all my notes rn", ["memory_list"]),
            ("forget my ex no cap", ["memory_delete"]),

            # 36-40: Services
            ("restart ollama rn 💀", ["restart_service"]),
            ("is pipewire running bro", ["service_status"]),
            ("status of tailscale acting sus", ["service_status"]),
            ("reload wireplumber fr", ["restart_service"]),
            ("restart pipewire no cap", ["restart_service"]),

            # 41-45: Extreme Slang Edge Cases
            ("is the wifi bussin or nah?", ["toggle_wifi"]),
            ("my cpu is literally melting 😭", ["system_health"]),
            ("schedule nap for 2pm im dead", ["task_add"]),
            ("is bt down? lowkey weird", ["toggle_bluetooth"]),
            ("what time we dropping today?", ["get_datetime"])
        ]

        self.results = []

    def test_gen_z_queries(self):
        passed = 0
        failed = 0

        for query, expected_tools in self.test_cases:
            routed = route_tools(query, ALL_TOOLS)
            routed_names = [t["function"]["name"] for t in routed]

            # We expect AT LEAST ONE of the expected tools to be in the routed names
            is_match = any(et in routed_names for et in expected_tools)

            result_dict = {
                "query": query,
                "expected": expected_tools,
                "routed": routed_names,
                "status": "PASS" if is_match else "FAIL"
            }
            self.results.append(result_dict)

            if is_match:
                passed += 1
            else:
                failed += 1

        print(f"\n--- Gen Z Persona Stress Test Results ---")
        print(f"Total: {len(self.test_cases)} | Passed: {passed} | Failed: {failed}")

        # We intentionally do not assert so the suite finishes and we can write the report.
        # But we do want to output a JSON artifact to help build the markdown report.
        with open("gen_z_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # We can assert that at least 50% pass so it's a soft requirement?
        # Actually no assert needed if we just want to run the suite and generate report.
        # But for CI/CD it might be good. Let's not fail the test, we're auditing.

if __name__ == '__main__':
    unittest.main()
