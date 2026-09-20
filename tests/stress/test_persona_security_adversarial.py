import os
import tempfile
import unittest
from runtime.db import init_db, get_connection
from runtime.functions import (
    calculator,
    memory_set,
    memory_get,
    memory_list,
    task_add,
    task_list,
    restart_service,
    service_status,
)


class TestAdversarialSecurity(unittest.TestCase):
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

    def test_calculator_ast_jailbreaks(self):
        attacks = [
            "__import__('os').system('id')",
            "open('/etc/passwd').read()",
            "eval('1+1')",
            "exec('import os')",
            "compile('1+1', '<string>', 'eval')",
            "globals()",
            "locals()",
            "__builtins__",
            "[x for x in (1, 2, 3)]", # List comps might not be supported but checking for crash
            "1 + 1; ls",
            "os.system('id')",
            "subprocess.run(['id'])"
        ]
        for payload in attacks:
            res = calculator(payload)
            self.assertTrue(
                "Error" in res or "Exception" in res,
                f"AST Escape detected for payload: {payload}. Got: {res}"
            )

    def test_sql_injections_memory(self):
        attacks = [
            "'; DROP TABLE user_memory; --",
            "' OR '1'='1",
            "admin' --",
            "\" OR \"1\"=\"1"
        ]
        for payload in attacks:
            # Setting with SQLi in key
            res = memory_set(key=payload, value="hacked")
            self.assertIn("Saved to memory", res)

            # Retrieving with SQLi in key
            get_res = memory_get(key=payload)
            # Either it retrieves "hacked" or it says not found, but it shouldn't crash or return all rows
            self.assertTrue("hacked" in get_res or "No memory found" in get_res)

        # Check that memory list doesn't fail
        list_res = memory_list()
        self.assertIsInstance(list_res, str)

    def test_sql_injections_tasks(self):
        attacks = [
            "'; DROP TABLE scheduled_tasks; --",
            "' OR '1'='1"
        ]
        for payload in attacks:
            res = task_add(title=payload, due_time="now")
            self.assertIn("scheduled", res)

        list_res = task_list(status="'; DROP TABLE scheduled_tasks; --")
        self.assertIsInstance(list_res, str)
        # Should not crash and likely return "No '; drop table scheduled_tasks; -- tasks found."
        self.assertNotIn("Error", list_res)


    def test_command_injections_services(self):
        attacks = [
            "pipewire; id",
            "ollama && ls",
            "wireplumber | rm -rf /",
            "$(id)",
            "`id`",
            "pipewire\nrm -rf /"
        ]
        for payload in attacks:
            res = restart_service(service_name=payload)
            # The function checks against an allowlist, so it should be blocked
            self.assertTrue(
                "ERROR[security_blocked]" in res or "not in the safe allowlist" in res,
                f"Command injection executed for service restart payload: {payload}. Got: {res}"
            )

            res_status = service_status(service_name=payload)
            # Status check uses systemctl but we should check what it outputs, it should not execute the shell command since systemctl is called via subprocess without shell=True
            self.assertTrue(
                isinstance(res_status, str),
                f"Service status check failed for payload: {payload}"
            )

    def test_path_traversal_services(self):
        attacks = [
            "../../gdm",
            "../../gnome-shell",
            "../../../etc/passwd",
            "../pipewire",
            "/usr/lib/systemd/system/gdm.service"
        ]
        for payload in attacks:
            res = restart_service(service_name=payload)
            self.assertTrue(
                "ERROR[security_blocked]" in res or "not in the safe allowlist" in res or "Error" in res,
                f"Path traversal executed for service restart payload: {payload}. Got: {res}"
            )

    def test_path_traversal_memory(self):
        payloads = [
            "../../../etc/passwd",
            "/tmp/hacked"
        ]
        for payload in payloads:
            res = memory_set(key=payload, value="test")
            self.assertIn("Saved to memory", res)

if __name__ == "__main__":
    unittest.main()
