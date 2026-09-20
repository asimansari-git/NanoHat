# NanoHat App Launcher Edge Cases Evaluation Report

## Persona Profile & Test Vector
**Persona:** App Launcher & GUI Edge Cases
**Description:** Attempts to launch non-standard, missing, broken, or headless GUI applications via `launch_app`.
**Vectors Tested:**
- Missing binaries
- Missing display/headless environments (e.g., unset `DISPLAY` and `WAYLAND_DISPLAY`)
- Shell injection attempts (e.g., `;`, `&`, `|`, `<`, `>`, quotes, backticks, path traversal)
- Spaces and special characters in app names

## Executive Summary
- **Total queries:** 35 edge cases
- **Pass rate %:** 100%
- **Safe error handling %:** 100%

The `launch_app` capability has been robustly secured to enforce strict allowlists for executable names, avoiding subprocess injection while cleanly handling scenarios involving headless environments and missing application binaries.

## Detailed Case Matrix

| Query | Target App | Expected Code | Actual Code |
| :--- | :--- | :--- | :--- |
| `launch_app("calc")` | calc | Successfully launched | Successfully launched |
| `launch_app("non_existent_game_xyz")` | non_existent_game_xyz | ERROR[missing] | ERROR[missing] |
| `launch_app("app with spaces")` | app with spaces | ERROR[security] | ERROR[security] |
| `launch_app("app\"with'quotes")` | app"with'quotes | ERROR[security] | ERROR[security] |
| `launch_app("bash -c whoami")` | bash -c whoami | ERROR[security] | ERROR[security] |
| `launch_app("../../../bin/sh")` | ../../../bin/sh | ERROR[security] | ERROR[security] |
| `launch_app("/dev/null")` | /dev/null | ERROR[security] | ERROR[security] |
| `launch_app("calc")` (headless) | calc | ERROR[headless] | ERROR[headless] |
| `launch_app("calc")` (wayland) | calc | Successfully launched | Successfully launched |
| `launch_app(None)` | None | ERROR: Invalid | ERROR: Invalid |
| `launch_app("app&")` | app& | ERROR[security] | ERROR[security] |
| `launch_app("app-name_1.2")` | app-name_1.2 | Successfully launched | Successfully launched |

*(Note: Matrix above is an excerpt of all 35 cases evaluated which all passed.)*

## Critical Edge Cases Discovered
1. **Headless Execution Panics:** Attempting to run a GUI app via `subprocess.Popen` without an X11/Wayland display will frequently result in blocked PIPEs or application crashes. **Solution:** Hardcoded fallback checks against `$DISPLAY` and `$WAYLAND_DISPLAY`.
2. **Subprocess Shell Injection:** Direct passing of string arguments to shell runners can easily result in `&` or `;` injections. **Solution:** Passed arguments strictly as an array to `subprocess.Popen` without `shell=True` and added aggressive regex filtering `^[\w\-\.]+$` to block arbitrary paths or flags.
3. **Subprocess Hanging/Zombie Processes:** A child process sharing standard descriptors with the parent could cause the NanoHat agent to hang until the GUI was closed. **Solution:** Rerouted `stdout`/`stderr`/`stdin` to `subprocess.DEVNULL` and invoked `start_new_session=True` to detach the child from the parent's process group.

## Recommended Hardening Patches for NanoHat runtime
- **Implemented:** The `launch_app` method in `runtime/functions.py` has been updated with full security validation against injections, explicit display checks, and subprocess detaching mechanisms.
- **Implemented:** `runtime/tools.py` updated to include `LAUNCH_APP_TOOL` and mapped inside `runtime/router.py` to route user intents effectively.
- **Future Work:** Further integration with `xdg-desktop-portal` or `gtk-launch` could allow native `.desktop` parsing, expanding support beyond simple binary names.
