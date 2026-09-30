---
title: "NanoHat v3: FunctionGemma 270M Native CLI Harness"
date: 2026-09-14
branch: "v3-dev"
status: "in-progress"
tags:
  - task/wip
  - milestone/v3
related:
  - "[[00_INDEX]]"
  - "[[ADR-003-V3-FunctionGemma-Pivot]]"
---

# NanoHat v3: FunctionGemma 270M Native CLI Harness

- **Branch:** `v3-dev`
- **Date:** 2026-09-14
- **Status:** `#task/wip`
- **Vault Index:** `[[00_INDEX]]`
- **Architectural Rationale:** `[[ADR-003-V3-FunctionGemma-Pivot]]`

---

## 🎯 Objective & Problem Statement

### Problem
1. **SmolLM2-360M Capacity Collapse**: Full fine-tuning from Base over 17 tools caused severe schema bleed and memory saturation. See `[[ADR-003-V3-FunctionGemma-Pivot]]`.
2. **Framework Token Overhead**: Text-delimited JSON schemes require large token budgets and fail frequently on sub-300M models.
3. **Hardware-Native Tool Calling**: Google's `google/functiongemma-270m-it` provides native hardware control tokens (`<start_function_call>`, `<start_function_response>`), offering reliable tool calling at a tiny 268M footprint.

### Accepted Solution
- Deploy a 6-module zero-overhead architecture directly in `runtime/`:
  - `runtime/functions.py`: Pure Python tool execution (AST calculator, `psutil` system metrics).
  - `runtime/tools.py`: OpenAI/Ollama compliant tool JSON schemas with strict parameter typing.
  - `runtime/prompts.py`: Versioned system prompt catalog (`v1`, `v2`) for prompt steering benchmarks.
  - `runtime/client.py`: Zero-bloat standard library `urllib` client for Ollama API completions.
  - `runtime/engine.py`: Agent loop managing tool execution, response parsing, and colorized step-by-step logs.
  - `runtime/main.py`: CLI entrypoint supporting `-p/--prompt`, `-v/--version`, and `--verbose`.

### Acceptance Criteria
- [x] `calculator` evaluates arithmetic expressions via safe AST parsing.
- [x] `system_health` reports CPU, RAM, and battery state.
- [x] `web_search` queries DuckDuckGo for live web information.
- [x] Disambiguates arithmetic vs system telemetry vs web search with zero schema bleed.
- [x] Direct responses for out-of-scope non-tool queries without hallucinating tools.
- [x] `--verbose` mode logs invocation parameters, intermediate outputs, and synthesis.
- [ ] Add persistent user memory (`user_memory`) and system actions (`system_action`).

