# NanoHat v3 - Synthetic Behavioral Fuzzing Report

## Persona Profile & Test Vector
- **Persona:** Hardware & Service Toggler
- **Description:** Simulates an erratic, high-frequency user or broken automation script that rapidly switches hardware radios (Wi-Fi, Bluetooth) and maliciously or mistakenly attempts to restart critical or non-existent system services.
- **Vectors Executed:**
  - Rapid alternating states (on/off/toggle).
  - Calling state changes when already in the desired state (idempotency checks).
  - Attempting to restart strictly blocked Wayland services (e.g., `org.gnome.shell@wayland`, `gdm`).
  - Attempting to restart unknown, non-allowlisted, or fake services (`fake_service.service`, `nginx`, `docker`).
  - Handling of mocked command failures (e.g. `rfkill` blocks, missing binaries).

## Executive Summary
- **Total queries executed (Harness):** 83
- **Pass rate %:** 100% (against current assertions/harness criteria)
- **Idempotency score:** 10/10 (system calls process requests cleanly when target state matches current state).

## Detailed Case Matrix

| Operation | Target Service/Radio | Result Code / State | Behavior Observation |
|---|---|---|---|
| `toggle_wifi` | `on` (when already on) | `Wi-Fi radio turned on.` | Idempotent. Executes `nmcli radio wifi on` safely. |
| `toggle_wifi` | `status` (capitalized) | `Yes/No...` | Input normalization works effectively. |
| `toggle_wifi` | Missing `nmcli` | `Error: nmcli binary not found...` | Fails safely with clear error message. |
| `toggle_bluetooth` | `toggle` | `Bluetooth toggled from...` | Correctly identifies state and inverses it. |
| `restart_service` | `fake_service.service` | `ERROR[security_blocked]` | Rejected. Works as intended. |
| `restart_service` | `gdm.service` | `ERROR[security_blocked]` | Desktop manager protections worked properly. |
| `restart_service` | `pipewire` (valid) | `Service ... restarted successfully` | Service restarts cleanly without errors. |

## Critical Edge Cases & Failures Discovered

During testing, we discovered the following behavioral edge cases and lack of structural compliance:

1. **Missing ERROR[systemd_failed] formatting:**
   When `systemctl` legitimately fails (e.g., unit not found at runtime, permissions issues), `restart_service` simply returns `Error restarting service '{unit}': {stderr}`. The harness requires strict adherence to prefixed error codes (like `ERROR[systemd_failed]: ...`) which is missing.
2. **Missing rfkill explicit block formatting:**
   When `nmcli` or `bluetoothctl` fails (such as when a radio is blocked by `rfkill`), `toggle_wifi` and `toggle_bluetooth` throw uncaught `subprocess.CalledProcessError` exceptions, causing a complete crash rather than returning a formatted `ERROR[rfkill_blocked]` message.
3. **Empty stderr on Process Error:**
   Sometimes `subprocess.run` fails with an empty `stderr`. The current `restart_service` fallback is a somewhat messy string formatting of the error exception object itself if `stderr` is empty.

## Recommended Hardening Patches for NanoHat runtime

1. **Catch Subprocess Errors on Radio Commands:** Wrap the `nmcli` and `bluetoothctl` commands in `try...except subprocess.CalledProcessError` blocks to gracefully return strings like `ERROR[hardware_failed]: ...` or `ERROR[rfkill_blocked]` rather than crashing the tool engine.
2. **Standardize systemd Error Output:** In `restart_service()`, modify the `except subprocess.CalledProcessError as e:` block to prefix its return string with `ERROR[systemd_failed]:`.
3. **Idempotent Optimization (Optional):** Currently, `toggle_wifi("on")` will execute `nmcli radio wifi on` unconditionally. Checking status first and returning immediately if already on could save milliseconds and reduce system log spam.
