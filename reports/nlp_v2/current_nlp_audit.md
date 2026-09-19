# Current NLP Repository and Frozen V1 Benchmark Audit (Phase N0)

Date: 2026-09-19  
Status: Complete  
Target Phase: Multimodal Multilingual NLP v2 Research Program  
Starting Reference Commit: `755f5754d9adb2ac7ea8358f5e7ae404ce942909`  
Knowledge Base Snapshot: `chennai_multimodal_v1.2.1`

---

## 1. Executive Summary

This audit assesses the state of all natural language processing assets, scripts, models, data splits, and benchmark documentation in `nlp-transport-assistant` before the v2 design phase.

The repository transitioned through two distinct historical phases:
1. The historical CMRL Metro NLP benchmark: focused exclusively on 41 operational metro stations and 7 intent classes in Hindi and Hinglish.
2. The multimodal transit knowledge expansion: culminating in snapshot `chennai_multimodal_v1.2.1` with 7,136 physical stops, 4,619 routes, 1,360,635 stop times, and 1,562 bus fare stages.

The NLP pipeline (`src/`) and generation scripts (`scripts/`) still reflect the historical CMRL metro-only assumptions. The knowledge base expanded by two orders of magnitude, but the NLU layer remains coupled to 35 metro station aliases, 7 fixed intents, and a legacy 75-station SQLite file.

This audit establishes explicit component boundaries categorized into four lifecycle decisions:
- FREEZE: Preserve immutable historical benchmark assets with zero modifications.
- REUSE: Retain verified evaluation mechanics, training harness discipline, and seed policies.
- ADAPT: Refactor core modules to support multimodal entities, multi-layer evaluation, and multi-pipeline testing.
- DEPRECATE: Retire obsolete hardcoded gazetteers, legacy SQLite interfaces, and naive generation scripts.

---

## 2. Frozen Historical Benchmark Audit

The existing CMRL benchmark represents an immutable historical record. It evaluates 7 intents across 5 seeds using early stopping.

### 2.1 Benchmark Partition Inventory

| File | Rows | Partition Role | Hash Verification | Decision |
| :--- | :--- | :--- | :--- | :--- |
| `data/processed/intents.csv` | 5,204 | Master generated v1 dataset | SHA-256 verified | FREEZE |
| `data/processed/split/train.csv` | 3,916 | Training partition (70%) | SHA-256 verified | FREEZE |
| `data/processed/split/validation.csv` | 716 | Early stopping & checkpoint selection (15%) | SHA-256 verified | FREEZE |
| `data/processed/split/test.csv` | 572 | Benchmark holdout (15%) | SHA-256 verified | FREEZE |
| `data/processed/split/split_manifest.json` | N/A | Split partition provenance | Seed 42, family-disjoint | FREEZE |
| `data/eval/acceptance_test_suite.json` | 149 | Gold independent test queries | Hand-reviewed 149 queries | FREEZE |

### 2.2 Historical Intent Distribution (v1 Benchmark)

```
service_availability : 1,090 samples (20.95%)
route_query          : 1,054 samples (20.25%)
out_of_scope         :   747 samples (14.35%)
ticketing            :   653 samples (12.55%)
service_timing       :   629 samples (12.09%)
accessibility        :   529 samples (10.16%)
station_information  :   502 samples ( 9.65%)
Total                : 5,204 samples
```

### 2.3 Authoritative Incumbent Results

The authoritative reference for existing models is `docs/benchmarks/current_multi_seed_5seed_benchmark.md` and `docs/benchmarks/current_multi_seed_5seed_results.json`.

Leaderboard summary across 5 seeds (`[42, 101, 777, 1337, 2026]`):
- Rank 1: Google MuRIL (`google/muril-base-cased`): Test Macro-F1 = `0.8927 ± 0.0226`, Test Accuracy = `90.49% ± 1.86%`, P95 Latency = `3.01 ms`, Best Epoch = `5` across all 5 seeds.
- Rank 2: AI4Bharat IndicBERT v2 (`ai4bharat/indic-bert`): Test Macro-F1 = `0.8772 ± 0.0284`, Test Accuracy = `87.17% ± 2.90%`.
- Rank 3: Multilingual MiniLM (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`): Test Macro-F1 = `0.8444 ± 0.0198`.
- Rank 4: Meta XLM-RoBERTa (`xlm-roberta-base`): Test Macro-F1 = `0.7595 ± 0.0419`.
- Rank 5: TF-IDF + Logistic Regression (deterministic baseline): Test Macro-F1 = `0.7523`, Test Accuracy = `83.57%`.
- Rank 6: L3Cube HingBERT (`l3cube-pune/hing-bert`): Test Macro-F1 = `0.6206 ± 0.0478`.

### 2.4 Resolution of Stale Documentation Claims

Earlier documentation (`docs/benchmarks/earlier_single_seed_3epoch_benchmark.md`) recorded a preliminary single-seed run with a fixed 3-epoch budget. In that preliminary run, models hit the 3-epoch ceiling prematurely, showing artificially lower performance (MuRIL Macro-F1 was 0.7712).

The 5-seed benchmark with early stopping (max epochs = 15, patience = 3, min_delta = 0.001) established that MuRIL converges at epoch 5 and achieves `0.8927 ± 0.0226`. All audit documents, comparison tables, and research references must cite `docs/benchmarks/current_multi_seed_5seed_benchmark.md` as the sole ground truth for v1.

---

## 3. Codebase Component-by-Component Audit

### 3.1 Text Normalization (`src/normalization.py`)
- Implementation: Class `HindiNormalizer` applying Unicode NFC normalization, lowercase conversion, punctuation removal, and Devanagari Nuqta removal.
- Strengths: Fast, robust, zero external dependencies.
- Deficiencies:
  - Strips all punctuation aggressively, which destroys bus route suffixes such as `102A`, `102-A`, `102K#`.
  - Does not distinguish Latin Hindi from English.
  - Lacks transliteration normalization (e.g. `gindi` vs `guindy`, `kese` vs `kaise`).
  - Cannot perform entity-protected masking for translation pivots.
- Classification: ADAPT. Maintain base Unicode NFC and Nuqta handling as a low-level utility; build configurable pipeline normalization stages for v2.

### 3.2 Entity Extraction & Gazetteers (`src/entity_extractor.py`)
- Implementation: `EntityExtractor` using a hardcoded 13-station dictionary (`DEFAULT_GAZETTEER`), regex postpositions (`से`, `तक`, `to`, `for`), RapidFuzz token matching, 4 static transport modes, and 23 facility keywords.
- Strengths: High precision on the 13 core CMRL stations.
- Deficiencies:
  - Does not scale to the 7,136 physical stops or 4,619 bus routes in `canonical_transport.db`.
  - Conflates span extraction with canonical entity resolution: if fuzzy matching selects a station ID, it replaces the span without tracking span boundaries, confidence, or alternate entity candidates.
  - Completely unaware of bus stop pole pairs, MRTS viaduct stations, suburban railway halts, or POIs.
  - No route number extraction logic.
  - No temporal extraction or normalization logic.
- Classification: DEPRECATE existing 13-station gazetteer and rigid postposition heuristic; ADAPT extractor into a two-layer architecture separating span extraction from canonical resolution.

### 3.3 Intent Classifier (`src/intent_classifier.py`)
- Implementation: Wraps TF-IDF Logistic Regression, HuggingFace AutoModelForSequenceClassification (MuRIL), and `RuleBasedFallbackClassifier`.
- Strengths: Clean class hierarchy (`BaseIntentClassifier`), clean inference interface returning `(intent, confidence)`.
- Deficiencies:
  - Hardcoded to the 7 CMRL intent classes.
  - Fallback classifier relies on brittle keyword sets tailored to metro queries.
  - Does not log per-token attention, calibrated probabilities, or out-of-scope confidence thresholds.
- Classification: ADAPT model loading and inference wrappers to accept arbitrary taxonomy configurations; DEPRECATE hardcoded 7-class keyword fallback for v2.

### 3.4 Transport Retrieval (`src/retrieval.py`)
- Implementation: Class `TransitRetriever` connecting to `data/processed/transport.db`.
- Deficiencies:
  - Connects to the obsolete 75-station demo database instead of `data/canonical/transit/canonical_transport.db`.
  - Schema in `data/processed/transport.db` (`stations`, `connections`, `facilities`, `service_info`) does not match the canonical relational schema (`transport_stops`, `route_stops`, `trips`, `stop_times`, `fares`, `interchanges`, `places`).
  - Does not support timetable queries, route stop sequences, or fare stage calculations.
- Classification: DEPRECATE `data/processed/transport.db` interface; ADAPT `TransitRetriever` to query the 20-table canonical multimodal SQLite database.

### 3.5 Pipeline Orchestrator (`src/pipeline.py`)
- Implementation: Class `TransportAssistant` executing `normalize -> classify -> extract -> retrieve -> generate`.
- Deficiencies:
  - Single monolithic path; cannot execute translation-pivot (Pipeline A), raw multilingual (Pipeline B), or normalized multilingual (Pipeline C).
  - Evaluates end-to-end output as a single opaque string rather than multi-layer structured outputs.
- Classification: ADAPT to support configurable pipeline strategies and structured intermediate layer outputs.

### 3.6 Response Generator (`src/response_generator.py`)
- Implementation: Class `ResponseGenerator` formatting deterministic Hindi text templates.
- Strengths: Factually grounded, zero hallucination of unsupported data, strict live-status refusal.
- Deficiencies:
  - Hindi only; does not support English or Hinglish output.
  - Templates assume metro-only responses.
- Classification: ADAPT to support multilingual response generation driven by canonical entity metadata.

### 3.7 Translation Module (`src/translator.py`)
- Implementation: NLLB-200 (`facebook/nllb-200-distilled-600M`) and static dictionary translating Hindi to Tamil for commuter-conductor assistance.
- Strengths: High-precision dictionary fallback for 47 transit terms.
- Deficiencies:
  - Built for outward passenger assistance, not for inward query translation pivot (Hinglish/Hindi to English).
  - Lacks entity protection masking and restoration logic.
- Classification: ADAPT translation architecture to support Pipeline A (entity-protected translation pivot).

### 3.8 Dataset Generation Scripts (`scripts/generate_intent_dataset.py`, `scripts/generate_multimodal_dataset.py`)
- Implementation:
  - `generate_intent_dataset.py`: Combines 35 station names with template strings into 5,204 rows. Hindi (55%) and Latin Hinglish (45%). No English.
  - `generate_multimodal_dataset.py`: Curated 100+ stations into `data/curated/chennai_multimodal_stations.json`.
- Deficiencies:
  - Combinatorial slot filling creates repetitive lexical patterns.
  - Does not model code-switch intensity (CS0 to CS4) or noise tiers (N0 to N5).
  - Lacks English queries.
  - Does not include bus routes, rail codes, POIs, or multi-stage fares.
- Classification: DEPRECATE for v2 dataset production; REUSE the family-disjoint splitting mathematical formulation in a clean, versioned v2 dataset generator.

### 3.9 Training and Benchmark Harness (`scripts/train_and_compare_models.py`, `scripts/benchmark_models.py`)
- Implementation: Multi-seed runner supporting BF16, AdamW, early stopping, per-seed evaluation, and markdown/JSON reporting.
- Strengths: Rigorous, reproducible, hardware-synchronized (`torch.cuda.synchronize()`), proper handling of seeds `[42, 101, 777, 1337, 2026]`.
- Deficiencies:
  - Hardcoded to the 7 v1 intents and single test set.
  - Does not log per-example prediction JSONL for paired statistical analysis (McNemar, bootstrap).
  - Does not evaluate slot extraction or entity resolution during benchmarking.
- Classification: REUSE the core training loop, optimizer configuration, and hardware synchronization; ADAPT to log per-example predictions and support multi-layer metrics.

---

## 4. Summary Component Decision Matrix

| Subsystem / File | Current Role | Quality Assessment | Proposed Action | Target v2 Role |
| :--- | :--- | :--- | :--- | :--- |
| `data/processed/split/*` | v1 70/15/15 dataset | Frozen, verified | **FREEZE** | Historical reference benchmark |
| `data/eval/acceptance_test_suite.json` | 149 gold queries | Frozen, verified | **FREEZE** | Historical reference gold suite |
| `docs/benchmarks/current_multi_seed_*` | v1 5-seed benchmark results | Authoritative | **FREEZE** | Historical incumbent to beat |
| `src/normalization.py` | Basic Unicode/Nuqta cleaner | Fast, but too simple | **ADAPT** | Pluggable normalization layers (Norm0 to Norm4) |
| `src/entity_extractor.py` | 13-station gazetteer + regex | Brittle, metro-only | **DEPRECATE / ADAPT** | Split into Span Extractor (NER) & Canonical Resolver |
| `src/intent_classifier.py` | MuRIL & TF-IDF wrapper | Solid wrapper, fixed intents | **ADAPT** | Taxonomy-agnostic classifier with confidence calibration |
| `src/retrieval.py` | Queries legacy `transport.db` | Obsolete schema (75 stns) | **DEPRECATE / ADAPT** | Connect to `canonical_transport.db` (20 relational tables) |
| `src/pipeline.py` | Monolithic end-to-end flow | Single path, opaque output | **ADAPT** | Multi-pipeline router (Pipelines A, B, C) with layered metrics |
| `src/response_generator.py` | Deterministic Hindi replies | Factually grounded, Hindi only | **ADAPT** | Multilingual response generator (EN, HI, Hinglish) |
| `src/translator.py` | NLLB-200 Hindi->Tamil | Built for commuter dialog | **ADAPT** | Entity-protected translation pivot for Pipeline A |
| `scripts/generate_intent_dataset.py` | Combinatorial v1 generator | Metro-only, no English | **DEPRECATE** | Replaced by `scripts/nlp_v2/generate_dataset.py` |
| `scripts/benchmark_models.py` | 5-seed benchmark runner | High rigor, BF16, synchronized | **REUSE / ADAPT** | Extend to log per-example predictions and layered metrics |
