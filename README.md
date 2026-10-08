# NLP v2 Multimodal Transport Assistant

A local Chennai transport assistant using the frozen **T3 Direct Dispatch taxonomy (16 intents)**, a selected MuRIL checkpoint, a read-only canonical SQLite snapshot, a JSON API, and a Streamlit chat interface. It accepts English, Hindi, Roman Hindi, Hinglish, and mixed-script text.

Published bus route sequences, directional route candidates, timetable records, dated fare records, and geometric nearest stops are connected. Verified multimodal transfers, current operating status, ticket/pass policy, and many accessibility/facility facts are unavailable in the snapshot. Responses expose these limits and request clarification when needed. This is a local demonstration; published records require operator verification for travel.

## Setup and run

Use Python 3.12 from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-nlp-v2.txt
export HF_HOME="$PWD/.cache/huggingface"
```

**Required model assets:** the selected checkpoint is approximately 950 MB and is intentionally excluded from Git. Supply the original `t3_muril_seed42_best.pt` at `experiments/nlp_v2/gate_b2/t3_muril_seed42_best.pt`, then prepare the pinned MuRIL tokenizer/config cache. Follow the [asset preparation steps](docs/nlp_v2/production_runbook.md#required-assets) before starting. The canonical database is already tracked; the prototype DB builder is not part of T3 setup.

Use the [artifact transfer and validation workflow](docs/nlp_v2/model_artifact_workflow.md) to check supplied bytes before startup:

```bash
.venv/bin/python -m scripts.nlp_v2.validate_model_artifact
```

Run the API:

```bash
python -m app.api
```

In another terminal, activate the same environment and set the same cache path:

```bash
source .venv/bin/activate
export HF_HOME="$PWD/.cache/huggingface"
streamlit run app/streamlit_app.py --server.address=127.0.0.1
```

Open `http://127.0.0.1:8501`. The API defaults to `http://127.0.0.1:8765`. Each clarification asks for a revised complete question.

The **English / हिंदी / Hinglish** selector changes the website's main text and curated assistant replies, including saved replies. Type questions in any supported language; the original question reaches the API unchanged. Language changes preserve history and unsubmitted drafts. Canonical stop names, route codes, amounts, dates and source identifiers stay unchanged. Unmapped explanations remain verbatim with a localized label; some built-in Streamlit controls remain English.

Choose **Bus, Metro, Rail (suburban), or MRTS** to apply that mode to subsequent questions. A mode explicitly written in the question takes priority; **Any mode** clears the default. **Published records** opens the source-coverage panel. Mode selection and saved history survive language changes. Typography and widget colors share the original parchment/oxblood theme.

## Verification and results

```bash
python -m pytest -q
python -m pip check
```

The verified local environment passes **1,344 tests**. The new [400-question language QA](reports/nlp_v2/language_400_qa_2026_10_08/summary.md) preserves 200 Hindi and 200 Hinglish questions, actual API responses, browser evidence and manual semantic judgments. It exposed bounded parsing defects now corrected, and substantial remaining recognition/source gaps. The retained intent model is unchanged. Earlier [language-selector QA](reports/nlp_v2/language_toggle_qa_2026_10_08/summary.md) covers 96 questions, and [frontend QA](reports/nlp_v2/frontend_qa/qa.md) records all five real API states. No lint/type checker is configured. Tests include strict real-checkpoint inference, synthetic contract/integration/UI cases, and frozen research integrity checks; they do not establish factual travel-answer accuracy.

- [Supported scope and known limitations](docs/nlp_v2/known_limitations.md)
- [Development acceptance](docs/nlp_v2/development_acceptance.md): answerable coverage **24/50→42/50**, false-positive clarification **30/104→3/104** on the observed frozen development suite.
- [Architecture and the 16 operation behaviors](ARCHITECTURE.md)
- [Setup, inference, optional training, evaluation and demo runbook](docs/nlp_v2/production_runbook.md)
- [Model manifest](models/nlp_v2_t3_manifest.json) and [phase progress](docs/nlp_v2/production_progress.md)
- [Frozen model evaluation](reports/nlp_v2/production_eval/production_t3_evaluation.md): stress intent accuracy **0.8300**, Macro-F1 **0.7918**.
- [Frozen complete-assistant evaluation](reports/nlp_v2/assistant_eval/assistant_evaluation.md): on 706 stress queries, **520 clarifications, 150 unavailable, 22 ok, 14 out of scope**; terminal dispatch accuracy **0.2323**, including correct unavailable/rejection operations. These are contract metrics, not factual-answer metrics. The frozen stress/reference sets contain training-family overlap, so full scores are descriptive rather than independent family-held-out estimates. These are the historical baseline reports. Subsequent phases use only the separate development suite and allowed validation; the new [post-development descriptive regression evaluation](reports/nlp_v2/post_development_regression/comparison.md) ran once from freeze `8ee8917`. Terminal dispatch improves 0.2323→0.4037, chiefly alongside more unavailable responses; historical OK answers and clarification precision/recall decline. Phase21 remains a valid unchanged historical result. The final independent review subsequently found a timetable scope defect, corrected under an explicit user-authorized exception with synthetic tests and a fresh review. The post-review backend freeze is `e008c0474c1301a3b442b31761f31c79e7dec446`; the separate [Phase23 post-fix descriptive regression](reports/nlp_v2/phase23_post_fix_descriptive/comparison.md) measures that correction once on the already observed set. No metric-driven tuning followed this run; the later synthetic review finding and authorized residual correction are disclosed below.

The original MandiPulse parchment/oxblood style was restored from the preserved UI history while retaining the T3 API and five response states. [Restoration evidence](reports/nlp_v2/restored_ui_qa/qa.md) includes desktop/mobile screenshots and independent review. Timetable waypoints are explicitly unsupported; extra or conflicting stops clarify before partial execution. [Final acceptance audit](docs/nlp_v2/final_acceptance_audit.md) records the complete closure gates.

## Research and preserved prototype

T3 is final. [Gate B.3 decision](reports/nlp_v2/gate_b3/GATE_B3_TAXONOMY_DECISION.md), Gate B.2/B.3 experiments, annotations, and human reference labels remain frozen. T2 is a historical comparator. Consult the [handoff](docs/nlp_v2/NLP_V2_HANDOFF.md) and [split policy](docs/nlp_v2/split_and_leakage_policy.md) before new model work; the runbook records discovered overlap and safe replacement-training behavior.

The earlier seven-label UI is preserved at `app/legacy_streamlit_app.py`; `src/pipeline.py`, [PRD](PRD.md), [roadmap](ROADMAP.md), and earlier benchmark documents describe that prototype. They are not the default T3 application path.

Code is MIT licensed. External model/data licensing must be checked per artifact before redistribution.

The subsequent final review found an unknown coordinated third-stop defect.
The user's “Fix it” authorized its narrow correction, now frozen at `1bf748c9e4cc35e75b1db004f5b74c9dad1eeb1b`.
Unknown extra timetable locations clarify before partial execution; supported
modifier clauses and ordinary requests retain their behavior. [Follow-up review](reports/nlp_v2/final_review/unknown_stop_scope_review.md)
records 201 additional synthetic cases and zero unresolved scoped findings.
Both earlier descriptive runs and contexts remain unchanged for their recorded
sources. No additional evaluator ran; final corrected-source aggregate performance
has not been measured. [Final source provenance](reports/nlp_v2/final_review/final_source_context.json)
records the separate freeze and preserved historical hashes.
