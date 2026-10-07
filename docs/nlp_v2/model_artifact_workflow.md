# Supplying and verifying the selected T3 checkpoint

A Git clone includes the canonical DB, strict model manifest and artifact
provenance, but excludes the **950,358,409-byte** checkpoint (906.33 MiB). There is
no repository public artifact URL. Obtain the exact file from the project/run
owner using an authorized local/private transfer; no external upload or account
connection is part of this workflow.

Place those bytes at:

```text
experiments/nlp_v2/gate_b2/t3_muril_seed42_best.pt
```

The expected SHA-256, stored in the trusted Git manifest, is:

```text
abac66fc9fa29212c7565117ae326e34f02b64e76dbb177c61e9661517803196
```

Create the Python environment using the [runbook setup](production_runbook.md#install-and-cache-preparation)
before these commands. For example, after receiving a local file, from repository root:

```bash
mkdir -p experiments/nlp_v2/gate_b2
cp --no-clobber /path/to/received/t3_muril_seed42_best.pt \
  experiments/nlp_v2/gate_b2/t3_muril_seed42_best.pt
.venv/bin/python -m scripts.nlp_v2.validate_model_artifact
```

Replace only the example received-file path. Do not overwrite an existing valid
artifact or recreate frozen research to obtain it. A missing/wrong copy exits
nonzero with an actionable message; no random, legacy or smoke fallback is loaded.
The basic command checks strict T3 metadata and content SHA without importing
torch or requiring a tokenizer cache. Hash verification identifies trusted bytes;
it is not a current transport-fact check or a new model-quality evaluation.

Prepare the pinned public tokenizer/config cache using the
[runbook installation steps](production_runbook.md#install-and-cache-preparation),
then verify actual loading before starting the API:

```bash
export HF_HOME="$PWD/.cache/huggingface"
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  .venv/bin/python -m scripts.nlp_v2.validate_model_artifact --load-model
```

Successful JSON reports `sha256_verified: true`; the second command additionally
reports `strict_model_loaded: true`. It uses the same existing strict CPU loader
as production, with fixed 16-label order, pinned MuRIL revision, raw-query
preprocessing and length64. Cache preparation needs public upstream network access;
startup/validation never automatically downloads the selected weights.

[Manifest](../../models/nlp_v2_t3_manifest.json) and
[provenance](../../models/nlp_v2_artifact_provenance.json) document path, hash,
original epoch/selection caveat and current retention decision. The Phase17
replacement artifact is **unselected** and remains local under the ignored
`experiments/nlp_v2/production_runs/` directory. Its matching metadata alone does
not authorize promotion. Preserve original weights; any future candidate must
pass an independently reviewed validation-only selection workflow.

After supplying the required file and cache, follow the runbook to start the
API/UI and run tests. A complete fresh-environment dependency installation and
owner-to-new-machine transfer were not performed here; actual selected-byte
hashing and strict local loading are verified.
