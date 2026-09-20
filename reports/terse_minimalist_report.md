# Terse Minimalist Evaluation Report

## Persona Profile & Test Vector
- **Persona:** Single-Word Terse Minimalist User
- **Profile:** Emits ultra-concise, single-word or 2-word telegraphic inputs with zero conversational filler.
- **Examples:** 'wifi', 'battery', 'trash', 'calc 99*4', 'memo test 123'
- **Test Vector:** Synthetic behavioral fuzzing testing zero-context classification, default action routing when verbs are missing, and token-constrained prompt sensitivity against the `NanoHat v3` intent router (`runtime/router.py`).

## Executive Summary
- **Total Queries Tested:** 43
- **Passed Queries:** 41
- **Failed Queries (Misrouted):** 2
- **Pass Rate:** 95.35%
- **Zero-Context Resolution Rate:** Very high. Most single keywords successfully map to the appropriate primary and secondary tool schemas.

## Detailed Case Matrix

| Input Query | Inferred Tools | Target Tool | Result |
| :--- | :--- | :--- | :--- |
| `wifi` | `['toggle_wifi']` | `toggle_wifi` | OK |
| `wifi on` | `['toggle_wifi']` | `toggle_wifi` | OK |
| `wifi off` | `['toggle_wifi']` | `toggle_wifi` | OK |
| `bt` | `['toggle_bluetooth']` | `toggle_bluetooth` | OK |
| `bluetooth` | `['toggle_bluetooth']` | `toggle_bluetooth` | OK |
| `bt toggle` | `['toggle_bluetooth']` | `toggle_bluetooth` | OK |
| `network` | `['toggle_wifi']` | `toggle_wifi` | OK |
| `battery` | `['system_health']` | `system_health` | OK |
| `charge` | `['system_health']` | `system_health` | OK |
| `health` | `['system_health']` | `system_health` | OK |
| `ram` | `['system_health']` | `system_health` | OK |
| `cpu` | `['system_health']` | `system_health` | OK |
| `swap` | `['system_health']` | `system_health` | OK |
| `power` | `['power_profile']` | `power_profile` | OK |
| `profile` | `['power_profile']` | `power_profile` | OK |
| `saver` | `['power_profile']` | `power_profile` | OK |
| `performance` | `['power_profile']` | `power_profile` | OK |
| `trash` | `['empty_trash']` | `empty_trash` | OK |
| `bin` | `['empty_trash']` | `empty_trash` | OK |
| `calc 2+2` | `['calculator']` | `calculator` | OK |
| `math 5/5` | `['calculator']` | `calculator` | OK |
| `date` | `['get_datetime']` | `get_datetime` | OK |
| `time` | `['get_datetime']` | `get_datetime` | OK |
| `today` | `['get_datetime']` | `get_datetime` | OK |
| `now` | `['get_datetime']` | `get_datetime` | OK |
| `clock` | `['get_datetime']` | `get_datetime` | OK |
| `services` | `['service_status', 'restart_service']` | `service_status` | OK |
| `systemd` | `['service_status', 'restart_service']` | `service_status` | OK |
| `daemon` | `['service_status', 'restart_service']` | `service_status` | OK |
| `restart ollama` | `['restart_service', 'service_status']` | `restart_service` | OK |
| `status pipewire` | `['system_health', 'get_datetime', 'calculator']` | `service_status` | **ERROR** |
| `memory` | `['memory_set', 'memory_get']` | `memory_set` | OK |
| `remember` | `['memory_set']` | `memory_set` | OK |
| `forget` | `['memory_delete']` | `memory_delete` | OK |
| `recall` | `['memory_get']` | `memory_get` | OK |
| `tasks` | `['task_add', 'task_list']` | `task_list` | OK |
| `todo` | `['task_add', 'task_list']` | `task_add` | OK |
| `remind` | `['task_add', 'task_list']` | `task_add` | OK |
| `cancel task` | `['task_cancel', 'task_list']` | `task_cancel` | OK |
| `whoami` | `['memory_set', 'memory_get']` | `memory_get` | OK |
| `memo test 123` | `['system_health', 'get_datetime', 'calculator']` | `memory_set` | **ERROR** |
| `calc 99*4` | `['calculator']` | `calculator` | OK |
| `reboot bluetooth`| `['toggle_bluetooth']` | `toggle_bluetooth` | OK |

## Critical Ambiguities & Misrouted Tools
1. **Service Status Ambiguity**: The query `status pipewire` fails to trigger the `service_status` tool and falls back to default tools (`system_health`, `get_datetime`, `calculator`). The router regex `RE_SERVICE_ACTION` looks for `\b(status of|state of|is|check|restart|reload)\s+([a-zA-Z0-9_\-\.]+)\b` which doesn't match just `status pipewire` (it expects "status of" or just "check").
2. **Memory Keyword Coverage**: The query `memo test 123` falls back to default tools. The regex `RE_MEMORY_WORDS` includes `remem*`, `recall*`, `memory`, etc., but does not include `memo` or `note` as a standalone keyword in that specific pattern (though `note` triggers memory when combined with `save/set` logic, `memo` does not).

## Recommended Hardening Patches
- **Update `RE_SERVICE_ACTION` in `runtime/router.py`**: Add support for the standalone word `status` followed by a service name. E.g., change `\b(status of|state of|is|check|restart|reload)\s+` to `\b(status|status of|state of|is|check|restart|reload)\s+`.
- **Update `RE_MEMORY_WORDS` in `runtime/router.py`**: Add `memo` and `note` as primary intent triggers to ensure short-hand memoizations route to the persistent memory suite. E.g., `\b(remem[a-z]*|remeb[a-z]*|recall[a-z]*|forget[a-z]*|memory|memories|preference|preferences|saved\s+note|saved\s+notes|memo|note)\b`.
