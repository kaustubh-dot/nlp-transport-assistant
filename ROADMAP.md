# Project Roadmap: Hindi Multimodal Transport Assistant for Chennai

This roadmap outlines the multi-phase engineering and research trajectory for developing the zero-cost Hindi Natural Language Understanding (NLU) transport assistant for Chennai.

---

## High-Level Milestone Overview

```text
Q1: Foundation & Data ──► Q2: NLU Dataset & Seeds ──► Q3: Modeling (TF-IDF & MuRIL)
                                                                 │
Q6: Evaluation & Benchmarks ◄── Q5: UI & Multimodal Stubs ◄──────┴──► Q4: Retrieval & Response Engine
```

---

## Phase 1: Foundation, Infrastructure & Data Engineering (Sprint 1)
**Target Outcome**: Establish reproducible repository structure, dependency configurations, documentation, and the foundational SQLite transit knowledge base with multilingual gazetteers.

### Milestones & Deliverables
- [x] **Repo Scaffolding**: Setup modular directories (`app/`, `data/`, `models/`, `notebooks/`, `scripts/`, `src/`, `tests/`).
- [x] **Documentation & Schemas**: Author `README.md`, `ROADMAP.md`, `TODO.md`, `DATA_SOURCES.md`, `ARCHITECTURE.md`.
- [ ] **Dependency Setup**: Specify clean, reproducible environment in `requirements.txt` with PyTorch, Hugging Face, Scikit-learn, RapidFuzz, and Streamlit.
- [ ] **Transit Data Preprocessing**:
  - Download or parse open Chennai transit datasets (CMRL Metro Blue/Green lines, Southern Suburban Railway network, major MTC bus corridors).
  - Extract station geographical coordinates, line associations, and interchange nodes.
  - Compile station accessibility data (lifts, wheelchair accessibility, accessible ticketing, tactile paths).
- [ ] **Gazetteer & Alias Database**:
  - Build `data/processed/aliases.csv` mapping Hindi Devanagari (`चेन्नई सेंट्रल`), transliterated Hinglish (`chennai central`, `central`), and English variations to standardized canonical IDs (`CHENNAI_CENTRAL`).
- [ ] **SQLite Knowledge Base**:
  - Implement `scripts/build_transport_db.py` to generate `data/processed/transport.db` with relational tables (`stations`, `station_aliases`, `connections`, `facilities`, `service_info`).

---

## Phase 2: NLU Dataset Construction & Augmentation (Sprint 2)
**Target Outcome**: Generate a stratified, reproducible intent classification and entity slot dataset without paid APIs.

### Milestones & Deliverables
- [ ] **Seed Dataset Integration**:
  - Ingest Amazon MASSIVE Hindi split transport domain examples (`transport_query`, `transport_ticket`, `transport_taxi`) and general domain utterances for `out_of_scope` calibration.
- [ ] **Template Engineering**:
  - Design `data/templates/hindi_templates.json` containing authentic, colloquial, and formal query patterns for all 7 project intents:
    1. `route_query`
    2. `service_availability`
    3. `service_timing`
    4. `station_information`
    5. `accessibility`
    6. `ticketing`
    7. `out_of_scope`
- [ ] **Combinatorial Slot Expansion**:
  - Build `scripts/generate_intent_dataset.py` to deterministically substitute canonical stations, transport modes (`metro`, `bus`, `suburban_rail`), and information types into templates.
- [ ] **Hinglish & Roman Script Augmentation**:
  - Add Romanized Hindi representations (`egmore se airport metro milegi kya`) to ensure real-world robustness.
- [ ] **Stratified Dataset Partitioning**:
  - Export `data/processed/intents.csv` split into 70% Train, 15% Validation, and 15% Test sets with balanced class distributions.

---

## Phase 3: Intent Classification & Entity Extraction (Sprint 3)
**Target Outcome**: Build, train, and evaluate both baseline and transformer intent classifiers alongside a deterministic gazetteer slot extractor.

### Milestones & Deliverables
- [ ] **Text Normalization Engine**:
  - Implement `src/normalization.py` to clean Unicode variations, remove redundant diacritics, handle case folding, and strip trailing punctuation.
- [ ] **Gazetteer-Based Slot Extractor**:
  - Implement `src/entity_extractor.py` using dictionary lookups, regular expression patterns, and RapidFuzz token matching to extract `origin`, `destination`, `transport_mode`, and `information_type`.
- [ ] **Baseline Classifier**:
  - Develop `src/intent_classifier.py` using word n-gram (1-3) and character n-gram (2-5) TF-IDF features with L2-regularized Logistic Regression.
  - Save baseline artifacts in `models/baseline/`.
- [ ] **Transformer Model (MuRIL)**:
  - Implement fine-tuning pipeline for `google/muril-base-cased` using PyTorch and Hugging Face `Trainer`.
  - Train locally leveraging the NVIDIA RTX 4000 Ada GPU (20 GB VRAM).
  - Save checkpoints in `models/muril/`.
- [ ] **Model Comparison & Diagnostics**:
  - Implement `scripts/evaluate.py` to produce classification reports, Macro-F1 scores, and confusion matrix visualizations.

---

## Phase 4: Deterministic Retrieval Engine & Hindi Response Generation (Sprint 4)
**Target Outcome**: Connect classified intents and extracted slots to the SQLite database and construct factual, hallucination-free Hindi responses.

### Milestones & Deliverables
- [ ] **Transit Retrieval Engine**:
  - Implement `src/retrieval.py` to execute parameterized SQL lookups for:
    - Point-to-point route connectivity and line changes.
    - Direct mode availability checks.
    - First and last train/bus timings.
    - Station facilities and accessibility attributes.
    - Fare and ticketing guidelines.
- [ ] **Deterministic Response Generator**:
  - Implement `src/response_generator.py` with parameterized Hindi response templates for every valid scenario.
  - Formulate empathetic, clear fallback responses for missing slots ("आप कहाँ से यात्रा शुरू कर रहे हैं?"), unknown stations, and out-of-scope queries.
- [ ] **End-to-End Pipeline Orchestration**:
  - Create a unified `TransportAssistant` class coordinating `normalize() → predict_intent() → extract_slots() → retrieve_info() → generate_response()`.

---

## Phase 5: Streamlit Web UI & Multimodal Extension Stubs (Sprint 5)
**Target Outcome**: Interactive, passenger-friendly web application with inspection utilities and modular speech/translation extension hooks.

### Milestones & Deliverables
- [ ] **Streamlit Interface Development**:
  - Build `app/streamlit_app.py` with clean layout, quick-query chips, and interactive response cards.
  - Support both Hindi Devanagari input and Hinglish Roman text.
- [ ] **Developer & Inspection Mode**:
  - Provide an expandable diagnostics panel showing detected intent confidence score, extracted slots, SQL query executed, and execution latency.
- [ ] **Tamil Translation Stub**:
  - Modular integration point for IndicTrans2 to translate verified Hindi responses into Tamil for cross-state linguistic accessibility.
- [ ] **Speech Input / Output Hooks**:
  - Add browser-based Web Speech API input/output or IndicConformer/Indic-TTS stubs.

---

## Phase 6: Robustness Evaluation & Project Benchmarking (Sprint 6)
**Target Outcome**: Comprehensive empirical analysis answering the core research questions and validating task success rate.

### Milestones & Deliverables
- [ ] **Unit & Integration Test Suite**:
  - Comprehensive tests in `tests/` covering normalization, entity extraction accuracy, SQL queries, and edge cases.
- [ ] **Robustness Test Corpus**:
  - Benchmark system against 5 distinct linguistic subsets:
    1. Formal Hindi
    2. Colloquial Hindi
    3. Code-mixed Hindi-English
    4. Romanized Hindi
    5. Queries with station-name typos
- [ ] **End-to-End Success Rate**:
  - Calculate holistic metric: `Intent Correct ∧ Slots Correct ∧ DB Lookup Correct ∧ Response Factual`.
- [ ] **Documentation & Walkthrough**:
  - Prepare final walkthrough report with comparative tables, confusion matrices, and reproducible run instructions.
