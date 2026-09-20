# NanoHat v3.0.0 Stress Test Report
**Persona:** Corporate Office Worker / Professional

## Persona Profile & Test Vector
This test suite simulates a business-oriented workflow typical for a corporate professional. The vectors primarily cover:
- Calendar scheduling and deadline reminders (e.g., quarterly reviews, standup checks).
- Corporate productivity applications and service status queries (e.g., Slack, Microsoft Teams, LibreOffice, Zoom).
- Memory retention for workflows (e.g., tracking employee ID, tracking budget approvals).
- Basic math parsing for financial contexts (e.g., Q1 revenue margins).
- Hardware management before flights or travel (Wi-Fi, Bluetooth, battery).

## Executive Summary
- **Total Queries Evaluated:** 43
- **Passed Queries:** 39
- **Failed Queries:** 4
- **Overall Pass Rate:** 90.7%
- **Scheduling Accuracy:** 100% (All `task_add`, `task_cancel`, and `task_list` variants correctly routed either by regex clustering or fallback).

## Detailed Case Matrix (Subset)

| Query | Target Tool(s) | Result | Notes |
| :--- | :--- | :--- | :--- |
| Remind me to sync with the product team tomorrow at 9:30 AM | `task_add` | OK | Task scheduling correctly inferred |
| Schedule weekly standup check every Monday | `task_add` | OK | Fallback/Router handles non-explicit times |
| launch slack and check if meeting is active | `service_status` | OK | Identifies service polling intent |
| Is Slack running? | `service_status` | OK | Standard daemon check |
| set memory: quarterly review deadline is Oct 15 | `memory_set` | OK | Exact keyword matches via `memory` fallback |
| Remember that the marketing budget is approved | `memory_set` | OK | Exact keyword matches via `remember` fallback |
| Save my employee ID as 123456 | `memory_set` | ERROR | Neither `memory` nor `remember` triggered intent. Sent to base tools. |
| What is the quarterly review deadline? | `memory_get` | ERROR | Ambiguous contextual data retrieval failed regex matching |
| Did the marketing budget get approved? | `memory_get` | ERROR | Lack of strict memory terms defaults to standard fallback |
| What time is my next meeting and is my battery full? | `system_health`, `get_datetime`, `task_list` | OK | Complex overlapping tools routed correctly. |

## Critical Edge Cases & Failures Discovered

The test identified a critical weakness in how NanoHat's deterministic routing parses **Persistent Memory** (Store/Retrieval/Delete) interactions.

**Specific Failure Cases:**
1. `Save my employee ID as 123456`
2. `What is the quarterly review deadline?`
3. `Did the marketing budget get approved?`
4. `Delete the quarterly review deadline note`

**Root Cause Analysis:**
The intent router and the engine's deterministic fallback heavily rely on exact keywords like "memory", "remember", or explicit commands like "set memory". When the user uses terms like "Save", "What is the", or "Did the", the query fails to hit the `memory_*` tool clusters. Instead, it gets routed to the base/default tools (`system_health`, `get_datetime`, `calculator`), dropping the intent completely.

## Recommended Hardening Patches for NanoHat runtime

To fix the memory retrieval and storage issues, the routing layer needs improved alias matching for memory operations:

1. **Broaden Memory Engine Fallbacks (`engine.py` / `router.py`):**
   - Add aliases for `memory_set`: "save", "note", "store", "keep track of".
   - Add contextual clues for `memory_get`: If a query is structured as a direct entity question ("What is my...", "What is the...", "Did the...") and fails other specific tool rules, it should dynamically include `memory_get` in its evaluation subset.
   - Expand `memory_delete`: "delete", "erase", "remove", "clear".

2. **Regex Expansion in `router.py`:**
   - Modify the pre-compiled regex clusters handling the persistent memory tools to capture these broader intents, preventing them from falling through to the generic default tool block (which currently defaults to `[system_health, get_datetime, calculator]`).

By applying these patches, the agent can retain its sub-1B parameter constraint while effectively capturing human-like memory interactions without requiring explicit "memory" keywords.