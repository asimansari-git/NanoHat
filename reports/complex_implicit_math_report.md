# Complex Implicit Math Stress Test Report

## 1. Persona Profile & Natural Word Problem Math Matrix
- **Persona Name:** Average Everyday User (Non-Programmer)
- **Characteristics:** Uses natural language to describe mathematical problems instead of raw operators (e.g., "What is 15% of 120 dollars" rather than "0.15 * 120").
- **Intent Vectors:**
  - Tipping & Percentages (e.g., restaurant bills, tax, discounts)
  - Splitting & Division (e.g., splitting rent, sharing apples)
  - Unit Conversions (e.g., miles to feet, Celsius to Fahrenheit)
  - Arithmetic Sums (e.g., total cost, adding lists of numbers)
  - Time Math (e.g., hours in a week)

## 2. Executive Summary
- **Total Test Cases:** 41
- **Passed:** 34
- **Failed / Expected Failures (XFailed):** 7
- **Pass Rate:** ~83%

The deterministic router successfully identified implicit mathematical intent in the vast majority of natural language queries, gracefully degrading to `calculator` as a fallback or matching it directly via keywords like "calculate" or embedded numbers. However, complex intent overlap with system functions (like RAM usage or services) caused expected failures due to the strict regex precedence in `runtime/router.py`.

## 3. Detailed Case Matrix

| Category | Passed | XFailed | Notes |
| :--- | :--- | :--- | :--- |
| **Tipping & Percentages** | 6 | 1 | "If my restaurant bill is $85..." incorrectly routed to `memory_set` because of the regex `(my\|mah)\s+...is`. |
| **Splitting & Division** | 7 | 0 | Router handled division concepts and implicit math well. |
| **Unit Conversions** | 8 | 0 | Router provided `calculator` successfully (often alongside `get_datetime` or fallbacks). |
| **Arithmetic Sums** | 10 | 0 | Direct sums and subtractions parsed effectively. |
| **Time Math** | 2 | 0 | "Days" and "Hours" queries successfully fell back to the tool catalog which included `calculator` alongside `get_datetime`. |
| **Mixed Intent Math** | 0 | 3 | **XFail**: "RAM", "remind", and "services" math queries get consumed by telemetry/task/service regexes, blocking `calculator`. |
| **Symbolic Algebra** | 0 | 3 | **XFail**: The AST parser `calculator()` intentionally rejects symbolic math (e.g., `2*x + 4 = 10`, `derivative(x**2)`). |
| **AST Limits & Precision** | 6 | 0 | Validated floating point precision (`0.1 + 0.2`), blocked large exponents (`2**2000`), prevented division by zero, and formatted scientific notation (`1e+16`). |

## 4. Implicit Math Keyword Extraction vs Expression Parser Boundaries

The `runtime/router.py` logic relies heavily on two mechanisms for math:
1. `RE_MATH_WORDS`: Explicit words like "calculate", "math", "eval".
2. `RE_MATH_EXPR`: Explicit expressions like `\d+\s*[\+\-\*\/]\s*\d+`.

When users use implicit words like "sum", "split", "percent", or "convert", the router often misses the mathematical intent entirely. Fortunately, the fallback mechanism (`FALLBACK_TOOL_NAMES`) includes `calculator`, which masks this flaw and allows many tests to pass.

However, if an implicit math query contains a stronger keyword from another domain (e.g., "my ... is", "RAM", "remind", "services"), the router aggressively routes to those tools and **omits** `calculator`, causing a failure in intent detection.

Furthermore, the actual execution engine (`runtime/functions.py -> calculator`) uses a strict `ast.parse` approach. It is an *expression evaluator*, not an NLP solver. It cannot solve word problems or symbolic algebra (e.g., `x + y = 5`). If the LLM successfully reformats the word problem into a raw string expression (e.g., `16 - 11.2`), the AST will evaluate it. If the LLM tries to pass the word problem directly to the tool, the AST parser will throw an error.

## 5. Recommended Hardening Patches

1. **Expand `RE_MATH_WORDS`**:
   Add common natural language arithmetic keywords to the regex:
   ```python
   RE_MATH_WORDS = re.compile(r"\b(calculate|calc|math|arithmetic|eval|evaluate|sum|split|divide|multiply|subtract|add|percent|percentage|convert)\b", re.IGNORECASE)
   ```
2. **Prioritize `calculator` in Mixed Intent**:
   If `RE_MATH_WORDS` or `RE_MATH_EXPR` matches, ensure `calculator` is appended to the active tool list *even if* telemetry or memory regexes also match. Currently, pure math skips other checks, but mixed queries can get swallowed.
3. **Refine `RE_MEMORY_SET_STATEMENT`**:
   The memory regex `(my|mah)\s+...is` is too broad and catches queries like "If my restaurant bill is...". Constrain it to avoid matching generic possessive nouns that aren't user preferences.
4. **AST Parser Feedback**:
   Enhance the `calculator` tool description to explicitly warn the LLM: *"Do not pass word problems or variables. You must convert the problem to a raw mathematical expression (e.g., 120 * 0.15) before calling this tool."*