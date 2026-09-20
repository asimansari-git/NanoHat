import os
import unittest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure we're in test mode
os.environ["NANOHAT_TEST_MODE"] = "1"

from runtime.functions import (
    memory_set,
    memory_get,
    memory_list,
    memory_delete,
    _match_key,
    _normalize_key
)
from runtime.db import get_connection, init_db

class TestComplexMemoryEvolution(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary database for safety
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "state.db"

        # Override the NANOHAT_DB_PATH for this test run
        self.env_patcher = patch.dict(os.environ, {"NANOHAT_DB_PATH": str(self.db_path)})
        self.env_patcher.start()

        # Initialize the database schema
        init_db()

        # Setup common mock system calls (though conftest handles this, good to be safe)
        self.subprocess_patcher = patch("subprocess.run")
        self.mock_subprocess = self.subprocess_patcher.start()

    def tearDown(self):
        # Stop patchers
        self.env_patcher.stop()
        self.subprocess_patcher.stop()

        # Ensure all connections are closed before deleting the temp dir
        # In SQLite, WAL mode can leave connections open, but since it's a file,
        # we just let tempfile clean it up.
        self.temp_dir.cleanup()

    def get_db_contents(self):
        """Helper to dump the DB contents for debugging."""
        with get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM user_memory;")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    def test_basic_memory_set_and_get(self):
        """Test setting and getting a basic memory."""
        res_set = memory_set(key="default_distro", value="Fedora Workstation 41")
        self.assertIn("Saved to memory: 'default_distro' = 'Fedora Workstation 41'", res_set)

        res_get = memory_get(key="default_distro")
        self.assertEqual(res_get, "default_distro is Fedora Workstation 41.")

    def test_memory_overwrite_evolution(self):
        """Test that preferences evolve (overwrite)."""
        memory_set(key="preferred_editor", value="VS Code")
        self.assertEqual(memory_get(key="preferred_editor"), "preferred_editor is VS Code.")

        # User evolves their preference
        res_set2 = memory_set(key="preferred_editor", value="Zed")
        self.assertIn("Saved to memory: 'preferred_editor' = 'Zed'", res_set2)

        # Verify it evolved
        res_get2 = memory_get(key="preferred_editor")
        self.assertEqual(res_get2, "preferred_editor is Zed.")

    def test_memory_list_empty_and_populated(self):
        """Test memory_list handles empty and populated states."""
        self.assertEqual(memory_list(), "User memory is currently empty.")

        memory_set(key="key1", value="val1")
        memory_set(key="key2", value="val2")

        res_list = memory_list()
        self.assertIn("- key1: val1", res_list)
        self.assertIn("- key2: val2", res_list)

    def test_memory_set_missing_args(self):
        """Test handling of missing arguments."""
        res = memory_set(key="just_key")
        self.assertIn("Error: Both 'key' and 'value' are required", res)

    def test_memory_get_missing_args(self):
        """Test handling of missing arguments."""
        res = memory_get()
        self.assertIn("Error: Please specify the 'key'", res)

    def test_memory_delete(self):
        """Test memory deletion."""
        memory_set(key="old_editor", value="Vim")
        self.assertEqual(memory_get(key="old_editor"), "old_editor is Vim.")

        res_del = memory_delete(key="old_editor")
        self.assertIn("Memory for key 'old_editor' deleted successfully.", res_del)

        self.assertEqual(memory_get(key="old_editor"), "No memory found for key 'old_editor'.")

    def test_complex_note_storage(self):
        """Test storing long/complex strings."""
        memory_set(key="project_ideas", value="rust-wasm, sub-1b agent, and pwa")
        res = memory_get(key="project_ideas")
        self.assertEqual(res, "project_ideas is rust-wasm, sub-1b agent, and pwa.")

    def test_match_key_pluralization(self):
        """Test that _match_key handles pluralization correctly."""
        self.assertTrue(_match_key("distro", "distros"))
        self.assertTrue(_match_key("distros", "distro"))
        self.assertTrue(_match_key("cat", "cats"))
        self.assertTrue(_match_key("cats", "cat"))

        # Test full end-to-end memory recall with pluralization
        memory_set(key="favorite_distro", value="Debian")
        # Ask for plural
        res = memory_get(key="favorite_distros")
        self.assertEqual(res, "favorite_distro is Debian.")

    def test_match_key_normalization(self):
        """Test that _match_key normalizes dashes, cases and spaces."""
        self.assertTrue(_match_key("WIFI Password", "wifi_password"))
        self.assertTrue(_match_key("wifi-password", "wifi_password"))
        self.assertTrue(_match_key("  WIFI    PASSWORD  ", "wifi_password"))

        memory_set(key="WIFI Password", value="12345678")
        res = memory_get(key="wifi-password")
        self.assertEqual(res, "wifi_password is 12345678.")

    def test_match_key_alias_matching(self):
        """Test that _match_key matches aliases correctly."""
        self.assertTrue(_match_key("pet_name", "pet"))
        self.assertTrue(_match_key("pet", "pet_name"))

        memory_set(key="pet_name", value="Fido")
        res = memory_get(key="pet")
        self.assertEqual(res, "pet_name is Fido.")

    @unittest.expectedFailure
    def test_fuzzy_semantic_search_ide_vs_editor(self):
        """Test fuzzy semantic matching (should fail currently)."""
        memory_set(key="preferred_editor", value="VS Code")
        # Currently, "ide" does not match "editor" using exact/regex rules
        res = memory_get(key="preferred_ide")
        self.assertEqual(res, "preferred_editor is VS Code.")

    @unittest.expectedFailure
    def test_fuzzy_semantic_search_laptop_vs_computer(self):
        """Test fuzzy semantic matching for computer synonyms (should fail currently)."""
        memory_set(key="work_laptop", value="Framework 13")
        res = memory_get(key="work_computer")
        self.assertEqual(res, "work_laptop is Framework 13.")

    @unittest.expectedFailure
    def test_fuzzy_semantic_search_browser_vs_web(self):
        """Test fuzzy semantic matching for web browser synonyms (should fail currently)."""
        memory_set(key="default_browser", value="Firefox")
        res = memory_get(key="default_web_client")
        self.assertEqual(res, "default_browser is Firefox.")

    @unittest.expectedFailure
    def test_fuzzy_semantic_search_distro_vs_os(self):
        """Test fuzzy semantic matching for operating system synonyms (should fail currently)."""
        memory_set(key="main_os", value="Arch Linux")
        res = memory_get(key="main_distro")
        self.assertEqual(res, "main_os is Arch Linux.")

    @unittest.expectedFailure
    def test_fuzzy_semantic_search_notes_vs_ideas(self):
        """Test fuzzy semantic matching for note types (should fail currently)."""
        memory_set(key="project_ideas", value="Build a new agent")
        res = memory_get(key="project_notes")
        self.assertEqual(res, "project_ideas is Build a new agent.")

if __name__ == "__main__":
    unittest.main()
