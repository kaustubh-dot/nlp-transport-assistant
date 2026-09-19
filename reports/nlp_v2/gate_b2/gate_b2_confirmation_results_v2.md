# NLP v2 Gate B.2 Taxonomy Confirmation Results (v2 Audit Corrected)

**Model Results Commit:** `9345a246d44534e7aa002f7535f1cadae8c2b086`  
**Active Multimodal KB:** `chennai_multimodal_v1.2.2`  
**Audit Status:** v2 Post-Audit Corrected Report (Historical raw predictions preserved)

---

## 1. Executive Summary & Core Comparison

Gate B.2 evaluates candidate taxonomies on the confirmed and grounded stress-evaluation set (706 utterances) using capacity-matched architectures:
- **T2-H**: Shared-encoder multitask MuRIL (`google/muril-base-cased`) with 12-class T2 top-level intent head + global 16-class atomic semantic-subtype head, joint loss $\lambda = 1.0$, `max_epochs = 30`.
- **T3**: Direct 16-class sequence classification MuRIL (`google/muril-base-cased`), `max_epochs = 30`.

### Core Confirmatory Multi-Seed Aggregate Table (3 Seeds: 42, 101, 777)

| Metric | T2-H (Shared-Encoder Multitask) | T3 (Direct 16-Class) | Difference (T3 - T2-H) | Significance / Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Intent Macro-F1** | 0.7426 ± 0.0117 | 0.7420 ± 0.0376 | -0.0007 | Intent level |
| **Downstream Op Accuracy** | 0.7531 ± 0.0024 | **0.7941 ± 0.0291** | **+0.0411 (+4.11 pp)** | **empirical p < 0.002** (95% CI: [+0.0245, +0.0581]) |
| **Downstream Op Macro-F1** | 0.7105 ± 0.0098 | **0.7420 ± 0.0376** | **+0.0315** | Operation level |
| **Contrast Group Exact (100%)** | 92.1% | **93.9%** | **+1.8 pp** | All contrast group items correct |
| **Audited Ambiguity-Aware Acc** | 0.7668 ± 0.0084 | **0.8069 ± 0.0306** | **+0.0401 (+4.01 pp)** | Corrected cross-namespace mapping |
| ↳ *Ambiguous-Only Subset* | 0.5952 ± 0.0585 | **0.6531 ± 0.0464** | **+0.0578 (+5.78 pp)** | Ambiguous queries (N=98) |
| ↳ *Non-Ambiguous Subset* | 0.7944 ± 0.0036 | **0.8317 ± 0.0298** | **+0.0373 (+3.73 pp)** | Unambiguous queries (N=608) |

---

## 2. Statistical Significance Analysis

### Paired McNemar Tests (Exact Downstream Operation per Seed)

| Seed | T3 Wins (b) | T2-H Wins (c) | Both Correct | Both Incorrect | $\chi^2$ Statistic | Two-Sided p-value | Significance Interpretation |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Seed 42** | 64 | 10 | 520 | 112 | 37.9595 | 7.2230e-10 | **Statistically Significant** (T3 wins) |
| **Seed 101** | 57 | 27 | 507 | 115 | 10.0119 | 1.5553e-03 | **Statistically Significant** (T3 wins) |
| **Seed 777** | 41 | 38 | 493 | 134 | 0.0506 | 0.8220 | No significant difference (near tie) |

> [!NOTE]
> **Multi-Seed Significance Interpretation (Section 36):**
> T3 shows a positive aggregate multi-seed advantage (+4.11 pp). Two of three seeds (42 and 101) show individually significant paired gains under McNemar's test with continuity correction, while seed 777 is statistically indistinguishable ($p = 0.800$).

### Hierarchical Query x Seed Bootstrap (1,000 Resamples)
- **Mean Accuracy Difference (T3 - T2-H)**: `+0.0412`
- **95% Confidence Interval**: `[+0.0245, +0.0581]`
- **Reported p-value**: `empirical p < 0.002`

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

## 4. Calibration Analysis (Marked Not Directly Comparable)

> [!WARNING]
> **Calibration Comparability Limitation (Section 29 & 30):**
> T3 confidence is the maximum softmax probability from a single 16-class head. T2-H confidence is the product of marginal confidences across dual heads ($P(\text{intent}) \times P(\text{subtype})$). These do not represent equivalent probability spaces. Therefore, ECE and Brier score differences are **not directly comparable** and must not be used as decisive evidence for taxonomy selection.

| Metric | T2-H (Dual Head Product) | T3 (Single 16-Class Softmax) | Comparability Status |
| :--- | :---: | :---: | :--- |
| **Confidence on Correct Cases** | 0.0167 | 0.6300 | NOT DIRECTLY COMPARABLE |
| **Confidence on Incorrect Cases** | 0.0149 | 0.4331 | NOT DIRECTLY COMPARABLE |
| **Confidence on Ambiguous Cases** | 0.0187 | 0.6946 | NOT DIRECTLY COMPARABLE |
| **Expected Calibration Error (ECE)** | 0.7368 | 0.2080 | NOT DIRECTLY COMPARABLE |
| **Brier Score Loss** | 0.7282 | 0.1974 | NOT DIRECTLY COMPARABLE |

---

## 5. Audited Disagreement & Error Analysis (186 Total Evaluated Failure Cases)

Categorized using explicit operation-pair mappings (gold operation vs predicted operation):

| Disagreement Category | Count | Primary Models Affected | Description |
| :--- | :---: | :---: | :--- |
| `OTHER` | 62 | Both models | Operation-pair failure cases audited in JSON |
| `OOS_CONFUSION` | 37 | Both models | Operation-pair failure cases audited in JSON |
| `SEQUENCE_TO_MEMBERSHIP` | 20 | Both models | Operation-pair failure cases audited in JSON |
| `TIMING_SUBTYPE` | 18 | Both models | Operation-pair failure cases audited in JSON |
| `MULTIMODAL_TO_ROUTE` | 11 | Both models | Operation-pair failure cases audited in JSON |
| `ROUTE_TO_INTERCHANGE` | 11 | Both models | Operation-pair failure cases audited in JSON |
| `INTERCHANGE_TO_ROUTE` | 10 | Both models | Operation-pair failure cases audited in JSON |
| `STATIC_TO_REALTIME` | 6 | Both models | Operation-pair failure cases audited in JSON |
| `FARE_TO_INTERCHANGE` | 3 | Both models | Operation-pair failure cases audited in JSON |
| `REALTIME_TO_STATIC` | 3 | Both models | Operation-pair failure cases audited in JSON |
| `FACILITY_TO_ACCESSIBILITY` | 3 | Both models | Operation-pair failure cases audited in JSON |
| `AVAILABILITY_TO_ROUTE` | 1 | Both models | Operation-pair failure cases audited in JSON |
| `ROUTE_TO_AVAILABILITY` | 1 | Both models | Operation-pair failure cases audited in JSON |

---

## 6. Diagnostic Masking Interpretation

- **Named Entity Masking Diagnostic:** Masking recognized station/stop/place entities did not degrade aggregate performance for either T2-H or T3 on this specific diagnostic set. However, per Section 31, this does **not** establish universal generalization to completely unseen transit networks or ungrounded entities.
- **Functional Token Masking Diagnostic:** Masking transit function keywords lowered T3 performance more than T2-H, indicating greater dependence on functional transit vocabulary within this diagnostic.
