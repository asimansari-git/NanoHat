import unittest
import os
from unittest.mock import patch, MagicMock
from runtime.functions import launch_app
from runtime.engine import AgentEngine
from runtime.client import OllamaClient

class TestAppLauncherStress(unittest.TestCase):
    def setUp(self):
        # We ensure DISPLAY is set for general tests, unless overridden
        os.environ["DISPLAY"] = ":0"

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_launch_valid_app(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/calc"
        res = launch_app("calc")
        self.assertIn("Successfully launched", res)
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0], ["/usr/bin/calc"])
        self.assertTrue(kwargs.get("start_new_session"))

    @patch('shutil.which')
    def test_launch_missing_app(self, mock_which):
        mock_which.return_value = None
        res = launch_app("non_existent_game_xyz")
        self.assertIn("ERROR[missing]", res)

    def test_launch_injection_spaces(self):
        res = launch_app("app with spaces")
        self.assertIn("ERROR[security]", res)

    def test_launch_injection_quotes(self):
        res = launch_app("app\"with'quotes")
        self.assertIn("ERROR[security]", res)

    def test_launch_injection_bash(self):
        res = launch_app("bash -c whoami")
        self.assertIn("ERROR[security]", res)

    def test_launch_injection_path_traversal(self):
        res = launch_app("../../../bin/sh")
        self.assertIn("ERROR[security]", res)

    def test_launch_injection_dev_null(self):
        res = launch_app("/dev/null")
        self.assertIn("ERROR[security]", res)

    @patch('shutil.which')
    def test_headless_no_display(self, mock_which):
        mock_which.return_value = "/usr/bin/calc"
        if "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]
        if "WAYLAND_DISPLAY" in os.environ:
            del os.environ["WAYLAND_DISPLAY"]

        res = launch_app("calc")
        self.assertIn("ERROR[headless]", res)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_wayland_display(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/calc"
        if "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]
        os.environ["WAYLAND_DISPLAY"] = "wayland-0"

        res = launch_app("calc")
        self.assertIn("Successfully launched", res)
        mock_popen.assert_called_once()

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_launch_exception(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/calc"
        mock_popen.side_effect = Exception("Mocked error")
        res = launch_app("calc")
        self.assertIn("ERROR: Failed to launch", res)

    def test_invalid_input_none(self):
        res = launch_app(None)
        self.assertIn("ERROR: Invalid application name", res)

    def test_invalid_input_int(self):
        res = launch_app(123)
        self.assertIn("ERROR: Invalid application name", res)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_launch_with_dashes_and_dots(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/gnome-terminal.desktop"
        res = launch_app("gnome-terminal.desktop")
        self.assertIn("Successfully launched", res)
        mock_popen.assert_called_once()

    @patch('shutil.which')
    def test_many_edge_cases(self, mock_which):
        edge_cases = [
            ("app&", False),
            ("app|", False),
            ("app;", False),
            ("app>", False),
            ("app<", False),
            ("app$", False),
            ("app*", False),
            ("app?", False),
            ("app=", False),
            ("app+", False),
            ("app!", False),
            ("app`", False),
            ("app~", False),
            ("app(", False),
            ("app)", False),
            ("app{", False),
            ("app}", False),
            ("app[", False),
            ("app]", False),
            ("app\\\\", False),
            ("app/", False),
            ("app:", False),
            ("app,", False),
            ("app^", False),
            ("app@", False),
            ("app#", False),
            ("app%", False),
            ("app-name", True),
            ("app_name", True),
            ("app.name", True),
            ("app-name_1.2", True)
        ]

        for case, should_pass in edge_cases:
            if should_pass:
                mock_which.return_value = "/usr/bin/" + case
                with patch('subprocess.Popen') as mock_popen:
                    res = launch_app(case)
                    self.assertIn("Successfully launched", res, f"Failed on valid case: {case}")
            else:
                res = launch_app(case)
                self.assertIn("ERROR[security]", res, f"Failed to block invalid case: {case}")

class TestAppLauncherEngineRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = OllamaClient()
        cls.engine = AgentEngine(client=cls.client, prompt_version="v1", verbose=False)

    @patch('runtime.engine.AgentEngine.execute_tool')
    def test_route_launch_app(self, mock_exec):
        pass

if __name__ == "__main__":
    unittest.main()
