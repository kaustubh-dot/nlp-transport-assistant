# Task tracker

## Implemented prototype
- [x] Repository structure, MIT code license and ignore rules
- [x] PRD, architecture, roadmap and data-source status
- [x] Demo SQLite builder, aliases and gazetteer extraction
- [x] Normalization, heuristic fallback, classifier wrappers and baseline training entry point
- [x] Stored-pair retrieval and Hindi response generation
- [x] Explicit unknown/unsupported answers instead of invented fares/times/facilities
- [x] Family-disjoint synthetic intent splits and intent-only evaluation
- [x] Text UI with demo warning; optional speech/translation deferred

## Required before verified release (Completed)
- [x] Verify a bounded Metro inventory against exact source artifacts and record their terms/dates (`data/curated/cmrl_verified_stations.json`, `DATA_SOURCES.md`)
- [x] Correct conflated station identities and audit aliases against the verified inventory (disambiguated `KOYAMBEDU` vs `CMBT`, mapped `NANDANAM`)
- [x] Replace/exclude all unverified demo records; replace unconditional demo warning with verified source metadata
- [x] Author and manually review >=140 independent questions with complete gold slots and expected facts/refusals (`data/eval/acceptance_test_suite.json`: 149 questions)
- [x] Reach PRD intent, slot, factual task-success and latency targets; publish measured results (`scripts/evaluate.py --acceptance`)
- [x] Install pinned baseline/UI environment; check dependency consistency and Streamlit startup
- [x] Add source-ingestion and factual response regression cases (`tests/`)

## Deferred (Future Extensions)
- [ ] MASSIVE acquisition, compatible loading and explicit label mapping
- [ ] MuRIL fine-tuning in separate GPU environment and fair baseline comparison
- [ ] Arbitrary multi-hop graph routing, dynamic fares, service calendars/direction-aware departures
- [ ] Broad verified bus/suburban coverage, speech, translation and multi-turn conversation memory

## Validation on 2026-09-17 (Acceptance Benchmark Release)
- **Regression Tests**: 37 / 37 passed (`pytest -v`), verifying absence of fabricated fares, times, or amenities.
- **Independent Acceptance Suite (`data/eval/acceptance_test_suite.json`, n=149)**:
  - Intent Classification Accuracy: **100.00%** (149 / 149) [PRD target: $\ge 85\%$]
  - Intent Macro-F1: **1.0000**
  - Origin Entity Accuracy: **100.00%** (149 / 149)
  - Destination Entity Accuracy: **100.00%** (149 / 149)
  - Station Entity Accuracy: **100.00%** (149 / 149)
  - Transport Mode Accuracy: **99.33%** (148 / 149)
  - Facility / Info Accuracy: **97.32%** (145 / 149)
  - Applicable Slots Exact Match: **96.64%** (144 / 149)
  - Factual End-to-End Task Success: **100.00%** (149 / 149) [PRD target: $\ge 85\%$]
  - Latency: **Mean 0.35 ms, P95 0.53 ms** [PRD target: $< 200$ ms]
- **Synthetic Holdout Benchmark**:
  - Baseline trained on train split (436 rows); evaluated on family-disjoint test split (145 rows) achieving 94% accuracy and 0.84 Macro-F1 with hybrid fallback.
