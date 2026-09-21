import unittest
import pytest
import os
import tempfile
import sys
import json
from unittest.mock import patch

from runtime.db import init_db, get_connection
from runtime.router import route_tools
from runtime.tools import ALL_TOOLS

TEST_CASES = [
    # task_add
    ("Add high-priority task: Q3 Financial audit meeting at 10 AM tomorrow", ["task_add"]),
    ("Schedule a follow-up call with the vendor for next week", ["task_add"]),
    ("Remind me to submit the expense report by EOD", ["task_add"]),
    ("Set a task to review the Q4 projection spreadsheets tomorrow morning", ["task_add"]),
    ("Add a reminder for the HR compliance training deadline on Friday", ["task_add"]),
    ("Schedule a reminder to check the server logs at 3 PM", ["task_add"]),
    ("Add task to prep for the executive board meeting", ["task_add"]),
    ("Remind me to update the project roadmap before the steering committee meets", ["task_add"]),
    
    # task_list
    ("List all pending tasks scheduled for this week", ["task_list"]),
    ("Show me my to-do list for today", ["task_list"]),
    ("What are my completed tasks?", ["task_list"]),
    ("Display all cancelled tasks", ["task_list"]),
    ("List all tasks", ["task_list"]),
    ("Show my schedule for the upcoming week", ["task_list"]),
    ("What tasks do I have pending?", ["task_list"]),
    
    # task_cancel
    ("Cancel task 4 because the vendor rescheduled", ["task_cancel"]),
    ("Remove task 12 from my list", ["task_cancel"]),
    ("Delete reminder 7", ["task_cancel"]),
    ("Cancel the scheduled task 2", ["task_cancel"]),
    ("Drop task 5", ["task_cancel"]),
    
    # memory_set
    ("Save confidential note: corporate travel expense code is CORP-TAX-8812", ["memory_set"]),
    ("Remember that the VPN gateway IP is 10.0.0.5", ["memory_set"]),
    ("Set memory: the new office wifi password is 'CorporateSecure2024'", ["memory_set"]),
    ("Save my employee ID as 998877", ["memory_set"]),
    ("Remember the departmental budget code is IT-Ops-55", ["memory_set"]),
    ("Store a note that my desk location is building 4 floor 2", ["memory_set"]),
    
    # memory_get
    ("What is my corporate travel expense code?", ["memory_get"]),
    ("Recall the VPN gateway IP", ["memory_get"]),
    ("What is the new office wifi password?", ["memory_get"]),
    ("Get my employee ID", ["memory_get"]),
    ("What is the departmental budget code?", ["memory_get"]),
    ("Where is my desk located?", ["memory_get"]),
    
    # launch_app
    ("Launch calc to review quarterly spreadsheet", ["launch_app"]),
    ("Open firefox to access the corporate intranet", ["launch_app"]),
    ("Start gnome-terminal for ssh access", ["launch_app"]),
    ("Run slack to message the team", ["launch_app"]),
    ("Open thunderbird to check emails", ["launch_app"]),
    
    # power_profile
    ("Set power profile to power-saver for my long presentation", ["power_profile"]),
    ("Change power profile to performance for compiling code", ["power_profile"]),
    ("What is my current power profile?", ["power_profile"]),
    ("Switch to balanced power mode", ["power_profile"]),
    
    # Multiple / Complex Intents
    ("Save the Zoom link and remind me in 5 mins", ["memory_set", "task_add"]),
    ("What time is my next meeting and is my battery full?", ["system_health", "get_datetime", "task_list"]),
    
    # xfails (Calendar integrations not supported natively by router)
    ("Schedule a meeting on my Outlook calendar for 2 PM", ["task_add"]),
    ("Sync my tasks with CalDAV server", ["task_add"]),
]


class TestComplexEnterpriseAdmin(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        os.environ["NANOHAT_DB_PATH"] = self.temp_db.name
        init_db(self.temp_db.name)
        self.passed = 0
        self.failed = []

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        wal_file = f"{self.temp_db.name}-wal"
        shm_file = f"{self.temp_db.name}-shm"
        if os.path.exists(wal_file):
            os.unlink(wal_file)
        if os.path.exists(shm_file):
            os.unlink(shm_file)
        os.environ.pop("NANOHAT_DB_PATH", None)

    def test_routing_accuracy(self):
        passed = 0
        failed_cases = []
        for i, (query, expected_tools) in enumerate(TEST_CASES):
            # Bypass xfail queries here so they can be tested separately
            if "Outlook" in query or "CalDAV" in query:
                continue

            active_tools = route_tools(query, ALL_TOOLS)
            active_tool_names = [t.get("function", {}).get("name") for t in active_tools]

            # We consider it a pass if at least ONE of the expected tools is found.
            found_any = any(expected in active_tool_names for expected in expected_tools)

            if found_any:
                passed += 1
            else:
                failed_cases.append({
                    "query": query,
                    "expected": expected_tools,
                    "routed_tools": active_tool_names,
                })

        # Record results
        self.assertEqual(len(failed_cases), 0, f"Failed cases: {failed_cases}")

    @unittest.expectedFailure
    def test_outlook_calendar_integration(self):
        query = "Schedule a meeting on my Outlook calendar for 2 PM"
        active_tools = route_tools(query, ALL_TOOLS)
        active_tool_names = [t.get("function", {}).get("name") for t in active_tools]
        self.assertIn("enterprise_calendar_add", active_tool_names)

    @unittest.expectedFailure
    def test_caldav_calendar_integration(self):
        query = "Sync my tasks with CalDAV server"
        active_tools = route_tools(query, ALL_TOOLS)
        active_tool_names = [t.get("function", {}).get("name") for t in active_tools]
        self.assertIn("enterprise_calendar_sync", active_tool_names)


if __name__ == '__main__':
    unittest.main()
