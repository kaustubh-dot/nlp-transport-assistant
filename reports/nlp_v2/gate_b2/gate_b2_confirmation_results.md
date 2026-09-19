# NLP v2 Gate B.2 Taxonomy Confirmation Results

## 1. Executive Summary & Core Comparison

Gate B.2 evaluates candidate taxonomies on the confirmed and grounded stress-evaluation set (706 utterances) using capacity-matched architectures:
- **T2-H**: Shared-encoder multitask MuRIL (`google/muril-base-cased`) with Intent Head (12 classes) + Conditional Subtype Head (16 classes), $\lambda = 1.0$, `max_epochs = 30`.
- **T3**: Direct 16-class sequence classification MuRIL (`google/muril-base-cased`), `max_epochs = 30`.

### Core Confirmatory Multi-Seed Aggregate Table (3 Seeds: 42, 101, 777)

| Metric | T2-H (Hierarchical Multitask) | T3 (Direct 16-Class) | Difference (T3 - T2-H) | Significance |
| :--- | :---: | :---: | :---: | :---: |
| **Intent Macro-F1** | 0.7426 ± 0.0117 | 0.7420 ± 0.0376 | -0.0007 | — |
| **Downstream Op Accuracy** | 0.7531 ± 0.0024 | **0.7941 ± 0.0291** | **+0.0411** | True (p=0.0000e+00) |
| **Downstream Op Macro-F1** | 0.7105 ± 0.0098 | **0.7420 ± 0.0376** | **+0.0315** | — |
| **Contrast Group Exact (100%)** | 92.1% | **93.9%** | **+1.8 pp** | — |
| **Ambiguity-Aware Accuracy** | 0.7531 ± 0.0024 | **0.8069 ± 0.0306** | **+0.0538** | — |

---

## 2. Statistical Significance Analysis

### Paired McNemar Tests (Exact Downstream Operation per Seed)

| Seed | T3 Wins (b) | T2-H Wins (c) | Both Correct | Both Incorrect | $\chi^2$ Statistic | Two-Sided p-value |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Seed 42** | 64 | 10 | 520 | 112 | 37.9595 | 7.2230e-10 |
| **Seed 101** | 57 | 27 | 507 | 115 | 10.0119 | 1.5553e-03 |
| **Seed 777** | 41 | 38 | 493 | 134 | 0.0506 | 8.2197e-01 |

### Hierarchical Query x Seed Bootstrap (1,000 Resamples)
- **Mean Accuracy Difference (T3 - T2-H)**: `+0.0412`
- **95% Confidence Interval**: `[+0.0245, +0.0581]`
- **Two-Sided p-value**: `0.0000e+00`

---

## 3. Stratified Subgroup Performance (3-Seed Average)

### Language Breakdown

| Language Class | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
| `EN` | 215 | 0.6822 | **0.7085** | +0.0264 |
| `HINGLISH_LATN` | 164 | 0.7703 | **0.8211** | +0.0508 |
| `HI_DEVA` | 202 | 0.8465 | **0.8498** | +0.0033 |
| `HI_LATN` | 72 | 0.9444 | **0.9491** | +0.0046 |
| `MIXED_SCRIPT_CS` | 53 | 0.3711 | **0.6352** | +0.2642 |

### Code-Switching Complexity (CS0–CS4)

| CS Level | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
| `CS0` | 327 | 0.7278 | **0.7594** | +0.0316 |
| `CS1` | 90 | 0.8852 | **0.8407** | -0.0444 |
| `CS2` | 74 | 0.9459 | **0.9505** | +0.0045 |
| `CS3` | 162 | 0.7675 | **0.8189** | +0.0514 |
| `CS4` | 53 | 0.3711 | **0.6352** | +0.2642 |

### Text Corruption Robustness (N0–N5)

| Noise Level | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
| `N0` | 330 | 0.7949 | **0.8242** | +0.0293 |
| `N1` | 101 | 0.7789 | **0.8284** | +0.0495 |
| `N2` | 91 | 0.7179 | **0.7509** | +0.0330 |
| `N3` | 58 | 0.8333 | **0.8448** | +0.0115 |
| `N4` | 71 | 0.6479 | **0.7418** | +0.0939 |
| `N5` | 55 | 0.5636 | **0.6364** | +0.0727 |

### Author Source Breakdown

| Author Source | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
| `CURATED_AMBIGUITY` | 98 | 0.4966 | **0.5612** | +0.0646 |
| `CURATED_HARD_CASE` | 217 | 0.7435 | **0.7727** | +0.0292 |
| `CURATED_MINIMAL_PAIR` | 181 | 0.9650 | **0.9742** | +0.0092 |
| `TEMPLATE_GENERATED` | 210 | 0.7000 | **0.7698** | +0.0698 |

---

## 4. Calibration Analysis

| Metric | T2-H | T3 |
| :--- | :---: | :---: |
| **Confidence on Correct Cases** | 0.0167 | 0.6300 |
| **Confidence on Incorrect Cases** | 0.0149 | 0.4331 |
| **Confidence on Ambiguous Cases** | 0.0187 | 0.6946 |
| **Expected Calibration Error (ECE)** | 0.7368 | 0.2080 |
| **Brier Score Loss** | 0.7282 | 0.1974 |

---

## 5. Systematic Error Analysis (186 Total Evaluated Failure Cases)

| Category | Total Count | Description |
| :--- | :---: | :--- |
| `INTERCHANGE_VS_ROUTE` | 39 | Representative failure cases documented in JSON |
| `ROUTE_VS_MULTIMODAL` | 23 | Representative failure cases documented in JSON |
| `AVAILABILITY_VS_ROUTE` | 38 | Representative failure cases documented in JSON |
| `TIMING_SUBTYPE` | 30 | Representative failure cases documented in JSON |
| `SEQUENCE_VS_MEMBERSHIP` | 24 | Representative failure cases documented in JSON |
| `SEVERE_NOISE_CORRUPTION` | 9 | Representative failure cases documented in JSON |
| `STATIC_VS_REALTIME` | 1 | Representative failure cases documented in JSON |
| `OTHER` | 20 | Representative failure cases documented in JSON |
| `FACILITY_VS_ACCESSIBILITY` | 2 | Representative failure cases documented in JSON |

