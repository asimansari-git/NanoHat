# Multilingual & Hinglish Evaluation Report

## Persona Profile & Test Vector
- **Persona:** Multilingual & Hinglish User
- **Profile:** Mixes English with Hindi/Urdu (Hinglish), Spanish, or colloquial non-native English code-switching.
- **Goal:** Test cross-lingual keyword extraction, intent preservation across romanized code-switching, and resilience against non-English syntax in the deterministic intent router (`runtime/router.py`).

## Executive Summary
- **Total Queries Tested:** 48
- **Passed:** 32
- **Failed:** 16
- **Overall Pass Rate:** 66.7%
- **Key Findings:** The router excels at English and mixed Hinglish queries for Telemetry and Hardware/Radios because it looks for English keywords (`battery`, `wifi`, `bluetooth`, `ram`, `cpu`) which are often retained in code-switching. However, it completely fails on non-English queries for Memory Management and struggles with Services/Scheduling when the target action verbs (`restart`, `status`, `empty`, `cancel`) are translated (`reinicia`, `estado`, `vaciar`, `cancela`).

## Detailed Case Matrix

### 1. Telemetry & Power (Pass Rate: 100%)
| Input Query | Target Tool | Result |
| :--- | :--- | :--- |
| `battery kitni bachi hai` | `system_health` | OK |
| `cuanta memoria queda` | `system_health` | OK |
| `mera ram clean karo bro` | `system_health` | OK |
| `bateria status por favor` | `system_health` | OK |
| `cpu kaisa chal raha hai` | `system_health` | OK |
| `estado de la bateria` | `system_health` | OK |
| `memoria RAM utilizada` | `system_health` | OK |
| `power saver mode on kardo` | `power_profile` | OK |
| `modo de energia performance` | `power_profile` | OK |
| `battery percent batao` | `system_health` | OK |

### 2. Hardware & Radios (Pass Rate: 100%)
| Input Query | Target Tool | Result |
| :--- | :--- | :--- |
| `wifi band kardo please` | `toggle_wifi` | OK |
| `apaga el bluetooth` | `toggle_bluetooth` | OK |
| `wifi chalu karo` | `toggle_wifi` | OK |
| `enciende el wifi` | `toggle_wifi` | OK |
| `bluetooth on hai kya` | `toggle_bluetooth` | OK |
| `el bluetooth esta prendido` | `toggle_bluetooth` | OK |
| `wifi disconnect kar` | `toggle_wifi` | OK |
| `conectar wifi` | `toggle_wifi` | OK |
| `bt off kardo` | `toggle_bluetooth` | OK |
| `wifi status batao` | `toggle_wifi` | OK |

### 3. Services & Daemons (Pass Rate: 50%)
| Input Query | Target Tool | Result |
| :--- | :--- | :--- |
| `pipewire restart maro` | `restart_service` | OK |
| `ollama restart kardo` | `restart_service` | OK |
| `como esta el daemon de bluetooth` | `service_status` | OK |
| `systemd status dekho` | `service_status` | OK |
| `ollama chalu hai kya` | `service_status` | ERROR |
| `estado del servicio docker` | `service_status` | ERROR |
| `reinicia el servidor nginx` | `restart_service` | ERROR |
| `wireplumber chal raha hai ya nahi` | `service_status` | ERROR |

### 4. Persistent Memory (Pass Rate: 0%)
| Input Query | Target Tool | Result |
| :--- | :--- | :--- |
| `mera naam yaad rakho Rahul` | `memory_set` | ERROR |
| `mi editor favorito es vim` | `memory_set` | ERROR |
| `kya yaad hai mere bare mein` | `memory_get` | ERROR |
| `quien soy yo` | `memory_get` | ERROR |
| `mera pet name bhool jao` | `memory_delete` | ERROR |
| `borra mis notas` | `memory_delete` | ERROR |
| `sab memories dikhao` | `memory_list` | ERROR |
| `lista todas las memorias` | `memory_list` | ERROR |
| `mera favorite distro kya hai` | `memory_get` | ERROR |

### 5. Scheduling & Housekeeping (Pass Rate: 72.7%)
| Input Query | Target Tool | Result |
| :--- | :--- | :--- |
| `task add karo: kal subah 9 baje meeting hai` | `task_add` | OK |
| `trash empty kardo` | `empty_trash` | OK |
| `kitne baje hai` | `get_datetime` | OK |
| `que hora es` | `get_datetime` | OK |
| `sab tasks dikhao` | `task_list` | OK |
| `task 2 cancel kardo` | `task_cancel` | OK |
| `calculate karo 5 + 5` | `calculator` | OK |
| `cuanto es 10 * 10` | `calculator` | OK |
| `basura vaciar` | `empty_trash` | ERROR |
| `lista de tareas` | `task_list` | ERROR |
| `cancela la tarea 1` | `task_cancel` | ERROR |

## Critical Failures & Unsupported Language Gaps
1.  **Memory Intent Regex Gaps:** The memory intent regexes (`RE_MEMORY_WORDS`, `RE_MEMORY_SET_STATEMENT`, `RE_MEMORY_QUERY`) are heavily reliant on English idioms (`remember`, `my name is`, `who am i`). They fail entirely to match translated equivalents (`yaad rakho`, `mi favorito`, `quien soy yo`, `bhool jao`, `borra`).
2.  **Service Intent Rigidity:** The `RE_SERVICE_ACTION` regex specifically looks for strictly formatted English action phrases like `status of`, `state of`, or `restart`. It does not match `estado del servicio`, `reinicia`, `chalu hai kya` (is it running?), or `chal raha hai ya nahi`.
3.  **Scheduling/Trash Verbs:** Words for trash/tasks (`basura`, `tareas`) and related verbs (`vaciar`, `cancela`, `borra`) are not captured, causing them to fall back to default tools (`system_health`, `get_datetime`, `calculator`).

## Recommended Hardening Patches for NanoHat runtime
To support this persona without switching from the deterministic router to an LLM-based router (which would increase latency and context dilution), we recommend expanding the regex clusters in `runtime/router.py`:
1.  **Enhance Service Action Regex:** Expand `RE_SERVICE_ACTION` and `RE_SERVICE_EXPLICIT` to include common Hinglish/Spanish terms (e.g., `chalu`, `chal raha`, `estado`, `reinicia`, `servicio`).
2.  **Broaden Memory Intent Words:** Add words like `yaad`, `bhool`, `naam`, `favorito`, `quien`, `soy`, `borra` to `RE_MEMORY_WORDS` and related memory regexes.
3.  **Include Multilingual Task/Trash terms:** Add `tarea`, `basura`, `vaciar`, `cancela` to the `RE_TASK` and `RE_TRASH` regexes.
4.  **Fallback Mechanism Tuning:** If no tool matches, consider identifying non-English languages to provide a generic LLM prompt instructing the model to translate and re-route, or keep the expanded regex strategy as the primary fix to maintain sub-second latency.