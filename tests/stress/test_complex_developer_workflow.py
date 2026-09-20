"""
test_complex_developer_workflow.py - Stress test harness for Full-Stack Developer Workflow & Workspace Orchestration.
Simulates realistic human usage patterns for developers using NanoHat.
"""

import unittest
from unittest.mock import patch
import os
import tempfile
from runtime.db import init_db, get_connection
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools
from runtime.engine import AgentEngine
from runtime.client import OllamaClient
import runtime.functions as rf

class TestDeveloperWorkflowRouting(unittest.TestCase):
    def test_launch_app_routing(self):
        queries = [
            "Launch firefox and gnome-terminal so I can start hacking",
            "Open vscode",
            "Start the docker desktop app",
            "Run postman",
            "Can you open my terminal?",
            "Start intellij idea",
            "Launch google chrome",
            "Open my browser"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("launch_app", names, f"Failed to route '{q}' to launch_app. Got {names}")

    def test_service_status_routing(self):
        queries = [
            "Is the docker daemon active right now?",
            "Check status of postgresql",
            "What is the state of nginx?",
            "Is redis running?",
            "Check if mysql service is up",
            "Status of ollama",
            "Is tailscale service active?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertTrue("service_status" in names or "restart_service" in names, f"Failed to route '{q}' to service tools. Got {names}")

    def test_restart_service_routing(self):
        queries = [
            "Restart the postgresql service for my local dev environment",
            "Restart docker daemon",
            "Reload nginx",
            "Restart ollama",
            "Can you reboot the redis service?",
            "Restart pipewire",
            "Kill and restart tailscale"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("restart_service", names, f"Failed to route '{q}' to restart_service. Got {names}")

    def test_calculator_routing(self):
        queries = [
            "Calculate 1024 * 1024 * 8 to find the buffer size in bytes",
            "What is 1920 * 1080?",
            "Calculate 16 * 1024 / 8",
            "Evaluate 256 + 512 + 1024",
            "Math: 10000 / 12",
            "Compute 3.14 * 10 * 10"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("calculator", names, f"Failed to route '{q}' to calculator. Got {names}")

    def test_task_add_routing(self):
        queries = [
            "Remind me to push feat/auth branch before 6 PM today",
            "Add a task to review the open PRs at 10am",
            "Schedule a reminder to deploy to staging",
            "Remind me to merge the hotfix tomorrow",
            "Task: fix the CSS bug in the header",
            "To-do: run database migrations",
            "Remind me to email the QA team in 30 minutes"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("task_add", names, f"Failed to route '{q}' to task_add. Got {names}")

    def test_system_health_routing(self):
        queries = [
            "Check current CPU and RAM usage to see if my build is throttling the system",
            "Is my RAM full?",
            "What's the CPU load like?",
            "Check system memory usage",
            "Is the laptop overheating? Check CPU",
            "Show me the battery status",
            "How much RAM is free?"
        ]
        for q in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            self.assertIn("system_health", names, f"Failed to route '{q}' to system_health. Got {names}")

    @unittest.expectedFailure
    def test_complex_cli_chaining_routing(self):
        # Queries involving complex CLI chaining or IDE extensions that are expected to fail routing
        # The router currently merges intents and doesn't split commands gracefully.
        queries = [
            ("Run git status and then launch vscode", ["launch_app", "git_status"]),
            ("Tail the docker logs and check CPU usage", ["service_status", "system_health"]),
            ("Restart postgresql and run db migrations", ["restart_service", "run_db_migration"])
        ]
        for q, expected in queries:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            # For complex chaining, the current regex cluster often fails to isolate all distinct intents
            # We expect these assertions to fail
            for exp in expected:
                self.assertIn(exp, names)

class TestDeveloperWorkflowLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["NANOHAT_DB_PATH"] = cls.temp_db.name
        init_db(cls.temp_db.name)

        # Override the OllamaClient chat method with a mock to prevent network timeouts during stress tests.
        class MockOllamaClient:
            def __init__(self):
                pass
            def chat(self, messages, tools=None, temperature=0.0, timeout=30.0):
                last_msg = messages[-1].get("content", "").lower()
                if messages[-1].get("role") == "tool":
                    return {"message": {"role": "assistant", "content": messages[-1]["content"]}}
                if "firefox" in last_msg:
                    return {"message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "launch_app", "arguments": {"app_name": "firefox"}}}]}}
                elif "ollama service" in last_msg:
                    return {"message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "restart_service", "arguments": {"service_name": "ollama.service"}}}]}}

                return {"message": {"role": "assistant", "content": "Mocked response"}}

        cls.client = MockOllamaClient()
        cls.engine = AgentEngine(client=cls.client, prompt_version="v1", verbose=False)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db.name):
            os.unlink(cls.temp_db.name)
        wal_file = f"{cls.temp_db.name}-wal"
        shm_file = f"{cls.temp_db.name}-shm"
        if os.path.exists(wal_file):
            os.unlink(wal_file)
        if os.path.exists(shm_file):
            os.unlink(shm_file)
        os.environ.pop("NANOHAT_DB_PATH", None)

    @patch('runtime.functions.shutil.which')
    @patch('runtime.functions.subprocess.run')
    def test_mocked_service_restart(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/systemctl"
        mock_run.return_value.returncode = 0
        response = self.engine.run("Restart the ollama service")
        self.assertTrue("restart" in response.lower() or "ollama" in response.lower())

    @patch.dict('os.environ', {'DISPLAY': ':0'})
    @patch('runtime.functions.shutil.which')
    @patch('runtime.functions.subprocess.Popen')
    def test_mocked_launch_app(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/firefox"
        response = self.engine.run("Launch firefox")
        self.assertTrue("firefox" in response.lower() or "launch" in response.lower() or "application" in response.lower())

if __name__ == "__main__":
    unittest.main()
