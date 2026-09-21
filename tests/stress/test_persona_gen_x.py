import unittest
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools

class TestPersonaGenX(unittest.TestCase):
    def test_polite_datetime(self):
        queries = [
            "Good morning. Could you please be so kind as to tell me the current date and time?",
            "I would appreciate it if you could inform me of the current time in standard 12-hour format.",
            "Pardon me, might you have the current date handy for my records?",
            "Hello there, kindly provide me with today's date, if you would not mind.",
            "Could you please let me know what day of the week it is presently?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("get_datetime", names, f"Query '{q}' failed to route to get_datetime. Got {names}")
            self.assertLessEqual(len(tools), 4, f"Query '{q}' returned too many tools: {names}")

    def test_formal_trash(self):
        queries = [
            "Kindly delete the contents of my recycling bin at your earliest convenience.",
            "Could you please empty the trash bin for me?",
            "I would like you to permanently remove the items currently sitting in the recycle bin.",
            "Please clear out the recycling bin so I can free up some storage space.",
            "I request that you empty the desktop trash folder, if you please."
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("empty_trash", names, f"Query '{q}' failed to route to empty_trash. Got {names}")
            self.assertLessEqual(len(tools), 4)

    @unittest.expectedFailure
    def test_traditional_memory_set(self):
        queries = [
            "I would like to store a note that my insurance policy number is 98421.",
            "Please make a note in my file that my preferred text editor is Microsoft Word.",
            "Kindly remember that my favorite color is navy blue, for future reference.",
            "Could you please save a reminder that my grandson's name is Timothy?",
            "I require you to memorize that my primary operating system is Windows 95."
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("memory_set", names, f"Query '{q}' failed to route to memory_set. Got {names}")
            self.assertLessEqual(len(tools), 4)

    @unittest.expectedFailure
    def test_traditional_memory_get(self):
        queries = [
            "Could you please retrieve the note containing my insurance policy number?",
            "I would be grateful if you could remind me of my grandson's name from your records.",
            "Please look up what I previously stated as my preferred text editor.",
            "Might you be able to recall the favorite color I had you memorize?",
            "I have forgotten, could you inform me of the primary operating system I asked you to store?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("memory_get", names, f"Query '{q}' failed to route to memory_get. Got {names}")
            self.assertLessEqual(len(tools), 4)

    @unittest.expectedFailure
    def test_polite_system_health(self):
        queries = [
            "Could you please be so kind as to check my available hard drive space and memory?",
            "I would greatly appreciate it if you could inform me of the current CPU utilization on my machine.",
            "Please provide a status report on my laptop's battery life, if you would not mind.",
            "Kindly check how much RAM is currently being utilized by the system.",
            "I am concerned about my computer's performance. Could you please run a diagnostic on the system health?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("system_health", names, f"Query '{q}' failed to route to system_health. Got {names}")
            self.assertLessEqual(len(tools), 4)

    def test_formal_networking(self):
        queries = [
            "Could you please establish a connection to the local Wi-Fi network for me?",
            "I would like to request that you disable the Bluetooth radio adapter, please.",
            "Kindly inform me if the Wireless Fidelity interface is currently active.",
            "Please turn on the Wi-Fi so that I may access the World Wide Web.",
            "I need to pair a peripheral. Could you please activate the Bluetooth capabilities?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            # Must route to toggle_wifi or toggle_bluetooth based on the query
            if "wi-fi" in q.lower() or "wireless" in q.lower():
                self.assertIn("toggle_wifi", names, f"Query '{q}' failed to route to toggle_wifi. Got {names}")
            if "bluetooth" in q.lower():
                self.assertIn("toggle_bluetooth", names, f"Query '{q}' failed to route to toggle_bluetooth. Got {names}")
            self.assertLessEqual(len(tools), 4)

    @unittest.expectedFailure
    def test_traditional_tasks(self):
        queries = [
            "I would like to schedule a reminder for my 3 PM appointment with Dr. Smith.",
            "Could you please add 'buy groceries' to my to-do list for tomorrow morning?",
            "Kindly read back all of the pending tasks you have on file for me.",
            "Please cancel the reminder I previously set regarding the car maintenance.",
            "I request that you create an alert to notify me when the laundry is finished."
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            if "read back" in q.lower() or "pending tasks" in q.lower():
                self.assertIn("task_list", names, f"Query '{q}' failed to route to task_list. Got {names}")
            elif "cancel" in q.lower():
                self.assertIn("task_cancel", names, f"Query '{q}' failed to route to task_cancel. Got {names}")
            else:
                self.assertIn("task_add", names, f"Query '{q}' failed to route to task_add. Got {names}")
            self.assertLessEqual(len(tools), 4)

    def test_formal_services(self):
        queries = [
            "Could you please verify if the Docker background service is currently operating?",
            "I would appreciate it if you could restart the Pipewire audio daemon for me.",
            "Kindly check the systemd status for the Ollama server, if you please.",
            "Please inform me whether the print spooler service has failed.",
            "I request that you reload the configuration for the web server process."
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertTrue(
                "service_status" in names or "restart_service" in names,
                f"Query '{q}' failed to route to service tools. Got {names}"
            )
            self.assertLessEqual(len(tools), 4)

    @unittest.expectedFailure
    def test_polite_calculator(self):
        queries = [
            "Could you please assist me with some arithmetic? What is the result of 15 multiplied by 4?",
            "I would be grateful if you could calculate the sum of 250 and 375 for me.",
            "Please evaluate the mathematical expression: 100 divided by 4 plus 10.",
            "Kindly compute the total for my expenses: 45 plus 82 plus 115.",
            "I am trying to balance my checkbook. Could you tell me what 500 minus 32.50 is?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("calculator", names, f"Query '{q}' failed to route to calculator. Got {names}")
            self.assertLessEqual(len(tools), 4)

if __name__ == "__main__":
    unittest.main()
