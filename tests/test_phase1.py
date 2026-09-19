"""
test_phase1.py — Automated verification for NanoHat v3.0.0 Phase 1 hardening.
"""

import unittest
from runtime.functions import calculator, system_health, power_profile, check_interactive_tty
from runtime.engine import AgentEngine
from runtime.client import OllamaClient
from runtime.prompts import get_system_prompt


class TestFunctions(unittest.TestCase):
    def test_calculator_simple(self):
        res = calculator("7+7")
        self.assertEqual(res, "14")

    def test_calculator_complex(self):
        res = calculator("7+7*18")
        self.assertEqual(res, "133")

    def test_calculator_long(self):
        res = calculator("7+7+7+7+9+10*14-7")
        self.assertEqual(res, "170")

    def test_system_health_all(self):
        res = system_health("all")
        self.assertIn("CPU:", res)
        self.assertIn("RAM:", res)
        self.assertIn("Battery:", res)

    def test_system_health_battery_metric(self):
        res = system_health("battery")
        self.assertTrue(res.startswith("Battery:"))
        self.assertNotIn(".0%", res)

    def test_system_health_cpu_metric(self):
        res = system_health("cpu")
        self.assertTrue(res.startswith("CPU:"))

    def test_power_profile_get(self):
        res = power_profile(action="get")
        self.assertTrue(res.startswith("Current power profile:"))

    def test_power_profile_fallback(self):
        # Action is 'set' but no profile provided -> falls back safely to 'get'
        res = power_profile(action="set")
        self.assertTrue(res.startswith("Current power profile:"))

    def test_tty_guard(self):
        self.assertIsInstance(check_interactive_tty(), bool)


class TestLiveRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = OllamaClient()
        cls.engine = AgentEngine(client=cls.client, prompt_version="v1", verbose=False)

    def test_route_math_simple(self):
        response = self.engine.run("What is 7+7?")
        self.assertIn("14", response)

    def test_route_math_7_plus_7_times_18(self):
        response = self.engine.run("What is 7+7*18?")
        self.assertIn("133", response)

    def test_route_math_long(self):
        response = self.engine.run("What is 7+7+7+7+9+10*14-7?")
        self.assertIn("170", response)

    def test_route_battery_level(self):
        response = self.engine.run("What is my battery level?")
        self.assertNotIn("medical", response.lower())
        self.assertIn("%", response)

    def test_route_battery_status(self):
        response = self.engine.run("Check my battery status")
        self.assertNotIn("medical", response.lower())
        self.assertIn("%", response)

    def test_route_battery_health(self):
        response = self.engine.run("What is my battery health?")
        self.assertNotIn("medical", response.lower())


    def test_route_power_profile(self):
        response = self.engine.run("What is my current power profile?")
        self.assertTrue(any(p in response.lower() for p in ["performance", "balanced", "power-saver"]))


if __name__ == "__main__":
    unittest.main()
