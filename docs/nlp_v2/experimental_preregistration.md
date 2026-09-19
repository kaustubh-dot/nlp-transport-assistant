# Experimental Preregistration Document (Phase N7)

Document: `docs/nlp_v2/experimental_preregistration.md`  
Snapshot Version: `chennai_multimodal_v1.2.2`  
Date: 2026-09-19  
Status: Authoritative Preregistration Plan (Corrected Methodology Patch)

---

## 1. Preregistration Mandate & Research Governance

To prevent p-hacking, selective reporting, and repeated optimization against the final test set, this preregistration document locks the experimental design, candidate architectures, hyperparameter spaces, pipeline ablations, statistical testing procedures, and decision gates **before running full-scale model training**.

---

## 2. Experimental Axes & Hypotheses

### Experiment 1: Dataset Size Scaling (Learning Curves)
- **Research Question**: At what dataset size does multimodal multilingual intent classification saturate?
- **Nested Subset Sizes**: `5k`, `10k`, `20k`, `40k`, `80k` (and `120k` if learning curve slope $\frac{\Delta F_1}{\Delta N} > 0.005$ between 40k and 80k).
- **Representative Benchmark Architectures**:
  - TF-IDF + Logistic Regression
  - Google MuRIL
  - AI4Bharat IndicBERT v2 (`ai4bharat/IndicBERTv2-MLM-only`)
- **Tracked Metrics**: Validation Macro-F1, Language Subgroup F1, Entity Resolution Accuracy.

### Experiment 2: Template-Family Scaling vs Sample-Size Inflation
- **Research Question**: Does syntactic template diversity matter more than raw sample count?
- **Controlled Comparison**:
  - Condition D1 (Low Diversity, High Repetition): 40k samples generated from 80 template families.
  - Condition D2 (High Diversity, Low Repetition): 40k samples generated from 400 template families.
- **Hypothesis**: Condition D2 will achieve statistically superior out-of-family generalization on test holdout.

### Experiment 3: Language-Mixture Variations (Covering All 5 Formal Classes)
- **Research Question**: What training language proportion maximizes code-switched and Romanized Hindi performance without degrading English?
- **Controlled Mixtures (Explicitly modeling `EN`, `HI_DEVA`, `HI_LATN`, `HINGLISH_LATN`, `MIXED_SCRIPT_CS`)**:
  - **Mixture `L1` (Balanced Baseline)**:
    `EN`: 25%, `HI_DEVA`: 25%, `HI_LATN`: 15%, `HINGLISH_LATN`: 25%, `MIXED_SCRIPT_CS`: 10%.
  - **Mixture `L2` (Colloquial Commuter Enriched)**:
    `EN`: 15%, `HI_DEVA`: 20%, `HI_LATN`: 20%, `HINGLISH_LATN`: 35%, `MIXED_SCRIPT_CS`: 10%.
  - **Mixture `L3` (High Code-Switching & Romanized Focus)**:
    `EN`: 15%, `HI_DEVA`: 15%, `HI_LATN`: 15%, `HINGLISH_LATN`: 40%, `MIXED_SCRIPT_CS`: 15%.

### Experiment 4: Pipeline Architectures & Preprocessing Ablations

```
PIPELINE EXPERIMENTAL DESIGNS:

Pipeline A: Translation Pivot
Input -> Entity Detection/Masking -> Neural Translation (to EN) -> English Model -> Entity Restoration -> Resolver

Pipeline B: Direct Multilingual
Input -> Minimal Unicode NFC -> Multilingual Transformer (MuRIL / IndicBERT) -> Resolver

Pipeline C: Normalized Multilingual
Input -> Script/Lang Detection -> Transliteration Normalization -> Code-Switch Normalization -> Model
```

- **Pipeline A Variants**:
  - `A1`: Raw translation (no entity protection).
  - `A2`: Entity-protected translation.
  - `A3`: Entity + route-number protection.
  - `A4`: Entity protection + transliteration normalization + translation.
- **Pipeline C Ablations**:
  - `C-Full`: All normalization modules enabled.
  - `C-NoSpelling`: Remove typo/spelling correction.
  - `C-NoTranslit`: Remove Roman-Hindi transliteration normalization.
  - `C-NoCS`: Remove code-switch token expansion.
  - `C-NoEntity`: Remove entity surface canonicalization before classification.

---

## 3. Candidate Model Registry

| Model Key | HuggingFace Hub Identifier | Pinned Revision | Parameters | Vocabulary Size | Linguistic Strengths | Research Justification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `baseline` | `sklearn.linear_model.LogisticRegression` | N/A | ~50k | Char (2-5) + Word (1-3) | Zero latency, deterministic | Fast empirical floor |
| `muril` | `google/muril-base-cased` | `main` | 236M | 197k (Indic-focused) | Trained on 17 Indic languages + English, transliterated pairs | **Historical incumbent champion** |
| `indicbert_v2` | `ai4bharat/IndicBERTv2-MLM-only` | `main` | 278M | 250k (ALUM) | Pre-trained on IndicCorp v2 + English; MLM-only objective | **Verified v1 runner-up checkpoint** |
| `indicbert_v1` | `ai4bharat/indic-bert` | `main` | 135M | 200k | Lightweight Indic ALBERT | Historical baseline comparison |
| `minilm` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | `main` | 117M | 250k | Low inference latency (2.7 ms) | High deployment efficiency |
| `xlm_roberta` | `xlm-roberta-base` | `main` | 278M | 250k | 100 languages, cross-lingual transfer | High capacity multilingual |
| `hingbert` | `l3cube-pune/hing-bert` | `main` | 110M | 30k | Explicit Hinglish Roman pre-training | Code-switch domain alignment |
| `mdeberta_v3` | `microsoft/mdeberta-v3-base` | `main` | 278M | 250k | Disentangled attention, high NLU benchmark scores | Strong modern NLU alternative |

---

## 4. Hyperparameter Search Space & Reproducibility (Validation Only)

Each serious candidate model receives an identical hyperparameter search budget of **8 trials** evaluated strictly on validation Macro-F1.

### Deterministic Trial Selection Protocol:
To eliminate researcher discretion, the 8 configurations are generated via **deterministic pseudo-random search using fixed search seed `42`** across the predefined search space:

| Hyperparameter | Search Space Grid |
| :--- | :--- |
| **Learning Rate** | `[1e-5, 2e-5, 3e-5, 5e-5]` (AdamW) |
| **Effective Batch Size** | `[16, 32]` |
| **Weight Decay** | `[0.01, 0.1]` |
| **Warmup Ratio** | `[0.05, 0.10]` |
| **Max Epochs** | `15` ceiling |
| **Early Stopping** | Patience = `3`, min_delta = `0.001` on Validation Macro-F1 |
| **Precision** | `bfloat16` mixed precision |
| **Max Sequence Length** | `128` tokens |

*Discipline Rule*: Hyperparameter tuning against the test partition is strictly prohibited. All 8 configurations and trial metrics must be logged in `experiments/nlp_v2/hyperparameter_trials.jsonl`.

---

## 5. Training Seed Protocol

To guarantee reproducibility and measure run-to-run variance:
- **Pilot Experiments (Gate B)**: 3 seeds (`[42, 101, 777]`).
  - Total pilot matrix: 3 taxonomies (T1, T2, T3) × 2 regimes (Regime A, Regime B) × 2 model families (TF-IDF, MuRIL) × 3 seeds = **36 total model-training runs** (18 runs per model family).
  - No artificial wall-clock limits; actual wall-clock runtimes are measured and logged.
- **Core Benchmark Comparisons**: The established 5 historical seeds:
  `[42, 101, 777, 1337, 2026]`.
- **Close Finalists (<0.01 Macro-F1 delta)**: Expanded to 10 seeds to verify statistical significance.

---

## 6. Pre-Registered Model Selection Protocol

To select the final champion architecture objectively, models are evaluated through a 5-stage gating funnel:

```
STAGE 1: SUBGROUP INTEGRITY GATE
Reject any model with Macro-F1 < 0.70 on any individual language partition
(EN, HI_DEVA, HI_LATN, HINGLISH_LATN, MIXED_SCRIPT_CS) or Noise Tier N0-N3.
                       │
STAGE 2: FACTUAL SAFETY & ENTITY FIDELITY GATE
Reject any model with Entity Corruption > 3.0%, Hallucination Rate > 0.0%,
or Realtime Status Rejection Accuracy < 90.0%.
                       │
STAGE 3: PRIMARY MACRO-F1 RANKING
Rank remaining models by Test Macro-F1 (mean across 5 seeds).
                       │
STAGE 4: STATISTICAL SIGNIFICANCE & EFFICIENCY BREAKERS
If top two models are not statistically distinguishable
(McNemar test p > 0.05 AND paired bootstrap 95% CI overlap on matched seeds):
Prefer model with lower P95 latency, smaller memory, or simpler pipeline.
                       │
STAGE 5: INDEPENDENT GOLD ACCEPTANCE
Evaluate selected champion on external, untouched Coverage-Based Gold Suite
(>= 10 cases x K intents x 5 language classes).
Pass condition: Overall task accuracy >= 95.0%, 0 hallucinations.
```

---

## 7. Statistical Testing Procedures Across Seeds

1. **Intra-Taxonomy Matched Testing**:
   - Within the same taxonomy (e.g. T2 MuRIL vs T2 TF-IDF), paired per-example statistical significance tests (McNemar's test and paired bootstrap) **must operate on matched per-example prediction pairs** on matched seeds. They must never be applied to averaged summary metrics across seeds.
   - For candidate models evaluated across 5 seeds:
     - For each seed $s \in \{42, 101, 777, 1337, 2026\}$, compute the per-example $2 \times 2$ contingency matrix between incumbent $M_{\text{incumbent}}$ and challenger $M_{\text{challenger}}$:
       $$\chi^2_s = \frac{(|b_s - c_s| - 1)^2}{b_s + c_s}, \quad df = 1$$
     - Report seed-specific $p$-values alongside the omnibus hierarchical bootstrap confidence interval for $\Delta \text{Macro-F1}$ ($B = 1,000$ iterations).
     - Reject the null hypothesis of equal performance at $\alpha = 0.05$ only when the improvement is statistically significant across matched seeds.
2. **Cross-Taxonomy Comparison Discipline**:
   - Across different taxonomies (T1 = 9 labels, T2 = 12 labels, T3 = 16 labels), **do NOT directly apply ordinary McNemar to raw class predictions**.
   - Primary cross-taxonomy evaluation relies on Macro-F1, overall accuracy, per-intent F1, confusion matrices, class-boundary confusion, sample efficiency, variance across seeds, downstream action correctness, slot-contract complexity, annotation ambiguity, and end-to-end usefulness.
   - If conducting paired statistical hypothesis testing across taxonomies, predictions and gold labels must first be mapped to a common shared semantic/action representation (`semantic_operation`), with the explicit mapping documented. Do not manufacture a significance test simply because a test procedure is available.
