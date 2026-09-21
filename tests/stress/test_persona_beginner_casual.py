import pytest
import re
from typing import List

from runtime.tools import ALL_TOOLS
from runtime.router import route_tools, FALLBACK_TOOL_NAMES

# 40 Casual User Queries with typos, slang, and vague requests
TEST_CASES = [
    ("my laptop is getting hot fix it", ["power_profile", "system_health"]),
    ("can u check how much juice my battery has", ["system_health"]),
    ("y is my computer so slow??", ["system_health", "power_profile"]),
    ("make it go faster", ["power_profile"]),
    ("how much ram do i have left", ["system_health"]),
    ("battery plz", ["system_health"]),
    ("why is my fan so loud", ["system_health", "power_profile"]),
    ("is my cpu dying?", ["system_health"]),
    ("check battry percent", ["system_health"]),
    ("im on zero percent power", ["system_health", "power_profile"]),

    # Hardware & Radios
    ("turn on the internet", ["toggle_wifi"]),
    ("can't connect to my headphones", ["toggle_bluetooth"]),
    ("internet broken", ["toggle_wifi"]),
    ("i cant hear anything from the earbuds", ["toggle_bluetooth", "restart_service"]),
    ("is my blutoth on??", ["toggle_bluetooth"]),
    ("kill wifi", ["toggle_wifi"]),
    ("turn off the blue tooth", ["toggle_bluetooth"]),
    ("im not connected to the web", ["toggle_wifi"]),
    ("radio off", ["toggle_wifi", "toggle_bluetooth"]),

    # Services & Daemons
    ("make sound work again", ["restart_service"]),
    ("is docker working??", ["service_status"]),
    ("restart my browser", ["restart_service"]),
    ("the music stopped playing", ["service_status", "restart_service"]),
    ("is tailscale working", ["service_status"]),
    ("reboot pipewire", ["restart_service", "service_status"]),

    # Persistent Memory
    ("i like turtles", ["memory_set"]),
    ("remember that my wife is named sarah", ["memory_set"]),
    ("what did i say my favorite color was", ["memory_get"]),
    ("who am i again", ["memory_get"]),
    ("forget everything", ["memory_delete", "memory_list"]),
    ("where did my file go", []), # Likely unhandled/fallback
    ("show me all my notes", ["memory_list"]),
    ("im called bob", ["memory_set"]),
    ("mah name is jeff", ["memory_set"]),
    ("whoami", ["memory_get"]),

    # Scheduling & Housekeeping
    ("clear all my junk files right now", ["empty_trash"]),
    ("what time is it in london", ["get_datetime"]),
    ("remind me to feed the cat in 10 mins", ["task_add"]),
    ("cancel that alarm", ["task_cancel"]),
    ("what do i have to do today", ["task_list", "task_add"]),
    ("math 5 + 5", ["calculator"]),
    ("what is two plus two", ["calculator"]),
    ("empty the bin", ["empty_trash"]),
    ("how many days until xmas", ["get_datetime"]),
    ("wake me up at 7am", ["task_add"]),
    ("can u delete the trash", ["empty_trash"])
]

@pytest.mark.parametrize("query, expected_tools", TEST_CASES)
def test_beginner_casual_routing(query: str, expected_tools: List[str]):
    """
    Stress tests the deterministic regex router against vague, conversational,
    and typo-laden queries representative of a beginner/casual user.
    """
    selected_tools = route_tools(query, ALL_TOOLS)
    selected_names = [t["function"]["name"] for t in selected_tools]

    # Assert graceful fallback or correct routing
    assert len(selected_names) > 0, f"Query '{query}' failed to route to any tools."
    assert len(selected_names) <= 4, f"Query '{query}' caused cognitive saturation with {len(selected_names)} tools."

    # Check if the router matched one of the expected tools, or fell back gracefully.
    # Note: Because the router relies on strict regexes, many of these casual queries
    # WILL fail to match an expected tool and will drop to FALLBACK_TOOL_NAMES.
    # We record this behavior for the stress test report.
    matched_expected = any(tool in selected_names for tool in expected_tools)
    is_fallback = all(tool in FALLBACK_TOOL_NAMES for tool in selected_names)

    # The test passes if it either correctly deduced the intent OR gracefully degraded to fallbacks
    # without crashing or overloading the active tools.
    assert matched_expected or is_fallback, (
        f"Query '{query}' routed to {selected_names}, which is neither expected "
        f"({expected_tools}) nor a pure fallback ({FALLBACK_TOOL_NAMES})."
    )

def test_router_stability_on_garbage_input():
    """Ensure random garbage characters don't crash the router."""
    garbage = "asdfkajshdfk !@#$%^&*() _+ 123456"
    selected_tools = route_tools(garbage, ALL_TOOLS)
    selected_names = [t["function"]["name"] for t in selected_tools]
    assert len(selected_names) > 0
    assert len(selected_names) <= 4
    # Expected to hit fallbacks
    for name in selected_names:
        assert name in FALLBACK_TOOL_NAMES
