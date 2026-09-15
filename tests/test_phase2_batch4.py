"""
test_phase2_batch4.py — Automated verification for NanoHat v3.0.0 Batch 4 tools:
- SQLite WAL mode state storage (db.py)
- memory_set, memory_get, memory_list, memory_delete
- task_add, task_list, task_cancel

All tests run against an isolated temporary SQLite database via NANOHAT_DB_PATH.
Zero data writes to host user's ~/.local/state/nanohat/state.db.
"""

import os
import tempfile
import unittest
from runtime.db import init_db, get_connection
from runtime.functions import (
    memory_set,
    memory_get,
    memory_list,
    memory_delete,
    task_add,
    task_list,
    task_cancel,
)
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools
from runtime.engine import AgentEngine
from runtime.client import OllamaClient


class TestBatch4DatabaseAndFunctions(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        os.environ["NANOHAT_DB_PATH"] = self.temp_db.name
        init_db(self.temp_db.name)

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

    def test_wal_mode_enabled(self):
        with get_connection(self.temp_db.name) as conn:
            mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            self.assertEqual(mode.lower(), "wal")

    def test_memory_lifecycle(self):
        # 1. Empty list
        self.assertIn("empty", memory_list().lower())

        # 2. Set memory
        res_set = memory_set(key="favorite_editor", value="neovim")
        self.assertIn("favorite_editor", res_set)
        self.assertIn("neovim", res_set)

        # 3. Get memory
        res_get = memory_get(key="favorite_editor")
        self.assertIn("neovim", res_get)

        # 4. Case-insensitive get
        res_get_ci = memory_get(key="FAVORITE_EDITOR")
        self.assertIn("neovim", res_get_ci)

        # 5. List memories
        res_list = memory_list()
        self.assertIn("favorite_editor", res_list)
        self.assertIn("neovim", res_list)

        # 6. Overwrite memory
        memory_set(key="favorite_editor", value="emacs")
        self.assertIn("emacs", memory_get(key="favorite_editor"))

        # 7. Delete memory
        res_del = memory_delete(key="favorite_editor")
        self.assertIn("deleted successfully", res_del)
        self.assertIn("no memory found", memory_get(key="favorite_editor").lower())

    def test_memory_key_normalization(self):
        # Setting with trailing space, underscore, or hyphen
        memory_set(key="favorite_ distro", value="Fedora Workstation")
        
        # Retrieving with clean key
        res = memory_get(key="favorite_distro")
        self.assertIn("Fedora Workstation", res)

        # Retrieving with spaces
        res_spaces = memory_get(key="favorite distro")
        self.assertIn("Fedora Workstation", res_spaces)

        # Retrieving with dashes
        res_dashes = memory_get(key="favorite-distro")
        self.assertIn("Fedora Workstation", res_dashes)

        # Deletion with alternate format
        del_res = memory_delete(key="favorite distro")
        self.assertIn("deleted successfully", del_res)

    def test_legacy_unnormalized_key_fallback(self):
        # Directly insert an unnormalized key without going through memory_set
        with get_connection(self.temp_db.name) as conn:
            conn.execute("INSERT INTO user_memory (key, value) VALUES ('legacy_ unnormalized_ key', 'legacy_value');")
            conn.commit()

        # memory_get with clean normalized key should find it via fallback scan
        res = memory_get(key="legacy_unnormalized_key")
        self.assertIn("legacy_value", res)

        # memory_delete with clean key should delete it
        del_res = memory_delete(key="legacy_unnormalized_key")
        self.assertIn("deleted successfully", del_res)

    def test_task_lifecycle(self):
        # 1. Empty list
        self.assertIn("no pending tasks", task_list(status="pending").lower())

        # 2. Add task
        res_add = task_add(title="Submit weekly report", due_time="Friday 5pm")
        self.assertIn("Task #1 scheduled", res_add)
        self.assertIn("Submit weekly report", res_add)

        # 3. List pending tasks
        res_list = task_list(status="pending")
        self.assertIn("Task #1", res_list)
        self.assertIn("Submit weekly report", res_list)

        # 4. Add second task
        res_add2 = task_add(title="Buy groceries", due_time="Saturday")
        self.assertIn("Task #2 scheduled", res_add2)

        # 5. Cancel task #1
        res_cancel = task_cancel(task_id=1)
        self.assertIn("Task #1 has been cancelled", res_cancel)

        # 6. Verify pending tasks only has #2
        pending = task_list(status="pending")
        self.assertNotIn("Submit weekly report", pending)
        self.assertIn("Buy groceries", pending)

        # 7. Verify cancelled list has #1
        cancelled = task_list(status="cancelled")
        self.assertIn("Task #1", cancelled)
        self.assertIn("Submit weekly report", cancelled)


class TestBatch4RouterIntegration(unittest.TestCase):
    def test_memory_routing(self):
        cases = [
            ("Remember that my pet name is Milo", ["memory_set"]),
            ("What is my pet name?", ["memory_get"]),
            ("List all my memories", ["memory_list"]),
            ("Forget my pet name", ["memory_delete"]),
        ]
        for q, expected in cases:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            for exp in expected:
                self.assertIn(exp, names, f"Query '{q}' failed to route to {exp}. Got {names}")
            self.assertLessEqual(len(tools), 3)

    def test_task_routing(self):
        cases = [
            ("Remind me to call the plumber tomorrow at 9am", ["task_add"]),
            ("List my pending tasks", ["task_list"]),
            ("Cancel task 1", ["task_cancel"]),
        ]
        for q, expected in cases:
            tools = route_tools(q, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            for exp in expected:
                self.assertIn(exp, names, f"Query '{q}' failed to route to {exp}. Got {names}")
            self.assertLessEqual(len(tools), 3)


class TestBatch4LiveRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["NANOHAT_DB_PATH"] = cls.temp_db.name
        init_db(cls.temp_db.name)
        cls.client = OllamaClient()
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

    def test_live_memory_set_and_get(self):
        # Set
        res_set = self.engine.run("Remember that my favorite distro is Fedora")
        self.assertTrue("fedora" in res_set.lower() or "saved" in res_set.lower() or "remember" in res_set.lower())

        # Get
        res_get = self.engine.run("What is my favorite distro?")
        self.assertIn("fedora", res_get.lower())

    def test_live_task_add_and_list(self):
        # Add task
        res_add = self.engine.run("Remind me to update kernel tomorrow")
        self.assertTrue("kernel" in res_add.lower() or "task" in res_add.lower() or "scheduled" in res_add.lower())

        # List tasks
        res_list = self.engine.run("List my pending tasks")
        self.assertTrue("kernel" in res_list.lower() or "task" in res_list.lower())


if __name__ == "__main__":
    unittest.main()
