# Supported scope and remaining limitations

“Supported” describes an operation with the required canonical evidence and
unambiguous execution inputs. It does not mean the retained classifier always
selects it correctly, or that a published snapshot confirms travel conditions
today. The backend's English response templates accept bounded English/Hindi/Roman/Hinglish/
mixed-script inputs. The frontend English / हिंदी / Hinglish selector localizes
curated replies and main website text while preserving factual values and raw
questions. Unknown explanations and some built-in Streamlit controls remain
English. Broad transliteration, spelling repair and context memory
are not implemented. Each clarification resubmits a complete question.

Fresh [Hindi/Hinglish product QA](../../reports/nlp_v2/language_toggle_qa_2026_10_08/summary.md)
confirms incomplete language understanding: some Hindi number/name forms miss
supplied inputs, and some conversational Hinglish frequency, delay and unrelated
questions select the wrong family. Source-unavailable and legitimate ambiguity
responses are recorded separately. These 96 manually scoped questions are not a
representative accuracy estimate; no model/alias/DB change or evaluator run
accompanied the frontend language extension.

The subsequent user-requested [400-question challenge QA](../../reports/nlp_v2/language_400_qa_2026_10_08/summary.md)
uses 200 fresh Hindi and 200 fresh Hinglish questions. Final manual review records
22 completed bounded published-data goals, 162 correct source/scope limitations,
38 legitimate clarifications, 175 recognition failures and 3 cases needing
source/anchor review. These deliberately varied observed development cases are
not a representative or independent accuracy estimate. Passing software tests
and matching localized browser replies do not mean the language goal succeeds.

Bounded fixes cover Unicode word boundaries, Hindi bus inflections and local/
suburban rail phrases, route labels/possessive suffixes, native/spelled fare
stages, explicit day periods, Night service and unknown service classes. Guards
clarify selected goals that the question explicitly excludes and independently
requested stop-list/live goals. They do not reroute model predictions. Positive
and negated mode/count combinations, native station names, conversational intent
recognition and unqualified locality/campus anchors still have failures.

Bus/Metro/Rail (suburban)/MRTS controls provide a separate default input for
questions without an explicit mode. They do not change raw classifier text or
improve the frozen intent model. Any mode clears that default. A combined route
or interchange still needs its actual mode pair; a single default cannot supply
it. Published records opens the coverage panel. All factual outputs retain
source/date/straight-line and current-operation qualifications.

## Fully supported within the stated scope

- **Nearest transport:** straight-line distance from exact canonical stop/hub/
  place coordinates to located transport stops, preserving a single requested
  mode. Pedestrian access, walking routes and current operation are unverified.
- **Product refusal/clarification:** structured out-of-scope, missing input,
  canonical ambiguity, temporal ambiguity, multiple scopes, unsupported source,
  external realtime requirement, malformed input and temporary failure. The five
  public statuses and `outcome_reason` remain separate from classifier confidence.
  This is a contract capability, not perfect intent recognition.

## Partially supported from published records

| Capability | Bounded answer | Limit |
|---|---|---|
| Bus routes / availability | Positive ordered stop-sequence connectivity | No current/dated trip availability, optimization, verified transfer or negative connectivity inference |
| Bus route stops | Mode-consistent published sequences and omitted-link/variant counts | Partial topology is disclosed; unusable links are not repaired or guessed |
| Route membership | Positive sourced membership; negative only with complete consistent candidate variants | Incomplete topology cannot prove a stop absent |
| First / last bus service | Published calendar and service-day departure bounds | No valid metro timetable; clock-constrained bounds are refused |
| Bus departures | Up to five published departures at/after one explicit clock, with supported calendar/destination filters | Before/range and multiple-time requests are refused/clarified; no live predictions |
| Bus frequency | Median interval for one route/direction/physical-stop schedule group | No mixed-direction averaging or live frequency |
| Fares | Dated metro station-pair token records, or explicit bus fare stage with requested service class; omitted class defaults to Ordinary and is disclosed | No bus OD stage arithmetic, unknown class substitution, unverified discount/concession/pass rules or AC tariff substitution |

Fare records and timetables retain their recorded sources/effective dates and
provisional caveats. The demo’s Deluxe stage-4 INR 17 record is effective
2018-01-29; it is not a current-price guarantee. Journey extraction preserves
known waypoints and requests missing unknown waypoints; unsupported route suffixes
remain execution constraints. Bounded guards cover coordinated route/line/stage/
clock/day scopes and specific journey, membership and nearest-location cases.
Exact aliases preserve duplicate physical nodes instead of guessing one.

## Timetable scope correction and supported boundary

The first Phase23 independent review found a real medium defect: three explicit
stops could lose the middle stop, and a waypoint could replace the destination.
Under an explicit user-authorized correctness exception, synthetic regressions
now prove endpoint role/order preservation and retained route/time/date inputs
across all three timetable intents. Extra/conflicting locations clarify; explicit
waypoints return unavailable before domain execution because the canonical
operation contract cannot filter them. Known spans remain ordered extraction
metadata. Ordinary one/two-point behavior remains unchanged. This is bounded
parsing for supported canonical names and via/Hindi/Roman markers, not general
natural-language understanding. See [the scoped review](../../reports/nlp_v2/final_review/timetable_scope_review.md).

Phase21 remains valid for freeze8ee8917 and every report is preserved unchanged.
The separate post-review freeze is `e008c0474c1301a3b442b31761f31c79e7dec446`.
The correction is synthetic-contract driven; no held-out item inspection,
alias/domain/model changes or general clarification development occurred.

## Unknown-stop follow-up and remaining parsing limit

The fresh final review after the single post-fix run found that unknown coordinated
third-stop text could disappear because only canonical spans were counted.
The user subsequently instructed “Fix it.” The narrow follow-up is frozen at
`1bf748c9e4cc35e75b1db004f5b74c9dad1eeb1b` and adds 201 synthetic regressions. It clarifies unresolved extra
location scopes before execution, preserving canonical names with punctuation
and complete supported timetable parameter/courtesy clauses. Numeric modifier
matching avoids exponential backtracking. The fresh scoped Sol xhigh review has
zero unresolved findings; full878 tests pass. See [follow-up evidence](../../reports/nlp_v2/final_review/unknown_stop_scope_review.md).

This is bounded parsing for canonical aliases and supported coordination/endpoint
syntax. It does not resolve arbitrary unknown names or prove all possible grammar
forms. Classifier/source limitations below remain. Both earlier evaluations and
contexts are preserved unchanged. Final corrected-source aggregate performance
has not been remeasured; no additional evaluator was invoked. Historical metrics
must not be attributed to this freeze. [Final source context](../../reports/nlp_v2/final_review/final_source_context.json)
records that distinction and the reviewed source hashes.

## Unsupported or requiring external verification

- Verified multimodal journey and interchange planning: all 45 interchange rows
  are unconfirmed; hub membership/walking candidates do not establish a graph.
- Verified accessibility/facility facts: accessibility availability fields are
  null and authoritative facility values are absent.
- Ticket/pass policy, eligibility and discounts: no authoritative policy source.
- Live GPS, delays, crowd levels or predicted arrivals: no authorized external
  telemetry source. Static connectivity never becomes a live assertion.
- Mode-consistent metro topology/timetables: corrupted cross-mode links are
  excluded; the snapshot cannot support those route/schedule answers.

## Model and evaluation limitations

The existing selected T3 MuRIL checkpoint remains after one full GPU candidate
failed the validation-only promotion gate (0.84658 versus existing 0.85122
disjoint-validation Macro-F1). No adaptive retry or historical selection followed.
Observed development raw accuracy is 92/118 single-label cases; classification
is still a bottleneck. Intended-intent downstream 50/50 answerable contracts is
conditional and is not model capability or factual transport accuracy.

The fixed development suite is observed and small/noise-skewed. Historical
stress/reference sets were already observed and have family overlap; the human
subset is nested. Phase21 is **post-development descriptive regression** for its earlier freeze.
It improves terminal dispatch chiefly alongside more unavailable responses,
while clarification precision/recall and historical OK count decline. No aligned
gold transport facts or canonical slot IDs exist in that evaluator, so factual
answer and slot accuracy are not measured. The later user-authorized correctness exception is disclosed above; its separate **Phase23 post-fix descriptive regression** uses the already observed set once. No model-only rerun or metric-driven tuning follows that measurement. The later residual correctness repair is disclosed above and was not evaluated again.

## Setup and deployment limits

The exact approximately 950 MB checkpoint is ignored and must be supplied by
the project/run owner through authorized manual transfer. There is no public
artifact download or automatic model fallback. Check trusted path/hash with the
artifact validator and prepare the pinned tokenizer/config cache explicitly.
Fresh owner transfer and a complete clean dependency installation were not
executed here; strict local loading and dependency consistency were verified.

API/Streamlit are a localhost demonstration, with a single-threaded API and no
public deployment/authentication integration. Desktop and narrow frontend visual
QA passed; see [the restored-style QA evidence](../../reports/nlp_v2/restored_ui_qa/qa.md).

Evidence: [development acceptance](development_acceptance.md),
[training decision](training_decision.md), [artifact workflow](model_artifact_workflow.md),
[descriptive regression](../../reports/nlp_v2/post_development_regression/comparison.md).
