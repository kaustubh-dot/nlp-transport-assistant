# Independent Hindi 200-query API assessment

All 200 Hindi cases were authored with explicit expectations before inference, cover all 16 T3 families (at least 12 per family), and have no exact query duplicates against the two earlier campaign files. Only public contracts/taxonomy/service sources informed authoring; no frozen/development/held-out examples, model, database, training, or evaluator were invoked. Baseline API results are preserved unchanged.

All 200 baseline responses were manually read and classified against the passenger goal, supplied positive/negative constraints, explicit modes, endpoint roles, clock/day meaning, missing-context guards, and independently declared source limits. This assessment does not equate intent agreement, a harmless refusal, or HTTP200 with answered goals.

| Category | Count | Share |
|---|---:|---:|
| goal_correct | 5 | 2.5% |
| safe_limitation | 83 | 41.5% |
| legitimate_clarification | 14 | 7% |
| recognition_failure | 95 | 47.5% |
| unsafe_or_wrong_answer | 3 | 1.5% |
| needs_review | 0 | 0% |

Only 5/200 (2.5%) achieve the requested supported API goal. Another 83/200 (41.5%) are correct, safe source/domain limitations, and 14/200 (7%) are legitimate requests for missing/ambiguous information. The 95 recognition failures plus 3 wrong/scope-dropping answers total 98/200 (49%) failures. These sampled counts are descriptive, not a statistically validated estimate for all Hindi traffic.

Correct source limitations retain the requested intent/operation and explain missing authoritative topology, timetable, policy, facilities, accessibility, transfers, or live feed. They are not goal success. A refusal in the wrong intent family is recognition_failure. Wrong returned slot values under a valid independent terminal preflight are secondary counterfactual defects in safe_limitation notes; unreturned slots under that preflight are not assumed to be extraction failures. This distinction prevents absent sources from artificially making recognition look successful or unsuccessful.

Genuine clarification is based on missing query context or a real choice of physical bus stops, not a clearly supplied native place that the recognizer failed to read. Several missing-context cases also have collateral loss of already supplied route/stop information; the notes retain that defect even when independent missing context makes clarification necessary. Invalid stage0/31 prompts safely request a valid fare basis, though the assistant should explain the1–30 bound.

For goal_correct stop sequences, the complete ordered source variants are present in structured API data. The text renderer previews only the first variant/first8 stops; it is not a complete natural-language list. Cases with explicitly uncovered source variants/links remain safe_limitation. Nearest results qualify their distance as straight-line and do not claim verified walking access or current station operations.

## Material wrong/scope-dropping answers

- HI200_012: The user asks only Guindy-to-Nandanam metro route and explicitly says किराया नहीं पूछ रहा. The system returns CALCULATE_FARE INR20, answering the excluded fare goal.
- HI200_165: The user asks the closest उपनगरीय rail station to Marina Beach. The system drops rail mode and returns bus stop Kannagi Statue/Presidency College277m.
- HI200_194: The user independently asks21G stop list and current bus position. The system executes stop-list lookup and silently ignores the live-position goal instead of asking which question first.

## Repeated recognition issues

- Native entities: HI200_006/007/037/041/059/062/074/086/087/102 and HI200_158–164 ask again for supplied place names, boarding stops, or landmarks. Explicit mode qualification does not resolve the Hindi forms in several cases.
- Native numerals/spelled stages: HI200_097–101/104/105/199 drop supplied stage counts (चार,६,आठ चरण,पाँच,१०,तीन,४,दस) and ask for a fare basis again. HI200_100 also misses native रात्रि service class. Complete suffix102K# is lost in HI200_036/044.
- Substring day parsing: लोकल incorrectly becomes temporal_relative=कल in HI200_051/063/075/091. This triggers fabricated day ambiguity instead of recognizing local/suburban rail.
- False scope guard: Single-goal questions HI200_052/055/067 and a single timetable range/before-bound HI200_083/084 trigger multiple_goals. Bare8 in HI200_079 should need AM/PM clarification, but gets a different family/multiple-goals response.
- Negation: HI200_060/072/143/156/177 choose the explicitly excluded stop-list, first-service, parking, or timetable goal. HI200_012 goes further by executing the excluded fare goal.
- Family boundaries: Station transfers HI200_147/148/151/152/153 become journey/facilities/availability; realtime HI200_170–173/175–180 mostly becomes static timing/transfer/ticketing; out-of-scope HI200_181/184–187/189–192 becomes transit workflows.

## Masked returned-slot defects

- HI200_001/008/085 store the supplied destination as origin. Correct independent metro-topology refusal prevents execution; the returned values remain wrong.
- HI200_053/080 return RAIL_CHENNAI_CENTRAL with explicit metro mode. Again, absent metro schedules mask the inconsistency.
- HI200_076 turns दोपहर२:३० into02:30 rather than14:30. Correct unavailable metro-schedule result is safe, but enabling schedules would expose the wrong requested time.

## Per-family outcome counts

| Expected family | Goal correct | Safe limitation | Legitimate clarification | Recognition failure | Wrong answer | Needs review |
|---|---:|---:|---:|---:|---:|---:|
| point_to_point_route | 0 | 4 | 1 | 6 | 1 | 0 |
| multimodal_route | 0 | 10 | 0 | 2 | 0 | 0 |
| route_stop_sequence | 3 | 5 | 1 | 3 | 0 | 0 |
| route_stop_membership | 0 | 1 | 2 | 9 | 0 | 0 |
| first_and_last_service | 0 | 5 | 2 | 5 | 0 | 0 |
| service_frequency | 0 | 6 | 1 | 5 | 0 | 0 |
| scheduled_departure | 0 | 7 | 1 | 5 | 0 | 0 |
| mode_availability | 0 | 5 | 2 | 5 | 0 | 0 |
| fare_calculation | 0 | 0 | 2 | 11 | 0 | 0 |
| ticketing_and_passes | 0 | 11 | 0 | 1 | 0 | 0 |
| station_facilities | 0 | 9 | 0 | 3 | 0 | 0 |
| station_accessibility | 0 | 10 | 0 | 2 | 0 | 0 |
| interchange_transfer | 0 | 5 | 0 | 7 | 0 | 0 |
| nearest_transport | 2 | 0 | 0 | 9 | 1 | 0 |
| realtime_status_query | 0 | 2 | 0 | 10 | 0 | 0 |
| out_of_scope | 0 | 3 | 0 | 9 | 0 | 0 |
| ambiguity/multiple-goal guard | 0 | 0 | 2 | 3 | 1 | 0 |

Assessment artifacts: cases.json (locked authored cases), dataset_validation.json (uniqueness/UTF-8/public-slot checks), baseline.json (unchanged API evidence), assessment.json (200 manual records with issue types and actual-output evidence), and this summary. No production code was edited by this author/assessor.
