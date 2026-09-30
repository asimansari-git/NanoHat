# NanoHat v3.1.0 Router Evaluation Scorecard

**Benchmark Date:** 2026-09-30 12:19:10  
**Evaluation Dataset:** 80 curated test queries across 4 difficulty tiers  
**Ground Truth Catalog:** 17 production tools (`runtime/tools.py`)  

---

## 🏆 Head-to-Head Executive Scorecard

| Metric | Regex Router (Baseline) | Semantic Router (BGE-small) | Delta / Winner |
| :--- | :--- | :--- | :--- |
| **Overall Top-1 Accuracy** | **68.75%** | **77.5%** | +8.75% 🏆 |
| **Overall Top-3 Accuracy** | **86.25%** | **93.75%** | +7.50% 🏆 |
| **Latency P50** | 0.086 ms | 11.118 ms | Regex (Fast-path) |
| **Latency P95** | 0.287 ms | 14.215 ms | Standard Sub-50ms Budget |

---

## 📊 Detailed Tier-by-Tier Breakdown (Top-3 Accuracy)

| Difficulty Tier | Cases | Regex Router | Semantic Router | Key Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Direct Queries** | 20 | 100.0% | 100.0% | Canonical precision |
| **Tier 2: Slang & Typos** | 20 | 90.0% | 90.0% | Dense vector tolerance |
| **Tier 3: Implicit Diagnostics** | 20 | 70.0% | 90.0% | Semantic hardware reasoning |
| **Tier 4: Adversarial / Multi** | 20 | 85.0% | 95.0% | Negative constraint disambiguation |

---

## 🔬 Architectural Summary
1. **Hybrid Execution:** NanoHat v3.1.0 leverages the fast-path regex bypass for immediate micro-queries (<0.05ms) while dispatching complex natural language queries to the 384-dimensional dense semantic index.
2. **Attention Budget Protection:** FunctionGemma 270M receives an exact, filtered 2-4 tool schema payload per turn, preserving context coherence and eliminating hallucinated parameters.
