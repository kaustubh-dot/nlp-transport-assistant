# Phase 20 whole-system QA and backend freeze

Full verification: **602 tests passed in 15.61 seconds**, compilation passed,
`pip check` reported no broken requirements, and `git diff --check` passed.
Tests run sequentially because prototype tests share a mutable fixture database.
Production canonical SQLite connections remain read-only.

Whole-project review covered the runtime, API/frontend schema, model loader and
artifact provenance, trainer, evaluators, documentation and frozen boundaries.
Four medium constraint-loss findings were reproduced with synthetic contract
tests, then fixed and re-reviewed. Scope cardinality includes numeric routes,
line names, stops, stages, clocks, ISO dates and recognized relative days.
Unknown explicit waypoints and rejected route suffixes become missing execution
inputs rather than widening routing/timetable requests. Before-time/range
semantics are refused; published departures retain at/after semantics.
Temporal numbers cannot become route codes. Metadata stays separate from frozen
canonical slot schemas and raw model preprocessing.

The final development reports lock current source hashes and retain 93/120
terminal contracts, 42/50 answerable cases and 3/104 false-positive
clarifications. Intended-intent diagnostics retain 119/120 terminal contracts,
50/50 answerable and zero false-positive clarifications; the sole policy/gold
divergence is unchanged. These observed contracts are not generalization or
independent transport-fact estimates.

Real selected-model local HTTP checks exercised source-backed fare, multi-scope
clarification, unsupported before-time scope, development realtime refusal,
out-of-scope and malformed request. Malformed requests return HTTP 422; health
reports T3. Public replies contain no raw/normalized query, confidence or
exception/traceback fields. Some other synthetic live/out-of-scope phrasings are
misclassified by the retained model; contract checks do not imply broad model
perfection.

No recognized secret prefixes, tracked model weights, cache/environment files,
or frozen research changes were found. Dev v1 normalized held-out overlap is
zero by opaque fingerprints; this is not a semantic-independence claim.

| Preserved asset | SHA-256 |
|---|---|
| Development v1 | `0de0ce7de1ca933b70321bf15c0d9bbc2d7db0dc694cd046064d28104988ea41` |
| Canonical DB | `583fd400bb3ee0d5af312e03ec78116de88ce162d6c33c2b87fd93df4da48791` |
| Selected manifest | `447a120090c33ba1259cad06ce9f216d80832d2540727c3330f14be3ec04dc39` |
| Selected checkpoint | `abac66fc9fa29212c7565117ae326e34f02b64e76dbb177c61e9661517803196` |

The Phase 20 commit is the new source freeze. Phase 21 runs the existing
evaluators once into new paths as **post-development descriptive regression
evaluation**, inspecting aggregates only and matching historical reference date
2026-10-06. No backend/model/prompt tuning follows that evaluation. Phase 22 may
change presentation only; the API, backend, model, canonical DB and evaluators
stay fixed. Old reports remain preserved.
