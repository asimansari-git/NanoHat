import unittest
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools

class TestComplexColloquialSlang(unittest.TestCase):
    """
    Stress tests for the router's handling of colloquial slang, regional dialects, and idioms.
    Tests verify if natural language utterances from different English variants are routed correctly.
    """

    def assert_tools(self, query: str, expected_tools: list):
        """Helper to assert that the routed tools contain the expected ones."""
        result = route_tools(query, ALL_TOOLS)
        routed_names = [tool["function"]["name"] for tool in result]
        for tool in expected_tools:
            self.assertIn(tool, routed_names, f"Expected '{tool}' in routed tools for query: '{query}'. Got: {routed_names}")

    # --- British / Commonwealth ---

    def test_british_dustbin(self):
        self.assert_tools("Fancy emptying the dustbin mate?", ["empty_trash"])

    def test_british_wireless(self):
        self.assert_tools("Turn off the wireless interface", ["toggle_wifi"])

    def test_british_time(self):
        self.assert_tools("Give us the time guv'nor", ["get_datetime"])

    def test_british_rubbish_bin(self):
        self.assert_tools("Empty the rubbish bin", ["empty_trash"])

    def test_british_lob_in_bin(self):
        self.assert_tools("Can you lob this in the bin?", ["empty_trash"])

    def test_british_flat_battery(self):
        self.assert_tools("Me battery's gone flat, innit", ["system_health"])

    def test_british_crank_up_performance(self):
        self.assert_tools("Oi, crank up the performance profile", ["power_profile"])

    def test_british_blue_teeth(self):
        self.assert_tools("Switch on the blue-teeth", ["toggle_bluetooth"])

    def test_british_quid_calculation(self):
        self.assert_tools("Calculate how much quid I owe: 50 * 4", ["calculator"])

    def test_british_diary_task(self):
        self.assert_tools("Chuck this task in me diary: tea at 4", ["task_add"])

    # --- Australian ---

    def test_australian_chugging_telly(self):
        self.assert_tools("Me laptop is fair dinkum chugging, check the telly... I mean CPU", ["system_health"])

    def test_australian_brekkie_task(self):
        self.assert_tools("Chuck this task in my list: grab brekkie tomorrow", ["task_add"])

    def test_australian_interwebs(self):
        self.assert_tools("Turn on the interwebs", ["toggle_wifi"])

    @unittest.expectedFailure
    def test_australian_juice(self):
        self.assert_tools("Check the juice level", ["battery"]) # No explicit battery word, routes to default

    def test_australian_garbo(self):
        self.assert_tools("Empty the garbo", ["empty_trash"])

    def test_australian_date_mate(self):
        self.assert_tools("What's the date today, mate?", ["get_datetime"])

    def test_australian_bucks_calc(self):
        self.assert_tools("Calculate 150 bucks divided by 5", ["calculator"])

    def test_australian_warm_rig(self):
        self.assert_tools("My rig's getting warm", ["system_health"])

    def test_australian_fire_up_browser(self):
        self.assert_tools("Fire up the browser", ["launch_app"])

    def test_australian_delete_memory(self):
        self.assert_tools("Delete that memory, mate", ["memory_delete"])

    # --- American ---

    def test_american_screaming_rig(self):
        self.assert_tools("Yo my rig is screaming, check the thermals", ["system_health"])

    def test_american_trash_can(self):
        self.assert_tools("Trash can is overflowing, dump it", ["empty_trash"])

    def test_american_fire_up_terminal(self):
        self.assert_tools("Fire up terminal", ["launch_app"])

    def test_american_calendar(self):
        self.assert_tools("Check my calendar for today", ["get_datetime"])

    def test_american_math(self):
        self.assert_tools("Can you do the math: 50 * 2?", ["calculator"])

    @unittest.expectedFailure
    def test_american_kill_app(self):
        self.assert_tools("Kill the lagging app", ["restart_service"])

    def test_american_wifi(self):
        self.assert_tools("Is my wifi connected?", ["toggle_wifi"])

    def test_american_remember_hamburger(self):
        self.assert_tools("Remember that I love hamburgers", ["memory_set"])

    def test_american_boot_up_firefox(self):
        self.assert_tools("Boot up firefox", ["launch_app"])

    def test_american_battery_saver(self):
        self.assert_tools("Switch to battery saver", ["power_profile"])

    # --- Indian / Subcontinent ---

    def test_indian_revert_battery(self):
        self.assert_tools("Kindly revert with the system battery status", ["system_health"])

    # "calculation" is not in RE_MATH_WORDS, but "do one calculation:" triggers RE_MATH_EXPR false positive sometimes? Wait.
    # Ah, let's see. In router, "Calculate" or "do the math" triggers.
    def test_indian_do_calculation(self):
        self.assert_tools("Do one calculation: 450 divided by 3", ["calculator"])

    def test_indian_wastebasket(self):
        self.assert_tools("Please clear the wastebasket", ["empty_trash"])

    def test_indian_bluetooth_device(self):
        self.assert_tools("Turn on the bluetooth device", ["toggle_bluetooth"])

    def test_indian_date(self):
        self.assert_tools("What's the date?", ["get_datetime"])

    def test_indian_heating_up(self):
        self.assert_tools("My PC is heating up too much", ["system_health"])

    def test_indian_prepone_task(self):
        self.assert_tools("Kindly prepone my scheduled task", ["task_list"])

    def test_indian_open_application(self):
        self.assert_tools("Open the application firefox", ["launch_app"])

    @unittest.expectedFailure
    def test_indian_doubt_ip(self):
        self.assert_tools("I have a doubt, what is my IP?", ["toggle_wifi"])

    def test_indian_do_the_needful(self):
        self.assert_tools("Please do the needful and restart the server", ["restart_service"])

if __name__ == '__main__':
    unittest.main()
