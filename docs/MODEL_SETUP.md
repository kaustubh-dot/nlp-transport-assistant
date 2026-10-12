# Model files and setup

The default TF-IDF baseline and nine-class MuRIL head are included in Git. The large seed encoder and fine-tuned layer patch are available from the [submission-models-v1 release](https://github.com/kaustubh-dot/nlp-transport-assistant/releases/tag/submission-models-v1).

| File | Purpose | Distribution |
| --- | --- | --- |
| `models/project/tfidf.pkl` | Character TF-IDF and Logistic Regression baseline | Git |
| `models/project/intent_head.pt` | Nine-class neural classifier head | Git |
| `models/tokenizer/` | Pinned MuRIL configuration, vocabulary and token settings | Git |
| `models/assets/muril_seed_encoder.safetensors` | Starting encoder, with the unused classifier removed | Release, 950,247,248 bytes |
| `models/assets/encoder_last_two.pt` | Trained encoder layers 10 and 11 | Release, 56,713,146 bytes |

Follow the dependency installation in the [README](../README.md#enable-muril-and-model-comparison), then run:

```bash
python -m scripts.prepare_models
```

Setup downloads into temporary files, checks size and SHA-256, and replaces an asset only after verification. A repeated run keeps already verified files. Interrupted or corrupt downloads leave the installed file intact. The [manifest](../models/hindi_project_manifest.json) records model labels, hashes, tokenizer files, raw-input preprocessing, pooling and training settings. Loaders check the saved files and load weights strictly.

For an offline machine, copy the two release files to a directory and run:

```bash
python -m scripts.prepare_models --local-dir /path/to/downloaded-assets
```

Inference uses the tokenizer saved in this repository and local model files. It makes no Hugging Face requests. The encoder originated from `google/muril-base-cased` revision `afd9f36c7923d54e97903922ff1b260d091d202f`, followed by earlier transport training. The original source-checkpoint hash remains in the manifest as provenance. The exported encoder produced bit-for-bit identical features on the 90 diagnostic questions and four user questions.

Use the baseline pickle supplied by this repository or produced by the training script. Its SHA-256 is checked before loading. Retraining updates model files and their manifest together; do not replace a weight independently of the manifest.
