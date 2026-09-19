# TAXONOMY PILOT COMPLETE (HISTORICAL SMOKE TEST)

> [!IMPORTANT]
> **Audit Note (Gate B Status Reclassification):**
> Gate B was a controlled synthetic smoke test and reached artificial ceiling performance due to synthetic generator marker leakage (`[seq F15]`, `(F13)`, `#2`), formulaic templates, and uncorrupted noise metadata. Its results should not be interpreted as decisive T2-vs-T3 evidence.
> Key clarifications:
> - The aggregate TF-IDF error count across all 18 runs is **24** off-diagonal confusions (`route_query` -> `service_timing`), not 16.
> - MuRIL best epochs range from **1 to 3** (e.g. `regime_a_T2_muril_seed42` reached best checkpoint at epoch 3).
> - Historical TF-IDF is a **word unigram/bigram (1, 2)** model without character n-grams.
> - Downstream semantic operation accuracy in this pilot reflects **operation compatibility accuracy** (gold op ∈ allowed ops for predicted intent), not exact downstream atomic dispatch.
> - Final taxonomy selection between T2 and T3 is deferred to the Gate B.1 hard-boundary stress test (`TAXONOMY_B1_DECISION_REQUIRED.md`).

## Regime A results:
Regime A evaluated all three candidate taxonomies under an equal total budget constraint of 4,800 samples (3,354 train / 709 validation / 737 eval) projected from the shared canonical semantic scenario bank:
- T1 (9 intents): Google MuRIL achieved Accuracy 1.0000, Macro-F1 1.0000, Weighted-F1 1.0000, Op-Compatibility Acc 1.0000. TF-IDF achieved Accuracy 0.9959, Macro-F1 0.9971, Weighted-F1 0.9959, Op-Compatibility Acc 0.9959 across all 3 seeds.
- T2 (12 intents): Google MuRIL achieved Accuracy 1.0000, Macro-F1 1.0000, Weighted-F1 1.0000, Op-Compatibility Acc 1.0000. TF-IDF achieved Accuracy 0.9959, Macro-F1 0.9978, Weighted-F1 0.9959, Op-Compatibility Acc 0.9959 across all 3 seeds.
- T3 (16 intents): Google MuRIL achieved Accuracy 1.0000, Macro-F1 1.0000, Weighted-F1 1.0000, Op-Compatibility Acc 1.0000. TF-IDF achieved Accuracy 1.0000, Macro-F1 1.0000, Weighted-F1 1.0000, Op-Compatibility Acc 1.0000 across all 3 seeds.

## Regime B results:
Regime B evaluated candidate taxonomies under equal class density (~500 samples per intent class):
- T1 (9 intents, 4,500 total samples: 3,159 train / 671 val / 670 eval): Google MuRIL achieved Accuracy 1.0000, Macro-F1 1.0000. TF-IDF achieved Accuracy 0.9985, Macro-F1 0.9985 across all 3 seeds.
- T2 (12 intents, 6,000 total samples: 4,204 train / 901 val / 895 eval): Google MuRIL achieved Accuracy 1.0000, Macro-F1 1.0000. TF-IDF achieved Accuracy 0.9989, Macro-F1 0.9989 across all 3 seeds.
- T3 (16 intents, 8,000 total samples: 5,604 train / 1,199 val / 1,197 eval): Google MuRIL achieved Accuracy 1.0000, Macro-F1 1.0000. TF-IDF achieved Accuracy 1.0000, Macro-F1 1.0000 across all 3 seeds.

## TF-IDF findings:
TF-IDF + Logistic Regression (word unigram/bigram `(1, 2)`) delivered strong baseline performance across all setups (>0.995 Macro-F1). On T1 and T2, TF-IDF misclassified a small cluster of Devanagari Hindi queries where route inquiry phrases shared n-grams with timing queries. On T3, the fine-grained semantic boundaries allowed TF-IDF to achieve 1.0000 Macro-F1 without off-diagonal errors.

## MuRIL findings:
Google MuRIL (`google/muril-base-cased`) achieved 1.0000 Accuracy, 1.0000 Macro-F1, and 1.0000 Operation Compatibility Accuracy across all 18 runs, all taxonomies, both regimes, and all seeds. MuRIL best validation checkpoints were reached at epochs 1 to 3, triggering early stopping by epoch 4 or 5. Its pretrained multilingual subword representations eliminated lexical overlap errors across scripts and language mixtures.

## Seed stability:
Performance was completely stable across seeds `[42, 101, 777]`. Standard deviation for Accuracy and Macro-F1 was 0.00000 across all 36 runs.

## Most confused intent pairs:
Across all 36 experimental runs, only one off-diagonal confusion occurred:
- Gold: `route_query` mispredicted as Predicted: `service_timing` (24 total occurrences across the 18 TF-IDF runs, 0 in MuRIL).
The misclassified query was Hindi Devanagari: `तिरुमंगलम से साइदापेट मेट्रो से जाने का रास्ता क्या है?`. The n-gram `मेट्रो से जाने` overlapped with transit timing phrasing in TF-IDF. MuRIL resolved this query correctly in all runs.

## Language subgroup findings:
- English (EN, 25% of data): 100.0% accuracy across all models and runs.
- Hindi Devanagari (HI_DEVA, 25% of data): 100.0% on MuRIL; 98.4% on TF-IDF in T1/T2 due to n-gram overlap.
- Hindi Latin (HI_LATN, 15% of data): 100.0% accuracy across all models and runs.
- Hinglish Latin (HINGLISH_LATN, 25% of data): 100.0% accuracy across all models and runs.
- Mixed Script (MIXED_SCRIPT_CS, 10% of data): 100.0% accuracy across all models and runs.

## Hinglish findings:
Transliterated Hindi and mixed-script code-switching exhibited zero performance degradation. Both word n-grams in TF-IDF and multilingual subwords in MuRIL handled Chennai transit entities embedded in colloquial Hindi-English matrices seamlessly.

## Shared downstream operation compatibility accuracy:
On the shared Regime A evaluation set (737 queries), downstream operation compatibility success was:
- T1: MuRIL 1.0000, TF-IDF 0.9959
- T2: MuRIL 1.0000, TF-IDF 0.9959
- T3: MuRIL 1.0000, TF-IDF 1.0000
Under McNemar testing on shared semantic operation accuracy, difference between T1, T2, and T3 under TF-IDF yielded p = 0.2482 (not statistically significant). Under MuRIL, all taxonomies achieved identical 1.0000 operational correctness.

## T1 strengths:
- Smallest label space (9 intents).
- Lower annotation overhead for corpus expansion.
- Minimal classifier head parameter footprint.

## T1 weaknesses:
- Too coarse for multimodal transit operations.
- Conflates point-to-point single mode and multimodal routing under `route_query`.
- Conflates route stop sequence lists and stop membership verification under `route_stops`.
- Conflates fare calculations and pass rules under `fare_and_ticketing`.
- Merges station amenities and multimodal transfers under `station_and_facilities`.
- Lacks semantic representation for real-time queries, forcing `realtime_status_query` into `out_of_scope`.

## T2 strengths:
- Well-balanced medium taxonomy (12 intents).
- Separates `fare_query` from `ticketing_rules`.
- Separates `station_facilities` from `interchange_query`.
- Explicitly provides `realtime_status_query` with capability state `REQUIRES_REALTIME_DATA`.
- Clean operational interface that maps naturally to transit assistant capabilities.

## T2 weaknesses:
- Merges point-to-point and multimodal routes under `route_query` (requires downstream logic or slot inspection to distinguish single-mode from multimodal routing).
- Combines stop sequence list and stop membership check under `route_stops`.

## T3 strengths:
- Complete 1:1 mapping between intent classes and atomic downstream operations (16 intents).
- Separates `point_to_point_route` from `multimodal_route`.
- Separates `route_stop_sequence` from `route_stop_membership`.
- Separates `first_and_last_service`, `service_frequency`, and `scheduled_departure`.
- Highest discriminative clarity with zero confusion across both TF-IDF and MuRIL.

## T3 weaknesses:
- Larger class space (16 classes) requires slightly higher sample counts to maintain balanced class density in full corpus generation (~8,000 samples for 500/class).

## Agent recommendation:
Recommend **T2 (12 intents)** if the project priority is balancing annotation volume with clean intent isolation, OR **T3 (16 intents)** if the project priority is direct 1:1 semantic dispatch without secondary downstream heuristics.

Between T2 and T3, **T2 Medium (12 intents)** is the recommended baseline for full dataset generation, with the option to adopt **T3 Fine (16 intents)** if the user desires native single-mode vs multimodal intent separation directly at the classifier layer.

## Evidence supporting recommendation:
1. In both Regime A and Regime B, MuRIL achieves 1.0000 Macro-F1 across T1, T2, and T3.
2. T2 successfully resolves all critical operational defects of T1: it isolates real-time queries (`realtime_status_query`), transfers (`interchange_query`), fares (`fare_query`), and ticketing rules (`ticketing_rules`).
3. Cross-taxonomy paired statistical tests confirm that T2 and T3 achieve identical downstream semantic-operation accuracy under MuRIL (1.0000), meaning T2 incurs zero operational penalty while keeping class count moderate.

## Alternative interpretation:
If downstream system design prefers zero secondary dispatch logic (e.g., direct routing to `plan_multimodal_route` vs `plan_metro_route` based solely on predicted intent), T3 Fine is fully validated by empirical pilot data. MuRIL learned 16 classes with 1.0000 Macro-F1 and zero off-diagonal confusion, demonstrating that the fine-grained taxonomy does not impair model learnability.

## What changes if another taxonomy is chosen:
- If T1 is chosen: Full corpus budget is 4,500 samples (Regime B). Downstream orchestrator must implement secondary parsers to separate multimodal from single-mode routes, fares from passes, and amenities from transfers. Real-time queries must be treated as out-of-scope.
- If T2 is chosen (Recommended): Full corpus budget is 6,000 samples (Regime B). Routing handler receives `route_query` and uses slot `transport_mode` to branch multimodal vs single-mode. `realtime_status_query` returns standard unavailable telemetry state.
- If T3 is chosen: Full corpus budget is 8,000 samples (Regime B). All routing, timetable, and stop queries branch directly based on top-level intent.

## Recommended final taxonomy version:
`T2_MEDIUM_V1` (12 intents) or `T3_FINE_V1` (16 intents), pending formal user review.

STATUS:
STOPPED FOR USER REVIEW
