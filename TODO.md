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

## Required before verified release
- [ ] Verify a bounded Metro inventory against exact source artifacts and record their terms/dates
- [ ] Correct conflated station identities and audit aliases against the verified inventory
- [ ] Replace/exclude all unverified demo records; then replace the unconditional demo warning with verified source metadata
- [ ] Author and manually review >=140 independent questions with complete gold slots and expected facts/refusals
- [ ] Reach PRD intent, slot, factual task-success and latency targets; publish measured results
- [x] Install pinned baseline/UI environment; check dependency consistency and Streamlit startup
- [ ] Add source-ingestion regression cases when actual external data is introduced

## Deferred
- [ ] MASSIVE acquisition, compatible loading and explicit label mapping (not currently integrated)
- [ ] MuRIL fine-tuning and fair baseline comparison
- [ ] Arbitrary routing, exact fares, service calendars/direction-aware departures
- [ ] Verified bus/suburban coverage, speech, translation and conversation memory

## Validation on 2026-09-17
- 37 regression tests passed, including specific facility absence, unknown data, split leakage and missing-model rejection.
- Baseline training and held-out-family evaluation ran: 808 unique synthetic questions, 436 train / 227 validation / 145 test; intent accuracy approximately 0.46 and Macro-F1 approximately 0.27.
- This result is below the PRD target. The tiny synthetic holdout is uneven (only one out-of-scope question); it is not a release benchmark. No factual end-to-end success claim is made.
- The experimental baseline was not retained as the UI default. The UI uses its labelled heuristic fallback until a suitable trained artifact is supplied.
- Full verified-data acquisition and independent human review remain outstanding; passing regressions does not satisfy those gates.
