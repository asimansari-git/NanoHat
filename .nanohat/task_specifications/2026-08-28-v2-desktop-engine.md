---
title: "NanoHat v2: Native Desktop Engine & Curriculum SFT"
date: 2026-08-28
branch: "main"
status: "completed"
tags:
  - task/done
  - milestone/v2
related:
  - "[[00_INDEX]]"
---

# NanoHat v2: Native Desktop Engine & Curriculum SFT

- **Branch:** `main`
- **Date:** 2026-08-28
- **Status:** `#task/done`
- **Vault Index:** `[[00_INDEX]]`

---

## 🎯 Objective & Problem Statement

### Problem
1. **Generic Framework Overhead**: High-level agent frameworks introduced unnecessary latency, fragile parsing, and brittle error handling.
2. **Data Scarcity**: SmolLM2 required high-quality multi-turn OS interaction trajectories to learn proper schema compliance without hallucinations.

### Accepted Solution
- **Curriculum Generation**: Built a 4-phase synthetic dataset generator querying teacher models (`DeepSeek V4 Pro` / `Ox Alpha`).
- **Validation Pipeline**: Built mechanical validators (`canonicalizer.py`, `schema_checker.py`, `validate_dataset.py`) enforcing role order, canonical syntax, and concise `<thought>` tags.
- **Unsloth 16-Bit LoRA SFT**: Developed response-only loss masking trainer (`training/train_unsloth.py` and `training/colab_train_v2.py`) training over 30,000 conversations.
- **GGUF Export**: Created `training/merge_adapter.py` exporting merged weights into `F16` and `Q4_K_M` GGUF for Ollama runtime.

### Acceptance Criteria
- [x] >30,000 verified multi-turn training conversations curated and split into train/eval.
- [x] Unsloth LoRA training completed in Colab T4 across 3 epochs.
- [x] GGUF adapter exported and registered as `nanohat2.1:360m` in Ollama.
- [x] Tool-calling accuracy >95% on evaluation benchmarks.
