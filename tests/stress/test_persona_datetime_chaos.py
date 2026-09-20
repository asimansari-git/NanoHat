import unittest
import json
import os
from runtime.functions import task_add, get_datetime

class TestDatetimeChaos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = []

    @classmethod
    def tearDownClass(cls):
        with open("chaos_results.json", "w") as f:
            json.dump(cls.results, f, indent=2)

    def test_get_datetime_does_not_crash(self):
        try:
            result = get_datetime()
            self.__class__.results.append({"tool": "get_datetime", "input": "N/A", "status": "OK", "output": result})
        except Exception as e:
            self.__class__.results.append({"tool": "get_datetime", "input": "N/A", "status": "ERROR", "output": str(e)})

    def test_task_add_due_time_chaos(self):
        due_time_cases = [
            # Relative parsing
            "0 minutes",
            "-5 minutes",
            "yesterday",
            "tomorrow",
            "in 100000 hours",
            "in -100000 hours",
            "next Friday after sunset",
            "a billion seconds from now",

            # Invalid bounds
            "25:00",
            "24:01",
            "00:61",
            "-01:00",
            "99:99",

            # Timezone ambiguities
            "12:00 PM EST",
            "12:00 PM Tokyo time",
            "now in GMT+14",
            "now in GMT-14",
            "midnight UTC",

            # Chronological edge cases
            "Feb 29 next year",
            "Feb 29 2023",
            "Feb 29 2024",
            "Feb 30",
            "Nov 31",

            # Absolute timestamp math
            "2038-01-19 03:14:07",
            "2038-01-19 03:14:08",
            "1970-01-01 00:00:00",
            "1969-12-31 23:59:59",
            "9999-12-31 23:59:59",
            "10000-01-01 00:00:00",

            # ISO-8601 formatting
            "2023-10-15T15:30:00Z",
            "2023-10-15T15:30:00.000Z",
            "2023-10-15T15:30:00+02:00",
            "2023-10-15T25:30:00Z",
            "2023-13-15T15:30:00Z",

            # Extra chaotic inputs
            "when pigs fly",
            "NULL",
            "NaN",
            "undefined",
            "None",
            "",
            "   ",
            "\n\t",
            "DROP TABLE scheduled_tasks;",
            "../../../../etc/passwd",
        ]

        for due in due_time_cases:
            try:
                res = task_add(title="Chaos Task", due_time=due)
                self.__class__.results.append({"tool": "task_add", "param": "due_time", "input": due, "status": "OK", "output": res})
            except Exception as e:
                self.__class__.results.append({"tool": "task_add", "param": "due_time", "input": due, "status": "ERROR", "output": str(e)})

    def test_task_add_notify_minutes_chaos(self):
        notify_cases = [
            -1,
            0,
            1000000000,
            -1000000000,
            "10",
            "-10",
            "0",
            "",
            None,
            "NaN",
            "infinity",
            "ten"
        ]
        for val in notify_cases:
            try:
                res = task_add(title="Notify Chaos", due_time="tomorrow", notify_minutes_before=val)
                self.__class__.results.append({"tool": "task_add", "param": "notify_minutes_before", "input": str(val), "status": "OK", "output": res})
            except Exception as e:
                self.__class__.results.append({"tool": "task_add", "param": "notify_minutes_before", "input": str(val), "status": "ERROR", "output": str(e)})

if __name__ == '__main__':
    unittest.main()
