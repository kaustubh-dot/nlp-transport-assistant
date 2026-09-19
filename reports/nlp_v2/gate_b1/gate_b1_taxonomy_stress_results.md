# NLP v2 Gate B.1 Hard-Boundary Taxonomy Stress Test Results

## 1. Executive Summary & Core Comparison

Gate B.1 rigorously stresses candidate taxonomies **T2_MEDIUM_V1** (12 intents) and **T3_FINE_V1** (16 intents) on a diagnostic corpus of 630 evaluation utterances featuring real text corruptions (N0–N5), multi-dialect code-switching (CS0–CS4), minimal-pair contrast groups, implicit queries, and ambiguous intents with zero synthetic markers.

### Multi-Seed Aggregate Performance Table

| Model Family | Taxonomy / Stage | Intent Accuracy | Intent Macro-F1 | Downstream Op Accuracy | Contrast Group Consistency (100%) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **TFIDF_WORD** | T2 (Coarse Intent) | 0.5269 ± 0.0000 | 0.4209 ± 0.0000 | — | — |
| | T2-A (Rule / Slot Dispatch) | — | — | 0.4334 ± 0.0000 | 25.0% |
| | T2-B (Auxiliary Classifier) | — | — | 0.4518 ± 0.0000 | 46.1% |
| | **T3 (Direct Dispatch)** | **0.4433 ± 0.0000** | **0.4323 ± 0.0000** | **0.4433 ± 0.0000** | **42.1%** |
| **TFIDF_WORDCHAR** | T2 (Coarse Intent) | 0.6232 ± 0.0000 | 0.5876 ± 0.0000 | — | — |
| | T2-A (Rule / Slot Dispatch) | — | — | 0.5113 ± 0.0000 | 43.4% |
| | T2-B (Auxiliary Classifier) | — | — | 0.5439 ± 0.0000 | 64.5% |
| | **T3 (Direct Dispatch)** | **0.5722 ± 0.0000** | **0.5914 ± 0.0000** | **0.5722 ± 0.0000** | **67.1%** |
| **MURIL** | T2 (Coarse Intent) | 0.7989 ± 0.0162 | 0.6508 ± 0.0383 | — | — |
| | T2-A (Rule / Slot Dispatch) | — | — | 0.6067 ± 0.0093 | 49.6% |
| | T2-B (Auxiliary Classifier) | — | — | 0.7011 ± 0.0140 | 70.6% |
| | **T3 (Direct Dispatch)** | **0.7422 ± 0.0092** | **0.6895 ± 0.0291** | **0.7422 ± 0.0092** | **85.1%** |

---

## 2. Statistical Significance Analysis

### Downstream Operation McNemar Test (T3 Direct vs T2-B Auxiliary)
- Discordant pairs: T3 correct & T2-B incorrect (b) = `83`, T3 incorrect & T2-B correct (c) = `37`
- Test statistic: `16.8750`
- p-value: `3.9924e-05`

### Paired Bootstrap Resampling (1,000 resamples)
- Mean Macro-F1 Difference (T3 - T2-B): `+0.1451`
- 95% Confidence Interval: `[+0.1092, +0.1816]`
- p-value: `0.0000e+00`

---

## 3. Stratified Subgroup Performance (MuRIL Seed 42)

### Language Class Breakdown

| Subgroup | Count | T2-A Op Acc | T2-B Op Acc | T3 Op Acc | T3 Gain over T2-B |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `EN` | 215 | 0.4744 | 0.5814 | **0.6326** | +0.0512 |
| `HINGLISH_LATN` | 164 | 0.7744 | 0.7439 | **0.7866** | +0.0427 |
| `HI_DEVA` | 202 | 0.5743 | 0.7921 | **0.8366** | +0.0446 |
| `HI_LATN` | 72 | 0.5833 | 0.8056 | **0.9167** | +0.1111 |
| `MIXED_SCRIPT_CS` | 53 | 0.6415 | 0.3585 | **0.5660** | +0.2075 |

### Code-Switching Complexity (CS0–CS4)

| Subgroup | Count | T2-A Op Acc | T2-B Op Acc | T3 Op Acc | T3 Gain over T2-B |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `CS0` | 327 | 0.5566 | 0.6422 | **0.7248** | +0.0826 |
| `CS1` | 90 | 0.4000 | 0.8333 | **0.7556** | -0.0778 |
| `CS2` | 74 | 0.5946 | 0.8108 | **0.9189** | +0.1081 |
| `CS3` | 162 | 0.7716 | 0.7407 | **0.7840** | +0.0432 |
| `CS4` | 53 | 0.6415 | 0.3585 | **0.5660** | +0.2075 |

### Robustness Under Text Corruptions (N0–N5)

| Subgroup | Count | T2-A Op Acc | T2-B Op Acc | T3 Op Acc | T3 Gain over T2-B |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `N0` | 330 | 0.6667 | 0.7485 | **0.8061** | +0.0576 |
| `N1` | 101 | 0.5743 | 0.6436 | **0.7921** | +0.1485 |
| `N2` | 91 | 0.6044 | 0.6703 | **0.7473** | +0.0769 |
| `N3` | 58 | 0.6034 | 0.7759 | **0.7759** | +0.0000 |
| `N4` | 71 | 0.5211 | 0.5915 | **0.6761** | +0.0845 |
| `N5` | 55 | 0.2909 | 0.4364 | **0.4182** | -0.0182 |

### Implicit Intent Accuracy (is_implicit)

| Subgroup | Count | T2-A Op Acc | T2-B Op Acc | T3 Op Acc | T3 Gain over T2-B |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `False` | 592 | 0.6774 | 0.6639 | **0.7517** | +0.0878 |
| `True` | 114 | 0.1754 | 0.7982 | **0.7456** | -0.0526 |

### Ambiguous / Multi-Intent Queries (is_ambiguous)

| Subgroup | Count | T2-A Op Acc | T2-B Op Acc | T3 Op Acc | T3 Gain over T2-B |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `False` | 608 | 0.5609 | 0.6974 | **0.7763** | +0.0789 |
| `True` | 98 | 0.8163 | 0.6122 | **0.5918** | -0.0204 |

### Generalization: Synthetic Stress vs Independent Authored

| Subgroup | Count | T2-A Op Acc | T2-B Op Acc | T3 Op Acc | T3 Gain over T2-B |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `independent_authored` | 181 | 0.7072 | 0.8343 | **0.9613** | +0.1271 |
| `synthetic_stress` | 525 | 0.5581 | 0.6343 | **0.6781** | +0.0438 |

---

## 4. Error Review & Failure Taxonomy (>= 100 Audited Cases)

Audited `259` evaluation errors across systematic failure modes:

| Failure Mode Category | Count | Primary Affected Sibling Pairs |
| :--- | :---: | :--- |
| `BOUNDARY_CONFUSION_FARE_VS_PASS_RULES` | 7 | Exemplars detailed in report JSON |
| `HIGH_COMPLEXITY_CODE_SWITCHING` | 31 | Exemplars detailed in report JSON |
| `SEVERE_ORTHOGRAPHIC_OR_KEYBOARD_NOISE` | 85 | Exemplars detailed in report JSON |
| `CROSS_DOMAIN_SEMANTIC_CONFUSION` | 40 | Exemplars detailed in report JSON |
| `BOUNDARY_CONFUSION_STOP_SEQUENCE_VS_MEMBERSHIP` | 10 | Exemplars detailed in report JSON |
| `BOUNDARY_CONFUSION_SERVICE_TIMING_SUBTYPES` | 2 | Exemplars detailed in report JSON |
| `LEXICAL_AMBIGUITY_OR_DUAL_INTENT` | 42 | Exemplars detailed in report JSON |
| `IMPLICIT_INTENT_WITHOUT_KEYWORDS` | 42 | Exemplars detailed in report JSON |

