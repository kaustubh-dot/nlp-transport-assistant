# NLP v2 Gate B.2 Training Convergence Report

**Date:** 2026-09-19  
**Snapshot:** `chennai_multimodal_v1.2.2`  
**Max Epochs Configured:** 30  
**Early Stopping Policy:** Patience = 3 epochs, min_delta = 0.001  
**Hardware:** NVIDIA RTX 4000 Ada Generation (BF16 Mixed Precision)  

---

## 1. Executive Convergence Summary

In Gate B.1, fine-tuning was constrained by `max_epochs = 15`, causing multiple runs to reach their best checkpoint at epoch 14 or 15 (a binding ceiling). Under Section 21 of the Gate B.2 master instruction, the ceiling was raised to `max_epochs = 30`.

**Finding:** All 6 transformer runs successfully converged and triggered early stopping naturally well before the 30-epoch ceiling. The distance from ceiling ranges from 8 to 21 epochs. No run was artificially truncated.

---

## 2. Detailed Convergence Table Across All 6 Transformer Runs

| Model / Architecture | Seed | Epochs Completed | Best Epoch | Stopping Epoch | Early Stop Triggered? | Distance from Max Ceiling (30) | Runtime (s) | Best Val Metric |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T2-H (Shared-Encoder Multitask)** | 42 | 12 | **9** | 12 | **YES** | **21 epochs** | 111.3s | Val Op-F1: 0.8563 |
| **T2-H (Shared-Encoder Multitask)** | 101 | 13 | **10** | 13 | **YES** | **20 epochs** | 119.9s | Val Op-F1: 0.8510 |
| **T2-H (Shared-Encoder Multitask)** | 777 | 14 | **11** | 14 | **YES** | **19 epochs** | 129.3s | Val Op-F1: 0.8548 |
| **T3 (Direct 16-Class)** | 42 | 25 | **22** | 25 | **YES** | **8 epochs** | 234.1s | Val Macro-F1: 0.9155 |
| **T3 (Direct 16-Class)** | 101 | 19 | **16** | 19 | **YES** | **14 epochs** | 178.2s | Val Macro-F1: 0.8605 |
| **T3 (Direct 16-Class)** | 777 | 16 | **13** | 16 | **YES** | **17 epochs** | 150.4s | Val Macro-F1: 0.8615 |

---

## 3. Ceiling Status & Sign-off

- **Max-Epoch Ceiling Binding:** **NO** (0 of 6 runs bound).
- **Early Stopping Integrity:** All models restored their best checkpoint state dictionary before final evaluation on `gate_b2_stress_eval.csv`.
- **Sign-off Condition (Section 21 & 46):** **SATISFIED**.
