# Phase23 post-fix descriptive regression evaluation

Post-review backend freeze: `e008c0474c1301a3b442b31761f31c79e7dec446`. Fixed Chennai reference date: **2026-10-06**.

The unchanged complete-assistant evaluator ran **exactly once** after this committed freeze, into this new directory. This measures the already observed evaluation set; it is not an untouched or independent test, or a replacement for valid Phase21. No model-only rerun was performed: selected model/inference/preprocessing are unchanged. No individual failures were inspected and no tuning follows.

Phase20 freeze → valid Phase21 descriptive evaluation → Phase22 presentation → independent Phase23 review discovered timetable scope loss → explicit user-authorized correctness exception → synthetic red/green fix and scoped review → new backend freeze → this separate descriptive run → final whole-project review → project close.

## Aggregate comparison to preserved Phase21

Every metric, status count, clarification count, and per-intent/language/code-switch/noise stratum is identical to Phase21 on both sets. This does not negate the synthetic correctness fix or establish semantic scope correctness on arbitrary queries. The success criterion is preserving route scope or declining unsupported scope; aggregate improvement was not required.

| Set | N | Metric | Phase21 | Phase23 | Delta |
|---|---:|---|---:|---:|---:|
| Stress | 706 | strict_intent_accuracy | 0.82719547 | 0.82719547 | 0.00000000 |
| Stress | 706 | selected_operation_accuracy | 0.61048159 | 0.61048159 | 0.00000000 |
| Stress | 706 | terminal_dispatch_accuracy | 0.40368272 | 0.40368272 | 0.00000000 |
| Stress | 706 | clarification_precision | 0.14986376 | 0.14986376 | 0 |
| Stress | 706 | clarification_recall | 0.56122449 | 0.56122449 | 0 |
| Human subset | 350 | strict_intent_accuracy | 0.83714286 | 0.83714286 | 0.00000000 |
| Human subset | 350 | selected_operation_accuracy | 0.63428571 | 0.63428571 | 0.00000000 |
| Human subset | 350 | terminal_dispatch_accuracy | 0.40857143 | 0.40857143 | 0.00000000 |
| Human subset | 350 | clarification_precision | 0.25274725 | 0.25274725 | 0 |
| Human subset | 350 | clarification_recall | 0.60526316 | 0.60526316 | 0 |

| Set | Clarification | Unavailable | OK | Out of scope | Error | Correct selected / terminal |
|---|---:|---:|---:|---:|---:|---|
| Stress | 367 | 306 | 19 | 14 | 0 | 431/706 / 285/706 |
| Human subset | 182 | 153 | 10 | 5 | 0 | 222/350 / 143/350 |

| Set | TP | FP | FN | TN |
|---|---:|---:|---:|---:|
| Stress | 55 | 312 | 43 | 296 |
| Human subset | 46 | 136 | 30 | 138 |

## Stress: language_class (all unchanged from Phase21)

| Stratum | N | Phase21 terminal | Phase23 terminal | Clarification | Unavailable | OK | Out of scope | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EN | 215 | 0.30232558 | 0.30232558 | 132 | 60 | 9 | 14 | 0 |
| HINGLISH_LATN | 164 | 0.45731707 | 0.45731707 | 79 | 84 | 1 | 0 | 0 |
| HI_DEVA | 202 | 0.42079208 | 0.42079208 | 97 | 101 | 4 | 0 | 0 |
| HI_LATN | 72 | 0.44444444 | 0.44444444 | 40 | 28 | 4 | 0 | 0 |
| MIXED_SCRIPT_CS | 53 | 0.52830189 | 0.52830189 | 19 | 33 | 1 | 0 | 0 |

## Stress: code_switch_level (all unchanged from Phase21)

| Stratum | N | Phase21 terminal | Phase23 terminal | Clarification | Unavailable | OK | Out of scope | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CS0 | 327 | 0.35779817 | 0.35779817 | 183 | 121 | 9 | 14 | 0 |
| CS1 | 90 | 0.36666667 | 0.36666667 | 46 | 40 | 4 | 0 | 0 |
| CS2 | 74 | 0.44594595 | 0.44594595 | 41 | 28 | 5 | 0 | 0 |
| CS3 | 162 | 0.45679012 | 0.45679012 | 78 | 84 | 0 | 0 | 0 |
| CS4 | 53 | 0.52830189 | 0.52830189 | 19 | 33 | 1 | 0 | 0 |

## Stress: noise_level (all unchanged from Phase21)

| Stratum | N | Phase21 terminal | Phase23 terminal | Clarification | Unavailable | OK | Out of scope | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| N0 | 330 | 0.48787879 | 0.48787879 | 150 | 163 | 12 | 5 | 0 |
| N1 | 101 | 0.44554455 | 0.44554455 | 50 | 43 | 3 | 5 | 0 |
| N2 | 91 | 0.34065934 | 0.34065934 | 52 | 36 | 0 | 3 | 0 |
| N3 | 58 | 0.41379310 | 0.41379310 | 27 | 26 | 4 | 1 | 0 |
| N4 | 71 | 0.19718310 | 0.19718310 | 52 | 19 | 0 | 0 | 0 |
| N5 | 55 | 0.18181818 | 0.18181818 | 36 | 19 | 0 | 0 | 0 |

## Human subset: language_class (all unchanged from Phase21)

| Stratum | N | Phase21 terminal | Phase23 terminal | Clarification | Unavailable | OK | Out of scope | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EN | 119 | 0.31932773 | 0.31932773 | 67 | 40 | 7 | 5 | 0 |
| HINGLISH_LATN | 93 | 0.54838710 | 0.54838710 | 39 | 53 | 1 | 0 | 0 |
| HI_DEVA | 88 | 0.38636364 | 0.38636364 | 49 | 38 | 1 | 0 | 0 |
| HI_LATN | 37 | 0.45945946 | 0.45945946 | 20 | 17 | 0 | 0 | 0 |
| MIXED_SCRIPT_CS | 13 | 0.23076923 | 0.23076923 | 7 | 5 | 1 | 0 | 0 |

## Human subset: code_switch_level (all unchanged from Phase21)

| Stratum | N | Phase21 terminal | Phase23 terminal | Clarification | Unavailable | OK | Out of scope | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CS0 | 180 | 0.36111111 | 0.36111111 | 99 | 69 | 7 | 5 | 0 |
| CS1 | 27 | 0.25925926 | 0.25925926 | 17 | 9 | 1 | 0 | 0 |
| CS2 | 39 | 0.46153846 | 0.46153846 | 21 | 17 | 1 | 0 | 0 |
| CS3 | 91 | 0.54945055 | 0.54945055 | 38 | 53 | 0 | 0 | 0 |
| CS4 | 13 | 0.23076923 | 0.23076923 | 7 | 5 | 1 | 0 | 0 |

## Human subset: noise_level (all unchanged from Phase21)

| Stratum | N | Phase21 terminal | Phase23 terminal | Clarification | Unavailable | OK | Out of scope | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| N0 | 172 | 0.48255814 | 0.48255814 | 79 | 84 | 7 | 2 | 0 |
| N1 | 47 | 0.44680851 | 0.44680851 | 21 | 22 | 2 | 2 | 0 |
| N2 | 37 | 0.37837838 | 0.37837838 | 22 | 14 | 0 | 1 | 0 |
| N3 | 34 | 0.35294118 | 0.35294118 | 20 | 13 | 1 | 0 | 0 |
| N4 | 33 | 0.18181818 | 0.18181818 | 23 | 10 | 0 | 0 | 0 |
| N5 | 27 | 0.25925926 | 0.25925926 | 17 | 10 | 0 | 0 | 0 |

## Integrity, scope and interpretation

Stress contains706 rows and the nested human subset350. Train semantic-family overlap affects187 stress and160 human rows; exact-query overlap is0. The earlier partial contrast-group caveat also remains. The evaluator has no aligned gold canonical slots or transport facts, so factual-answer/slot accuracy is not measured. Correct terminal dispatch includes unavailable and out-of-scope operations. Clarification precision and successful-answer coverage remain limited.

Only the independently found timetable defect was corrected, using fixture-only synthetic regressions. The canonical contract cannot execute waypoint filters, so explicit unavailable prevents partial answers; extra/conflicting stops clarify. No general extractor/alias/domain/model changes occurred. Full677 tests and fresh scoped review pass. No post-run tuning or new development phase follows.

Original [Phase21 reports](../post_development_regression/comparison.md) remain unchanged and valid for freeze8ee8917. [Machine-readable aggregates](assistant/assistant_evaluation.json) preserve the unchanged evaluator schema and all16 intent strata. [Context ledger](evaluation_context.json) records invocation count, labels, hashes and freeze; [final review](../final_review/review.md) records the whole-project gate.
