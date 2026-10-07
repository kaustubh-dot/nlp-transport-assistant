# Phase23 unknown-stop follow-up — pre-freeze correctness gate

After the single Phase23 descriptive run, the fresh whole-project review found
one residual medium: unknown coordinated stop text was not counted as a canonical
span and could disappear from timetable execution. The user subsequently
instructed “Fix it.” This authorizes the narrow residual correctness repair.
Both completed descriptive evaluations remain unchanged, including contexts.
No additional evaluator invocation is authorized or performed. Neither historical
report measures this final follow-up source; separate provenance records it.

## Correction and boundaries

Only `src/nlp_v2/slots.py` changes production behavior since `0501fab`.
The timetable branch masks recognized canonical names, retaining their ordered
spans and punctuation/conjunctions inside names. It preserves list punctuation
outside names and checks complete coordinated components and repeated endpoint
roles before domain execution. An unresolved extra location returns the existing
multiple-scope clarification rather than executing the recognized subset.
Complete time/date/route/mode/courtesy clauses and first/last service modifiers
remain ordinary inputs. Atomic complete-component matching prevents numeric
prefixes from causing exponential backtracking; its internal token boundary
still permits complete ISO dates instead of prematurely selecting clock prefixes.

No unknown name is resolved and no aliases are added. No model, inference,
canonical schema/data, domain handler, public reply contract or non-timetable
extraction branch changes. Explicit waypoint refusal remains unchanged.
This is bounded timetable syntax, not a claim of arbitrary language parsing.

## Synthetic red/green evidence

The existing fresh four-stop SQLite fixture gains **201 cases**: 84 unknown
location structures, 114 compatibility/temporal controls and three bounded
whole-assistant numeric-tail regressions across all three timetable intents.
The unknown cases cover ordering, source/destination coordination, repeated
roles, single-token names, Hindi/Roman/noisy inputs, list punctuation and extra
stops after modifiers. Controls cover first/last grammar, clocks/dates/routes,
ordinary one/two stops and fixture-only aliases containing conjunctions/commas.
No held-out query, label or individual failure is inspected or copied.

Temporarily restoring committed `e008c047` produced **87 expected failures,
114 passing controls, 66 deselected in 9.18s**; corrected source was restored
in `finally`. Initial guard drafts introduced modifier/first-last/temporal
compatibility regressions, each reproduced before correction. The reviewer also
found numeric backtracking: three subprocess tests timed out at three seconds
before the atomic correction; all now clarify without domain execution.
No draft was committed or evaluated.

Primary final timetable verification: **267 passed in 11.86s**.
Primary complete repository verification: **878 passed in 32.49s** (677 prior
cases plus 201 follow-up cases). Focused timetable/slot/entity/domain/assistant/
policy/dispatch/multilingual/API/frontend verification: **663 passed in 17.25s**.
Compileall, pip check and diff check pass. The selected artifact validator checks
unchanged 950358409 bytes/SHA, 16 labels, raw64 and pinned MuRIL revision.
Research Git diff is empty. Canonical DB, model manifest and development suite
hashes match. Both historical report directories and contexts remain byte-for-byte
unchanged; recorded report hashes verify. No evaluator or training run occurs.

## Fresh independent scoped review

Fresh **GPT-6.1 Sol, xhigh** reviewed the actual diff, contracts, authorization,
red evidence and frozen boundaries. All introduced compatibility/performance
findings were corrected and re-reviewed. Independent **267 timetable tests pass
in 12.18s**, plus **300 synthetic compatibility, scope and latency probes**.
3074-character numeric unknown tails clarify without execution in approximately
0.003s across all three intents. Diff and historical-preservation checks pass.
Final scoped signoff: **0 critical, 0 high, 0 medium, 0 low unresolved**.

The behavioral correction is committed separately after verification. Its full
freeze SHA and final whole-project review are recorded in the separate final
source context. The valid measurements remain historical for `8ee8917` and
`e008c047`; final corrected-source aggregate performance has not been remeasured.
