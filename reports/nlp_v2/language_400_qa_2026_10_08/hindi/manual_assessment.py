import json
from pathlib import Path
from collections import Counter,defaultdict
B=Path(__file__).parent
# Each categorization is a manual semantic assessment of the preserved API baseline.
# No predictions are generated and no case/production/evaluator files are modified.
MANUAL='''
1|S|matched_source_limitation;counterfactual_endpoint_role_error|Correct metro-route topology refusal. Returned origin=METRO_NANDANAM is the supplied destination, with no Saidapet origin; this is a masked endpoint-role error, not a completed journey.
2|F|wrong_intent_family|Single bus journey is classified multimodal and refused for missing cross-mode graph. The safe refusal is for the wrong requested family.
3|S|matched_source_limitation|Correct MRTS point-to-point topology limitation, without invented route. Unreturned endpoints do not prove extraction failure under terminal preflight.
4|F|wrong_intent_family|Explicit metro-only journey becomes multimodal; missing cross-mode graph does not answer the requested metro route.
5|C|genuine_physical_bus_stop_ambiguity|Anna Nagar/Koyambedu bus references can denote several physical stops; the reply retains bus and direct_only and asks which physical location is meant, providing candidates.
6|F|supplied_native_mode_and_endpoints_unrecognized|Tambaram, Chennai Beach, and suburban rail are explicitly supplied, yet slots are empty and the assistant asks for both journey endpoints again.
7|F|supplied_native_destination_unrecognized|Egmore origin is retained, but supplied Vadapalani destination is lost and requested again.
8|S|matched_source_limitation;counterfactual_endpoint_role_error|Correct terminal metro topology refusal is safe even with missing journey origin. Returned origin=METRO_ARIGNAR_ANNA_ALANDUR misuses the supplied destination; no route was executed.
9|F|wrong_intent_family|Metro-only incomplete journey is mislabeled multimodal; cross-mode refusal is not a missing-destination clarification or the correct source limitation.
10|F|cheapest_route_confused_with_fare|Request for cheapest public journey becomes fare_calculation; no cheapest-route preference retained. Subsequent entity clarification is in the wrong goal family.
11|S|matched_source_limitation|Correct metro journey topology refusal. No fabricated journey or travel-time claim; this is not goal success.
12|U|negated_goal_answered|User explicitly says fare is not requested, but API returns CALCULATE_FARE INR20 between Guindy and Nandanam. The factual-looking answer addresses the excluded goal.
13|S|matched_source_limitation|Correct multimodal family and explicit absence of a confirmed cross-mode graph; no invented rail/metro itinerary.
14|S|matched_source_limitation|Correct bus-plus-metro planning refusal for missing confirmed graph; endpoints are not fabricated.
15|S|matched_source_limitation|Correct combined bus/metro itinerary limitation, rather than invented airport transfer routing.
16|F|multimodal_goal_collapsed_to_single_mode|Full rail-then-metro journey is classified point_to_point_route with metro only, so its source refusal is for a narrower goal.
17|S|matched_source_limitation|Correct combined local train/bus itinerary refusal due to absent cross-mode graph.
18|S|matched_source_limitation|Correct MRTS-plus-bus journey family and missing cross-mode graph refusal.
19|S|matched_source_limitation|Correct three-leg bus/metro/bus itinerary goal; no unverified transfer points are supplied.
20|S|matched_source_limitation|Correct ordered bus/suburban-rail itinerary family and explicit graph limitation.
21|S|matched_source_limitation|Correct metro-plus-bus journey to IIT Madras is refused for absent confirmed graph, without inventing landmark routing.
22|S|matched_source_limitation|Correct combined metro/local-train planning family; source limitation is explicit.
23|S|matched_source_limitation_with_incomplete_context|Missing origin is real, but terminal graph absence independently prevents any multimodal plan. Correct source refusal is safe, without inventing origin.
24|F|wrong_intent_family|Incomplete full mixed-mode itinerary becomes interchange_transfer. A station-interchange source refusal is not the intended planning limitation or missing-destination prompt.
25|S|partial_published_route_coverage|Preserves route21G and bus, and returns ordered published sequences. Explicit partial topology excludes route variants/links, so a complete start-to-end list is not established.
26|G|published_structured_stop_sequence|Preserves 102A bus suffix and supplies both published ordered stop variants (34/36 stops) in API data with no coverage gaps. Text previews first8 stops; full data supports the sequence goal with provisional-source qualification.
27|S|partial_published_route_coverage|Correct570 sequence family and route, with ordered variants. Explicit uncovered route IDs mean the full route list is source-limited, not fully achieved.
28|F|supplied_native_line_unrecognized|नीली लाइन is explicitly supplied, but no line_name is extracted and route/line is asked again.
29|S|matched_source_limitation|Correct metro stop-sequence topology refusal. Missing returned Green Line slot is not scored as a failure under terminal source preflight.
30|G|published_structured_stop_sequence|Correct27D bus sequence despite negated last-stop phrase; API data contains all published ordered variants with no coverage gaps. Text renders the first variant, while complete variants remain in structured data.
31|F|supplied_route_and_negation_unrecognized|Positive route102 and explicitly excluded102A yield no route slot and a request for route/line again; the supplied positive scope was not retained.
32|G|published_structured_stop_sequence|Correct47A suffix and ordered published variants (8/10/7/10 stops), with no reported topology gaps. Structured data supplies the stop-order goal.
33|S|matched_source_limitation|Correct MRTS sequence family and honest lack of mode-consistent topology; no false station list.
34|C|genuine_missing_route|This bus has no identified route or line. Asking for route/line is necessary and preserves bus mode.
35|S|partial_published_route_coverage|Spaced Devanagari21 जी is correctly normalized21G, but explicit omitted route variants/links prevent a complete sequence guarantee.
36|F|supplied_route_suffix_unrecognized|Full102K# route is supplied, yet route slot is empty and assistant requests a supported route suffix again; preservation/normalization failed before source lookup.
37|F|supplied_native_stop_unrecognized|Preserves21G bus but asks the stop to check despite the explicit Saidapet stop.
38|F|supplied_native_route_and_stop_unrecognized|Supplied102A and Adyar membership request produce neither slot and both are requested again.
39|S|matched_source_limitation|Correct metro membership family and Guindy stop, safely refused because metro topology is absent. Unreturned Blue Line is not proof of extraction failure under terminal preflight.
40|F|membership_confused_with_sequence|Egmore membership of Green Line becomes route_stop_sequence; asking for missing line also ignores the supplied native line.
41|F|supplied_native_stop_unrecognized|Preserves bus570 but loses supplied Sholinganallur stop and asks for it again.
42|F|supplied_native_stop_unrecognized|Preserves27D but fails to retain Vadapalani and asks which stop, instead of evaluating the negative membership question.
43|F|membership_confused_with_sequence|Question whether Thiruvanmiyur belongs to MRTS becomes an MRTS stop-list refusal; correct source limits do not excuse wrong family.
44|F|wrong_intent_family_and_route_suffix|Single102K# Kannagi Nagar membership becomes route_stop_sequence with no route preserved, then requests route again.
45|F|supplied_native_stop_unrecognized|Preserves47A bus, but asks for the explicitly supplied Anna Nagar stop instead of checking membership.
46|C|genuine_missing_route;secondary_supplied_stop_loss|Route is genuinely unspecified, so route clarification is appropriate. Asking for stop as well unnecessarily loses the supplied Tambaram reference; no membership facts are asserted.
47|C|genuine_missing_stop;secondary_supplied_route_loss|The referent यह जगह is genuinely unspecified, so stop clarification is appropriate. The prompt also asks route although21G was supplied; note collateral route recognition loss.
48|F|supplied_native_stop_unrecognized|Correct membership family despite negated fare, but Adyar stop is supplied and requested again; no membership answer is produced.
49|S|matched_source_limitation|Correct first-service metro goal, station and timing_type, with explicit absent metro timetable.
50|S|matched_source_limitation|Correct last-service metro goal and last timing, with absent metro timetable; no live or invented departure time.
51|F|substring_false_temporal_ambiguity|No कल appears as a standalone day request. लोकल incorrectly produces temporal_relative=कल, omits suburban mode/endpoints, and triggers irrelevant day clarification.
52|F|false_multiple_scope_guard|One21G last departure from Broadway is treated as multiple execution scopes. No actual second goal, route, or time is requested.
53|S|matched_source_limitation;counterfactual_mode_inconsistent_station|Correct metro first-and-last goal and source refusal. Returned station=RAIL_CHENNAI_CENTRAL contradicts explicit metro qualification; masked by absent metro schedules.
54|S|matched_source_limitation|Correct metro first-service family and missing metro schedule refusal. Empty line/station/timing extraction is not penalized under terminal source limitation.
55|F|false_multiple_scope_guard|Single Alandur last-metro question triggers multiple_goals; no additional independently requested scope exists.
56|S|matched_source_limitation|Correct first MRTS service family and explicit absence of mode-consistent schedule.
57|C|genuine_physical_bus_stop_ambiguity|Guindy with bus570 can refer to multiple physical boarding stops. Route, bus, and last timing survive; physical-stop clarification with candidates avoids arbitrary scheduling.
58|C|genuine_missing_boarding_stop|First bus time lacks boarding station/stop. Correct first_service family and useful stop clarification; no fabricated system-wide departure.
59|F|supplied_native_mode_and_station_unrecognized|Tambaram and suburban rail are explicit, yet mode/station are lost and a boarding stop is requested again; Sunday scope is not retained.
60|F|negated_sequence_controls_intent|User asks last metro and excludes last-station list, but gets route_stop_sequence topology refusal instead of first_and_last_service.
61|S|matched_source_limitation|Correct metro frequency family and Guindy station, with honest absence of metro published schedules.
62|F|supplied_native_boarding_stop_unrecognized|Bus21G is retained but Broadway is supplied and requested again as missing station/stop.
63|F|wrong_intent_and_substring_temporal_ambiguity|South Line suburban frequency becomes mode_availability; लोकल spuriously produces कल and day clarification.
64|S|matched_source_limitation|Typical Green Line metro wait is correctly frequency, safely limited by absent metro schedules rather than asserted as live wait.
65|F|frequency_confused_with_departure|Explicit average interval request for570 becomes scheduled_departure. Physical-stop ambiguity does not excuse wrong user-goal family.
66|S|matched_source_limitation|Correct Green Line metro frequency family and absent metro timetable limitation.
67|F|false_multiple_scope_guard|One Saidapet27D headway request is incorrectly treated as multiple scopes; no second goal/time is present.
68|S|matched_source_limitation|Correct MRTS frequency family and source refusal; no guessed trips-per-hour figure.
69|S|matched_source_limitation|Correct peak-period metro frequency family with absent published metro schedules; no guessed peak headway.
70|C|genuine_missing_route_and_stop|Generic bus intervals lack route/line and boarding stop. Both requested execution facts are genuinely missing.
71|S|matched_source_limitation_with_incomplete_context|Correct Blue Line metro frequency cannot execute even after supplying station because source timetable is absent. Terminal refusal is safe, without arbitrary estimate.
72|F|negated_first_service_controls_intent|User asks21G frequency and says not first-bus time; reply chooses first_and_last_service and first timing.
73|S|matched_source_limitation|Correct metro scheduled departures, Guindy, and normalized07:15 are preserved, with absent metro schedule limitation.
74|F|supplied_native_boarding_stop_unrecognized|Preserves21G bus and18:00, but Broadway boarding stop is explicitly supplied and requested again.
75|F|substring_false_temporal_ambiguity|लोकल causes fictitious कल ambiguity in an explicit Tambaram-to-Beach suburban timetable request; no day ambiguity was asked.
76|S|matched_source_limitation;counterfactual_wrong_day_period|Correct metro schedule source refusal. Returned time02:30 contradicts दोपहर२:३० (14:30); source absence masks a dangerous period-normalization defect.
77|S|matched_source_limitation|Correct MRTS published-departure goal is safely refused for absent schedules; no real-time substitution.
78|C|genuine_physical_bus_stop_ambiguity|Retains570, bus,21:00 after threshold. Guindy boarding-node ambiguity is clarified with candidates before any departure answer.
79|F|wrong_intent_and_false_multiple_scope_guard|Bare8 legitimately needs AM/PM clarification, but system selects first_and_last_service and calls it multiple goals instead of scheduled_departure temporal ambiguity.
80|S|matched_source_limitation;counterfactual_mode_inconsistent_station|Correct metro schedule source refusal safely prevents resolving ambiguous कल. Returned RAIL_CHENNAI_CENTRAL is incompatible with explicit metro station; no schedule executed.
81|S|matched_source_limitation_with_incomplete_context|Station is genuinely unspecified, but absent metro schedules independently prevent a timetable; correct family source refusal invents no station.
82|S|matched_source_limitation_with_invalid_clock|Correct metro timetable source refusal makes no claim about25:61. It does not demonstrate proper invalid-clock recognition; no valid time was invented or used.
83|F|time_range_misread_as_multiple_goals|06:00-to08:00 is a single schedule range, not two independent goals. Multiple-goals clarification does not explain unsupported range semantics.
84|F|single_before_bound_misread_as_multiple_goals|One before22:00 schedule request is mislabeled multiple scopes, instead of respecting before-bound or explaining its unsupported operation scope.
85|S|matched_source_limitation;counterfactual_endpoint_role_error|Correct metro availability source refusal. Returned origin=Nandanam reverses supplied destination role and omits Saidapet; no connection was falsely asserted.
86|F|supplied_native_endpoints_unrecognized|Both Broadway and Adyar are supplied in a bus existence question, but reply asks for both endpoints again.
87|F|supplied_native_mode_and_endpoints_unrecognized|Tambaram, Chennai Beach, suburban rail are supplied; empty extraction prompts for origin/destination again.
88|S|matched_source_limitation|Correct MRTS existence question and explicit missing mode topology; no unsupported service absence assertion.
89|S|matched_source_limitation|Correct metro availability family; safely refuses absent metro topology rather than interpreting service existence as a route itinerary.
90|C|genuine_physical_bus_stop_ambiguity|Guindy bus origin can denote multiple physical bus stops. Mode is preserved and clarification avoids treating user direct-bus assertion as verified connection.
91|F|substring_day_and_duplicate_entity_ambiguity|Supplied suburban mode is lost, लोकल creates कल, and Central candidates differ only by canonical hub spelling. This does not establish meaningful passenger ambiguity for the specified rail query.
92|F|alternative_mode_scope_misread|Primary question is whether metro service exists, with bus as fallback. Reply asks to choose one mode and stores Alandur as origin rather than preserving the requested metro connection.
93|F|wrong_intent_and_false_multiple_scope_guard|A single availability-at23:00 question becomes first_and_last_service with multiple_goals; no valid availability scope limitation is given.
94|C|genuine_missing_origin;secondary_supplied_destination_loss|Origin is genuinely missing in bus-to-Adyar availability. Origin clarification is necessary; prompt also unnecessarily asks destination despite supplied Adyar.
95|S|matched_source_limitation_with_incomplete_context|Destination is genuinely missing, but terminal metro topology absence independently blocks confirmation. Correct source refusal preserves Guindy origin without inventing destination.
96|S|matched_source_limitation|Correct metro availability and both endpoints are preserved despite negated route-detail phrase; absent topology is explicit.
97|F|supplied_spelled_stage_unrecognized|Ordinary bus and चार stage4 are supplied, but stage_number is omitted and fare basis is requested again.
98|F|supplied_devanagari_stage_unrecognized|Express bus and६ stage6 are supplied, but stage is omitted and fare basis is requested again.
99|F|supplied_spelled_stage_synonym_unrecognized|Deluxe bus with आठ चरण (eight fare stages) is supplied; extraction keeps class but drops stage and asks fare basis again.
100|F|supplied_spelled_stage_and_native_class_unrecognized|रात्रि सेवा and पाँच stages are supplied, but both Night service class and stage5 are lost; no stage fare goal achieved.
101|F|supplied_devanagari_stage_unrecognized|Air Conditioned bus class is retained but explicit१० stages are lost, resulting in unnecessary origin/stage prompt.
102|F|supplied_native_destination_unrecognized|Metro Guindy origin retained, but Chennai Airport destination supplied in Hindi is lost and requested again.
103|F|mode_qualified_entity_and_role_error|Explicit Egmore metro origin yields rail/bus/hub ambiguity, while Nandanam destination is wrongly stored as origin. This is recognition/role failure, not genuine user ambiguity.
104|F|supplied_spelled_stage_unrecognized|Ordinary MTC bus and तीन stage3 are supplied, but only fare_type/class survive; stage basis is requested again.
105|F|clarification_asks_wrong_missing_fact|Stage4 is supplied and service class explicitly unknown. Reply drops stage and asks fare basis rather than the genuinely missing service class.
106|F|fare_goal_confused_with_ticket_policy|Incomplete fare calculation is classified ticketing_and_passes and refused for missing policy table, rather than requesting fare basis.
107|C|invalid_zero_stage_safely_clarified|Zero stages are invalid under public1–30 contract. No tariff is asserted; request for a valid stage or endpoints is a safe clarification, though range/zero error should be stated more explicitly.
108|C|invalid_out_of_range_stage_safely_clarified|इकतीस stages=31 is outside1–30 contract. Reply requests valid fare basis without using invalid count or producing fare; it could explain the bound more clearly.
109|S|matched_source_limitation|Correct smart-card minimum-recharge policy goal, honestly refused for absent authoritative ticket/pass policy.
110|S|matched_source_limitation|Correct QR-ticket policy goal with source limitation; no invented purchase rule.
111|S|matched_source_limitation|Correct monthly-pass validity family and absent authoritative policy limitation.
112|S|matched_source_limitation|Correct suburban season-pass documents goal and policy source refusal.
113|S|matched_source_limitation|Correct NCMC ticketing-policy family and explicit missing authoritative policy.
114|S|matched_source_limitation|Correct lost-token replacement policy family; no guessed replacement rules.
115|F|pass_policy_confused_with_service_frequency|Tourist-pass journey allowance is classified service_frequency and asks boarding stop/line, which are irrelevant policy execution facts.
116|S|matched_source_limitation|Correct child concession ticket-rule family, with no unsupported age limit or percentage.
117|S|matched_source_limitation|Correct smart-card refund policy family and explicit absent policy source.
118|S|matched_source_limitation|Correct payment-method policy family, refused due to absent authoritative ticket policy.
119|S|matched_source_limitation|Correct pass transferability policy, safely refuses absent authoritative allowed/disallowed rules.
120|S|matched_source_limitation|Correct QR validity policy despite negated price; absent policy source prevents unsupported validity claim.
121|S|matched_source_limitation|Correct bike-parking facility goal, explicitly unverified rather than affirmative parking claim.
122|S|matched_source_limitation|Correct drinking-water facility family with unverified-source refusal.
123|S|matched_source_limitation|Correct general restroom facility family, safely refuses absent verification.
124|S|matched_source_limitation|Correct waiting-room facility family and honest missing verification.
125|S|matched_source_limitation|Correct cloakroom facility family and source refusal; no fabricated luggage-storage availability.
126|F|facility_confused_with_interchange|ATM query becomes interchange_transfer and receives missing-interchange refusal; safe wording belongs to wrong family.
127|F|facility_confused_with_mode_availability|Airport-station Wi-Fi is classified mode_availability and refused for absent metro topology, not station facility evidence.
128|S|matched_source_limitation|Correct Nandanam car-parking facility family with unverified availability.
129|S|matched_source_limitation|Correct Tambaram waiting-room station facility family with absent verification.
130|S|matched_source_limitation_with_incomplete_context|Station is genuinely unspecified, but terminal facility-source absence prevents an answer independently. Correct refusal picks no arbitrary station.
131|S|matched_source_limitation|Correct parking family despite explicitly excluded wheelchair goal; no false accessibility or parking answer.
132|F|colloquial_restroom_confused_with_interchange|Egmore bathroom query is classified interchange_transfer; missing-interchange records do not address bathroom facility evidence.
133|S|matched_source_limitation|Correct wheelchair accessibility goal and explicit absence of verified accessibility feature values.
134|S|matched_source_limitation|Correct lift/step-free accessibility family and missing feature-value source, without guessed availability.
135|S|matched_source_limitation|Correct ramp accessibility family and absence of verified feature values.
136|S|matched_source_limitation|चलती सीढ़ी is correctly understood as accessibility; source refusal makes no unsupported escalator assertion.
137|S|matched_source_limitation|Correct tactile-path accessibility family and explicit missing verified feature values.
138|S|matched_source_limitation|Correct accessible-toilet accessibility family rather than general facility; absent verified values disclosed.
139|S|matched_source_limitation|Correct lift accessibility goal for elderly access and honest missing verified values.
140|S|matched_source_limitation|Correct wheelchair-platform access family; no unsupported affirmative confirmation.
141|S|matched_source_limitation|Correct suburban ramp accessibility family; terminal verified-feature-value absence stated.
142|F|accessibility_confused_with_nearest|Station is genuinely missing, but wheelchair-accessibility question becomes nearest_transport and asks for landmark/locality rather than station.
143|F|negated_facility_controls_intent|User asks lift and explicitly excludes parking, but reply chooses station_facilities and facility-source refusal instead of accessibility.
144|S|matched_source_limitation|Implicit step-free platform access correctly classified accessibility, with no unverified assurance.
145|S|matched_source_limitation|Correct metro-to-local-train interchange goal and missing confirmed interchange records; no invented connection directions.
146|S|matched_source_limitation|Correct Alandur Blue-to-Green line transfer family; confirmed interchange source missing.
147|F|station_transfer_confused_with_full_multimodal_route|Central rail-to-metro physical connection becomes multimodal_route, refusing a whole journey graph rather than transfer records.
148|F|interchange_confused_with_facility|Bus-terminal/metro transfer arrangement becomes generic station_facilities; no correct interchange limitation given.
149|S|matched_source_limitation|Correct Chennai Beach rail-to-MRTS interchange family; source refuses unconfirmed transfer connection.
150|S|matched_source_limitation|Correct same-mode metro-line interchange family and missing confirmed transfer records.
151|F|station_transfer_confused_with_full_multimodal_route|Tambaram rail-to-bus transfer point becomes full multimodal_route; refusal uses wrong operation/source family.
152|F|station_transfer_confused_with_full_multimodal_route|Guindy bus-to-metro physical transfer information becomes multimodal_route rather than interchange_transfer.
153|F|interchange_confused_with_mode_availability|Egmore rail-platform-to-metro connection becomes mode_availability; topology absence does not address physical transfer records.
154|S|matched_source_limitation|Correct metro-to-bus transfer family without specified station; terminal missing interchange records prevents any factual transfer guidance.
155|F|incomplete_interchange_confused_with_facility|Here and both transfer modes are unspecified, but changing vehicle is an interchange goal. Reply assumes generic facility rather than asking station/modes or correct interchange source limit.
156|F|negated_parking_controls_intent|User asks Alandur line-transfer method and excludes parking; reply selects facilities and refuses facility source.
157|G|published_nearest_with_scope_qualification|Correct Marina Beach bus-mode anchor; source returns bus stop Kannagi Statue/Presidency College277m and explicitly labels straight-line distance with walking access unverified.
158|F|supplied_native_landmark_unrecognized|IIT Madras landmark and metro mode are explicit; mode survives but landmark/locality is asked again.
159|F|supplied_native_locality_and_mode_unrecognized|Anna Nagar locality and rail station request are supplied; both anchor and rail mode are lost, and locality is requested again.
160|F|supplied_native_landmark_unrecognized|Full Apollo Hospital Greams Road landmark is supplied with bus mode; assistant asks landmark/locality again.
161|F|supplied_native_locality_unrecognized|Adyar locality is explicit but no spatial anchor is retained and locality is requested again.
162|F|supplied_native_landmark_unrecognized|Chepauk stadium landmark is supplied; MRTS mode is retained but reference landmark/locality is requested again.
163|F|supplied_native_landmark_unrecognized|Phoenix Marketcity is supplied as landmark but lost; nearest bus query asks location again.
164|F|supplied_native_locality_unrecognized|Velachery locality is explicit; nearest metro query requests an already supplied location.
165|U|dropped_required_mode_wrong_nearest_answer|Explicit उपनगरीय rail mode is dropped and API returns bus stop Kannagi Statue/Presidency College277m. Correct anchor/proximity family cannot excuse wrong transport mode.
166|F|nearest_goal_confused_with_sequence|A nearest bus stop with missing location becomes route_stop_sequence and asks route/line rather than nearby landmark/locality.
167|G|published_nearest_with_scope_qualification|Correct Marina Beach nearest metro goal despite excluded route request. Returns metro stop Lighthouse1121m with explicit straight-line/provisional and unverified-walking qualifications.
168|F|locality_anchor_confused_with_physical_stop|User specifies Guindy locality and metro result, but anchor resolution returns bus/hub/rail/metro station ambiguity. It does not use the supplied locality as geographic reference.
169|S|matched_external_source_limitation|Correct live21G GPS-location family and explicit lack of live transport status; no fabricated vehicle position.
170|F|realtime_delay_confused_with_first_last|Current metro delay is classified first_and_last_service; missing published timetable refusal does not explain unavailable live delay feed.
171|F|realtime_crowd_confused_with_frequency|Current Central metro crowd level becomes service_frequency and timetable-source refusal, not realtime source limitation.
172|F|realtime_location_confused_with_interchange|Current Tambaram–Beach train position is classified interchange_transfer, producing irrelevant transfer-record refusal.
173|F|realtime_disruption_confused_with_static_availability|Current airport-metro shutdown/running status becomes mode_availability, with static topology refusal instead of live source explanation.
174|S|matched_external_source_limitation|Correct live570 ETA family, explicit unavailable live transport status, and no scheduled-time-as-actual-arrival substitution.
175|F|realtime_incident_confused_with_interchange|Present Blue Line accident/disruption becomes interchange_transfer and irrelevant source refusal.
176|F|live_equipment_status_confused_with_static_accessibility|User asks if lift is working right now; classification station_accessibility addresses static feature evidence, not live equipment status.
177|F|negated_schedule_controls_realtime_intent|User asks actual present delay and excludes timetable, yet scheduled_departure selected and timetable absence refused.
178|F|realtime_departure_confused_with_first_last_and_false_scope|Actual MRTS departure already happened is realtime; reply selects first_and_last_service with multiple_goals despite one present-status question.
179|F|realtime_capacity_confused_with_ticketing|Current27D crowd/seat availability becomes ticketing_and_passes and missing ticket policy, not live capacity source need.
180|F|realtime_platform_closure_confused_with_interchange|Current Alandur platform closure is classified interchange_transfer; confirmed-interchange source absence is irrelevant to live closure status.
181|F|weather_confused_with_first_last|Future rain/weather is out of scope but becomes first_and_last_service with day clarification. Irrelevant transport family is a failure even without weather hallucination.
182|S|correct_out_of_scope_rejection|Taxi booking is correctly rejected as outside Chennai public-transport scope; requested transaction remains unfulfilled and no booking is claimed.
183|S|correct_out_of_scope_rejection|Hotel reservation is correctly rejected without fabricated booking. Safe domain boundary, not completed user booking goal.
184|F|flight_purchase_confused_with_ticket_policy|Delhi flight purchase becomes ticketing_and_passes and policy-source refusal instead of correct out_of_scope transaction rejection.
185|F|intercity_reservation_confused_with_ticket_policy|Bangalore intercity rail-seat reservation becomes ticketing_and_passes; missing local policy is the wrong rejection reason/family.
186|F|ticket_purchase_transaction_confused_with_information|User asks actual metro ticket purchase/payment; API chooses informational ticket policy and absent source instead of out_of_scope transaction boundary.
187|F|utility_bill_confused_with_transit_fare|Electric bill account query becomes fare_calculation and asks fare endpoints/stages; irrelevant transportation workflow.
188|S|correct_out_of_scope_rejection|Food recommendation is correctly rejected as outside transport scope; no unsupported restaurant recommendation is provided and original goal remains unfulfilled.
189|F|device_location_confused_with_transport_realtime|User asks own phone location, but realtime transport status refusal is selected; correct device/scope boundary is not recognized.
190|F|unrelated_arithmetic_confused_with_ticketing|Explicitly excluded metro topic and arithmetic question become ticketing_and_passes, with unrelated policy refusal.
191|F|financial_transaction_confused_with_ticket_policy|Bank money-transfer request is classified ticketing policy, instead of out_of_scope transaction rejection; no transfer is falsely claimed.
192|F|horoscope_confused_with_transport_realtime|Horoscope request becomes realtime_status_query; missing live transport feed is not an appropriate domain rejection.
193|C|genuine_multiple_goals|Fare and first-service time are independently requested; correct null intent/operation and multiple_goals clarification ask which to answer first.
194|U|silently_dropped_independent_goal|Stop-list plus actual live bus position are independently requested. API executes stop sequence and supplies only that answer, silently dropping realtime goal instead of clarifying.
195|C|genuine_multiple_goals|Lift accessibility and parking facility are independently requested; null intent/operation with multiple_goals correctly asks which goal first.
196|F|multiple_goals_unrecognized_wrong_sequence_goal|Nearest bus stop and full journey are independently requested. Reply instead assumes route_stop_sequence and asks route/line, neither requested clarification nor appropriate family.
197|F|undetermined_goal_arbitrarily_selected|गिंडी मेट्रो की सुविधा is genuinely unspecified across service/facilities/accessibility. Assistant chooses mode availability and topology refusal rather than asking the actual goal.
198|F|undetermined_goal_and_polysemous_bus_assumption|Sparse Tambaram/train/कल input contains no first/last goal. Reply arbitrarily selects first_and_last_service and interprets बस इतनी (only this much) as bus mode; day clarification alone does not resolve the unspecified goal.
199|F|supplied_positive_spelled_stage_unrecognized|Positive दस stages and Ordinary bus supplied, with चार explicitly negated. Stage10 is omitted and fare basis asked again; positive/negated scope not represented.
200|S|matched_source_limitation_with_invalid_clock|Correct metro departure source refusal asserts no clock/fact at invalid11:75. Terminal preflight makes invalid-minute parsing unproven; no invented valid time is executed.
'''
CATEGORY={'S':'safe_limitation','F':'recognition_failure','G':'goal_correct','C':'legitimate_clarification','U':'unsafe_or_wrong_answer','R':'needs_review'}
rows=json.loads((B/'baseline.json').read_text(encoding='utf-8'))
byid={r['id']:r for r in rows}
out=[]
for line in MANUAL.strip().splitlines():
 num,cat,issue,note=line.split('|',3)
 cid=f'HI200_{int(num):03d}'
 assert cid in byid
 a=byid[cid]['actual']
 evidence=f" Evidence: status={a['status']}; intent={a['intent']}; operation={a['operation']}; clarification_reason={a['clarification_reason']}; slots={json.dumps(a['slots'],ensure_ascii=False,sort_keys=True)}."
 out.append({'id':cid,'category':CATEGORY[cat],'notes':note+evidence,'issue_type':issue})
assert len(out)==200 and len({x['id'] for x in out})==200
assert {x['id'] for x in out}==set(byid)
(B/'assessment.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
counts=Counter(x['category'] for x in out)
print(dict(counts))
print('Manual assessment records:',len(out))
