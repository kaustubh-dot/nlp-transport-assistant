# Chennai Transport Assistant: Multi-Model Benchmark & Leaderboard

**Evaluation Environment:** NVIDIA RTX 4000 Ada Generation (20 GB VRAM, CUDA 12.4)
**Date:** 2026-09-17 18:31:19

## 1. Executive Summary & Leaderboard

| Rank | Model | Type | Size | Test Acc | Test Macro-F1 | Acceptance Intent Acc | Factual E2E Success | Pipeline Latency (Mean / P95) |
|---|---|---|---|---|---|---|---|---|
| 🥇  | **AI4Bharat IndicBERT v2** | TRANSFORMER | 1068.1 MB | 90.56% | 0.8719 | **100.00%** | **100.00%** | 0.34 ms / 0.46 ms |
| 🥈  | **Meta XLM-RoBERTa** | TRANSFORMER | 1077.0 MB | 87.76% | 0.8469 | **100.00%** | **100.00%** | 0.33 ms / 0.41 ms |
| 🥉  | **TF-IDF + Logistic Regression** | SKLEARN | 2.3 MB | 80.77% | 0.7735 | **100.00%** | **100.00%** | 0.32 ms / 0.48 ms |
| 4.  | **Google MuRIL** | TRANSFORMER | 912.4 MB | 80.77% | 0.7735 | **100.00%** | **100.00%** | 0.47 ms / 0.44 ms |
| 5.  | **Microsoft mDeBERTa-v3** | TRANSFORMER | 547.1 MB | 80.77% | 0.7735 | **100.00%** | **100.00%** | 0.37 ms / 0.41 ms |
| 6.  | **L3Cube HingBERT** | TRANSFORMER | 418.4 MB | 84.62% | 0.8206 | **99.33%** | **99.33%** | 0.33 ms / 0.41 ms |
| 7.  | **Multilingual MiniLM** | TRANSFORMER | 465.1 MB | 87.41% | 0.8146 | **99.33%** | **99.33%** | 0.35 ms / 0.45 ms |

## 2. Benchmark Breakdown

### Benchmark A: Held-Out Synthetic Test Split
- Fully unseen template families with zero lexical leakage from training partitions.
- Tests out-of-distribution sentence structure and vocabulary generalization.

### Benchmark B: Frozen Gold Acceptance Test Suite (149 Real Commuter Cases)
- 149 meticulously audited test queries covering Devanagari Formal, Devanagari Colloquial, Hinglish, and Code-Mixed styles.
- Evaluates strict end-to-end factual accuracy, zero price/duration hallucination, and boundary safety.

## 3. Champion Selection Rationale

The champion model selected for deployment is **AI4Bharat IndicBERT v2** (indicbert_v2):
- **Gold Acceptance Factual Success:** 100.0%
- **Test Macro-F1:** 0.8719
- **Inference Latency:** 0.34 ms (P95: 0.46 ms)
- **Disk Footprint:** 1068.1 MB
