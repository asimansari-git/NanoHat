# Complex Conversational Follow-ups Stress Test Report

## Persona & Multi-Turn Shorthand Profile
This stress test is modeled after a typical human user interacting with a Linux desktop environment OS assistant. Humans natively utilize contextual conversational shorthands, often known as anaphora, cross-referencing previous statements. A typical conversation turn behaves in the following profile:
1. **Explicit Entity Turn**: Introduce a clear entity (e.g., "Is wireplumber service running?", "How hot is my CPU?", "Open firefox").
2. **Anaphoric Shorthand Turn**: Action or follow up utilizing a pronoun / contextual implicit reference (e.g., "Restart it then", "And what about the RAM?", "Actually open chromium instead").

## Executive Summary
- **Total multi-turn interaction tests**: 99 unique test cases covering 50 sequence workflows (routing scenarios + engine multi-turn mocking scenarios).
- **Passed**: 52 explicitly expected successful workflows.
- **Failed (XFailed)**: 47 Known architectural limitations correctly yielding Expected Failures (XFail).
- **Pass Rate (Adjusted for XFail)**: 100% test-suite completion rate.
- **Failures Identified**: Deterministic string-regex routing inherently drops contextual subject-object dependencies.

## Detailed Case Matrix
| Scenario Sequence | Turn Example | Route Status | Notes |
|-------------------|--------------|--------------|-------|
| 1. CPU / Power | "How hot is my CPU?" -> "And what about the RAM?" -> "Is that normal?" -> "Turn on power saver mode then." | Pass / Pass / **XFail** / Pass | Standalone phrases like "Is that normal?" lack metric/hardware keywords to route correctly. |
| 2. Service Restart | "Is wireplumber service running?" -> "Restart it then" -> "Check its status once more" | Pass / **XFail** / Pass | "Restart it then" drops the explicit daemon/service target regex string. |
| 3. Memory Set/Delete | "Remember my favorite editor is Neovim" -> "Actually forget that" -> "Remember it is Emacs now" | Pass / Pass / Pass | Covered smoothly via intent words ("remember", "forget"). |
| 4. Network Radio | "Is wifi connected?" -> "Turn it off" | Pass / **XFail** | "Turn it off" lacks the keyword 'wifi' required by the network regex. |
| 5. Calculator | "Calculate 10 + 15" -> "Multiply that by 3" | Pass / **XFail** | Math logic via "Multiply that" gets missed by explicit operator symbol checks in regex. |
| 6. Time/Date | "What time is it?" -> "And the date?" | Pass / Pass | |
| 7. Power/Battery | "How much battery do I have left?" -> "Turn on power saver" -> "Is it saving now?" | Pass / Pass / **XFail** | "Is it saving now?" does not hit the explicit "power profiles" keywords. |
| 8. Housekeeping | "Empty the trash" -> "Did you do it?" | Pass / **XFail** | |
| 9. App Launcher | "Open firefox" -> "Actually open chromium instead" -> "What about terminal?" | Pass / Pass / **XFail** | "terminal" without an explicit launcher verb ('open', 'launch') bypasses intent. |
| 10. Task Manager | "Remind me to eat at 5pm" -> "Cancel that" | Pass / **XFail** | |

## Anaphora Resolution & Context Window Boundary Analysis
The deterministic intent router (`runtime/router.py`) sits in front of the Large Language Model inference API. While the LLM operates with conversational context awareness via multi-turn chat history (which we validated in `test_engine_multiturn_mocked`), the router operates strictly amnesiac and contextless.

When a user submits "Restart it then", the `router.py` does not review the fact that the previous user message queried `wireplumber`. Consequently, `route_tools` fails to supply `restart_service` to the dynamic LLM system prompt because it lacks the 'service/daemon' intent keywords in isolation.

## Recommended Architectural Patches for NanoHat runtime
To successfully merge contextual anaphoric intent with strict deterministic gating, we recommend the following enhancements:

1. **Lightweight LLM Query Rewriter (Query Expansion)**: Insert an ultra-fast query expansion pass before `route_tools`. For example, `f("Restart it then", Context: ["Is wireplumber service running?"]) -> "Restart wireplumber service"`. The deterministic router can then route on the expanded query.
2. **Turn-based Router Memory**: Introduce a bounded memory buffer in `router.py`. If a query strongly maps to an explicit cluster on Turn 1 (e.g. `service_status`), the router could lazily append `service_status` and `restart_service` as fallback context schemas to any unrecognized Turn 2 queries.
3. **Contextual Fallback Schema Heuristic**: Broaden the default fallback set if recent interactions were observed (e.g. if the last turn was `launch_app`, append `launch_app` to the default schema temporarily).
