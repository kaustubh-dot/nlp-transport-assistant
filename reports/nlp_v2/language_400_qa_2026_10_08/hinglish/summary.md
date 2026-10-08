# Hinglish 200 custom-query baseline assessment

All 200 new queries were authored and fixed before API prediction, with 12 examples for each of the 16 T3 families and eight competing-scope/multiple-goal guards. Exact uniqueness checks found zero overlaps against either prior 48-query language baseline. Public contract/taxonomy/answerability documents informed expected intent, operation and only explicit unambiguous slot subsets. No individual frozen/development/held-out corpus examples were inspected. No factual fare amounts, departure times, membership flags, nearest-stop names or facility values were invented as expected values.

Root captured all 200 through the real API as part of the coordinated 400-query baseline. This agent made zero API/model/evaluator calls and no production/model/database edits. Every baseline response was manually read and assessed using the uniform rubric, including query negation, goal cardinality, location roles, supplied stage/route/clock inputs, status, source explanation, structured data and entity/intent candidates. `assessment.json` contains all 200 individual judgments; `assessment_counts.json` contains aggregates.

| Category | Count | Interpretation |
|---|---:|---|
| `goal_correct` | 10 | Eight grounded bounded answers plus two correct domain rejections |
| `safe_limitation` | 70 | Goal family recognized, but unavailable source/scope or disclosed partial topology prevents full fulfillment |
| `legitimate_clarification` | 19 | Genuine missing input, canonical ambiguity or competing explicit scope |
| `recognition_failure` | 99 | Wrong family, missed clearly supplied input, negation failure, false ambiguity/multiple scope, or a dropped goal |
| `unsafe_or_wrong_answer` | 1 | An OK answer silently returns a different timetable scope |
| `needs_review` | 1 | Locality implicitly anchored to a physical stop, then returns that stop at zero distance |

The API produced 14 OK replies. Their manual dispositions are eight goal-correct, two disclosed partial-list limitations, two wrong-family route-list answers, one wrong timetable answer and one anchor needing review. There are 127 matching-family replies among the 192 single-family cases, but family match alone does not establish input preservation or goal fulfillment. These deliberately broad colloquial custom queries describe product behavior, not a representative language accuracy estimate or a frozen benchmark result.

Matched-family blanket source preflight refusals remain `safe_limitation`, including those that skip extraction. They are never counted as goal fulfillment. Secondary endpoint/time/constraint omissions are recorded explicitly where exposed. Clear already-supplied inputs that are requested again under clarification remain recognition failures. Wrong-family source refusals also remain recognition failures.

Representative observed behavior:

- HG200_050 asks the last **25R** bus from Poonamallee Bus Terminus. The OK reply selects scheduled departures, omits 25R and last-service scope, and returns 597A/66P midnight departures. This is the unsafe/wrong answer, despite a published-schedule caveat.
- HG200_076 asks metro departures after **shaam 6:20**. A correct-family metro-source refusal is safe, but returned time is **06:20**, not **18:20**. This secondary time defect is not hidden in the source-limitation count.
- HG200_098/099/102 clearly supply **11 stages**, **8 stage**, and **६ stage** respectively, yet the assistant asks for stage. These are recognition failures, not legitimate missing-input prompts.
- HG200_012/096 treat excluded bus as a requested mode; HG200_059 treats negated live wording as a live-status goal; HG200_143/155 select the explicitly negated parking/fare goal.
- HG200_170/171/172/174 select static first/last or frequency families for current delay/crowd/arrival/disruption. Safe static-source refusals do not establish live-goal recognition.
- HG200_197/199 drop route or live-location goals from explicit paired requests. HG200_198 correctly retains parking plus lift as two candidate families and clarifies.
- HG200_073 correctly preserves morning 07:15 and reports source-qualified departures. HG200_097/100/107 preserve requested stage/class and disclose recorded source/effective date; HG200_107 visibly discloses the Ordinary default.
- HG200_168 returns Thiruvanmiyur bus stop itself at 0 m after implicitly using it as the reference for the broader Thiruvanmiyur place. This remains `needs_review`; no guessed locality-coordinate oracle is used.

Oracle review retained the original cases unchanged. Out-of-scope cases request concrete non-CMA/non-transit goals (food/hotel/cab/flight/private intercity booking, weather, cinema, housing, cricket, computer repair or Mumbai pass rules), even where transit entities appear. An ATM **inside High Court metro** (HG200_124) is an in-domain facility goal with unsupported source; it is not out of scope. HG200_141 asks generic lift status without explicit current malfunction, so accessibility is the authored family. HG200_046 deliberately says the membership stop was not named; returning a full route sequence does not satisfy that scoped missing-input request, though its colloquial "kisi stop" wording is a possible boundary for further independent review. First plus last bounds (HG200_053) belong to one operation, whereas route plus fare and parking plus lift belong to separate families. HG200_080 has true CMBT physical ambiguity, so the stop clarification is legitimate; invalid 26:75 handling remains explicitly unverified behind it rather than claimed successful.

Baseline cases SHA-256: `91bcb569710063ef9e018e7dfc519486b0cb2a2d406483908776e72250c7da8c`. Baseline responses SHA-256 remains `5537a88b7ef7a5be2ecdb59a8b0f165b16b423793ca12aa8959ca59514afc956`. The coordinated baseline manifest records source commit `3336e0d4ed0f84ddc706bf14cbf1aaa1e5c33a4c`. Read-only source tracing and general recommendations are in `root_causes.md`; no fixes or inference re-runs accompanied this assessment.
