import unittest
from unittest.mock import MagicMock, patch
import pytest

from runtime.engine import AgentEngine
from runtime.client import OllamaClient
from runtime.router import route_tools
from runtime.tools import ALL_TOOLS


class TestComplexConversationalFollowups(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=OllamaClient)
        self.engine = AgentEngine(client=self.client, prompt_version="v1", verbose=False)

    def test_routing_sequence_1_cpu_power(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("How hot is my CPU?", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("And what about the RAM?", ALL_TOOLS)])
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Turn on power saver mode then.", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_1_cpu_power_xfail(self):
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Is it saving now?", ALL_TOOLS)])

    def test_routing_sequence_2_service(self):
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("Is wireplumber service running?", ALL_TOOLS)])
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("Check its status once more", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_2_service_xfail(self):
        self.assertIn("restart_service", [t["function"]["name"] for t in route_tools("Restart it then", ALL_TOOLS)])

    def test_routing_sequence_3_memory(self):
        self.assertIn("memory_set", [t["function"]["name"] for t in route_tools("Remember my favorite editor is Neovim", ALL_TOOLS)])
        self.assertIn("memory_delete", [t["function"]["name"] for t in route_tools("Actually forget that", ALL_TOOLS)])
        self.assertIn("memory_set", [t["function"]["name"] for t in route_tools("Remember it is Emacs now", ALL_TOOLS)])

    def test_routing_sequence_4_network(self):
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Is wifi connected?", ALL_TOOLS)])
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("What about bluetooth?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_4_network_xfail(self):
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Turn it off", ALL_TOOLS)])

    def test_routing_sequence_5_math(self):
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("Calculate 10 + 15", ALL_TOOLS)])

    def test_routing_sequence_6_datetime(self):
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("What time is it?", ALL_TOOLS)])
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("And the date?", ALL_TOOLS)])
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("What day is today?", ALL_TOOLS)])

    def test_routing_sequence_7_battery_power(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("How much battery do I have left?", ALL_TOOLS)])
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Turn on power saver", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_7_battery_power_xfail(self):
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Is it saving now?", ALL_TOOLS)])

    def test_routing_sequence_8_trash(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Empty the trash", ALL_TOOLS)])
        self.assertIn("memory_set", [t["function"]["name"] for t in route_tools("Remember I like a clean desktop", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_8_trash_xfail(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Did you do it?", ALL_TOOLS)])

    def test_routing_sequence_9_apps(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Open firefox", ALL_TOOLS)])
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Actually open chromium instead", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_9_apps_xfail(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("What about terminal?", ALL_TOOLS)])

    def test_routing_sequence_10_tasks(self):
        self.assertIn("task_add", [t["function"]["name"] for t in route_tools("Remind me to eat at 5pm", ALL_TOOLS)])
        self.assertIn("task_add", [t["function"]["name"] for t in route_tools("Remind me to sleep at 10pm instead", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_10_tasks_xfail(self):
        self.assertIn("task_cancel", [t["function"]["name"] for t in route_tools("Cancel that", ALL_TOOLS)])

    @patch("runtime.engine.AgentEngine.execute_tool")
    def test_engine_multiturn_mocked(self, mock_execute):
        self.client.chat.side_effect = [
            {"message": {"content": "", "tool_calls": [{"function": {"name": "system_health", "arguments": '{"metric": "cpu"}'}}]}},
            {"message": {"content": "Your CPU is 45C."}},
            {"message": {"content": "", "tool_calls": [{"function": {"name": "system_health", "arguments": '{"metric": "ram"}'}}]}},
            {"message": {"content": "You have 16GB free."}}
        ]
        mock_execute.side_effect = ["CPU 45C", "16GB Free"]
        res1 = self.engine.run("How hot is my CPU?")
        self.assertEqual(res1, "Your CPU is 45C.")
        self.assertEqual(self.client.chat.call_count, 2)
        mock_execute.assert_any_call("system_health", {"metric": "cpu"})
        res2 = self.engine.run("And what about the RAM?")
        self.assertEqual(res2, "You have 16GB free.")
        self.assertEqual(self.client.chat.call_count, 4)
        mock_execute.assert_any_call("system_health", {"metric": "ram"})

    @patch("runtime.engine.AgentEngine.execute_tool")
    def test_engine_multiturn_anaphora_failure_mocked(self, mock_execute):
        self.client.chat.side_effect = [
            {"message": {"content": "", "tool_calls": [{"function": {"name": "service_status", "arguments": '{"service_name": "wireplumber"}'}}]}},
            {"message": {"content": "Yes, it is running."}},
            {"message": {"content": "I'm sorry, I don't have the tool to restart it."}}
        ]
        mock_execute.side_effect = ["active (running)"]
        res1 = self.engine.run("Is wireplumber service running?")
        self.assertEqual(res1, "Yes, it is running.")
        self.assertEqual(self.client.chat.call_count, 2)
        mock_execute.assert_any_call("service_status", {"service_name": "wireplumber"})
        res2 = self.engine.run("Restart it then")
        self.assertEqual(res2, "I'm sorry, I don't have the tool to restart it.")
        self.assertEqual(self.client.chat.call_count, 3)

    def test_routing_sequence_11_bluetooth(self):
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("Is bluetooth on?", ALL_TOOLS)])
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("Turn off bluetooth", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_11_bluetooth_xfail(self):
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("Turn it on", ALL_TOOLS)])

    def test_routing_sequence_12_music(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Open Spotify", ALL_TOOLS)])
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Launch music player", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_12_music_xfail(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Play it", ALL_TOOLS)])

    def test_routing_sequence_13_cpu(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Check CPU utilization", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("How much CPU is used?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_13_cpu_xfail(self):
        self.assertEqual(len(route_tools("Is it too high?", ALL_TOOLS)), 1)

    def test_routing_sequence_14_memory(self):
        self.assertIn("memory_set", [t["function"]["name"] for t in route_tools("Remember I love linux", ALL_TOOLS)])
        self.assertIn("memory_get", [t["function"]["name"] for t in route_tools("What preferences do you recall about me?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_14_memory_xfail(self):
        self.assertIn("memory_get", [t["function"]["name"] for t in route_tools("Did you save it?", ALL_TOOLS)])

    def test_routing_sequence_15_math2(self):
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("Evaluate 100 / 4", ALL_TOOLS)])
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("Calculate 25 * 4", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_15_math2_xfail(self):
        self.assertEqual(len(route_tools("Divide that by 5", ALL_TOOLS)), 1)

    def test_routing_sequence_16_time2(self):
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("Give me the current time", ALL_TOOLS)])
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("What's the date?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_16_time2_xfail(self):
        self.assertEqual(len(route_tools("Is it late?", ALL_TOOLS)), 1)

    def test_routing_sequence_17_battery2(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Battery status", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("How much charge?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_17_battery2_xfail(self):
        self.assertEqual(len(route_tools("Will it last?", ALL_TOOLS)), 1)

    def test_routing_sequence_18_trash2(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Clear recycling bin", ALL_TOOLS)])
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Empty trash", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_18_trash2_xfail(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Is it clean?", ALL_TOOLS)])

    def test_routing_sequence_19_task2(self):
        self.assertIn("task_list", [t["function"]["name"] for t in route_tools("Show my tasks", ALL_TOOLS)])
        self.assertIn("task_list", [t["function"]["name"] for t in route_tools("List all reminders", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_19_task2_xfail(self):
        self.assertIn("task_list", [t["function"]["name"] for t in route_tools("Are there any?", ALL_TOOLS)])

    def test_routing_sequence_20_service2(self):
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("Is sshd running?", ALL_TOOLS)])
        self.assertIn("restart_service", [t["function"]["name"] for t in route_tools("Restart sshd", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_20_service2_xfail(self):
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("Kill it", ALL_TOOLS)])

    def test_routing_sequence_21_network2(self):
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Is my wifi working?", ALL_TOOLS)])
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Turn wifi on", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_21_network2_xfail(self):
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Disable it", ALL_TOOLS)])

    def test_routing_sequence_22_math3(self):
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("50 - 20", ALL_TOOLS)])
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("30 * 2", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_22_math3_xfail(self):
        self.assertEqual(len(route_tools("Divide that by 5", ALL_TOOLS)), 1)

    def test_routing_sequence_23_memory3(self):
        self.assertIn("memory_set", [t["function"]["name"] for t in route_tools("Remember I use Ubuntu", ALL_TOOLS)])
        self.assertIn("memory_get", [t["function"]["name"] for t in route_tools("What distro do you remember I use?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_23_memory3_xfail(self):
        self.assertIn("memory_set", [t["function"]["name"] for t in route_tools("I changed it", ALL_TOOLS)])

    def test_routing_sequence_24_power2(self):
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Enable performance profile", ALL_TOOLS)])
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Switch to power saver", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_24_power2_xfail(self):
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Turn it off", ALL_TOOLS)])

    def test_routing_sequence_25_cpu2(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Are fans running loud?", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Is it overheating?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_25_cpu2_xfail(self):
        self.assertEqual(len(route_tools("Should I worry?", ALL_TOOLS)), 1)

    def test_routing_sequence_26_ram2(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("How much memory is used?", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Check RAM", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_26_ram2_xfail(self):
        self.assertEqual(len(route_tools("Free some up", ALL_TOOLS)), 1)

    def test_routing_sequence_27_time3(self):
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("What year is it?", ALL_TOOLS)])
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("Current month", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_27_time3_xfail(self):
        self.assertEqual(len(route_tools("How long ago was that?", ALL_TOOLS)), 1)

    def test_routing_sequence_28_task3(self):
        self.assertIn("task_add", [t["function"]["name"] for t in route_tools("Remind me to call Mom", ALL_TOOLS)])
        self.assertIn("task_cancel", [t["function"]["name"] for t in route_tools("Cancel all tasks", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_28_task3_xfail(self):
        self.assertIn("task_cancel", [t["function"]["name"] for t in route_tools("Stop reminding me", ALL_TOOLS)])

    def test_routing_sequence_29_app2(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Start discord", ALL_TOOLS)])
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Launch VSCode", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_29_app2_xfail(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Close it", ALL_TOOLS)])

    def test_routing_sequence_30_bluetooth2(self):
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("Is BT on?", ALL_TOOLS)])
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("Disable bluetooth", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_30_bluetooth2_xfail(self):
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("Check its status", ALL_TOOLS)])

    def test_routing_sequence_31_service3(self):
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("State of docker daemon", ALL_TOOLS)])
        self.assertIn("restart_service", [t["function"]["name"] for t in route_tools("Reload nginx", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_31_service3_xfail(self):
        self.assertIn("restart_service", [t["function"]["name"] for t in route_tools("Do it again", ALL_TOOLS)])

    def test_routing_sequence_32_trash3(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Clear recycle bin", ALL_TOOLS)])
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Empty the bin", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_32_trash3_xfail(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Delete everything", ALL_TOOLS)])

    def test_routing_sequence_33_memory4(self):
        self.assertIn("memory_delete", [t["function"]["name"] for t in route_tools("Forget my name", ALL_TOOLS)])
        self.assertIn("memory_list", [t["function"]["name"] for t in route_tools("List all notes", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_33_memory4_xfail(self):
        self.assertIn("memory_list", [t["function"]["name"] for t in route_tools("Read them back", ALL_TOOLS)])

    def test_routing_sequence_34_battery3(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Battery health", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Is it charging?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_34_battery3_xfail(self):
        self.assertEqual(len(route_tools("Plug it in", ALL_TOOLS)), 1)

    def test_routing_sequence_35_math4(self):
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("What is 120 / 3", ALL_TOOLS)])
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("Multiply 40 and 2", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_35_math4_xfail(self):
        self.assertEqual(len(route_tools("Take away 10", ALL_TOOLS)), 1)

    def test_routing_sequence_36_app3(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Open calculator app", ALL_TOOLS)])
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Run vlc", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_36_app3_xfail(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Kill it", ALL_TOOLS)])

    def test_routing_sequence_37_network3(self):
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Check network connection", ALL_TOOLS)])
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Is wlan0 up?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_37_network3_xfail(self):
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Restart it", ALL_TOOLS)])

    def test_routing_sequence_38_trash4(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Trash bin", ALL_TOOLS)])
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Clear recycling", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_38_trash4_xfail(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Done?", ALL_TOOLS)])

    def test_routing_sequence_39_task4(self):
        self.assertIn("task_add", [t["function"]["name"] for t in route_tools("Schedule a meeting", ALL_TOOLS)])
        self.assertIn("task_list", [t["function"]["name"] for t in route_tools("What tasks are pending?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_39_task4_xfail(self):
        self.assertIn("task_list", [t["function"]["name"] for t in route_tools("Show them", ALL_TOOLS)])

    def test_routing_sequence_40_service4(self):
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("Status of daemon", ALL_TOOLS)])
        self.assertIn("restart_service", [t["function"]["name"] for t in route_tools("Restart process", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_40_service4_xfail(self):
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("Is it still dead?", ALL_TOOLS)])

    def test_routing_sequence_41_memory5(self):
        self.assertIn("memory_set", [t["function"]["name"] for t in route_tools("Note that I have a pet dog", ALL_TOOLS)])
        self.assertIn("memory_get", [t["function"]["name"] for t in route_tools("What did I say my pet was?", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_41_memory5_xfail(self):
        self.assertIn("memory_get", [t["function"]["name"] for t in route_tools("What is it?", ALL_TOOLS)])

    def test_routing_sequence_42_time4(self):
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("Time in Tokyo", ALL_TOOLS)])
        self.assertIn("get_datetime", [t["function"]["name"] for t in route_tools("Timezone info", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_42_time4_xfail(self):
        self.assertEqual(len(route_tools("Is it morning there?", ALL_TOOLS)), 1)

    def test_routing_sequence_43_app4(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Open terminal", ALL_TOOLS)])
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Start gedit", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_43_app4_xfail(self):
        self.assertIn("launch_app", [t["function"]["name"] for t in route_tools("Bring it to front", ALL_TOOLS)])

    def test_routing_sequence_44_network4(self):
        self.assertIn("toggle_bluetooth", [t["function"]["name"] for t in route_tools("Connect to bluetooth speaker", ALL_TOOLS)])
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Check wifi network", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_44_network4_xfail(self):
        self.assertIn("toggle_wifi", [t["function"]["name"] for t in route_tools("Disconnect from it", ALL_TOOLS)])

    def test_routing_sequence_45_math5(self):
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("Math 50 / 2", ALL_TOOLS)])
        self.assertIn("calculator", [t["function"]["name"] for t in route_tools("Arithmetic 8 * 9", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_45_math5_xfail(self):
        self.assertEqual(len(route_tools("Divide that by 5", ALL_TOOLS)), 1)

    def test_routing_sequence_46_power3(self):
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Turbostat check", ALL_TOOLS)])
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Switch power profile", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_46_power3_xfail(self):
        self.assertIn("power_profile", [t["function"]["name"] for t in route_tools("Turn that off", ALL_TOOLS)])

    def test_routing_sequence_47_cpu3(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("CPU throttling", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Thermals", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_47_cpu3_xfail(self):
        self.assertEqual(len(route_tools("Cool it down", ALL_TOOLS)), 1)

    def test_routing_sequence_48_ram3(self):
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Swap usage", ALL_TOOLS)])
        self.assertIn("system_health", [t["function"]["name"] for t in route_tools("Available ram", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_48_ram3_xfail(self):
        self.assertEqual(len(route_tools("Clear it", ALL_TOOLS)), 1)

    def test_routing_sequence_49_trash5(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Recycle bin empty", ALL_TOOLS)])
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Clear trash", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_49_trash5_xfail(self):
        self.assertIn("empty_trash", [t["function"]["name"] for t in route_tools("Empty it", ALL_TOOLS)])

    def test_routing_sequence_50_service5(self):
        self.assertIn("service_status", [t["function"]["name"] for t in route_tools("Is the server up?", ALL_TOOLS)])
        self.assertIn("restart_service", [t["function"]["name"] for t in route_tools("Restart processes", ALL_TOOLS)])

    @unittest.expectedFailure
    def test_routing_sequence_50_service5_xfail(self):
        self.assertIn("restart_service", [t["function"]["name"] for t in route_tools("Bounce it", ALL_TOOLS)])
