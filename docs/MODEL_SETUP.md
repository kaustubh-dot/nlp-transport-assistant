# Required model asset

The selected MuRIL checkpoint is supplied separately by the project owner. No public download URL for the selected weights is provided. A clone contains the [manifest](../models/nlp_v2_t3_manifest.json), [artifact provenance](../models/nlp_v2_artifact_provenance.json), canonical database and source code.

After [installing the runtime](../README.md#setup), place the **950,358,409-byte** `t3_muril_seed42_best.pt` at:

```text
experiments/nlp_v2/gate_b2/t3_muril_seed42_best.pt
```

This path is retained by the production manifest; only the supplied local weights belong there and they are excluded from Git. Expected SHA-256:

```text
abac66fc9fa29212c7565117ae326e34f02b64e76dbb177c61e9661517803196
```

Check the supplied bytes:

```bash
python -m scripts.nlp_v2.validate_model_artifact
```

Prepare the pinned public tokenizer and configuration cache once, with network access:

```bash
export HF_HOME="$PWD/.cache/huggingface"
python - <<'PY'
from transformers import AutoConfig, AutoTokenizer
model = "google/muril-base-cased"
revision = "afd9f36c7923d54e97903922ff1b260d091d202f"
AutoTokenizer.from_pretrained(model, revision=revision)
AutoConfig.from_pretrained(model, revision=revision)
PY
```

This downloads tokenizer/config assets, without fetching base-model weights. Keep the same `HF_HOME` in API, UI and test terminals. Inference loads locally with the pinned revision, fixed 16-label order, raw-question preprocessing and maximum length 64. Missing, corrupt or incompatible assets fail loading.

Verify strict loading before starting:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  python -m scripts.nlp_v2.validate_model_artifact --load-model
```

Successful JSON reports `sha256_verified: true` and `strict_model_loaded: true`. Hash validation confirms supplied bytes; it makes no model-quality or travel-fact claim. Tokenizer warnings about Mistral regex detection do not change this BERT/WordPiece configuration; do not apply `fix_mistral_regex=True` to the pinned tokenizer.
