# Production T3 evaluation plan

1. Write synthetic metric and reference-join tests before evaluator implementation.
2. Implement read-only evaluation with immutable input hashes, strict/ambiguity-aware scoring, operation mapping, and aggregate strata.
3. Verify synthetic tests, freeze manifest/checkpoint identity, and run the held-out evaluation once to a new report directory.
4. Review metrics and claims with a fresh Astra Low agent, fix only reporting or implementation defects, verify, and commit Phase 4.
