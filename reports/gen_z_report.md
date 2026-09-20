# 🎩 NanoHat v3.0 - Gen Z / Mobile Native Stress Test Report

## 1. Persona Profile & Test Vector
**Target Persona:** Gen Z / Mobile Native
**Characteristics:**
- Extreme use of slang (e.g., *bruh, rn, no cap, fr fr, deadass*).
- Frequent lack of standard punctuation or capitalization.
- Heavy use of emojis (`💀`, `🗑️`, `⏰`, `🐐`, `😭`).
- Abstract phrasing instead of technical commands (e.g., "wifi acting sus", "cpu goes brrr", "kill the wifi rn", "yeet the trash").

**Testing Focus:**
- **Token Entropy & Fuzzing:** Testing how the sub-word tokenization and deterministic regex intent router handle heavy lexical distortion and noisy text.
- **Intent Extraction Resiliency:** Ensuring NanoHat still maps highly chaotic natural language down to 1-4 canonical system tool schemas.

---

## 2. Executive Summary
- **Total Queries Tested:** 45
- **Passed Intent Routings:** 44
- **Failed Intent Routings:** 1
- **Pass Rate:** **97.8%**
- **Slang Tolerance Rate:** Excellent. The deterministic regex router was exceptionally resilient to slang due to focusing on core keyword anchors while ignoring adjacent slang noise.

---

## 3. Detailed Case Matrix (Subset of Interest)

| Query | Expected Tools | Routed Tools | Result | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `bruh clean my ram rn 💀` | `[system_health]` | `[system_health]` | **PASS** | Correctly anchored on "ram" despite emoji and "bruh/rn". |
| `turn off bt no cap` | `[toggle_bluetooth]` | `[toggle_bluetooth]` | **PASS** | "bt" matched successfully, ignoring "no cap". |
| `yeet the trash 🗑️` | `[empty_trash]` | `[empty_trash]` | **PASS** | "trash" triggered core regex. |
| `yo schedule gym 6pm fr` | `[task_add]` | `[task_add, task_list]` | **PASS** | "schedule" triggered task routing cleanly. |
| `math is hard whats 9 + 10` | `[calculator]` | `[calculator]` | **PASS** | "math" and expressions trigger calculation intent. |
| `call me goat 🐐` | `[memory_set]` | `[memory_set]` | **PASS** | "call me" trigger hits identity set. |
| `list all my notes rn` | `[memory_list]` | `[system_health, get_datetime, calculator]` | **FAIL** | Failed to recognize "notes" due to interference or missing regex coverage. Triggered fallback tools. |
| `is the wifi bussin or nah?` | `[toggle_wifi]` | `[toggle_wifi]` | **PASS** | Slang ignored, core intent extracted. |
| `is bt down? lowkey weird` | `[toggle_bluetooth]` | `[toggle_bluetooth, service_status, restart_service]` | **PASS** | Routed to BT, but also picked up "down?" as a service status query. Still successful because target tool was supplied. |

---

## 4. Critical Edge Cases & Failures Discovered

1. **Failure Case:** `"list all my notes rn"`
   - **Why it failed:** The `RE_MEMORY_WORDS` regex looks for `\b(remem[a-z]*|remeb[a-z]*|recall[a-z]*|forget[a-z]*|memory|memories|preference|preferences|saved\s+note|saved\s+notes)\b`. It explicitly required "saved note(s)", completely missing raw "notes". Thus, the query failed to trigger the `is_mem` check and cascaded down to the default fallback tools.

2. **Partial Collision (BT + Service):** `"is bt down? lowkey weird"`
   - **Analysis:** The word "down" triggered `RE_SERVICE_ACTION` (`re.search(r"\b(running|active|failed|dead|up|down|status)\b", q)`). So it added `service_status` and `restart_service` alongside `toggle_bluetooth`. This is safe (the LLM can figure it out), but slightly inefficient for prompt size.

---

## 5. Recommended Hardening Patches for NanoHat Runtime

1. **Update `runtime/router.py` - `RE_MEMORY_WORDS`:**
   - Change `saved\s+note` and `saved\s+notes` to simply include `note` and `notes`.
   - **Proposed Patch:**
     ```python
     RE_MEMORY_WORDS = re.compile(r"\b(remem[a-z]*|remeb[a-z]*|recall[a-z]*|forget[a-z]*|memory|memories|preference|preferences|note|notes)\b", re.IGNORECASE)
     ```
   - This will fix the `list all my notes rn` query.

2. **Update `runtime/router.py` - `RE_SERVICE_ACTION` / `_is_service_query`:**
   - To prevent "is bt down?" from triggering systemd service checks, consider enforcing that words like `down`, `up`, `dead` are only service queries if not accompanied by hardware keywords (wifi, bluetooth), or tighten the regex.
