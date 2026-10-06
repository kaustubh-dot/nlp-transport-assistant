# T3 Production Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load the selected T3 checkpoint reproducibly and offer a safe train/validation-only production trainer.

**Architecture:** A committed manifest identifies the existing seed-42 checkpoint and pinned MuRIL inputs. `T3IntentClassifier` validates and loads it without fallback. An independent trainer supports future reproduction and a CPU smoke run without touching frozen Gate B.2 artifacts.

**Tech Stack:** Python 3.12, PyTorch, Transformers, scikit-learn, pytest.

**Spec:** `docs/superpowers/specs/2026-10-06-t3-production-model-design.md`

## Global Constraints

- T3 only: exact 16-class checkpoint head and original Gate B.2 class index order.
- Training/model selection may use train/validation only.
- No automatic reads from stress/reference or writes to frozen Gate B.2 paths.
- The existing checkpoint is local and ignored by Git; never add its weights to commits.
- Host has no CUDA device; CPU smoke output is not a final model.

## Review Focus

- Manifest label order mismatch: loading must fail before inference.
- Checkpoint missing/hash mismatch: loading must fail rather than fallback.
- Legacy normalized preprocessing: raw-query inference must match training.
- Overlapping train/validation families: trainer must reject.
- Smoke output: metadata must make it impossible to mistake for the selected production checkpoint.

### Task 1: Frozen checkpoint manifest and inference

**Files:** Create `models/nlp_v2_t3_manifest.json`, `src/nlp_v2/model.py`; test `tests/test_t3_model.py`.

**Interfaces:** `T3IntentClassifier(manifest_path=None).predict(query: str) -> IntentPrediction`; `load_manifest(path) -> dict`.

- [x] Write failing tests for metadata validation, missing/hash-mismatched checkpoint, and synthetic CPU prediction.
- [x] Run focused tests and observe red.
- [x] Add selected-checkpoint manifest and strict T3 model loader.
- [x] Run focused tests and verify green.

### Task 2: Safe production trainer and smoke run

**Files:** Create `scripts/nlp_v2/train_production_t3.py`; extend `tests/test_t3_model.py`.

**Interfaces:** `load_training_splits(train_path, validation_path)`; `train(config) -> metadata`; CLI `--smoke --output-dir ...` and full mode.

- [x] Write failing tests for split isolation, overlap rejection, forbidden output paths, and smoke metadata.
- [x] Run focused tests and observe red.
- [x] Implement train/validation-only training with early stopping and separate outputs.
- [x] Run CPU smoke training and focused/full tests; record compute limits.
- [x] Request fresh Astra Low review, fix findings, verify, and commit Phase 3.
