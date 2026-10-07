# Phase 21 post-development descriptive regression evaluation

1. Commit and push the reviewed Phase 20 backend; require a clean freeze path.
2. Run the existing selected-model and complete-assistant evaluators once into
   new `reports/nlp_v2/post_development_regression/{model,assistant}` directories.
   Use reference date 2026-10-06, matching the historical b9b2271 baseline.
3. Inspect aggregate outputs only. Reconstruct counts/metrics and compare the
   unchanged model and changed assistant to preserved historical reports.
4. Write a prominently labeled post-development descriptive report, including
   statuses, clarification precision/recall, language/switch/noise strata and
   leakage/factual-answer limitations. The historical sets have already been
   observed; this is not an untouched test estimate.
5. Fresh GPT-6.1 Sol xhigh reviews integrity and claims. Commit/push reports.

No individual failures, query text or held-out slot/fact labels are inspected.
No backend/model/prompt/threshold/extractor tuning follows the evaluation. Phase
22 may change presentation only, with the API, backend and model held fixed.
An invalid run requires transparent catastrophic-bug documentation before any
replacement; ordinary score limitations do not justify a retry.
