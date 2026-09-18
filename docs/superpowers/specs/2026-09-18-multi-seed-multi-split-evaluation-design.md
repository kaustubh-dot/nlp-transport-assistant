# Multi-Seed, Multi-Split Evaluation & Extended Training Design

**Status:** Proposed  
**Date:** 2026-09-18  
**Scope:** Rigorous statistical evaluation across multiple random splits and random initialization seeds with extended epochs (6 epochs) for all candidate NLU models on the NVIDIA RTX 4000 Ada GPU.  

---

## 1. Motivation & Requirements

In the initial evaluation phase, 6 candidate architectures were fine-tuned for 3 epochs on a single fixed split (seed 42). To establish rigorous scientific confidence:
1. **Longer Epochs**: Train models for 6 epochs with validation Macro-F1 checkpointing, linear learning rate warmup, and decay to evaluate convergence and peak generalization without overfitting.
2. **Multiple Test Splits & Seeds**: Evaluate across 3 independent random partitionings and initialization seeds ($S \in \{42, 1337, 2026\}$) with strict template family-disjoint splits, guaranteeing zero holdout leakage.
3. **Comprehensive Comparative Matrix**: Aggregate statistical metrics ($\text{Mean} \pm \text{Std}$) for Test Accuracy, Test Macro-F1, Acceptance Intent Accuracy, Acceptance Factual Success, and Inference Latency across:
   - Baseline (TF-IDF + Logistic Regression)
   - Google MuRIL (`google/muril-base-cased`)
   - AI4Bharat IndicBERT v2 (`ai4bharat/IndicBERTv2-MLM-only`)
   - Meta XLM-RoBERTa (`xlm-roberta-base`)
   - Sentence-Transformers MiniLM (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
   - L3Cube HingBERT (`l3cube-pune/hing-bert`)

---

## 2. Architecture & Pipeline Design

### Component 1: Multi-Split Generation Pipeline
* File: `scripts/generate_intent_dataset.py`
* Enhancements:
  - Add `--seed` argument (default: 42) and `--output` argument.
  - Shuffle template families using the specified seed.
  - Maintain exact 70% train / 15% val / 15% test proportions.
  - Restrict external harvested queries strictly to the training partition.
  - Enforce zero query string or template family overlap across splits.
  - Generate 3 distinct split datasets:
    - `data/processed/splits/intents_seed_42.csv`
    - `data/processed/splits/intents_seed_1337.csv`
    - `data/processed/splits/intents_seed_2026.csv`

### Component 2: Extended Multi-Seed Training Harness
* File: `scripts/train_and_compare_models.py`
* Enhancements:
  - Add `--seed` CLI argument to control `torch.manual_seed`, `np.random.seed`, and `random.seed`.
  - Add `--data-path` CLI argument to train against specific split datasets.
  - Increase default `--epochs` from 3 to 6.
  - Per-epoch validation evaluation with model checkpoint selection based on highest validation Macro-F1.
  - Maintain Bfloat16 mixed precision on the RTX 4000 Ada GPU.

### Component 3: Statistical Multi-Seed Benchmarker & Report Generator
* File: `scripts/benchmark_multi_seed.py`
* Functionality:
  - Orchestrates training and evaluation across all 6 models and all 3 seeds.
  - For each run, evaluates:
    1. Unseen held-out test split for that seed.
    2. Frozen 149-case gold acceptance test suite (`data/eval/acceptance_test_suite.json`).
  - Computes summary statistics:
    - $\text{Mean} \pm \text{Std}$ for Test Accuracy & Test Macro-F1.
    - $\text{Mean} \pm \text{Std}$ for Gold Acceptance Intent Accuracy.
    - $\text{Mean} \pm \text{Std}$ for Gold Acceptance Factual E2E Success.
    - Per-class F1 breakdown across all 7 intent classes.
    - Mean and P95 latency (ms).
  - Outputs:
    - `docs/benchmarks/multi_seed_comparison.md`: Detailed markdown report with full comparison tables.
    - `docs/benchmarks/multi_seed_results.json`: Machine-readable raw metrics.
    - Updates `docs/benchmarks/model_comparison.md` with multi-seed statistical summary.

### Component 4: Production Champion Integrity Verification
* Verification:
  - The highest-performing model across multi-seed evaluations is verified as the active backend in `src/pipeline.py`.
  - Full test suite (`pytest -v`) and independent acceptance evaluation must pass 100%.

---

## 3. Verification & Acceptance Criteria
1. `data/processed/splits/` contains 3 valid disjoint splits with $\ge 5,000$ rows each and 0 overlap.
2. All 6 candidate architectures successfully complete 6-epoch training runs across all 3 seeds.
3. `docs/benchmarks/multi_seed_comparison.md` contains complete $\text{Mean} \pm \text{Std}$ comparative tables.
4. Acceptance test suite passes $\ge 95\%$ Intent Accuracy and $100\%$ Factual E2E Success on the champion model.
5. All 68+ tests in `pytest -v` pass.
