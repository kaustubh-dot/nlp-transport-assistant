# T3 Dispatch Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a production T3 dispatch contract with explicit behavior for all 16 frozen intents.

**Architecture:** A focused `src/nlp_v2` package validates structured predictions and canonical slots, maps intent to operation, and invokes an injected domain service. Unconnected services return an explicit unavailable state.

**Tech Stack:** Python 3.12 standard library, pytest.

**Spec:** `docs/superpowers/specs/2026-10-06-t3-dispatch-contract-design.md`

## Global Constraints

- Frozen T3 contains exactly 16 labels; do not change research artifacts.
- Held-out and reference examples are evaluation-only.
- Never fabricate transport facts or realtime results.
- Keep the legacy seven-label prototype operational until the new application path is connected.

## Review Focus

- Unknown intent: reject before invoking any service.
- Missing route or station information: clarify without a service call.
- Realtime query: explicit unavailable state even when a service is injected.
- Multiple goals or ambiguous intent: preserve candidate labels and request clarification.
- Service failure: return an error state without false transport data.

### Task 1: T3 prediction and slot validation

**Files:** Create `src/nlp_v2/contracts.py`, `src/nlp_v2/__init__.py`; test `tests/test_t3_dispatch.py`.

**Interfaces:** `IntentPrediction(primary_label, acceptable_labels, confidence, clarification_reason)`; `validate_prediction(prediction)`; `missing_slots(intent, slots)`.

- [x] Write literal table tests for all T3 intents and specific missing/conditional-slot tests.
- [x] Run `.venv/bin/python -m pytest tests/test_t3_dispatch.py -q` and observe the missing contract failure.
- [x] Implement immutable prediction, canonical slot allowlist, and missing-slot rules.
- [x] Run the focused tests and verify green.

### Task 2: Dispatcher and unavailable domain service

**Files:** Create `src/nlp_v2/dispatch.py`; extend `tests/test_t3_dispatch.py`.

**Interfaces:** `dispatch(prediction: IntentPrediction, slots: Mapping[str, object], service: DomainService | None = None) -> DispatchResult`; `DomainService.execute(operation, slots) -> ServiceResult`.

- [x] Write failing tests for service invocation, missing slots, ambiguity, realtime, out-of-scope, and service errors.
- [x] Run focused tests and confirm expected red failures.
- [x] Implement the mapping and result states with an unavailable default service.
- [x] Run focused tests, then `.venv/bin/python -m pytest -q`; record unrelated historical failures.
- [x] Request fresh Astra Low phase review, reconcile findings, rerun verification, and commit Phase 1.
