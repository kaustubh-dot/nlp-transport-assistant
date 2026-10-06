# T3 Slot Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract and resolve typed T3 slots from multilingual commuter utterances without guessing ambiguous entities or times.

**Architecture:** `CanonicalResolver` supplies exact canonical candidates from the read-only KB; `T3SlotExtractor` identifies surface spans and semantic slots by T3 role. An `ExtractionResult` carries slot and uncertainty state independently of intent prediction.

**Tech Stack:** Python 3.12, sqlite3, existing normalization, pytest.

**Spec:** `docs/superpowers/specs/2026-10-06-t3-slot-pipeline-design.md`

## Global Constraints

- Preserve the frozen 23-slot ontology and T3 16 intents.
- Do not read held-out stress/reference rows during extraction development.
- No unsupported entity or AM/PM inference.
- Canonical DB is read-only; no research files change.

## Review Focus

- Duplicate name across modes: clarify unless a hub or explicit mode resolves it.
- Same bus stop name at several poles: route context selects only a unique on-route node.
- `8 baje` and `kal`: preserve ambiguity and avoid execution.
- Route suffix `102A` or `102K#`: never truncate to base code.
- Unknown landmark: no fabricated canonical place ID.

### Task 1: Canonical name resolver

**Files:** Create `src/nlp_v2/entities.py`; test `tests/test_t3_slots.py`.

**Interfaces:** `CanonicalResolver(db_path).find_spans(text) -> tuple[EntitySpan, ...]`; `resolve(span, role, intent, mode=None, route_number=None) -> Resolution`.

- [x] Write temporary canonical DB fixture and failing tests for hub, mode, duplicates, route-constrained stop, and unknown names.
- [x] Run `.venv/bin/python -m pytest tests/test_t3_slots.py -q` and observe red.
- [x] Implement read-only DB name index, current-ID alias mapping, span matching, and resolution precedence.
- [x] Run focused tests and verify green.

### Task 2: Semantic and temporal slot extractor

**Files:** Create `src/nlp_v2/slots.py`; extend `tests/test_t3_slots.py`.

**Interfaces:** `T3SlotExtractor(resolver).extract(query: str, intent: str) -> ExtractionResult`.

- [x] Write failing synthetic query tests across English, Hindi, Roman Hindi, Hinglish, mixed script, route codes, enums, time, and relative day.
- [x] Run focused tests and observe red.
- [x] Implement explicit-only extraction and separate uncertainty metadata.
- [x] Run focused tests and full suite; record known historical failures.
- [x] Request fresh Astra Low review, fix valid findings with failing tests, verify, and commit Phase 2.
