import unittest
from runtime.router import route_tools
from runtime.tools import ALL_TOOLS

class TestComplexSemanticPolysemy(unittest.TestCase):
    """
    Stress tests for the deterministic intent router.
    Evaluates router precision in distinguishing overlapping keywords and routing
    to the single most appropriate tool without collisions.
    """
    def setUp(self):
        # conftest.py already mocks system binaries. We don't need to do it here.
        pass

    def check_route(self, query, expected_tools, exact=True):
        tools = route_tools(query, ALL_TOOLS)
        tool_names = [t["function"]["name"] for t in tools]
        if exact:
            self.assertCountEqual(tool_names, expected_tools, f"Query '{query}' routed to {tool_names}, expected {expected_tools}")
        else:
            for et in expected_tools:
                self.assertIn(et, tool_names, f"Query '{query}' routed to {tool_names}, expected to contain {et}")

    # ==========================
    # 1. "Remember" Polysemy
    # ==========================
    def test_remember_note(self):
        self.check_route("Remember I like vim", ["memory_set"])
        self.check_route("Remember my favorite color is blue", ["memory_set"])
        self.check_route("Please remember that my dog's name is Rex", ["memory_set"])

    @unittest.expectedFailure
    def test_remember_task(self):
        # Expected: ["task_add", "task_list"]
        self.check_route("Remember to water the plants", ["task_add", "task_list"])
        self.check_route("Remember to buy milk at 5pm", ["task_add", "task_list"])

    @unittest.expectedFailure
    def test_remember_ambiguous(self):
        # Expected: task tools
        self.check_route("Remember to call mom", ["task_add", "task_list"])

    # ==========================
    # 2. "Power" Polysemy
    # ==========================
    @unittest.expectedFailure
    def test_power_battery(self):
        # 'Power status' -> battery/cpu/ram
        self.check_route("Power status", ["system_health"])

    def test_power_profile(self):
        self.check_route("Set power to performance", ["power_profile"])
        self.check_route("Turn on power saver", ["power_profile"])

    def test_power_radio(self):
        self.check_route("Power on wifi", ["toggle_wifi", "power_profile"])
        self.check_route("Power off bluetooth", ["toggle_bluetooth", "power_profile"])

    # ==========================
    # 3. "Trash" Polysemy
    # ==========================
    def test_trash_desktop(self):
        self.check_route("Empty trash", ["empty_trash"])
        self.check_route("Clear the recycle bin", ["empty_trash"])

    @unittest.expectedFailure
    def test_trash_memory(self):
        # 'Trash my saved notes' should ideally go to memory_delete, but 'trash' triggers empty_trash
        self.check_route("Trash my saved notes", ["memory_delete"])

    # ==========================
    # 4. "Run / Launch" Polysemy
    # ==========================
    def test_run_app(self):
        self.check_route("Run firefox", ["launch_app"])
        self.check_route("Launch calculator", ["launch_app"])

    def test_run_diagnostic(self):
        # 'Is it running hot?' should trigger system_health
        self.check_route("Is it running hot?", ["system_health"])

    def test_run_daemon(self):
        self.check_route("Is pipewire running?", ["service_status", "restart_service"])

    # ==========================
    # 5. "Service" Polysemy
    # ==========================
    def test_service_daemon(self):
        self.check_route("Restart the docker service", ["restart_service", "service_status"])

    @unittest.expectedFailure
    def test_service_daemon_bluetooth(self):
        self.check_route("Service status bluetooth", ["service_status", "restart_service"])

    @unittest.expectedFailure
    def test_service_task(self):
        # 'Remind me to service car' should go to task_add, but 'service' triggers service_status
        self.check_route("Remind me to service car", ["task_add", "task_list"])

    # ==========================
    # 6. "Clear" Polysemy
    # ==========================
    @unittest.expectedFailure
    def test_clear_memory(self):
        self.check_route("Clear my favorite editor", ["memory_delete"])

    def test_clear_trash(self):
        self.check_route("Clear trash", ["empty_trash"])

    # ==========================
    # 7. "Status" Polysemy
    # ==========================
    def test_status_wifi(self):
        self.check_route("Status of wifi", ["toggle_wifi"])

    def test_status_battery(self):
        self.check_route("Status of battery", ["system_health"])

    def test_status_daemon(self):
        self.check_route("Status of nginx", ["service_status", "restart_service"])

    # ==========================
    # 8. "Time" Polysemy
    # ==========================
    def test_time_clock(self):
        self.check_route("What time is it?", ["get_datetime"])

    @unittest.expectedFailure
    def test_time_task(self):
        self.check_route("Set a timer for 10 minutes", ["task_add", "task_list"])

    # ==========================
    # 9. "Memory" Polysemy
    # ==========================
    @unittest.expectedFailure
    def test_memory_ram(self):
        self.check_route("How much memory is used?", ["system_health"])

    def test_memory_note(self):
        self.check_route("Show my saved memories", ["memory_list"])

    # ==========================
    # 10. "Hot/Warm/Thermal" Polysemy
    # ==========================
    def test_hot_system(self):
        self.check_route("Is my laptop too hot?", ["system_health"])

    @unittest.expectedFailure
    def test_hot_weather(self):
        self.check_route("Is it hot outside today?", ["get_datetime"])

    # ==========================
    # 11. "Turn" Polysemy
    # ==========================
    def test_turn_wifi(self):
        self.check_route("Turn on wifi", ["toggle_wifi"])
        self.check_route("Turn off wifi", ["toggle_wifi"])

    # ==========================
    # 12. "Check" Polysemy
    # ==========================
    def test_check_battery(self):
        self.check_route("Check battery", ["system_health"])

    def test_check_service(self):
        self.check_route("Check if ollama is running", ["service_status", "restart_service"])

    # ==========================
    # 13. "Fast/Slow" Polysemy
    # ==========================
    def test_slow_system(self):
        self.check_route("My computer is slow", ["system_health"])

    @unittest.expectedFailure
    def test_slow_wifi(self):
        # 'My wifi is slow' might trigger toggle_wifi instead of system_health, but contextually both might make sense.
        self.check_route("My wifi is slow", ["system_health"])

    # ==========================
    # 14. "Profile" Polysemy
    # ==========================
    def test_power_profile_word(self):
        self.check_route("Change profile to balanced", ["power_profile"])

    @unittest.expectedFailure
    def test_profile_memory(self):
        self.check_route("Remember my profile name is Jules", ["memory_set"])

    # ==========================
    # 15. "Kill" Polysemy
    # ==========================
    def test_kill_process(self):
        self.check_route("Kill the firefox process", ["restart_service", "service_status"])

    @unittest.expectedFailure
    def test_kill_task(self):
        self.check_route("Kill the alarm", ["task_cancel", "task_list"])

    # ==========================
    # 16. Edge Cases and Overlaps
    # ==========================
    @unittest.expectedFailure
    def test_wifi_service(self):
        self.check_route("Restart wifi service", ["toggle_wifi"])

    def test_forget_note(self):
        self.check_route("Forget I like apples", ["memory_delete"])

    def test_forget_wifi(self):
        self.check_route("Forget this wifi network", ["toggle_wifi"])


if __name__ == '__main__':
    unittest.main()
