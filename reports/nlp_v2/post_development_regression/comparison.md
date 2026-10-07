# Post-development descriptive regression evaluation — Phase 21

Backend freeze: `8ee8917fef1f3664ec53d25e38dc5b9134aec270`. Selected model/checkpoint unchanged. Both existing evaluators ran once into new output directories. Chennai reference date **2026-10-06** matches the preserved `b9b2271` assistant baseline.

**These historical stress/reference sets have already been observed. This is a post-development descriptive regression evaluation, not a new untouched test estimate.** Only aggregate outputs were inspected; no individual failures or queries were used for tuning. Evaluation ends backend development. Later frontend work changes presentation only.

## Model intent and mapped operation metrics

| Set | Count | Intent accuracy | Macro-F1 | Mapped operation accuracy |
|---|---:|---:|---:|---:|
| Stress | 706 | 0.8300 | 0.7918 | 0.8300 |
| Nested human subset | 350 | 0.8400 | 0.7777 | 0.8400 |

All model-only aggregate metrics and hashes match the historical selected-model report exactly. Mapped operation accuracy is a label mapping, not domain execution.

## Complete assistant versus historical baseline

| Set / state | Reply-intent accuracy | Selected operation | Terminal dispatch | Clarification precision | Clarification recall |
|---|---:|---:|---:|---:|---:|
| Stress / b9b2271 | 0.8272 | 0.5042 | 0.2323 | 0.1673 | 0.8878 |
| Stress / Phase 20 freeze | 0.8272 | 0.6105 | 0.4037 | 0.1499 | 0.5612 |
| Human subset / b9b2271 | 0.8371 | 0.5314 | 0.2571 | 0.2669 | 0.8816 |
| Human subset / Phase 20 freeze | 0.8371 | 0.6343 | 0.4086 | 0.2527 | 0.6053 |

| Set / state | OK | Clarification | Unavailable | Out of scope | Error |
|---|---:|---:|---:|---:|---:|
| Stress / b9b2271 | 22 | 520 | 150 | 14 | 0 |
| Stress / Phase 20 freeze | 19 | 367 | 306 | 14 | 0 |
| Human subset / b9b2271 | 12 | 251 | 82 | 5 | 0 |
| Human subset / Phase 20 freeze | 10 | 182 | 153 | 5 | 0 |

Stress selected-operation count improves 356→431/706; terminal dispatch improves 164→285/706. Clarification falls 520→367 and false-positive clarification against frozen annotations falls 433→312. **Clarification precision declines 0.1673→0.1499 and recall declines 0.8878→0.5612; OK answers decline 22→19.** No claim of uniform improvement or increased historical answer coverage is made.

More terminal dispatch largely coexists with unavailable responses (150→306), so it is not evidence of more correct travel answers. The development policy refuses absent sources before asking non-actionable execution inputs; that policy can differ from the frozen query-level clarification annotation. Aggregate data cannot establish the cause or appropriateness of each changed case, and no item inspection was performed. The classifier, source and ambiguity limitations remain.

## Stress language, code-switch and noise strata

| Dimension | Group | Count | Baseline terminal dispatch | Current terminal dispatch | OK / clarify / unavailable / OOS / error |
|---|---|---:|---:|---:|---|
| language_class | EN | 215 | 0.2279 | 0.3023 | 9/132/60/14/0 |
| language_class | HINGLISH_LATN | 164 | 0.2866 | 0.4573 | 1/79/84/0/0 |
| language_class | HI_DEVA | 202 | 0.1832 | 0.4208 | 4/97/101/0/0 |
| language_class | HI_LATN | 72 | 0.2639 | 0.4444 | 4/40/28/0/0 |
| language_class | MIXED_SCRIPT_CS | 53 | 0.2264 | 0.5283 | 1/19/33/0/0 |
| code_switch_level | CS0 | 327 | 0.1804 | 0.3578 | 9/183/121/14/0 |
| code_switch_level | CS1 | 90 | 0.3000 | 0.3667 | 4/46/40/0/0 |
| code_switch_level | CS2 | 74 | 0.2703 | 0.4459 | 5/41/28/0/0 |
| code_switch_level | CS3 | 162 | 0.2840 | 0.4568 | 0/78/84/0/0 |
| code_switch_level | CS4 | 53 | 0.2264 | 0.5283 | 1/19/33/0/0 |
| noise_level | N0 | 330 | 0.2485 | 0.4879 | 12/150/163/5/0 |
| noise_level | N1 | 101 | 0.2673 | 0.4455 | 3/50/43/5/0 |
| noise_level | N2 | 91 | 0.2088 | 0.3407 | 0/52/36/3/0 |
| noise_level | N3 | 58 | 0.2241 | 0.4138 | 4/27/26/1/0 |
| noise_level | N4 | 71 | 0.1549 | 0.1972 | 0/52/19/0/0 |
| noise_level | N5 | 55 | 0.2182 | 0.1818 | 0/36/19/0/0 |

Full nested-subset strata, per-intent aggregates, model language/switch/noise scores and clarification confusion counts remain in the linked JSON outputs. Counts are overlapping stratifications of the same evaluation set, not independent experiments.

## Integrity and limits

- Frozen T3 labels/raw MuRIL/max64/revision/checkpoint, canonical DB, stress/reference/train hashes and existing evaluator source remain unchanged. Source freeze verification passed before and after evaluation.
- The original selected checkpoint used train-family-overlapping validation; the Phase17 disjoint-validation candidate failed its validation-only promotion gate and the selected checkpoint was retained. Human-subset contrast-group accuracy also covers 17 partial groups out of 73 observed groups.
- 350 human rows are nested in 706 stress rows. Family/semantic/exact overlap affects 187 stress and 160 human rows; exact query overlap is zero. These are descriptive, not independent family-held-out estimates.
- Terminal dispatch counts correct gold operation with OK, unavailable or out-of-scope. Selected-operation accuracy can include missing-slot clarification. Reply-intent accuracy is after assistant guards, distinct from raw model accuracy.
- No aligned gold domain facts or canonical slot IDs exist here. Factual transport-answer accuracy and slot accuracy are not measured. No claim of safe travel/current operation follows these metrics.
- Generated JSON preserves the existing evaluator schema/evaluation_type. This document, the new report titles and evaluation_context.json supply the required post-development interpretation without changing scoring or rerunning.
- Historical reports and research remain untouched. No invalid run/replacement was needed. No backend tuning, model selection or adaptive rerun follows these results.

[Model aggregates](model/production_t3_evaluation.json) · [Assistant aggregates](assistant/assistant_evaluation.json) · [Historical baseline](../assistant_eval/assistant_evaluation.json) · [Development acceptance](../../../docs/nlp_v2/development_acceptance.md)
