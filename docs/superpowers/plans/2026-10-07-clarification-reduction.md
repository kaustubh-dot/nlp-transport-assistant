# Clarification reduction implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Primary implements; fresh GPT-6.1 Sol xhigh reviews the phase.

**Goal:** remove non-actionable entity questions and align actual schedule inputs.
**Architecture:** safe optional canonical capability preflight; exact operational route-context index; existing contracts remain the validation gate.
**Tech Stack:** Python, pytest, canonical read-only SQLite.
**Spec:** `docs/nlp_v2/clarification_reduction_design.md`.

## Global Constraints

- Exactly 16 frozen T3 labels and operations; checkpoint/raw model input unchanged.
- No historical query targeting, research or DB edits.
- No fuzzy guesses, fabricated answers or silently discarded explicit entities.
- Phase exit unresolved critical/high/medium = 0; primary implements on authorized main.

## Review Focus

- Multiple real on-route candidates must clarify.
- An off-route explicit node must not be replaced.
- Capability DB errors must not become fabricated refusals.
- Explicit multi-goal/intent uncertainty must precede capability checks.
- Gold-intent reductions must remain distinct from real-model results.

### Task 1: executable inputs and exact context

**Files:** `src/nlp_v2/contracts.py`, `src/nlp_v2/entities.py`, focused dispatch/slots tests.
**Interfaces:** unchanged `missing_slots(intent,slots)` and `resolve(...)` signatures.

- [x] Write failing tests for station-or-stop-or-origin scheduling, route-required frequency, context keys `25R` matching canonical `25 R`, unique timing stop resolution, and multiple/off-route candidates.
- [x] Observe focused failures; implement minimal canonical requirements and exact mode-consistent index/context filtering.
- [x] Run focused tests plus suite downstream diagnostics; verify no guesses.

### Task 2: capability preflight and integration

**Files:** `src/nlp_v2/domain.py`, `src/nlp_v2/assistant.py`, `tests/test_t3_assistant.py`, development reports/progress.
**Interfaces:** `CanonicalTransitService.preflight(operation: str) -> ServiceResult | None`; assistant retains existing public reply shape.

- [x] Write failing real-canonical assistant tests for absent policy and verified-transfer/feature coverage, with ambiguity preservation and safe DB failure.
- [x] Implement narrow read-only preflight and optional integration after semantic/multiple-goal guards.
- [x] Run focused tests, v1 real-model/downstream before-after, full pytest/compileall/diff check.
- [x] Record clarification and false-positive clarification counts/rates, any remaining safety failures; fresh Sol xhigh review, fixes and verification.
- [x] Commit phase, push main, continue Phase 14 automatically.
