# Chennai Multimodal Multilingual NLP v2 Master Task Specification (Phase N8)

Document: `docs/nlp_v2/nlp_v2_task_spec.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Reference Commit: `755f5754d9adb2ac7ea8358f5e7ae404ce942909`  
Database Structure: 19 application tables + SQLite internal `sqlite_sequence`  
Date: 2026-09-19  
Status: Authoritative Consolidated Specification (Gate A Deliverable, Corrected Methodology Patch)

---

## 1. Executive Summary & Program Objective

The objective of the Chennai Multimodal Multilingual NLP v2 research program is to establish a rigorous, reproducible, and factually grounded conversational assistant across Chennai's public transport network. 

Following the completion of the multimodal data expansion phase (snapshot `chennai_multimodal_v1.2.1`), the transit knowledge base encompasses 7,136 physical stops, 4,619 routes, 1,360,635 stop times, and 1,562 official bus fare stages stored across 19 application tables in `canonical_transport.db` (81.27 MB SQLite). The historical CMRL v1 benchmark (5,204 samples, 7 metro-only intents, 41 stations) is preserved intact as an immutable reference.

This master task specification consolidates the research design produced across Phases N0 through N7 and incorporates the Gate A methodology corrections to govern all subsequent dataset synthesis, pilot testing, and model benchmarking.

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
| Refuses realtime_status_query (zero hallucination of live positions)    |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| LAYER 6: DETERMINISTIC MULTILINGUAL RESPONSE GENERATOR                  |
| Generates factual response in commuter's preferred language             |
+-------------------------------------------------------------------------+
```

---

## 3. Consolidation of Phase Specifications & Methodology Corrections

### 3.1 Immutable V1 Benchmark Reference (Phase N0)
- Preserved Files: `data/processed/split/train.csv` (3,916), `validation.csv` (716), `test.csv` (572), `data/eval/acceptance_test_suite.json` (149 queries).
- Historical Incumbent: Google MuRIL (`google/muril-base-cased`): Test Macro-F1 = `0.8927 ± 0.0226`, Accuracy = `90.49% ± 1.86%`, Best Epoch = 5.
- Component Decisions: Normalization (ADAPT), Entity Extractor (DEPRECATE / ADAPT), Intent Classifier (ADAPT), Retrieval (DEPRECATE legacy DB / ADAPT to canonical DB).
- Reference Document: [current_nlp_audit.md](file:///home/ug3aidsstudents/projects/NLP/reports/nlp_v2/current_nlp_audit.md).

### 3.2 Canonical Knowledge Base Answerability Contract (Phase N1)
- Data Foundation: `canonical_transport.db` (19 application tables + `sqlite_sequence`, 81.27 MB).
- Answerability Rules:
  - `ANSWERABLE_NOW`: Confirmed CMRL metro topology, official MTC stage tariffs G.O. Ms 48, Metro station parking availability (`accessibility.parking_available`).
  - `ANSWERABLE_WITH_PROVISIONAL_DATA`: GTFS representative longest-trip route stops, static timetables, 579 matched bus stages, CMRL distance-tier fare calculation, direct coordinate spatial proximity lookups (`places`, `transport_stops`).
  - `ANSWERABLE_AFTER_ROUTING_GRAPH`: Multimodal transfer pathfinding across graph edges, pedestrian walkable network routing.
  - `ANSWERABLE_AFTER_MANUAL_VERIFICATION`: 45 candidate interchanges, 151 walking transfers (`confirmed=0`).
  - `REQUIRES_REALTIME_DATA`: Live vehicle positions, live delays, crowd levels (Intent: `realtime_status_query`; deterministic refusal required).
  - `NOT_CURRENTLY_SUPPORTED`: Gate numbers, suburban platform allocations, bus stop accessibility, general commercial amenities (cloak rooms, ATMs, Wi-Fi, waiting rooms), direct Southern Railway station code lookups.
  - `OUT_OF_SCOPE`: Non-CMA transit, ride-hailing cabs, flights, weather.
- Reference Documents: [kb_answerability_audit.md](file:///home/ug3aidsstudents/projects/NLP/reports/nlp_v2/kb_answerability_audit.md), [answerability_matrix.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/answerability_matrix.md).

### 3.3 Intent Taxonomy Alternatives & Pilot Governance (Phase N2)
- T1 (Broad: 9 Intents): Coarse goals, high sample efficiency, extensive slot delegation. Real-time inquiries pooled in `out_of_scope`.
- T2 (Medium: 12 Intents): Separates fare calculation from ticketing rules; dedicated interchange intent; semantic `realtime_status_query` intent evaluated for safe refusal.
- T3 (Fine: 16 Intents): Atomic capabilities, higher boundary overlap.
- Gate B Pilot Fairness: Evaluated under **Regime A** (Equal Total Data: ~5,000 samples each) and **Regime B** (Equal Samples Per Class: ~500 samples/intent) across pilot seeds `[42, 101, 777]`, totaling **36 model-training runs** (3 taxonomies × 2 regimes × 2 model families × 3 seeds = 36 runs; 18 runs per model family). Taxonomy is frozen only after Gate B comparison.
- Reference Document: [intent_taxonomy_candidates.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/intent_taxonomy_candidates.md).

### 3.4 Canonical Slot Schema & Ambiguity Rules (Phase N3)
- Canonical Slots: Exactly **23 canonical slots** (`origin`, `destination`, `via`, `station`, `stop`, `landmark`, `locality`, `route_number`, `line_name`, `transport_mode`, `mode_from`, `mode_to`, `preference`, `timing_type`, `time`, `temporal_relative`, `date`, `ticket_type`, `fare_type`, `stage_number`, `service_type`, `facility_type`, `accessibility_feature`).
- Strict Zero-Default Ambiguity Rules:
  - Bare time expressions (`8 baje`, `8 बजे`): Dual candidates `["08:00:00", "20:00:00"]` preserved with `temporal_ambiguity = true`. No silent morning defaulting.
  - Hindi `कल / kal`: Resolved to `+1` or `-1` **only** under unambiguous grammatical tense/aspect evidence. In neutral contexts, emits `UNRESOLVED_TEMPORAL_AMBIGUITY` requiring dialogue clarification.
- Route Numbers: Strict preservation of alphanumeric suffixes (`102A` never truncated to `102`).
- Reference Documents: [slot_schema.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/slot_schema.md), [entity_resolution_contract.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/entity_resolution_contract.md).

### 3.5 Language & Robustness Framework (Phase N4)
- 5 Language Classes: `EN` (25%), `HI_DEVA` (25%), `HI_LATN` (15%), `HINGLISH_LATN` (25%), `MIXED_SCRIPT_CS` (10%) (starting proposal; explicitly parameterized in language-mix experiments).
- 5 Code-Switch Tiers: `CS0` (monolingual) to `CS4` (heavy intra-sentential mixed script).
- 6 Noise Tiers: `N0` (canonical) to `N5` (severe human-interpretable chat abbreviations).
- Surface Noise Invariant: Raw noise preserved in benchmark queries; normalization evaluated as pipeline module.
- Reference Document: [language_and_robustness_spec.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/language_and_robustness_spec.md).

### 3.6 Dataset Generation, Challenge Isolation & Leakage Policy (Phases N5 & N6)
- Hierarchy: `semantic_family_id` -> `family_id` -> `paraphrase_group_id` -> `utterance_id`.
- Primary Partition: 70% train / 15% validation / 15% test (Seed 42), strictly semantic-family-disjoint.
- Controlled Challenge Sets:
  - `challenge_unseen_pairs`: Isolates unseen origin-destination pairs while permitting known training families.
  - `challenge_unseen_aliases`: Isolates unseen alias forms while permitting known training families.
  - Optional `challenge_hard_*` sets simultaneously isolate syntactic families and entity conditions.
- Out-of-Scope Entity Rule: Out-of-scope queries may legitimately contain transit entities; entity annotations must be preserved.
- Secondary Sensitivity: 3 alternate split seeds (`101`, `777`, `1337`) evaluated on finalists.
- Reference Documents: [dataset_contract.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/dataset_contract.md), [split_and_leakage_policy.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/split_and_leakage_policy.md).

### 3.7 Evaluation Protocol & Preregistration (Phase N7)
- 6 Evaluation Layers: Intent Macro-F1, Slot BIO F1, Top-1/Top-3 Entity Accuracy, Routing Graph Correctness, Task Success Rate, Response Grounding.
- Model Registry: Google MuRIL (`google/muril-base-cased`), AI4Bharat IndicBERT v2 (`ai4bharat/IndicBERTv2-MLM-only`), Multilingual MiniLM, Meta XLM-RoBERTa, L3Cube HingBERT, and Microsoft mDeBERTa-v3.
- Hyperparameter Reproducibility: 8 trials per model selected via deterministic random search with fixed seed `42`.
- Statistical Testing Discipline: Within the same taxonomy, matched per-example paired McNemar and bootstrap testing is valid; across different taxonomies, models are compared via Macro-F1, confusion matrices, and downstream semantic-operation correctness (raw cross-taxonomy McNemar is invalid across differing label spaces unless projected onto a common semantic space).
- Final Test Discipline: Development -> Finalist Freeze -> Final Test -> Gold Acceptance.
- Coverage-Based Gold Suite: $\ge 10$ independently authored cases per intent $\times$ 5 language classes ($\ge 600$ cases for T2).
- Reference Documents: [evaluation_protocol.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/evaluation_protocol.md), [experimental_preregistration.md](file:///home/ug3aidsstudents/projects/NLP/docs/nlp_v2/experimental_preregistration.md).

---

## 4. Open Decisions Requiring User Approval

Before the research program advances past Gate A into Gate B (Taxonomy Pilot Implementation), the user must review and approve three key methodological decisions documented in [DECISION_REQUIRED.md](file:///home/ug3aidsstudents/projects/NLP/DECISION_REQUIRED.md):

1. **Taxonomy Pilot Execution (Gate B)**:
   Conduct controlled empirical comparison across T1 (Broad), T2 (Medium), and T3 (Fine) under Regime A (Equal Total Data ~5k) and Regime B (Equal Samples Per Class ~500/intent) using TF-IDF and MuRIL on pilot seeds `[42, 101, 777]`.
2. **Real-Time Intent Semantics**:
   Adopt semantic intent `realtime_status_query` (with capability state `answerability_status = REQUIRES_REALTIME_DATA`) in T2/T3, evaluated for safe deterministic refusal without live tracking.
3. **Pilot Evaluation Scope**:
   Confirm pilot datasets will use pilot seeds `[42, 101, 777]` without inspecting the frozen v2 test set.
