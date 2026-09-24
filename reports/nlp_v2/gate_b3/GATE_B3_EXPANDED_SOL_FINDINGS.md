# Gate B.3 Expanded Sol Audit Findings

**Document Status:** Complete Evidence Summary  
**Audit Scope:** 128 Purposively Selected Frozen Challenge Queries (256 Sol Judgments: 128 T2, 128 T3)  
**Primary Evaluators:** GPT-5.6 Sol (Audit Arm, Blind-to-Label), MODEL_G (Gemini 2.5 Pro First Pass, Frozen)  
**Reference Benchmark:** Gate B.2 Human Reference Key (`human_annotation_key.json`)  
**Decision Policy:** This document reports descriptive audit evidence only. It does **NOT** make the final T2-vs-T3 gate decision.

---

## 1. Executive Summary & Purpose

Following the retirement of the student annotator arm, Gate B.3 evaluates taxonomy robustness across two active evidence streams:
1. **MODEL_G / Gemini:** The complete, frozen 350-query T2 and T3 first-pass annotations.
2. **GPT-5.6 Sol:** An expanded masked blind-to-label audit across 128 purposively selected challenge queries evaluated under both T2 and T3 (256 total judgments).

The purpose of this audit is to stress-test whether transitioning from T2 (coarse 10-class taxonomy) to T3 (fine-grained 16-class taxonomy) introduces systematic regressions in challenging linguistic contexts (Hindi, Hinglish, code-switching, noise types, and ambiguous queries).

---

## 2. Interpretation Guardrails

The following methodological constraints apply to all findings in this document:
* **Purposive Fixed Challenge Subset:** The 128 queries were selected via a frozen deterministic seed (`GATE_B3_SOL_EXPANDED_256_V1`) without access to MODEL_G predictions or reference gold labels. They deliberately over-represent stress phenomena (code-switching, noise, ambiguity).
* **Descriptive Analysis Only:** Results are presented as empirical counts, percentages, and percentage-point (pp) deltas. No population confidence intervals, standard errors, or hypothesis significance tests are asserted.
* **Audit Nature:** GPT-5.6 Sol is an independent, masked, blind-to-label model auditor. Its judgments provide high-capability secondary evaluation, not human inter-annotator agreement (IAA).
* **Complementary Evidence:** This 128-query audit complements, and does not replace or supersede, the primary 350-query MODEL_G Gate B.3 baseline.
* **No Premature Taxonomy Selection:** Final adoption between T2 and T3 requires holistic gate review; no decision is made here.

---

## 3. Context: Full 350-Query MODEL_G Reference Concordance

For reference and context, the previously computed baseline concordance for the full 350-query Gate B.3 benchmark under MODEL_G is recorded below (not re-run):

| Metric | T2 (350 queries) | T3 (350 queries) | T3 − T2 Delta |
|:---|---:|---:|---:|
| Primary Exact Match | 78.57% (275/350) | 81.14% (284/350) | +2.57 pp |
| MODEL_G Primary in Reference Acceptable Set | 79.43% (278/350) | 84.29% (295/350) | +4.86 pp |
| Reference Primary in MODEL_G Acceptable Set | 99.71% (349/350) | 97.14% (340/350) | -2.57 pp |
| Exact Acceptable-Set Match | 56.57% (198/350) | 66.86% (234/350) | +10.29 pp |
| Mean Acceptable-Set Jaccard | 77.64% | 81.52% | +3.88 pp |
| Clarification Agreement | 80.57% (282/350) | 82.86% (290/350) | +2.29 pp |

*Note: These 350-query baseline figures represent the entire challenge evaluation pool, whereas subsequent sections focus strictly on the 128-query expanded Sol audit subset.*

---

## 4. Overall Concordance & Inter-Model Agreement (128-Query Audit)

On the 128 challenge queries, both models achieve high concordance with the human reference key under both taxonomies.

### Primary Concordance Against Reference

| Source | T2 Primary Exact | T3 Primary Exact | T3 − T2 Delta | T2 Primary in Ref Set | T3 Primary in Ref Set |
|:---|---:|---:|---:|---:|---:|
| **GPT-5.6 Sol** | 92.2% (118/128) | 91.4% (117/128) | -0.8 pp | 93.8% (120/128) | 93.0% (119/128) |
| **MODEL_G** | 89.8% (115/128) | 90.6% (116/128) | +0.8 pp | 89.8% (115/128) | 90.6% (116/128) |

* Sol changes on exactly 1 query (`ANN_B2_097`: T2 correct `service_timing` → T3 predicted `None`/clarification vs gold `first_and_last_service`, delta = -0.8 pp).
* MODEL_G changes on 3 queries (+2 correct on route stop membership, -1 dropped on an underspecified route query, net delta = +0.8 pp).

### Sol ↔ MODEL_G Concordance

| Metric | T2 | T3 | Delta (T3 − T2) |
|:---|---:|---:|---:|
| Primary Label Agreement | 90.6% (116/128) | 93.0% (119/128) | +2.3 pp |
| Acceptable-Set Exact Agreement | 75.8% (97/128) | 82.8% (106/128) | +7.0 pp |
| Clarification Required Agreement | 82.8% (106/128) | 85.9% (110/128) | +3.1 pp |

Inter-model alignment improves under T3 across all dimensions: primary agreement rises to 93.0%, set agreement improves by +7.0 pp, and clarification judgment agreement increases by +3.1 pp.

---

## 5. Language Robustness

The 128-query selection includes all 5 language classes observed in the dataset.

| Language Class | N | Sol T2 | Sol T3 | Sol Δ | MODEL_G T2 | MODEL_G T3 | MODEL_G Δ | Agreement T2 → T3 |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **EN** | 30 | 83.3% (25) | 80.0% (24) | -3.3 pp | 80.0% (24) | 83.3% (25) | +3.3 pp | 76.7% → 83.3% |
| **HINGLISH_LATN** | 29 | 93.1% (27) | 93.1% (27) | +0.0 pp | 89.7% (26) | 89.7% (26) | +0.0 pp | 96.6% → 96.6% |
| **HI_DEVA** | 30 | 93.3% (28) | 93.3% (28) | +0.0 pp | 93.3% (28) | 93.3% (28) | +0.0 pp | 96.7% → 96.7% |
| **HI_LATN** | 29 | 96.6% (28) | 96.6% (28) | +0.0 pp | 93.1% (27) | 93.1% (27) | +0.0 pp | 93.1% → 93.1% |
| **MIXED_SCRIPT_CS** | 10 | 100.0% (10) | 100.0% (10) | +0.0 pp | 100.0% (10) | 100.0% (10) | +0.0 pp | 100.0% → 100.0% |

### Key Findings
1. **Zero Difference in Indic & Mixed-Script Classes:** For all 98 queries comprising `HINGLISH_LATN`, `HI_DEVA`, `HI_LATN`, and `MIXED_SCRIPT_CS`, primary-exact concordance between T2 and T3 is strictly identical (0.0 pp delta) for both Sol and MODEL_G.
2. **Movement Concentrated in English:** All observed primary movements across both models occurred exclusively within the 30 English queries.
3. **No Indic Penalty:** There is no descriptive evidence from this audit that moving from T2 to T3 introduces a Hindi, Hinglish, or mixed-script penalty.

*(Note: These findings describe the purposive challenge sample only and do not assert statistical population generalization.)*

---

## 6. Surface Robustness

### Script Breakdown

| Script | N | Sol T2 | Sol T3 | Sol Δ | MODEL_G T2 | MODEL_G T3 | MODEL_G Δ | Primary Agreement |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Deva** | 30 | 93.3% | 93.3% | +0.0 pp | 93.3% | 93.3% | +0.0 pp | 96.7% → 96.7% |
| **Latn** | 88 | 90.9% | 89.8% | -1.1 pp | 87.5% | 88.6% | +1.1 pp | 87.5% → 90.9% |
| **Mixed** | 10 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 100.0% → 100.0% |

Devanagari and Mixed-script groups exhibit complete stability between T2 and T3. Latin-script movement is strictly driven by the English subset.

### Code-Switch Level Breakdown

| Level | Description | N | Sol T2 | Sol T3 | Sol Δ | MODEL_G T2 | MODEL_G T3 | MODEL_G Δ | Primary Agreement |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **CS0** | Monolingual | 51 | 86.3% | 84.3% | -2.0 pp | 84.3% | 86.3% | +2.0 pp | 80.4% → 86.3% |
| **CS1** | Minimal insertion | 9 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 100.0% → 100.0% |
| **CS2** | Moderate intra-sentential | 30 | 96.7% | 96.7% | +0.0 pp | 93.3% | 93.3% | +0.0 pp | 96.7% → 96.7% |
| **CS3** | Heavy alternation | 28 | 92.9% | 92.9% | +0.0 pp | 89.3% | 89.3% | +0.0 pp | 96.4% → 96.4% |
| **CS4** | Matrix frame ambiguity | 10 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 100.0% → 100.0% |

All code-switched categories (CS1–CS4, total N=77) display zero variance between T2 and T3 across both models. The only variation occurs in CS0 (N=51), which contains the English queries.

### Noise Level and Noise Type Breakdown

Each noise level in the audit set maps directly to a distinct noise type:

| Level | Noise Type | N | Sol T2 | Sol T3 | Sol Δ | MODEL_G T2 | MODEL_G T3 | MODEL_G Δ | Primary Agreement |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **N0** | clean | 57 | 93.0% | 91.2% | -1.8 pp | 89.5% | 91.2% | +1.8 pp | 93.0% → 96.5% |
| **N1** | casing_and_punctuation_normalization | 18 | 94.4% | 94.4% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 94.4% → 94.4% |
| **N2** | phonetic_transliteration_misspelling | 15 | 86.7% | 86.7% | +0.0 pp | 86.7% | 93.3% | +6.7 pp | 86.7% → 93.3% |
| **N3** | keyboard_adjacent_typo | 14 | 85.7% | 85.7% | +0.0 pp | 85.7% | 78.6% | -7.1 pp | 78.6% → 78.6% |
| **N4** | vowel_omission_and_truncation | 14 | 92.9% | 92.9% | +0.0 pp | 85.7% | 85.7% | +0.0 pp | 92.9% → 92.9% |
| **N5** | commuter_sms_chat_shorthand | 10 | 100.0% | 100.0% | +0.0 pp | 90.0% | 90.0% | +0.0 pp | 90.0% → 90.0% |

**Pattern Analysis:**
* No noise category exhibits a simultaneous degradation for both Sol and MODEL_G.
* In clean text (N0), Sol drops by 1 query while MODEL_G gains 1 query.
* In phonetic transliteration errors (N2), MODEL_G improves by +6.7 pp (+1 query) while Sol remains stable.
* In keyboard typos (N3), MODEL_G drops 1 query while Sol remains stable.
* N1, N4, and N5 show complete stability (0.0 pp delta) across both models.

---

## 7. Ambiguity and Answerability

### Ambiguity Breakdown

| Ambiguity Type | N | Sol T2 | Sol T3 | Sol Δ | MODEL_G T2 | MODEL_G T3 | MODEL_G Δ | Primary Agreement |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **none** | 109 | 99.1% | 98.2% | -0.9 pp | 93.6% | 95.4% | +1.8 pp | 92.7% → 95.4% |
| **dual_goal_conjunction** | 2 | 0.0% | 0.0% | +0.0 pp | 0.0% | 0.0% | +0.0 pp | 100.0% → 100.0% |
| **missing_destination_slot** | 1 | 0.0% | 0.0% | +0.0 pp | 100.0% | 0.0% | -100.0 pp | 0.0% → 0.0% |
| **missing_origin_slot** | 1 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 100.0% → 100.0% |
| **route_isolated_number** | 3 | 0.0% | 0.0% | +0.0 pp | 66.7% | 66.7% | +0.0 pp | 33.3% → 33.3% |
| **station_context_underspecified** | 2 | 50.0% | 50.0% | +0.0 pp | 50.0% | 50.0% | +0.0 pp | 100.0% → 100.0% |
| **underspecified_od_intent** | 2 | 50.0% | 50.0% | +0.0 pp | 50.0% | 50.0% | +0.0 pp | 100.0% → 100.0% |
| **underspecified_origin_transit** | 1 | 0.0% | 0.0% | +0.0 pp | 0.0% | 0.0% | +0.0 pp | 0.0% → 0.0% |
| **underspecified_temporal_departure** | 7 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 100.0% → 100.0% |

**Key Ambiguity Observations:**
* The vast majority of queries have no ambiguity (`none`, N=109), where concordance remains exceptionally high for both models (Sol 98.2%, MODEL_G 95.4%).
* Ambiguity categories have small counts (N=1 to 7). In `missing_destination_slot` (N=1, query: *"Guindy to anywhere mtero?"*), MODEL_G classified it under T2 as `route_query`, but under T3 flagged it for clarification (`primary_label = None`), aligning with Sol's assessment in both passes.
* **No ambiguity category shows joint degradation across both models.**

### Answerability Status Breakdown

| Answerability Status | N | Sol T2 | Sol T3 | Sol Δ | MODEL_G T2 | MODEL_G T3 | MODEL_G Δ | Primary Agreement |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **ANSWERABLE_NOW** | 57 | 96.5% | 94.7% | -1.8 pp | 91.2% | 91.2% | +0.0 pp | 94.7% → 96.5% |
| **ANSWERABLE_WITH_PROVISIONAL_DATA** | 54 | 87.0% | 87.0% | +0.0 pp | 87.0% | 88.9% | +1.9 pp | 83.3% → 87.0% |
| **ANSWERABLE_AFTER_MANUAL_VERIFICATION** | 5 | 80.0% | 80.0% | +0.0 pp | 80.0% | 80.0% | +0.0 pp | 100.0% → 100.0% |
| **OUT_OF_SCOPE** | 4 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 100.0% → 100.0% |
| **REQUIRES_REALTIME_DATA** | 8 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp | 100.0% → 100.0% |

**Key Answerability Observations:**
* Complete stability across `ANSWERABLE_AFTER_MANUAL_VERIFICATION`, `OUT_OF_SCOPE`, and `REQUIRES_REALTIME_DATA`.
* In `ANSWERABLE_NOW` (N=57), Sol experienced a 1-query drop (-1.8 pp) while MODEL_G remained invariant.
* In `ANSWERABLE_WITH_PROVISIONAL_DATA` (N=54), MODEL_G gained 1 query (+1.9 pp) while Sol remained invariant.
* **No answerability tier shows concurrent degradation for both models.**

---

## 8. Summary of Evidence

1. **Overall Parity:** On this 128-query challenge set, overall primary-exact concordance between T2 and T3 changes by less than 1 percentage point for both models (Sol: -0.8 pp; MODEL_G: +0.8 pp).
2. **Enhanced Model Alignment:** Inter-model agreement between GPT-5.6 Sol and MODEL_G increases under T3 across primary intent (+2.3 pp to 93.0%), acceptable set match (+7.0 pp to 82.8%), and clarification need (+3.1 pp to 85.9%).
3. **Indic Robustness:** Non-English and code-switched queries demonstrate total invariance between T2 and T3 across both models (0.0 pp change across 98 Indic/mixed queries). There is no descriptive indication of a Hindi or Hinglish degradation under T3.
4. **Surface & Ambiguity Invariance:** Noise types, script variations, ambiguity modes, and answerability categories reveal no systematic failure modes or simultaneous regressions across models under T3.
