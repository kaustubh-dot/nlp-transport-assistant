# Phase 15 operational response policy

Keep five public statuses and sixteen frozen T3 operations. Add a derived public
`outcome_reason` describing semantic/temporal/entity ambiguity, multiple goals,
missing execution input, unsupported source, external/realtime source, malformed
request, temporary failure, answered or out-of-scope behavior. Retain existing
`clarification_reason`, missing slot IDs and canonical candidates for compatibility.
Operation-specific `data.reason` remains available as finer detail.

Only actionable missing information prompts a revision. Map required slot groups
to readable questions: starting stop, destination, route/line, boarding stop,
fare stage or endpoints, nearby anchor, and single transport mode. A frequency
operation with several directions can ask for a destination because its actual
schedule filter uses that destination; once supplied, residual source ambiguity
stays unavailable. Unsupported capabilities continue to refuse without irrelevant
questions. Realtime requests remain unavailable, never ambiguous.

Punctuation-only/empty requests are malformed errors before inference. Invalid
service result messages must become safe temporary errors, preserving known
intent/operation. Direct dispatch must handle the same ambiguous relative days
as extraction (`kal` and `parso`). Explicit first/last clock scope is unavailable
because the slot does not distinguish before/after/at semantics; do not silently
ignore it. This is a contract integrity fix, not taxonomy/model tuning.

No frontend polish or model changes, frozen suite edits, DB writes, held-out
inspection or historical evaluation. API adds a backwards-compatible string field;
frontend validation accepts known optional reason codes and rejects malformed ones.

Mode-specific source capability is checked through optional
`preflight_mode(operation, mode) -> ServiceResult | None` after extraction and the
multiple-mode choice, before entity/missing questions. Base canonical handlers
query read-only operational route records and mode-consistent topology or schedule
rows. No usable rows means unsupported snapshot source, never proof that actual
transport does not exist. An overridden execution/handler/map bypasses base
assumptions; malformed/throwing preflight becomes a safe known-operation error.
The unchanged standalone `dispatch` accepts already structured slots and enforces
its own execution requirements; source preflight is an assistant orchestration
policy. Direct canonical execute retains conservative unavailable behavior.
