---
type: dashboard
title: "NanoHat OS Agent — Obsidian Vault"
tags: [project/index, dashboard]
updated: 2026-09-20
---

# 🎩 NanoHat OS Agent — Obsidian Knowledge Vault

Welcome to the internal engineering vault for **NanoHat**, an autonomous sub-1B Linux OS agent. This vault tracks all milestones, task specifications, commits, pull requests, and architectural decisions.

---

## 🗺️ Project Evolution & Milestones

| Milestone | Status | Branch | Spec Link | Core Focus |
|:---|:---|:---|:---|:---|
| **v1 Foundation** | `#task/done` | `main` | [[2026-08-15-v1-foundation\|v1 Foundation]] | SmolLM2-360M Instruct setup, `smolagents` prototype, initial 6 tools |
| **v2 Desktop Engine** | `#task/done` | `main` | [[2026-08-28-v2-desktop-engine\|v2 Desktop Engine]] | Native Fedora runtime, curriculum synthetic data, Unsloth LoRA training |
| **v2.1 CLI Packaging** | `#task/done` | `main` | [[2026-09-12-v2.1-cli-packaging\|v2.1 CLI Packaging]] | `nanohat <query>` entrypoint, AST calculator, fail-closed gates (PR #12) |
| **v3 FunctionGemma** | `#task/done` | `v3-dev` | [[2026-09-14-v3-functiongemma-harness\|v3 FunctionGemma]] | Sub-300M native hardware tokens, 6-module architecture, zero bloat |
| **Master Specification** | `#spec/canonical` | `v3-dev` | [[NANOHAT_MASTER_SPECIFICATION\|Master System Specification]] | Definitive 5-pillar charter, ToolGrad distillation, & audit protocol |
| **v3.0.0 Lean Scope** | `#task/done` | `v3-dev` | [[2026-09-14-v3.0.0-frozen-17-tools-scope\|v3.0.0 Lean Scope]] | 100% offline, deterministic core, Batches 1, 2, 3 complete |
| **v3 Batch 4 SQLite State** | `#task/done` | `v3-dev` | [[2026-09-15-v3-batch4-sqlite-wal-state\|Batch 4 SQLite State]] | Concurrency-safe WAL state.db, memory_* (4 units), task_* (3 units) |
| **v3.0.0 Release & PR** | `#task/wip` | `v3-dev` | [[2026-09-20-v3.0.0-release-and-pr\|v3.0.0 Release & PR]] | Sub-300M zero-shot OS agent with intent tool routing, PR and release runbook |

---

## 🏛️ Architectural Decision Records (ADRs)

| ADR | Status | Date | Decision |
|:---|:---|:---|:---|
| [[ADR-001-AST-Calculator-Security\|ADR-001]] | `#adr/accepted` | 2026-09-12 | AST expression evaluation replacing `eval()` for arbitrary code protection |
| [[ADR-002-Fail-Closed-Confirmation-Gates\|ADR-002]] | `#adr/accepted` | 2026-09-12 | Fail-closed security gating on destructive bash/file modifications |
| [[ADR-003-V3-FunctionGemma-Pivot\|ADR-003]] | `#adr/accepted` | 2026-09-13 | Pivot to FunctionGemma 270M native control tokens after Base FFT capacity collapse |
| [[ADR-004-Sub-300M-Tool-Induction-and-Few-Shot\|ADR-004]] | `#adr/accepted` | 2026-09-14 | In-context balanced exemplars for sub-300M tool induction & how-to search routing |
| [[ADR-005-Offline-First-Frozen-17-Scope\|ADR-005]] | `#adr/accepted` | 2026-09-14 | Offline-first architecture and 17 frozen OS functionalities for v3.0.0 release |
| [[ADR-006-Sub-1B-Dynamic-Tool-Gating-and-Dynamic-Prompts\|ADR-006]] | `#adr/accepted` | 2026-09-15 | Deterministic intent router and dynamic system prompt assembly resolving 270M context wall |
| [[ADR-007-Lean-Scope-Exclusion-of-Desktop-Session-and-Process-Killing\|ADR-007]] | `#adr/accepted` | 2026-09-15 | Lean scope exclusion of desktop session and process killing tools to maximize reliability |

---

## 🧪 Quality Assurance & Test Matrices

| Document | Status | Scope | Description |
|:---|:---|:---|:---|
| [[testing/2026-09-15-v3.0.0-manual-test-matrix\|v3.0.0 Manual Test Matrix]] | `#testing/active` | 60 Test Cases | Exhaustive manual verification checklist across all 16 tools, typos, slang, and ADR-007 safety boundaries |

---

## ⚡ Quick Architecture Overview

```text
NanoHat Runtime (v3-dev)
├── runtime/
│   ├── functions.py    # Pure Python execution (AST calculator, psutil health)
│   ├── tools.py        # OpenAI/Ollama compliant tool JSON schemas
│   ├── prompts.py      # Versioned steering system prompts (v1, v2)
│   ├── client.py       # Zero-dependency urllib Ollama API chat client
│   ├── engine.py       # Agent dispatch loop with step-by-step color logger
│   └── main.py         # CLI entrypoint with flag parser
└── .notes/             # Obsidian knowledge vault (ignored in git)
```
