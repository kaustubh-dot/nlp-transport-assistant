# Multilingual Remediation v2 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans. The primary agent implements; fresh GPT-6.1 Sol xhigh agents perform read-only reviews at the user-required gates.

**Goal:** Resolve the preserved high and four medium defect classes, then pass independent English, UI, source and safety gates before one committed-freeze challenge rerun.

**Architecture:** Preserve the failed v1 bytes and isolate v2 evidence. Add literal independently authored multilingual cases and production-facing regression tests. Extend existing semantic extraction and Streamlit turn persistence without changing raw classifier inputs or source safeguards.

**Tech Stack:** Python, pytest, SQLite canonical transport data, MuRIL T3 classifier, JSON HTTP API, Streamlit.

**Spec:** `/home/kaustubh/.codex/attachments/6b906686-4058-4821-a068-66be262771ce/Pasted text.txt` (preserved in v2 R0).

## Global Constraints

- Work on main; primary implementation and read-only GPT-6.1 Sol xhigh review.
- No individual frozen 400 examples inspected, paraphrased, tuned against or rerun before R9.
- V1 checkpoint, evidence, corpus, reports and protected research assets stay byte-identical.
- No cleanup. No automatic retraining. No safety relaxation to increase answer counts.
- R9 is a committed source freeze; R10 is exactly one real API rerun. No behavioral edits after R9/R10 without new authorization.

## Review Focus

- Pre/post exclusions around numeric, prefix and suffix route IDs must never dispatch excluded codes.
- Specific train noun modifiers must retain genuine independent mode mentions.
- Hindi combining marks must not create conjunctions inside words.
- Negative availability propositions must differ from instructions to avoid a mode.
- A queued Streamlit control rerun during an accepted POST must retain exactly one complete turn and its original mode.

### R1/R2: independent invariant suite

- [x] R0 archive and integrity manifest before source changes.
- [x] Create `reports/nlp_v2/multilingual_quality_v2/r1_invariants.json` with subsystem, mechanism, risk and invariant for all five findings.
- [x] Author `data/nlp_v2/remediation_v2/cases.json` with unique case/family IDs, scripts, literal slots/modes/states and safety expectations. Add contrast pairs across all four language forms and source/state categories.
- [x] Add `tests/test_multilingual_remediation_v2.py` and `tests/test_remediation_v2_frontend.py`; record five independent RED reproductions.

### R3: excluded routes (high first)

- [x] RED tests assert that excluded routes never appear in dispatched slots, positive codes survive, multiple/conflicting codes clarify; include units, dates and clock boundaries.
- [x] Modify `src/nlp_v2/slots.py`: collect route mentions with polarity instead of selecting a lexical first hit. Retain safe single-operation cardinality and Unicode suffix handling.
- [x] Run focused, existing extraction/assistant, English counterparts and full pytest sequentially. Fresh focused reviewer must report high=0 before R4.

### R4: four medium invariants

- [x] For each: record RED, implement root fix, run GREEN and nearby contrast tests.
- [x] `slots.py`: bounded specific-mode noun modifiers; Unicode-safe coordination; distinguish availability propositions from avoidance.
- [x] `app/streamlit_app.py`: persist accepted submission before execution yields and persist outcome before spinner teardown; resume interrupted pre-request turns without duplicate requests.
- [x] Fresh read-only review requires critical/high/medium=0.

### R5/R6/R7: independent product/model gates

- [x] Extend English counterparts for every affected intent, entity, time, default, API and UI state; semantic failures block.
- [x] Real API + Streamlit desktop/narrow QA using independently authored queries; persist evidence under v2.
- [x] Evaluate independent cases, legitimate multilingual validation and English. Retain original model unless wrong intent dominates and legitimate candidate selection satisfies all guards. Record decision.

### R8/R9: pre-freeze gate and committed freeze

- [x] Full pytest, English/API/UI tests, Python compile checks, pip check, integrity hashes and finalized model decision.
- [x] Fresh whole-system GPT-6.1 Sol xhigh review requires unresolved critical/high/medium=0; fix pre-freeze findings via RED/GREEN.
- [x] Commit source, record full SHA and model/DB/development/independent-suite hashes. No behavioral changes thereafter.

### R10/R11/R12: one challenge run and final gate

- [x] Exactly one 200 Hindi + 200 Hinglish real API run labeled post-remediation regression on previously observed challenge set. Independent semantic/source assessment into the six authorized categories.
- [x] Compare aggregate v1 recognition162/wrong1 and baseline175. Final recognition169/wrong0; material Bus27D regression means STOP.
- [x] Fresh final GPT-6.1 Sol xhigh review complete: C0/H0/M2, challenge not used for tuning; STOP reported without tuning or cleanup.
- [ ] R12 STOP: failed final gate; no push, cleanup or completion declaration.

### Subsequent publication authorization

On 2026-10-12 the user explicitly requested pushing the work. Commit and publish the frozen source and failed-gate reports to main. Preserve R11 failure and all evidence; no behavioral tuning, challenge reruns or cleanup.
