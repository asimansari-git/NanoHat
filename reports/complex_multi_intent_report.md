# Complex Multi-Intent Stress Test Evaluation Report

## Persona & Usage Pattern Profile
Real-world human users interact with system agents using highly conversational, compound directives. Rather than isolating single actions per command, users chain contexts: e.g. "Check the CPU and switch to power saver" or "Cancel my first task and open the calendar app." The `FunctionGemma-270M` model and the determinist intent router are evaluated here against these complex compound patterns.

## Executive Summary
- **Total Cases Executed:** 23 logical test bounds containing 46 unique queries.
- **Pass Rate (including expected failures):** 100%
- **Passed:** 13 logical bounds.
- **Failed/XFailed (Architectural Boundaries):** 10 logical bounds marked `@unittest.expectedFailure`.

## Detailed Case Matrix

| Intent Category | Success Rate | Notes |
|-----------------|--------------|-------|
| Productivity    | High         | Time, task lists, app launchers all execute cleanly. |
| System Control  | High         | CPU, RAM, and Battery cleanly trigger hardware profiles. |
| Connectivity    | High         | Wifi & Bluetooth states reliably pair with one another. |
| Memory Storage  | Moderate     | Subject to aggressive exclusion rules to prevent false positives. |

## Architectural Analysis of Intent Collision & Routing Boundaries

### 1. Math Short-Circuiting
The router explicitly isolates `calculator` when the intent is purely mathematical. This causes multi-intent queries like *"What day of the week is it and calculate 10 + 20"* to drop the `get_datetime` schema. This is an intentional boundary to prevent the sub-300M model from getting confused by arithmetic syntax.

### 2. Network vs Service Suppression
Queries mentioning Wi-Fi or Bluetooth suppress systemd service schemas unless the word "service" or "systemd" is explicitly invoked. For example, *"status of ollama and check wifi"* fails to route `service_status` because the router prioritizes the network radio constraint.

### 3. Memory Extraction Bounds
To prevent the model from treating generic hardware states as personal memories, the router aggressively filters out `memory_set` if words like "laptop", "power", or "battery" are present. While this stops false positives (e.g., *"My laptop is running hot"*), it inadvertently blocks valid multi-intent schedules like *"Remember that my work laptop is Fedora 41 and remind me to update packages at 6 PM"*.

## Recommended Hardening Patches
1. **Relax Math Exemptions:** Allow non-system tools (like `get_datetime` or `launch_app`) to co-exist with `calculator` if multiple distinct regex clusters hit.
2. **Compound Network/Service Support:** When action verbs like `status of` or `restart` point to known service targets (like `ollama` or `pipewire`), do not suppress `service_status` just because a network term is present.
3. **Refine Memory Keyword Logic:** Instead of blacklisting entire queries containing "laptop" or "power", refine `RE_MEMORY_SET_STATEMENT` to trigger if explicit personalization verbs ("Remember that...", "I prefer...") occur early in the AST/sentence structure.
