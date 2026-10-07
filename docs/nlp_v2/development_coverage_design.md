# Development-only assistant coverage design

Purpose: improve legitimate answer coverage for Chennai commuters across the 16
frozen T3 intents, without tuning on observed stress/reference examples. Primary
agent implements; fresh GPT-6.1 Sol xhigh reviews each phase, as requested.

## Scope and choices

Use a reviewed, versioned JSON suite authored from T3 contracts and canonical
entities with expected behavior independent of present implementation. Do not
mine train/validation outcomes or held-out outcomes to choose easy cases. Five
language classes per intent establish breadth; supplementary contrasts cover
missing inputs, duplicate entities, bare times, neutral relative days, unknown
routes, unsupported sources, combined-mode/date/time constraint preservation,
place endpoints, exact-stop anchors and bounded noise. This is a diagnostic development
instrument, not an untouched generalization estimate or factual benchmark.

A real-model run exercises the production assistant. A separate gold-intent run
injects the annotated intent via the existing classifier interface and exercises
real extraction, resolution, policy and canonical service. Its scores are marked
as downstream diagnostics and never described as classifier performance.
Choosing only stub inference would hide classifier errors; choosing only real
inference would obscure the causes of downstream failures. No weights or model
preprocessing change in Phase 12.

## Suite contract

Each case records id, new query, language, noise, scenario, provenance/rationale,
expected intent, expected operation, expected status, optional clarification
reason, gold slot subset, and optional expected evidence kind. Missing-slot cases
may require named missing slots; ambiguity cases require candidates without
assuming an arbitrary winner. Source-backed OK cases require provenance and
provisional scope. Exact response wording and unverified fare amounts are not
gold. Use a fixed Chennai reference date 2026-10-07.

Version v1 is immutable after the phase review: manifest records suite SHA-256,
DB SHA-256, authoring sources and limitations. Loader refuses drift. Future
suite versions must retain old scores and explicitly document changes.

## Evaluation contract

Report count and denominator for intent, selected operation, gold-slot resolution,
terminal contract accuracy (status plus gold clarification reason and operation
where executable), evidence contract, missing-slot and candidate checks. Rates:
clarification, false-positive clarification over non-clarification gold,
unavailable, OK, and per-intent/status/language/noise breakdowns. Gold-slot
accuracy counts annotated slot checks, with case-level success separately.
Answerable terminal coverage requires gold OK, actual OK and the expected
operation, gold slots and evidence. An increased OK count alone is not success.

Aggregate scores are saved under new report paths. Development case diagnostics
may list dev case ids, failure categories, and actual contracts; no held-out
rows are exposed. Record Git revision plus dirty state, source hashes, suite/DB/
model hashes, run mode and fixed date. Reject nonempty output directories before
loading the model and do not write into historical asset directories.

## Leakage guard and verification

Use an isolated function to compute normalized query fingerprints from frozen
stress CSV and reference JSON without returning text, IDs or labels. Compare
suite fingerprints, return only overlap count, and fail on any overlap. Protect
it with synthetic files; do not print or inspect the frozen records. This checks
exact normalized overlap, not semantic independence. Authorship record and fresh
review address provenance; no process can prove unseen semantic independence
from an observed benchmark.

TDD covers scoring wrong operation/status/slots/provenance, reason and missing
slot mismatches, malformed suites, drift, overlap, and output guards. Actual
model baseline and downstream baseline are measured only after the suite is
fixed for review. Full tests and phase review gate commit and push.
