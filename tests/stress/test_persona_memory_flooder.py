import unittest
import os
import sys
import tempfile
import time
import json
import string
import random

# Add parent directory to path to resolve 'runtime'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from runtime.db import get_connection, init_db, DEFAULT_DB_PATH
from runtime.functions import memory_set, memory_get, memory_list, memory_delete

class TestPersonaMemoryFlooder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to configure the db to be a temp file
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.temp_dir.name, "state.db")
        os.environ["NANOHAT_DB_PATH"] = cls.db_path
        init_db()

    @classmethod
    def tearDownClass(cls):
        del os.environ["NANOHAT_DB_PATH"]
        cls.temp_dir.cleanup()

    def setUp(self):
        # Clear the memory table for each test for isolation
        with get_connection() as conn:
            conn.execute("DELETE FROM user_memory;")
            conn.commit()

    def test_rapid_insertion_100_keys(self):
        start_time = time.time()
        for i in range(100):
            res = memory_set(key=f"key_{i}", value=f"val_{i}")
            self.assertIn("Saved to memory", res)
        duration = time.time() - start_time

        # Verify
        res = memory_list()
        for i in range(100):
            self.assertIn(f"key_{i}", res)

        print(f"\n100 insertions took {duration:.4f}s")
        self.assertTrue(duration < 2.0, "Insertions took too long")

    def test_duplicate_key_overwrites(self):
        memory_set(key="target_key", value="initial_value")
        for i in range(50):
            memory_set(key="target_key", value=f"overwrite_{i}")

        res = memory_get(key="target_key")
        self.assertIn("overwrite_49", res)

    def test_memory_get_return_format(self):
        memory_set(key="test_get_fmt", value="hello_world")
        res = memory_get(key="test_get_fmt")
        self.assertIn("hello_world", res)
        self.assertIn("test_get_fmt", res)

    def test_large_payload_10kb(self):
        large_payload = "A" * 10240
        res = memory_set(key="large_blob", value=large_payload)
        self.assertIn("Saved to memory", res)

        get_res = memory_get(key="large_blob")
        self.assertIn(large_payload, get_res)

    def test_emoji_and_unicode(self):
        key = "emoji_🔑"
        val = "value_🔥_日本語"
        res = memory_set(key=key, value=val)
        self.assertIn("Saved to memory", res)

        get_res = memory_get(key=key)
        self.assertIn(val, get_res)

    def test_nested_json_string(self):
        key = "json_payload"
        val = json.dumps({"nested": {"key": "value"}, "list": [1, 2, 3]})
        res = memory_set(key=key, value=val)
        self.assertIn("Saved to memory", res)

        get_res = memory_get(key=key)
        self.assertIn(val, get_res)

    def test_empty_values(self):
        res = memory_set(key="empty_val", value="")
        self.assertIn("Error", res)

    def test_non_existent_key_lookup(self):
        res = memory_get(key="does_not_exist")
        self.assertIn("no memory found", res.lower())

    def test_topic_aliases(self):
        memory_set(key="pet_name", value="Fido")
        # Should be able to look up just 'pet' based on match logic
        res = memory_get(key="pet")
        self.assertIn("Fido", res)

    def test_delete_already_deleted(self):
        memory_set(key="to_delete", value="delete_me")
        res = memory_delete(key="to_delete")
        self.assertIn("deleted successfully", res.lower())

        res_second = memory_delete(key="to_delete")
        self.assertNotIn("successfully", res_second.lower())

    def test_delete_non_existent(self):
        res = memory_delete(key="phantom_key")
        self.assertNotIn("successfully", res.lower())

    def test_concurrent_reads_writes(self):
        # We simulate this via rapid succession
        keys = [f"key_{i}" for i in range(50)]
        for k in keys:
            memory_set(key=k, value=f"val_{k}")

        for k in keys:
            self.assertIn(f"val_{k}", memory_get(key=k))

    def test_listing_behavior_large_dataset(self):
        for i in range(60):
            memory_set(key=f"large_list_key_{i}", value=f"large_list_val_{i}")
        res = memory_list()
        self.assertEqual(res.count("- large_list_key_"), 60)

if __name__ == '__main__':
    unittest.main()
