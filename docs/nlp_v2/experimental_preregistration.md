# Experimental Preregistration Document (Phase N7)

Document: `docs/nlp_v2/experimental_preregistration.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Preregistration Plan (Pre-Execution Lock)

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
  - AI4Bharat IndicBERT v2
- **Tracked Metrics**: Validation Macro-F1, Language Subgroup F1, Entity Resolution Accuracy.

### Experiment 2: Template-Family Scaling vs Sample-Size Inflation
- **Research Question**: Does syntactic template diversity matter more than raw sample count?
- **Controlled Comparison**:
  - Condition D1 (Low Diversity, High Repetition): 40k samples generated from 80 template families.
  - Condition D2 (High Diversity, Low Repetition): 40k samples generated from 400 template families.
- **Hypothesis**: Condition D2 will achieve statistically superior out-of-family generalization on test holdout.

### Experiment 3: Language-Mixture Variations
- **Research Question**: What training language proportion maximizes code-switched and Romanized Hindi performance without degrading English?
- **Controlled Mixtures**:
  - Mixture `L1` (Balanced Equal): English 33%, Hindi-Devanagari 33%, Hinglish 34%.
  - Mixture `L2` (Commuter Real-World): English 20%, Hindi-Devanagari 30%, Hinglish 50%.
  - Mixture `L3` (Code-Switch Enriched): English 20%, Hindi-Devanagari 20%, Hinglish 40%, Mixed-Script 20%.

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

| Model Key | HuggingFace Hub Identifier | Parameters | Vocabulary Size | Linguistic Strengths | Research Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `baseline` | `sklearn.linear_model.LogisticRegression` | ~50k | Char (2-5) + Word (1-3) | Zero latency, deterministic | Fast empirical floor |
| `muril` | `google/muril-base-cased` | 236M | 197k (Indic-focused) | Trained on 17 Indic languages + English, transliterated pairs | **Historical incumbent champion** |
| `indicbert_v2` | `ai4bharat/indic-bert` | 135M | 200k (ALUM) | Efficient Indic parameterization | Historical v1 runner-up |
| `minilm` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 117M | 250k | Low inference latency (2.7 ms) | High deployment efficiency |
| `xlm_roberta` | `xlm-roberta-base` | 278M | 250k | 100 languages, cross-lingual transfer | High capacity multilingual |
| `hingbert` | `l3cube-pune/hing-bert` | 110M | 30k | Explicit Hinglish Roman pre-training | Code-switch domain alignment |
| `mdeberta_v3` | `microsoft/mdeberta-v3-base` | 278M | 250k | Disentangled attention, high NLU benchmark scores | Strong modern NLU alternative |

---

## 4. Hyperparameter Search Space (Validation Only)

Each serious candidate model receives an identical hyperparameter search budget of **8 trials** evaluated strictly on validation Macro-F1:

| Hyperparameter | Search Range / Grid Values |
| :--- | :--- |
| **Learning Rate** | `[1e-5, 2e-5, 3e-5, 5e-5]` (AdamW) |
| **Batch Size** | `[16, 32]` (standardized effective batch size = 32) |
| **Weight Decay** | `[0.01, 0.1]` |
| **Warmup Ratio** | `[0.05, 0.10]` |
| **Max Epochs** | `15` ceiling |
| **Early Stopping** | Patience = `3`, min_delta = `0.001` on Validation Macro-F1 |
| **Precision** | `bfloat16` mixed precision |
| **Max Sequence Length** | `128` tokens |

*Discipline Rule*: Hyperparameter tuning against the test partition is strictly prohibited.

---

## 5. Training Seed Protocol

To guarantee reproducibility and measure run-to-run variance, we establish a two-tiered seed funnel:
- **Exploratory Pilot Experiments**: 2 seeds (`[42, 101]`).
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
or Unsupported Request Rejection Accuracy < 90.0%.
                       │
STAGE 3: PRIMARY MACRO-F1 RANKING
Rank remaining models by Test Macro-F1 (mean across 5 seeds).
                       │
STAGE 4: STATISTICAL SIGNIFICANCE & EFFICIENCY BREAKERS
If top two models are not statistically distinguishable
(McNemar test p > 0.05 AND paired bootstrap 95% CI overlap):
Prefer model with lower P95 latency, smaller memory, or simpler pipeline.
                       │
STAGE 5: INDEPENDENT GOLD ACCEPTANCE
Evaluate selected champion on external, untouched 150-case Gold Suite.
Pass condition: Overall task accuracy >= 95.0%, 0 hallucinations.
```

---

## 7. Statistical Testing Procedures

1. **Paired Bootstrap Confidence Intervals**:
   Compute 95% bootstrap confidence intervals for Macro-F1 by resampling test queries with replacement ($B = 1,000$ iterations).
2. **McNemar's Test**:
   Evaluate paired binary correctness matrices between the incumbent (MuRIL) and challengers:
   $$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}, \quad df = 1$$
   where $b$ is queries model 1 got right and model 2 got wrong, and $c$ is vice-versa. Reject null hypothesis of equal performance at $\alpha = 0.05$.
