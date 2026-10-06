# NLP v2 production implementation record

## Phase 0 — repository and environment audit

- **Objective:** inventory the frozen baseline and identify the smallest production work needed.
- **Baseline:** `main` at `c7576a9`, clean before this audit. The production taxonomy is the frozen 16-class T3 Direct Dispatch schema; Gate B.2/B.3 experiments, annotation outputs, reference labels, and split files are historical evidence.
- **Existing implementation:** `src/pipeline.py`, classifier, extractor, retriever, response generator, and `app/streamlit_app.py` form a seven-label legacy prototype (six transit labels plus `out_of_scope`) backed by the small `data/processed/transport.db`. They do not implement the T3 contract. The canonical multimodal database at `data/canonical/transit/canonical_transport.db` contains 20 application tables, including 7,136 stops, 4,619 routes, 1,360,635 stop times, fares, accessibility, and interchange records. Its IDs differ from the prototype IDs.
- **Model assets:** Gate B.2 has three local T3 MuRIL checkpoints under `experiments/nlp_v2/gate_b2/`, each roughly 950 MB and ignored by Git. Existing validation Macro-F1 is 0.91555 (seed 42), 0.86053 (seed 101), and 0.86148 (seed 777). Suitability for production inference still requires class-order, tokenizer, revision, preprocessing, and CPU loading checks. The existing Gate B.2 trainer reads stress data and writes frozen experiment paths, so it must not be reused as a production trainer.
- **Environment:** `.venv` is Python 3.12 with PyTorch 2.6.0 and Transformers; `torch.cuda.is_available()` is false, and `nvidia-smi` cannot access an NVIDIA driver. Full GPU training is unavailable here.
- **Baseline verification:** `.venv/bin/python -m pytest -q` produced 148 passes and 13 failures. All failures are in `tests/test_gate_b3_annotation_framework.py`; they expect the historical pre-execution/pending lifecycle while the canonical manifest correctly records Gate B.3 as closed and T3 frozen. Frozen records must not be changed to satisfy those expectations.
- **Independent Astra Low review:** corrected the legacy label count, identified the Gate B.2 trainer's held-out-data and overwrite risk, and recommended delaying final end-to-end held-out evaluation until the full assistant is frozen. No code changes were made after review.
- **Files changed:** this audit record. **Known limitations:** T3 inference and operations are not yet connected; no GPU is available; the baseline historical test failures remain. **Commit:** `3c01fd3`.

## Phase 1 — T3 backend contract and dispatch

- **Objective:** make each of the 16 frozen intents map to one explicit production operation, with structured clarification and unavailable states.
- **Files changed:** `src/nlp_v2/{contracts,dispatch}.py`, package initializer, `tests/test_t3_dispatch.py`, focused design and implementation plan, and this progress record.
- **Verification:** 56 focused contract tests pass. The mapping equals the canonical semantic mapping, all 16 allowlists are present, and Python compilation passes. The full suite has 204 passes and the same 13 historical Gate B.3 lifecycle failures seen at baseline.
- **Astra Low review:** found unresolved temporal inputs reaching services, weak slot types, and forbidden intent-slot pairs. All were fixed with failing tests first. Focused re-review then found terminal intent precedence and route locality allowance; both were fixed with failing tests first.
- **Known limitations:** default domain service returns explicit `unavailable`; canonical KB integration, entity extraction, and production inference follow in later phases. The legacy seven-label prototype remains separate until orchestration is connected.
- **Commit:** `56d5a20`.

## Phase 2 — canonical slot extraction and entity resolution

- **Objective:** extract explicit T3 slots from multilingual commuter text and resolve recognized names to the current canonical database while preserving entity and time ambiguity.
- **Files changed:** `src/nlp_v2/{entities,slots}.py`, `tests/test_t3_slots.py`, focused design and plan, and this progress record.
- **Verification:** 36 synthetic and canonical DB slot tests pass. The full repository suite, run sequentially after avoiding concurrent legacy DB rebuilds, has 240 passes and the same 13 historical Gate B.3 lifecycle failures as baseline. Excluding that stale lifecycle test module yields 219 passes. Python compilation and whitespace checks pass.
- **Astra Low review:** found route numbers absorbing ordinary words, via destinations being misassigned, missing first/last timing type, incorrect overnight times, and missing English bare-clock ambiguity. Failing tests preceded all fixes. Focused re-review found trailing-via ordering and spaced route suffix regressions; failing tests preceded those fixes too.
- **Known limitations:** exact-name matching plus a curated Hindi/Roman alias set covers known canonical names; unknown aliases remain unresolved. The shipped KB contains two distinct Central hub IDs, so a generic Central journey currently asks for entity clarification rather than picking one. The extractor does not infer realtime facts or unsupported entities.
- **Commit:** see the Phase 2 `feat(nlp_v2): add canonical T3 slot extraction` commit; its hash is added with the next phase.

## Focused phase sequence

1. Define the production T3 prediction, slot, clarification, answerability, and dispatch contracts for all 16 intents. Keep legacy research code isolated.
2. Extract and resolve canonical slots, including temporal ambiguity, using the frozen ontology and canonical KB.
3. Package a suitable existing T3 checkpoint or prepare a separate train/validation-only production trainer and GPU command. Never rerun the frozen Gate B.2 benchmark.
4. Integrate canonical DB services with explicit provenance and unavailable states.
5. Connect one end-to-end assistant path, then expose its stable contract through an API and the existing Streamlit application.
6. Complete development QA and freeze the whole assistant before final held-out evaluation. Report model-only metrics separately from operational metrics; do not tune against held-out results.
7. Update setup, architecture, run, test, evaluation, and demo documentation. Address stale historical lifecycle tests without modifying frozen study assets.

Each implementation phase receives tests, verification, independent Astra Low review, fixes, and a separate commit. Final evaluation is delayed until the complete assistant is frozen to preserve the held-out boundary.
