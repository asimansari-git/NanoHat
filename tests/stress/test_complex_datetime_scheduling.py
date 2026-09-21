import unittest
import pytest
from typing import List, Dict, Any

import runtime.router as router
import runtime.tools as tools

ALL_TOOLS = [
    tools.TASK_ADD_TOOL,
    tools.TASK_LIST_TOOL,
    tools.TASK_CANCEL_TOOL,
    tools.GET_DATETIME_TOOL,
    tools.CALCULATOR_TOOL,
    tools.SYSTEM_HEALTH_TOOL,
]

def get_tool_names(query: str) -> List[str]:
    routed = router.route_tools(query, ALL_TOOLS)
    return [t["function"]["name"] for t in routed]

class TestComplexDateTimeScheduling(unittest.TestCase):

    def test_basic_relative_task_add(self):
        query = "Remind me the day after tomorrow at noon to file taxes"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_next_monday_task_add(self):
        query = "Set a reminder for next Monday morning to call the mechanic"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_how_many_hours_until_midnight(self):
        query = "How many hours until midnight?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_remind_me_in_45_mins(self):
        query = "Remind me in 45 minutes to stand up and stretch"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_what_day_of_the_week(self):
        query = "What day of the week will October 15th be?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_cancel_afternoon_task(self):
        query = "Cancel the task I scheduled for this afternoon"
        names = get_tool_names(query)
        self.assertIn("task_cancel", names)

    def test_list_tasks_for_tomorrow(self):
        query = "Show me my tasks for tomorrow"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_task_add_this_evening(self):
        query = "Schedule a meeting for this evening at 6pm"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_add_end_of_month(self):
        query = "Remind me at the end of the month to pay rent"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_list_tasks_next_week(self):
        query = "What tasks do I have scheduled for next week?"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_cancel_meeting_tomorrow(self):
        # "meeting" doesn't have "remind", "task", etc. so this might fail
        query = "Cancel my meeting for tomorrow morning"
        names = get_tool_names(query)
        self.assertIn("task_cancel", names)

    def test_how_many_days_until_christmas(self):
        query = "How many days until Christmas?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_task_add_in_a_fortnight(self):
        query = "Set a task in a fortnight to check the garden"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_add_next_year(self):
        query = "Remind me next year on Jan 1st to renew my license"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_what_time_is_it_in_tokyo(self):
        query = "What time is it in Tokyo right now?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_cancel_all_reminders_today(self):
        query = "Delete all my reminders for today"
        names = get_tool_names(query)
        self.assertIn("task_cancel", names)

    def test_task_add_specific_date(self):
        # The query contains '2024-11-05', triggering CALCULATOR_TOOL instead of TASK due to routing issues
        query = "Add a to-do for 2024-11-05: vote"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    @unittest.expectedFailure
    def test_task_add_specific_date_2(self):
        query = "Add a to-do for 2024-11-05: vote"
        names = get_tool_names(query)
        self.assertNotIn("calculator", names)

    def test_task_add_noon(self):
        query = "At noon remind me to eat lunch"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_add_midday(self):
        query = "Remind me midday to drink water"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_list_morning(self):
        query = "What are my morning tasks?"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_task_add_weekend(self):
        query = "Schedule a run for the weekend"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_datetime_how_long_ago(self):
        query = "How long ago was yesterday?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_cancel_last_task(self):
        query = "Cancel the last task I made"
        names = get_tool_names(query)
        self.assertIn("task_cancel", names)

    def test_datetime_leap_year(self):
        query = "Is this year a leap year?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_task_add_half_an_hour(self):
        query = "Remind me in half an hour"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_add_a_week_from_now(self):
        query = "Set an alarm for a week from now"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_list_weekend(self):
        query = "Show tasks for this weekend"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_task_cancel_weekend(self):
        query = "Cancel my weekend tasks"
        names = get_tool_names(query)
        self.assertIn("task_cancel", names)

    def test_task_add_q3(self):
        query = "Remind me in Q3 to do the report"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_datetime_first_monday(self):
        query = "When is the first Monday of next month?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_task_add_first_monday(self):
        query = "Schedule meeting for first Monday of next month"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_add_tomorrow_evening(self):
        query = "Remind me tomorrow evening"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_add_next_tuesday(self):
        query = "Task: buy milk next Tuesday"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_task_list_past(self):
        query = "What tasks did I have yesterday?"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_datetime_is_it_friday(self):
        query = "Is it Friday yet?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_task_add_five_mins(self):
        query = "Remind me in 5 mins"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    def test_cancel_id(self):
        query = "Cancel task 12345"
        names = get_tool_names(query)
        self.assertIn("task_cancel", names)

    def test_list_all(self):
        query = "Show all tasks"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_list_completed(self):
        query = "List completed tasks"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_datetime_days_in_feb(self):
        query = "How many days in February this year?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    def test_datetime_what_is_date(self):
        query = "What is the date today?"
        names = get_tool_names(query)
        self.assertIn("get_datetime", names)

    # Edge cases expected to fail due to Regex limitations
    @unittest.expectedFailure
    def test_xfail_implicit_task_tonight(self):
        # "I need to call mom tonight" doesn't have "remind", "task", etc.
        query = "I need to call mom tonight"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    @unittest.expectedFailure
    def test_xfail_implicit_task_cancel(self):
        query = "Nevermind about the dentist appointment"
        names = get_tool_names(query)
        self.assertIn("task_cancel", names)

    @unittest.expectedFailure
    def test_xfail_implicit_task_list(self):
        query = "What's on the docket for the 5th?"
        names = get_tool_names(query)
        self.assertIn("task_list", names)

    def test_xfail_implicit_task_add_ambiguous(self):
        # "Push my meeting to later" implies task edit/cancel/add
        query = "Push my meeting to later"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    @unittest.expectedFailure
    def test_xfail_implicit_task_add_event(self):
        query = "I have a flight to catch in 3 hours"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

    @unittest.expectedFailure
    def test_xfail_implicit_task_add_no_keywords(self):
        query = "I must buy groceries before returning home"
        names = get_tool_names(query)
        self.assertIn("task_add", names)

if __name__ == '__main__':
    unittest.main()
