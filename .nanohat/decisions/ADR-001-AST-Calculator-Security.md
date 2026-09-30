---
adr: "001"
title: "AST-Based Expression Evaluation for Calculator Tool"
date: 2026-09-12
status: "accepted"
tags:
  - adr/accepted
  - security
related:
  - "[[00_INDEX]]"
  - "[[2026-09-12-v2.1-cli-packaging]]"
---

# ADR-001: AST-Based Expression Evaluation for Calculator Tool

- **Status:** `#adr/accepted`
- **Date:** 2026-09-12
- **Context:** `[[00_INDEX]]`, `[[2026-09-12-v2.1-cli-packaging]]`

## Context & Problem Statement
In earlier prototypes (v1 & v2), the `calculator` tool relied on Python's built-in `eval()` function to compute arithmetic results. Because NanoHat operates with local shell access, an LLM generating arbitrary string injections (e.g. `__import__('os').system(...)`) could lead to Remote Code Execution (RCE) on the host machine.

## Considered Alternatives
1. **Python `eval()` with restricted globals/builtins**: Still vulnerable to bytecode inspection, subclass traversal, and memory exhaustion.
2. **Third-party math parser (e.g. `sympy` or `simpleeval`)**: Adds heavy external dependencies and runtime latency to a lightweight sub-1B agent.
3. **Recursive AST Parser (`ast.parse`)**: Zero-dependency standard library implementation that parses arithmetic into an Abstract Syntax Tree, strictly permitting only whitelisted binary/unary operators and numerical constants.

## Decision Outcome
- **Chosen Option**: Recursive AST Parser (`ast.parse(mode='eval')`).
- **Rationale**: Completely eliminates arbitrary code execution by rejecting function calls, attribute access, and imports at the syntax tree level before evaluation occurs. Enforces strict exponent ceilings (`2**1000`) to prevent denial-of-service hangs.

## Consequences
- **Positive**: 100% immune to prompt injection RCE; zero external dependencies; sub-millisecond execution.
- **Negative / Trade-offs**: Does not support complex symbolic calculus, which is out of scope for a basic OS calculator.
