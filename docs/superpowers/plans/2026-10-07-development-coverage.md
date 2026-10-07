# Development coverage implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. The primary agent implements; GPT-6.1 Sol xhigh independently reviews each phase.

**Goal:** establish a separate versioned coverage improvement loop for all 16 T3 intents.

**Architecture:** JSON suite plus strict manifest loader and contract scorer. Real production inference and explicitly labeled gold-intent diagnostics share the same canonical assistant path.

**Tech Stack:** Python 3.12, pytest, JSON, existing read-only SQLite service and MuRIL.

**Spec:** `docs/nlp_v2/development_coverage_design.md`, user phase 12 requirements.

## Global Constraints

- Exactly 16 T3 intents; fixed model label order/raw preprocessing.
- No held-out query examples/labels/outcomes used for development targeting.
- Canonical DB and historical research untouched.
- Reviewer GPT-6.1 Sol xhigh; unresolved critical/high/medium = 0.
- User requests autonomous inline implementation and focused main commits/pushes.

## Review Focus

- Gold status must represent product behavior, including honest unavailable, not bless existing defects.
- No OK without evidence and intended operation/entity.
- Generic duplicate names must not select an arbitrary physical stop.
- Diagnostic injected intents must not inflate reported model accuracy.
- Leakage checks must never expose held-out text/labels or claim semantic independence.

### Task 1: contract metrics and suite validation

**Files:** create `scripts/nlp_v2/evaluate_development_coverage.py`, `tests/test_t3_development_coverage.py`.
**Interfaces:** `score_cases(cases: list[dict], replies: list[AssistantReply]) -> dict`; `load_suite(path: Path, manifest_path: Path) -> list[dict]`; `heldout_fingerprints(stress: Path, reference: Path) -> set[str]`.

- [x] Write tests: wrong operation/status must lower terminal accuracy; wrong entity must lower gold-slot and answerable success; absent source must fail evidence; clarification reason/missing slots/candidates must be checked. Explicit denominators and false-positive clarification rate verified with hand-authored replies.
- [x] Run `.venv/bin/python -m pytest tests/test_t3_development_coverage.py -q`; expect missing evaluator until implemented.
- [x] Implement strict suite validation and scoring; keep per-case output development-only.
- [x] Add drift, duplicate-id/query, malformed enum/status, synthetic overlap and empty-output guards; watch tests fail before each corresponding behavior.
- [x] Run focused tests; expected all pass.

### Task 2: author and freeze development v1

**Files:** create `data/nlp_v2/development/assistant_coverage_v1.json`, accompanying manifest; update design and progress.
**Interfaces:** validated suite consumed by evaluator; manifest hashes frozen after review.

- [x] Author five languages for each of 16 intents plus contract contrasts, from newly constructed language and canonical entities.
- [x] Check expected slots/status/evidence against independently inspected canonical data; do not assert exact unverified transport facts.
- [x] Check opaque held-out fingerprint overlap; expected zero; fix accidental authoring collision without inspecting held-out text.
- [x] Freeze suite SHA and DB hash, provenance limitations in manifest.

### Task 3: reproducible evaluation and phase review

**Files:** evaluator CLI, `reports/nlp_v2/development_coverage/phase12_baseline.json`, progress record.
**Interfaces:** `evaluate(output_dir: Path, *, gold_intent: bool = False) -> dict` records real-model and downstream scores without conflation.

- [x] Test evaluator refusal of existing/frozen output before model loading; implement minimal CLI.
- [x] Run real-model and gold-intent development baselines with fixed date/cache/two threads.
- [x] Run full pytest, compilation and diff checks; expect all pass.
- [x] Focused Sol xhigh re-review of four medium/two low fixes before phase exit.
- [x] Record final review, commit focused phase, push main; proceed to Phase 13.
