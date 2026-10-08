# Hindi Devanagari baseline product QA — 2026-10-08

48 independently authored manual Hindi questions were submitted sequentially to the existing real API at http://127.0.0.1:8875/api/v2/query. Source HEAD during collection: `490ba62b65f7bd3b223f66eaa1ac3c6335800006`; collected UTC 2026-10-08T04:37:39.861474+00:00. Health was HTTP200/T3; all48 query responses were HTTP200. Proper names, AM notation and two date/clock contrasts use Latin symbols inside predominantly Hindi questions. Two phrases per16 intended T3 families are followed by16 missing-slot/entity/time/noise/waypoint/out-of-scope contrasts. This is fresh manually scoped product QA, **not** a representative model-accuracy estimate or frozen evaluation. No evaluator, training, development/held-out rows, alias, classifier, DB, app or tests were changed by this agent. UI testing was pending at collection; browser verification was subsequently reassigned to the primary after this agent's browser context became unavailable. See independent_review.md for the ownership and evidence limits.

Exact structured public JSON is preserved in baseline.json and each baseline.csv row. The API exposes actual intent/operation, slots, status, outcome_reason and candidates; it does not expose model confidence or raw classifier internals. Recognition mismatch is a broad product category covering wrong-family choice, supplied inputs missed by extraction, unexpected scope guard and dropped goals; it is not proof that every issue originates exclusively in the model. Categories were manually assigned after inspecting replies, not inferred from status alone.

Observed status counts: {"clarification": 25, "unavailable": 14, "ok": 8, "out_of_scope": 1}. Manual categories: {"legitimate ambiguity": 7, "recognition mismatch": 22, "unsupported source": 10, "successful bounded answer": 6, "safe guard": 3}. Counts describe this48-case scope and are not accuracy or generalization claims. Two OK replies(H13,H44) are material goal mismatches, so OK does not mean the user goal passed.

## Findings

- Numeric ordinary stage8 and deluxe stage6 fares(H17,H18), Hindi suffix25आर stop sequence(H06), explicit सुबह८ departures(H40) and noisy route102(H47) produced bounded published answers. Missing service classH33 visibly defaulted to Ordinary Services; that behavior is reported rather than assuming a required slot.
- Goal mismatches include post09:00 departures→bounds(H13), transfer→ticket policy(H25), live crowd→frequency(H30), weather→service-time ambiguity(H32), and poem near transit→ticket policy(H48). H44 answers only fare despite two explicitly asked goals.
- Stop-number forms संख्या१०२(H05) and१०२नंबर(H07) did not preserve the supplied route. Hindi proper names in H02,H09,H14,H16,H27,H28 were often missing from execution slots. Spelled ordinalआठवें(H36) was not accepted as a stage number.
- Frequency H11/H12 and last-serviceH10 received multiple-scope clarifications despite singular route/stop wording. H04's output included कल although the only containing word in the query was लोकल. These are observed recognition/guard limitations; no production fixes or speculative causal tuning were made.
- Genuine Central/Guindy entity ambiguity(H01,H08,H38,H45) remained conservative. Bare कल(H41), invalid time/date(H42), missing route(H34) and invented anchor(H37) avoided fabricated facts.
- Correct matched source boundaries were reached for multimodal, metro availability, ticketing, facility, accessibility, interchange and realtime. Preflight refuses before slot extraction for some capabilities, so these refusals do not prove every Hindi facility/feature/card/station token was parsed.
- Known/unknown Hindi waypoint contrastsH45/H46 did not answer successfully, but also did not establish the explicit waypoint-refusal path. Do not count intended waypoint wording as all timetable-operation guard coverage.

## Compact case index

|ID|Intended family / contrast|Actual intent|Actual operation|Status|Manual category|
|---|---|---|---|---|---|
|H01|point_to_point_route / family_pair|point_to_point_route|None|clarification|legitimate ambiguity|
|H02|point_to_point_route / family_pair|point_to_point_route|PLAN_ROUTE|clarification|recognition mismatch|
|H03|multimodal_route / family_pair|multimodal_route|PLAN_MULTIMODAL_ROUTE|unavailable|unsupported source|
|H04|multimodal_route / family_pair|point_to_point_route|None|clarification|recognition mismatch|
|H05|route_stop_sequence / family_pair|route_stop_sequence|LIST_ROUTE_STOPS|clarification|recognition mismatch|
|H06|route_stop_sequence / family_pair|route_stop_sequence|LIST_ROUTE_STOPS|ok|successful bounded answer|
|H07|route_stop_membership / family_pair|route_stop_membership|CHECK_STOP_ON_ROUTE|clarification|recognition mismatch|
|H08|route_stop_membership / family_pair|route_stop_membership|None|clarification|legitimate ambiguity|
|H09|first_and_last_service / family_pair|first_and_last_service|GET_FIRST_LAST_SERVICE|clarification|recognition mismatch|
|H10|first_and_last_service / family_pair|scheduled_departure|None|clarification|recognition mismatch|
|H11|service_frequency / family_pair|service_frequency|None|clarification|recognition mismatch|
|H12|service_frequency / family_pair|scheduled_departure|None|clarification|recognition mismatch|
|H13|scheduled_departure / family_pair|first_and_last_service|GET_FIRST_LAST_SERVICE|ok|recognition mismatch|
|H14|scheduled_departure / family_pair|scheduled_departure|GET_SCHEDULED_DEPARTURES|clarification|recognition mismatch|
|H15|mode_availability / family_pair|mode_availability|CHECK_SERVICE_AVAILABILITY|unavailable|unsupported source|
|H16|mode_availability / family_pair|mode_availability|CHECK_SERVICE_AVAILABILITY|clarification|recognition mismatch|
|H17|fare_calculation / family_pair|fare_calculation|CALCULATE_FARE|ok|successful bounded answer|
|H18|fare_calculation / family_pair|fare_calculation|CALCULATE_FARE|ok|successful bounded answer|
|H19|ticketing_and_passes / family_pair|ticketing_and_passes|GET_TICKETING_POLICY|unavailable|unsupported source|
|H20|ticketing_and_passes / family_pair|ticketing_and_passes|GET_TICKETING_POLICY|unavailable|unsupported source|
|H21|station_facilities / family_pair|station_facilities|GET_STATION_FACILITY|unavailable|unsupported source|
|H22|station_facilities / family_pair|station_facilities|GET_STATION_FACILITY|unavailable|unsupported source|
|H23|station_accessibility / family_pair|station_accessibility|GET_ACCESSIBILITY_INFO|unavailable|unsupported source|
|H24|station_accessibility / family_pair|station_accessibility|GET_ACCESSIBILITY_INFO|unavailable|unsupported source|
|H25|interchange_transfer / family_pair|ticketing_and_passes|GET_TICKETING_POLICY|unavailable|recognition mismatch|
|H26|interchange_transfer / family_pair|interchange_transfer|GET_INTERCHANGE_DETAILS|unavailable|unsupported source|
|H27|nearest_transport / family_pair|nearest_transport|FIND_NEAREST_STATION|clarification|recognition mismatch|
|H28|nearest_transport / family_pair|nearest_transport|FIND_NEAREST_STATION|clarification|recognition mismatch|
|H29|realtime_status_query / family_pair|realtime_status_query|REJECT_UNSUPPORTED_REALTIME|unavailable|unsupported source|
|H30|realtime_status_query / family_pair|service_frequency|GET_SERVICE_FREQUENCY|unavailable|recognition mismatch|
|H31|out_of_scope / family_pair|out_of_scope|REJECT_OUT_OF_SCOPE|out_of_scope|safe guard|
|H32|out_of_scope / family_pair|first_and_last_service|None|clarification|recognition mismatch|
|H33|fare_calculation / missing_service_class|fare_calculation|CALCULATE_FARE|ok|successful bounded answer|
|H34|route_stop_sequence / missing_route|route_stop_sequence|LIST_ROUTE_STOPS|clarification|legitimate ambiguity|
|H35|nearest_transport / missing_anchor|route_stop_sequence|LIST_ROUTE_STOPS|unavailable|recognition mismatch|
|H36|fare_calculation / spelled_ordinal|fare_calculation|CALCULATE_FARE|clarification|recognition mismatch|
|H37|nearest_transport / unknown_anchor|nearest_transport|FIND_NEAREST_STATION|clarification|safe guard|
|H38|nearest_transport / entity_ambiguity|nearest_transport|None|clarification|legitimate ambiguity|
|H39|scheduled_departure / clock_ambiguity|route_stop_sequence|LIST_ROUTE_STOPS|clarification|recognition mismatch|
|H40|scheduled_departure / explicit_morning_clock|scheduled_departure|GET_SCHEDULED_DEPARTURES|ok|successful bounded answer|
|H41|first_and_last_service / relative_day_ambiguity|first_and_last_service|None|clarification|legitimate ambiguity|
|H42|scheduled_departure / invalid_date_time|scheduled_departure|None|clarification|safe guard|
|H43|route_stop_sequence / multiple_route_scope|route_stop_sequence|LIST_ROUTE_STOPS|clarification|recognition mismatch|
|H44|multiple_goals / fare_and_departure|fare_calculation|CALCULATE_FARE|ok|recognition mismatch|
|H45|scheduled_departure / known_waypoint|scheduled_departure|None|clarification|legitimate ambiguity|
|H46|service_frequency / unknown_waypoint|service_frequency|GET_SERVICE_FREQUENCY|clarification|legitimate ambiguity|
|H47|route_stop_sequence / punctuation_whitespace_noise|route_stop_sequence|LIST_ROUTE_STOPS|ok|successful bounded answer|
|H48|out_of_scope / transit_entity_out_of_scope|ticketing_and_passes|GET_TICKETING_POLICY|unavailable|recognition mismatch|

## Exact questions, assessments and actual public JSON

### H01 — point_to_point_route / family_pair

Question: बस से चेन्नई सेंट्रल से एयरपोर्ट तक जाने का रास्ता बताइए।

Category: **legitimate ambiguity**. The route family is selected; Central resolves to three candidates. Entity clarification is conservative.

HTTP 200; observed request round trip 52.6 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "point_to_point_route",
  "operation": null,
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL",
    "HUB_PURATCHI_THALAIVAR_DR__M__G__RAMACHANDRAN_CENTRAL",
    "RAIL_CHENNAI_CENTRAL"
  ],
  "candidate_intents": [
    "point_to_point_route"
  ]
}
```

### H02 — point_to_point_route / family_pair

Question: सचिवालय से वॉर मेमोरियल तक बस से कैसे पहुँचूँ?

Category: **recognition mismatch**. Route family matches but both Hindi endpoint names were lost; asks for supplied start/end. Alias/extraction coverage gap, not a routing answer.

HTTP 200; observed request round trip 54.3 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the starting stop, the destination stop.",
  "intent": "point_to_point_route",
  "operation": "PLAN_ROUTE",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "origin",
    "destination"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "point_to_point_route"
  ]
}
```

### H03 — multimodal_route / family_pair

Question: गिंडी से चेन्नई एयरपोर्ट जाने के लिए बस और मेट्रो जोड़कर यात्रा बताइए।

Category: **unsupported source**. Multimodal family and explicit missing confirmed transfer graph match the goal. No factual trip plan.

HTTP 200; observed request round trip 59.8 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "No confirmed cross-mode transfer graph is available in this snapshot.",
  "intent": "multimodal_route",
  "operation": "PLAN_MULTIMODAL_ROUTE",
  "slots": {},
  "data": {
    "reason": "confirmed_multimodal_graph_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "multimodal_route"
  ]
}
```

### H04 — multimodal_route / family_pair

Question: तांबरम से अन्ना नगर तक लोकल ट्रेन और मेट्रो से यात्रा कैसे करूँ?

Category: **recognition mismatch**. Two-mode journey is selected as point-to-point and asks to choose one mode. Slots also contain कल although user wrote लोकल, not a relative day; attribution not repaired.

HTTP 200; observed request round trip 56.5 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please choose one transport mode for this question.",
  "intent": "point_to_point_route",
  "operation": null,
  "slots": {
    "temporal_relative": "कल"
  },
  "data": {
    "requested_modes": [
      "suburban_rail",
      "metro"
    ]
  },
  "missing_slots": [
    "transport_mode"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "point_to_point_route"
  ]
}
```

### H05 — route_stop_sequence / family_pair

Question: बस संख्या १०२ किन-किन स्टॉप पर जाती है, क्रम में नाम बताइए।

Category: **recognition mismatch**. Stop-list intent matches, but explicit बस संख्या १०२ is not retained as route_number; asks for route.

HTTP 200; observed request round trip 54.9 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the route number or line name.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "route_number_or_line_name"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_sequence"
  ]
}
```

### H06 — route_stop_sequence / family_pair

Question: रूट २५आर की बस के पूरे स्टॉपों की सूची दिखाइए।

Category: **successful bounded answer**. Hindi suffix २५आर resolves to 25R; published 25 R stop sequence with source/provisional caveat. Not live operation.

HTTP 200; observed request round trip 54.7 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "25 R stops: Anna Square Bus Terminus one, Madras University, Marina Beach, Kannagi Statue Or Presidency College, Vivekananda House, Ice House Police Station, Meersahibpet Market, New College, …. Published stop sequences found. Service operation is not confirmed.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "bus",
    "route_number": "25R"
  },
  "data": {
    "sequences": [
      {
        "route_id": "GTFS_ROUTE_20163",
        "route_name": "25 R",
        "mode": "bus",
        "direction_id": 0,
        "stops": [
          {
            "sequence": 1,
            "stop_id": "BUS_495",
            "name": "Anna Square Bus Terminus one"
          },
          {
            "sequence": 2,
            "stop_id": "BUS_2413",
            "name": "Madras University"
          },
          {
            "sequence": 3,
            "stop_id": "BUS_2601",
            "name": "Marina Beach"
          },
          {
            "sequence": 4,
            "stop_id": "BUS_5918",
            "name": "Kannagi Statue Or Presidency College"
          },
          {
            "sequence": 5,
            "stop_id": "BUS_5916",
            "name": "Vivekananda House"
          },
          {
            "sequence": 6,
            "stop_id": "BUS_9449",
            "name": "Ice House Police Station"
          },
          {
            "sequence": 7,
            "stop_id": "BUS_9455",
            "name": "Meersahibpet Market"
          },
          {
            "sequence": 8,
            "stop_id": "BUS_9464",
            "name": "New College"
          },
          {
            "sequence": 9,
            "stop_id": "BUS_154",
            "name": "Thousand Light Or Us Embassy"
          },
          {
            "sequence": 10,
            "stop_id": "BUS_5560",
            "name": "M.G.R Salai Nungambakkam Or Palm Grove"
          },
          {
            "sequence": 11,
            "stop_id": "BUS_156",
            "name": "Vetnary Hospital"
          },
          {
            "sequence": 12,
            "stop_id": "BUS_104",
            "name": "Periyar Salai"
          },
          {
            "sequence": 13,
            "stop_id": "BUS_63",
            "name": "Liberty"
          },
          {
            "sequence": 14,
            "stop_id": "BUS_138",
            "name": "Trustpuram"
          },
          {
            "sequence": 15,
            "stop_id": "BUS_111",
            "name": "Power House Kodambakkam"
          },
          {
            "sequence": 16,
            "stop_id": "BUS_120",
            "name": "Saamiyar Madam"
          },
          {
            "sequence": 17,
            "stop_id": "BUS_90",
            "name": "Nagathamman Koil"
          },
          {
            "sequence": 18,
            "stop_id": "BUS_9393",
            "name": "Virugambakkam"
          },
          {
            "sequence": 19,
            "stop_id": "BUS_10235",
            "name": "Alwar Thirunagar"
          },
          {
            "sequence": 20,
            "stop_id": "BUS_9359",
            "name": "Kesavardhini"
          },
          {
            "sequence": 21,
            "stop_id": "BUS_9351",
            "name": "Valasaravakkam"
          },
          {
            "sequence": 22,
            "stop_id": "BUS_9326",
            "name": "Jai Garden"
          },
          {
            "sequence": 23,
            "stop_id": "BUS_9269",
            "name": "Gopala Krishna Theatre"
          },
          {
            "sequence": 24,
            "stop_id": "BUS_5774",
            "name": "Porur"
          },
          {
            "sequence": 25,
            "stop_id": "BUS_5775",
            "name": "Ramachandra Hospital"
          },
          {
            "sequence": 26,
            "stop_id": "BUS_5776",
            "name": "Iyappanthangal"
          },
          {
            "sequence": 27,
            "stop_id": "BUS_5926",
            "name": "Iyyappanthangal Bus Depot"
          },
          {
            "sequence": 28,
            "stop_id": "BUS_5778",
            "name": "Kattupakkam"
          },
          {
            "sequence": 29,
            "stop_id": "BUS_5642",
            "name": "Poonamallee Municipality Or Kumananchavadi"
          },
          {
            "sequence": 30,
            "stop_id": "BUS_5780",
            "name": "Karayanchavadi"
          },
          {
            "sequence": 31,
            "stop_id": "BUS_5781",
            "name": "Kallarai"
          },
          {
            "sequence": 32,
            "stop_id": "BUS_5782",
            "name": "Poonamallee Government Hospital"
          },
          {
            "sequence": 33,
            "stop_id": "BUS_9440",
            "name": "Poonamallee"
          }
        ],
        "source": "CHENNAI_COMMUNITY_GTFS"
      }
    ],
    "truncated": false,
    "provisional": true,
    "partial_topology": false,
    "excluded_unusable_rows": 0,
    "uncovered_route_ids": []
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_sequence"
  ]
}
```

### H07 — route_stop_membership / family_pair

Question: क्या १०२ नंबर बस मरिना बीच स्टॉप पर रुकती है?

Category: **recognition mismatch**. Membership family matches but explicit १०२ नंबर बस is rejected as requiring a supported complete route suffix.

HTTP 200; observed request round trip 53.6 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide a supported route number including its complete suffix.",
  "intent": "route_stop_membership",
  "operation": "CHECK_STOP_ON_ROUTE",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "route_number"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_membership"
  ]
}
```

### H08 — route_stop_membership / family_pair

Question: क्या २१जी बस गिंडी स्टॉप पर ठहरती है?

Category: **legitimate ambiguity**. Membership route21G is preserved; गिंडी has ten bus-stop candidates. No arbitrary stop chosen.

HTTP 200; observed request round trip 53.1 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "route_stop_membership",
  "operation": null,
  "slots": {
    "transport_mode": "bus",
    "route_number": "21G"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_1007625852",
    "BUS_10167",
    "BUS_11200",
    "BUS_11203",
    "BUS_2241055785",
    "BUS_256039818",
    "BUS_3264712327",
    "BUS_3264712469",
    "BUS_5631301427",
    "BUS_CMRL_22"
  ],
  "candidate_intents": [
    "route_stop_membership"
  ]
}
```

### H09 — first_and_last_service / family_pair

Question: आइलैंड ग्राउंड टर्मिनस से १०२ बस की पहली और आखिरी सेवा के समय बताइए।

Category: **recognition mismatch**. First/last family and route102 match; Hindi Island ground Terminus is not retained as a boarding stop.

HTTP 200; observed request round trip 53.6 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the boarding stop or station.",
  "intent": "first_and_last_service",
  "operation": "GET_FIRST_LAST_SERVICE",
  "slots": {
    "transport_mode": "bus",
    "route_number": "102"
  },
  "data": {},
  "missing_slots": [
    "station_or_stop"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H10 — first_and_last_service / family_pair

Question: पूनमल्ली बस टर्मिनस से रूट ६२ की आखिरी बस का निर्धारित समय क्या है?

Category: **recognition mismatch**. Last-service goal becomes scheduled_departure and a multiple-scope clarification despite one stop/route.

HTTP 200; observed request round trip 52.4 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "multiple_goals",
  "response_text": "Please ask about one route, stop, fare stage or time at a time.",
  "intent": "scheduled_departure",
  "operation": null,
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": "multiple_goals",
  "candidate_entities": [],
  "candidate_intents": [
    "scheduled_departure"
  ]
}
```

### H11 — service_frequency / family_pair

Question: आइलैंड ग्राउंड टर्मिनस से रूट १०२ की बस कितने मिनट के अंतराल से चलती है?

Category: **recognition mismatch**. Frequency intent matches but single route/stop question triggers multiple_goals; no headway answer.

HTTP 200; observed request round trip 53.2 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "multiple_goals",
  "response_text": "Please ask about one route, stop, fare stage or time at a time.",
  "intent": "service_frequency",
  "operation": null,
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": "multiple_goals",
  "candidate_entities": [],
  "candidate_intents": [
    "service_frequency"
  ]
}
```

### H12 — service_frequency / family_pair

Question: पूनमल्ली बस टर्मिनस पर ६२ बस की निर्धारित आवृत्ति क्या है?

Category: **recognition mismatch**. Frequency goal becomes scheduled_departure with multiple_goals on a single route/stop question.

HTTP 200; observed request round trip 52.1 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "multiple_goals",
  "response_text": "Please ask about one route, stop, fare stage or time at a time.",
  "intent": "scheduled_departure",
  "operation": null,
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": "multiple_goals",
  "candidate_entities": [],
  "candidate_intents": [
    "scheduled_departure"
  ]
}
```

### H13 — scheduled_departure / family_pair

Question: पूनमल्ली बस टर्मिनस से सुबह नौ बजे के बाद बसों का प्रस्थान समय बताइए।

Category: **recognition mismatch**. After-morning-nine departures request receives first/last bounds00:18:00/25:16:00; requested departure scope is not answered.

HTTP 200; observed request round trip 95.9 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published first departure: 00:18:00; last: 25:16:00 (service-day time). Published schedule bounds; verify current operation with the operator.",
  "intent": "first_and_last_service",
  "operation": "GET_FIRST_LAST_SERVICE",
  "slots": {
    "transport_mode": "bus",
    "station": "BUS_5821"
  },
  "data": {
    "first_departure": "00:18:00",
    "last_departure": "25:16:00",
    "timing_type": null,
    "source": [
      "CHENNAI_COMMUNITY_GTFS"
    ],
    "time_format": "gtfs_service_day",
    "provisional": true
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H14 — scheduled_departure / family_pair

Question: आइलैंड ग्राउंड टर्मिनस से १०२ बस के निर्धारित प्रस्थान 09:30 AM के बाद दिखाइए।

Category: **recognition mismatch**. Departure family/time09:30AM/route102 retained, but supplied Hindi boarding stop is missing.

HTTP 200; observed request round trip 52.3 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the boarding stop or station.",
  "intent": "scheduled_departure",
  "operation": "GET_SCHEDULED_DEPARTURES",
  "slots": {
    "transport_mode": "bus",
    "route_number": "102",
    "time": "09:30:00"
  },
  "data": {},
  "missing_slots": [
    "station_or_stop"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "scheduled_departure"
  ]
}
```

### H15 — mode_availability / family_pair

Question: गिंडी और चेन्नई सेंट्रल के बीच मेट्रो सेवा मिलती है क्या?

Category: **unsupported source**. Mode-availability family matches; metro topology source is absent. No claim that the real metro does not run.

HTTP 200; observed request round trip 53.5 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "No mode-consistent published topology is available for the requested transport mode.",
  "intent": "mode_availability",
  "operation": "CHECK_SERVICE_AVAILABILITY",
  "slots": {
    "transport_mode": "metro",
    "origin": "METRO_GUINDY"
  },
  "data": {
    "reason": "published_mode_topology_absent",
    "transport_mode": "metro"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "mode_availability"
  ]
}
```

### H16 — mode_availability / family_pair

Question: अड्यार से ब्रॉडवे तक सीधी बस सेवा उपलब्ध है क्या?

Category: **recognition mismatch**. Availability family matches but Hindi Adyar/Broadway endpoints are missing from slots.

HTTP 200; observed request round trip 52.7 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the starting stop, the destination stop.",
  "intent": "mode_availability",
  "operation": "CHECK_SERVICE_AVAILABILITY",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "origin",
    "destination"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "mode_availability"
  ]
}
```

### H17 — fare_calculation / family_pair

Question: साधारण बस में स्टेज ८ के लिए कितना किराया लगता है?

Category: **successful bounded answer**. Explicit ordinary stage8 yields INR12, MTC_OFFICIAL, effective2018-01-29, provisional/current-fare caveats.

HTTP 200; observed request round trip 52.4 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published fare (Ordinary Services): INR 12 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "service_type": "Ordinary Services",
    "stage_number": 8
  },
  "data": {
    "amount": 12.0,
    "currency": "INR",
    "stage_number": 8,
    "service_type": "Ordinary Services",
    "effective_date": "2018-01-29",
    "source": "MTC_OFFICIAL",
    "government_order": "G.O (Ms.) No.48 Dated 28.01.2018",
    "provisional": true
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "fare_calculation"
  ]
}
```

### H18 — fare_calculation / family_pair

Question: डीलक्स बस का स्टेज ६ वाला किराया रुपये में बताइए।

Category: **successful bounded answer**. Explicit deluxe stage6 yields INR21 with the dated official source and caveats.

HTTP 200; observed request round trip 54.7 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published fare (Deluxe Services): INR 21 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "service_type": "Deluxe Services",
    "stage_number": 6
  },
  "data": {
    "amount": 21.0,
    "currency": "INR",
    "stage_number": 6,
    "service_type": "Deluxe Services",
    "effective_date": "2018-01-29",
    "source": "MTC_OFFICIAL",
    "government_order": "G.O (Ms.) No.48 Dated 28.01.2018",
    "provisional": true
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "fare_calculation"
  ]
}
```

### H19 — ticketing_and_passes / family_pair

Question: मेट्रो के मासिक पास को खरीदने का नियम बताइए।

Category: **unsupported source**. Ticket/pass family matches; no authoritative policy table.

HTTP 200; observed request round trip 52.2 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "This snapshot contains no authoritative ticket or pass policy table.",
  "intent": "ticketing_and_passes",
  "operation": "GET_TICKETING_POLICY",
  "slots": {},
  "data": {
    "reason": "ticket_policy_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "ticketing_and_passes"
  ]
}
```

### H20 — ticketing_and_passes / family_pair

Question: चेन्नई मेट्रो में एनसीएमसी कार्ड को रिचार्ज कैसे करते हैं?

Category: **unsupported source**. Ticket/pass family matches; policy preflight refuses before extraction. Does not prove NCMC slot recognition.

HTTP 200; observed request round trip 52.1 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "This snapshot contains no authoritative ticket or pass policy table.",
  "intent": "ticketing_and_passes",
  "operation": "GET_TICKETING_POLICY",
  "slots": {},
  "data": {
    "reason": "ticket_policy_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "ticketing_and_passes"
  ]
}
```

### H21 — station_facilities / family_pair

Question: एयरपोर्ट मेट्रो स्टेशन में शौचालय की सुविधा है क्या?

Category: **unsupported source**. Facility family matches; availability is unverified. Preflight does not prove per-station/facility extraction.

HTTP 200; observed request round trip 51.9 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "Facility availability is not verified in this snapshot.",
  "intent": "station_facilities",
  "operation": "GET_STATION_FACILITY",
  "slots": {},
  "data": {
    "reason": "facility_verification_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "station_facilities"
  ]
}
```

### H22 — station_facilities / family_pair

Question: गिंडी मेट्रो स्टेशन पर गाड़ी पार्क करने की जगह उपलब्ध है?

Category: **unsupported source**. Facility family matches; no verified facility answer.

HTTP 200; observed request round trip 52.3 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "Facility availability is not verified in this snapshot.",
  "intent": "station_facilities",
  "operation": "GET_STATION_FACILITY",
  "slots": {},
  "data": {
    "reason": "facility_verification_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "station_facilities"
  ]
}
```

### H23 — station_accessibility / family_pair

Question: गिंडी मेट्रो में व्हीलचेयर के लिए रैंप मौजूद है क्या?

Category: **unsupported source**. Accessibility family matches; no verified values. Preflight does not prove feature-slot parsing.

HTTP 200; observed request round trip 53.7 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "The snapshot contains no verified accessibility feature values.",
  "intent": "station_accessibility",
  "operation": "GET_ACCESSIBILITY_INFO",
  "slots": {},
  "data": {
    "reason": "accessibility_values_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "station_accessibility"
  ]
}
```

### H24 — station_accessibility / family_pair

Question: चेन्नई सेंट्रल मेट्रो स्टेशन में दृष्टिबाधित यात्रियों के लिए स्पर्श पथ हैं क्या?

Category: **unsupported source**. Accessibility family matches; no verified values for a tactile-path request.

HTTP 200; observed request round trip 56.9 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "The snapshot contains no verified accessibility feature values.",
  "intent": "station_accessibility",
  "operation": "GET_ACCESSIBILITY_INFO",
  "slots": {},
  "data": {
    "reason": "accessibility_values_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "station_accessibility"
  ]
}
```

### H25 — interchange_transfer / family_pair

Question: चेन्नई सेंट्रल पर मेट्रो से उपनगरीय ट्रेन में बदलने की जानकारी दीजिए।

Category: **recognition mismatch**. Metro-to-suburban transfer goal selects ticketing_and_passes and an unrelated policy-source refusal.

HTTP 200; observed request round trip 58.0 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "This snapshot contains no authoritative ticket or pass policy table.",
  "intent": "ticketing_and_passes",
  "operation": "GET_TICKETING_POLICY",
  "slots": {},
  "data": {
    "reason": "ticket_policy_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "ticketing_and_passes"
  ]
}
```

### H26 — interchange_transfer / family_pair

Question: गिंडी में बस और मेट्रो के बीच इंटरचेंज कहाँ करना होता है?

Category: **unsupported source**. Interchange family matches; no confirmed interchange records. No transfer instructions invented.

HTTP 200; observed request round trip 53.1 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "The snapshot has no confirmed interchange records.",
  "intent": "interchange_transfer",
  "operation": "GET_INTERCHANGE_DETAILS",
  "slots": {},
  "data": {
    "reason": "confirmed_interchanges_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "interchange_transfer"
  ]
}
```

### H27 — nearest_transport / family_pair

Question: मरिना बीच के सबसे निकट कौन सा मेट्रो स्टेशन पड़ता है?

Category: **recognition mismatch**. Nearest family matches; supplied Hindi Marina Beach name is not retained as anchor.

HTTP 200; observed request round trip 53.9 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide a nearby landmark or locality.",
  "intent": "nearest_transport",
  "operation": "FIND_NEAREST_STATION",
  "slots": {
    "transport_mode": "metro"
  },
  "data": {},
  "missing_slots": [
    "landmark_or_locality"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "nearest_transport"
  ]
}
```

### H28 — nearest_transport / family_pair

Question: आईआईटी मद्रास के पास का निकटतम बस स्टॉप बताइए।

Category: **recognition mismatch**. Nearest family matches; supplied Hindi IIT Madras name is not retained as anchor. No campus inferred in this case.

HTTP 200; observed request round trip 53.4 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide a nearby landmark or locality.",
  "intent": "nearest_transport",
  "operation": "FIND_NEAREST_STATION",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "landmark_or_locality"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "nearest_transport"
  ]
}
```

### H29 — realtime_status_query / family_pair

Question: रूट २५आर की बस का लाइव जीपीएस अभी दिखा सकते हैं?

Category: **unsupported source**. Realtime family selects REJECT_UNSUPPORTED_REALTIME; external_source_required, no live coordinates.

HTTP 200; observed request round trip 53.6 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "external_source_required",
  "response_text": "Live transport status is unavailable; please verify with the operator.",
  "intent": "realtime_status_query",
  "operation": "REJECT_UNSUPPORTED_REALTIME",
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "realtime_status_query"
  ]
}
```

### H30 — realtime_status_query / family_pair

Question: इस समय एयरपोर्ट मेट्रो ट्रेन में भीड़ कितनी है?

Category: **recognition mismatch**. Current crowd question selects service_frequency with metro schedule-source refusal, not realtime refusal.

HTTP 200; observed request round trip 352.1 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "No mode-consistent published schedule is available for the requested transport mode.",
  "intent": "service_frequency",
  "operation": "GET_SERVICE_FREQUENCY",
  "slots": {
    "transport_mode": "metro"
  },
  "data": {
    "reason": "published_mode_schedule_absent",
    "transport_mode": "metro"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "service_frequency"
  ]
}
```

### H31 — out_of_scope / family_pair

Question: आज रात के खाने के लिए पनीर की कोई नई रेसिपी सुझाओ।

Category: **safe guard**. Unrelated recipe correctly selects REJECT_OUT_OF_SCOPE; no transit facts.

HTTP 200; observed request round trip 51.6 ms (single local client, not backend benchmark).

```json
{
  "status": "out_of_scope",
  "outcome_reason": "out_of_scope",
  "response_text": "I can help with Chennai public transport questions.",
  "intent": "out_of_scope",
  "operation": "REJECT_OUT_OF_SCOPE",
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "out_of_scope"
  ]
}
```

### H32 — out_of_scope / family_pair

Question: मुंबई के कल के मौसम का पूर्वानुमान क्या है?

Category: **recognition mismatch**. Mumbai weather goal selects first_and_last_service and कल temporal ambiguity, not outside-scope rejection.

HTTP 200; observed request round trip 52.4 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "temporal_ambiguity",
  "response_text": "Please clarify the time or day you mean.",
  "intent": "first_and_last_service",
  "operation": null,
  "slots": {
    "temporal_relative": "कल"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "temporal_ambiguity",
  "candidate_entities": [],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H33 — fare_calculation / missing_service_class

Question: बस के स्टेज ८ का किराया कितना है?

Category: **successful bounded answer**. No class supplied; API defaults to Ordinary Services for stage8 and explicitly reports that class/source. This is observed default behavior, not a missing-class pass/fail assumption.

HTTP 200; observed request round trip 52.9 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published fare (Ordinary Services): INR 12 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "stage_number": 8
  },
  "data": {
    "amount": 12.0,
    "currency": "INR",
    "stage_number": 8,
    "service_type": "Ordinary Services",
    "effective_date": "2018-01-29",
    "source": "MTC_OFFICIAL",
    "government_order": "G.O (Ms.) No.48 Dated 28.01.2018",
    "provisional": true
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "fare_calculation"
  ]
}
```

### H34 — route_stop_sequence / missing_route

Question: बस के सभी स्टॉप क्रम से लिख दीजिए।

Category: **legitimate ambiguity**. No route/line supplied; stop-list intent asks for the required route/line.

HTTP 200; observed request round trip 52.0 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the route number or line name.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "route_number_or_line_name"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_sequence"
  ]
}
```

### H35 — nearest_transport / missing_anchor

Question: निकटतम मेट्रो स्टेशन का नाम बताइए।

Category: **recognition mismatch**. Anchorless nearest request becomes route_stop_sequence and metro topology refusal rather than anchor clarification.

HTTP 200; observed request round trip 53.1 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "No mode-consistent published topology is available for the requested transport mode.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "metro"
  },
  "data": {
    "reason": "published_mode_topology_absent",
    "transport_mode": "metro"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_sequence"
  ]
}
```

### H36 — fare_calculation / spelled_ordinal

Question: साधारण बस में आठवें स्टेज का किराया बताइए।

Category: **recognition mismatch**. Fare intent/class match but spelled ordinal आठवें is not accepted as stage8; no fare guessed.

HTTP 200; observed request round trip 52.0 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide a fare stage number, or the starting and destination stops.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "service_type": "Ordinary Services"
  },
  "data": {},
  "missing_slots": [
    "origin_or_stage_number",
    "destination_or_stage_number"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "fare_calculation"
  ]
}
```

### H37 — nearest_transport / unknown_anchor

Question: कल्पित नीलकमल चौराहे के पास कौन सा बस स्टॉप है?

Category: **safe guard**. Unknown invented landmark yields missing anchor; no location is fabricated.

HTTP 200; observed request round trip 52.0 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide a nearby landmark or locality.",
  "intent": "nearest_transport",
  "operation": "FIND_NEAREST_STATION",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "landmark_or_locality"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "nearest_transport"
  ]
}
```

### H38 — nearest_transport / entity_ambiguity

Question: सेंट्रल के नजदीक मेट्रो स्टेशन कौन सा है?

Category: **legitimate ambiguity**. Central has three canonical candidates; nearest intent clarifies location.

HTTP 200; observed request round trip 51.4 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "nearest_transport",
  "operation": null,
  "slots": {
    "transport_mode": "metro"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL",
    "HUB_PURATCHI_THALAIVAR_DR__M__G__RAMACHANDRAN_CENTRAL",
    "RAIL_CHENNAI_CENTRAL"
  ],
  "candidate_intents": [
    "nearest_transport"
  ]
}
```

### H39 — scheduled_departure / clock_ambiguity

Question: Poonamallee Bus Terminus से ८ बजे की निर्धारित बसें दिखाइए।

Category: **recognition mismatch**. Bare-eight scheduled departure goal becomes stop-list intent. Intended clock-ambiguity guard not reached.

HTTP 200; observed request round trip 51.9 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the route number or line name.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "route_number_or_line_name"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_sequence"
  ]
}
```

### H40 — scheduled_departure / explicit_morning_clock

Question: Poonamallee Bus Terminus से सुबह ८ बजे के बाद की निर्धारित बसें दिखाइए।

Category: **successful bounded answer**. Explicit Hindi सुबह ८ resolves to08:00:00, stationBUS_5821; five published08:00 departures with schedule caveats.

HTTP 200; observed request round trip 99.7 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published departures: 154 R at 08:00:00, 62 at 08:00:00, 597A R at 08:00:00, 591 at 08:00:00, 49X at 08:00:00 (service-day time). Published departures only; times are not live predictions.",
  "intent": "scheduled_departure",
  "operation": "GET_SCHEDULED_DEPARTURES",
  "slots": {
    "transport_mode": "bus",
    "time": "08:00:00",
    "station": "BUS_5821"
  },
  "data": {
    "departures": [
      {
        "time": "08:00:00",
        "route_id": "GTFS_ROUTE_23733",
        "route_name": "154 R",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "08:00:00",
        "route_id": "GTFS_ROUTE_20088",
        "route_name": "62",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "08:00:00",
        "route_id": "GTFS_ROUTE_22780",
        "route_name": "597A R",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "08:00:00",
        "route_id": "GTFS_ROUTE_12362",
        "route_name": "591",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "08:00:00",
        "route_id": "GTFS_ROUTE_20338",
        "route_name": "49X",
        "source": "CHENNAI_COMMUNITY_GTFS"
      }
    ],
    "time_format": "gtfs_service_day",
    "provisional": true
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "scheduled_departure"
  ]
}
```

### H41 — first_and_last_service / relative_day_ambiguity

Question: कल पूनमल्ली बस टर्मिनस से ६२ बस की पहली सेवा कब है?

Category: **legitimate ambiguity**. Bare कल is temporally ambiguous; first-service route62/station preserved, temporal clarification is appropriate.

HTTP 200; observed request round trip 58.2 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "temporal_ambiguity",
  "response_text": "Please clarify the time or day you mean.",
  "intent": "first_and_last_service",
  "operation": null,
  "slots": {
    "transport_mode": "bus",
    "route_number": "62",
    "timing_type": "first",
    "temporal_relative": "कल",
    "station": "BUS_5821"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "temporal_ambiguity",
  "candidate_entities": [],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H42 — scheduled_departure / invalid_date_time

Question: रूट १०२ के प्रस्थान 2026-02-31 को 27:80 बजे दिखाइए।

Category: **safe guard**. Invalid date2026-02-31/time27:80 yield temporal ambiguity; no malformed schedule answered.

HTTP 200; observed request round trip 53.4 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "temporal_ambiguity",
  "response_text": "Please clarify the time or day you mean.",
  "intent": "scheduled_departure",
  "operation": null,
  "slots": {
    "route_number": "102"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "temporal_ambiguity",
  "candidate_entities": [],
  "candidate_intents": [
    "scheduled_departure"
  ]
}
```

### H43 — route_stop_sequence / multiple_route_scope

Question: १०२ और २१जी दोनों बसों के सभी स्टॉप बताओ।

Category: **recognition mismatch**. Two explicit route scopes return unsupported complete-suffix clarification; requested multi-route guard not established. No stop list silently chooses one.

HTTP 200; observed request round trip 53.5 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide a supported route number including its complete suffix.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [
    "route_number"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_sequence"
  ]
}
```

### H44 — multiple_goals / fare_and_departure

Question: साधारण बस के स्टेज ८ का किराया बताओ और पूनमल्ली से बस के प्रस्थान दिखाओ।

Category: **recognition mismatch**. Explicit fare plus departure goals return only an OK fare; the second goal is dropped without clarification.

HTTP 200; observed request round trip 54.0 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published fare (Ordinary Services): INR 12 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "service_type": "Ordinary Services",
    "stage_number": 8
  },
  "data": {
    "amount": 12.0,
    "currency": "INR",
    "stage_number": 8,
    "service_type": "Ordinary Services",
    "effective_date": "2018-01-29",
    "source": "MTC_OFFICIAL",
    "government_order": "G.O (Ms.) No.48 Dated 28.01.2018",
    "provisional": true
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "fare_calculation"
  ]
}
```

### H45 — scheduled_departure / known_waypoint

Question: चेन्नई सेंट्रल से तांबरम तक गिंडी के रास्ते निर्धारित प्रस्थान बताओ।

Category: **legitimate ambiguity**. Known waypoint query stops at genuine Guindy entity ambiguity. No successful constraint drop. This does not establish Hindi waypoint recognition/refusal coverage.

HTTP 200; observed request round trip 53.3 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "scheduled_departure",
  "operation": null,
  "slots": {
    "station": "RAIL_CHENNAI_CENTRAL"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_1007625852",
    "BUS_10167",
    "BUS_11200",
    "BUS_11203",
    "BUS_2241055785",
    "BUS_256039818",
    "BUS_3264712327",
    "BUS_3264712469",
    "BUS_5631301427",
    "BUS_CMRL_22",
    "HUB_GUINDY",
    "METRO_GUINDY",
    "RAIL_GUINDY"
  ],
  "candidate_intents": [
    "scheduled_departure"
  ]
}
```

### H46 — service_frequency / unknown_waypoint

Question: चेन्नई सेंट्रल से तांबरम तक काल्पनिक सूरज चौक होकर ट्रेन कितनी देर में चलती है?

Category: **legitimate ambiguity**. Frequency contract needs route/line not supplied, so missing-route clarification is legitimate. Unknown Hindi waypoint was not exposed in slots; waypoint guard coverage remains unestablished.

HTTP 200; observed request round trip 52.9 ms (single local client, not backend benchmark).

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the route number or line name.",
  "intent": "service_frequency",
  "operation": "GET_SERVICE_FREQUENCY",
  "slots": {
    "station": "RAIL_CHENNAI_CENTRAL"
  },
  "data": {},
  "missing_slots": [
    "route_number_or_line_name"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "service_frequency"
  ]
}
```

### H47 — route_stop_sequence / punctuation_whitespace_noise

Question (JSON string; whitespace preserved):

```json
"  बस १०२... के स्टॉप???\nकृपया क्रम से बताओ!!  "
```

Category: **successful bounded answer**. Whitespace, newline, punctuation and Hindi102 numeral preserved; route102 stops with partial/provisional caveats.

HTTP 200; observed request round trip 54.3 ms (single local client, not backend benchmark).

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "bus",
    "route_number": "102"
  },
  "data": {
    "sequences": [
      {
        "route_id": "GTFS_ROUTE_24079",
        "route_name": "102",
        "mode": "bus",
        "direction_id": 0,
        "stops": [
          {
            "sequence": 1,
            "stop_id": "BUS_11159",
            "name": "Island ground Terminus"
          },
          {
            "sequence": 2,
            "stop_id": "BUS_9782",
            "name": "High Court"
          },
          {
            "sequence": 3,
            "stop_id": "BUS_9783",
            "name": "Parrys Corner"
          },
          {
            "sequence": 4,
            "stop_id": "BUS_5814",
            "name": "Secretariat"
          },
          {
            "sequence": 5,
            "stop_id": "BUS_5932",
            "name": "War Memorial"
          },
          {
            "sequence": 6,
            "stop_id": "BUS_11192",
            "name": "Annasquare"
          },
          {
            "sequence": 7,
            "stop_id": "BUS_10941",
            "name": "Kannagi Statue Shelter 1"
          },
          {
            "sequence": 8,
            "stop_id": "BUS_2601",
            "name": "Marina Beach"
          },
          {
            "sequence": 9,
            "stop_id": "BUS_5916",
            "name": "Vivekananda House"
          },
          {
            "sequence": 10,
            "stop_id": "BUS_5917",
            "name": "Queen Marys College"
          },
          {
            "sequence": 11,
            "stop_id": "BUS_9318",
            "name": "Nochikuppam"
          },
          {
            "sequence": 12,
            "stop_id": "BUS_9262",
            "name": "Santhome Church"
          },
          {
            "sequence": 13,
            "stop_id": "BUS_247677936",
            "name": "Foreshore Estate Bus Terminus"
          },
          {
            "sequence": 14,
            "stop_id": "BUS_9128",
            "name": "Mrc Nagar"
          },
          {
            "sequence": 15,
            "stop_id": "BUS_10814",
            "name": "Music College Annamalai Puram"
          },
          {
            "sequence": 16,
            "stop_id": "BUS_5758",
            "name": "M.G.R Janaki College Or Sathya Studio"
          },
          {
            "sequence": 17,
            "stop_id": "BUS_5760",
            "name": "Adyar Signal"
          },
          {
            "sequence": 18,
            "stop_id": "BUS_5441",
            "name": "Kamarajar Avenue 2nd Street"
          },
          {
            "sequence": 19,
            "stop_id": "BUS_8924",
            "name": "Shasthri Nagar"
          },
          {
            "sequence": 20,
            "stop_id": "BUS_5914",
            "name": "Jayanthi Theatre"
          },
          {
            "sequence": 21,
            "stop_id": "BUS_11149",
            "name": "Thiruvanmiyur Ration Shop"
          },
          {
            "sequence": 22,
            "stop_id": "BUS_8693",
            "name": "Srp Tools"
          },
          {
            "sequence": 23,
            "stop_id": "BUS_8624",
            "name": "I G P"
          },
          {
            "sequence": 24,
            "stop_id": "BUS_8542",
            "name": "Kandanchavadi"
          },
          {
            "sequence": 25,
            "stop_id": "BUS_8481",
            "name": "Perungudi"
          },
          {
            "sequence": 26,
            "stop_id": "BUS_8425",
            "name": "Seevaram"
          },
          {
            "sequence": 27,
            "stop_id": "BUS_8379",
            "name": "D B Jain College"
          },
          {
            "sequence": 28,
            "stop_id": "BUS_8323",
            "name": "Mettukuppam"
          },
          {
            "sequence": 29,
            "stop_id": "BUS_10066",
            "name": "Ptc Quarters Or Mootakaran Chavadi"
          },
          {
            "sequence": 30,
            "stop_id": "BUS_6686",
            "name": "Okkiyampet"
          },
          {
            "sequence": 31,
            "stop_id": "BUS_6622",
            "name": "Kcg College"
          },
          {
            "sequence": 32,
            "stop_id": "BUS_6579",
            "name": "Karapakkam"
          },
          {
            "sequence": 33,
            "stop_id": "BUS_10031",
            "name": "Dollar Or Accenture"
          },
          {
            "sequence": 34,
            "stop_id": "BUS_10022",
            "name": "Shozhinganallur"
          },
          {
            "sequence": 35,
            "stop_id": "BUS_10012",
            "name": "Government School Shozhinganallur"
          },
          {
            "sequence": 36,
            "stop_id": "BUS_6454",
            "name": "Ponniamman Kovil"
          },
          {
            "sequence": 37,
            "stop_id": "BUS_6420",
            "name": "Kumaran Nagar"
          },
          {
            "sequence": 38,
            "stop_id": "BUS_6403",
            "name": "Satyabhama University"
          },
          {
            "sequence": 39,
            "stop_id": "BUS_6358",
            "name": "Semmancheri"
          },
          {
            "sequence": 40,
            "stop_id": "BUS_6314",
            "name": "Ags Complex Navalur"
          },
          {
            "sequence": 41,
            "stop_id": "BUS_9974",
            "name": "Navalur"
          },
          {
            "sequence": 42,
            "stop_id": "BUS_6269",
            "name": "Egattur"
          },
          {
            "sequence": 43,
            "stop_id": "BUS_9966",
            "name": "It Park Siruseri Or Muttukadu"
          },
          {
            "sequence": 44,
            "stop_id": "BUS_6225",
            "name": "Vaniyanchavadi Padma Adarsh School"
          },
          {
            "sequence": 45,
            "stop_id": "BUS_6198",
            "name": "Kazhipattur"
          },
          {
            "sequence": 46,
            "stop_id": "BUS_6179",
            "name": "Akshaya Padur"
          },
          {
            "sequence": 47,
            "stop_id": "BUS_6157",
            "name": "Padur"
          },
          {
            "sequence": 48,
            "stop_id": "BUS_6150",
            "name": "Hindustan College"
          },
          {
            "sequence": 49,
            "stop_id": "BUS_6132",
            "name": "Chettinad Hospital"
          },
          {
            "sequence": 50,
            "stop_id": "BUS_6125",
            "name": "Kelambakkam V A O Office"
          },
          {
            "sequence": 51,
            "stop_id": "BUS_6099",
            "name": "Kelambakkam Bus Terminal"
          }
        ],
        "source": "CHENNAI_COMMUNITY_GTFS"
      }
    ],
    "truncated": false,
    "provisional": true,
    "partial_topology": true,
    "excluded_unusable_rows": 0,
    "uncovered_route_ids": [
      "GTFS_ROUTE_16861"
    ]
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_sequence"
  ]
}
```

### H48 — out_of_scope / transit_entity_out_of_scope

Question: गिंडी मेट्रो स्टेशन के पास एक जन्मदिन की कविता लिखो।

Category: **recognition mismatch**. Poem request mentioning Guindy metro selects ticketing/pass policy. Transit entity does not make the requested action in scope.

HTTP 200; observed request round trip 52.5 ms (single local client, not backend benchmark).

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "This snapshot contains no authoritative ticket or pass policy table.",
  "intent": "ticketing_and_passes",
  "operation": "GET_TICKETING_POLICY",
  "slots": {},
  "data": {
    "reason": "ticket_policy_absent"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "ticketing_and_passes"
  ]
}
```
