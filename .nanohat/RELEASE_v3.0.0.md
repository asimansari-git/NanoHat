# 🎩 NanoHat v3.0.0: The Sub-300M Zero-Shot OS Agent

> *"Fine-tuning is the last resort. First, try all methods of systems engineering."*

We are proud to announce **NanoHat v3.0.0**—an ultra-lightweight, offline-first autonomous OS agent that runs locally with sub-second CPU latency and a **~600MB RAM footprint**.

NanoHat v3.0.0 is officially live on [PyPI](https://pypi.org/project/nanohat/3.0.0/)!

---

### The Core Breakthrough: Intent Routing vs. Context Dilution

When building sub-1B parameter agents, the fundamental failure mode is **context dilution**. Exposing a 270M model to 16 complex tool schemas simultaneously saturates its attention window, causing hallucinations, schema confusion, and syntax breakdowns.

In v3.0.0, we bypassed brute-force fine-tuning and solved this through **clean systems architecture**:

1. **Stock FunctionGemma 270M:** Uses native tool-calling control tokens directly out-of-the-box without requiring custom model weights.
2. **Deterministic Intent Router (`runtime/router.py`):** A pre-compiled regex classifier dynamically prunes the 16-tool catalog down to **1–4 candidate tools** per turn based on user intent.
3. **Dynamic Prompt Assembly (`runtime/prompts.py`):** Injects steering instructions *only* for the active tool subset, keeping prompt overhead under 120 tokens.
4. **Deterministic OS Execution (`runtime/functions.py`):** 16 pure Python OS functions covering system telemetry, systemd daemons, power profiles, Wi-Fi/Bluetooth, persistent memory, and task scheduling.
5. **Concurrency-Safe SQLite State (`runtime/db.py`):** Thread-safe SQLite engine running in WAL mode at `~/.local/state/nanohat/state.db`.

---

### Installation & Quickstart

#### 1. Pull FunctionGemma via Ollama
```bash
ollama pull functiongemma
```

#### 2. Install NanoHat Globally via Pipx / Pip
```bash
pipx install nanohat
```
*(Or install in any virtual environment via `pip install nanohat`)*

#### 3. Run One-Shot OS Queries
```bash
# System Telemetry & Power
nanohat "What is my current RAM and CPU usage?"
nanohat "Check battery status"

# Hardware & Daemons
nanohat "Turn off wifi"
nanohat "Status of pipewire"
nanohat "Restart ollama"

# Persistent User Memory
nanohat "Remember my favorite editor is neovim"
nanohat "What is my editor?"

# Task Scheduling & Reminders
nanohat "Remind me for coffee in 10 minutes"
nanohat "List my pending tasks"

# Utilities & Math
nanohat "What time is it right now?"
nanohat "What is 1024 * 768 / 16?"
nanohat "Empty trash"
```

---

### Canonical Tool Surface (16 Tools across 5 Pillars)

- **Telemetry & Power:** `system_health`, `power_profile`
- **Hardware & Radios:** `toggle_wifi`, `toggle_bluetooth`
- **Services & Daemons:** `service_status`, `restart_service`
- **Persistent Memory:** `memory_set`, `memory_get`, `memory_list`, `memory_delete`
- **Scheduling & Utilities:** `task_add`, `task_list`, `task_cancel`, `get_datetime`, `calculator`, `empty_trash`

---

### Security & Privacy Principles

- **100% Offline & Private:** Zero external network calls, zero telemetry, zero cloud API bills. Runs completely on your localhost Ollama instance.
- **AST Math Evaluation:** Math expressions are parsed into Python Abstract Syntax Trees with whitelist-only operators (no `eval()` vulnerabilities).
- **Fail-Closed Confirmation Gates:** Destructive operations (`empty_trash`) require interactive TTY confirmation.
- **License:** Apache License, Version 2.0.
