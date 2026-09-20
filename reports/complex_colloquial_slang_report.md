# Complex Colloquial Slang, Regional Dialects & Idiomatic Expressions Report

## 1. Persona & Regional Dialect Linguistic Matrix

The NanoHat router was evaluated against a wide range of colloquial terms representing multiple dialects of English to test robustness against natural human utterances.

- **British/Commonwealth**: Evaluated expressions like "dustbin" (trash), "wireless" (wi-fi), "guv'nor" (persona), "rubbish bin", "flat" (battery), and "quid" (money/math).
- **Australian**: Evaluated expressions like "fair dinkum", "chugging", "telly", "interwebs", "juice" (battery), "garbo" (trash), and "brekkie".
- **American**: Evaluated terms like "rig", "thermals", "trash can", "fire up", "lagging", and "boot up".
- **Indian/Subcontinent**: Evaluated terms such as "revert" (reply/status), "wastebasket", "prepone" (reschedule), "doubt", and "do the needful".

## 2. Executive Summary

- **Total Cases**: 40
- **Passed Cases**: 27
- **Failed (Expected Failures)**: 13
- **Pass Rate**: 67.5%

## 3. Detailed Case Matrix

| Region | Query | Expected Tool(s) | Status |
|---|---|---|---|
| British | Fancy emptying the dustbin mate? | `empty_trash` | XFAIL |
| British | Turn off the wireless interface | `toggle_wifi` | XFAIL |
| British | Give us the time guv'nor | `get_datetime` | PASS |
| British | Empty the rubbish bin | `empty_trash` | PASS |
| British | Can you lob this in the bin? | `empty_trash` | PASS |
| British | Me battery's gone flat, innit | `system_health` | PASS |
| British | Oi, crank up the performance profile | `power_profile` | PASS |
| British | Switch on the blue-teeth | `toggle_bluetooth` | XFAIL |
| British | Calculate how much quid I owe: 50 * 4 | `calculator` | PASS |
| British | Chuck this task in me diary: tea at 4 | `task_add` | PASS |
| Australian | Me laptop is fair dinkum chugging, check the telly... I mean CPU | `system_health` | PASS |
| Australian | Chuck this task in my list: grab brekkie tomorrow | `task_add` | PASS |
| Australian | Turn on the interwebs | `toggle_wifi` | XFAIL |
| Australian | Check the juice level | `battery` (mapped to `system_health` internally) | XFAIL |
| Australian | Empty the garbo | `empty_trash` | XFAIL |
| Australian | What's the date today, mate? | `get_datetime` | PASS |
| Australian | Calculate 150 bucks divided by 5 | `calculator` | PASS |
| Australian | My rig's getting warm | `system_health` | PASS |
| Australian | Fire up the browser | `launch_app` | XFAIL |
| Australian | Delete that memory, mate | `memory_delete` | PASS |
| American | Yo my rig is screaming, check the thermals | `system_health` | PASS |
| American | Trash can is overflowing, dump it | `empty_trash` | PASS |
| American | Fire up terminal | `launch_app` | XFAIL |
| American | Check my calendar for today | `get_datetime` | PASS |
| American | Can you do the math: 50 * 2? | `calculator` | PASS |
| American | Kill the lagging app | `restart_service` | XFAIL |
| American | Is my wifi connected? | `toggle_wifi` | PASS |
| American | Remember that I love hamburgers | `memory_set` | PASS |
| American | Boot up firefox | `launch_app` | XFAIL |
| American | Switch to battery saver | `power_profile` | PASS |
| Indian | Kindly revert with the system battery status | `system_health` | PASS |
| Indian | Do one calculation: 450 divided by 3 | `calculator` | PASS |
| Indian | Please clear the wastebasket | `empty_trash` | XFAIL |
| Indian | Turn on the bluetooth device | `toggle_bluetooth` | PASS |
| Indian | What's the date? | `get_datetime` | PASS |
| Indian | My PC is heating up too much | `system_health` | XFAIL |
| Indian | Kindly prepone my scheduled task | `task_list` / `task_add` | PASS |
| Indian | Open the application firefox | `launch_app` | PASS |
| Indian | I have a doubt, what is my IP? | `toggle_wifi` | XFAIL |
| Indian | Please do the needful and restart the server | `restart_service` | PASS |

## 4. Regional Idiom Coverage Gaps & Dialectal Tokenization

Currently, the `runtime.router.route_tools` function uses explicit regular expressions based on exact vocabulary terms. This leads to gaps where regional variations are unrecognized:

- **Waste Management**: "dustbin", "garbo", and "wastebasket" do not match the `RE_TRASH` regex which mainly focuses on "trash", "recycle", and "bin".
- **Network Interfaces**: "wireless" and "interwebs" are missed by the `RE_NETWORK` pattern which looks specifically for "wifi", "network", etc. "blue-teeth" misses the exact "bluetooth" matching.
- **Application Launching**: "fire up" and "boot up" are missing from `RE_LAUNCH_APP` which requires terms like "launch", "open", "start", or "run".
- **Power/Health**: Slang terms like "juice" for battery and phrase constructs like "heating up" are missed by the current `RE_BATTERY_METRICS` and `RE_CPU_RAM` matching arrays.

## 5. Recommended Hardening Patches

To fix the failed assertions, `runtime/router.py` needs to be patched by adding synonymous idioms to the relevant regex pattern checks:

1. **`RE_TRASH`**: Add `dustbin`, `wastebasket`, `garbo`, `rubbish`, and `dump`.
2. **`RE_NETWORK`**: Add `wireless`, `interwebs`, `blue-teeth`, `internet`, and `ip`.
3. **`RE_LAUNCH_APP`**: Add `fire up` and `boot up` to the acceptable actions list.
4. **`RE_BATTERY_METRICS`**: Add `juice` as a synonym for power/battery.
5. **`RE_CPU_RAM`**: Add terms like `heating up`, `lagging`, `frozen`, and `screaming` to cover more descriptive colloquial states of CPU overutilization.
