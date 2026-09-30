---
title: "NanoHat v1 Foundation: SmolLM2-360M Prototype"
date: 2026-08-15
branch: "main"
status: "completed"
tags:
  - task/done
  - milestone/v1
related:
  - "[[00_INDEX]]"
---

# NanoHat v1 Foundation: SmolLM2-360M Prototype

- **Branch:** `main`
- **Date:** 2026-08-15
- **Status:** `#task/done`
- **Vault Index:** `[[00_INDEX]]`

---

## 🎯 Objective & Problem Statement

### Problem
1. **Sub-1B Agent Feasibility**: Can an ultra-lightweight language model (SmolLM2-360M-Instruct) act as an autonomous operating system agent on Fedora Linux?
2. **Context Preservation**: Heavy frameworks consume hundreds of tokens on system prompts and JSON schemas, leaving little context window for a 360M model.

### Accepted Solution
- Utilize Hugging Face `smolagents` with a minimal prompt overhead (~100 tokens).
- Define 6 initial prototype tools: `calculator`, `web_search`, `user_memory`, `scheduler`, `system_health`, and `system_action`.
- Implement `FedoraFormatBridge` to intercept `<thought>` and `<tool_call>` tags emitted by fine-tuned weights.

### Acceptance Criteria
- [x] SmolLM2-360M-Instruct successfully initialized via Ollama / Transformers backend.
- [x] Basic tool execution functional in test scripts.
- [x] Initial dataset recording pipeline established.

---

## 🔨 Historical Implementation & Commits

- Scaffolded initial directory structure (`grounding/`, `generator/`, `validator/`, `runtime/`).
- Built CLI fixtures capture via `grounding/capture_tool_outputs.py`.
- Verified basic agent loop in `runtime/agent.py`.
