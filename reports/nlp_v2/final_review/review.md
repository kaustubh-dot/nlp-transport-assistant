# Phase23 review history and final acceptance

## First independent review — acceptance withheld at that time

Fresh reviewer: **GPT-6.1 Sol, xhigh reasoning**. Result: **0 critical, 0 high,
1 medium unresolved**. Two low documentation findings were corrected after
review: completed Phase21 tense and disclosure of the existing Ordinary fare
default. Current desktop/mobile visual QA subsequently passed. The frontend reviewer
inspected all eight screenshots and granted final Phase22 signoff with zero
unresolved findings; Phase22 committed/pushed as `b0b3139`.

## Medium: timetable location constraints silently lost

The shared extraction branch at
[`src/nlp_v2/slots.py`](../../../src/nlp_v2/slots.py) selects first/last recognized
locations for scheduled departures, first/last service and frequency without a
timetable location-cardinality guard or explicit waypoint handling.

Reviewer reproduction using the real selected checkpoint:

> What are the scheduled departures from Island ground Terminus to Poonamallee Bus Terminus and Annasquare?

Result: `scheduled_departure`, `ok`, five departures; station `BUS_11159`,
destination `BUS_11192`. Poonamallee `BUS_5821` is silently omitted.

Primary independent intended-intent synthetic contract probes:

| Query | Observed status | Extracted station / destination | Lost scope |
|---|---|---|---|
| Show bus departures from Island ground Terminus to Poonamallee Bus Terminus and Annasquare | ok, 5 departures | BUS_11159 / BUS_11192 | Poonamallee omitted |
| Show bus departures from Island ground Terminus to Annasquare via Poonamallee Bus Terminus | unavailable | BUS_11159 / BUS_5821 | Annasquare replaced by waypoint |

These are new synthetic canonical contract examples, not held-out failures.
No historical queries, labels or individual evaluation outcomes were inspected.

## Scoped proposal requiring governance authorization

1. Add synthetic red regressions for all three timetable intents, covering
   three-location coordination, an explicit known/unknown waypoint, and normal
   one/two-location requests.
2. Prevent dispatch when extra locations would be dropped. Use the existing
   multiple-scope clarification and source-capability refusal paths; refuse
   unsupported timetable waypoints without replacing the destination. Preserve
   raw inference, taxonomy, canonical slot schema, model, source evidence and caps.
3. Run focused and full verification; obtain fresh Sol xhigh review of the
   scoped change and commit a new backend freeze.
4. Preserve the valid Phase21 run and reports unchanged. Only with explicit user
   authorization, run a separately labeled descriptive regression iteration
   after the new freeze; inspect aggregates only and do no subsequent tuning.
5. Complete final review and focused commits/push; current visual QA has passed.

At this first review, no behavioral patch or evaluator rerun had been made. The user's Phase21 rule,
“Otherwise, evaluation ends development,” blocked implementing this proposal at that time
without a governance decision. This defect does not invalidate the completed run.

## Independent verification

443 focused tests passed in 7.42 seconds; strict selected-model startup succeeded.
Source/report/DB/development/provenance hashes match the freeze except the allowed
Streamlit presentation change. Frozen research diff is empty; links resolve; no
tracked checkpoint, cache or environment artifacts were found. Passing tests and
documentation disclosure do not resolve the runtime defect or grant final signoff.

## Explicit authorization and scoped review closure

The user explicitly authorized the strict timetable correction, new source freeze
and exactly one separately labeled descriptive assistant run. Phase21 remains a
valid historical result, never invalidated, rewritten or replaced. The original
medium was corrected only in slots.py/assistant.py with 66 synthetic regressions;
[the scoped review](timetable_scope_review.md) records observed reds, 454 focused
passes, 677 full passes and a fresh GPT-6.1 Sol xhigh signoff with zero unresolved
critical/high/medium/low. The reviewer’s low old-extractor metadata compatibility
finding was also reproduced and resolved within the new metadata seam.

Behavioral commit/post-review backend freeze: `e008c0474c1301a3b442b31761f31c79e7dec446`.
No evaluation outputs were combined with that commit. The unchanged complete-
assistant evaluator runs once at reference date2026-10-06 in the new
[Phase23 post-fix descriptive directory](../phase23_post_fix_descriptive/comparison.md).
No model-only rerun or item-level inspection occurs; no tuning follows.

The post-fix measurement completed once. The fresh final whole-project review
withheld signoff because of the residual medium below.

## Final source/runtime and integrity checks

Fresh primary compileall, pip check and diff check pass. The frozen research Git
boundary is empty; the Phase21 directory diff against its fa4aaf7 commit is empty.
All five recorded Phase21 report hashes and its context bytes are preserved.
Phase23 source/output hashes match its context. Selected artifact validation
checks exact950358409 bytes/SHA, raw64/pinned MuRIL and16 labels. The frozen
canonical DB, model manifest and development suite hashes remain unchanged.
No tracked checkpoint/environment/cache/bytecode artifacts were found. A bounded
recognized AWS/GitHub/OpenAI key-prefix/private-key-header scan over current
tracked/untracked files below10MB found no matches; this is pattern evidence,
not an exhaustive credential guarantee. Final document links resolve.

The task-owned localhost API8875 was refreshed to the final frozen source for
the user's open restored-style UI8601. Real HTTP health reports T3. The original
review's three-stop departure request now clarifies with multiple_goals; an
explicit synthetic scheduled-departures request with a trailing waypoint returns
unavailable/timetable_waypoint_scope_unsupported, retaining stationBUS_11159 and
destinationBUS_11192 rather than replacing the destination. The existing Deluxe
stage4 fare demo still returns OK with source/effective metadata. The selected
classifier can still route shorter paraphrases to other intents; intended-intent
fixture tests remain separate from real-model capability evidence. No classifier
changes or tuning followed this observation. Both localhost demo services remain
available for the open UI; temporary QA tabs and viewports were cleared.

## Fresh final whole-project review — one residual medium

Fresh **GPT-6.1 Sol xhigh** final review: **0 critical, 0 high, 1 medium,
0 low unresolved**. Independently full677 passed18.06s; compile/pip/diff, strict
model loading, frozen research/input/source/report hashes and UI renderer parity
passed. Phase21 remains unchanged; Phase23 aggregate JSON differs from Phase21
only by freeze SHA. No other material finding was identified.

The timetable guard at slots.py432–436 counts recognized canonical spans only.
A new synthetic real-model query, “What are the scheduled departures from Island
ground Terminus to Annasquare and Unlisted Cedar Terminal?”, still returns
scheduled_departure / GET_SCHEDULED_DEPARTURES / OK and five departures for
BUS_11159→BUS_11192. The explicitly coordinated unknown third stop is lost; the
two-stop control returns identical departures. Unknown via correctly refuses.
This belongs to the authorized third-stop invariant, not an unrelated alias issue.
The primary independently reproduced three fixture-only intended-intent red
cases for all timetable intents: each incorrectly returns OK rather than
clarification. These temporary tests do not alter the production source or
repository test suite. No held-out individual queries/failures were inspected.

Concrete follow-up scope: add the unknown-coordinated-third-stop regressions to
the existing synthetic fixture suite, with mixed/noisy coordination and ordinary
first-and-last/time/date/conjunction controls. Add only a timetable syntactic
scope guard before canonical matching discards extra endpoint text. Decline
unrepresentable coordinated endpoint scopes; add no aliases or fuzzy selection,
model/domain/schema/general extraction changes. Verify focused/full suites and
fresh scoped/final Sol xhigh reviews; commit a separate follow-up backend freeze.

This review occurred after the user's exactly-one post-fix descriptive run had
already completed. Both valid Phase21 and Phase23 measurements must remain
unchanged for their recorded freezes. The exact-one/no-following-tuning governance
needs an explicit decision before a further behavioral freeze or evaluation.
The concrete recommended exception is the narrow residual correctness repair
and one additional separately labeled descriptive run, preserving both earlier
runs, inspecting aggregates only and doing no subsequent tuning. Alternatively,
authorize the correction with no further evaluation and disclose that the final
source has no matching aggregate measurement. No such further action has occurred.
Project implementation is **not COMPLETE** while this medium remains unresolved.
