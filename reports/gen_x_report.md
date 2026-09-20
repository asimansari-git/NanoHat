# NanoHat v3: Gen X / Traditionalist Stress Test Evaluation Report

## Persona Profile & Test Vector
**Persona:** Gen X / Traditionalist
**Characteristics:** Highly formal, polite, complete grammatical sentences, explicit punctuation, and traditional file-manager expectations.
**Test Vector:** The deterministic intent router (`runtime/router.py`) was evaluated against 45 formal queries designed to test whether excessive courtesy wrappers, formal phrasing, and classic desktop terminology (e.g. "hard drive", "World Wide Web") would misroute intents or degrade tool mapping.

## Executive Summary
**Total Queries:** 45
**Pass Rate:** ~69% (31 passing queries out of 45 individually routed)
**Courtesy Filter Efficiency:** Poor. The router is brittle to courtesy words masking intent (e.g., "tell me what 500 minus 32.50 is" gets routed to `memory_get` due to "what"). Traditional hardware queries (e.g., "performance") get routed to power management instead of generic system health.

## Detailed Case Matrix
| Query | Expected Target Tool | Result | Notes |
| :--- | :--- | :--- | :--- |
| "Good morning. Could you please be so kind as to tell me the current date and time?" | `get_datetime` | **OK** | Matched `time` and `date`. |
| "Kindly delete the contents of my recycling bin at your earliest convenience." | `empty_trash` | **OK** | Matched `recycling bin`. |
| "Could you please save a reminder that my grandson's name is Timothy?" | `memory_set` | **ERROR** | Routed to `task_add`, `task_list`. The word "reminder" triggers task scheduling, overriding the memory set intent. |
| "Could you please retrieve the note containing my insurance policy number?" | `memory_get` | **ERROR** | Routed to fallbacks `['system_health', 'get_datetime', 'calculator']`. The word "note" failed to trigger memory retrieval. |
| "I am concerned about my computer's performance. Could you please run a diagnostic on the system health?" | `system_health` | **ERROR** | Routed to `power_profile`, `memory_set`. "performance" triggers power profile, overriding system health. |
| "Kindly inform me if the Wireless Fidelity interface is currently active." | `toggle_wifi` | **ERROR** | Routed to `service_status`, `restart_service`. "active" triggers the service daemon checker. |
| "I request that you create an alert to notify me when the laundry is finished." | `task_add` | **ERROR** | Routed to fallbacks. "alert" or "notify" are not recognized as tasks. |
| "I am trying to balance my checkbook. Could you tell me what 500 minus 32.50 is?" | `calculator` | **ERROR** | Routed to `memory_get`. "what" triggers memory getter instead of math parser. |

## Critical Edge Cases & Failures Discovered
1. **Keyword Collisions:** Words like "reminder" used in the context of persistent memory ("save a reminder that...") trigger the task scheduler instead of the memory key-value store.
2. **Obsolete/Formal Terminology:** "Wireless Fidelity", "alert", "notify", "note" are missing from the intent dictionaries.
3. **Action Verbs Overriding Intent:** The word "active" in "Wireless Fidelity interface is currently active" triggered `_is_service_query()` logic, treating the query as a systemd service check.
4. **Question Words Hijacking:** "What" in "what 500 minus 32.50 is" incorrectly matched the `RE_MEMORY_QUERY` regex, routing arithmetic to memory retrieval.

## Recommended Hardening Patches for NanoHat runtime
1. **Enhance Regex Definitions in `router.py`:**
   - Add "note" and "retrieve" to `RE_MEMORY_WORDS` or a specific retrieval pattern.
   - Add "alert" and "notify" to `RE_TASK`.
   - Update `RE_NETWORK` to include "wireless fidelity".
2. **Refine Intent Hierarchy and Stopwords:**
   - Math expressions (`RE_MATH_EXPR`) must take absolute precedence over memory queries (like "what is...").
   - Service routing `_is_service_query()` should exclude common network terms if a network match is also present, or prioritize network tools.
   - Separate "reminder" for tasks from "remind me that/of" for memory, potentially using multi-word lookaheads.
