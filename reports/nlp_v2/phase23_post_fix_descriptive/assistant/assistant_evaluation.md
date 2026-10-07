# Phase23 post-fix descriptive regression evaluation

Assistant freeze: `e008c0474c1301a3b442b31761f31c79e7dec446`. Fixed reference date2026-10-06.

One separately authorized complete-assistant run on the already observed set; valid Phase21 is preserved unchanged. No model-only rerun or tuning follows. See [comparison and all strata](../comparison.md).

| Set | Queries | Intent accuracy | Selected operation accuracy | Terminal dispatch accuracy |
|---|---:|---:|---:|---:|
| Stress | 706 | 0.82719547 | 0.61048159 | 0.40368272 |
| Human subset | 350 | 0.83714286 | 0.63428571 | 0.40857143 |

Both sets’ metrics, statuses, clarification statistics and all strata exactly match Phase21. JSON is the unchanged evaluator output; this Markdown title/table formatting is documentary only, with no evaluator rerun.

## Interpretation

- Terminal dispatch accuracy counts correct operation with ok, unavailable, or out_of_scope; it does not establish a correct transport answer.
- Selected operation accuracy includes missing-slot clarifications carrying an operation; entity clarifications may carry no operation.
- Clarification gold is the frozen query annotation. Canonical entity ambiguity, missing KB coverage, and conservative runtime requirements can cause additional clarifications.
- The 350-row human subset is nested in stress. Both sets have train-family overlap; full scores are descriptive, not independent family-held-out estimates.
- No gold domain answers or aligned canonical slot IDs are supplied by this evaluator; slot accuracy and factual answer accuracy are not claimed.
- No model, extractor, dispatcher, or service tuning is permitted from this final evaluation.
