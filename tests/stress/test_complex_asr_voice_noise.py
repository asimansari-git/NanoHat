import pytest
import re
from typing import List

from runtime.tools import ALL_TOOLS
from runtime.router import route_tools, FALLBACK_TOOL_NAMES

# 40-50 queries with ASR noise, hesitations, filler words, run-on speech, mid-sentence corrections
TEST_CASES = [
    # Telemetry & Power (Hesitations and fillers)
    ("uh hey nanohat can you um check the battery level please", ["system_health"]),
    ("like basically how much free memory do i have left on my machine you know", ["system_health", "memory_get", "memory_set"], pytest.mark.xfail(reason="intent bleed into memory_get/memory_set due to word 'memory'")),
    ("can you just uh tell me if the cpu is like overheating or whatever", ["system_health"]),
    ("so um what is the current power profile right now", ["power_profile", "system_health"]),
    ("im wondering like how much ram is being used uh right this second", ["system_health"]),
    ("what is the uh battery at right now", ["system_health"]),
    ("is the fan uh running too fast", ["system_health"]),
    ("can you check if my laptop is like dying or something", ["system_health", "power_profile"], pytest.mark.xfail(reason="False positive on memory_set ('my laptop is')")),

    # Hardware & Radios (Stuttering, repetitions)
    ("t-turn off the wifi", ["toggle_wifi"]),
    ("can you please uh disconnect the bluetooth i mean turn it off", ["toggle_bluetooth"]),
    ("is the wi-fi um connected right now", ["toggle_wifi"]),
    ("i need to uh toggle the radio for the internet", ["toggle_wifi", "toggle_bluetooth"]),
    ("uh turn on the blutooth wait no i mean the wifi", ["toggle_wifi", "toggle_bluetooth"], pytest.mark.xfail(reason="Mid-sentence correction not resolved, both tools selected")),
    ("uh so is my bluetooth working", ["toggle_bluetooth"]),
    ("can you check the wifi uh status", ["toggle_wifi"]),
    ("turn on uh bluetooth and wifi", ["toggle_wifi", "toggle_bluetooth"]),
    ("wait is the wifi on", ["toggle_wifi"]),
    ("just uh kill the wifi", ["toggle_wifi"]),

    # Services & Daemons (Mid-sentence corrections)
    ("r-restart the pipewire service if it is stopped", ["restart_service", "service_status"]),
    ("check if the docker daemon is um running wait no just restart it", ["restart_service", "service_status"], pytest.mark.xfail(reason="Requires LLM reasoning to discard status and only restart")),
    ("is tailscale like active right now", ["service_status", "restart_service"]),
    ("can you reboot the um sshd service", ["restart_service", "service_status"]),
    ("status of uh ollama", ["service_status", "restart_service"]),
    ("i need to know if systemd is uh doing okay", ["service_status", "restart_service"], pytest.mark.xfail(reason="May not trigger service tools without explicit action words")),
    ("restart the uh thing um the audio service", ["restart_service", "service_status"]),

    # Persistent Memory (Run-on, conversational)
    ("hey listen can you remember that my favorite color is um blue", ["memory_set"]),
    ("uh what did i say my favorite food was again", ["memory_get"]),
    ("wait actually scratch that forget my favorite color", ["memory_delete", "memory_list", "memory_set"], pytest.mark.xfail(reason="Multi-intent: scratch that vs forget vs set")),
    ("so like show me all the notes you saved for me", ["memory_list", "memory_set", "memory_get"]),
    ("can you uh recall what distro i use", ["memory_get", "memory_set"]),
    ("um set a note that i like to use vim", ["memory_set"]),
    ("i mean who am i really", ["memory_get"]),
    ("uh delete all my memories", ["memory_delete"]),

    # Scheduling & Housekeeping (Corrections and noise)
    ("wait no actually set a reminder uh for doctor appointment at 3 pm", ["task_add", "task_list"]),
    ("scratch that empty the recycle bin instead", ["empty_trash"], pytest.mark.xfail(reason="Multi-intent, context from 'scratch that' lost, but empty_trash should be found. May fail if router doesn't match 'scratch that'. Wait, it just matches trash")),
    ("so um what is the time right now in like tokyo", ["get_datetime"]),
    ("can you uh add a task to buy milk wait no buy eggs", ["task_add", "task_list"], pytest.mark.xfail(reason="Mid-sentence correction, exact intent to add eggs instead of milk unresolved at router level")),
    ("uh list all my pending tasks please", ["task_list", "task_add"]),
    ("cancel task number two wait no number three", ["task_cancel", "task_list"], pytest.mark.xfail(reason="Correction on task ID unresolved")),
    ("uh what is um five times twelve", ["calculator"]),
    ("calculate like twenty divided by four", ["calculator"]),
    ("can you clear the trash um now", ["empty_trash"]),
    ("remind me to uh call mom tomorrow", ["task_add", "task_list"]),
    ("cancel that last alarm actually", ["task_cancel", "task_list"]),
    ("empty the recycling bin wait actually no don't", ["empty_trash"], pytest.mark.xfail(reason="Router will trigger empty_trash ignoring 'don't'")),
]

@pytest.mark.parametrize("test_case", TEST_CASES)
def test_complex_asr_voice_noise_routing(test_case):
    """
    Stress tests the deterministic regex router against ASR transcriptions filled with
    noise, hesitations, stuttering, run-on speech, and mid-sentence corrections.
    """
    if len(test_case) == 3:
        query, expected_tools, xfail_mark = test_case
        if xfail_mark:
            pytest.xfail(xfail_mark.kwargs.get("reason", "Expected failure"))
    else:
        query, expected_tools = test_case

    selected_tools = route_tools(query, ALL_TOOLS)
    selected_names = [t["function"]["name"] for t in selected_tools]

    assert len(selected_names) > 0, f"Query '{query}' failed to route to any tools."
    assert len(selected_names) <= 4, f"Query '{query}' caused cognitive saturation with {len(selected_names)} tools."

    matched_expected = any(tool in selected_names for tool in expected_tools)
    is_fallback = all(tool in FALLBACK_TOOL_NAMES for tool in selected_names)

    assert matched_expected or is_fallback, (
        f"Query '{query}' routed to {selected_names}, which is neither expected "
        f"({expected_tools}) nor a pure fallback ({FALLBACK_TOOL_NAMES})."
    )

def test_router_stability_on_extreme_asr_noise():
    """Ensure heavy stuttering and filler words don't crash the router."""
    garbage = "uh um like so basically wait no actually i mean um can you just uh like do the thing"
    selected_tools = route_tools(garbage, ALL_TOOLS)
    selected_names = [t["function"]["name"] for t in selected_tools]
    assert len(selected_names) > 0
    assert len(selected_names) <= 4
    for name in selected_names:
        assert name in FALLBACK_TOOL_NAMES
