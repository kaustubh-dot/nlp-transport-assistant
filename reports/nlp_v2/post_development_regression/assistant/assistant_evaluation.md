# Post-development descriptive regression — complete T3 assistant evaluation

The historical evaluation sets were already observed. This rerun is descriptive, not an untouched test estimate. No backend tuning follows it.

Assistant freeze: `8ee8917fef1f3664ec53d25e38dc5b9134aec270`.

| Set | Queries | Intent accuracy | Selected operation accuracy | Terminal dispatch accuracy |
|---|---:|---:|---:|---:|
| Stress | 706 | 0.8272 | 0.6105 | 0.4037 |
| Human subset | 350 | 0.8371 | 0.6343 | 0.4086 |

Stress statuses: `{'clarification': 367, 'ok': 19, 'out_of_scope': 14, 'unavailable': 306}`. Clarification: `{'true_positive': 55, 'false_positive': 312, 'false_negative': 43, 'true_negative': 296, 'precision': 0.14986376021798364, 'recall': 0.5612244897959183}`.

Human subset statuses: `{'clarification': 182, 'ok': 10, 'out_of_scope': 5, 'unavailable': 153}`. Clarification: `{'true_positive': 46, 'false_positive': 136, 'false_negative': 30, 'true_negative': 138, 'precision': 0.25274725274725274, 'recall': 0.6052631578947368}`.


Per-class and language/code-switch/noise aggregates, source hashes, and overlap counts are in `assistant_evaluation.json`.

## Interpretation

- Terminal dispatch accuracy counts correct operation with ok, unavailable, or out_of_scope; it does not establish a correct transport answer.
- Selected operation accuracy includes missing-slot clarifications carrying an operation; entity clarifications may carry no operation.
- Clarification gold is the frozen query annotation. Canonical entity ambiguity, missing KB coverage, and conservative runtime requirements can cause additional clarifications.
- The 350-row human subset is nested in stress. Both sets have train-family overlap; full scores are descriptive, not independent family-held-out estimates.
- No gold domain answers or aligned canonical slot IDs are supplied by this evaluator; slot accuracy and factual answer accuracy are not claimed.
- No model, extractor, dispatcher, or service tuning is permitted from this final evaluation.
