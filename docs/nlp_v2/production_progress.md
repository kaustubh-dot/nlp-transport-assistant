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
- **Commit:** `596e856`.

## Phase 3 — production T3 model and safe trainer

- **Objective:** package the existing 16-class MuRIL checkpoint for strict production inference and provide a separate train/validation-only replacement training path.
- **Files changed:** `models/nlp_v2_t3_manifest.json`, `src/nlp_v2/model.py`, `scripts/nlp_v2/train_production_t3.py`, `tests/test_t3_model.py`, focused design and plan, and this progress record.
- **Model selection:** seed 42 checkpoint loaded strictly on CPU, with pinned MuRIL revision, raw-query tokenization, max length 64, and verified SHA-256. The frozen training and validation CSVs unexpectedly share 39 family IDs and 35 semantic family IDs, affecting 78 of 410 validation rows. Without editing them, we compared all three existing checkpoints on 332 disjoint validation rows: Macro-F1 0.85122 (42), 0.84260 (101), 0.82535 (777). The original published seed-42 validation score of 0.91555 is retained with this leakage caveat. Selection used validation only, never stress/test/reference.
- **Verification:** 7 focused tests pass, including real checkpoint inference and a CPU smoke training run. CLI smoke training completed under `/tmp/nlp_v2_t3_smoke_20261006`; its random-small-model metadata says `production_eligible: false`. The full suite has 247 passes and the same 13 historical Gate B.3 lifecycle failures as baseline. No CUDA device is available, so no new full MuRIL training was run; the pre-existing selected checkpoint supplies production inference.
- **Astra Low review:** found that trainer metadata omitted configurable hyperparameters. Added the effective configuration, optimizer settings, device, package versions, corresponding CLI flags, and a nondefault-parameter smoke assertion. Focused re-review confirmed the fix.
- **Known limitations:** the 950 MB checkpoint is ignored by Git and must be supplied locally for a fresh clone; the pinned MuRIL tokenizer/base files must be cached or explicitly installed. Family-disjoint validation has small counts for several classes. Full replacement training requires suitable GPU compute. Held-out evaluation follows the model freeze in Phase 4; no stress/test data has been read for model selection.
- **Commit:** `1f31956`.

## Phase 4 — frozen production T3 model evaluation

- **Objective:** evaluate the Phase 3 frozen seed-42 checkpoint once on the authorized stress set and human-reference subset, with aggregate-only reports separate from historical Gate B.2 research outputs.
- **Files changed:** `scripts/nlp_v2/evaluate_production_t3.py`, `tests/test_t3_production_evaluation.py`, `reports/nlp_v2/production_eval/production_t3_evaluation.{json,md}`, focused design and plan, and this progress record.
- **Verification:** 5 synthetic evaluator tests pass. The checkpoint and frozen input hashes were checked before inference. On 706 stress rows, strict intent accuracy is 0.8300, Macro-F1 0.7918, ambiguity-aware acceptance 0.8399, mapped operation accuracy 0.8300. On the nested 350-row human-reference subset, strict accuracy is 0.8400 and Macro-F1 0.7777. Per-class and language/code-switch/noise aggregates are in the JSON report. No model or prompt change followed evaluation.
- **Split integrity:** metadata-only audit found 187 of 706 stress rows and 160 of 350 human-reference rows sharing a training family or semantic family, with zero exact query duplicates. These are frozen-data limitations; the files remain untouched. Full-set metrics are descriptive stress performance, not independent family-held-out generalization estimates. Among 73 observed human-subset contrast groups, 17 are partial; the report discloses this.
- **Astra Low review:** checked hashes, reference/gold alignment, per-class metric reconstruction, operation mapping, and aggregate-only claims. It requested clearer subset contrast semantics and stronger evaluator guard tests; both were added. Focused re-review confirmed the reporting and guard fixes.
- **Known limitations:** the classifier emits a single label; its ambiguity-aware score is retrospective acceptance, not clarification behavior. Domain answer quality and end-to-end operational behavior are assessed only after integration. The stress set was not used for model selection or any checkpoint change.
- **Commit:** `dde96d9`.

## Phase 5 — canonical transport domain service

- **Objective:** back the T3 dispatcher with read-only canonical SQLite operations and explicit unavailability where the snapshot cannot support a verified answer.
- **Files changed:** `src/nlp_v2/domain.py`, `tests/test_t3_domain_service.py`, focused design and plan, and this progress record.
- **Behavior:** all 16 T3 operations have explicit handlers. Mode-consistent published bus stop sequences, direct route candidates, stop membership, provisional timetable bounds/departures/frequency, dated official fare records, and straight-line nearest stops use canonical source rows. Current availability, ticket policy, accessibility with null records, unconfirmed interchange/multimodal transfer, and realtime return structured unavailable states. The service uses read-only SQLite and never emits a live-data claim.
- **Verification:** 20 focused tests pass, including canonical route/fare/schedule/nearest records and missing-schema/unavailable cases. The full suite has 272 passes and the same 13 stale Gate B.3 lifecycle failures as baseline. No frozen data or evaluation result was changed.
- **Astra Low review:** identified destination-blind schedules, time-blind frequency, and cross-mode fare substitution. All were reproduced with failing tests and fixed. Focused re-review confirmed the fixes and compatible bus fares/daytime frequency.
- **Known limitations:** canonical hub memberships are all unverified, all 45 interchanges unconfirmed, accessibility fields null, and ticket policy absent; verified multimodal routing and affirmative accessibility/ticket answers cannot be produced from this snapshot. Schedule and fare records are historical/provisional and require operator verification. Direct route planning is based on published stop sequence, not confirmed trip availability.
- **Commit:** `23190b0`.

## Phase 6 — single T3 assistant path

- **Objective:** connect raw-query MuRIL T3 inference, canonical slot/entity extraction, clarification, operation dispatch, canonical SQLite service, and user-facing response formatting without a legacy taxonomy fallback.
- **Files changed:** `src/nlp_v2/assistant.py`, `tests/test_t3_assistant.py`, focused design and plan, and this progress record.
- **Verification:** 14 synthetic English/Hindi/Roman/mixed/noisy contract tests pass. A manual run using the real frozen checkpoint reached `nearest_transport` and the canonical nearest-stop service for a Marina Beach query; live status returned explicit unavailable. The full suite has 286 passes and the same 13 stale historical Gate B.3 failures. Python compilation and whitespace checks pass.
- **Astra Low review:** found classifier-supplied multi-goal clarification could be overwritten by entity ambiguity and mixed-route departure times lost their route names. Both were reproduced with failing tests and fixed; focused re-review found no remaining issue. Candidate intent alternatives were added to clarification replies.
- **Known limitations:** the classifier emits one T3 label in normal inference, so multi-goal clarification currently requires an upstream structured prediction. Conservative entity resolution can ask for a stop when a named location has no route-constrained physical match. Replies use English templates while preserving the original multilingual query and canonical slots.
- **Commit:** `dbc76d1`.

## Phase 7 — local JSON application API

- **Objective:** expose the completed T3 assistant through a stable localhost request/response contract for the existing frontend.
- **Files changed:** `app/api.py`, `tests/test_t3_api.py`, focused design and plan, and this progress record.
- **Behavior:** `POST /api/v2/query` accepts a bounded JSON query and returns status, response text, T3 intent/operation, slots, operation data, and clarification alternatives. `GET /health` reports the loaded T3 service. Raw/normalized query, confidence, and exception details are excluded. The standard-library server binds to `127.0.0.1` by default.
- **Verification:** 9 in-process API contract tests pass. A local-only HTTP smoke verified health/query responses, lowercase headers returning 200, a truncated body timing out with 408, and health remaining responsive afterward. The full suite has 295 passes and the same 13 stale Gate B.3 lifecycle failures. No new web dependency was needed.
- **Astra Low review:** found case-sensitive header lookup after adapter conversion and an unbounded blocking body read. Added red tests, case-normalized headers, a finite socket timeout, and safe 408 handling. Focused re-review confirmed both fixes.
- **Known limitations:** the endpoint is a local demo server, single threaded and without public deployment/authentication. The Streamlit frontend has not yet been switched to this API.
- **Commit:** `e607d46`.

## Phase 8 — T3 Streamlit frontend

- **Objective:** route the default Streamlit page through the local T3 API and present structured answers, clarifications, provenance, and unavailable states.
- **Files changed:** `app/streamlit_app.py`, `app/frontend_contract.py`, preserved `app/legacy_streamlit_app.py`, retargeted legacy UI tests, `tests/test_t3_frontend.py`, focused design and plan, and this progress record.
- **Behavior:** the default page uses the API only, with 16-intent-compatible answer panels, source metadata where available, suggested clarification choices, explicit snapshot caveats, and no seven-label fallback. The prior prototype remains accessible as `app/legacy_streamlit_app.py` for historical tests.
- **Verification:** 37 focused frontend and preserved-legacy tests pass. The full suite has 315 passes and the same 13 stale Gate B.3 lifecycle failures. A live localhost Streamlit/API browser smoke rendered a nearest metro answer with canonical source rows at desktop width; narrow-width DOM geometry stayed within a 390-pixel viewport.
- **Astra Low review:** found undisplayed entity clarification choices and source fields missing from stop, timetable, and frequency panels. Both were fixed with failing tests first; focused re-review confirmed the fixes.
- **Known limitations:** the UI depends on a separately running local API. It does not infer live service or verified walking access. The browser's narrow-width screenshot was visually scaled by the test browser, so responsive layout was checked using DOM element bounds in addition to the desktop screenshot.
- **Commit:** `bef1235`.

## Phase 9 — system QA and assistant freeze

- **Objective:** verify the complete repository, reconcile obsolete lifecycle tests with the closed study, harden production behavior, and prepare a one-way aggregate assistant evaluator.
- **Files changed:** production slot/resolver/contract/service/assistant modules, frontend response validation, `requirements-nlp-v2.txt`, `scripts/nlp_v2/evaluate_assistant.py`, focused regression tests, the Gate B.3 test module, the QA plan, and this progress record.
- **Governance:** all 34 Gate B.3 framework tests now run against the correct lifecycle. Pre-execution gate unit tests use temporary synthetic manifests; current-study tests validate closed T3 state and the two MODEL_G output hashes. No tests were skipped. Frozen B.2/B.3 data, annotations, research reports, and experiment records remain byte-for-byte unchanged from `c7576a9`.
- **GPT-6.1 Sol xhigh review:** the user changed the reviewer requirement for this and later phases. The full-project reviewer found dropped fare modifiers, dropped timing destinations, unreachable production multiple-goal clarification, ignored relative days, missing negative membership, MRTS remapping, rejected line identifiers, widened invalid/bare temporal inputs, reversed Hindi directions, and unsafe nested frontend replies. Each issue received a synthetic failing regression before its fix. Re-review added canonical Night Services spelling, clock seconds, and default reference-date staleness; these were fixed too. The real checkpoint now reaches explicit conjoined-goal clarification without altering model weights or single-label inference.
- **Verification:** all 368 repository tests pass; focused re-review closed with no unresolved high/medium findings. Compilation, whitespace, installed dependency version matching, and `pip check` pass. No T2/baseline dependency is active in production. No tracked checkpoint or credential was found; the only tracked artifact larger than 10 MB is the existing canonical SQLite database. Real-model synthetic smoke returned the Deluxe stage fare, MRTS-only nearest stops, and ambiguous-clock clarification, with valid public/frontend contracts.
- **Evaluation boundary:** the complete assistant evaluator requires committed production source matching a supplied freeze revision, verifies frozen input/model hashes, records the canonical DB hash and fixed Chennai reference date, and writes aggregate metrics only. It reports selected operation, terminal dispatch, status and clarification behavior, without claiming factual or slot correctness. The final run occurs after this phase's source commit; its results will not be used to tune the assistant.
- **Known limitations:** multiple-goal detection covers explicit coordinated requests through a clarification-only guard. Unknown aliases and unsupported temporal expressions remain limited by deterministic extraction. Transformers 5.17 emits a generic Mistral-regex warning for MuRIL because its large vocabulary and config without `transformers_version` trigger a faulty library check. Independent inspection confirmed BertTokenizer/WordPiece/BertPreTokenizer/BertNormalizer; applying the suggested Mistral patch would incorrectly change frozen BERT preprocessing, so the tokenizer remains unchanged.
- **Commit:** `b9b2271`.

## Focused phase sequence

1. Define the production T3 prediction, slot, clarification, answerability, and dispatch contracts for all 16 intents. Keep legacy research code isolated.
2. Extract and resolve canonical slots, including temporal ambiguity, using the frozen ontology and canonical KB.
3. Package a suitable existing T3 checkpoint or prepare a separate train/validation-only production trainer and GPU command. Never rerun the frozen Gate B.2 benchmark.
4. Integrate canonical DB services with explicit provenance and unavailable states.
5. Connect one end-to-end assistant path, then expose its stable contract through an API and the existing Streamlit application.
6. Complete development QA and freeze the whole assistant before final held-out evaluation. Report model-only metrics separately from operational metrics; do not tune against held-out results.
7. Update setup, architecture, run, test, evaluation, and demo documentation. Address stale historical lifecycle tests without modifying frozen study assets.

Each implementation phase receives tests, verification, independent review, fixes, and a separate commit. Phases 0–8 used Astra Low; the user's updated requirement selects GPT-6.1 Sol xhigh for Phase 9 and later reviews. Final evaluation is delayed until the complete assistant is frozen to preserve the held-out boundary.


## Phase 10 — documentation, reproducibility and demo readiness

- **Objective:** make the final local T3 system understandable and runnable for a new developer with the required model artifact, and record its verified scope and final evaluation.
- **Files changed:** `README.md`, `ARCHITECTURE.md`, `docs/nlp_v2/production_runbook.md`, the readiness plan, ignored-cache configuration, `reports/nlp_v2/assistant_eval/assistant_evaluation.{json,md}`, and this progress record. Historical research reports remain untouched.
- **Final evaluation:** the complete assistant was evaluated once after source freeze `b9b2271b1761d08752786f22b558862f45ed1dac`, with fixed Chennai reference date `2026-10-06`. On 706 stress rows: strict reply-intent accuracy 0.8272, selected-operation accuracy 0.5042, terminal-dispatch accuracy 0.2323; statuses 520 clarification, 150 unavailable, 22 ok, 14 out of scope, zero error. Human-subset terminal dispatch is 0.2571. These measure reply/operation contracts, including unavailable operations, and do not establish factual travel correctness. Overlap and clarification caveats remain explicit. Markdown table placement was corrected without changing scores or evaluator logic. No product/model tuning followed.
- **Verification:** all 368 tests pass against a freshly prepared repository-local pinned tokenizer/config cache. The public cache preparation, CPU CLI smoke trainer, API/UI startup, HTTP health/query commands, live sourced Deluxe fare UI reply, CLI help/options, documentation links, compilation, dependency version matching, `pip check`, and whitespace checks were verified. The selected checkpoint SHA is verified by real-model tests. Complete clean-environment dependency installation and full GPU training were not executed; the existing environment has no GPU.
- **GPT-6.1 Sol xhigh review:** found that the documented standalone CUDA assertion did not prevent a subsequently pasted Bash training command from running on CPU. The GPU example now invokes training only after CUDA verification and cache preparation succeed. All runbook Bash blocks pass syntax checks; a simulated prerequisite failure skips training. Focused re-review confirmed the fix and closed with no unresolved high/medium findings. Documentation/source contracts, links, aggregate report counts and frozen boundaries were independently checked; held-out evaluation was not rerun.
- **Remaining limitations:** a fresh clone requires the original ignored 950 MB checkpoint from the project/run owner or an authorized archive; no public artifact URL is available. The high clarification rate and limited successful responses reflect alias/KB/verified-service coverage limits. Live status, confirmed multimodal transfer planning, policy, facility and accessibility coverage remain unavailable as described in the runbook.
- **Commit:** `84dc5e5`.

## Phase 11 — current-state reconfirmation and coverage diagnosis

- **Objective:** establish the actual baseline and identify structural coverage limits without targeting held-out examples.
- **Baseline:** clean `main`; local HEAD, cached `origin/main`, and live remote main all `9c9f707199ad210878baa08ff536358da9386c03`. Checkpoint and DB SHA-256 verified; frozen research Git boundary unchanged from `c7576a9`.
- **Files changed:** `docs/nlp_v2/coverage_diagnosis.md` and this record. Production code unchanged.
- **Diagnosis:** inconsistent schedule execution requirements; exact-name ambiguity and limited route-context resolution; unnecessary entity questions for absent policy/source capability; underexposed positive static connectivity; exact tariff-category casing mismatch; genuine mode-inconsistent metro links, null accessibility, and unconfirmed transfers. Older specification claims exceed actual snapshot evidence.
- **Verification:** baseline full suite 368 passed in 13.18 s; read-only schema/count/provenance audit and new synthetic slot probes. No historical evaluator run or item-level held-out inspection.
- **GPT-6.1 Sol xhigh review:** two medium omissions (discarded multiple-mode/date/time constraints and place/stop execution-kind mismatch) and one low count precision issue fixed in the diagnosis after independent reproduction. Focused re-review passed: unresolved critical/high/medium/low = 0.
- **Limitations:** this audit cannot quantify causes from aggregate historical metrics; development reachability and improvement require the new suite. No new training justified yet.
- **Commit:** `docs(nlp_v2): diagnose operational coverage from canonical evidence` (hash recorded in the next phase).

## Phase 12 — development-only assistant coverage suite

- **Objective:** create a legitimate contract improvement loop separate from historical stress/reference evaluation.
- **Files changed:** versioned development JSON/manifest, development evaluator, synthetic scorer/guard tests, design/plan, baseline development reports and this record. No production code or historical assets changed.
- **Suite:** 120 independently authored contract cases; every T3 intent has five language cases, with additional noise, missing inputs, entity/time ambiguity, endpoint-kind, unsupported constraints/source and multiple-goal contrasts. Gold expectations describe intended contracts, including currently missing legitimate capabilities. Suite hash `0de0ce7de1ca933b70321bf15c0d9bbc2d7db0dc694cd046064d28104988ea41`; canonical DB hash locked. Opaque normalized held-out query overlap = 0; this is not proof of semantic independence.
- **Baseline, production model:** intent contract 93/120; terminal contract 64/120; legitimate answerable coverage 24/50; false-positive clarification 30/104; statuses 43 clarification, 41 unavailable, 31 ok, 5 out_of_scope, 0 error.
- **Baseline, gold-intent downstream diagnostic:** terminal contract 77/120; answerable 28/50; false-positive clarification 29/104; statuses 42 clarification, 40 unavailable, 32 ok, 6 out_of_scope, 0 error. Injected-intent scores are not model accuracy. False-positive clarification denominator is cases with non-clarification gold; status-only OK counts do not establish successful answers.
- **Verification:** 29 synthetic evaluator tests passed after observed red/green cycles; full suite 397 passed in 13.61 s; compilation, whitespace and pip dependency checks pass. Historical evaluators not run; fingerprint function returns only digests, never held-out examples or labels.
- **GPT-6.1 Sol xhigh review:** four medium findings fixed: malformed evidence accepted, unchecked membership Boolean, nearest anchor/mode loss, and forbidden slots/duplicate candidate gold. Two low findings fixed: language/noise tags and manifest metadata validation. Failing synthetic regressions reproduced scorer/validation issues; independently checked canonical membership and anchor records before pre-freeze gold corrections. Focused re-review passed: unresolved critical/high/medium/low = 0. Final reports/source hashes and metric reconstruction independently verified.
- **Limitations:** development observations are not generalization estimates. Source-presence checks validate contracts, not independent current transport facts. Failure counts are overlapping diagnostic flags rather than causal proof. Ambiguous-intent gold injections explicitly bypass classifier uncertainty.
- **Commit:** `test(nlp_v2): freeze development-only assistant coverage suite` (hash recorded in Phase 13). Phase 11 commit: `5ae4621`.
