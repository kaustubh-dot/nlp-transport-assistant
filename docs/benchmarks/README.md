# Benchmark Suite & Historical Comparison Guide

This directory contains the experimental evaluations and comparative leaderboards for the Chennai Hindi/Hinglish Transport Assistant.

---

## 🧭 Which Benchmark Should I Look At?

| Use Case | Relevant Benchmark | Report File | Raw Data |
|---|---|---|---|
| **Production Decision / Current Leaderboard** | **Current Multi-Seed Benchmark** (5 Seeds, Early Stopping) | [`current_multi_seed_5seed_benchmark.md`](current_multi_seed_5seed_benchmark.md) | [`current_multi_seed_5seed_results.json`](current_multi_seed_5seed_results.json) |
| **Historical Comparison / Preliminary Run** | **Earlier Single-Seed Benchmark** (Fixed 3 Epochs, Seed 42) | [`earlier_single_seed_3epoch_benchmark.md`](earlier_single_seed_3epoch_benchmark.md) | [`earlier_single_seed_3epoch_results.json`](earlier_single_seed_3epoch_results.json) |
| **Gold Acceptance Suite Audit** | **149 Real-World Commuter Queries** (Evaluated on Champion) | *Included in reports* | [`gold_acceptance_results.json`](gold_acceptance_results.json) |

---

## 📊 Side-by-Side Methodology Comparison

| Experimental Parameter | Earlier Preliminary Run (2026-09-17) | Current Production Benchmark (2026-09-18) | Rationale for Change |
|---|---|---|---|
| **Status** | 🗄️ Archived / Preliminary | 🏆 **Current Official Benchmark** | Rigorous multi-seed verification |
| **Seeds Evaluated** | 1 seed (`42`) | **5 independent seeds** (`[42, 101, 777, 1337, 2026]`) | Mitigates seed variance in fine-tuning |
| **Training Budget** | Fixed 3 epochs | **Up to 15 epochs** with early stopping (patience=3) | Prevents premature truncation of large models |
| **Stopping Criterion** | None (stopped at 3) | Validation Macro-F1 ($\Delta \ge 0.001$) | Stops when model reaches true convergence |
| **Hardware Precision** | FP32 | **BF16 AMP** (RTX 4000 Ada) | Higher training throughput, zero underflow |
| **Latency Measurement** | Async CPU dispatch (~0.33 ms) | **CUDA-synchronized physical time** (`torch.cuda.synchronize()`, batch=1, ~3.0 ms) | Accurate real-world execution profiling |
| **Champion Model** | AI4Bharat IndicBERT v2 (90.56% Acc) | **Google MuRIL** (`0.8927 ± 0.0226` Macro-F1, `90.49%` Acc) | MuRIL converges at epoch 5–8 |

---

## 🔍 Why Did the Leaderboard Rankings Change?

### 1. MuRIL Underfitting in the Earlier 3-Epoch Run
In the **earlier benchmark**, models were restricted to only 3 epochs. Google MuRIL (236M parameters) has heavy bidirectional representation capacity and required 5 to 8 epochs to converge on Indian transit queries. At 3 epochs, MuRIL was severely underfitted, scoring only 78.85% accuracy. In the **current benchmark** with early stopping up to 15 epochs, MuRIL peaked at epoch 5 and outperformed every other model across all 5 seeds.

### 2. IndicBERT v2 Fast Convergence
AI4Bharat IndicBERT v2 has an architecture pre-trained specifically on IndicCorp corpora. It adapts very quickly in early epochs (peaking near epoch 3–5), which made it dominate the earlier 3-epoch benchmark. With full training and multi-seed averaging, it remains strong at #2 (`0.8772 ± 0.0284` Macro-F1).

### 3. Latency Measurement Correction
In the earlier benchmark, latency was reported as `~0.33 ms` because `time.perf_counter()` was measuring the asynchronous submission of CUDA kernels from the CPU without waiting for the GPU to complete execution. The current benchmark forces `torch.cuda.synchronize()` on every iteration with 30 warmup iterations and 100 timed iterations, reflecting true physical GPU latency (`2.7 - 3.1 ms`).

---

## 📁 File Manifest

- **[`current_multi_seed_5seed_benchmark.md`](current_multi_seed_5seed_benchmark.md)**: Full markdown report of the 5-seed benchmark with $\text{Mean} \pm \text{Std}$ leaderboard, per-seed breakdown, and convergence statistics.
- **[`current_multi_seed_5seed_results.json`](current_multi_seed_5seed_results.json)**: Machine-readable JSON containing full metric dictionaries for all 26 model-seed runs.
- **[`earlier_single_seed_3epoch_benchmark.md`](earlier_single_seed_3epoch_benchmark.md)**: Archived markdown report from the preliminary 3-epoch trial.
- **[`earlier_single_seed_3epoch_results.json`](earlier_single_seed_3epoch_results.json)**: Archived JSON from the preliminary 3-epoch trial.
- **[`gold_acceptance_results.json`](gold_acceptance_results.json)**: Verification log of the 149-query gold acceptance suite on Champion Google MuRIL.
