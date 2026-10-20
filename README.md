# NanoHat: Linux Fedora OS Agent

> *"Local-first system control with zero cloud dependencies and verifiable safety."*

**NanoHat** is an ultra-lightweight, private, offline Linux system agent purpose-built for Fedora Workstation. Powered by the fine-tuned **NanoHat-0.6B** model (refined via Group Relative Policy Optimization on Linux OS operational directives) and an unbloated direct-dispatch Python runtime, NanoHat bridges the gap between colloquial natural language instructions and low-level Linux system calls.

It diagnoses hardware telemetry, adjusts energy profiles, toggles wireless radios, controls audio and desktop appearances, audits disk storage, checks packages, and inspects systemd services—all running locally on your hardware at sub-second latencies with zero external network requests.

---

## ⚡ What's New in v4.0

* **Policy Optimization Alignment (GRPO):** Upgraded from FunctionGemma-270M to Qwen3-0.6B, refined via Group Relative Policy Optimization (GRPO) with order-invariant multi-tool matching and read-only safety invariants.
* **Expanded 10-Tool Catalog:** Added storage audits (`disk_usage`), package inspection (`package_manager`), audio sink control (`audio_control`), and GNOME theme switching (`desktop_appearance`).
* **Preserved Foundation Reasoning:** 100% accuracy on complex arithmetic and general Linux conceptual questions without tool-hallucination regressions.
* **Zero Heuristic Crutches:** Completely purged legacy keyword/regex inspection from the runtime harness; the model drives 100% of tool selection and argument generation natively.
* **Instant Pre-Flight Diagnostics:** Auto-detects local Ollama daemon status and provides interactive 1-click model onboarding.

---

## 📊 Benchmark Highlights (Unseen 299-Query Evaluation)

Evaluated against 299 unseen test queries (239 system tool tasks + 60 conversational, arithmetic, and security refusal queries) under live Fedora hardware execution:

| Evaluation Metric | Base (`think=OFF`) | Base (`think=ON`) | **NanoHat v4 (`think=OFF`)** | **NanoHat v4 (`think=ON`)** |
| :--- | :---: | :---: | :---: | :---: |
| **Overall Intent & Tool Accuracy** | 74.25% | 79.60% | **92.31%** | **95.65%** |
| **Canonical Argument Match** | 63.88% | 69.57% | **88.29%** | **91.30%** |
| **Single-Tool Execution Rate** | 74.16% | 80.38% | **97.61%** | **98.56%** |
| **Multi-Tool Chain Success** | 23.33% | 36.67% | **46.67%** | **70.00%** |
| **Sandbox Execution Safety Pass** | 73.64% | 82.01% | **99.58%** | **98.74%** |
| **Math & General QA Preservation** | 70.00% | 70.00% | **80.00%** | **100.00%** |
| **Duplicate Tool Hallucination Rate** | 0.84% | 0.84% | **0.00%** | **0.42%** |
| **Median Latency (P50 on T4)** | 749 ms | 1667 ms | **682 ms** | **1970 ms** |

> 🔗 *For deep-dive telemetry matrices, per-category breakdowns, and interactive latency curves, visit our official project documentation.*

---

## 🛠️ Hardened 10-Tool Core Catalog

| Tool | Action Scope | Mechanism / Backend |
| :--- | :--- | :--- |
| `system_health` | Query CPU %, RAM usage, or battery charge (`battery`, `ram`, `cpu`, `all`) | `psutil` virtual memory, CPU percent, coretemp, UPower |
| `power_profile` | Inspect or switch energy profiles (`power-saver`, `balanced`, `performance`) | `powerprofilesctl get` / `set` |
| `toggle_wifi` | Check Wi-Fi state or toggle adapter power (`status`, `on`, `off`, `toggle`) | `nmcli radio wifi` |
| `toggle_bluetooth` | Check Bluetooth power or toggle adapter state (`status`, `on`, `off`, `toggle`) | `bluetoothctl show` / `power <state>` |
| `service_status` | Inspect systemd unit states across user and system scopes | `systemctl is-active <unit>` |
| `restart_service` | Restart allowlisted user-space daemons with Wayland crash protection | `systemctl --user restart <unit>.service` |
| `disk_usage` | Inspect mounted filesystem storage and percentage full | `shutil.disk_usage` / `df` |
| `package_manager` | Search repo metadata or verify if RPM/Flatpak packages are installed | `dnf`, `rpm -q`, `flatpak info` |
| `audio_control` | Inspect or adjust default audio sink volume and mute state | `wpctl`, `pactl` |
| `desktop_appearance` | Switch GNOME color-scheme (light/dark) or toggle Night Light | `gsettings` (`org.gnome.desktop.interface`) |

---

## 🚀 Installation & Quickstart

### 1. Prerequisites (Ollama)
Ensure [Ollama](https://ollama.com) is installed and running on your local machine:
```bash
# Install Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the NanoHat model weights (~700 MB)
ollama pull asimansari-o/nanohat
```

### 2. Install NanoHat CLI

#### Via PyPI (Recommended):
```bash
# Using pipx (recommended for isolated global CLI tools)
pipx install nanohat

# Using uv
uv tool install nanohat
# or into active environment: uv pip install nanohat

# Using pip
pip install nanohat
```

#### From Source (Development):
```bash
git clone https://github.com/asimansari-git/NanoHat.git
cd NanoHat
pip install -e .
```

---

## 💡 Usage Examples

Run commands directly from your terminal:

```bash
# Hardware Telemetry & Health Checks
nanohat "What's my battery percentage?"
nanohat "Check CPU load and temperature"
nanohat "Show complete system health"

# Energy Profile Management
nanohat "What is my current power profile?"
nanohat "Switch energy profile to power-saver"

# Wireless Radio Control
nanohat "Is Wi-Fi turned on?"
nanohat "Turn off Bluetooth"

# Service Inspection & Daemon Recovery
nanohat "Is pipewire running?"
nanohat "Restart wireplumber service"

# Storage & Package Audits
nanohat "Check my root disk usage"
nanohat "Is brave-browser installed?"
nanohat "Search for vlc in package repositories"

# Desktop & Audio Control
nanohat "Switch desktop to dark mode"
nanohat "Mute audio volume"

# Complex Cross-Domain Multi-Tool
nanohat "What is my current power profile and what is my CPU usage?"

# General Reasoning & Arithmetic (Zero Tool Dispatches)
nanohat "What is 88 * 7 + 4 - 12 * 72?"
nanohat "What is dnf?"
```

### Verbose Mode
Inspect prompt tokens, parameter normalization, and raw execution details:
```bash
nanohat -v "Check battery charge"
```

---

## 🔒 Security & Read-Only Invariants

* **Read-Only Safety Invariant:** Informational inquiries (*"Is Wi-Fi on?"*, *"What power profile is active?"*) are mathematically rewarded to use strictly non-mutating parameters (`status`, `get`).
* **Wayland Crash Shield:** Critical desktop components (`gnome-shell`, `gdm`, `wayland`) are rejected inside `restart_service` to prevent session termination.
* **Allowlisted Daemon Recovery:** Service restarts are restricted strictly to user-space multimedia and agent utilities (`pipewire`, `wireplumber`, `ollama`).
* **Dry-Run Sandbox:** Run with `--sandbox` (`NANOHAT_SANDBOX=1`) to perform live hardware reads while safely simulating any state-mutating actions.
* **100% Offline Privacy:** Executes entirely on `http://127.0.0.1:11434` with zero telemetry, zero analytics, and zero external network access.

---

## 📜 License
Licensed under the [Apache License, Version 2.0](LICENSE).