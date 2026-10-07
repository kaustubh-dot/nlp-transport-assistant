# Authorized Phase23 timetable scope correction

**Goal:** prevent timetable extraction from silently discarding stops or replacing
the destination with a waypoint. User explicitly authorized this exception in
the attached October7 request; Phase21 remains valid and immutable.

**Scope:** shared timetable branch in `src/nlp_v2/slots.py`, extraction uncertainty
metadata and its refusal in `src/nlp_v2/assistant.py`. No classifier, alias,
taxonomy, canonical schema/data or unrelated domain changes. Timetable contracts
have one boarding station and optional destination; they cannot execute waypoint
filters. Preserve explicit endpoint roles when unambiguous and decline unsupported
waypoint structures. Extra unrepresentable locations clarify before execution.

- [x] Add new synthetic SQLite-backed regressions for all three timetable intents:
  waypoint before/after destination, unknown/multiple waypoints, third stop,
  normalized/reordered/Hindi/mixed-script scope, route/time/date retention,
  ordinary one/two-stop behavior and explicit non-execution of unsupported scopes.
- [x] Observe behavioral reds on the frozen implementation, then make the minimal
  structured extraction correction and explicit unsupported refusal.
- [x] Run new regressions plus slot/entity/domain/assistant/API/frontend tests;
  then full suite, compileall/pip/diff and frozen/report/asset checks.
- [x] Fresh GPT-6.1 Sol xhigh scoped review; resolve all critical/high/medium.
- [x] Commit fix separately and record exact full post-review backend freeze SHA.
- [x] Preserve Phase21 unchanged. Run assistant evaluator exactly once after
  freeze with fixed reference date2026-10-06 into a NEW Phase23 post-fix descriptive
  directory. No model-only rerun, individual held-out inspection or metric tuning.
- [ ] Record hashes, aggregate metrics/strata and Phase21 comparison, update docs
  to disclose the authorized sequence, obtain fresh final whole-project review.
- [ ] Final verification, focused documentation/report commit/push, clean main,
  retain the refreshed localhost demo for the user's open UI, complete the original objective. No new phase.

The user's separate original-style UI restoration is reviewed and committed as
`7cac770` before this correction. Final frontend semantics remain T3/API backed.

Fresh final review and independent677-pass verification completed; signoff is
withheld for one medium unknown-coordinated-third-stop gap. Both descriptive
runs remain valid unchanged. No further production/evaluation changes occur
before reconciling the user's exactly-one/no-following-tuning restriction. The
concrete follow-up proposal is in reports/nlp_v2/final_review/review.md.
