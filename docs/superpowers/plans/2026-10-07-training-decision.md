# Phase 17 evidence and training decision plan

Primary implements inline; fresh GPT-6.1 Sol xhigh reviews.

- [x] Add synthetic attribution regressions for raw/reply differences, recovered wrong classes, null-intent contracts and downstream failures.
- [x] Capture raw model predictions and run intended-intent counterfactuals on frozen development v1; evaluate only allowed disjoint validation aggregates.
- [x] Correct future coverage metadata that conflates reply-intent metrics with raw classifier accuracy, preserving existing phase reports.
- [x] Write the evidence-based decision and exact guarded GPU candidate command, resources, artifact destination and promotion limits if justified.
- [x] Verify full tests, hashes and report reconstruction; independent review, fixes/re-review, progress record, commit/push.
- [x] Respect the user's conditional GPU stop if reached; otherwise continue Phase 18.
