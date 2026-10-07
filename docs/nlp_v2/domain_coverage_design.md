# Phase 14 canonical domain coverage

Use immutable canonical records and frozen T3 operations. Expand three bounded
paths: positive directional published connectivity, case-normalized Night
Services tariffs, and exact stop/hub/place coordinate anchors. Membership also
needs its source identifiers. Availability preserves route-number and via constraints. Positive connectivity means the published sequence
contains ordered endpoints; it never confirms operation now. Dated/timed availability
and dated/timed route planning remain unavailable because sequence evidence does
not establish an active trip at the requested time. No negative connectivity
claim is inferred from absence.

Preserve multiple explicit modes: atomic operations request a single mode rather
than silently dropping the constraint. Universally unavailable multimodal and
transfer capabilities retain their preflight refusals. Retain exact candidate
ambiguity and model raw-input/tokenization contracts.

Expose incomplete topology explicitly. A negative membership claim requires the
candidate routes' full published rows to be mode-consistent; positive matches may
be bounded to consistent records. Filtered route sequences report excluded rows
and partial coverage, including empty same-code route variants. A frequency estimate requires one route, direction and
physical stop group; mixing opposing directions is unavailable rather than a
misleading headway. Existing timetable source and provisional fields remain.

## Capability matrix

| T3 operation | State | Category and evidence |
|---|---|---|
| PLAN_ROUTE | partially supported | A: ordered mode-consistent bus sequences; B: provisional hubs; no trip/time optimization |
| PLAN_MULTIMODAL_ROUTE | verification-required | B: hub/transfer records unverified; no confirmed graph |
| LIST_ROUTE_STOPS | partially supported | A: bus sequences; B: corrupt metro links excluded and partial coverage disclosed |
| CHECK_STOP_ON_ROUTE | partially supported | A: bounded sequence membership; B: incomplete routes cannot establish absence |
| GET_FIRST_LAST_SERVICE | partially supported | A: published bus timetable/calendar; B: no valid metro schedule |
| GET_SERVICE_FREQUENCY | partially supported | A: one route/direction/stop published departure interval; no live frequency |
| GET_SCHEDULED_DEPARTURES | partially supported | A: published bus timetable; D: no live predictions |
| CHECK_SERVICE_AVAILABILITY | partially supported | A: positive static connectivity; D/B: current/dated operation unconfirmed |
| CALCULATE_FARE | partially supported | A: dated metro token and explicit bus stage tariff, case-normalized category; B: no discount eligibility or OD stage ordinal |
| GET_TICKETING_POLICY | unsupported | C: authoritative policy table absent |
| GET_STATION_FACILITY | verification-required | B/C: verified facility values absent |
| GET_ACCESSIBILITY_INFO | verification-required | B: all snapshot values null |
| GET_INTERCHANGE_DETAILS | verification-required | B: all records unconfirmed |
| FIND_NEAREST_STATION | supported | A: straight-line lookup from exact canonical coordinates; B: pedestrian access unverified |
| REJECT_UNSUPPORTED_REALTIME | realtime-only | D: no telemetry source |
| REJECT_OUT_OF_SCOPE | supported | Product scope rejection |

No external integration, DB repair, inferred walking links, tariff substitution,
model training, frozen suite edits, or held-out item inspection is authorized by
this phase. Test additions are synthetic contracts or direct canonical evidence.
