"""
test_phase2_batch2.py — Automated verification for NanoHat v3.0.0 Batch 2 tools:
- get_datetime
- empty_trash (with headless TTY safety gate)
"""

import os
import sys
import unittest
from runtime.functions import (
    calculator,
    system_health,
    power_profile,
    get_datetime,
    empty_trash,
    check_interactive_tty
)
from runtime.engine import AgentEngine
from runtime.client import OllamaClient


class TestBatch2Functions(unittest.TestCase):
    def test_get_datetime_format(self):
        dt_str = get_datetime()
        # Example format: "Monday, September 14, 2026, 06:45:10 PM IST"
        self.assertIsInstance(dt_str, str)
        self.assertIn(",", dt_str)
        # Check that year is present
        self.assertTrue(any(char.isdigit() for char in dt_str))

    def test_empty_trash_headless_gate(self):
        # In automated test runner without TTY and without env var, empty_trash must abort fail-closed
        old_env = os.environ.get("NANOHAT_AUTO_APPROVE_DESTRUCTIVE")
        if "NANOHAT_AUTO_APPROVE_DESTRUCTIVE" in os.environ:
            del os.environ["NANOHAT_AUTO_APPROVE_DESTRUCTIVE"]

        # Ensure mock non-interactive check
        try:
            # If sys.stdin is not a tty (like in CI or pipe)
            if not sys.stdin.isatty():
                res = empty_trash()
                self.assertTrue(res.startswith("ERROR[aborted]"))
        finally:
            if old_env is not None:
                os.environ["NANOHAT_AUTO_APPROVE_DESTRUCTIVE"] = old_env

    def test_empty_trash_auto_approve(self):
        # With explicit NANOHAT_AUTO_APPROVE_DESTRUCTIVE=1, it executes without hanging
        old_env = os.environ.get("NANOHAT_AUTO_APPROVE_DESTRUCTIVE")
        os.environ["NANOHAT_AUTO_APPROVE_DESTRUCTIVE"] = "1"
        try:
            res = empty_trash()
            self.assertIn("Trash emptied successfully", res)
        finally:
            if old_env is not None:
                os.environ["NANOHAT_AUTO_APPROVE_DESTRUCTIVE"] = old_env
            else:
                os.environ.pop("NANOHAT_AUTO_APPROVE_DESTRUCTIVE", None)


class TestBatch2LiveRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = OllamaClient()
        cls.engine = AgentEngine(client=cls.client, prompt_version="v1", verbose=False)

    def test_route_datetime(self):
        response = self.engine.run("Check current date and time")
        self.assertNotIn("cannot assist", response.lower())
        # Check that either month or year or day is present in response
        self.assertTrue(any(word in response.lower() for word in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "2026", "september", "am", "pm"]))

    def test_route_day_of_week(self):
        response = self.engine.run("Check current day of the week")
        self.assertNotIn("cannot assist", response.lower())
        self.assertTrue(any(day in response.lower() for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "7"]))


    def test_route_empty_trash(self):
        # Use auto-approve for non-interactive test run
        os.environ["NANOHAT_AUTO_APPROVE_DESTRUCTIVE"] = "1"
        try:
            response = self.engine.run("Empty my trash bin")
            self.assertIn("trash", response.lower())
        finally:
            os.environ.pop("NANOHAT_AUTO_APPROVE_DESTRUCTIVE", None)

    def test_regression_math_and_health(self):
        math_res = self.engine.run("What is 7+7*18?")
        self.assertIn("133", math_res)

        health_res = self.engine.run("What is my battery level?")
        self.assertNotIn("medical", health_res.lower())
        self.assertIn("%", health_res)


if __name__ == "__main__":
    unittest.main()
