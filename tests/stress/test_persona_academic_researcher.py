import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import sqlite3
import tempfile
import shutil

from runtime.functions import (
    calculator, memory_set, memory_get, system_health, get_datetime,
    memory_list, memory_delete, task_add, task_list, task_cancel
)
from runtime.db import init_db, get_connection
import runtime.db

class TestAcademicResearcherPersona(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temp dir for sqlite db
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_state.db")
        os.environ["NANOHAT_DB_PATH"] = cls.db_path
        # Force reload db path
        import importlib
        importlib.reload(runtime.db)
        runtime.db.init_db()
        cls.conn = sqlite3.connect(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        # Clear the memory for each test to avoid interference
        with runtime.db.get_connection() as conn:
            conn.execute("DELETE FROM user_memory;")
            conn.execute("DELETE FROM scheduled_tasks;")
            conn.commit()

    # --- Math & AST Safe Calculator Tests ---

    def test_math_basic_roots_and_powers(self):
        self.assertEqual(calculator("144 ** 0.5 * 3 ** 4"), "972")
        self.assertEqual(calculator("144 ** 0.5 * (3 ** 4)"), "972")

    def test_math_scientific_notation(self):
        # AST parser needs to handle scientific notation
        self.assertEqual(calculator("(1.25e4 * 3.7) / 2.1"), str((1.25e4 * 3.7) / 2.1))
        self.assertEqual(calculator("6.022e23 / 2"), str(6.022e23 / 2))
        self.assertEqual(calculator("1.6e-19 * 5e18"), str(1.6e-19 * 5e18))

    def test_math_complex_expressions(self):
        self.assertEqual(calculator("((15.5 * 3) + 2.5) / 2"), "24.5")
        self.assertEqual(calculator("100 / 3"), str(100/3))
        self.assertEqual(calculator("2 ** 10"), "1024")
        self.assertEqual(calculator("3 * (4 + 5) - 6 / 2"), "24")
        self.assertEqual(calculator("12.5 % 3"), "0.5")
        self.assertEqual(calculator("15 // 4"), "3")

    def test_math_large_exponent_protection(self):
        # AST calc protects against exponent too large
        self.assertTrue("Error" in calculator("2 ** 10000"))
        self.assertTrue("Error" in calculator("1e11 ** 2"))

    def test_math_invalid_expression(self):
        self.assertTrue("Error" in calculator("import os; os.system('ls')"))
        self.assertTrue("Error" in calculator("__import__('os').system('ls')"))
        self.assertTrue("Error" in calculator("open('test', 'w')"))
        self.assertTrue("Error" in calculator("a = 5"))
        self.assertTrue("Error" in calculator("lambda x: x"))
        self.assertTrue("Error" in calculator("[1, 2, 3]"))

    def test_math_with_constants(self):
        # Needs to handle pi and e
        self.assertEqual(calculator("pi * 2"), str(3.141592653589793 * 2))
        self.assertEqual(calculator("e ** 2"), str(2.718281828459045 ** 2))
        self.assertEqual(calculator("pi ** 2 / e"), str((3.141592653589793 ** 2) / 2.718281828459045))

    # --- Persistent Memory Tests ---

    def test_memory_scientific_hypotheses(self):
        res = memory_set("hypothesis_H1", "beta coefficient equals 0.045 with p<0.01")
        self.assertTrue("Saved" in res)

        get_res = memory_get("hypothesis_H1")
        self.assertTrue("0.045" in get_res)

        res = memory_set("theorem_42", "The square of the hypotenuse is equal to the sum of the squares of the other two sides")
        self.assertTrue("Saved" in res)

        get_res = memory_get("theorem_42")
        self.assertTrue("hypotenuse" in get_res)

    def test_memory_dense_phrasing(self):
        res = memory_set("spectral_analysis_results", "Eigenvalues: 3.14, 2.71, 1.61. Matrix is positive definite.")
        self.assertTrue("Saved" in res)

        get_res = memory_get("spectral_analysis_results")
        self.assertTrue("positive definite" in get_res)

        get_res2 = memory_get("spectral_analysis_result") # Should match alias / variations
        self.assertTrue("positive definite" in get_res2)

    def test_memory_complex_keys_and_retrieval(self):
        memory_set("experiment_alpha_v2_results", "Yield: 85.4%, Purity: 99.1%")
        memory_set("literature_review_jones_2023", "Summary of findings regarding quantum entanglement.")

        self.assertTrue("99.1%" in memory_get("experiment_alpha_v2_results"))
        self.assertTrue("quantum" in memory_get("literature_review_jones_2023"))

        # Test listing
        list_res = memory_list()
        self.assertTrue("experiment_alpha_v2_results" in list_res)
        self.assertTrue("literature_review_jones_2023" in list_res)

        # Test deletion
        del_res = memory_delete("experiment_alpha_v2_results")
        self.assertTrue("deleted successfully" in del_res)
        self.assertTrue("No memory found" in memory_get("experiment_alpha_v2_results"))

    # --- Task Scheduling Tests ---

    def test_task_scheduling_research_events(self):
        task_add("Submit grant proposal to NSF", "2024-12-15 17:00")
        task_add("Review paper for Journal of Physics", "Tomorrow 9am")

        list_res = task_list()
        self.assertTrue("Submit grant proposal" in list_res)
        self.assertTrue("Review paper" in list_res)

        # We don't easily know the ID unless we parse the add result, let's extract it
        add_res = task_add("Attend lab meeting", "Today 2pm")
        import re
        m = re.search(r"Task #(\d+)", add_res)
        task_id = m.group(1) if m else "3"

        cancel_res = task_cancel(task_id)
        self.assertTrue("cancelled" in cancel_res)

        list_res_after = task_list("pending")
        self.assertTrue("Attend lab meeting" not in list_res_after or "cancelled" not in list_res_after)
        # Verify the cancelled filter works
        list_cancelled = task_list("cancelled")
        self.assertTrue("Attend lab meeting" in list_cancelled)


    # --- Telemetry & OS Mock Tests ---

    @patch('runtime.functions.psutil.cpu_percent')
    @patch('runtime.functions.psutil.virtual_memory')
    @patch('runtime.functions.psutil.sensors_battery')
    def test_system_health_telemetry(self, mock_battery, mock_memory, mock_cpu):
        mock_cpu.return_value = 15.5

        mock_mem_obj = MagicMock()
        mock_mem_obj.used = 8 * (1024 ** 3)
        mock_mem_obj.total = 16 * (1024 ** 3)
        mock_mem_obj.percent = 50.0
        mock_memory.return_value = mock_mem_obj

        mock_batt_obj = MagicMock()
        mock_batt_obj.percent = 85
        mock_batt_obj.power_plugged = False
        mock_battery.return_value = mock_batt_obj

        res = system_health("all")
        self.assertTrue("15.5%" in res)
        self.assertTrue("8.0GB" in res)
        self.assertTrue("85%" in res)

        res_cpu = system_health("cpu")
        self.assertTrue("15.5%" in res_cpu)

        res_ram = system_health("ram")
        self.assertTrue("8.0GB" in res_ram)

    def test_datetime(self):
        res = get_datetime()
        self.assertTrue(len(res) > 5)

if __name__ == '__main__':
    unittest.main()
