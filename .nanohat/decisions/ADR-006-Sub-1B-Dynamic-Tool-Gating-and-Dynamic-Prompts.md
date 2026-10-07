---
title: "ADR-006: Sub-1B Dynamic Tool Gating & Dynamic System Prompt Assembly"
date: 2026-09-15
status: "#adr/accepted"
tags:
  - adr
  - architecture/runtime
  - sub-1b/attention
related:
  - "[[00_INDEX]]"
  - "[[ADR-003-V3-FunctionGemma-Pivot]]"
  - "[[NANOHAT_MASTER_SPECIFICATION]]"
---

# ADR-006: Sub-1B Dynamic Tool Gating & Dynamic System Prompt Assembly

## Context
When scaling NanoHat v3.0.0 from 5 tools (Batches 1 & 2) to 9+ tools (Batch 3), FunctionGemma 270M hit the **Cognitive Context Saturation Wall**:
1. **Attention Diffusion**: 9 dense JSON schemas overwhelmed the model's 268M parameter attention budget (~300MB RAM).
2. **Pre-training Refusal Override**: The Gemma base model's pre-trained RLHF safety prior (*"I cannot assist with querying current date/time..."*) dominated when attention weights were diluted across 9 schemas.
3. **Keyword Collisions**: Overlapping terms like `"status"` in `toggle_bluetooth` and `toggle_wifi` hijacked service inspection queries (`"What ollama status?"` fired `toggle_bluetooth`).
4. **Token Bloat in System Prompt**: Static prompts listing 9+ tool guidelines degraded attention and caused hallucinations of inactive tools.

## Decision
1. **Deterministic Intent Router (`runtime/router.py`)**:
   - Implement zero-overhead (`<0.01s`, `0MB` extra RAM) deterministic token and regex cluster gating in Python.
   - Restrict active tool schemas to strictly $\le 3$ per turn before passing them to FunctionGemma 270M.
   - Use generalized intent patterns (`(is|check|status of|restart)\s+<unit>`) rather than maintaining fragile, hardcoded lists of thousands of Linux units.
2. **Dynamic System Prompt Assembly (`runtime/prompts.py`)**:
   - Decouple tool instructions into modular snippets (`TOOL_SNIPPETS`).
   - Dynamically compile the system prompt per query to include *only* instructions for active tools, reducing prompt token bloat by ~70%.
3. **Schema De-confliction (`runtime/tools.py`)**:
   - Remove ambiguous `"check status"` phrasing from peripheral tools (`toggle_wifi`, `toggle_bluetooth`).
   - Provide explicit multi-term expression hints in `calculator` to prevent term dropping (`7+7*18` $\rightarrow$ `133`).
4. **Scope Fallback in Service Inspection (`runtime/functions.py`)**:
   - `service_status` inspects `--user` session services first, falling back to read-only system scope and daemon suffixes (`tailscale` $\rightarrow$ `tailscaled.service`).
   - `restart_service` strictly remains guarded by the Wayland allowlist shield (`pipewire`, `wireplumber`).

## Consequences & Verification
- **Positive**: 100% routing accuracy restored across all 9 tools. Refusal on date/time queries eliminated. Zero performance overhead.
- **Positive**: 45/45 automated regression tests pass in 17.3s with 100% mocked hardware execution.
- **Trade-off**: Requires maintaining cluster patterns in `runtime/router.py`. In Phase 4, if tool count exceeds 20+, an ultra-light ONNX micro-embedding model can be evaluated as an alternative backend.
