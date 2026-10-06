# T3 assistant orchestration plan

1. Write contract tests for dependency-injected classifier, extractor, service, ambiguity, missing slots, unavailable, out-of-scope, and representative English/Hindi/Roman/mixed/noisy synthetic queries.
2. Implement one production `T3Assistant.process_query` path and structured response formatting, preserving raw-query model inference and canonical IDs.
3. Verify with the real local checkpoint on a synthetic query, run focused/full tests, request fresh Astra Low review, fix, verify, and commit Phase 6.
