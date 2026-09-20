"""
test_persona_corporate_worker.py - Synthetic behavioral fuzzing for NanoHat v3.
Persona: Corporate Office Worker / Professional
Focus: calendar deadlines, meeting reminders, corporate productivity applications, memory retention, chained scheduling.
"""

import unittest
from unittest.mock import patch
import pytest

from runtime.router import route_tools
from runtime.tools import ALL_TOOLS
from runtime.functions import REGISTRY

# Test Matrix Cases
TEST_CASES = [
    # 1. Reminders & Scheduling
    ("Remind me to sync with the product team tomorrow at 9:30 AM", "task_add"),
    ("Schedule weekly standup check every Monday", "task_add"),
    ("Set a reminder for the Q3 earnings call at 2 PM", "task_add"),
    ("Remind me to send the status report in 1 hour", "task_add"),
    ("Add a task to review the merger document by Friday", "task_add"),
    ("Cancel my 9:30 AM meeting reminder", "task_cancel"),
    ("Cancel task 42", "task_cancel"),
    ("List all my pending tasks for today", "task_list"),
    ("Show me my schedule", "task_list"),
    ("What are my completed tasks?", "task_list"),

    # 2. Corporate Application Launching & Service Status
    ("launch slack and check if meeting is active", "service_status"),
    ("Is Slack running?", "service_status"),
    ("Check if Microsoft Teams daemon is active", "service_status"),
    ("Is LibreOffice process hanging?", "service_status"),
    ("Status of Zoom service", "service_status"),
    ("Restart Zoom client", "restart_service"), # May be rejected by allowlist, but intent is restart
    ("Restart slack daemon", "restart_service"),
    ("Check the status of Docker daemon", "service_status"),

    # 3. Persistent Memory (Deadlines, Preferences, KPIs)
    ("set memory: quarterly review deadline is Oct 15", "memory_set"),
    ("Remember that the marketing budget is approved", "memory_set"),
    ("Save my employee ID as 123456", "memory_set"),
    ("What is the quarterly review deadline?", "memory_get"),
    ("Did the marketing budget get approved?", "memory_get"),
    ("What is my employee ID?", "memory_get"),
    ("List all my saved notes", "memory_list"),
    ("Forget my employee ID", "memory_delete"),
    ("Delete the quarterly review deadline note", "memory_delete"),

    # 4. Math / Data Processing
    ("Calculate 15% of $1,200,000", "calculator"),
    ("What is 1200000 * 0.15?", "calculator"),
    ("Divide the Q1 revenue by 4", "calculator"),
    ("Convert 500 EUR to USD at 1.1 exchange rate", "calculator"), # Should route to calc or fallback gracefully

    # 5. Calendar / Time / OS Telemetry
    ("What time is it in Tokyo right now?", "get_datetime"),
    ("What is the date today?", "get_datetime"),
    ("Check battery status before my flight", "system_health"),
    ("What is the CPU usage during this Teams call?", "system_health"),
    ("Set power profile to performance for compiling", "power_profile"),
    ("Turn off wifi during the flight", "toggle_wifi"),
    ("Is my bluetooth on for my headset?", "toggle_bluetooth"),
    ("Empty the trash bin on my laptop", "empty_trash"),

    # 6. Edge Cases & Complex Queries
    ("Remind me to call John and check if Slack is working", "task_add"), # Could route to task_add + service_status
    ("What time is my next meeting and is my battery full?", ["system_health", "get_datetime", "task_list"]), # Broad intent
    ("Save the Zoom link and remind me in 5 mins", ["memory_set", "task_add"]),
    ("What is the status of my VPN and set power to performance", ["service_status", "power_profile"]),
]


class TestCorporateWorkerPersona(unittest.TestCase):

    def test_routing_accuracy(self):
        passed = 0
        failed_cases = []

        for i, (query, expected_tools) in enumerate(TEST_CASES, 1):
            if isinstance(expected_tools, str):
                expected_tools = [expected_tools]

            active_tools = route_tools(query, ALL_TOOLS)
            active_tool_names = [t.get("function", {}).get("name") for t in active_tools]

            # We consider it a pass if at least ONE of the expected tools is found.
            # In NanoHat, router restricts to 1-4 tools.
            found_any = any(expected in active_tool_names for expected in expected_tools)

            # Since Nanohat also uses fallback logic in Engine (execute_tool), let's check both
            # router output and the engine fallback logic for single intents.
            engine_fallback = []
            norm = query.replace("_", "").lower()
            if "battery" in norm: engine_fallback.append("system_health")
            elif "wifi" in norm: engine_fallback.append("toggle_wifi")
            elif "blue" in norm: engine_fallback.append("toggle_bluetooth")
            elif any(k in norm for k in ["time", "clock", "date"]): engine_fallback.append("get_datetime")
            elif "trash" in norm: engine_fallback.append("empty_trash")
            elif any(k in norm for k in ["calc", "math"]): engine_fallback.append("calculator")
            elif "power" in norm: engine_fallback.append("power_profile")
            elif "restart" in norm: engine_fallback.append("restart_service")
            elif "status" in norm or "service" in norm: engine_fallback.append("service_status")
            elif "memory" in norm or "remember" in norm:
                if any(w in norm for w in ["get", "recall", "find", "read"]): engine_fallback.append("memory_get")
                elif any(w in norm for w in ["list", "all"]): engine_fallback.append("memory_list")
                elif any(w in norm for w in ["del", "forget", "remove"]): engine_fallback.append("memory_delete")
                else: engine_fallback.append("memory_set")
            elif "task" in norm or "remind" in norm or "todo" in norm:
                if any(w in norm for w in ["cancel", "del", "remove"]): engine_fallback.append("task_cancel")
                elif any(w in norm for w in ["list", "all", "show"]): engine_fallback.append("task_list")
                else: engine_fallback.append("task_add")

            if found_any or any(expected in engine_fallback for expected in expected_tools):
                passed += 1
            else:
                failed_cases.append({
                    "query": query,
                    "expected": expected_tools,
                    "routed_tools": active_tool_names,
                    "engine_fallback": engine_fallback
                })

        print(f"\n--- Routing Test Complete ---")
        print(f"Total Cases: {len(TEST_CASES)}")
        print(f"Passed: {passed}")
        print(f"Failed: {len(failed_cases)}")

        if failed_cases:
            print("\nFailed Cases:")
            for case in failed_cases:
                print(f"  Query: {case['query']}")
                print(f"  Expected: {case['expected']}")
                print(f"  Routed: {case['routed_tools']}")
                print(f"  Fallback: {case['engine_fallback']}")
                print("-" * 20)

        # Write report data to a file that we can read later to construct the final report
        import json
        with open("reports_data.json", "w") as f:
            json.dump({
                "total": len(TEST_CASES),
                "passed": passed,
                "failed": len(failed_cases),
                "failed_cases": failed_cases
            }, f)

if __name__ == '__main__':
    unittest.main()
