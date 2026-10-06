# Canonical domain service plan

1. Write synthetic and canonical-data tests for route ordering, membership, fare provenance, nearest geometric distance, provisional schedules, and unavailable ticket/accessibility/realtime data.
2. Implement a parameterized read-only SQLite `DomainService`, one explicit handler per T3 operation. Avoid route claims from unconfirmed transfers or mismatched route/stop modes.
3. Run focused and repository tests, request fresh Astra Low review, fix valid findings, verify, and commit Phase 5.
