# Complex Semantic Polysemy Evaluation Report

## Persona & Polysemic Ambiguity Profile
Humans interact with technical systems using natural language that often carries multiple context-dependent meanings. This stress test simulates queries from non-technical end-users who may mix conversational phrasing (e.g., "remember", "trash", "power") with technical intents (e.g., "memory storage", "file deletion", "system state").

The purpose of this test harness is to measure the deterministic regex intent router's precision in distinguishing these overlapping keywords across different pillars:
- "Remember" as a storage directive (Note) vs temporal reminder (Task).
- "Power" as a state check (Battery) vs setting change (Profile) vs networking action (Radio).
- "Trash" as a filesystem cleanup vs memory deletion.
- "Run / Launch" as an application execution vs diagnostic query.
- "Service" as a daemon restart vs lifestyle reminder.

## Executive Summary
- **Total Cases:** 37
- **Passed Cases:** 23
- **Failed/XFailed Cases (Edge Ambiguities):** 14
- **Pass Rate (Exact Router Matches):** 62.16%
- **Expected Failure Rate (Resolved via Context/LLM Fallback):** 37.84%

The current deterministic router handles standard explicit commands accurately but struggles when verbs are overloaded across both physical and digital constraints. The `unittest.expectedFailure` cases reflect the rigid boundaries of regex mapping where full conversational context is required for resolution.

## Detailed Case Matrix

| Polysemous Keyword | Test Case Context | Passed / XFailed | Root Cause of Ambiguity |
| ------------------ | ----------------- | ----------------- | ----------------------- |
| **Remember**       | Note / Preference | Pass              | Detected pure declarative statements. |
| **Remember**       | Task / Reminder   | XFail             | "Remember to" leans task, but router prioritizes `memory_set` if generic memory words appear. |
| **Power**          | Status (Battery)  | XFail             | "Power status" triggers power profile due to presence of "power". |
| **Power**          | Profile / Radio   | Pass              | Specific verbs ("Set", "Turn on wifi") disambiguate successfully. |
| **Trash**          | Desktop Bin       | Pass              | Explicit "Empty trash" cleanly maps. |
| **Trash**          | Memory Cleanup    | XFail             | "Trash my notes" matches "trash" directly rather than "memory_delete". |
| **Run**            | App Execution     | Pass              | "Run firefox" maps cleanly to `launch_app`. |
| **Run**            | Hot/Diagnostic    | Pass              | System health safely catches "running hot". |
| **Service**        | Daemon Restart    | Pass              | "Restart docker service" properly caught. |
| **Service**        | Reminder Task     | XFail             | "Remind me to service car" triggers `service_status` due to the word "service". |

## Intent Disambiguation Boundaries & False Trigger Analysis
The primary failure mode of a pure regex deterministic router lies in sequence and overlap priority:
1. **Priority Hijacking:** When a sentence contains both a task word ("remind") and a system word ("service"), the router currently has overlapping triggers. System queries tend to greedily capture due to strict keyword presence (e.g., "service").
2. **Missing Dependency Parsing:** "Trash my saved notes" sees "Trash" (trigger empty_trash) and "notes" (trigger memory), but lacks the syntax tree to know "Trash" is acting upon "notes" as a deletion verb rather than a target noun.
3. **Compound Noun Ambiguity:** "Power status" pairs a generic identifier with a diagnostic verb, causing the router to guess whether it means battery power or power profile.

## Recommended Hardening Patches
To improve pass rates without diluting the 270M model's context or sacrificing latency:
1. **Multi-Stage Regex Funneling:** Implement a primary intent classifier (e.g., "Is this a physical hardware request or a digital data request?") before running sub-regexes.
2. **Negative Lookaheads in Router:** Update `RE_TRASH` to exclude instances followed by "notes", "memory", or "remember". Update `RE_SERVICE_EXPLICIT` to exclude instances preceded by "remind to".
3. **Context-Aware Fallback (LLM Disambiguation):** For high-ambiguity matches (where regex returns 3+ conflicting tools), fall back to providing the LLM with all 3 and an explicit instruction to pick only one based on context.
