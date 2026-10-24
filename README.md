# NanoHat: Linux Fedora OS Agent

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23618506.svg)](https://doi.org/10.5281/zenodo.23618506)

> *"Local-first, on-demand system control with zero cloud dependencies and verifiable safety."*

**NanoHat** is an ultra-lightweight, private, offline Linux system control agent and CLI harness purpose-built for Fedora Workstation. Powered by the fine-tuned **[NanoHat-0.6B](https://huggingface.co/blackpirates/nanohat-qwen3-0.6b-final)** model (built on `Qwen/Qwen3-0.6B`) and a direct-dispatch Python runtime, NanoHat translates on-demand natural language instructions into structured Linux system calls when prompted by the user.

When invoked from your terminal, it diagnoses hardware telemetry, switches energy profiles, toggles wireless radios, controls audio and desktop themes, audits disk storage, checks packages, and inspects systemd services—running locally on your hardware at sub-second latencies with zero external network requests.

* **Research Paper (Preprint):** [10.5281/zenodo.23618506](https://doi.org/10.5281/zenodo.23618506)
* **Ollama Model Registry:** [`asimansari-o/nanohat`](https://ollama.com/asimansari-o/nanohat)
* **Hugging Face Weights:** [`blackpirates/nanohat-qwen3-0.6b-final`](https://huggingface.co/blackpirates/nanohat-qwen3-0.6b-final)

---

## ⚡ What's New in v4.0 & v4.1

* **Upgraded `Qwen3-0.6B` Tool-Calling Engine:** Upgraded from FunctionGemma-270M to `Qwen/Qwen3-0.6B`, specialized for single-tool and multi-tool Linux system calls and strict read-only vs. state-mutating parameter selection.
* **Expanded 10-Tool Direct-Dispatch Catalog:** Added storage audits (`disk_usage`), package inspection (`package_manager`), audio sink control (`audio_control`), and GNOME theme switching (`desktop_appearance`).
* **Preserved Foundation Reasoning:** High accuracy on arithmetic and general Linux conceptual questions alongside system tool calling.
* **Zero Heuristic Crutches:** Completely purged legacy keyword/regex inspection from the runtime harness; the model drives 100% of tool selection and argument generation natively.
* **Instant Pre-Flight Diagnostics:** Auto-detects local Ollama daemon status and provides interactive 1-click model onboarding.

---

## 📊 Benchmark Highlights (Unseen 299-Query Evaluation)

Evaluated against **299 unseen test queries** (239 system tool tasks + 60 conversational, arithmetic, and security refusal queries) under live Fedora hardware execution (`NANOHAT_SANDBOX=1`):

| Evaluation Metric | Base Qwen3-0.6B (`think=OFF`) | Base Qwen3-0.6B (`think=ON`) | NanoHat v4.0 (`think=OFF`) | NanoHat v4.0 (`think=ON`) | NanoHat v4.1 (`think=OFF`) | NanoHat v4.1 (`think=ON`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Exact Tool Match Rate (239 Tool Queries)** | 66.95% | 76.99% | 90.38% | 77.82% | 92.47% | **92.89%** |
| **Canonical Argument Match (239 Tool Queries)** | 51.05% | 65.27% | 86.19% | 71.13% | 87.03% | **88.28%** |
| **Strict Argument Match (239 Tool Queries)** | 41.84% | 58.58% | **85.36%** | 69.04% | 83.68% | 83.68% |
| **Single-Tool Execution Rate (209 Queries)** | 73.68% | 82.78% | **97.61%** | 82.78% | **97.61%** | **97.61%** |
| **Multi-Tool Chain Exact Match (30 Queries)** | 20.00% | 36.67% | 40.00% | 43.33% | 56.67% | **60.00%** |
| **Sandbox Execution Safety Pass (239 Queries)** | 73.64% | 86.19% | 99.58% | 94.14% | **100.0%** | **100.0%** |
| **Destructive Security Refusal Pass (20 Queries)** | **100.0%** | **100.0%** | 90.00% | 90.00% | 60.00% | 60.00% |
| **Pure Arithmetic Accuracy (10 Queries)** | 70.00% | **100.0%** | **100.0%** | **100.0%** | 60.00% | 70.00% |
| **Non-Tool Clean Rate — Zero Hallucination (60 Queries)** | **100.0%** | **100.0%** | 96.67% | 96.67% | 83.33% | 83.33% |
| **Spurious Tool Hallucination Rate (Lower is Better)** | **0.00%** | **0.00%** | 3.33% | 3.33% | 16.67% | 16.67% |
| **Duplicate Tool Call Rate (Lower is Better)** | 0.84% | 1.26% | 1.67% | 1.67% | 0.42% | **0.00%** |
| **True Read-Only Violations — Mutated on Status (Lower is Better)** | 12.61% | 4.20% | 3.36% | 5.88% | **2.52%** | **2.52%** |
| **Overall Combined Intent Match (299 Queries)** | 73.58% | 81.61% | **91.64%** | 81.61% | 90.64% | 90.97% |
| **Median Latency — P50 (Lower is Better)** | **580 ms** | 1461 ms | 672 ms | 2043 ms | 607 ms | 636 ms |

> ⚠️ **Note on `v4.1` vs. Default `v4.0` (`nanohat:latest`):**  
> While `v4.1` (`asimansari-o/nanohat:v4.1`) achieves lower P50 latency (607 ms) and higher multi-tool chain execution (56.67% vs 40.00%), **`v4.0` remains the default model for the NanoHat harness** (`asimansari-o/nanohat:latest`). On security and non-tool benchmarks, `v4.1` failed to score equal or higher than `v4.0` (60.0% vs 90.0% on destructive refusals and 83.33% vs 96.67% on non-tool clean rate). `v4.1.1` is actively being curated to resolve these regressions before updating the default tag.

---

## 🛠️ Hardened 10-Tool Core Catalog

| Canonical Tool Signature | Parameter Scope | OS Backend / Mechanism |
| :--- | :--- | :--- |
| `system_health(metric)` | Query CPU %, RAM usage, or battery charge (`metric`: `"battery" \| "ram" \| "cpu" \| "all"`) | `psutil` (`sensors_battery`, `virtual_memory`, `cpu_percent`) & `/sys/class/thermal` (`coretemp`/`k10temp`) |
| `power_profile(action, profile)` | Inspect or switch energy profiles (`action`: `"get" \| "set"`, `profile`: `"power-saver" \| "balanced" \| "performance"`) | `powerprofilesctl get` / `set` |
| `toggle_wifi(state)` | Check Wi-Fi state or toggle adapter power (`state`: `"status" \| "on" \| "off" \| "toggle"`) | `nmcli radio wifi` |
| `toggle_bluetooth(state)` | Check Bluetooth power or toggle adapter state (`state`: `"status" \| "on" \| "off" \| "toggle"`) | `bluetoothctl show` / `power <on\|off>` |
| `service_status(service_name)` | Inspect systemd unit states across user and system scopes (`service_name`: string) | `systemctl --user is-active` & `systemctl is-active` |
| `restart_service(service_name)` | Restart allowlisted user-space daemons with Wayland crash protection | `systemctl --user restart <service_name>` |
| `disk_usage(path)` | Inspect mounted filesystem storage and percentage full (`path`: e.g. `"/"`, `"/home"`) | Python `shutil.disk_usage(path)` |
| `package_manager(action, package_name, provider)` | Search repo metadata, check installation, or show install command (`action`: `"search" \| "is_installed" \| "install_cmd"`, `provider`: `"dnf" \| "flatpak"`) | `dnf search`, `rpm -q`, `flatpak search` / `info` |
| `audio_control(action, level)` | Inspect or adjust default audio sink volume and mute state (`action`: `"status" \| "mute" \| "unmute" \| "set_volume"`, `level`: `0–100`) | PipeWire WirePlumber `wpctl` (`@DEFAULT_AUDIO_SINK@`) |
| `desktop_appearance(setting, value)` | Switch GNOME color-scheme or Night Light (`setting`: `"theme" \| "night_light"`, `value`: `"status" \| "dark" \| "light" \| "on" \| "off"`) | `gsettings` (`org.gnome.desktop.interface` & `plugins.color`) |

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

## 🔒 Security & Runtime Guardrails

* **Zero Shell Injection:** Executes OS binaries exclusively via Python `subprocess.run([...], shell=False)` argument lists—never `bash -c` or `eval()`.
* **Read-Only Status Separation:** Informational inquiries (*"Is Wi-Fi on?"*, *"What power profile is active?"*) use strictly non-mutating parameters (`status`, `get`) rather than altering system state.
* **Wayland Crash Shield:** Critical desktop components (`gnome-shell`, `gdm`, `wayland`) are rejected inside `restart_service` to prevent session termination.
* **Allowlisted Daemon Recovery:** Service restarts are restricted strictly to safe user-space services (`pipewire`, `pipewire-pulse`, `wireplumber`, `xdg-desktop-portal`, `xdg-desktop-portal-gnome`, `ollama`).
* **Dry-Run Sandbox:** Run with `--sandbox` (`NANOHAT_SANDBOX=1`) to perform live hardware reads while safely simulating any state-mutating actions.
* **100% Offline Privacy:** Executes entirely on `http://127.0.0.1:11434` with zero telemetry, zero analytics, and zero external network access.

---

## 📜 Citation

If you use NanoHat or the NanoHat-0.6B models in your research, please cite our preprint:

```bibtex
@article{ansari2026nanohat,
  title={NanoHat: Polarity-Safe Reinforcement Fine-Tuning and Execution-Grounded Alignment for Sub-1B Local Linux OS Agents},
  author={Ansari, Asim},
  year={2026},
  journal={Zenodo Preprint},
  doi={10.5281/zenodo.23618506},
  url={https://doi.org/10.5281/zenodo.23618506}
}
```

```text
Ansari, A. (2026). NanoHat: Polarity-Safe Reinforcement Fine-Tuning and Execution-Grounded Alignment for Sub-1B Local Linux OS Agents (Version 1.0.0). Zenodo. https://doi.org/10.5281/zenodo.23618506
```

---

## 📄 License
Licensed under the [Apache License, Version 2.0](LICENSE).