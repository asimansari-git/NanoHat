---
adr: "004"
title: "In-Context Balanced Exemplars for Sub-300M Tool Induction"
date: 2026-09-14
status: "accepted"
tags:
  - adr/accepted
  - architecture
  - few-shot
related:
  - "[[00_INDEX]]"
  - "[[2026-09-14-v3-functiongemma-harness]]"
---

# ADR-004: In-Context Balanced Exemplars for Sub-300M Tool Induction

- **Status:** `#adr/accepted`
- **Date:** 2026-09-14
- **Context:** `[[00_INDEX]]`, `[[2026-09-14-v3-functiongemma-harness]]`

## Context & Problem Statement
When tested with open-ended Linux how-to questions (e.g. *"How can I get a clipboard in Fedora 44 Workstation?"*), FunctionGemma 270M frequently emitted safe refusals (*"I cannot assist with clipboard settings..."*) instead of invoking `web_search`. However, when explicitly ordered (*"Use web search and answer: ..."*), it called `web_search` immediately.

### Root Cause
1. **Narrow Semantic Induction in Sub-300M Models**: Unlike 70B models with broad latent reasoning, 268M models rely heavily on direct semantic verbs (`search`, `find`, `calculate`).
2. **Missing Specific Tool Reflex**: Without a dedicated `clipboard` tool in the catalog, the model's instruction-tuned alignment default was to safely refuse rather than infer that `web_search` should act as an open-domain fallback.

## Considered Alternatives
1. **Zero-Shot System Prompt Instructions Only**: Failed. The model ignored prompt instructions to search for general questions because pre-trained refusal weights dominated.
2. **Engine Keyword Interception**: Using regex/heuristics in Python to force `web_search` on questions starting with "How do I". Brittle and degrades model autonomy.
3. **In-Context Balanced Few-Shot Exemplars**: Injecting 1 minimal example for each tool class (`calculator`, `web_search`, `system_health`) into the conversation history.

## Decision Outcome
- **Chosen Option**: Balanced In-Context Few-Shot Exemplars + Refusal-Recovery Safety Net.
- **Rationale**: Providing 1 exemplar of `"How do I..."` mapping to `web_search` immediately shifted the model's attention weights, causing it to autonomously route general how-to questions to `web_search` without explicit user directives. Providing a corresponding `calculator` exemplar prevented few-shot imbalance bias.

## Consequences
- **Positive**: Seamless, natural tool invocation on natural language queries; zero need for users to prefix queries with "Use web search".
- **Negative / Trade-offs**: Consumes ~80 prompt tokens per turn for the exemplars, easily sustained by FunctionGemma's 32k context window.
