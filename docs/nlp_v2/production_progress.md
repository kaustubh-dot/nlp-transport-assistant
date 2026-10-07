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

## Phase 13 — reduce unnecessary clarifications

- **Objective:** align scheduling execution requirements, use safe exact route context, and avoid entity questions that cannot change source answerability.
- **Files changed:** production contracts/resolver/domain/assistant; focused dispatch/slot/assistant tests; design/plan; development reports and this record.
- **Behavior:** scheduling requires a station/stop/origin; frequency also requires a route/line. Route context normalizes canonical delimiter/case differences and uses only operational mode-consistent links for membership/timing. Unique exact candidates resolve; multiple/off-route/incompatible candidates are preserved. Canonical capability preflight identifies absent policy/facility/multimodal/transfer/accessibility coverage before non-actionable slot questions; semantic and multiple-goal guards retain precedence. Injected services without preflight retain the established path.
- **Development comparison (v1 unchanged):** real-model clarification 43 → 22; false-positive clarification 30/104 → 11/104 (28.85% → 10.58%); terminal contract 64/120 → 74/120; answerable 24/50 → 25/50. Gold-intent downstream clarification 42 → 24; false-positive 29/104 → 8/104 (27.88% → 7.69%); terminal 77/120 → 99/120; answerable 28/50 → 32/50. Real statuses: 22 clarification, 55 unavailable, 38 ok, 5 out_of_scope, 0 error. More OK statuses alone do not establish correct coverage.
- **Verification:** 13 observed failing behavior regressions before implementation, 149 focused passes, then 421 full passes in 16.69 s including unusable-link and review regressions. Compilation/diff checks pass; v1 hash and frozen research boundaries unchanged. No held-out evaluation run or targeting.
- **GPT-6.1 Sol xhigh review:** one medium extension-service veto and one low malformed-message finding reproduced with five failing tests and fixed. Overridden execution/handlers/maps bypass base assumptions; malformed/throwing preflight becomes a safe error preserving intent/operation. Independent focused re-review: 215 tests pass; final reports/source hashes verified; unresolved critical/high/medium/low = 0.
- **Limitations:** genuine duplicate-node/time ambiguity remains; source/time/mode constraint integrity, new domain evidence paths and language aliases remain subsequent-phase work. Preflight is a source-capability refusal, not an intent reclassification or successful transport answer.
- **Commit:** `fix(nlp_v2): reduce non-actionable assistant clarifications` (hash recorded next phase). Phase 12 commit: `c33d6f1`.

## Phase 14 — expand canonical domain coverage

- **Objective:** expose category-A snapshot evidence while preserving explicit constraints and unavailable boundaries; operation-by-operation capability matrix in `domain_coverage_design.md`.
- **Files changed:** domain/assistant/resolver/extractor, focused service/assistant regressions, design/plan, v1 development reports and this record. Immutable DB/model/suite and historical assets unchanged.
- **Behavior:** positive ordered published connectivity with source and explicit current-operation refusal; Night Services tariff case normalization only; exact physical stop coordinate anchors; sourced membership. Date/time route constraints and dated availability are unavailable. Atomic multiple-mode requests ask for one mode. Partial sequences disclose omitted unusable rows; incomplete topology cannot prove negative membership; via links require mode consistency; frequency cannot merge route/direction/physical-stop groups. Nearest distances remain straight-line, with no verified walking access.
- **Development comparison:** real-model terminal contract 74/120 → 84/120, answerable 25/50 → 35/50; statuses 22 clarification, 50 unavailable, 43 ok, 5 out_of_scope, zero error; false-positive clarification unchanged 11/104. Gold-intent downstream terminal 99/120 → 111/120, answerable 32/50 → 43/50; statuses 23 clarification, 46 unavailable, 45 ok, 6 out_of_scope, zero error; false-positive clarification 8/104 → 7/104. Contract success, not status-only OK, measures gains.
- **Verification:** 13 new behavioral red cases plus via-mode red reproduced before fixes; review regressions also reproduced red; focused 237 passed; full 443 passed in 14.95 s; compile/diff checks pass. No historical evaluator run or item-level held-out inspection.
- **GPT-6.1 Sol xhigh review:** four medium findings reproduced red and fixed: timed availability, empty same-code route variants, invisible partial topology, and dropped availability route/via constraints. Availability preserves the existing canonical time/route/via fields; topology checks each variant and discloses bounded positive matches. Minimal availability panel integration preserves candidate/source visibility. Independent 237-test re-review and Streamlit source/partial-caveat smoke pass; final report/model/DB/suite hash and metric reconstruction pass. Unresolved critical/high/medium/low = 0.
- **Limitations:** dated/current operation, metro topology/schedules, policy, facilities, discount eligibility, OD fare-stage arithmetic, verified transfer graph and walking access remain unsupported or verification-required. Published frequency is a bounded single-direction estimate, not a realtime claim. Exact nearest anchor candidates remain ambiguous where several actual nodes share a name.
- **Commit:** `feat(nlp_v2): expose bounded canonical transport coverage` (hash recorded next phase). Phase 13 commit: `71ff200`.

## Phase 15 — clarification policy and operational contracts

- **Objective:** distinguish actionable uncertainty, source limitations and request/service failures without changing T3 taxonomy or the five statuses.
- **Files changed:** assistant/contracts/dispatch/domain, API/frontend contract, synthetic response-policy tests, design/plan, development reports and this record.
- **Behavior:** derived public `outcome_reason` distinguishes semantic/entity/temporal uncertainty, multiple goals, missing execution input, unsupported source, external realtime requirement, malformed request, temporary failure, answered and out-of-scope. Existing reason/candidate/slot fields remain. Missing prompts describe actual boarding/end/route/anchor/fare inputs. Frequency ambiguity asks for a destination only when absent because the schedule query can filter on it; residual ambiguity remains unavailable. Empty/punctuation-only requests are malformed; malformed service messages become safe known-operation errors; direct parso dispatch matches extraction. First/last clock constraints remain unavailable rather than assuming before/after/at semantics.
- **Development evidence:** mode source preflight reduces non-actionable questions: real-model terminal 84/120 → 86/120, answerable unchanged 35/50, false-positive clarification 11/104 → 8/104; statuses 18 clarification, 54 unavailable, 43 ok, 5 out_of_scope, zero error. Gold-intent terminal 111/120 → 112/120, answerable unchanged 43/50, false-positive clarification 7/104 → 5/104; statuses 20 clarification, 49 unavailable, 45 ok, 6 out_of_scope, zero error. Frozen v1-098 expects entity clarification for metro departures; the new policy refuses the absent mode schedule regardless of ambiguous station. This one policy/gold divergence remains visible; no gold edits or claim of perfection.
- **Verification:** 22 policy regressions observed failing before implementation; focused 167 passed, with additional intent/temporary failure coverage added. Full 474 passed in 15.74 s; mode source/extension/DB failure guards and API review regressions verified. Compilation and diff checks pass. No historical evaluator run or targeting.
- **GPT-6.1 Sol xhigh review:** one medium malformed-request HTTP 503 mapping and two low optional-null reason/null schedule-existence findings reproduced red and fixed. Malformed HTTP input now 422, temporary failures 503; present outcome reason must be a known string; schedule capability requires a non-null departure. Optional mode source preflight, extension guards, safe failures, policy/gold divergence and direct-dispatch boundary independently assessed. Focused 209 passed; final report/source/model/DB/suite hashes and metrics verified. Unresolved critical/high/medium/low = 0.
- **Limitations:** unavailable categories are source capability statements, not verified present-day absence. Semantic classifier uncertainty still requires an explicit structured prediction; no confidence threshold or classifier normalization added. English response templates remain; original multilingual model input preserved. Optional mode source preflight uses only base handler assumptions and follows the explicit multiple-mode choice; custom execution/handlers remain authoritative.
- **Commit:** `fix(nlp_v2): clarify actionable response outcomes` (hash recorded next phase). Phase 14 commit: `d5cc8ac`.

## Phase 16 — multilingual and noisy input hardening

- **Objective:** improve bounded deterministic extraction while preserving raw model inference and frozen evaluation boundaries.
- **Files changed:** resolver/extractor/assistant/domain, synthetic multilingual tests, design/plan, v1 development reports and this record.
- **Behavior:** exact Hindi/mixed-script surfaces resolve through current Alwar Thirunagar, Poonamallee Bus Terminus and Marina Beach canonical names; duplicate physical nodes remain distinct and route context uses only existing verified-kind links. Bounded Hindi suffix names follow route digits; unknown adjoining letters/marks cannot truncate to a shorter code. Allowed training `bs` shorthand, development `Deluxw` and bounded `mnthly pass` phrases are recognized. Similarity to Ordinary/Express/Deluxe only requests a service class, never selects one; multiple exact classes also clarify. Night similarity is excluded because right/light/eight are common words. Non-bus service-class scope stays unavailable; multiple modes keep priority. Model raw input, taxonomy, labels, checkpoint and tokenizer remain unchanged.
- **Development comparison:** real-model terminal 86/120 → 93/120; answerable 35/50 → 42/50; false-positive clarification 8/104 → 3/104; statuses 13 clarification, 54 unavailable, 48 ok, 5 out_of_scope, zero error. Gold-intent downstream terminal 112/120 → 119/120; answerable 43/50 → 50/50; false-positive clarification 5/104 → 0/104; statuses 15 clarification, 49 unavailable, 50 ok, 6 out_of_scope, zero error. The sole downstream failure is the documented frozen v1-098 policy/gold divergence; no suite edits.
- **Verification:** 22 initial observed red tests, plus common-word, non-bus actionability and combining-mark boundary regressions reproduced/fixed. Review findings reproduced with behavioral red regressions, including punctuation/Unicode suffix truncation and non-actionable fare-class prompts. Focused multilingual/slot 117 passed; full 532 passed in 15.84 s; compile/diff/suite SHA checks pass. No historical evaluator or item-level held-out inspection.
- **GPT-6.1 Sol xhigh review:** three medium findings (suffix truncation including punctuation/Unicode/composite variants, non-actionable fare-class questions, and a transient overly narrow typo-context fix) plus one low common-word false-match finding reproduced red and fixed. Shared domain fare scope now owns refusal precedence; extension execution/handlers/maps bypass base assumptions. Independent 326-test re-review, API/frontend compatibility, raw-input and duplicate-candidate checks pass. Final source/model/DB/suite hashes and language/noise metrics independently reconstructed. Unresolved critical/high/medium/low = 0.
- **Limitations:** bounded aliases are development improvements, not broad transliteration/generalization claims. Unknown unrelated spelling remains unresolved; explicit name duplication still clarifies. Real-model versus gold-intent gaps require actual classifier/guard attribution in Phase 17 before training is justified.
- **Commit:** `fix(nlp_v2): harden bounded multilingual extraction` (hash recorded next phase). Phase 15 commit: `56d3e08`.


## Phase 17 — classifier attribution and replacement decision

- **Objective:** measure remaining raw-classifier, guard, downstream and source limitations, then decide training from legitimate development/validation evidence.
- **Files changed:** read-only diagnosis script and synthetic attribution tests; future coverage metadata; GPU-only trainer guard/resource logging; decision/design/plan; baseline diagnosis and candidate metadata/comparison reports; runbook/local-artifact ignore rule and this record.
- **Evidence:** raw development model 92/118 single-label accuracy (two null-intent contracts excluded), Macro-F1 0.75675; final terminal 93/120 and answerable 42/50. Of 27 terminal failures, 25 wrong raw classes become correct with intended intent, one requires structured ambiguity, one is frozen v1-098 policy/gold divergence. Gold-intent terminal 119/120 and answerable 50/50; no additional slot/entity/domain-code failures. Correct unavailable contracts: 48, comprising six external realtime and 42 data/verified-scope limitations. These are not failed answers. Actual raw traces replace previous reply-intent-based classifier metadata; earlier phase reports are preserved with an explicit interpretation correction.
- **Decision:** one unchanged-data seed 42 full MuRIL candidate justified by classifier bottleneck, with 332 train-disjoint validation rows for epoch/selection comparison and 1396 train-only fit rows. Pinned T3/model revision/raw/max64/config and all splitfiles preserved; no development augmentation or stress/reference selection. Predeclared promotion threshold baseline 0.8512157223 + 0.001. Sandbox hid CUDA; authorized host check/allocation found RTX4000Ada 20 GB total, 6392 MiB free under another workload. Actual-process GPU guard prevents CPU fallback; memory failure would stop without changing other jobs/configuration.
- **Outcome:** one full GPU run stopped after 13 epochs, best epoch 10 Macro-F1 0.8465825050, below baseline/threshold; independently reconstructed saved-artifact CPU validation 289/332 and identical Macro-F1. Existing checkpoint/manifest retained. Training loop 316.94 s, peak CUDA 4.48 GiB. Candidate stays ignored outside historical paths at production_runs/t3-disjoint-seed42-20261007; metadata/comparison tracked. No candidate development/historical evaluation, adaptive seed/config retry, artifact upload or current-weight overwrite.
- **Verification:** synthetic red/green attribution, reply-metric, CPU/allocation guard and candidate-manifest tests; focused 39 passed; full 542 passed in 16.10 s. Compilation/pip/diff and frozen Git boundary checks pass; no tracked weight binaries; DB/suite/model manifest unchanged.
- **GPT-6.1 Sol xhigh review:** preliminary scientific go; two medium execution findings (total/free resource precision and actual-process GPU guard) reproduced/fixed, independent 43 focused passes. Final independent strict candidate CPU reconstruction matched all validation metrics/confusion/per-intent counts; checkpoint/manifest/metadata/source hashes and frozen boundaries verified. Independent 46 focused passes; unresolved critical/high/medium/low = 0.
- **Limitations:** observed development and small-class disjoint validation are not independent test estimates. Counterfactual reachability does not predict retraining gain. Classifier remains a bottleneck after this negative candidate; source coverage and one semantic-ambiguity contract remain limited. Existing model retained for the failed comparison, not because downstream alone is limiting. No GPU stop applies because the host run succeeded.
- **Commit:** `feat(nlp_v2): diagnose and evaluate classifier replacement` (hash recorded next phase). Phase 16 commit:`826e96f`.


## Phase 18 — selected checkpoint portability

- **Objective:** make required artifact supply/verification reproducible without uploading or tracking huge weights.
- **Files changed:** read-only artifact validator, synthetic tests, selected provenance JSON, workflow design/plan/docs, README/runbook links, strict malformed-manifest guard and this record.
- **Workflow:** exact owner-supplied selected 950,358,409-byte file at the preserved path; trusted Git manifest and SHA verified before startup. Basic checks use no transformer runtime/cache; optional --load-model reuses authoritative strict offline CPU loader. Missing/corrupt/malformed inputs fail clearly and nonzero. No archive extraction/installer, external host upload, LFS migration or training fallback. Provenance preserves original overlapping-validation caveat and Phase17 negative-candidate retention.
- **Verification:** six initial synthetic reds and one malformed-root red reproduced/fixed; 14 focused passes; full 549 passed in 15.37 s. Real strict command verifies selectedSHA/manifest/16 labels/raw 64 and model/cache load. Compilation/diff/frozen boundary/no-weight tracking checks pass.
- **GPT-6.1 Sol xhigh review:** independent 14 focused passes; basic Python -S validation succeeds without site packages. Invalid JSON/root/missing metadata/corrupt bytes return status1 without traceback; provenance/links/ignore rules and frozen boundaries checked. Unresolved critical/high/medium = 0.
- **Limitations:** complete fresh dependency installation and owner-to-new-machine transfer not executed. Exact trusted bytes and strict local loading verified; no public artifact download exists. The model is 906.33 MiB, intentionally ignored.
- **Commit:** `feat(nlp_v2): validate portable selected model artifacts` (hash recorded next phase). Phase 17 commit:`f36e70b`.


## Phase 19 — development acceptance matrix

- **Objective:** report practical bounded coverage and remaining failure taxonomy without an unsafe metric target.
- **Files changed:** acceptance matrix, refreshed real/gold-intent development reports and this record; production code and suite unchanged.
- **Evidence:** terminal contracts 64/120 → 93/120; answerable 24/50 → 42/50; false-positive clarification 30/104 → 3/104. Status counts alone are not accepted as coverage. Gold-intent answerable 50/50, terminal 119/120 with the unchanged v1-098 policy divergence. Raw traces observe all 16 labels and contract tests exercise all 16 operations; source answerability remains bounded.
- **Taxonomy:** 25 wrong-raw-intent terminal failures corrected by intended intent, one structured ambiguity, one residual policy/gold divergence. Downstream slot/entity/domain-code flags zero on this suite. Under intended intent, 48/48 gold-unavailable contracts are correct data/scope or external refusals; production achieves 38/48, with ten wrong-intent terminal failures. Source limitations remain distinct from classifier failures. The negative validation-only candidate remains unselected; no further implementation defect or defensible suite-specific tuning was identified.
- **Verification:** both new empty-directory evaluators ran on current source, fixed date and frozen hashes; matrix sums/counts and answerable totals checked; diff check passes. Prior Phase 18 full 549 verification still applies because this phase changes only documents/reports. No historical evaluator/item inspection.
- **GPT-6.1 Sol xhigh review:** all 17 rows/120 cases, metrics, raw attribution, reachability and frozen/source hashes reconstructed. One low conditional-versus-production refusal-count wording fixed (48/48 intended versus38/48 actual). Final re-review unresolved critical/high/medium/low = 0.
- **Limitations:** development is observed, small/noise-skewed; conditional downstream success is not classifier capability or travel-fact accuracy. Remaining raw errors and genuine source/verified-scope limits remain explicit.
- **Commit:** `docs(nlp_v2): record development acceptance and coverage` (hash recorded next phase). Phase 18 commit:`393cdce`.

## Phase 20 — whole-system QA and backend source freeze

- **Objective:** verify the complete production project and eliminate valid review blockers before one-way final descriptive evaluation.
- **Files changed:** assistant/extraction metadata, 53 synthetic contract regressions, QA plan/report, architecture/runbook/README corrections, final development reports and this record.
- **Fixes:** repeated same-operation requests and coordinated routes/lines/stages/stops/nearest anchors/clocks/dates/relative days clarify instead of dropping constraints. Unknown explicit via and rejected numeric route suffixes remain execution inputs, including optional timetable scopes and Hindi suffix-before-mode variants. Unsupported before/range semantics refuse rather than return at/after departures. Clock/date numeric tails cannot become route codes. Mode source capability precedes non-actionable missing questions; fare preflight remains fare-only; canonical slots/model preprocessing are unchanged.
- **Verification:** red regressions reproduced all valid findings and boundary variants. Final full 602 passed in 15.61 s; compilation/pip/diff checks pass. Exact checkpoint bytes/hash/16 labels/raw64 manifest verified; DB/dev-v1/model hashes and frozen Git diff unchanged. No recognized secret prefixes or tracked binary/cache/environment files. Real local API covers source-backed fare, missing/multiple clarification, unavailable/realtime, out-of-scope and malformed422 with no internal fields.
- **Development:** actual terminal93/120, answerable42/50, false-positive clarification3/104 unchanged; intended terminal119/120, answerable50/50, FP0/104, with unchanged v1-098 policy/gold divergence. Fresh reports match final source hashes.
- **GPT-6.1 Sol xhigh review:** complete runtime/app/artifact/trainer/evaluator/docs/frozen-state review, four medium constraint-loss findings and their bounded variants reproduced/fixed, one low stale-test-count corrected. Independent final ALL T3 441 passed in 9.87 s, real-checkpoint behavior and public-schema checks pass; unresolved critical/high/medium/low=0.
- **Limitations/freeze:** [QA record](system_qa.md). Classifier and current-data limits remain; no perfection/factual-answer estimate. Phase20 commit freezes backend/API/model/data/evaluators before Phase21 aggregate-only post-development descriptive evaluation. Phase22 presentation-only changes are permitted; no backend tuning follows evaluation.
- **Commit:** `fix(nlp_v2): preserve execution scope before final freeze` (hash recorded next phase). Phase19 commit: `6085129`.

## Phase 21 — post-development descriptive regression evaluation

- **Objective:** one-way aggregate regression measurement after committed backend freeze, never a new untouched test estimate.
- **Files changed:** new model/assistant aggregate reports and interpretation/context hashes, comparison tables, evaluation plan, README/runbook links and Phase20 timing-only doc correction. Backend/evaluators/model/data unchanged.
- **Execution:** existing evaluators each ran once into new paths from8ee8917fef1f3664ec53d25e38dc5b9134aec270. Fixed Chennai date2026-10-06 matches b9b2271 baseline. Freeze verification passed before/after. No individual stress/reference failures/queries inspected, invalid replacement run or adaptive retry.
- **Evidence:** selected model entire aggregate JSON equals historical report (stress accuracy0.8300283, Macro-F1.7917698). Assistant stress selected operation356→431/706, terminal164→285/706, statuses clarification520→367, unavailable150→306,OK22→19,OOS14,errors0. Clarification precision.1673→.1499 and recall.8878→.5612 decline explicitly; human subset, full language/switch/noise strata and original overlap/partial-group caveats recorded. More terminal/unavailable is not more factual travel answers.
- **Verification/review:** fresh GPT-6.1 Sol xhigh independently reconstructs aggregate count/metric/hash/freeze/schema and historical preservation; no critical/high/medium findings. One low new-report Markdown table-layout finding fixed without evaluator edits/rerun. Phase20 timing typo corrected to15.61seconds (doc only). Diff check passes; no behavioral test rerun needed after602 full pass because this phase has no runtime changes.
- **Limitations:** observed historical sets and original validation overlap, nested human subset and partial contrast groups; no aligned domain facts/slot IDs. [Comparison](../../reports/nlp_v2/post_development_regression/comparison.md) is explicitly descriptive. No backend/model/prompt tuning follows. Next frontend phase is presentation-only.
- **Commit:** `docs(nlp_v2): record post-development descriptive regression` (hash recorded next phase). Phase20 freeze commit:`8ee8917`.

## Phase 22 — frontend polish (verified)

- **Objective:** presentation-only status/source/caveat clarity after backend freeze.
- **Files changed:** Streamlit, focused UI regressions, frontend plan/QA record and desktop evidence. API/contracts/backend/model/data/evaluators unchanged from `8ee8917`.
- **Behavior:** five readable status labels, persistent no-live snapshot notice, dated/source-backed panels and partial/hub caveats. Clarification no longer exposes canonical IDs; table labels omit direction/stop debug identifiers. Unavailable/error never show success panels. Nullable optional coverage metadata is guarded against renderer exceptions.
- **Verification:** seven initial UI red cases and three reviewer crash red cases reproduced/fixed; 37 focused UI pass, full 611 pass in 15.01 seconds, compile/pip/diff pass. Seven real API replies cover all five statuses plus fare/stops/nearest; primary and reviewer AppTest render without exceptions. Backend freeze diff is empty.
- **GPT-6.1 Sol xhigh review:** one medium optional-metadata crash and one low raw-direction-code usability finding fixed; independent seven real replies plus five malformed variants render safely. Unresolved critical/high/medium/low code findings = 0. Current post-CSS visual confirmation passed; reviewer inspected all eight current screenshots and granted final Phase22 signoff with0critical/high/medium/low.
- **Visual QA:** browser access temporarily disappeared, then returned. Current1280×900 and390×844 layouts verified for all five real API statuses. Header clears toolbar; fare/source/date/caveats wrap; clarification revision controls usable; no success panels for non-OK replies. Body/document widths equal viewport widths, temporary viewport reset. Current screenshots in frontend QA record.
- **Commit:** `feat(nlp_v2): clarify demo statuses and source limits` (hash recorded next phase). Phase21 commit: `fa4aaf7`.

## Phase 23 — first final review and historical governance block

- README, architecture, runbook/demo instructions and supported/partial/unsupported limitations have prepared updates, with611 verification and honest observed-development/descriptive-evaluation claims. Artifact/setup instructions and preserved reports remain linked.
- **Fresh GPT-6.1 Sol xhigh complete-project review:** 0 critical, 0 high, 1 medium unresolved. Reviewer independently passed443 focused tests in7.42seconds, verified frozen source/report/assets and reproduced timetable location-scope loss with the real selected model. Three named locations select first/last and drop the middle; a timetable via can replace the destination. The shared extractor also serves first/last and frequency. Primary independently reproduced using new synthetic intended-intent contract probes; no held-out item inspection or evaluator rerun. [Evidence and scoped proposal](../../reports/nlp_v2/final_review/review.md).
- **Documentation corrections:** stale future Phase21 wording now describes the completed valid run. Fare scope discloses the existing omitted-class Ordinary default. Overbroad timetable-scope preservation claims replaced with the confirmed limitation. Both low findings resolved by focused document re-review; current unresolved counts0critical/0high/1medium/0low.
- **Governance blocker:** Phase21 remains valid, so fixing the newly found backend defect conflicts with the user's “Otherwise, evaluation ends development” instruction. Backend remains unchanged at8ee8917; user decision requested to authorize a scoped new development iteration and separately labeled descriptive run, or retain the freeze with acceptance incomplete. Documentation cannot clear the medium gate.
- **Continuation audit:** prior turn made progress by completing/reviewing/committing/pushing Phase22. Fresh source/report/asset hashes, Git inventory and bounded secret-prefix checks pass; remote main equals localb0b3139. [Read-only evidence](../../reports/nlp_v2/final_review/preparation_audit.md). Remaining changes are documentation only. No explicit governance answer has arrived, and continuation alone does not override the post-evaluation freeze.
- Current desktop/narrow visual QA is complete. Medium governance resolution, requirement audit, final verification, clean focused Phase23 commit/push and project closure remain required. The full objective remains incomplete; this preparation is not final acceptance. Phase22 completed and pushed as `b0b3139`; Phase23 remains uncommitted pending governance resolution.

- **Blocked audit:** the same frozen-governance conflict persisted across three consecutive goal turns. The prior turn completed a reviewed read-only preservation audit; current revalidation confirms unchanged backend and one unresolved medium finding. No explicit authorization arrived, and no meaningful authorized work remains that can clear final acceptance. Goal is being marked blocked pending the user decision; scope is unchanged.

## Original UI restoration — separately requested

- The user requested the original style from old logs. The preserved pre-T3
  MandiPulse workbench provided the parchment/linen, oxblood, small-radius rules,
  Cormorant/Manrope/IBM typography and masthead/sidebar language.
- `app/transit_theme.html` and static Streamlit framing restore that style;
  six API/render function bodies remain identical. No old prototype/model/debug
  workflow returns. All five T3 statuses, caveats and clarification resubmission
  remain. Desktop1440×1000/mobile390×844, focus and no-overflow QA passed.
- 37 frontend passes; fresh GPT-6.1 Sol xhigh signoff zero findings. Commit
  `7cac770` pushed. [Evidence](../../reports/nlp_v2/restored_ui_qa/qa.md).

## Phase23 — explicitly authorized timetable correctness exception

- **Authorization:** the user accepted Phases11–22 and explicitly superseded the
  evaluation-ends-development restriction only for the independent review's
  timetable route-scope defect. The old blocked audit above records the prior
  state; it is superseded by this authorization, not erased.
- **Scope:** slots.py/assistant.py only: explicit origin/destination roles cannot
  be overwritten by waypoint ordering. All recognized spans remain ordered;
  route/time/date constraints persist. Extra/conflicting stops clarify; waypoint
  requests explicitly return unavailable before execution because no canonical
  waypoint filter exists. Ordinary two-stop behavior stays unchanged. No aliases,
  domain/model/schema/taxonomy/preprocessing/research changes.
- **TDD:** 63 new fixture-only synthetic cases produced51 failures/12 controls
  passing on the frozen implementation. Three review-driven old-extractor
  metadata cases failed before the optional-field compatibility correction.
  Final66 regressions cover all three timetable intents, English/Hindi/Roman/
  mixed/noisy/reordered/unknown waypoint and third-stop structure.
- **Verification:** 454 focused passed7.89s, full677 passed18.12s; compileall/pip/
  diff pass. Selected artifact validator and frozen Git/data/report hashes pass.
- **Scoped GPT-6.1 Sol xhigh:** independent39 public-contract probes and27 frozen
  ordinary extraction comparisons pass. One low metadata compatibility finding
  reproduced/fixed/reviewed. Final unresolved critical/high/medium/low=0.
- **Separate behavioral commit/new freeze:** `e008c0474c1301a3b442b31761f31c79e7dec446`
  (`fix(nlp_v2): preserve timetable route scope`), pushed to main before evaluation.
- **Historical preservation:** original validPhase21 freeze8ee8917 and all reports
  remain byte-for-byte unchanged. Independent synthetic review evidence caused
  the correction, never individual held-out failures or aggregate targeting.
- **Post-fix measurement:** exactly one unchanged complete-assistant evaluator
  invocation, reference date2026-10-06, new Phase23 post-fix descriptive directory.
  It measures the already observed set; no untouched/independent/replacement claim.
  Model/checkpoint unchanged, so no model-only rerun. Aggregate context/comparison
  and final whole-project signoff are recorded below when verified.

- **Verified post-fix aggregates:** stress706 intent0.8271955, selected431/706,
  terminal285/706; statuses367 clarification/306 unavailable/19OK/14OOS/0error.
  Clarification TP55/FP312/FN43/TN296, precision0.1498638/recall0.5612245.
  Human350 selected222/350, terminal143/350;182clarification/153unavailable/
  10OK/5OOS/0error; precision0.2527473/recall0.6052632. All metrics and every
  intent/language/code-switch/noise stratum exactly equal Phase21. This is a
  descriptive observation, not proof of scope semantics or a promotion target.
  No tuning follows. [Context/comparison](../../reports/nlp_v2/phase23_post_fix_descriptive/comparison.md).

- **Final primary audit/runtime:** frozen research/Phase21 diffs empty, five
  Phase21 report hashes/context preserved, Phase23 evaluated source/report hashes
  verified, artifact validator exact bytes/16T3/raw64/revision passes. Inventory,
  bounded credential-prefix and final document-link checks pass. Refreshed local
  API verifies real-model three-stop clarification, trailing-waypoint explicit
  refusal with correct destination, and existing fare OK; no tuning. Restored
  UI/local API remain available for the user's open demo.

- **Fresh final whole-project GPT-6.1 Sol xhigh review:** independent677 passes
  in18.06s and all artifact/source/report/research/renderer audits pass. Final
  gate0critical/0high/1medium/0low: unknown coordinated third timetable stop is
  dropped because the new guard counts canonical spans only. Primary reproduced
  three new fixture-only reds outside the repository suite. This remains the
  authorized defect; no unrelated issue or held-out targeting. [Evidence and
  concrete proposal](../../reports/nlp_v2/final_review/review.md).
- **Governance/remaining acceptance:** the exactly-one Phase23 post-fix run has
  completed and remains valid for e008c047, just as original Phase21 is valid
  for8ee8917. No further behavioral change or evaluator invocation has occurred.
  An explicit reconciliation is required for a follow-up narrow correctness
  freeze and any additional descriptive measurement. Final implementation is
  not COMPLETE while the medium remains. Report/document commits preserve the
  actual sequence and do not grant acceptance.
