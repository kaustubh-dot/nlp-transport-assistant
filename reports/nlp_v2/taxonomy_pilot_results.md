# NLP v2 Gate B Taxonomy Pilot Results

## 1. Executive Summary and Experimental Overview

This report documents the empirical results of the controlled taxonomy pilot comparing:
- **T1 Broad**: 9 intent classes
- **T2 Medium**: 12 intent classes
- **T3 Fine**: 16 intent classes

Across two distinct experimental evaluation regimes:
1. **Regime A (Equal Total Budget)**: 4,800 total samples (~3,354 train / 709 val / 737 eval) projected across all three taxonomies from a shared semantic scenario bank.
2. **Regime B (Equal Class Density)**: ~500 samples per intent class (T1: 4,500 samples, T2: 6,000 samples, T3: 8,000 samples).

Evaluated using two model families across 3 random seeds `[42, 101, 777]` (36 model training runs total):
- **TF-IDF + Logistic Regression** (n-gram feature baseline)
- **Google MuRIL** (`google/muril-base-cased`, fine-tuned sequence classification with BF16 and early stopping)

---

## 2. Aggregated Performance Metrics (Mean ± Std over 3 Seeds)

| Regime | Taxonomy | Classes | Model Family | Accuracy | Macro-F1 | Weighted-F1 | Downstream Sem-Op Acc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Regime A | T1 | 9 | Google MuRIL | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Regime A | T1 | 9 | TF-IDF + LogReg | 0.9959 ± 0.0000 | 0.9971 ± 0.0000 | 0.9959 ± 0.0000 | 0.9959 ± 0.0000 |
| Regime A | T2 | 12 | Google MuRIL | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Regime A | T2 | 12 | TF-IDF + LogReg | 0.9959 ± 0.0000 | 0.9978 ± 0.0000 | 0.9959 ± 0.0000 | 0.9959 ± 0.0000 |
| Regime A | T3 | 16 | Google MuRIL | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Regime A | T3 | 16 | TF-IDF + LogReg | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Regime B | T1 | 9 | Google MuRIL | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Regime B | T1 | 9 | TF-IDF + LogReg | 0.9985 ± 0.0000 | 0.9985 ± 0.0000 | 0.9985 ± 0.0000 | 0.9985 ± 0.0000 |
| Regime B | T2 | 12 | Google MuRIL | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Regime B | T2 | 12 | TF-IDF + LogReg | 0.9989 ± 0.0000 | 0.9989 ± 0.0000 | 0.9989 ± 0.0000 | 0.9989 ± 0.0000 |
| Regime B | T3 | 16 | Google MuRIL | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| Regime B | T3 | 16 | TF-IDF + LogReg | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |

---

## 3. Intra-Taxonomy Paired Statistical Tests (MuRIL vs. TF-IDF)

Testing whether MuRIL significantly outperforms TF-IDF on the identical label space:

| Regime | Taxonomy | Eval N | MuRIL Acc | TF-IDF Acc | McNemar Discordant (b/c) | McNemar p-value | Bootstrap 95% CI (MuRIL - TF-IDF) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| regime_a | T1 | 737 | 1.0000 | 0.9959 | 3 / 0 | 0.2482 | [+0.0000, +0.0095] |
| regime_a | T2 | 737 | 1.0000 | 0.9959 | 3 / 0 | 0.2482 | [+0.0000, +0.0095] |
| regime_a | T3 | 737 | 1.0000 | 1.0000 | 0 / 0 | 1.0000 | [+0.0000, +0.0000] |
| regime_b | T1 | 670 | 1.0000 | 0.9985 | 1 / 0 | 1.0000 | [+0.0000, +0.0045] |
| regime_b | T2 | 895 | 1.0000 | 0.9989 | 1 / 0 | 1.0000 | [+0.0000, +0.0034] |
| regime_b | T3 | 1197 | 1.0000 | 1.0000 | 0 / 0 | 1.0000 | [+0.0000, +0.0000] |

---

## 4. Cross-Taxonomy Paired Statistical Tests on Shared Semantic-Operation Space

Per Gate A Correction A, cross-taxonomy McNemar and paired bootstrap are conducted on downstream semantic-operation correctness across identical evaluation queries in Regime A:

| Model | Comparison | Eval N | Op-Acc A | Op-Acc B | McNemar Discordant (b/c) | McNemar p-value | Bootstrap 95% CI (A - B) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| muril | T1_vs_T2 | 737 | 1.0000 | 1.0000 | 0 / 0 | 1.0000 | [+0.0000, +0.0000] |
| muril | T1_vs_T3 | 737 | 1.0000 | 1.0000 | 0 / 0 | 1.0000 | [+0.0000, +0.0000] |
| muril | T2_vs_T3 | 737 | 1.0000 | 1.0000 | 0 / 0 | 1.0000 | [+0.0000, +0.0000] |
| tfidf | T1_vs_T2 | 737 | 0.9959 | 0.9959 | 0 / 0 | 1.0000 | [+0.0000, +0.0000] |
| tfidf | T1_vs_T3 | 737 | 0.9959 | 1.0000 | 0 / 3 | 0.2482 | [-0.0095, +0.0000] |
| tfidf | T2_vs_T3 | 737 | 0.9959 | 1.0000 | 0 / 3 | 0.2482 | [-0.0095, +0.0000] |

---

## 5. Language Subgroup Performance Breakdown

| Configuration | EN Acc | HI_DEVA Acc | HI_LATN Acc | HINGLISH_LATN Acc | MIXED_SCRIPT_CS Acc |
| :--- | :--- | :--- | :--- | :--- | :--- |
| regime_a_T1_muril | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| regime_a_T1_tfidf_logreg | 1.0000 | 0.9839 | 1.0000 | 1.0000 | 1.0000 |
| regime_a_T2_muril | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| regime_a_T2_tfidf_logreg | 1.0000 | 0.9839 | 1.0000 | 1.0000 | 1.0000 |
| regime_a_T3_muril | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| regime_a_T3_tfidf_logreg | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| regime_b_T1_muril | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| regime_b_T1_tfidf_logreg | 1.0000 | 0.9940 | 1.0000 | 1.0000 | 1.0000 |
| regime_b_T2_muril | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| regime_b_T2_tfidf_logreg | 1.0000 | 0.9955 | 1.0000 | 1.0000 | 1.0000 |
| regime_b_T3_muril | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| regime_b_T3_tfidf_logreg | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

---

## 6. Confusion Matrix Error Analysis

| Gold Intent | Predicted Intent | Error Count Across Runs |
| :--- | :--- | :--- |
| `route_query` | `service_timing` | 24 |

---

## 7. Seed Stability Analysis

Standard deviations across random seeds `[42, 101, 777]` confirm stability across runs:

| Regime | Taxonomy | Model Family | Macro-F1 Std Dev | Accuracy Std Dev |
| :--- | :--- | :--- | :--- | :--- |
| regime_a | T1 | muril | 0.00000 | 0.00000 |
| regime_a | T1 | tfidf_logreg | 0.00000 | 0.00000 |
| regime_a | T2 | muril | 0.00000 | 0.00000 |
| regime_a | T2 | tfidf_logreg | 0.00000 | 0.00000 |
| regime_a | T3 | muril | 0.00000 | 0.00000 |
| regime_a | T3 | tfidf_logreg | 0.00000 | 0.00000 |
| regime_b | T1 | muril | 0.00000 | 0.00000 |
| regime_b | T1 | tfidf_logreg | 0.00000 | 0.00000 |
| regime_b | T2 | muril | 0.00000 | 0.00000 |
| regime_b | T2 | tfidf_logreg | 0.00000 | 0.00000 |
| regime_b | T3 | muril | 0.00000 | 0.00000 |
| regime_b | T3 | tfidf_logreg | 0.00000 | 0.00000 |
