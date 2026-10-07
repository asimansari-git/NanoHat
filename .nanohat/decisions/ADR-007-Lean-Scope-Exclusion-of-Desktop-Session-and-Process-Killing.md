---
title: "ADR-007: Lean Scope Exclusion of Desktop Session & Process Killing from v3.0.0"
date: 2026-09-15
status: "#adr/accepted"
tags:
  - adr
  - architecture
  - security
  - scope
related:
  - "[[00_INDEX]]"
  - "[[ADR-005-Offline-First-Frozen-17-Scope]]"
  - "[[NANOHAT_MASTER_SPECIFICATION]]"
---

# ADR-007: Lean Scope Exclusion of Desktop Session & Process Killing from v3.0.0

- **Status:** `#adr/accepted`
- **Date:** 2026-09-15
- **Deciders:** Kaizen & Liz

---

## 🎯 Context & Problem Statement

In the initial draft of the Frozen 17 OS Scope (`ADR-005`), Batch 5 proposed 4 desktop session and app control tools:
1. `take_screenshot` (Wayland `grim` / `gnome-screenshot`)
2. `lock_screen` (`loginctl lock-session`)
3. `launch_app` (`gtk-launch` / `xdg-open`)
4. `kill_process` (`pkill` with confirmation gates)

While theoretically possible, practical evaluation revealed substantial usability and safety friction:
- **Typing Friction**: Typing a verbose prompt to take a screenshot, lock the desktop, or launch an app is vastly slower and less intuitive than native Fedora/GNOME keyboard shortcuts (`PrintScreen`, `Super+L`, or `Super` $\rightarrow$ type app name).
- **Safety & Blast Radius**: Process termination (`kill_process`) carries unacceptable risks of crashing active Wayland sessions, graphical compositors, or dependent developer tooling, even with confirmation gates.
- **Cognitive Budget**: Adding these tools consumes slots in the sub-1B dynamic router without providing high-value OS intelligence.

---

## 💡 Decision

1. **Defer Batch 5**: Formally exclude `take_screenshot`, `lock_screen`, `launch_app`, and `kill_process` from the `v3.0.0` core release.
2. **Preserve Pristine Core**: Freeze `v3.0.0` at **16 rock-solid, zero-friction, offline-first tools** spanning:
   - System Telemetry & Power (`system_health`, `power_profile`)
   - Persistent Memory (`memory_set`, `memory_get`, `memory_list`, `memory_delete`)
   - Scheduled Tasks (`task_add`, `task_list`, `task_cancel`)
   - Hardware Radios & Services (`toggle_wifi`, `toggle_bluetooth`, `service_status`, `restart_service`)
   - Housekeeping & Math (`calculator`, `get_datetime`, `empty_trash`)
3. **Future Roadmap**: Revisit desktop automation in `v3.x.x` as opt-in specialized modules or in `v4.0.0` (Multimodal Vision OS Agent).

---

## ⚖️ Consequences

### Positive
- **Rock-Solid Reliability**: Eliminates risky shell interactions that could kill user desktop processes.
- **Zero Typing Friction**: Focuses NanoHat on tasks where conversational AI delivers genuine speed advantages (complex calculations, state recall, radio toggling, service diagnostics, and natural task scheduling).
- **Faster Release**: Streamlines `v3.0.0` directly toward standalone CLI packaging and background task daemon lifecycle.

### Negative / Trade-offs
- NanoHat v3.0.0 cannot launch GUI apps or capture screenshots from the command line (both of which are natively handled by GNOME shortcuts).
