# Phase 17 — classifier replacement decision

**Decision: one full MuRIL replacement candidate is justified.** Training is an
experiment, not a promised improvement. The existing checkpoint remains selected
until the candidate clears the predeclared validation-only comparison and contract
checks. No historical stress/reference evaluation is run or used for selection.

## Evidence after Phase 16

Frozen development v1 has 120 contracts. Raw single-label accuracy is **92/118
(77.97%)**, Macro-F1 **0.75675**; two null-intent contracts are excluded from raw
accuracy. Final reply-intent/terminal contracts are 93/120. Raw inference before
guards is necessary: previous coverage report metadata called the reply-intent
score classifier accuracy. Future reports correct that name; original phase
reports remain preserved, with this interpretation correction.

Of 27 actual terminal failures, **25** have an incorrect raw class and become
correct under an intended-intent counterfactual; **one** is a semantic-ambiguity
contract that requires structured ambiguity rather than single-class argmax;
**one** is the documented frozen v1-098 policy/gold divergence. There are no
additional gold-intent slot/entity/domain-code failures on this suite. Answerable
terminal coverage is **42/50** with the classifier versus **50/50** with intended
intent. This establishes a classifier bottleneck on observed development contracts,
not a causal guarantee that training will recover these cases.

Raw language slices are EN 32/49, Hindi Devanagari 15/16, Hindi Latin 14/16,
Hinglish 17/20 and mixed-script 14/17. Single-case noise slices are too small to
support robustness claims. No item-specific held-out targeting or fitting to the
development suite is permitted.

Allowed train-disjoint validation contains 332 rows across all 16 T3 classes,
after excluding train family, semantic-family and exact casefolded query overlap.
The selected checkpoint scores **301/332 (90.66%)**, Macro-F1 **0.8512157223**,
reproducing its manifest. Original selection Macro-F1 0.91555 used overlapping
validation; it is not the replacement comparison baseline. Very small validation
classes (frequency 3, realtime 4) make uncertainty material.

Failure taxonomy: classifier 25 correctable terminal failures; structured
ambiguity/clarification policy one; residual policy/gold divergence one; slot
extraction zero; entity resolution zero; domain-code zero under intended intent.
The 48 correctly expected unavailable contracts are source/scope limitations:
six require external realtime data, and 42 lack usable verified data or the
requested supported scope. They are successful refusals, not failed answers.
No claim is made that new intent training supplies missing transport evidence.

## Focused, predeclared candidate

Use the unchanged **1,396 train rows only** for fitting; **332 disjoint validation
rows only** for epoch selection. The focused change from the original selection
procedure is disjoint validation selection. Do not augment from development,
stress or reference examples. Run exactly one candidate: pinned
`google/muril-base-cased` revision `afd9f36c7923d54e97903922ff1b260d091d202f`, fixed
16-label order, raw query, length 64, seed 42, maximum 30 epochs, patience 3,
minimum delta 0.001, batch 16, learning rate 2e-5, AdamW weight decay 0.01,
gradient clipping 1.0. No confidence threshold, label change or smoke promotion.

Candidate promotion requires disjoint validation Macro-F1 **greater than
0.8522157223** (baseline + 0.001), strict artifact/label/hash checks and preserved
structural, dispatch and anti-fabrication contracts. Development accuracy is not
a competing checkpoint-selection criterion. Validation Macro-F1 is the model comparison criterion;
development is an observed operational verification suite, not a model-selection
score. If the candidate fails the comparison, retain the existing checkpoint and
document the negative experiment. Do not run extra seeds/configurations in response
to development or historical scores. Preserve both artifacts and exact metadata.

## GPU and execution

The sandbox reports CUDA unavailable and cannot initialize NVML. An escalated
host check detects **NVIDIA RTX 4000 Ada Generation, 20,982,726,656 bytes**;
torch **2.6.0+cu124**, CUDA runtime **12.4**, one device, successful CUDA tensor
allocation. This corrects the earlier environment assumption: the GPU blocker
does not apply when this authorized host execution is available.

A fresh GPU environment needs the pinned Python 3.12 dependencies from
`requirements-nlp-v2.txt`, a CUDA-capable torch 2.6 build and a functioning NVIDIA
driver. Verify actual allocation before running. The existing environment meets
these checks. Cache the pinned base weights explicitly; current inference needs
only the selected checkpoint plus config/tokenizer. No artifact upload occurs.

From repository root, execute with host GPU access:

```bash
export HF_HOME="$PWD/.cache/huggingface"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
if .venv/bin/python - <<'PY'
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
assert torch.cuda.is_available(), "Full training requires a usable GPU"
assert (torch.ones(1, device="cuda") + 1).item() == 2
AutoTokenizer.from_pretrained("google/muril-base-cased",
    revision="afd9f36c7923d54e97903922ff1b260d091d202f")
AutoModelForSequenceClassification.from_pretrained("google/muril-base-cased",
    revision="afd9f36c7923d54e97903922ff1b260d091d202f", num_labels=16)
print(torch.cuda.get_device_name(0))
PY
then
  .venv/bin/python -m scripts.nlp_v2.train_production_t3 \
    --output-dir experiments/nlp_v2/production_runs/t3-disjoint-seed42-20261007 \
    --seed 42 --max-epochs 30 --patience 3 --min-delta 0.001 \
    --batch-size 16 --learning-rate 2e-5
else
  exit 1
fi
```

Artifact destination is the new directory shown above: `t3_best.pt` and
`metadata.json`; never overwrite Gate B.2 or the current checkpoint. The trainer
refuses nonempty destinations and hash-checks both input CSVs. A full run remains
GPU-only in the trainer itself and under this guarded command; the explicit small CPU
smoke mode is separate. A failed preflight exits nonzero.

There are 237,568,528 parameters. FP32 parameters, gradients and two Adam moments
alone require approximately **3.54 GiB**, excluding activations, buffers and
optimizer temporaries. The device has 20 GB total; a pre-run host snapshot shows only 6,392 MiB free
and 100% utilization from another workload. Total capacity is not free capacity.
Do not terminate or modify that workload. If the fixed batch-16 run cannot obtain
needed memory, stop rather than change the recipe or fall back to CPU. Measured
peak allocation should be recorded rather than inventing a benchmark. Maximum
work is **2,640 optimizer steps** (88 per epoch), plus 21 validation batches per
epoch, with early stopping. Wall time is undetermined until the actual run;
record elapsed time and epochs. Budget approximately 4 GB additional local disk
for pinned base cache, candidate checkpoint and temporary serialization headroom.

## Verification and outcome

Diagnostic reproduction:

```bash
HF_HOME="$PWD/.cache/huggingface" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  .venv/bin/python -m scripts.nlp_v2.diagnose_training_need \
  --output-dir /tmp/nlp-v2-training-decision-new
```

The report contains aggregate validation metrics and development case IDs; no
validation query examples or held-out failure contents. Independent decision
review and candidate result are recorded below before phase exit.

**Candidate result: existing checkpoint retained.** The one full GPU candidate
stopped after 13 epochs; epoch 10 was best at Macro-F1 **0.8465825050**, below both
the existing 0.8512157223 and declared 0.8522157223 threshold. No additional seeds,
configurations, augmentation or development-based selection followed. The candidate
was not evaluated on development or historical data because it failed validation
comparison. Its strict saved-artifact load and independent CPU validation metric
reconstruction are recorded in `candidate_comparison.json`.

The measured training loop took **316.94 seconds** (5.28 minutes, excluding base
cache preparation/model loading) and peak CUDA allocation was **4,806,520,832 bytes
(4.48 GiB)**. Memory sharing did not cause an error. The candidate stays ignored at
the new artifact destination; reviewed metadata and comparison are tracked under
`reports/nlp_v2/training_decision/phase17/`. Candidate SHA-256 is
`834d3511eef74a6566cbbcfb3346e617055a01402047be42bd6aa50fc0a8fc34`.
Production manifest/checkpoint are unchanged. The classifier bottleneck remains,
with the documented operational limitations; this negative experiment does not
justify promising better accuracy or adapting to development failures.
