# Frozen complete T3 assistant evaluation

Assistant freeze: `b9b2271b1761d08752786f22b558862f45ed1dac`.

| Set | Queries | Intent accuracy | Selected operation accuracy | Terminal dispatch accuracy |
|---|---:|---:|---:|---:|
| Stress | 706 | 0.8272 | 0.5042 | 0.2323 |
| Human subset | 350 | 0.8371 | 0.5314 | 0.2571 |

Stress statuses: `{'clarification': 520, 'ok': 22, 'out_of_scope': 14, 'unavailable': 150}`. Clarification: `{'true_positive': 87, 'false_positive': 433, 'false_negative': 11, 'true_negative': 175, 'precision': 0.1673076923076923, 'recall': 0.8877551020408163}`.

Human subset statuses: `{'clarification': 251, 'ok': 12, 'out_of_scope': 5, 'unavailable': 82}`. Clarification: `{'true_positive': 67, 'false_positive': 184, 'false_negative': 9, 'true_negative': 90, 'precision': 0.26693227091633465, 'recall': 0.881578947368421}`.

Per-class and language/code-switch/noise aggregates, source hashes, and overlap counts are in `assistant_evaluation.json`.

## Interpretation

- Terminal dispatch accuracy counts correct operation with ok, unavailable, or out_of_scope; it does not establish a correct transport answer.
- Selected operation accuracy includes missing-slot clarifications carrying an operation; entity clarifications may carry no operation.
- Clarification gold is the frozen query annotation. Canonical entity ambiguity, missing KB coverage, and conservative runtime requirements can cause additional clarifications.
- The 350-row human subset is nested in stress. Both sets have train-family overlap; full scores are descriptive, not independent family-held-out estimates.
- No gold domain answers or aligned canonical slot IDs are supplied by this evaluator; slot accuracy and factual answer accuracy are not claimed.
- No model, extractor, dispatcher, or service tuning is permitted from this final evaluation.
