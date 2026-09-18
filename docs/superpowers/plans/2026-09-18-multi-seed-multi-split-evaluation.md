# Multi-Seed, Multi-Split Evaluation & Extended Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conduct an exhaustive, scientifically rigorous statistical comparison across all 6 candidate NLU architectures by training for 6 epochs across 3 independent seeds and disjoint test splits, compiling Mean ± Std metrics on holdouts and the frozen gold acceptance benchmark.

**Architecture:** Python CLI tools leveraging PyTorch 2.6, BF16 mixed precision, Hugging Face transformers, and scikit-learn. Generates deterministic, family-disjoint train/val/test splits, executes multi-seed training with validation-guided checkpointing, evaluates against holdout splits and the frozen 149-case gold acceptance suite, and outputs comprehensive statistical reports.

**Tech Stack:** PyTorch 2.6.0+cu124, Hugging Face Transformers 5.17, Scikit-learn, Pandas, SQLite3, Streamlit 1.44.

**Spec:** `docs/superpowers/specs/2026-09-18-multi-seed-multi-split-evaluation-design.md`

## Global Constraints
- Strictly open source, ₹0 cost, local inference on NVIDIA RTX 4000 Ada Generation GPU (20 GB VRAM).
- Frozen gold acceptance suite (`data/eval/acceptance_test_suite.json`, 149 cases) must remain unmodified.
- No template family or query string leakage across train, val, and test splits.
- All existing tests (68 tests) must continue to pass with zero regressions.

---

### Task 1: Multi-Split Dataset Generation Pipeline with Seed Controls
**Files:**
- Modify: `scripts/generate_intent_dataset.py`
- Create: `tests/test_multi_split_generation.py`
- Target outputs: `data/processed/splits/intents_seed_42.csv`, `data/processed/splits/intents_seed_1337.csv`, `data/processed/splits/intents_seed_2026.csv`

**Interfaces:**
- CLI: `python scripts/generate_intent_dataset.py --seed <int> --output <path>`
- Ensures family disjointness and class balance for every generated split.

- [ ] **Step 1: Write tests for multi-split generation in `tests/test_multi_split_generation.py`**
- [ ] **Step 2: Update `scripts/generate_intent_dataset.py` to accept `--seed` and `--output`**
- [ ] **Step 3: Generate the 3 split files (`seed_42`, `seed_1337`, `seed_2026`)**
- [ ] **Step 4: Run `pytest tests/test_multi_split_generation.py -v` and commit**

---

### Task 2: Extended Multi-Seed Training Harness with Validation Macro-F1 Checkpointing
**Files:**
- Modify: `scripts/train_and_compare_models.py`
- Test: `tests/test_model_harness.py`

**Interfaces:**
- CLI: `python scripts/train_and_compare_models.py --model <key> --epochs 6 --seed <int> --data-path <path>`
- Trains with BF16 mixed precision, evaluates validation loss and Macro-F1 at every epoch, and saves the best validation checkpoint.

- [ ] **Step 1: Update `scripts/train_and_compare_models.py` with seed, data path, and checkpointing logic**
- [ ] **Step 2: Test single-model training run on Seed 42 for 6 epochs**
- [ ] **Step 3: Run `pytest tests/test_model_harness.py -v` and commit**

---

### Task 3: Statistical Multi-Seed Benchmarker & Report Generator
**Files:**
- Create: `scripts/benchmark_multi_seed.py`
- Create: `tests/test_multi_seed_benchmarker.py`
- Outputs: `docs/benchmarks/multi_seed_comparison.md`, `docs/benchmarks/multi_seed_results.json`

**Interfaces:**
- CLI: `python scripts/benchmark_multi_seed.py --seeds 42 1337 2026 --epochs 6 --output-md docs/benchmarks/multi_seed_comparison.md`
- Runs 6 models across 3 seeds ($6 \times 3 = 18$ runs), evaluates on both holdout test split and gold acceptance suite.
- Calculates Mean ± Std for Test Accuracy, Test Macro-F1, Acceptance Accuracy, E2E Factual Success, and Latency.

- [ ] **Step 1: Write test for multi-seed benchmarker structure**
- [ ] **Step 2: Implement `scripts/benchmark_multi_seed.py`**
- [ ] **Step 3: Execute the full multi-seed benchmark across all 6 models and 3 seeds**
- [ ] **Step 4: Verify generated `docs/benchmarks/multi_seed_comparison.md` and commit**

---

### Task 4: Champion Model Integrity & Production Verification
**Files:**
- Verify: `src/pipeline.py`
- Update: `docs/benchmarks/model_comparison.md`
- Test: Full test suite (`pytest -v`) and `scripts/evaluate.py --acceptance`

- [ ] **Step 1: Verify champion model weights loaded into production pipeline**
- [ ] **Step 2: Run full regression test suite (`pytest -v`)**
- [ ] **Step 3: Run gold acceptance evaluation on champion model**
- [ ] **Step 4: Commit and push all benchmark results and code to GitHub**
