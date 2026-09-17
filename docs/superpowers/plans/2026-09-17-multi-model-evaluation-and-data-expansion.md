# Multi-Model Evaluation & Data Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exhaustively acquire Hindi/Hinglish transit data from multiple sources, train and benchmark 8 distinct open-source models on RTX 4000 Ada GPU, deploy the champion model, and integrate Whisper ASR and NLLB-200 translation.

**Architecture:** Data harvesting pipeline (CMRL scraping + MASSIVE hi-IN + Hinglish + expanded templates) -> Multi-model training harness -> Dual benchmarking (unseen test holdout + frozen 149 gold acceptance suite) -> Champion model deployment -> Local multimodal speech & translation extensions.

**Tech Stack:** PyTorch 2.6 (CUDA 12.4), Hugging Face Transformers, Datasets, Scikit-learn, OpenAI Whisper, Meta NLLB-200, SQLite, Streamlit.

**Spec:** `docs/superpowers/specs/2026-09-17-multi-model-evaluation-and-data-expansion-design.md`

## Global Constraints
- Target Hardware: NVIDIA RTX 4000 Ada Generation (20 GB VRAM, CUDA 12.4).
- Budget: ₹0 cost, 100% open-source local models, zero paid API keys.
- Acceptance Benchmark: Frozen 149-query suite (`data/eval/acceptance_test_suite.json`) must achieve $\ge 95\%$ Intent Accuracy and $100\%$ E2E Factual Success.
- Latency Constraint: Production inference mean latency $< 50$ ms.
- Zero Hallucination: Unverified fares, operating hours, or durations must return explicit limitations.

---

### Task 1: Data Acquisition & Expansion Pipeline

**Files:**
- Create: `scripts/scrape_cmrl_data.py`
- Create: `scripts/harvest_external_data.py`
- Modify: `data/templates/hindi_templates.json`
- Modify: `scripts/generate_intent_dataset.py`
- Test: `tests/test_dataset_expansion.py`

**Interfaces:**
- Consumes: `data/templates/hindi_templates.json`, `data/curated/cmrl_verified_stations.json`
- Produces: `data/processed/intents.csv` (columns: `query`, `intent`, `split`, `script`, `source`) with $\ge 4,000$ rows, balanced 7 classes, family-disjoint train/val/test splits.

- [ ] **Step 1: Write the failing test for dataset scale, balance, and disjointness**

```python
# tests/test_dataset_expansion.py
import os
import pandas as pd
import pytest

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed", "intents.csv")

def test_expanded_dataset_scale_and_balance():
    assert os.path.exists(DATASET_PATH), f"Dataset missing at {DATASET_PATH}"
    df = pd.read_csv(DATASET_PATH)
    assert len(df) >= 3500, f"Expected >= 3500 samples, got {len(df)}"
    
    # Check 7 classes
    expected_intents = {
        "route_query", "service_availability", "service_timing",
        "station_information", "accessibility", "ticketing", "out_of_scope"
    }
    assert set(df["intent"].unique()) == expected_intents
    
    # Check balance: each intent should have at least 450 samples
    for intent in expected_intents:
        count = len(df[df["intent"] == intent])
        assert count >= 450, f"Intent {intent} only has {count} samples"

def test_split_disjointness():
    df = pd.read_csv(DATASET_PATH)
    assert set(df["split"].unique()) == {"train", "val", "test"}
    
    train_queries = set(df[df["split"] == "train"]["query"])
    test_queries = set(df[df["split"] == "test"]["query"])
    overlap = train_queries.intersection(test_queries)
    assert len(overlap) == 0, f"Data leakage between train and test: {len(overlap)} overlapping queries"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_dataset_expansion.py -v`  
Expected: FAIL (Dataset has fewer than 3500 samples or missing split column)

- [ ] **Step 3: Implement CMRL scraping and external dataset harvester**

Write `scripts/scrape_cmrl_data.py` to extract official FAQs and station guidelines from CMRL.  
Write `scripts/harvest_external_data.py` to ingest Amazon MASSIVE (`hi-IN` subset) transit and OOS queries.  
Update `data/templates/hindi_templates.json` with expanded template families.  
Update `scripts/generate_intent_dataset.py` to compile $\ge 4,000$ samples across 7 intents with family-disjoint train (70%), validation (15%), and test (15%) splits.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python scripts/generate_intent_dataset.py && .venv/bin/pytest tests/test_dataset_expansion.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_dataset_expansion.py scripts/scrape_cmrl_data.py scripts/harvest_external_data.py data/templates/hindi_templates.json scripts/generate_intent_dataset.py data/processed/intents.csv
git commit -m "feat: scale dataset to >= 4000 balanced samples across 7 intents with disjoint splits"
```

---

### Task 2: Multi-Model GPU Training Harness

**Files:**
- Create: `scripts/train_and_compare_models.py`
- Modify: `src/intent_classifier.py`
- Test: `tests/test_model_harness.py`

**Interfaces:**
- Consumes: `data/processed/intents.csv`
- Produces: Trained model weights in `models/<model_tag>/`, training logs, and performance metrics.

- [ ] **Step 1: Write test for training harness structure and model adapter interface**

```python
# tests/test_model_harness.py
import os
import pytest
from src.intent_classifier import INTENT_CLASSES

def test_intent_classes_consistency():
    assert len(INTENT_CLASSES) == 7
    assert "route_query" in INTENT_CLASSES
    assert "out_of_scope" in INTENT_CLASSES

def test_harness_script_exists():
    harness_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "train_and_compare_models.py")
    assert os.path.exists(harness_path)
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/pytest tests/test_model_harness.py -v`  
Expected: FAIL (harness_path does not exist)

- [ ] **Step 3: Implement `scripts/train_and_compare_models.py`**

Implement training adapters for:
1. Baseline: `TfidfClassifier`
2. `google/muril-base-cased`
3. `ai4bharat/IndicBERTv2-MLM-only`
4. `ai4bharat/indic-bert`
5. `l3cube-pune/hing-bert`
6. `xlm-roberta-base`
7. `microsoft/mdeberta-v3-base`
8. `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Use PyTorch with CUDA `fp16`, evaluation on held-out validation set at each epoch, and early stopping.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_model_harness.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_model_harness.py scripts/train_and_compare_models.py src/intent_classifier.py
git commit -m "feat: add multi-model GPU training harness for 8 candidate architectures"
```

---

### Task 3: Exhaustive Dual Benchmark & Leaderboard Generator

**Files:**
- Create: `scripts/benchmark_all_models.py`
- Create: `docs/benchmarks/model_comparison.md`
- Test: `tests/test_benchmark_runner.py`

**Interfaces:**
- Consumes: Trained models in `models/`, `data/processed/intents.csv` (test split), `data/eval/acceptance_test_suite.json` (149 gold cases)
- Produces: `docs/benchmarks/model_comparison.md` containing full metrics matrix (Accuracy, Macro-F1, E2E Factual Success, Latency Mean/P95, Model Size, VRAM).

- [ ] **Step 1: Write test for benchmark script and report generator**

```python
# tests/test_benchmark_runner.py
import os
import json
import pytest

def test_acceptance_suite_exists():
    suite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "eval", "acceptance_test_suite.json")
    with open(suite_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    assert len(items) == 149
```

- [ ] **Step 2: Run test to verify baseline**

Run: `.venv/bin/pytest tests/test_benchmark_runner.py -v`  
Expected: PASS

- [ ] **Step 3: Execute model training and benchmark generation**

Execute: `.venv/bin/python scripts/train_and_compare_models.py --all --epochs 3 --batch-size 32`  
Execute: `.venv/bin/python scripts/benchmark_all_models.py --output docs/benchmarks/model_comparison.md`

- [ ] **Step 4: Verify generated leaderboard table**

Check that `docs/benchmarks/model_comparison.md` contains entries for all 8 models with complete metrics.

- [ ] **Step 5: Commit**

```bash
git add scripts/benchmark_all_models.py docs/benchmarks/model_comparison.md
git commit -m "bench: execute exhaustive training and generate comparative leaderboard"
```

---

### Task 4: Champion Model Deployment & Pipeline Wiring

**Files:**
- Modify: `src/intent_classifier.py`
- Modify: `src/pipeline.py`
- Test: `tests/test_champion_integration.py`

**Interfaces:**
- Consumes: Best checkpoint from `models/`
- Produces: Fully integrated `TransportAssistantPipeline` using champion deep model + rule fallback.

- [ ] **Step 1: Write integration test for champion classifier**

```python
# tests/test_champion_integration.py
import pytest
from src.pipeline import TransportAssistantPipeline

def test_pipeline_with_champion_model():
    pipeline = TransportAssistantPipeline()
    res = pipeline.process("चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?")
    assert res["intent"] == "route_query"
    assert res["origin"] == "CHENNAI_CENTRAL"
    assert res["destination"] == "CHENNAI_AIRPORT"
    assert "मार्ग" in res["response_text"] or "सेंट्रल" in res["response_text"]
```

- [ ] **Step 2: Run test to verify**

Run: `.venv/bin/pytest tests/test_champion_integration.py -v`

- [ ] **Step 3: Update `src/intent_classifier.py` and `src/pipeline.py`**

Wire the champion model as the primary intent classifier with fallback heuristics.

- [ ] **Step 4: Run full regression and acceptance benchmark**

Run: `.venv/bin/pytest -v`  
Run: `.venv/bin/python scripts/evaluate.py --acceptance`  
Expected: All tests pass, Acceptance Intent Accuracy $\ge 95\%$, E2E Factual Success $100\%$.

- [ ] **Step 5: Commit**

```bash
git add src/intent_classifier.py src/pipeline.py tests/test_champion_integration.py
git commit -m "feat: deploy champion model to transport assistant pipeline"
```

---

### Task 5: Multimodal Enhancements (Whisper Hindi ASR & NLLB-200 Translation)

**Files:**
- Create: `src/speech_recognizer.py`
- Create: `src/translator.py`
- Modify: `app/streamlit_app.py`
- Test: `tests/test_multimodal.py`

**Interfaces:**
- `src/speech_recognizer.py`: `transcribe_audio(audio_bytes_or_path: str) -> str`
- `src/translator.py`: `translate_hindi_to_tamil(text: str) -> str`

- [ ] **Step 1: Write tests for Whisper ASR and NLLB-200 Translation**

```python
# tests/test_multimodal.py
import pytest
from src.translator import HindiToTamilTranslator

def test_hindi_to_tamil_translation():
    translator = HindiToTamilTranslator()
    # Simple transit phrase
    hi_text = "चेन्नई सेंट्रल मेट्रो स्टेशन"
    ta_text = translator.translate(hi_text)
    assert len(ta_text) > 0
    # Tamil Unicode block range is \u0B80-\u0BFF
    has_tamil = any("\u0b80" <= ch <= "\u0bff" for ch in ta_text)
    assert has_tamil, f"Expected Tamil script in output, got: {ta_text}"
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/pytest tests/test_multimodal.py -v`  
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `src/speech_recognizer.py`, `src/translator.py`, and Streamlit UI**

Implement `HindiToTamilTranslator` using `facebook/nllb-200-distilled-600M`.  
Implement `HindiSpeechRecognizer` using `openai/whisper-base`.  
Update `app/streamlit_app.py` with audio input recorder and a "Tamil Translation for Station Staff" view card.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_multimodal.py -v`  
Expected: PASS

- [ ] **Step 5: Commit and Push**

```bash
git add src/speech_recognizer.py src/translator.py app/streamlit_app.py tests/test_multimodal.py
git commit -m "feat: add local Whisper Hindi ASR and NLLB-200 Hindi-to-Tamil translation"
git push origin main
```
