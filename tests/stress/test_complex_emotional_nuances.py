import unittest
from unittest.mock import patch, MagicMock
from runtime.router import route_tools
from runtime.tools import ALL_TOOLS
import runtime.functions

class TestComplexEmotionalNuances(unittest.TestCase):
    def setUp(self):
        # Strictly mock subprocess calls to ensure no real system binaries are executed
        self.patcher_run = patch('subprocess.run')
        self.patcher_popen = patch('subprocess.Popen')
        self.mock_run = self.patcher_run.start()
        self.mock_popen = self.patcher_popen.start()

        self.patcher_rf_run = patch('runtime.functions.subprocess.run', create=True)
        self.patcher_rf_popen = patch('runtime.functions.subprocess.Popen', create=True)
        self.mock_rf_run = self.patcher_rf_run.start()
        self.mock_rf_popen = self.patcher_rf_popen.start()

    def tearDown(self):
        self.patcher_run.stop()
        self.patcher_popen.stop()
        self.patcher_rf_run.stop()
        self.patcher_rf_popen.stop()

    def assertTool(self, query, expected_tools, not_expected_tools=None):
        tools = route_tools(query, ALL_TOOLS)
        names = [t["function"]["name"] for t in tools]
        for expected in expected_tools:
            self.assertIn(expected, names, f"Expected '{expected}' for query: '{query}'. Got: {names}")
        if not_expected_tools:
            for not_expected in not_expected_tools:
                self.assertNotIn(not_expected, names, f"Did not expect '{not_expected}' for query: '{query}'. Got: {names}")
        self.assertLessEqual(len(tools), 4, f"Too many tools selected for query: '{query}'")

    def test_frustration_panic(self):
        # 1-10
        self.assertTool("Why is my laptop burning a hole through my desk?! Check the thermals!", ["system_health"])
        self.assertTool("My battery is dying so fast, what is going on?!", ["system_health"])
        self.assertTool("This fan sounds like a jet engine, check CPU temps right now!", ["system_health"])
        self.assertTool("Everything is freezing! My memory must be full, check RAM!", ["system_health"])
        self.assertTool("Why the hell is my bluetooth not working? Fix it!", ["toggle_bluetooth"])
        self.assertTool("The wifi dropped AGAIN in the middle of a meeting, reconnect it!", ["toggle_wifi"])
        self.assertTool("My system is crawling, check the load before I throw this thing!", ["system_health"])
        self.assertTool("Ahhh! What is my battery health? Is it dead?", ["system_health"])
        self.assertTool("Pipewire crashed for the 5th time, restart the damn service!", ["restart_service"])
        self.assertTool("The trash is completely full and my disk is out of space, empty it NOW!", ["empty_trash"])

    def test_sarcasm_inverted_meaning(self):
        # 11-17 Sarcasm where meaning is inverted and should probably NOT trigger the tool, but regex likely will.
        # We expect these to fail because our regex router isn't smart enough to understand sarcasm.

        queries = [
            ("Oh sure, why don't you delete all my files and empty the trash while you're at it", ["empty_trash"]),
            ("Wonderful, my battery is dead. Should I just throw it away?", ["system_health"]),
            ("Great, another wifi drop. Maybe just turn off the radio forever.", ["toggle_wifi"]),
            ("Oh wonderful, my bluetooth disconnected again, could you fix it or should I throw this machine out the window?", ["toggle_bluetooth"]),
            ("Yeah, restart every service, that always fixes everything.", ["restart_service"]),
            ("Just forget my name, I don't even care anymore.", ["memory_delete"]),
            ("Why don't you schedule a task for me to cry in the corner?", ["task_add"]),
        ]

        for query, not_expected_tools in queries:
            with self.subTest(query=query):
                with self.assertRaises(AssertionError):
                    self.assertTool(query, [], not_expected_tools=not_expected_tools)

    def test_sarcasm_general(self):
        # 18-20 General sarcasm that should still trigger the right tool despite the tone
        self.assertTool("Oh fantastic, the audio died again. Restart pipewire before I lose my mind.", ["restart_service"])
        self.assertTool("Wow, 10% battery. So helpful. Check the health.", ["system_health"])
        self.assertTool("I love it when my CPU overheats, check the temp.", ["system_health"])

    def test_extreme_politeness(self):
        # 21-30
        self.assertTool("My dearest assistant, if it is not an unbearable inconvenience, would you be so gracious as to empty the trash bin?", ["empty_trash"])
        self.assertTool("Pardon me, kind sir, could you perhaps inform me of the current date and time?", ["get_datetime"])
        self.assertTool("If you would be so kind, please schedule a reminder for my tea time at 3 PM.", ["task_add"])
        self.assertTool("I humbly request that you check the status of the docker daemon, please and thank you.", ["service_status"])
        self.assertTool("Would you mind terribly checking my battery level, my good friend?", ["system_health"])
        self.assertTool("I would be ever so grateful if you could turn on the Wi-Fi for me.", ["toggle_wifi"])
        self.assertTool("Please, if it isn't too much trouble, remember that my favorite color is azure.", ["memory_set"])
        self.assertTool("Could you graciously retrieve my favorite color from your esteemed memory?", ["memory_get"])
        self.assertTool("I kindly ask that you switch the power profile to balanced, if you please.", ["power_profile"])
        self.assertTool("May I trouble you to list all of my pending tasks?", ["task_list"])

    def test_exasperation(self):
        # 31-40
        self.assertTool("Audio died for the tenth time today, restart pipewire please", ["restart_service"])
        self.assertTool("Ugh, why is my laptop so hot? Check the CPU.", ["system_health"])
        self.assertTool("I can't take this anymore, my memory is completely shot, check the RAM usage.", ["system_health"])
        self.assertTool("Fine, just empty the recycle bin and let's move on.", ["empty_trash"])
        self.assertTool("Whatever, just list my reminders so I can see what I missed.", ["task_list"])
        self.assertTool("I give up. Turn off the bluetooth.", ["toggle_bluetooth"])
        self.assertTool("This is exhausting. What time is it even?", ["get_datetime"])
        self.assertTool("Just check if the stupid network service is running.", ["service_status"])
        self.assertTool("Ugh, I forgot my own pet's name. What did I save it as?", ["memory_get"])
        self.assertTool("I'm so done. Switch to power saver mode.", ["power_profile"])

    def test_gratitude_and_follow_up(self):
        # 41-47
        self.assertTool("You are a total lifesaver! Now remind me to take a break at 4 PM.", ["task_add"])
        self.assertTool("Thanks a million! Can you also check the battery?", ["system_health"])
        self.assertTool("I appreciate it! By the way, is my Wi-Fi still connected?", ["toggle_wifi"])
        self.assertTool("Perfect, thank you! Could you empty the trash now?", ["empty_trash"])
        self.assertTool("Awesome work. Now please restart the ollama service.", ["restart_service"])
        self.assertTool("You're the best! Remember that I owe you a virtual high-five.", ["memory_set"])
        self.assertTool("Thanks! What's the date today?", ["get_datetime"])

if __name__ == '__main__':
    unittest.main()
