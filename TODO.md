# Project TODO & Task Tracker

This living task list tracks the implementation status of the **Hindi Multimodal Transport Assistant for Chennai Using NLP**.

---

## Progress Dashboard

| Phase | Description | Status | Priority | Target Completion |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Foundation, Infrastructure & Data Engineering | 🔄 In Progress | Critical | Sprint 1 |
| **Phase 2** | NLU Dataset Construction & Augmentation | ⏳ Scheduled | High | Sprint 2 |
| **Phase 3** | Intent Classification & Entity Extraction | ⏳ Scheduled | High | Sprint 3 |
| **Phase 4** | Retrieval Engine & Hindi Response Generation | ⏳ Scheduled | High | Sprint 4 |
| **Phase 5** | Streamlit Web Application & Multimodal Stubs | ⏳ Scheduled | Medium | Sprint 5 |
| **Phase 6** | Comprehensive Evaluation & Benchmarks | ⏳ Scheduled | Medium | Sprint 6 |

---

## Phase 1: Foundation, Infrastructure & Data Engineering

### Repository & Scaffolding
- [x] Create directory structure (`app/`, `data/`, `models/`, `notebooks/`, `scripts/`, `src/`, `tests/`)
- [x] Author core documentation (`README.md`, `ROADMAP.md`, `TODO.md`, `DATA_SOURCES.md`, `ARCHITECTURE.md`)
- [ ] Create `requirements.txt` with pinned open-source dependencies
- [ ] Create `.gitignore` for Python, PyTorch weights, SQLite databases, and virtualenvs
- [ ] Create open-source `LICENSE` (MIT)

### Data Engineering & SQLite Knowledge Base
- [ ] Define relational SQLite schema in `scripts/build_transport_db.py`:
  - `stations` (station_id, name_en, name_hi, name_ta, type, lat, lon)
  - `station_aliases` (station_id, alias, language, script)
  - `connections` (origin_id, destination_id, mode, line_name, travel_time_mins, distance_km)
  - `facilities` (station_id, wheelchair_available, lift_available, tactile_paths, accessible_toilet, parking)
  - `service_info` (route_id, mode, line_name, first_service, last_service, frequency_mins, fare_min, fare_max)
- [ ] Compile comprehensive station gazetteer for:
  - CMRL Metro (Blue Line: Wimco Nagar to Airport; Green Line: Central to St. Thomas Mount)
  - Chennai Suburban Rail (Central-Arakkonam, Beach-Tambaram-Chengalpattu, Beach-Velachery MRTS)
  - Major interchange transit terminals (Chennai Central, Egmore, CMBT Koyambedu, Guindy, Airport)
- [ ] Build alias mapping table `data/processed/aliases.csv` (Hindi Devanagari, English, Roman Hinglish, colloquial short names)
- [ ] Execute `scripts/build_transport_db.py` and verify `data/processed/transport.db` integrity

---

## Phase 2: NLU Dataset Construction & Augmentation

### Template & Seed Corpus
- [ ] Create `data/templates/hindi_templates.json` covering:
  - `route_query` (e.g. `{origin} से {destination} कैसे जाएँ?`, `{origin} to {destination} route`)
  - `service_availability` (e.g. `{origin} से {destination} के लिए {mode} उपलब्ध है क्या?`)
  - `service_timing` (e.g. `{origin} से आखिरी {mode} कब चलती है?`, `{mode} operating timings`)
  - `station_information` (e.g. `{station} पर क्या सुविधाएं हैं?`, `interchange options at {station}`)
  - `accessibility` (e.g. `{station} पर व्हीलचेयर मिलेगी?`, `lift and ramps at {station}`)
  - `ticketing` (e.g. `{origin} से {destination} का किराया कितना है?`, `metro smart card recharge rules`)
  - `out_of_scope` (weather, sports, general knowledge, food queries)
- [ ] Download Amazon MASSIVE Hindi split transport seed utterances into `data/raw/massive/`
- [ ] Build `scripts/generate_intent_dataset.py`:
  - Deterministic slot substitution with combinatorial coverage
  - Script transliteration & Hinglish augmentation
  - Balanced class generation for all 7 intents
  - Train/Val/Test stratification (70/15/15)
- [ ] Export `data/processed/intents.csv` and verify label distributions

---

## Phase 3: Intent Classification & Entity Extraction

### Text Normalization & Slot Extraction
- [ ] Build `src/normalization.py`:
  - Unicode NFC/NFKD normalization
  - Hindi punctuation removal (Purna Viram `।`, exclamation, question marks)
  - Case folding for Roman text
  - Redundant whitespace compression
- [ ] Build `src/entity_extractor.py`:
  - Gazetteer lookup with longest-match substring matching
  - Regex pattern matching for transport modes (`मेट्रो`, `बस`, `ट्रेन`, `लोकल`)
  - RapidFuzz token matching for misspelled station names
  - Slot extraction for `origin`, `destination`, `transport_mode`, `information_type`

### Classification Models
- [ ] Implement baseline classifier in `src/intent_classifier.py`:
  - `TfidfVectorizer` (word n-grams 1-3 + char n-grams 2-5)
  - `LogisticRegression(max_iter=1000, class_weight='balanced')`
  - Model serialization into `models/baseline/`
- [ ] Implement MuRIL transformer classifier:
  - Hugging Face `AutoTokenizer` and `AutoModelForSequenceClassification` (`google/muril-base-cased`)
  - PyTorch training loop / Hugging Face `Trainer` configured for local RTX 4000 Ada GPU
  - Evaluation on validation set with early stopping
  - Save fine-tuned checkpoint in `models/muril/`
- [ ] Build evaluation script `scripts/evaluate.py`:
  - Precision, Recall, Macro-F1, Accuracy
  - Confusion matrix generation and visualization

---

## Phase 4: Retrieval Engine & Hindi Response Generation

### Transit Query Logic & Response Formatting
- [ ] Build `src/retrieval.py`:
  - `query_route(origin_id, destination_id)`
  - `check_availability(origin_id, destination_id, mode)`
  - `get_service_timing(station_id, mode, direction)`
  - `get_station_facilities(station_id, facility_type)`
  - `get_fare_and_ticketing(origin_id, destination_id, mode)`
- [ ] Build `src/response_generator.py`:
  - Deterministic Hindi templates for successful queries
  - Helpful clarifying responses for missing `origin` or `destination`
  - Fallback responses for unknown stations
  - Graceful rejection messages for `out_of_scope` queries
  - Informative denial for unsupported live tracking/delays
- [ ] Build integrated pipeline in `src/pipeline.py` combining normalizer, classifier, extractor, retriever, and response generator

---

## Phase 5: Streamlit Web UI & Multimodal Stubs

### User Interface & Extensibility
- [ ] Build `app/streamlit_app.py`:
  - Clean conversational layout with custom CSS
  - Sample prompt buttons ("चेन्नई सेंट्रल से एयरपोर्ट", "कोयम्बेडु पर व्हीलचेयर", etc.)
  - Clear multi-pane display:
    - Input & Normalized Query
    - Predicted Intent (with confidence meter)
    - Extracted Slots (Origin, Destination, Mode)
    - Database Lookup Summary
    - Final Hindi Response
- [ ] Add Developer / Inspection Drawer:
  - Raw SQL query inspection
  - Fuzzy match score breakdown
  - Alternative mode suggestions
- [ ] Add Optional Multimodal Stubs:
  - IndicTrans2 Hindi-to-Tamil translation toggle button
  - Browser Speech-to-Text / Text-to-Speech audio controls

---

## Phase 6: Robustness Evaluation & QA

### Testing & Research Deliverables
- [ ] Write unit tests:
  - `tests/test_normalization.py`
  - `tests/test_entity_extractor.py`
  - `tests/test_retrieval.py`
  - `tests/test_pipeline.py`
- [ ] Execute robustness test suite across:
  - Formal Hindi queries
  - Colloquial Hindi
  - Code-mixed Hinglish
  - Roman script queries
  - Typo-injected queries
- [ ] Measure and report **End-to-End Task Success Rate**:
  - `Intent Correct ∧ Entities Correct ∧ SQL Lookup Correct ∧ Response Valid`
- [ ] Generate comprehensive walkthrough report and comparison table: Baseline TF-IDF vs MuRIL
