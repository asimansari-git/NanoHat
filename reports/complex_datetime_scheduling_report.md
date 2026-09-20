# Complex DateTime & Ambiguous Scheduling Stress Test Report

## Persona Profile & Temporal Linguistic Matrix
Human users often employ natural language which is inherently ambiguous and deeply contextual. Instead of phrasing intent explicitly (e.g., "Add a task to my schedule for 2024-11-05 at 12:00 PM titled 'Buy Groceries'"), humans naturally condense phrasing into conversational chunks such as:
- **Relative intervals:** "in a fortnight", "half an hour", "Q3", "tomorrow evening".
- **Implicit action boundaries:** "Push my meeting to later" (Implies modify or cancel and add, rather than an explicit "update task").
- **Date Arithmetic references:** "How long ago was yesterday?", "How many days until Christmas?".
- **Omission of task keywords:** "I need to call mom tonight" (Lacks "remind", "task", "schedule", or "todo").

The testing persona emulates these natural variations across tasks like additions, cancellations, list queries, and general temporal state inquiries.

## Executive Summary
- **Total Cases:** 48
- **Passed:** 39
- **Failed / XFailed:** 9 (Expected Failures due to current regex architecture limitations)
- **Pass Rate:** ~81.25%

The deterministic regex router (`runtime/router.py`) handles basic temporal keyword combinations excellently. However, without a semantic NLP model, purely intent-driven phrases lacking explicitly defined triggers (e.g., "remind", "task", "schedule", "alarm") will silently fail to map to task functions. Furthermore, dates formatted specifically (like `YYYY-MM-DD`) often trigger math intent (e.g., `-` as subtraction) inappropriately.

## Detailed Case Matrix
| Type | Query | Expected Tool(s) | Result |
|---|---|---|---|
| Basic Add | "Remind me the day after tomorrow at noon to file taxes" | `task_add` | Pass |
| Implicit Add | "I need to call mom tonight" | `task_add` | XFail |
| Arithmetic | "Add a to-do for 2024-11-05: vote" | `task_add` (not `calculator`) | XFail |
| Implied Cancel | "Cancel my meeting for tomorrow morning" | `task_cancel` | XFail |
| Implicit List | "What's on the docket for the 5th?" | `task_list` | XFail |

*Refer to `tests/stress/test_complex_datetime_scheduling.py` for the complete matrix of the 48 cases.*

## Relative Date Arithmetic & Tokenization Analysis
The deterministic router tokenizes text and attempts substring pattern matching. This approach breaks down under the following conditions:
1. **Math Expression Collision:** As seen in `2024-11-05`, the presence of numbers flanking hyphens incorrectly satisfies the `RE_MATH_EXPR = re.compile(r"\d+\s*[\+\-\*\/]\s*\d+")` token pattern.
2. **Contextual Action Loss:** "meeting" without the word "task" or "schedule" does not trigger routing rules. Similarly "on the docket" means "scheduled items" in English, but the router lacks synonymous breadth.

## Recommended Hardening Patches
1. **Enhance Regex Definitions:**
   - Modify `RE_MATH_EXPR` to ignore standard ISO date string matches (e.g., negative lookbehind/lookahead for month/day lengths).
   - Expand `RE_TASK` to include "meeting", "appointment", "event", and synonyms for to-do items.
2. **Implement LLM-based Fallback / Semantic Router:**
   Instead of purely deterministic matching, utilize a lightweight local embeddings model (or standard LLM call if network is active) to determine intent when regex yields zero or uncertain results.
3. **Date Parser Integration:**
   Integrate an engine like `dateparser` to transform "a fortnight" or "next Monday" into exact offsets before parsing intent, enriching the contextual data available to the LLM.
