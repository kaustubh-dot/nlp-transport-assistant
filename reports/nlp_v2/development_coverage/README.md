# Development-only assistant coverage

Suite v1 is authored from T3 contracts and the canonical snapshot. It is an
observed development instrument, not an untouched test/generalization estimate.
The SHA-locked suite/manifest live in `data/nlp_v2/development/`.

Run from the root with the prepared Python environment and pinned model cache:

```bash
HF_HOME="$PWD/.cache/huggingface" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  .venv/bin/python -m scripts.nlp_v2.evaluate_development_coverage \
  --output-dir /tmp/nlp-dev-new-model-run
HF_HOME="$PWD/.cache/huggingface" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  .venv/bin/python -m scripts.nlp_v2.evaluate_development_coverage \
  --gold-intent --output-dir /tmp/nlp-dev-new-downstream-run
```

Output directories must be new/empty. A fixed Chennai date comes from the suite
manifest. The real-model run exercises production inference. Gold-intent runs
bypass it and diagnose the actual downstream path; their injected intent score
is not model accuracy. Genuine semantic ambiguity is also injected for that
mode, so its success cannot establish real classifier ambiguity detection.

Terminal contract success requires gold status, intent, relevant operation,
annotated slots, clarification reason/required candidates/inputs and evidence.
The false-positive clarification rate uses non-clarification gold cases as its
denominator. Answerable coverage uses gold OK cases and requires the complete
terminal/evidence contract; raw OK counts may include incorrect answers.
Source-shape checks alone do not verify transport facts. Diagnostic failure
flags may overlap and do not establish causal attribution.

Phase 12 records the production baseline before downstream changes. Reports
record source hashes and the dirty development source state, rather than
claiming a committed production freeze. No item-level historical evaluation
examples were used to author or tune the suite. The opaque normalized overlap
guard reports zero exact overlaps; semantic independence is not claimed.

Before v1 freeze, independent review tightened payload types and evidence-kind
compatibility, annotated true/false membership from canonical sequences, bound
nearest evidence to the gold anchor/mode, validated manifest metadata and fixed
noise/language tags. Two noisy prompts were corrected to match their intended
noise class (adjacent-key substitution and vowel omission). These authoring
corrections occurred before any production change; final baseline reports were
regenerated and the aggregate scores remained unchanged.
