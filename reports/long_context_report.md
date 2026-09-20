# Long Context and Backstory Dumper Evaluation Report

## Persona Profile & Test Vector
- **Persona:** Long-Context Wall-of-Text / Backstory Dumper
- **Characteristics:** Dumps massive paragraphs, error logs, and elaborate conversational backstories before asking for a single action.
- **Test Vector:** Tests context window truncation, needle-in-a-haystack command extraction, and prevention of prompt overflow crashes.
- **Methodology:** Generated 40 high-word-count queries (300-800 words) burying distinct target tool requests. Tested against the intent router and dispatcher.

## Executive Summary
- **Total Queries:** 40
- **Passed (Needle Extracted):** 30
- **Failed (Context Dilution):** 10
- **Pass Rate:** 75.00%

## Detailed Case Matrix

| Case ID | Word Count | Target Tool | Routed Tools | Result |
|---|---|---|---|---|
| 1 | 355 | `task_add` | `get_datetime, task_list, task_add` | OK |
| 2 | 87 | `system_health` | `calculator, system_health` | OK |
| 3 | 283 | `memory_set` | `calculator, system_health, task_list, task_add` | ERROR |
| 4 | 85 | `calculator` | `calculator, system_health` | OK |
| 5 | 309 | `calculator` | `calculator` | OK |
| 6 | 237 | `task_add` | `get_datetime, empty_trash, task_list, task_add` | OK |
| 7 | 231 | `system_health` | `get_datetime, system_health, empty_trash, task_list` | OK |
| 8 | 216 | `memory_set` | `get_datetime, empty_trash, task_list, task_add` | ERROR |
| 9 | 278 | `task_add` | `calculator, get_datetime, system_health, empty_trash` | ERROR |
| 10 | 303 | `memory_set` | `service_status, restart_service, task_list, task_add` | ERROR |
| 11 | 203 | `task_add` | `service_status, restart_service, task_add, task_list` | OK |
| 12 | 277 | `calculator` | `calculator, get_datetime, system_health, empty_trash` | OK |
| 13 | 298 | `calculator` | `calculator, get_datetime, system_health, empty_trash` | OK |
| 14 | 259 | `get_datetime` | `calculator, get_datetime, system_health` | OK |
| 15 | 197 | `task_add` | `calculator, get_datetime, system_health, empty_trash` | ERROR |
| 16 | 295 | `empty_trash` | `calculator, get_datetime, system_health, empty_trash` | OK |
| 17 | 362 | `calculator` | `calculator` | OK |
| 18 | 215 | `toggle_wifi` | `get_datetime, toggle_wifi, service_status, restart_service` | OK |
| 19 | 216 | `get_datetime` | `get_datetime, service_status, restart_service, task_add` | OK |
| 20 | 184 | `calculator` | `calculator, get_datetime, system_health, empty_trash` | OK |
| 21 | 240 | `get_datetime` | `get_datetime, task_list, task_add` | OK |
| 22 | 283 | `system_health` | `get_datetime, service_status, restart_service, system_health` | OK |
| 23 | 272 | `get_datetime` | `calculator, get_datetime, system_health, empty_trash` | OK |
| 24 | 114 | `get_datetime` | `get_datetime, empty_trash` | OK |
| 25 | 134 | `memory_set` | `task_list, task_add` | ERROR |
| 26 | 179 | `task_add` | `calculator, system_health, task_add, task_list` | OK |
| 27 | 165 | `restart_service` | `calculator, system_health` | ERROR |
| 28 | 217 | `task_add` | `get_datetime, empty_trash, task_list, task_add` | OK |
| 29 | 140 | `get_datetime` | `get_datetime, task_add, task_list` | OK |
| 30 | 222 | `memory_set` | `get_datetime, empty_trash, task_list, task_add` | ERROR |
| 31 | 86 | `empty_trash` | `calculator, system_health, empty_trash` | OK |
| 32 | 279 | `toggle_wifi` | `get_datetime, toggle_wifi, service_status, restart_service` | OK |
| 33 | 220 | `restart_service` | `calculator, get_datetime, system_health, task_add` | ERROR |
| 34 | 341 | `empty_trash` | `calculator, get_datetime, system_health, empty_trash` | OK |
| 35 | 214 | `restart_service` | `get_datetime, restart_service, service_status, task_add` | OK |
| 36 | 335 | `calculator` | `get_datetime, empty_trash, task_list, task_add` | ERROR |
| 37 | 230 | `toggle_wifi` | `toggle_wifi, task_list, task_add` | OK |
| 38 | 223 | `system_health` | `get_datetime, system_health, empty_trash, task_list` | OK |
| 39 | 322 | `calculator` | `calculator` | OK |
| 40 | 318 | `empty_trash` | `calculator, get_datetime, system_health, empty_trash` | OK |

## Critical Context Failures & Truncation Anomalies Discovered
- **Target:** `memory_set` was missed. Routed: `['calculator', 'system_health', 'task_list', 'task_add']`.
  - **Context excerpt:** 'Journalctl log output follows:
kernel: Linux version 6.1.18-200.fc37.x86_64
kernel: Command line: BO...'
- **Target:** `memory_set` was missed. Routed: `['get_datetime', 'empty_trash', 'task_list', 'task_add']`.
  - **Context excerpt:** 'Listen, I don't mean to rant, but the way this project is being managed is an absolute disaster. The...'
- **Target:** `task_add` was missed. Routed: `['calculator', 'get_datetime', 'system_health', 'empty_trash']`.
  - **Context excerpt:** 'Listen, I don't mean to rant, but the way this project is being managed is an absolute disaster. The...'
- **Target:** `memory_set` was missed. Routed: `['service_status', 'restart_service', 'task_list', 'task_add']`.
  - **Context excerpt:** 'The sociological implications of a heavily networked society have been debated since the inception o...'
- **Target:** `task_add` was missed. Routed: `['calculator', 'get_datetime', 'system_health', 'empty_trash']`.
  - **Context excerpt:** 'Listen, I don't mean to rant, but the way this project is being managed is an absolute disaster. The...'
- **Target:** `memory_set` was missed. Routed: `['task_list', 'task_add']`.
  - **Context excerpt:** 'I've been staring at this screen for what feels like 12 hours straight. The coffee ran out around 2 ...'
- **Target:** `restart_service` was missed. Routed: `['calculator', 'system_health']`.
  - **Context excerpt:** 'Journalctl log output follows:
kernel: Linux version 6.1.18-200.fc37.x86_64
kernel: Command line: BO...'
- **Target:** `memory_set` was missed. Routed: `['get_datetime', 'empty_trash', 'task_list', 'task_add']`.
  - **Context excerpt:** 'You know, I remember when I first got my dog, a golden retriever named Buster. He was so small he co...'
- **Target:** `restart_service` was missed. Routed: `['calculator', 'get_datetime', 'system_health', 'task_add']`.
  - **Context excerpt:** 'You know, I remember when I first got my dog, a golden retriever named Buster. He was so small he co...'
- **Target:** `calculator` was missed. Routed: `['get_datetime', 'empty_trash', 'task_list', 'task_add']`.
  - **Context excerpt:** 'I've been staring at this screen for what feels like 12 hours straight. The coffee ran out around 2 ...'

## Recommended Hardening Patches for NanoHat runtime
- **Enhanced Regex Boundaries:** To further prevent false positives from long stories (e.g., mentioning "my battery died yesterday" in a story triggering `system_health`), we recommend tightening the regex patterns in `router.py` to look for imperative verbs (e.g., "check", "set", "turn") in proximity to the keywords.
- **Length Throttling:** Consider a pre-processing step that summarizes excessively long queries before routing, though this may incur a latency penalty.
- **Stopword Expansion:** Add more conversational stop words to the router's ignore list to prevent spurious matches from narrative text.
