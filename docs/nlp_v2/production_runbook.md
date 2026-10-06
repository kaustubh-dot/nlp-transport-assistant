# Production T3 runbook

Run commands from the repository root using Python 3.12. T3 is the default application; historical baseline/database-generation commands are not required for it.

## Required assets

| Asset | Location | Availability |
|---|---|---|
| Canonical SQLite snapshot | `data/canonical/transit/canonical_transport.db` | Tracked, approximately 86 MB; production opens it read-only. |
| Production manifest | `models/nlp_v2_t3_manifest.json` | Tracked; fixed labels, preprocessing, MuRIL revision and checkpoint SHA. |
| Selected checkpoint | `experiments/nlp_v2/gate_b2/t3_muril_seed42_best.pt` | Local artifact, approximately 950 MB; intentionally ignored. Obtain the original artifact from the project/run owner or an authorized archive. There is no public download URL in this repository. |
| MuRIL tokenizer and config | Hugging Face cache | Public pinned upstream files; explicit preparation needed on a fresh machine. Production never downloads them automatically. |

Check the selected artifact:

```bash
sha256sum experiments/nlp_v2/gate_b2/t3_muril_seed42_best.pt
```

Expected SHA-256:

```text
abac66fc9fa29212c7565117ae326e34f02b64e76dbb177c61e9661517803196
```

Do not recreate the closed Gate B.2 benchmark to obtain weights. Without this artifact, the selected production model cannot start. The optional replacement trainer below supplies a separate development path, with a new checkpoint/manifest selection requiring its own development freeze and evaluation.

## Install and cache preparation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-nlp-v2.txt
export HF_HOME="$PWD/.cache/huggingface"
python - <<'PY'
from transformers import AutoConfig, AutoTokenizer
model = "google/muril-base-cased"
revision = "afd9f36c7923d54e97903922ff1b260d091d202f"
AutoTokenizer.from_pretrained(model, revision=revision)
AutoConfig.from_pretrained(model, revision=revision)
print("Pinned tokenizer and config cached")
PY
```

The explicit cache preparation requires network access to the public model repository. `.cache/` is ignored. Keep `HF_HOME` set in every API, UI, test, training, or evaluation terminal, or use an already prepared default Hugging Face cache consistently. The inference loader needs tokenizer/config plus the selected checkpoint, so this command does not fetch base-model weights. Full replacement training needs those additional weights.

The verified environment has torch `2.6.0+cu124`, transformers `5.17.0`, and no available GPU. The CPU install commands above select the same torch release's CPU wheel. Exact declared package versions were checked against the current environment and `pip check` passes; a complete clean-environment dependency installation was not executed during final verification.

Transformers 5.17 can emit a misleading Mistral-regex warning when loading this pinned MuRIL model. Inspection confirmed `BertTokenizer`, WordPiece, `BertPreTokenizer`, and `BertNormalizer`; the library's large-vocabulary/config check misidentifies this BERT model. Do not apply `fix_mistral_regex=True`: it would replace frozen BERT preprocessing. Cache or checkpoint errors are real startup errors and should be resolved by supplying the correct assets.

## API and frontend

API terminal:

```bash
source .venv/bin/activate
export HF_HOME="$PWD/.cache/huggingface"
python -m app.api --host 127.0.0.1 --port 8765
```

UI terminal:

```bash
source .venv/bin/activate
export HF_HOME="$PWD/.cache/huggingface"
streamlit run app/streamlit_app.py --server.address=127.0.0.1 --server.port=8501
```

Open `http://127.0.0.1:8501`. Use Ctrl-C in each terminal to stop. The UI calls `http://127.0.0.1:8765` by default; `NLP_V2_API_URL` can point it to another already authorized local API port. The API is a single-threaded demonstration server, with no public-deployment/authentication configuration. Keep the services bound to localhost.

HTTP smoke:

```bash
curl --fail --silent http://127.0.0.1:8765/health
curl --fail --silent http://127.0.0.1:8765/api/v2/query \
  -H 'Content-Type: application/json' \
  --data '{"query":"Where is the nearest metro station to Marina Beach?"}'
```

`POST /api/v2/query` accepts one nonempty `query` string inside an at-most-8192-byte JSON body. The response contains `status`, `response_text`, `intent`, `operation`, `slots`, `data`, `missing_slots`, `clarification_reason`, `candidate_entities`, and `candidate_intents`. Safe API validation/availability errors contain `status` and `response_text`. Valid assistant statuses are `ok`, `clarification`, `unavailable`, `out_of_scope`, and `error`. Raw/normalized queries, classifier confidence and exception details are not returned.

Direct inference:

```bash
python - <<'PY'
from src.nlp_v2.assistant import T3Assistant
reply = T3Assistant().process_query("What is the deluxe bus fare for stage 4?")
print(reply.status, reply.intent, reply.response_text)
PY
```

Model inference preserves the original multilingual text. Extraction uses deterministic canonical aliases and explicit cues; replies currently use English templates. Each question is self-contained. The revision form resubmits a full question rather than maintaining conversational slots.

## Tests and static verification

```bash
python -m pytest -q
python -m compileall -q src/nlp_v2 app/api.py app/frontend_contract.py app/streamlit_app.py scripts/nlp_v2
python -m pip check
git diff --check
```

The verified suite has 368 passes, including real-checkpoint inference, synthetic multilingual/slot/dispatch/service/API/UI cases, trainer smoke, evaluator guards, and frozen annotation/hash checks. The 34 Gate B.3 framework tests retain pre-execution checks using temporary synthetic manifests and validate the real closed state. No lint/type checker is configured. Run tests sequentially; legacy tests rebuild shared prototype SQLite fixtures.

Frozen Git boundary check:

```bash
git diff c7576a9 --name-only -- \
  data/nlp_v2/gate_b2 data/nlp_v2/gate_b3 \
  reports/nlp_v2/gate_b2 reports/nlp_v2/gate_b3 \
  experiments/nlp_v2/gate_b2
```

No output is expected for the completed production phases. This check and the tests verify stored hashes without rerunning closed research studies.

## Optional replacement training

The existing seed-42 artifact supplies current production inference. Full retraining was not performed because no GPU is available. The separate trainer uses only frozen train/validation CSVs, hash-checks them, excludes overlapping validation families/semantic families/exact queries, and selects by validation Macro-F1. It never reads stress/reference data. Output must be new or empty and outside frozen research/source directories.

CPU pipeline smoke; the resulting small random model is **not production eligible**:

```bash
python -m scripts.nlp_v2.train_production_t3 \
  --smoke --output-dir /tmp/nlp_v2-t3-smoke-demo
```

For a new full GPU run, install a suitable official torch 2.6 wheel (the observed environment uses CUDA 12.4), cache the pinned base model explicitly, and verify CUDA:

```bash
if python - <<'PY'
import torch
from transformers import AutoModelForSequenceClassification
assert torch.cuda.is_available(), "A GPU is required for this planned full run"
AutoModelForSequenceClassification.from_pretrained(
    "google/muril-base-cased",
    revision="afd9f36c7923d54e97903922ff1b260d091d202f",
    num_labels=16,
)
print(torch.cuda.get_device_name(0))
PY
then
  python -m scripts.nlp_v2.train_production_t3 \
    --output-dir experiments/nlp_v2/production_runs/t3-new-seed42 \
    --seed 42 --max-epochs 30 --patience 3 --min-delta 0.001 \
    --batch-size 16 --learning-rate 2e-5
fi
```

The trainer itself permits CPU execution without `--smoke`; the conditional block starts the planned large run only when CUDA verification and cache preparation succeed. Its metadata records hyperparameters, versions, device, hashes, label order, epoch history and selected checkpoint. Training does not replace the current production manifest automatically. Do not promote a smoke model or select against final evaluation results.

## Evaluation records and reproduction

The [model report](../../reports/nlp_v2/production_eval/production_t3_evaluation.md) uses the selected manifest/checkpoint frozen before held-out inference. Stress accuracy is 0.8300 and Macro-F1 0.7918. The [complete-assistant report](../../reports/nlp_v2/assistant_eval/assistant_evaluation.md) was run once from source freeze `b9b2271b1761d08752786f22b558862f45ed1dac`, with Chennai reference date `2026-10-06`.

On 706 stress queries the assistant returned 520 clarifications, 150 unavailable, 22 ok, and 14 out of scope, with no error status. Strict reply-intent accuracy is 0.8272, selected-operation accuracy 0.5042, and terminal-dispatch accuracy 0.2323. Terminal dispatch includes correct unavailable/rejection operations; these scores do not establish factual travel-answer correctness. The 350-row human subset is nested in stress. Frozen train-family overlap affects 187 stress rows and 160 human-subset rows, so full scores are descriptive rather than independent family-held-out estimates. Additional runtime clarifications reflect alias/entity ambiguity, required inputs, and limited canonical coverage. There are no aligned gold factual answers or canonical slot IDs in this evaluator.

The following commands are for an explicitly authorized reproducibility run using the unchanged frozen source/assets and a **new** output directory. Existing reports are never overwritten; repeated runs are not a model-selection loop. They were not rerun during documentation verification:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m scripts.nlp_v2.evaluate_production_t3 \
  --output-dir /tmp/nlp_v2-model-eval-reproduction
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m scripts.nlp_v2.evaluate_assistant \
  --freeze-commit b9b2271b1761d08752786f22b558862f45ed1dac \
  --reference-date 2026-10-06 \
  --output-dir /tmp/nlp_v2-assistant-eval-reproduction
```

The assistant evaluator refuses changed/uncommitted freeze paths. It records source commit, model/input/DB hashes, and the fixed reference date, with per-class and language/code-switch/noise aggregates. Model-only mapped-operation accuracy differs from actual assistant dispatch after extraction/clarification. No code, model, prompt, or parameter tuning followed final assistant evaluation.

## Demo workflow and limitations

1. Ask “Where is the nearest metro station to Marina Beach?” and inspect straight-line distance, mode, source, and walking-access caveat.
2. Ask “List stops on bus route 102” and expand the published directional sequences.
3. Ask “What is the deluxe bus fare for stage 4?” and inspect the recorded service class, amount, effective date and source.
4. Ask “Departures from Poonamallee Bus Terminus at 8:00 baje” to demonstrate temporal clarification; revise the complete question with explicit AM/PM.
5. Ask a live-status question to demonstrate unavailable information. Try Hindi/Roman/mixed questions and inspect missing/ambiguous entity prompts; aliases have limited coverage.

The canonical database's hub memberships are unverified and its 45 interchange rows are unconfirmed. Accessibility values are null, authoritative ticket/pass policy is absent, and facility availability is unverified. Published timetables/fare records are dated/provisional; no realtime source is configured. Directional bus candidates are stop-sequence evidence, not confirmed trip availability or multimodal optimization. Nearest-stop distances are geometric rather than walking routes.

The final evaluation's high clarification rate and limited successful-response count are recorded coverage limits. Expanding the system requires new development data and verified transport sources under the frozen governance policy. It must not use held-out labels/queries to train, augment, patch predictions, or tune parameters.
