# Project architecture

The demo runs in one Streamlit process through `app/streamlit_app.py`.

```text
Hindi or Hinglish question
    -> nine-intent classifier
    -> canonical name matching and slot extraction
    -> curated facts or read-only canonical lookup
    -> Hindi or Hinglish answer, intent, slots and sources
```

`src/hindi_project/model.py` loads the bundled TF-IDF baseline or the local MuRIL encoder, adapted layers and nine-class head. `encoder.py` uses the saved tokenizer and checks model-file hashes. Large assets are prepared by `scripts/prepare_models.py`; the baseline imports no PyTorch or Transformers modules. MuRIL uses attention-masked mean pooling and raw questions truncated to 64 tokens. Display language changes response rendering and leaves model input intact. Scores are uncalibrated model outputs.

`locations.py` builds the name index from the canonical SQLite snapshot and stored aliases. `assistant.py` extracts Hindi `से` and Hinglish `se` roles, station qualifiers, target modes and information types. The seven curated locations are example IDs. Typed queries can use other database names. Station context applies only to explicit references such as `इस स्टेशन` and `is station`.

`lookup.py` returns bounded published route options without selecting an ambiguous physical station silently. The shared modules in `src/nlp_v2/` supply canonical name resolution, slot rules, operation/result types and SQLite transport lookups. They remain because the academic assistant uses them. The retired API, earlier chat renderer and original intent classifier are absent from the submission.

Answers retain source boundaries. Railway/Metro qualifiers identify the anchor independently of a nearby target mode. Cross-source coordinate conflicts prevent unreliable distances. Central/Velachery MRTS guidance identifies Park Town as a separate station and leaves access and current service unverified. Missing schedules, facilities and walking paths remain unavailable. The database is read without mutation.

The interface keeps editable drafts, quick examples, five recent submitted questions, source-linked answers and a compact NLP panel. Comparison uses the last submitted question and its saved station context. A changed draft or setting leaves the old result labeled until submission. The fixed Hindi-Tamil phrasebook does not alter model input.

Training adapts only encoder layers 10 and 11 and the head, selecting an epoch by validation macro F1. Dataset generation, training and diagnostic evaluation are in `scripts/nlp_v2/`. The manifest records file hashes and settings. Classification, slot and pipeline metrics remain separate; synthetic data and development-exposed diagnostics do not establish passenger accuracy.
