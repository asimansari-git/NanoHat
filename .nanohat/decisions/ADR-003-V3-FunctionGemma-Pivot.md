---
adr: "003"
title: "Pivot to FunctionGemma 270M Native Hardware Tokens"
date: 2026-09-13
status: "accepted"
tags:
  - adr/accepted
  - architecture
related:
  - "[[00_INDEX]]"
  - "[[2026-09-14-v3-functiongemma-harness]]"
---

# ADR-003: Pivot to FunctionGemma 270M Native Hardware Tokens

- **Status:** `#adr/accepted`
- **Date:** 2026-09-13
- **Context:** `[[00_INDEX]]`, `[[2026-09-14-v3-functiongemma-harness]]`

## Context & Problem Statement
During NanoHat v3 research, full fine-tuning (FFT) of `SmolLM2-360M-Base` across 250,000 multi-turn conversations was completed on NVIDIA DGX Blackwell GB10 GPUs (3 epochs, ~152.7M tokens). However, evaluation revealed severe capacity collapse:
1. **Base-to-Instruct Deficit**: Starting from a raw base model forced 360M parameters to simultaneously learn language alignment, chat syntax, and 17 complex tool schemas, exceeding parameter capacity.
2. **Schema Bleed**: The model blended arguments across distinct tools (e.g. emitting `{'action': 'number', ...}` inside calculator).
3. **Delimiter Fragility**: Text-delimited JSON tool calls (`<tool_call>{...}</tool_call>`) frequently suffered syntax breakage on sub-1B models without aggressive regex repair routines.

## Considered Alternatives
1. **LoRA Fine-Tuning SmolLM2-360M-Instruct with 6 tools**: Functional in v2.1, but constrained to 8k context and requires runtime regex normalization.
2. **Qwen 2.5 / 3 (1.5B–4B)**: Exceptionally smart, but parameter count (>1.4GB) exceeds sub-1B ultra-lightweight target.
3. **Google FunctionGemma 270M (`google/functiongemma-270m-it`)**: A 268M parameter model specifically pre-trained by Google for multi-function declarations using hardware-level control tokens (`<start_function_call>`, `<start_function_response>`).

## Decision Outcome
- **Chosen Option**: Pivot the v3 OS Agent to `functiongemma:latest` (268M Q8_0, 300MB footprint).
- **Rationale**: Dedicated hardware control tokens eliminate ASCII delimiter parsing errors; native tool capability in Ollama enables clean, zero-overhead execution; fits entirely within 300MB VRAM with zero host CPU/RAM pressure.

## Consequences
- **Positive**: Zero schema bleed; sub-second inference latency; native multi-function declarations; ultra-compact 300MB footprint.
- **Negative / Trade-offs**: Smaller world knowledge base compared to 4B+ models; strictly suited for function dispatching and execution rather than open-domain conversational essays.
