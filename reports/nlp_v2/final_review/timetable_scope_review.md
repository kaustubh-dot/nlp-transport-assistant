# Authorized Phase23 timetable correction — pre-freeze gate

The user explicitly authorized a bounded exception on October7 after the first
independent whole-project review found a medium timetable scope-loss defect.
This is implementation correctness work based on new synthetic contracts, not
held-out failure inspection or metric tuning. Phase21 remains valid and unchanged.

## Correction and boundary

Only `src/nlp_v2/slots.py` and `src/nlp_v2/assistant.py` change production behavior.
For all three timetable intents, explicit origin/destination roles are retained
independently of waypoint mention order; recognized spans retain their original
order. Route, time, date and mode extraction remain intact. The canonical
operation contract has no executable waypoint filter, so waypoint requests
return explicit unavailable without domain execution. Three-location requests
and conflicting endpoint roles clarify instead of executing a partial scope.
Ordinary one/two-point extraction stays unchanged. No aliases, schema, domain,
classifier, inference preprocessing, labels, model, research or data changes.
The new metadata field defaults false; old injected extractor result shapes
remain compatible through an optional `getattr` read.

## Synthetic red/green evidence

`tests/test_t3_timetable_scope.py` uses a fresh four-stop SQLite fixture, English
and Hindi fixture-only names and an injected classifier. No historical query or
label is copied. The initial 63 cases cover waypoint ordering/unknown/multiple
waypoints, third stops, explicit conflicting endpoint roles, normalization,
Hindi/Roman/noisy inputs, retained route/time/date and ordinary controls across
all three timetable operations. Restoring the frozen implementation temporarily
produced **51 failures and 12 passes**; the patch was restored immediately.
Three additional old-metadata extension cases failed with `error` before the
reviewer's compatibility correction. The final 66 synthetic cases pass.

Focused slot/entity/domain/assistant/policy/dispatch/multilingual/API/frontend
verification: **454 passed in 7.89s**. Complete repository verification: **677 passed in 18.12s** (611 baseline plus
66 new regressions).
Compileall over src/nlp_v2, app and scripts/nlp_v2, pip check and diff check pass.
Research Git boundary and Phase21 report diff are empty. All five recorded
Phase21 report hashes, canonical DB and selected manifest hashes match; artifact
validator verifies the unchanged 950358409-byte checkpoint SHA, 16-label T3,
raw_query/max64 and pinned MuRIL revision. No model-only evaluator is rerun.

## Independent scoped review

Fresh GPT-6.1 Sol, xhigh, reviewed the authorization, synthetic tests, production
diff, contracts and frozen boundaries. Independent 39 synthetic assistant/API/
frontend probes and 27 ordinary extraction comparisons against frozen8ee8917
passed. Positional dataclass compatibility passed. The sole low custom-extractor
metadata compatibility finding was reproduced and corrected with three synthetic
regressions; the updated final signoff is **0 critical, 0 high, 0 medium, 0 low unresolved**.
The reviewer independently verified three previous-metadata extension cases and
three waypoint refusal controls after the compatibility fix.
No reviewer or primary inspected individual held-out queries/labels/failures.

The separate behavioral commit is the post-review Phase23 backend freeze. Only
after that commit may the existing complete-assistant evaluator run exactly once,
with reference date2026-10-06 in a new Phase23 post-fix descriptive directory.
Evaluation outputs are excluded from this commit; no metric-driven tuning follows.
