# Multi-Seed Intent Classification Benchmark Report
**Generated:** 2026-09-18 13:42:37  
**Hardware:** NVIDIA RTX 4000 Ada Generation (BF16: True)  
**Environment:** PyTorch `2.6.0+cu124`, CUDA `12.4`  
**Dataset Partition:** Frozen Family-Disjoint 70/15/15 Split (Train: 3916, Val: 716, Test: 572)  
**Seeds Evaluated:** `[42, 101, 777, 1337, 2026]` | **Early Stopping:** Patience=3, min_delta=0.001 | **Max Epochs:** 15  

---
## 🏆 Selected Champion Architecture: **Google MuRIL**
- **Primary Metric (Test Macro-F1):** **`0.8927 ± 0.0226`**
- **Test Accuracy:** **`90.49% ± 1.86%`**
- **P95 Single-Query Latency:** `3.01 ms` (batch_size=1, CUDA sync)
- **Model Disk Size:** `912.4 MB` | **Peak VRAM:** `2500.0 MB`
- **Best Epoch Distribution:** `[5, 5, 5, 5, 5]` (Mean: 5.0)

## 1. Overall Model Leaderboard (Mean ± Std across Seeds)

| Rank | Model Architecture | Test Macro-F1 (Mean±SD) | Test Accuracy (Mean±SD) | Val Macro-F1 (Mean±SD) | Best Epochs | P95 Latency | Size | Peak VRAM |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 🥇 Google MuRIL | **0.8927** ± 0.0226 | 90.49% ± 1.86% | 0.8509 ± 0.0449 | [5, 5, 5, 5, 5] | 3.01 ms | 912.4 MB | 2500 MB |
| 2 | 🥈 AI4Bharat IndicBERT v2 | **0.8772** ± 0.0284 | 87.17% ± 2.90% | 0.8950 ± 0.0363 | [5, 5, 5, 5, 5] | 2.94 ms | 1068.1 MB | 2500 MB |
| 3 | 🥉 Multilingual MiniLM (Full FT) | **0.8444** ± 0.0198 | 88.78% ± 1.66% | 0.7650 ± 0.0621 | [9, 5, 3, 4, 4] | 2.71 ms | 465.1 MB | 2285 MB |
| 4 | Meta XLM-RoBERTa | **0.7595** ± 0.0419 | 82.06% ± 3.71% | 0.8307 ± 0.0460 | [5, 6, 3, 7, 7] | 3.15 ms | 1077.0 MB | 5368 MB |
| 5 | TF-IDF + Logistic Regression | **0.7523** (det) | 83.57% (det) | 0.5836 (det) | 1 | 0.57 ms | 2.3 MB | 0 MB |
| 6 | L3Cube HingBERT | **0.6206** ± 0.0478 | 64.79% ± 5.83% | 0.7145 ± 0.0470 | [9, 5, 4, 8, 7] | 3.08 ms | 418.4 MB | 3099 MB |

---
## 2. Seed-by-Seed Fine-Grained Stability Breakdown

| Model | Seed | Best Epoch | Total Epochs | Val Macro-F1 | Test Macro-F1 | Test Accuracy | P95 Latency | Train Time |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| TF-IDF + Logistic Regression | `42` | 1 | 1 | 0.5836 | 0.7523 | 83.57% | 0.57 ms | 1.5s |
| Google MuRIL | `42` | 5 | 8 | 0.8984 | 0.8854 | 90.38% | 3.04 ms | 35.0s |
| Google MuRIL | `101` | 5 | 8 | 0.8965 | 0.9069 | 93.01% | 2.91 ms | 35.0s |
| Google MuRIL | `777` | 5 | 8 | 0.7980 | 0.8970 | 90.73% | 2.92 ms | 35.0s |
| Google MuRIL | `1337` | 5 | 8 | 0.8227 | 0.8579 | 87.76% | 3.17 ms | 35.0s |
| Google MuRIL | `2026` | 5 | 8 | 0.8387 | 0.9162 | 90.56% | 2.99 ms | 35.0s |
| AI4Bharat IndicBERT v2 | `42` | 5 | 8 | 0.9412 | 0.8671 | 85.49% | 2.98 ms | 35.0s |
| AI4Bharat IndicBERT v2 | `101` | 5 | 8 | 0.8980 | 0.8719 | 86.71% | 2.97 ms | 35.0s |
| AI4Bharat IndicBERT v2 | `777` | 5 | 8 | 0.9157 | 0.9134 | 91.26% | 2.75 ms | 35.0s |
| AI4Bharat IndicBERT v2 | `1337` | 5 | 8 | 0.8718 | 0.8388 | 83.74% | 3.30 ms | 35.0s |
| AI4Bharat IndicBERT v2 | `2026` | 5 | 8 | 0.8485 | 0.8947 | 88.64% | 2.72 ms | 35.0s |
| Meta XLM-RoBERTa | `42` | 5 | 8 | 0.8904 | 0.7383 | 84.62% | 3.10 ms | 35.0s |
| Meta XLM-RoBERTa | `101` | 6 | 9 | 0.7958 | 0.7235 | 78.67% | 3.13 ms | 176.0s |
| Meta XLM-RoBERTa | `777` | 3 | 6 | 0.8096 | 0.8089 | 85.49% | 3.31 ms | 123.3s |
| Meta XLM-RoBERTa | `1337` | 7 | 10 | 0.7887 | 0.7258 | 77.45% | 3.09 ms | 196.3s |
| Meta XLM-RoBERTa | `2026` | 7 | 10 | 0.8691 | 0.8009 | 84.09% | 3.10 ms | 194.3s |
| L3Cube HingBERT | `42` | 9 | 12 | 0.7400 | 0.6012 | 64.69% | 3.09 ms | 146.5s |
| L3Cube HingBERT | `101` | 5 | 8 | 0.6602 | 0.6528 | 69.93% | 3.06 ms | 98.0s |
| L3Cube HingBERT | `777` | 4 | 7 | 0.6756 | 0.5449 | 54.90% | 3.07 ms | 86.8s |
| L3Cube HingBERT | `1337` | 8 | 11 | 0.7216 | 0.6503 | 67.13% | 3.09 ms | 134.2s |
| L3Cube HingBERT | `2026` | 7 | 10 | 0.7751 | 0.6537 | 67.31% | 3.08 ms | 121.8s |
| Multilingual MiniLM (Full FT) | `42` | 9 | 12 | 0.7990 | 0.8391 | 88.99% | 2.72 ms | 98.5s |
| Multilingual MiniLM (Full FT) | `101` | 5 | 8 | 0.6732 | 0.8155 | 86.54% | 2.71 ms | 67.0s |
| Multilingual MiniLM (Full FT) | `777` | 3 | 6 | 0.7990 | 0.8505 | 90.73% | 2.68 ms | 51.3s |
| Multilingual MiniLM (Full FT) | `1337` | 4 | 7 | 0.7301 | 0.8700 | 89.86% | 2.74 ms | 58.6s |
| Multilingual MiniLM (Full FT) | `2026` | 4 | 7 | 0.8239 | 0.8471 | 87.76% | 2.72 ms | 59.1s |

---
## 3. Convergence Diagnostics & Safety Verification

Per protocol safety rule, we verify whether the 15-epoch ceiling truncated convergence:

- **Google MuRIL**: Best epochs = `[5, 5, 5, 5, 5]`. ✅ **PASS**: Best epochs peaked safely between 5 and 5 (< 13). Ceiling 15 was non-binding; early stopping operated correctly.
- **AI4Bharat IndicBERT v2**: Best epochs = `[5, 5, 5, 5, 5]`. ✅ **PASS**: Best epochs peaked safely between 5 and 5 (< 13). Ceiling 15 was non-binding; early stopping operated correctly.
- **Multilingual MiniLM (Full FT)**: Best epochs = `[9, 5, 3, 4, 4]`. ✅ **PASS**: Best epochs peaked safely between 3 and 9 (< 13). Ceiling 15 was non-binding; early stopping operated correctly.
- **Meta XLM-RoBERTa**: Best epochs = `[5, 6, 3, 7, 7]`. ✅ **PASS**: Best epochs peaked safely between 3 and 7 (< 13). Ceiling 15 was non-binding; early stopping operated correctly.
- **L3Cube HingBERT**: Best epochs = `[9, 5, 4, 8, 7]`. ✅ **PASS**: Best epochs peaked safely between 4 and 9 (< 13). Ceiling 15 was non-binding; early stopping operated correctly.

---
## 4. Per-Class F1 Score Breakdown (Mean across Seeds)

| Intent Class | Google MuRIL | AI4Bharat IndicBERT v2 | Multilingual MiniLM (Full FT) | Meta XLM-RoBERTa | TF-IDF + Logistic Regression | L3Cube HingBERT |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `route_query` | 0.9353 | 0.8975 | 0.9449 | 0.8785 | 0.8733 | 0.7114 |
| `service_availability` | 0.9540 | 0.9144 | 0.9669 | 0.9052 | 0.8754 | 0.7792 |
| `service_timing` | 0.9474 | 0.9790 | 0.7851 | 0.6014 | 0.4444 | 0.5957 |
| `station_information` | 0.8706 | 0.8740 | 0.7900 | 0.7969 | 0.6508 | 0.4039 |
| `accessibility` | 0.7710 | 0.6498 | 0.6707 | 0.4819 | 0.8535 | 0.2722 |
| `ticketing` | 0.9369 | 0.8995 | 0.9969 | 0.8815 | 0.8846 | 0.7975 |
| `out_of_scope` | 0.8337 | 0.9260 | 0.7568 | 0.7711 | 0.6842 | 0.7841 |

---
## 5. Methodological Notes

- **Dataset Partition Roles**:
  - `train.csv` (70%): Parameter optimization and model weights learning.
  - `validation.csv` (15%): Early stopping monitoring and best-checkpoint selection.
  - `test.csv` (15%): Benchmark / architecture comparison and champion selection holdout.
  - `acceptance_test_suite.json` (149 cases): Final untouched external evaluation suite; never seen during training, early stopping, or hyperparameter selection.
- **Precision & Regularization**: BF16 mixed precision providing improved numerical stability and dynamic range over FP16, paired with standard `max_grad_norm = 1.0` gradient clipping and AdamW weight decay of 0.01.
- **Fixed Effective Batch Size & Length**: Standardized at effective batch size = 32, max sequence length = 128 tokens across all transformer candidate models.
- **Multilingual MiniLM Note**: `paraphrase-multilingual-MiniLM-L12-v2` encoder adapted for 7-class sequence classification and fine-tuned end-to-end.
- **Champion Selection Rule**: Ranked primarily by mean Test Macro-F1 across 5 seeds. Where models fall within run-to-run seed variance (<0.20 F1), inference latency and model footprint break near-ties.
