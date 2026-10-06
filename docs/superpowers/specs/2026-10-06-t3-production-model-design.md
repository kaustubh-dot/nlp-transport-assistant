# T3 production model design

**Intent:** Use a validated existing 16-class T3 MuRIL checkpoint for production inference and provide a separate reproducible training entrypoint that never reads or writes frozen held-out research artifacts.

## Existing artifact decision

The Gate B.2 seed-42 T3 checkpoint is locally available and its 16-way head loads with all keys matched. The three existing seeds have reported validation Macro-F1 0.91555 (42), 0.86053 (101), and 0.86148 (777). An audit found 78 of 410 validation rows share a train `family_id` or `semantic_family_id`, violating the documented split policy. Without editing frozen CSVs, the three existing checkpoints were compared on the 332 disjoint validation rows: Macro-F1 0.85122 (42), 0.84260 (101), and 0.82535 (777). Seed 42 remains the validation-only selection. The original reported scores are retained with the leakage caveat, not treated as family-disjoint evidence. This promotes an existing checkpoint; it does not rerun Gate B.2 or claim a new training run. The checkpoint remains ignored by Git. A committed manifest records its relative path, SHA-256, pinned base model revision, exact class order, raw-query preprocessing, max length 64, train/validation hashes, and selection basis. Fresh checkouts must supply this local checkpoint or train a replacement.

## Inference

`T3IntentClassifier` reads the manifest, verifies taxonomy/class order and checkpoint hash, loads MuRIL config and tokenizer from the pinned revision, constructs the 16-label model, then strictly loads the state dict. Inference tokenizes the raw query exactly as the original Gate B.2 trainer did, without the legacy normalizer or heuristic override. It returns `IntentPrediction` with a T3 label and probability. Missing/incompatible assets fail clearly; there is no T2 or seven-label fallback. The pinned source files may be in the local Hugging Face cache; any network retrieval is an explicit setup action, not hidden at inference time.

## Reproducible optional training

`scripts/nlp_v2/train_production_t3.py` is a separate train/validation-only entrypoint. It reads only `gate_b2_train.csv` and `gate_b2_validation.csv`, checks their hashes, excludes validation rows with train family, semantic family, or query overlap, seeds random/NumPy/PyTorch, trains MuRIL using disjoint validation Macro-F1 for early stopping, and writes checkpoint plus metadata to a new output directory. It never imports the Gate B.2 trainer or opens `stress_eval`/human reference files. The smoke mode uses a small random MuRIL-shaped config and a tiny train/validation subset to verify the pipeline on CPU; its output is marked non-production. Full runs use the pinned pretrained backbone and require appropriate compute. Output paths inside frozen research directories are rejected.

## Verification

Tests validate manifest consistency and hash rejection, strict 16-class CPU loading and synthetic inference, train/validation loader isolation, disjointness checks, and smoke metadata. A smoke run verifies training mechanics on this CPU-only host. Final held-out evaluation remains deferred until the full assistant is frozen.
