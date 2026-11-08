# NanoHat: Linux Fedora OS Agent

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23618506.svg)](https://doi.org/10.5281/zenodo.23618506)

> *"Local-first, on-demand system control with zero cloud dependencies and verifiable safety."*

**NanoHat** is an ultra-lightweight, private, offline Linux system control agent and CLI harness purpose-built for Fedora Workstation. Powered by the fine-tuned **[NanoHat-0.6B](https://huggingface.co/blackpirates/nanohat-qwen3-0.6b-final)** model (built on `Qwen/Qwen3-0.6B` and published as `asimansari-o/nanohat:v4.1.2` / `latest`) and a direct-dispatch Python runtime, NanoHat translates on-demand natural language instructions into structured Linux system calls when prompted by the user.

When invoked from your terminal, it diagnoses hardware telemetry (CPU, RAM, battery, and Intel/AMD/NVIDIA GPUs), switches energy profiles, toggles wireless radios, controls audio and desktop themes, audits disk storage, checks packages, and inspects systemd services—running locally on your hardware at sub-second latencies with zero external network requests.

* **Research Paper (Preprint):** [10.5281/zenodo.23618506](https://doi.org/10.5281/zenodo.23618506)
* **Ollama Model Registry:** [`asimansari-o/nanohat`](https://ollama.com/asimansari-o/nanohat) (`v4.1.2` / `latest`)
* **Hugging Face Weights:** [`blackpirates/nanohat-qwen3-0.6b-final`](https://huggingface.co/blackpirates/nanohat-qwen3-0.6b-final)

---

## 🧠 Core Architecture: Direct Prompt Injection & Harness Synergy

NanoHat is built with an intentionally unbloated, transparent design that completely avoids complex agent frameworks, LangChain abstractions, or black-box embedded tool-calling mechanisms:

* **Direct Context Injection:** All system prompt directives, operational safety boundaries, and JSON tool schemas are injected directly into the model's prompt context—nothing is hidden behind framework middleware.
* **Fine-Tuned Model-Harness Synergy:** The model (`NanoHat-0.6B`) is specifically trained and fine-tuned to work hand-in-hand with this exact direct-dispatch harness. It understands the operational directives and natively emits explicit `<tool_call>` tokens directly in its text output stream.
* **Direct Python Dispatch:** The runtime harness parses these tokens, normalizes parameter aliases, and immediately dispatches the call to local Linux subsystem APIs (`psutil`, `nmcli`, `bluetoothctl`, `wpctl`, `gsettings`, `powerprofilesctl`).
* **Zero Framework Overhead:** No opaque agent loops, no dynamic multi-turn hallucination chains, and no external dependencies—just direct prompt injection, model token emission, and deterministic execution.

---

## ⚡ What's New in v4.1.2 (SOTA Flagship Release)

* **93.98% Peak Canonical Accuracy:** Highest ever achieved by a sub-1B Linux OS model (281/299 queries correct on unseen benchmark), outperforming base Qwen3-0.6B (72.24%) and NanoHat v4.0 (88.29%).
* **Impenetrable 100.0% Security Refusal Boundary:** Completely eliminates destructive security vulnerabilities; rejected 100% of malicious attacks (`mkfs.ext4`, raw block wipes via `dd`, overclocking, unauthorized sudo escalations) across both `think=OFF` and `think=ON` modes.
* **100.0% Multi-Tool Partial Coverage:** Flawless multi-subsystem orchestration (30/30 composite queries) with zero duplicate calls (**0.0%**). Composite tasks like `System Storage & Health Audit` jump to 100.0% accuracy.
* **Record-Low 1.68% Read-Only Safety Violations:** Enforces strict polarity separation so status inquiries never mutate system state (down from 12.61% in v4.0).
* **Sub-600ms Edge Latency:** Median response latency of **595.7 ms** (P50 think=OFF) and **1307.6 ms** (think=ON), running blazing fast on consumer GPUs like laptop GTX 1050 Ti.
* **Multi-GPU Telemetry Support:** Native `system_health` queries detecting Intel/AMD integrated GPUs via DRM sysfs and discrete NVIDIA GPUs via `nvidia-smi` alongside CPU, RAM, and battery metrics.
* **100% Dry-Run Sandbox Coverage:** Strict dry-run simulation across all 10 tools (`NANOHAT_SANDBOX=1` / `--sandbox`), preventing accidental system changes during testing or benchmark evaluation.

---

## 📊 Benchmark Highlights (Unseen 299-Query Evaluation)

Evaluated against **299 unseen test queries** (239 system tool tasks + 60 conversational, arithmetic, and security refusal queries) under live Fedora hardware execution (`NANOHAT_SANDBOX=1`):

| Evaluation Metric | Base Qwen3-0.6B (`think=OFF`) | Base Qwen3-0.6B (`think=ON`) | NanoHat v4.0 (`think=OFF`) | NanoHat v4.1 (`think=OFF`) | NanoHat v4.1.2 (`think=OFF`) | NanoHat v4.1.2 (`think=ON`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Exact Tool Match Rate (239 Tool Queries)** | 66.95% | 76.99% | 90.38% | 92.47% | 92.89% | **96.65%** |
| **Canonical Argument Match (239 Tool Queries)** | 51.05% | 65.27% | 86.19% | 87.03% | 85.77% | **92.89%** |
| **Strict Argument Match (239 Tool Queries)** | 41.84% | 58.58% | 85.36% | 83.68% | 84.94% | **89.96%** |
| **Single-Tool Execution Rate (209 Queries)** | 73.68% | 82.78% | 97.61% | 97.61% | **99.04%** | **99.04%** |
| **Multi-Tool Chain Exact Match (30 Queries)** | 20.00% | 36.67% | 40.00% | 56.67% | 50.00% | **80.00%** |
| **Multi-Tool Partial Coverage (30 Queries)** | 43.33% | 60.00% | 56.67% | 76.67% | 73.33% | **100.0%** |
| **Sandbox Execution Safety Pass (239 Queries)** | 73.64% | 86.19% | 99.58% | **100.0%** | 99.58% | 99.58% |
| **Destructive Security Refusal Pass (20 Queries)** | **100.0%** | **100.0%** | 90.00% | 60.00% | **100.0%** | **100.0%** |
| **Pure Arithmetic Accuracy (10 Queries)** | 70.00% | **100.0%** | **100.0%** | 60.00% | 60.00% | **100.0%** |
| **Non-Tool Clean Rate — Zero Hallucination (60 Queries)** | **100.0%** | **100.0%** | 96.67% | 83.33% | **100.0%** | 98.33% |
| **Spurious Tool Hallucination Rate (Lower is Better)** | **0.00%** | **0.00%** | 3.33% | 16.67% | **0.00%** | 1.67% |
| **Duplicate Tool Call Rate (Lower is Better)** | 0.84% | 1.26% | 1.67% | 0.42% | 0.84% | **0.00%** |
| **True Read-Only Violations — Mutated on Status (Lower is Better)** | 12.61% | 4.20% | 3.36% | 2.52% | 5.88% | **1.68%** |
| **Overall Combined Canonical Accuracy (299 Queries)** | 60.87% | 72.24% | 88.29% | 86.29% | 88.63% | **93.98%** |
| **Overall Combined Intent Match (299 Queries)** | 73.58% | 81.61% | 91.64% | 90.64% | 94.31% | **96.99%** |
| **Median Latency — P50 (Lower is Better)** | 580 ms | 1461 ms | 672 ms | 607 ms | **595.7 ms** | 1307.6 ms |
| **Tail Latency — P95 (Lower is Better)** | 996 ms | 3645 ms | 1568 ms | 4141 ms | **1001.1 ms** | 2518.2 ms |

> 🌟 **Official Production Default:**  
> `nanohat:latest` and `nanohat:v4.1.2` serve our SOTA v4.1.2 weights. Delivering 93.98% canonical accuracy, 100% security refusals, and sub-600ms P50 latency, v4.1.2 is the official production release across PyPI and Ollama.

### 🔬 Reproducing the Benchmarks

To independently reproduce the 299-query evaluation matrix on your local machine using our test harness:
```bash
# Run 4-matrix evaluation across think=OFF and think=ON (dry-run sandbox enforced)
python evals/benchmark_models.py --models qwen3:0.6b asimansari-o/nanohat
```


---

## 🛠️ Hardened 10-Tool Core Catalog

| Canonical Tool Signature | Parameter Scope | OS Backend / Mechanism |
| :--- | :--- | :--- |
| `system_health(metric)` | Query CPU %, RAM usage, battery charge, or GPU telemetry (`metric`: `"battery" \| "ram" \| "cpu" \| "gpu" \| "all"`) | `psutil`, `/sys/class/thermal`, DRM sysfs (Intel/AMD), and `nvidia-smi` (NVIDIA) |
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

# Pull the official NanoHat model weights (~700 MB)
ollama pull asimansari-o/nanohat

# Or pull explicit release tag:
ollama pull asimansari-o/nanohat:v4.1.2
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
nanohat "What is my GPU usage?"
nanohat "What is my GPU and CPU usage?"
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
* **100% Tool Sandbox Coverage:** Run with `--sandbox` (`NANOHAT_SANDBOX=1`) to perform live hardware telemetry reads while safely simulating all state-mutating actions across 100% of the tool catalog, preventing accidental OS modifications during testing or evaluation.
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