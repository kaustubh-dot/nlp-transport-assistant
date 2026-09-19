# Chennai Multimodal Multilingual NLP v2 Master Task Specification (Phase N8)

Document: `docs/nlp_v2/nlp_v2_task_spec.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Reference Commit: `755f5754d9adb2ac7ea8358f5e7ae404ce942909`  
Date: 2026-09-19  
Status: Authoritative Consolidated Specification (Gate A Deliverable)

---

## 1. Executive Summary & Program Objective

The objective of the Chennai Multimodal Multilingual NLP v2 research program is to establish a rigorous, reproducible, and factually grounded conversational assistant across Chennai's public transport network. 

Following the completion of the multimodal data expansion phase (snapshot `chennai_multimodal_v1.2.1`), the transit knowledge base encompasses 7,136 physical stops, 4,619 routes, 1,360,635 stop times, and 1,562 official bus fare stages. The historical CMRL v1 benchmark (5,204 samples, 7 metro-only intents, 41 stations) is preserved intact as an immutable reference. 

This master task specification consolidates the research design produced across Phases N0 through N7 to govern all subsequent dataset synthesis, pilot testing, and model benchmarking.

---

## 2. Program Architecture & Separation of Concerns

The v2 conversational pipeline maintains strict boundaries between language understanding, knowledge retrieval, and dialogue generation:

```
+-------------------------------------------------------------------------+
| COMMUTER INPUT QUERY                                                    |
| (English, Hindi Devanagari, Roman Hindi, Hinglish, Mixed Script)        |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| PIPELINE ROUTER                                                         |
| - Pipeline A: Entity-Protected Translation Pivot (NLLB-200 -> EN Model) |
| - Pipeline B: Direct Multilingual Transformer (MuRIL, IndicBERT)        |
| - Pipeline C: Normalized Multilingual Transformer (Normalized Hinglish) |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| LAYER 1: INTENT CLASSIFIER                                              |
| Classifies query into approved intent (e.g. route_query, fare_query)    |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| LAYER 2 & 3: SPAN EXTRACTOR & CANONICAL RESOLVER                        |
| Extracts raw text spans and resolves to canonical IDs in SQLite         |
| (HUB_GUINDY, BUS_5822, ROUTE_MTC_102, FARE_MTC_ORDINARY)               |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| LAYER 4 & 5: STRUCTURED TRANSIT RETRIEVAL & SAFETY GATE                 |
| Queries canonical_transport.db (route_stops, stop_times, fares)         |
| Refuses unsupported requests (zero hallucination of live positions)     |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| LAYER 6: DETERMINISTIC MULTILINGUAL RESPONSE GENERATOR                  |
| Generates factual response in commuter's preferred language             |
+-------------------------------------------------------------------------+
```

---

## 3. Consolidation of Phase Specifications

### 3.1 Immutable V1 Benchmark Reference (Phase N0)
- Preserved Files: `data/processed/split/train.csv` (3,916), `validation.csv` (716), `test.csv` (572), `data/eval/acceptance_test_suite.json` (149 queries).
- Historical Benchmark Incumbent: Google MuRIL (`google/muril-base-cased`): Test Macro-F1 = `0.8927 ± 0.0226`, Accuracy = `90.49% ± 1.86%`, Best Epoch = 5.
- Component Decisions: Normalization (ADAPT), Entity Extractor (DEPRECATE / ADAPT), Intent Classifier (ADAPT), Retrieval (DEPRECATE legacy DB / ADAPT to canonical DB).
- Reference Document: `reports/nlp_v2/current_nlp_audit.md`.

### 3.2 Canonical Knowledge Base Answerability Contract (Phase N1)
- Data Foundation: `data/canonical/transit/canonical_transport.db` (20 relational tables, 81.27 MB).
- Answerability Rules:
  - `ANSWERABLE_NOW`: Confirmed CMRL metro topology, official MTC stage tariffs, Southern Railway station codes.
  - `ANSWERABLE_WITH_PROVISIONAL_DATA`: GTFS representative longest-trip route stops, static timetables, 579 matched bus stages.
  - `ANSWERABLE_AFTER_ROUTING_GRAPH`: Multimodal transfer paths, POI spatial proximity.
  - `ANSWERABLE_AFTER_MANUAL_VERIFICATION`: 45 candidate interchanges, 151 walking transfers (`confirmed=0`).
  - `REQUIRES_REALTIME_DATA`: Live vehicle positions, live delays, crowd levels (Strict refusal required).
  - `NOT_CURRENTLY_SUPPORTED`: Gate numbers, suburban platform allocations, bus stop accessibility.
  - `OUT_OF_SCOPE`: Non-CMA transit, ride-hailing cabs, flights, weather.
- Reference Documents: `reports/nlp_v2/kb_answerability_audit.md`, `docs/nlp_v2/answerability_matrix.md`.

### 3.3 Intent Taxonomy Alternatives (Phase N2)
- T1 (Broad: 9 Intents): Coarse goals, high sample efficiency, extensive slot delegation.
- T2 (Medium: 12 Intents - Recommended): Separate fare calculation from ticketing rules; dedicated interchange intent; explicit live-status refusal intent.
- T3 (Fine: 16 Intents): Highly fine-grained, high risk of boundary confusion.
- Reference Document: `docs/nlp_v2/intent_taxonomy_candidates.md`.

### 3.4 Typed Slot Schema & Entity Resolution (Phase N3)
- Typed Slots: `origin`, `destination`, `station`, `landmark`, `route_number`, `transport_mode`, `timing_type`, `time`, `facility_type`, `accessibility_feature`, `ticket_type`.
- Contract Matrix: Enforces `REQ`, `OPT`, `CONDITIONAL`, and `FORBIDDEN` rules.
- Ambiguity Policy: Disambiguates between multimodal hubs (`HUB_GUINDY`) and modal station nodes (`METRO_GUINDY_9011`, `RAIL_GUINDY`).
- Normalization Rules: Strict retention of route suffixes (`102A` never truncated to `102`); explicit handling of Hindi `कल` ambiguity.
- Reference Documents: `docs/nlp_v2/slot_schema.md`, `docs/nlp_v2/entity_resolution_contract.md`.

### 3.5 Language & Robustness Framework (Phase N4)
- 5 Language Classes: `EN` (25%), `HI_DEVA` (25%), `HI_LATN` (15%), `HINGLISH_LATN` (25%), `MIXED_SCRIPT_CS` (10%).
- 5 Code-Switch Tiers: `CS0` (pure monolingual) to `CS4` (heavy intra-sentential mixed script).
- 6 Noise Tiers: `N0` (canonical) to `N5` (severe human-interpretable chat abbreviations).
- Surface Noise Invariant: Raw noise preserved in benchmark queries; normalization evaluated as pipeline module.
- Reference Document: `docs/nlp_v2/language_and_robustness_spec.md`.

### 3.6 Dataset Generation & Leakage Policy (Phases N5 & N6)
- Hierarchy: `semantic_family_id` -> `family_id` -> `paraphrase_group_id` -> `utterance_id`.
- Primary Partition: 70% train / 15% validation / 15% test (Seed 42).
- Zero Leakage Invariant: 100% semantic family disjointness across train, validation, and test.
- Challenge Partitions: `challenge_unseen_pairs` (unseen origin-destination pairs) and `challenge_unseen_aliases` (unseen transliterated aliases).
- Secondary Sensitivity: 3 alternate split seeds (`101`, `777`, `1337`) evaluated on finalists.
- Reference Documents: `docs/nlp_v2/dataset_contract.md`, `docs/nlp_v2/split_and_leakage_policy.md`.

### 3.7 Evaluation Protocol & Preregistration (Phase N7)
- 6 Evaluation Layers: Intent Macro-F1, Slot BIO F1, Top-1/Top-3 Entity Accuracy, Routing Graph Correctness, Task Success Rate, Response Grounding.
- Model Selection Funnel: 5-stage pre-registered gating protocol.
- Seed Discipline: Core 5 seeds (`[42, 101, 777, 1337, 2026]`).
- Statistical Testing: Paired bootstrap confidence intervals and McNemar significance tests.
- Reference Documents: `docs/nlp_v2/evaluation_protocol.md`, `docs/nlp_v2/experimental_preregistration.md`.

---

## 4. Open Decisions Requiring User Approval

Before the research program advances past Gate A into Gate B (Taxonomy Pilot Implementation), the user must review and approve three key methodological decisions:

### Decision 1: Taxonomy Selection Strategy for Gate B
- **Question**: Should we run a comparative pilot study evaluating all three taxonomies (T1 Broad, T2 Medium, T3 Fine), or approve T2 directly?
- **Option A (Recommended)**: Conduct a controlled empirical pilot study training TF-IDF and MuRIL across small synthetic datasets (~2,000 samples each) for T1, T2, and T3 to quantitatively measure boundary confusion and learnability before generating the large corpus.
- **Option B**: Formally adopt Taxonomy T2 (Medium, 12 intents) directly and proceed to full dataset generation without piloting T1 and T3.
- **Option C**: Adopt Taxonomy T1 (Broad, 9 intents) directly.

### Decision 2: Handling of Unsupported Real-Time Queries
- **Question**: How should requests for live bus tracking, delays, and vehicle positions be handled in the NLU layer?
- **Option A (Recommended)**: Formalize `unsupported_live_status` as an explicit in-domain intent class in Taxonomy T2, enabling deterministic, helpful commuter explanations ("Live GPS tracking is unavailable; scheduled departure is 17:15").
- **Option B**: Fold all real-time tracking requests into a generic `out_of_scope` rejection class.
- **Option C**: Filter real-time queries using deterministic regex keyword matching prior to model inference.

### Decision 3: Initial Pilot Dataset Scale
- **Question**: What sample size should be used for the Gate B taxonomy pilot?
- **Option A (Recommended)**: 2,000 samples per candidate taxonomy (6,000 total pilot queries), evaluated across Seeds `[42, 101]` on TF-IDF and MuRIL.
- **Option B**: 5,000 samples per candidate taxonomy (15,000 total queries).
- **Option C**: 1,000 samples per candidate taxonomy (3,000 total queries).

---

## 5. Next Program Phase (Gate B)

Upon user review of `DECISION_REQUIRED.md` and approval of Gate A deliverables, the next execution step is **Phase P1: Taxonomy Pilot Implementation**:
1. Implement pilot utterance generators for the candidate taxonomies.
2. Generate controlled pilot datasets.
3. Train baseline TF-IDF and Google MuRIL models.
4. Deliver `reports/nlp_v2/taxonomy_pilot_results.md` comparing Macro-F1, per-class confusion matrices, and learnability to lock the final intent taxonomy.
