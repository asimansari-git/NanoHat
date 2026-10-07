---
adr: "005"
title: "Offline-First Architecture & Frozen 17 OS Functionalities for v3.0.0"
date: 2026-09-14
status: "accepted"
tags:
  - adr/accepted
related:
  - "[[00_INDEX]]"
  - "[[ADR-003-V3-FunctionGemma-Pivot]]"
  - "[[2026-09-14-v3.0.0-frozen-17-tools-scope]]"
---

# ADR-005: Offline-First Architecture & Frozen 17 OS Functionalities for v3.0.0

- **Status:** `#adr/accepted`
- **Date:** 2026-09-14
- **Context:** `[[00_INDEX]]`, `[[2026-09-14-v3.0.0-frozen-17-tools-scope]]`

---

## Context & Problem Statement

In developing NanoHat v3 with `FunctionGemma 270M`, generic web search was introduced as a fallback tool. Testing revealed several critical architectural liabilities:
1. **Host Environment Fragility**: Web search clients triggered local SSL permission errors (e.g. unreadable root-owned `/etc/pki/tls/certs/sendmail.pem`).
2. **Context Window Contamination**: Raw web search snippets (300–600 tokens) flooded the prompt, leading to synthesis degradation on small 268M models.
3. **Cross-Distro Pollution**: Open web searches frequently returned Debian/Ubuntu instructions (`apt-get`) instead of native Fedora commands (`dnf5`, `flatpak`).
4. **Scope Creep**: Expanding into web search diverted focus from NanoHat's core identity as a fast, reliable, offline Linux desktop controller.

---

## Considered Alternatives

1. **Option 1: Retain Open Web Search with Filter Gates**: Keep generic DuckDuckGo and parse results with regex filters.
   - *Cons*: High latency, network failure points, and token bloating.
2. **Option 2: Scoped Fedora Web Search Only (`site:docs.fedoraproject.org`)**: Restrict search strictly to Fedora docs.
   - *Cons*: Still introduces network dependence, latency, and SSL edge cases into the core runtime.
3. **Option 3 (Chosen): Ditch Web Search for v3.0.0; Freeze 17 Offline OS Functionalities**:
   - Focus exclusively on local system control, metrics, application management, safe AST math, user memory, and task scheduling.
   - Defer web/documentation search to a future minor release (`v3.3.x`) as an optional opt-in plugin.

---

## Decision Outcome

- **Chosen Option**: Option 3 (Offline-First Architecture with 17 Frozen OS Functionalities).
- **Rationale**:
  - Eliminates network dependencies and host SSL permission issues.
  - Ensures deterministic, sub-second execution on sub-1B hardware.
  - Locks down a definitive, testable scope for the `v3.0.0` milestone.

---

## Consequences

- **Positive**:
  - 100% deterministic, offline operation.
  - Sub-300M model operates with high tool calling precision without token bloat.
  - Clear, discrete boundary of 17 testable OS capabilities.
- **Trade-offs**:
  - NanoHat v3.0.0 will not answer broad internet queries (e.g. "latest news" or online documentation lookups). These queries will be deferred to v3.3.x or local `tldr`/`man` tools in v3.1.x.
