---
adr: "002"
title: "Fail-Closed Confirmation Gates for Destructive OS Actions"
date: 2026-09-12
status: "accepted"
tags:
  - adr/accepted
  - security
related:
  - "[[00_INDEX]]"
  - "[[2026-09-12-v2.1-cli-packaging]]"
---

# ADR-002: Fail-Closed Confirmation Gates for Destructive OS Actions

- **Status:** `#adr/accepted`
- **Date:** 2026-09-12
- **Context:** `[[00_INDEX]]`, `[[2026-09-12-v2.1-cli-packaging]]`

## Context & Problem Statement
Autonomous agents that execute bash commands or modify files can inadvertently delete user data or overwrite critical configuration files if hallucinated or invoked in non-interactive pipelines (e.g. headless cron, automated scripts, piped stdin).

## Considered Alternatives
1. **Unrestricted Execution**: Always execute commands immediately without confirmation. Unacceptable risk for user systems.
2. **Interactive-Only Confirmation**: Prompt user via `input()` on stdin. Fails or hangs when stdin is not a TTY or when running in background scripts.
3. **Fail-Closed Confirmation Gate with Explicit Daemon Override**: Interactively prompts on TTY; if non-interactive (headless), automatically refuses destructive actions unless an explicit environment variable (`NANOHAT_AUTO_APPROVE_DESTRUCTIVE=1`) is set.

## Decision Outcome
- **Chosen Option**: Fail-Closed Confirmation Gate (`_confirm_action`).
- **Rationale**: Prioritizes host system integrity. Headless executions default to safe refusal (`[Declined: Non-interactive session requires manual approval]`), preventing accidental destruction.

## Consequences
- **Positive**: Complete host safety in automated runs; explicit opt-in for trusted environments.
- **Negative / Trade-offs**: Headless automated test suites must explicitly mock or set the override flag to test destructive code paths.
