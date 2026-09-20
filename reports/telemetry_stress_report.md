# Telemetry Stress Report
## Persona Profile & Test Vector
- **Persona:** Telemetry Spammer / High-Frequency Monitor
- **Behavior:** Hits `system_health` continuously with all supported and unsupported metrics. Simulates extreme hardware states (no battery, 100% CPU).
- **Test Vector:** Parametrized test matrix using `unittest.mock` to mock `psutil` sensor returns and raise exceptions. Included 35+ test cases covering varying inputs and system conditions.

## Executive Summary
- **Total Queries:** 36 cases tested in unit test suite.
- **Pass Rate:** 100% (All cases successfully matched expected substring handling).
- **Sensor Robustness:** 100% in terms of not crashing. The function gracefully falls back to the "all" default format when unsupported metrics (like 'gpu' or 'fan') are queried or invalid battery objects are returned. Exception handling covers underlying `psutil` errors securely without taking down the application.

## Detailed Case Matrix
| Metric | Simulated State | Returned Schema | Pass/Fail |
|--------|-----------------|-----------------|-----------|
| `all`  | Normal | `CPU: X% \| RAM: Y GB... \| Battery: Z%...` | Pass |
| `cpu`  | 0.0% CPU | `CPU: 0.0%` | Pass |
| `cpu`  | 100.0% CPU | `CPU: 100.0%` | Pass |
| `cpu`  | 105.0% CPU (Spike) | `CPU: 105.0%` | Pass |
| `ram`  | Normal RAM | `RAM: XGB / YGB (Z%)` | Pass |
| `battery` | Normal Battery | `Battery: X% (charging/discharging)` | Pass |
| `battery` | No Battery Detected | `Battery: No battery detected` | Pass |
| `gpu` (invalid) | Normal | Defaults to `all` string | Pass |
| `fan` (invalid) | Normal | Defaults to `all` string | Pass |
| `network` (invalid) | Normal | Defaults to `all` string | Pass |
| `voltage` (invalid) | Normal | Defaults to `all` string | Pass |
| `all` | `psutil` Exception | `Error querying system health: ...` | Pass |

## Critical Edge Cases Discovered
1. **Fallback Behavior on Unsupported Metrics:**
   When an unknown metric string (e.g. `gpu`, `fan`, `network`, `voltage`, `unknown_metric_123`, `None`, `""`) is provided, the function does not error out or reject it. Instead, it falls through to the `else:` condition and behaves exactly like querying `all`. While safe, this could mask invalid API requests in production.
2. **CPU Metrics Out of Bounds:**
   `psutil` can theoretically return CPU percent > 100 (e.g., when accumulated over cores), and the function returns exactly what `psutil` produces (`105.0%` etc.).
3. **Hardware Missing (No Battery):**
   When `sensors_battery()` returns `None` (as on desktop or VM machines without battery), the tool gracefully handles it by formatting `No battery detected`.

## Recommended Hardening Patches for NanoHat runtime
1. **Strict Input Validation:** Modify `system_health` to validate the `metric` parameter against an allowed set (e.g. `['all', 'cpu', 'ram', 'memory', 'battery']`). If an unsupported metric is passed, return a standard "Invalid metric requested" error rather than defaulting to `all`.
2. **CPU Bounding (Optional):** If consumers of this function strictly expect a `[0, 100]` bound, explicitly bound `psutil.cpu_percent` or document that it can exceed 100 on multi-core environments based on the interval used.
3. **Interval Tweaking:** `interval=0.1` inside `psutil.cpu_percent` may result in unreliable short-term CPU readings and cause a slight blocking overhead of 0.1 seconds per request, which can be amplified under a telemetry spamming scenario. Consider `interval=None` (checking since last call) if high frequency is expected.
