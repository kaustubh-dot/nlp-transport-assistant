# Fresh Roman Hindi / Hinglish API product QA

48 independently authored queries: two per each of the 16 intended T3 families (32), plus 16 missing-slot, entity, time, noise, waypoint, multiple-scope and nontransport contrasts. All requests went sequentially to the real local API at http://127.0.0.1:8875/api/v2/query. The default shell sandbox denied local socket access; the authorized local QA script then ran with approved escalation. No evaluator, frozen/dev/held-out cases, training, alias/model/DB edits or app/test edits were used. Only this slice's report artifacts were written.

This is manually scoped product QA, not a representative test sample or model accuracy estimate. An intended family describes the author's purpose; actual API fields are preserved separately. Recognition mismatches, source refusal, ambiguity, and safe guards are distinct. Safe refusal does not establish correct recognition or prove a desired guard ran.

## Findings

The user's exact diagnostic “guindy se central kaise jau” selected point_to_point_route, resolved origin HUB_GUINDY, and returned entity_ambiguity. Central candidates were HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL and HUB_PURATCHI_THALAIVAR_DR__M__G__RAMACHANDRAN_CENTRAL. They differ only by underscore punctuation in the returned identifiers; possible duplicate identities are an inference, not verified equivalence. No canonical data was inspected. This diagnostic is not a Hinglish intent-recognition failure.

Ten cases selected a different family from the manually intended request: H12 frequency→fare, H21 drinking-water facility→interchange, H30 delay→first/last, H31 recipe→route, H32 Java programming→ticket policy, H34 incomplete fare→realtime, H44 frequency waypoint→route stops, H45 departures with a third stop→route stops, H46 competing fare stages→route stops, H48 biryani with Guindy location→interchange. Full intent/operation/status values are below; safe statuses on these cases do not count as intended-operation coverage.

Six bounded published answers were returned for H05/H06 route-stop lists, H07 route membership, H13 scheduled departures and H17/H18 stage fares. Multimodal transfer plans, ticket policy, accessibility, station parking and live status were refused according to actual unsupported-source/external-source reasons. These are capability limits rather than classification failures when the intended intent was selected.

H43's “hote hue” first-train waypoint selected first_and_last_service / GET_FIRST_LAST_SERVICE and explicitly refused waypoint-filtered timetable execution. H44's unknown waypoint did not test frequency execution because the classifier selected route_stop_sequence. H45 similarly did not reach the intended scheduled-departure third-stop guard. H47 recognized route-stop questions, but route extraction stayed empty despite two supplied route codes; it produced missing-route clarification, so the competing-route guard is unconfirmed.

H09 selected the intended first/last family but used a conservative multiple-goal refusal for the natural combined morning-first/night-last question. That is a recorded product limitation, not a claim that the user's wording truly requires two independent operations. H33's missing-endpoint contrast was preempted by metro topology availability. H38's unknown origin was preempted by an entity-ambiguity result. H40's invalid clock and H41's “Kal” day ambiguity produced temporal clarification instead of a time-substituted answer. Punctuation-only H42 returned HTTP 422 / malformed_request.

At this baseline stage, every actual response text is English. This API run does not test UI response-language localization. Browser toggle coverage is pending the coordinator's ready notice and will be recorded separately.

## Recorded categories and statuses

- legitimate ambiguity: 11
- recognition mismatch: 10
- safe guard: 8
- successful bounded answer: 6
- unsupported source: 13

Status counts: clarification=23, error=1, ok=6, unavailable=18. Counts describe only these deliberately chosen examples.

| ID | Exact query | Intended family | Actual intent | Actual operation | Actual status / reason | Category |
| --- | --- | --- | --- | --- | --- | --- |
| H01 | guindy se central kaise jau | point_to_point_route | point_to_point_route | null | clarification / entity_ambiguity | legitimate ambiguity |
| H02 | Tambaram se Egmore bus se jaane ka rasta bata do | point_to_point_route | point_to_point_route | null | clarification / entity_ambiguity | legitimate ambiguity |
| H03 | Airport se Marina Beach tak metro aur bus badal kar kaise pahunchu? | multimodal_route | multimodal_route | PLAN_MULTIMODAL_ROUTE | unavailable / unsupported_source | unsupported source |
| H04 | Chennai Central se Velachery tak pehle suburban train phir bus wala safar batao | multimodal_route | multimodal_route | PLAN_MULTIMODAL_ROUTE | unavailable / unsupported_source | unsupported source |
| H05 | 27D bus ke saare stops ek kram mein dikhao | route_stop_sequence | route_stop_sequence | LIST_ROUTE_STOPS | ok / answered | successful bounded answer |
| H06 | 102 route ka stop sequence shuru se ant tak batao | route_stop_sequence | route_stop_sequence | LIST_ROUTE_STOPS | ok / answered | successful bounded answer |
| H07 | 102 bus Marina Beach par rukti hai kya? | route_stop_membership | route_stop_membership | CHECK_STOP_ON_ROUTE | ok / answered | successful bounded answer |
| H08 | 27D route mein Egmore stop aata hai ya nahi? | route_stop_membership | route_stop_membership | null | clarification / entity_ambiguity | legitimate ambiguity |
| H09 | Guindy metro ki subah pehli aur raat ki aakhri service kitne baje hai? | first_and_last_service | first_and_last_service | null | clarification / multiple_goals | safe guard |
| H10 | Tambaram se nikalne wali pehli train aur aakhiri train ka published time kya hai? | first_and_last_service | first_and_last_service | null | clarification / entity_ambiguity | legitimate ambiguity |
| H11 | Guindy se Central wali metro kitni der ke gap mein chalti hai? | service_frequency | service_frequency | GET_SERVICE_FREQUENCY | unavailable / unsupported_source | unsupported source |
| H12 | 102 bus ki frequency Island ground Terminus par kitni hai? | service_frequency | fare_calculation | CALCULATE_FARE | clarification / missing_execution_slot | recognition mismatch |
| H13 | Island ground Terminus se 102 bus ke scheduled departures 10:00 ke baad dikhao | scheduled_departure | scheduled_departure | GET_SCHEDULED_DEPARTURES | ok / answered | successful bounded answer |
| H14 | Guindy station se Tambaram ki taraf train ka timetable 18:30 ke baad batao | scheduled_departure | scheduled_departure | null | clarification / entity_ambiguity | legitimate ambiguity |
| H15 | Egmore se Tambaram ke beech bus service milti hai kya? | mode_availability | mode_availability | null | clarification / entity_ambiguity | legitimate ambiguity |
| H16 | Airport se Guindy tak metro ka connection available hai? | mode_availability | mode_availability | CHECK_SERVICE_AVAILABILITY | unavailable / unsupported_source | unsupported source |
| H17 | Express bus mein stage 7 ka kiraya kitna padta hai? | fare_calculation | fare_calculation | CALCULATE_FARE | ok / answered | successful bounded answer |
| H18 | Night bus stage 9 ka published fare rupaye mein batao | fare_calculation | fare_calculation | CALCULATE_FARE | ok / answered | successful bounded answer |
| H19 | Metro monthly pass kharidne ke niyam kya hain? | ticketing_and_passes | ticketing_and_passes | GET_TICKETING_POLICY | unavailable / unsupported_source | unsupported source |
| H20 | Chennai suburban train ke season pass kaise milta hai? | ticketing_and_passes | ticketing_and_passes | GET_TICKETING_POLICY | unavailable / unsupported_source | unsupported source |
| H21 | Egmore station par peene ka paani milta hai kya? | station_facilities | interchange_transfer | GET_INTERCHANGE_DETAILS | unavailable / unsupported_source | recognition mismatch |
| H22 | Airport metro station mein parking ki suvidha hai kya? | station_facilities | station_facilities | GET_STATION_FACILITY | unavailable / unsupported_source | unsupported source |
| H23 | Guindy metro mein wheelchair ke liye ramp hai? | station_accessibility | station_accessibility | GET_ACCESSIBILITY_INFO | unavailable / unsupported_source | unsupported source |
| H24 | Tambaram station mein lift se platform tak pahunch sakte hain? | station_accessibility | station_accessibility | GET_ACCESSIBILITY_INFO | unavailable / unsupported_source | unsupported source |
| H25 | Chennai Central par bus se metro mein badalne ki jagah kahan hai? | interchange_transfer | interchange_transfer | GET_INTERCHANGE_DETAILS | unavailable / unsupported_source | unsupported source |
| H26 | Guindy mein suburban train aur metro ka interchange batao | interchange_transfer | interchange_transfer | GET_INTERCHANGE_DETAILS | unavailable / unsupported_source | unsupported source |
| H27 | Kapaleeshwarar Temple ke sabse nazdik bus stop ka naam batao | nearest_transport | nearest_transport | null | clarification / entity_ambiguity | legitimate ambiguity |
| H28 | Besant Nagar ke paas nearest metro station kaun sa padta hai? | nearest_transport | nearest_transport | null | clarification / entity_ambiguity | legitimate ambiguity |
| H29 | 102 bus abhi live kahan chal rahi hai? | realtime_status_query | realtime_status_query | REJECT_UNSUPPORTED_REALTIME | unavailable / external_source_required | unsupported source |
| H30 | Aaj Central se Tambaram train kitni delay hai? | realtime_status_query | first_and_last_service | null | clarification / entity_ambiguity | recognition mismatch |
| H31 | Mujhe nariyal chutney banane ka tarika samjhao | out_of_scope | point_to_point_route | PLAN_ROUTE | clarification / missing_execution_slot | recognition mismatch |
| H32 | Java mein do numbers jodne ka program likh do | out_of_scope | ticketing_and_passes | GET_TICKETING_POLICY | unavailable / unsupported_source | recognition mismatch |
| H33 | Mujhe metro se jaana hai, raasta batao. | point_to_point_route | point_to_point_route | PLAN_ROUTE | unavailable / unsupported_source | unsupported source |
| H34 | Deluxe bus ka kiraya bata do, stage baad mein bolunga. | fare_calculation | realtime_status_query | REJECT_UNSUPPORTED_REALTIME | unavailable / external_source_required | recognition mismatch |
| H35 | Is bus route ke saare stops dikhao | route_stop_sequence | route_stop_sequence | LIST_ROUTE_STOPS | clarification / missing_execution_slot | safe guard |
| H36 | Scheduled departures 16:00 ke baad batao | scheduled_departure | scheduled_departure | GET_SCHEDULED_DEPARTURES | clarification / missing_execution_slot | safe guard |
| H37 | Sabse nazdeek railway station batao | nearest_transport | nearest_transport | FIND_NEAREST_STATION | clarification / missing_execution_slot | safe guard |
| H38 | Zorvix Nagar se Guindy tak bus ka rasta batao | point_to_point_route | point_to_point_route | null | clarification / entity_ambiguity | legitimate ambiguity |
| H39 | Central ke paas nearest metro kaun si hai? | nearest_transport | nearest_transport | null | clarification / entity_ambiguity | legitimate ambiguity |
| H40 | 102 bus ke scheduled departures Island ground Terminus se 28:77 par batao. | scheduled_departure | scheduled_departure | null | clarification / temporal_ambiguity | safe guard |
| H41 | Kal 17:00 ke baad Island ground Terminus se 102 bus kab niklegi? | scheduled_departure | scheduled_departure | null | clarification / temporal_ambiguity | legitimate ambiguity |
| H42 | !!! ??? … 😵 | out_of_scope | null | null | error / malformed_request | safe guard |
| H43 | Guindy se Tambaram tak Egmore hote hue pehli train kab hai? | first_and_last_service | first_and_last_service | GET_FIRST_LAST_SERVICE | unavailable / unsupported_source | safe guard |
| H44 | Chennai Central se Tambaram tak Zafria Chowk hote hue train ki frequency batao | service_frequency | route_stop_sequence | LIST_ROUTE_STOPS | clarification / missing_execution_slot | recognition mismatch |
| H45 | Guindy se Tambaram aur Egmore tak scheduled train departures dikhao | scheduled_departure | route_stop_sequence | LIST_ROUTE_STOPS | clarification / missing_execution_slot | recognition mismatch |
| H46 | Ordinary bus mein stage 6 aur stage 8 dono ka kiraya batao | fare_calculation | route_stop_sequence | LIST_ROUTE_STOPS | clarification / missing_execution_slot | recognition mismatch |
| H47 | 27D aur 102 dono routes ke stops ek saath dikhao | route_stop_sequence | route_stop_sequence | LIST_ROUTE_STOPS | clarification / missing_execution_slot | safe guard |
| H48 | Guindy mein acchi biryani kaise banate hain? | out_of_scope | interchange_transfer | GET_INTERCHANGE_DETAILS | unavailable / unsupported_source | recognition mismatch |

## Exact actual JSON responses

### H01

Exact query: "guindy se central kaise jau"

Manually intended family: point_to_point_route. Contrast: family.

Category: legitimate ambiguity. Route intent and Guindy origin were recognized. Central returned two candidate hub IDs differing only in underscore punctuation; possible duplicate identities are an inference from returned IDs, not verified canonical data.

Actual response (HTTP 200, observed 66.02 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "point_to_point_route",
  "operation": null,
  "slots": {
    "origin": "HUB_GUINDY"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL",
    "HUB_PURATCHI_THALAIVAR_DR__M__G__RAMACHANDRAN_CENTRAL"
  ],
  "candidate_intents": [
    "point_to_point_route"
  ]
}
```

### H02

Exact query: "Tambaram se Egmore bus se jaane ka rasta bata do"

Manually intended family: point_to_point_route. Contrast: family.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 52.3 ms):

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
    "BUS_1173910097",
    "BUS_5275790188",
    "BUS_5286945822",
    "BUS_5329907499",
    "BUS_5553",
    "BUS_9658",
    "BUS_CMRL_G02"
  ],
  "candidate_intents": [
    "point_to_point_route"
  ]
}
```

### H03

Exact query: "Airport se Marina Beach tak metro aur bus badal kar kaise pahunchu?"

Manually intended family: multimodal_route. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 52.98 ms):

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

### H04

Exact query: "Chennai Central se Velachery tak pehle suburban train phir bus wala safar batao"

Manually intended family: multimodal_route. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 52.44 ms):

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

### H05

Exact query: "27D bus ke saare stops ek kram mein dikhao"

Manually intended family: route_stop_sequence. Contrast: family.

Category: successful bounded answer. Intended intent was selected and the API returned a bounded published-snapshot answer.

Actual response (HTTP 200, observed 53.1 ms):

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "27D stops: Ayanavaram Depot, Sayani Theatre Aynavaram, Noor Hotel, Joint Office, Railway Quarters, Kambar Arangam, Icf, Icf. Published stop sequences found. Service operation is not confirmed.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
    "transport_mode": "bus",
    "route_number": "27D"
  },
  "data": {
    "sequences": [
      {
        "route_id": "GTFS_ROUTE_18808",
        "route_name": "27D",
        "mode": "bus",
        "direction_id": 1,
        "stops": [
          {
            "sequence": 1,
            "stop_id": "BUS_9904",
            "name": "Ayanavaram Depot"
          },
          {
            "sequence": 2,
            "stop_id": "BUS_5618",
            "name": "Sayani Theatre Aynavaram"
          },
          {
            "sequence": 3,
            "stop_id": "BUS_5617",
            "name": "Noor Hotel"
          },
          {
            "sequence": 4,
            "stop_id": "BUS_5616",
            "name": "Joint Office"
          },
          {
            "sequence": 5,
            "stop_id": "BUS_5615",
            "name": "Railway Quarters"
          },
          {
            "sequence": 6,
            "stop_id": "BUS_5614",
            "name": "Kambar Arangam"
          },
          {
            "sequence": 7,
            "stop_id": "BUS_5613",
            "name": "Icf"
          },
          {
            "sequence": 8,
            "stop_id": "BUS_5669",
            "name": "Icf"
          }
        ],
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "route_id": "GTFS_ROUTE_10605",
        "route_name": "27D",
        "mode": "bus",
        "direction_id": 1,
        "stops": [
          {
            "sequence": 1,
            "stop_id": "BUS_9904",
            "name": "Ayanavaram Depot"
          },
          {
            "sequence": 2,
            "stop_id": "BUS_5665",
            "name": "Noor Hotel"
          },
          {
            "sequence": 3,
            "stop_id": "BUS_5666",
            "name": "Joint Office"
          },
          {
            "sequence": 4,
            "stop_id": "BUS_5667",
            "name": "Railway Quarters"
          },
          {
            "sequence": 5,
            "stop_id": "BUS_5668",
            "name": "Kambar Arangam"
          },
          {
            "sequence": 6,
            "stop_id": "BUS_5669",
            "name": "Icf"
          },
          {
            "sequence": 7,
            "stop_id": "BUS_5670",
            "name": "Icf Annexe"
          },
          {
            "sequence": 8,
            "stop_id": "BUS_5671",
            "name": "Kallukkadai"
          },
          {
            "sequence": 9,
            "stop_id": "BUS_5672",
            "name": "Kalpana Hotel"
          },
          {
            "sequence": 10,
            "stop_id": "BUS_5817",
            "name": "Villivakkam Bus Stand"
          }
        ],
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "route_id": "GTFS_ROUTE_18780",
        "route_name": "27D",
        "mode": "bus",
        "direction_id": 0,
        "stops": [
          {
            "sequence": 1,
            "stop_id": "BUS_5669",
            "name": "Icf"
          },
          {
            "sequence": 2,
            "stop_id": "BUS_5610",
            "name": "Kalpana Hotel"
          },
          {
            "sequence": 3,
            "stop_id": "BUS_5611",
            "name": "Kallukkadai"
          },
          {
            "sequence": 4,
            "stop_id": "BUS_5612",
            "name": "Icf Annexe"
          },
          {
            "sequence": 5,
            "stop_id": "BUS_5613",
            "name": "Icf"
          },
          {
            "sequence": 6,
            "stop_id": "BUS_5614",
            "name": "Kambar Arangam"
          },
          {
            "sequence": 7,
            "stop_id": "BUS_5615",
            "name": "Railway Quarters"
          },
          {
            "sequence": 8,
            "stop_id": "BUS_5616",
            "name": "Joint Office"
          },
          {
            "sequence": 9,
            "stop_id": "BUS_5617",
            "name": "Noor Hotel"
          },
          {
            "sequence": 10,
            "stop_id": "BUS_5618",
            "name": "Sayani Theatre Aynavaram"
          },
          {
            "sequence": 11,
            "stop_id": "BUS_9904",
            "name": "Ayanavaram Depot"
          }
        ],
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "route_id": "GTFS_ROUTE_18782",
        "route_name": "27D",
        "mode": "bus",
        "direction_id": 0,
        "stops": [
          {
            "sequence": 1,
            "stop_id": "BUS_247677936",
            "name": "Foreshore Estate Bus Terminus"
          },
          {
            "sequence": 2,
            "stop_id": "BUS_5820",
            "name": "Foreshore Estate Bus Stop"
          },
          {
            "sequence": 3,
            "stop_id": "BUS_5644",
            "name": "Kuil Thoppu"
          },
          {
            "sequence": 4,
            "stop_id": "BUS_5645",
            "name": "Employment Office"
          },
          {
            "sequence": 5,
            "stop_id": "BUS_5646",
            "name": "Santhome Church"
          },
          {
            "sequence": 6,
            "stop_id": "BUS_5647",
            "name": "All India Radio Light House"
          },
          {
            "sequence": 7,
            "stop_id": "BUS_5648",
            "name": "D.G.P Office"
          },
          {
            "sequence": 8,
            "stop_id": "BUS_5777",
            "name": "City Centre Or Kalyani Hospital"
          },
          {
            "sequence": 9,
            "stop_id": "BUS_5566",
            "name": "Yellow Pages"
          },
          {
            "sequence": 10,
            "stop_id": "BUS_5582",
            "name": "Avm Rajeshwari Thirumana Mandapam"
          },
          {
            "sequence": 11,
            "stop_id": "BUS_5575",
            "name": "New Woodlands"
          },
          {
            "sequence": 12,
            "stop_id": "BUS_5783",
            "name": "Chola Hotel Or Music Academy"
          },
          {
            "sequence": 13,
            "stop_id": "BUS_5651",
            "name": "Stella Marys College"
          },
          {
            "sequence": 14,
            "stop_id": "BUS_5652",
            "name": "Semmozhi Poonga"
          },
          {
            "sequence": 15,
            "stop_id": "BUS_155",
            "name": "Anand Theatre Or Thousand Light"
          },
          {
            "sequence": 16,
            "stop_id": "BUS_129",
            "name": "Spencer Plaza"
          },
          {
            "sequence": 17,
            "stop_id": "BUS_66",
            "name": "Lic"
          },
          {
            "sequence": 18,
            "stop_id": "BUS_121",
            "name": "Shanthi Theatre"
          },
          {
            "sequence": 19,
            "stop_id": "BUS_5654",
            "name": "Pudupet"
          },
          {
            "sequence": 20,
            "stop_id": "BUS_5655",
            "name": "Egmore Court"
          },
          {
            "sequence": 21,
            "stop_id": "BUS_33",
            "name": "Commissioner Office"
          },
          {
            "sequence": 22,
            "stop_id": "BUS_20",
            "name": "Egmore Station Mmda"
          },
          {
            "sequence": 23,
            "stop_id": "BUS_5748",
            "name": "Egmore Railway Station - South"
          },
          {
            "sequence": 24,
            "stop_id": "BUS_134",
            "name": "T N Sports Authority"
          },
          {
            "sequence": 25,
            "stop_id": "BUS_5757",
            "name": "Dasaprakash Hotel Or Petrol Pump"
          },
          {
            "sequence": 26,
            "stop_id": "BUS_5658",
            "name": "Dharma Prakash Or Mctm School"
          },
          {
            "sequence": 27,
            "stop_id": "BUS_5659",
            "name": "Alagappa Schools"
          },
          {
            "sequence": 28,
            "stop_id": "BUS_5622",
            "name": "Motcham Aysha Hospital Or Motcham Theatre"
          },
          {
            "sequence": 29,
            "stop_id": "BUS_5660",
            "name": "Motcham Theatre Or Grt"
          },
          {
            "sequence": 30,
            "stop_id": "BUS_5661",
            "name": "Abirami Theatre"
          },
          {
            "sequence": 31,
            "stop_id": "BUS_5662",
            "name": "Medavakkam Kellys"
          },
          {
            "sequence": 32,
            "stop_id": "BUS_5663",
            "name": "Medavakkam Mental Hospital"
          },
          {
            "sequence": 33,
            "stop_id": "BUS_5735",
            "name": "E.S.I Hospital Ayanavaram"
          },
          {
            "sequence": 34,
            "stop_id": "BUS_5664",
            "name": "Sayani Theatre Aynavaram"
          },
          {
            "sequence": 35,
            "stop_id": "BUS_5665",
            "name": "Noor Hotel"
          },
          {
            "sequence": 36,
            "stop_id": "BUS_5666",
            "name": "Joint Office"
          },
          {
            "sequence": 37,
            "stop_id": "BUS_5667",
            "name": "Railway Quarters"
          },
          {
            "sequence": 38,
            "stop_id": "BUS_5668",
            "name": "Kambar Arangam"
          },
          {
            "sequence": 39,
            "stop_id": "BUS_5669",
            "name": "Icf"
          }
        ],
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "route_id": "GTFS_ROUTE_20311",
        "route_name": "27D",
        "mode": "bus",
        "direction_id": 1,
        "stops": [
          {
            "sequence": 1,
            "stop_id": "BUS_5669",
            "name": "Icf"
          },
          {
            "sequence": 2,
            "stop_id": "BUS_5610",
            "name": "Kalpana Hotel"
          },
          {
            "sequence": 3,
            "stop_id": "BUS_5611",
            "name": "Kallukkadai"
          },
          {
            "sequence": 4,
            "stop_id": "BUS_5612",
            "name": "Icf Annexe"
          },
          {
            "sequence": 5,
            "stop_id": "BUS_5613",
            "name": "Icf"
          },
          {
            "sequence": 6,
            "stop_id": "BUS_5614",
            "name": "Kambar Arangam"
          },
          {
            "sequence": 7,
            "stop_id": "BUS_5615",
            "name": "Railway Quarters"
          },
          {
            "sequence": 8,
            "stop_id": "BUS_5616",
            "name": "Joint Office"
          },
          {
            "sequence": 9,
            "stop_id": "BUS_5617",
            "name": "Noor Hotel"
          },
          {
            "sequence": 10,
            "stop_id": "BUS_5618",
            "name": "Sayani Theatre Aynavaram"
          },
          {
            "sequence": 11,
            "stop_id": "BUS_5721",
            "name": "E.S.I Hospital Ayanavaram"
          },
          {
            "sequence": 12,
            "stop_id": "BUS_5620",
            "name": "Medavakkam Mental Hospital"
          },
          {
            "sequence": 13,
            "stop_id": "BUS_5621",
            "name": "Medavakkam Kellys"
          },
          {
            "sequence": 14,
            "stop_id": "BUS_5622",
            "name": "Motcham Aysha Hospital Or Motcham Theatre"
          },
          {
            "sequence": 15,
            "stop_id": "BUS_5623",
            "name": "Purasaivakkam Tank"
          },
          {
            "sequence": 16,
            "stop_id": "BUS_5624",
            "name": "Alagappa Schools"
          },
          {
            "sequence": 17,
            "stop_id": "BUS_5625",
            "name": "Dharma Prakash Or Mctm School"
          },
          {
            "sequence": 18,
            "stop_id": "BUS_5754",
            "name": "Dasaprakash Hotel Or Petrol Pump"
          },
          {
            "sequence": 19,
            "stop_id": "BUS_9634",
            "name": "T N Sports Authority"
          },
          {
            "sequence": 20,
            "stop_id": "BUS_5748",
            "name": "Egmore Railway Station - South"
          },
          {
            "sequence": 21,
            "stop_id": "BUS_9640",
            "name": "Albert Theatre"
          },
          {
            "sequence": 22,
            "stop_id": "BUS_9609",
            "name": "Commissioner Office"
          },
          {
            "sequence": 23,
            "stop_id": "BUS_5628",
            "name": "Egmore Court"
          },
          {
            "sequence": 24,
            "stop_id": "BUS_11145",
            "name": "Aadhithanar salai - Pudupet"
          },
          {
            "sequence": 25,
            "stop_id": "BUS_5629",
            "name": "Pudupet"
          },
          {
            "sequence": 26,
            "stop_id": "BUS_122",
            "name": "Shanthi Theatre"
          },
          {
            "sequence": 27,
            "stop_id": "BUS_65",
            "name": "Lic"
          },
          {
            "sequence": 28,
            "stop_id": "BUS_128",
            "name": "Spencer Plaza TVS"
          },
          {
            "sequence": 29,
            "stop_id": "BUS_5630",
            "name": "Anand Theatre Or Thousand Light"
          },
          {
            "sequence": 30,
            "stop_id": "BUS_29",
            "name": "Church Park School"
          },
          {
            "sequence": 31,
            "stop_id": "BUS_154",
            "name": "Thousand Light Or Us Embassy"
          },
          {
            "sequence": 32,
            "stop_id": "BUS_5632",
            "name": "Semmozhi Poonga"
          },
          {
            "sequence": 33,
            "stop_id": "BUS_5633",
            "name": "Stella Marys College"
          },
          {
            "sequence": 34,
            "stop_id": "BUS_5779",
            "name": "Chola Hotel Or Music Academy"
          },
          {
            "sequence": 35,
            "stop_id": "BUS_9384",
            "name": "New Woodlands"
          },
          {
            "sequence": 36,
            "stop_id": "BUS_5635",
            "name": "Avm Rajeshwari Thirumana Mandapam"
          },
          {
            "sequence": 37,
            "stop_id": "BUS_5924",
            "name": "Yellow Pages"
          },
          {
            "sequence": 38,
            "stop_id": "BUS_5765",
            "name": "City Centre Or Kalyani Hospital"
          },
          {
            "sequence": 39,
            "stop_id": "BUS_5637",
            "name": "D.G.P Office"
          },
          {
            "sequence": 40,
            "stop_id": "BUS_5638",
            "name": "All India Radio Light House"
          },
          {
            "sequence": 41,
            "stop_id": "BUS_5639",
            "name": "Santhome Church"
          },
          {
            "sequence": 42,
            "stop_id": "BUS_5640",
            "name": "Employment Office"
          },
          {
            "sequence": 43,
            "stop_id": "BUS_5641",
            "name": "Kuil Thoppu"
          },
          {
            "sequence": 44,
            "stop_id": "BUS_5819",
            "name": "Foreshore Estate Bus Stop"
          },
          {
            "sequence": 45,
            "stop_id": "BUS_247677936",
            "name": "Foreshore Estate Bus Terminus"
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

### H06

Exact query: "102 route ka stop sequence shuru se ant tak batao"

Manually intended family: route_stop_sequence. Contrast: family.

Category: successful bounded answer. Intended intent was selected and the API returned a bounded published-snapshot answer.

Actual response (HTTP 200, observed 53.39 ms):

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {
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

### H07

Exact query: "102 bus Marina Beach par rukti hai kya?"

Manually intended family: route_stop_membership. Contrast: family.

Category: successful bounded answer. Intended intent was selected and the API returned a bounded published-snapshot answer.

Actual response (HTTP 200, observed 53.34 ms):

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "The stop appears on the published route sequence. Published route-stop sequence checked; current service is not confirmed.",
  "intent": "route_stop_membership",
  "operation": "CHECK_STOP_ON_ROUTE",
  "slots": {
    "transport_mode": "bus",
    "route_number": "102",
    "stop": "BUS_2601"
  },
  "data": {
    "on_route": true,
    "route_ids": [
      "GTFS_ROUTE_16861",
      "GTFS_ROUTE_24079"
    ],
    "matched_route_ids": [
      "GTFS_ROUTE_24079"
    ],
    "source": [
      "CHENNAI_COMMUNITY_GTFS"
    ],
    "partial_topology": true,
    "provisional": true,
    "hub_membership_unverified": false
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "route_stop_membership"
  ]
}
```

### H08

Exact query: "27D route mein Egmore stop aata hai ya nahi?"

Manually intended family: route_stop_membership. Contrast: family.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 52.28 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "route_stop_membership",
  "operation": null,
  "slots": {
    "route_number": "27D"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_5275790188",
    "BUS_5329907499",
    "BUS_5553",
    "BUS_9658",
    "BUS_CMRL_G02",
    "METRO_EGMORE_652426199",
    "RAIL_CHENNAI_EGMORE"
  ],
  "candidate_intents": [
    "route_stop_membership"
  ]
}
```

### H09

Exact query: "Guindy metro ki subah pehli aur raat ki aakhri service kitne baje hai?"

Manually intended family: first_and_last_service. Contrast: family.

Category: safe guard. Correct first/last intent, but conservative multiple-goal guard on the natural combined morning-first/night-last question. No useful service-bound answer; this is product friction, not proof that the question truly contains independent goals.

Actual response (HTTP 200, observed 51.3 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "multiple_goals",
  "response_text": "Please ask about one route, stop, fare stage or time at a time.",
  "intent": "first_and_last_service",
  "operation": null,
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": "multiple_goals",
  "candidate_entities": [],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H10

Exact query: "Tambaram se nikalne wali pehli train aur aakhiri train ka published time kya hai?"

Manually intended family: first_and_last_service. Contrast: family.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 52.25 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "first_and_last_service",
  "operation": null,
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_1173910097",
    "BUS_5286945822",
    "RAIL_TAMBARAM"
  ],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H11

Exact query: "Guindy se Central wali metro kitni der ke gap mein chalti hai?"

Manually intended family: service_frequency. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 347.05 ms):

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "No mode-consistent published schedule is available for the requested transport mode.",
  "intent": "service_frequency",
  "operation": "GET_SERVICE_FREQUENCY",
  "slots": {
    "transport_mode": "metro",
    "station": "METRO_GUINDY"
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

### H12

Exact query: "102 bus ki frequency Island ground Terminus par kitni hai?"

Manually intended family: service_frequency. Contrast: family.

Category: recognition mismatch. Selected fare_calculation, while the manually intended family was service_frequency.

Actual response (HTTP 200, observed 51.22 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the starting stop or fare stage number.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "route_number": "102",
    "destination": "BUS_11159"
  },
  "data": {},
  "missing_slots": [
    "origin_or_stage_number"
  ],
  "clarification_reason": "missing_slot",
  "candidate_entities": [],
  "candidate_intents": [
    "fare_calculation"
  ]
}
```

### H13

Exact query: "Island ground Terminus se 102 bus ke scheduled departures 10:00 ke baad dikhao"

Manually intended family: scheduled_departure. Contrast: family.

Category: successful bounded answer. Intended intent was selected and the API returned a bounded published-snapshot answer.

Actual response (HTTP 200, observed 87.57 ms):

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published departures: 102 at 10:05:00, 102 at 13:10:00, 102 at 13:55:00, 102 at 15:20:00, 102 at 16:30:00 (service-day time). Published departures only; times are not live predictions.",
  "intent": "scheduled_departure",
  "operation": "GET_SCHEDULED_DEPARTURES",
  "slots": {
    "transport_mode": "bus",
    "route_number": "102",
    "time": "10:00:00",
    "station": "BUS_11159"
  },
  "data": {
    "departures": [
      {
        "time": "10:05:00",
        "route_id": "GTFS_ROUTE_24079",
        "route_name": "102",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "13:10:00",
        "route_id": "GTFS_ROUTE_24079",
        "route_name": "102",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "13:55:00",
        "route_id": "GTFS_ROUTE_24079",
        "route_name": "102",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "15:20:00",
        "route_id": "GTFS_ROUTE_24079",
        "route_name": "102",
        "source": "CHENNAI_COMMUNITY_GTFS"
      },
      {
        "time": "16:30:00",
        "route_id": "GTFS_ROUTE_24079",
        "route_name": "102",
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

### H14

Exact query: "Guindy station se Tambaram ki taraf train ka timetable 18:30 ke baad batao"

Manually intended family: scheduled_departure. Contrast: family.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 51.49 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "scheduled_departure",
  "operation": null,
  "slots": {
    "time": "18:30:00"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_1007625852",
    "BUS_10167",
    "BUS_11200",
    "BUS_11203",
    "BUS_1173910097",
    "BUS_2241055785",
    "BUS_256039818",
    "BUS_300316947",
    "BUS_3264712327",
    "BUS_3264712469",
    "BUS_5286945822",
    "BUS_5631301427",
    "BUS_CMRL_22",
    "HUB_TAMBARAM",
    "METRO_GUINDY",
    "RAIL_GUINDY",
    "RAIL_TAMBARAM"
  ],
  "candidate_intents": [
    "scheduled_departure"
  ]
}
```

### H15

Exact query: "Egmore se Tambaram ke beech bus service milti hai kya?"

Manually intended family: mode_availability. Contrast: family.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 51.6 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "mode_availability",
  "operation": null,
  "slots": {
    "transport_mode": "bus"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_1173910097",
    "BUS_5275790188",
    "BUS_5286945822",
    "BUS_5329907499",
    "BUS_5553",
    "BUS_9658",
    "BUS_CMRL_G02"
  ],
  "candidate_intents": [
    "mode_availability"
  ]
}
```

### H16

Exact query: "Airport se Guindy tak metro ka connection available hai?"

Manually intended family: mode_availability. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 58.5 ms):

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

### H17

Exact query: "Express bus mein stage 7 ka kiraya kitna padta hai?"

Manually intended family: fare_calculation. Contrast: family.

Category: successful bounded answer. Intended intent was selected and the API returned a bounded published-snapshot answer.

Actual response (HTTP 200, observed 58.4 ms):

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published fare (Express Services): INR 16 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "service_type": "Express Services",
    "stage_number": 7
  },
  "data": {
    "amount": 16.0,
    "currency": "INR",
    "stage_number": 7,
    "service_type": "Express Services",
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

### H18

Exact query: "Night bus stage 9 ka published fare rupaye mein batao"

Manually intended family: fare_calculation. Contrast: family.

Category: successful bounded answer. Intended intent was selected and the API returned a bounded published-snapshot answer.

Actual response (HTTP 200, observed 53.31 ms):

```json
{
  "status": "ok",
  "outcome_reason": "answered",
  "response_text": "Published fare (Night Services): INR 27 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.",
  "intent": "fare_calculation",
  "operation": "CALCULATE_FARE",
  "slots": {
    "transport_mode": "bus",
    "service_type": "Night Services",
    "stage_number": 9
  },
  "data": {
    "amount": 27.0,
    "currency": "INR",
    "stage_number": 9,
    "service_type": "Night Services",
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

### H19

Exact query: "Metro monthly pass kharidne ke niyam kya hain?"

Manually intended family: ticketing_and_passes. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 52.1 ms):

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

### H20

Exact query: "Chennai suburban train ke season pass kaise milta hai?"

Manually intended family: ticketing_and_passes. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 51.56 ms):

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

### H21

Exact query: "Egmore station par peene ka paani milta hai kya?"

Manually intended family: station_facilities. Contrast: family.

Category: recognition mismatch. Selected interchange_transfer, while the manually intended family was station_facilities.

Actual response (HTTP 200, observed 52.26 ms):

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

### H22

Exact query: "Airport metro station mein parking ki suvidha hai kya?"

Manually intended family: station_facilities. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 51.71 ms):

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

### H23

Exact query: "Guindy metro mein wheelchair ke liye ramp hai?"

Manually intended family: station_accessibility. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 52.0 ms):

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

### H24

Exact query: "Tambaram station mein lift se platform tak pahunch sakte hain?"

Manually intended family: station_accessibility. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 51.97 ms):

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

### H25

Exact query: "Chennai Central par bus se metro mein badalne ki jagah kahan hai?"

Manually intended family: interchange_transfer. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 51.93 ms):

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

### H26

Exact query: "Guindy mein suburban train aur metro ka interchange batao"

Manually intended family: interchange_transfer. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 51.12 ms):

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

### H27

Exact query: "Kapaleeshwarar Temple ke sabse nazdik bus stop ka naam batao"

Manually intended family: nearest_transport. Contrast: family.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 53.02 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "nearest_transport",
  "operation": null,
  "slots": {},
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_12458756394",
    "BUS_12458756398",
    "BUS_12512509201",
    "BUS_6057945756",
    "BUS_6518468529",
    "BUS_7255754030"
  ],
  "candidate_intents": [
    "nearest_transport"
  ]
}
```

### H28

Exact query: "Besant Nagar ke paas nearest metro station kaun sa padta hai?"

Manually intended family: nearest_transport. Contrast: family.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 50.81 ms):

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
    "BUS_10914",
    "BUS_417750654",
    "BUS_8912",
    "BUS_8922"
  ],
  "candidate_intents": [
    "nearest_transport"
  ]
}
```

### H29

Exact query: "102 bus abhi live kahan chal rahi hai?"

Manually intended family: realtime_status_query. Contrast: family.

Category: unsupported source. Intended intent was selected; the snapshot/source cannot support the requested answer.

Actual response (HTTP 200, observed 50.81 ms):

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

### H30

Exact query: "Aaj Central se Tambaram train kitni delay hai?"

Manually intended family: realtime_status_query. Contrast: family.

Category: recognition mismatch. Selected first_and_last_service, while the manually intended family was realtime_status_query.

Actual response (HTTP 200, observed 51.27 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "entity_ambiguity",
  "response_text": "Please clarify which stop or location you mean.",
  "intent": "first_and_last_service",
  "operation": null,
  "slots": {
    "temporal_relative": "aaj",
    "station": "RAIL_CHENNAI_CENTRAL"
  },
  "data": {},
  "missing_slots": [],
  "clarification_reason": "entity_ambiguity",
  "candidate_entities": [
    "BUS_1173910097",
    "BUS_5286945822",
    "HUB_TAMBARAM",
    "RAIL_TAMBARAM"
  ],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H31

Exact query: "Mujhe nariyal chutney banane ka tarika samjhao"

Manually intended family: out_of_scope. Contrast: family.

Category: recognition mismatch. Selected point_to_point_route, while the manually intended family was out_of_scope.

Actual response (HTTP 200, observed 50.79 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the starting stop, the destination stop.",
  "intent": "point_to_point_route",
  "operation": "PLAN_ROUTE",
  "slots": {},
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

### H32

Exact query: "Java mein do numbers jodne ka program likh do"

Manually intended family: out_of_scope. Contrast: family.

Category: recognition mismatch. Selected ticketing_and_passes, while the manually intended family was out_of_scope.

Actual response (HTTP 200, observed 50.75 ms):

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

### H33

Exact query: "Mujhe metro se jaana hai, raasta batao."

Manually intended family: point_to_point_route. Contrast: missing endpoints.

Category: unsupported source. Correct route intent; mode capability refusal preceded missing-endpoint clarification. This does not cover the missing-endpoint guard.

Actual response (HTTP 200, observed 53.48 ms):

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "No mode-consistent published topology is available for the requested transport mode.",
  "intent": "point_to_point_route",
  "operation": "PLAN_ROUTE",
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
    "point_to_point_route"
  ]
}
```

### H34

Exact query: "Deluxe bus ka kiraya bata do, stage baad mein bolunga."

Manually intended family: fare_calculation. Contrast: missing fare stage.

Category: recognition mismatch. Selected realtime_status_query, while the manually intended family was fare_calculation.

Actual response (HTTP 200, observed 51.16 ms):

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

### H35

Exact query: "Is bus route ke saare stops dikhao"

Manually intended family: route_stop_sequence. Contrast: missing route.

Category: safe guard. Intended intent was selected; guard/clarification reason is missing_execution_slot.

Actual response (HTTP 200, observed 51.17 ms):

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

### H36

Exact query: "Scheduled departures 16:00 ke baad batao"

Manually intended family: scheduled_departure. Contrast: missing boarding stop.

Category: safe guard. Intended intent was selected; guard/clarification reason is missing_execution_slot.

Actual response (HTTP 200, observed 51.28 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the boarding stop or station.",
  "intent": "scheduled_departure",
  "operation": "GET_SCHEDULED_DEPARTURES",
  "slots": {
    "time": "16:00:00"
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

### H37

Exact query: "Sabse nazdeek railway station batao"

Manually intended family: nearest_transport. Contrast: missing reference locality.

Category: safe guard. Intended intent was selected; guard/clarification reason is missing_execution_slot.

Actual response (HTTP 200, observed 50.83 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide a nearby landmark or locality.",
  "intent": "nearest_transport",
  "operation": "FIND_NEAREST_STATION",
  "slots": {},
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

### H38

Exact query: "Zorvix Nagar se Guindy tak bus ka rasta batao"

Manually intended family: point_to_point_route. Contrast: unknown origin.

Category: legitimate ambiguity. Correct route intent, but ambiguity in a known endpoint can preempt the deliberately unknown origin. This does not prove an unknown-origin-specific guard.

Actual response (HTTP 200, observed 51.36 ms):

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
    "point_to_point_route"
  ]
}
```

### H39

Exact query: "Central ke paas nearest metro kaun si hai?"

Manually intended family: nearest_transport. Contrast: ambiguous Central entity.

Category: legitimate ambiguity. Intended intent was selected; entity_ambiguity requires clarification.

Actual response (HTTP 200, observed 53.82 ms):

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

### H40

Exact query: "102 bus ke scheduled departures Island ground Terminus se 28:77 par batao."

Manually intended family: scheduled_departure. Contrast: invalid clock.

Category: safe guard. Correct scheduled-departure intent; invalid clock 28:77 safely produced temporal clarification, without an answer at a substituted time.

Actual response (HTTP 200, observed 59.07 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "temporal_ambiguity",
  "response_text": "Please clarify the time or day you mean.",
  "intent": "scheduled_departure",
  "operation": null,
  "slots": {
    "transport_mode": "bus",
    "route_number": "102",
    "station": "BUS_11159"
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

### H41

Exact query: "Kal 17:00 ke baad Island ground Terminus se 102 bus kab niklegi?"

Manually intended family: scheduled_departure. Contrast: ambiguous relative day.

Category: legitimate ambiguity. Intended intent was selected; temporal_ambiguity requires clarification.

Actual response (HTTP 200, observed 53.86 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "temporal_ambiguity",
  "response_text": "Please clarify the time or day you mean.",
  "intent": "scheduled_departure",
  "operation": null,
  "slots": {
    "transport_mode": "bus",
    "route_number": "102",
    "time": "17:00:00",
    "temporal_relative": "kal",
    "station": "BUS_11159"
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

### H42

Exact query: "!!! ??? … 😵"

Manually intended family: out_of_scope. Contrast: malformed punctuation noise.

Category: safe guard. Punctuation-only input was rejected as malformed before intent inference.

Actual response (HTTP 422, observed 0.66 ms):

```json
{
  "status": "error",
  "outcome_reason": "malformed_request",
  "response_text": "Please enter a transport question.",
  "intent": null,
  "operation": null,
  "slots": {},
  "data": {
    "reason": "malformed_request"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": []
}
```

### H43

Exact query: "Guindy se Tambaram tak Egmore hote hue pehli train kab hai?"

Manually intended family: first_and_last_service. Contrast: known trailing waypoint.

Category: safe guard. The requested timetable waypoint constraint was preserved and refused as unsupported.

Actual response (HTTP 200, observed 52.24 ms):

```json
{
  "status": "unavailable",
  "outcome_reason": "unsupported_source",
  "response_text": "Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.",
  "intent": "first_and_last_service",
  "operation": "GET_FIRST_LAST_SERVICE",
  "slots": {
    "timing_type": "first"
  },
  "data": {
    "reason": "timetable_waypoint_scope_unsupported"
  },
  "missing_slots": [],
  "clarification_reason": null,
  "candidate_entities": [],
  "candidate_intents": [
    "first_and_last_service"
  ]
}
```

### H44

Exact query: "Chennai Central se Tambaram tak Zafria Chowk hote hue train ki frequency batao"

Manually intended family: service_frequency. Contrast: unknown trailing waypoint.

Category: recognition mismatch. Selected route_stop_sequence, while the manually intended family was service_frequency.

Actual response (HTTP 200, observed 53.31 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the route number or line name.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {},
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

### H45

Exact query: "Guindy se Tambaram aur Egmore tak scheduled train departures dikhao"

Manually intended family: scheduled_departure. Contrast: coordinated third stop.

Category: recognition mismatch. Selected route_stop_sequence, while the manually intended family was scheduled_departure.

Actual response (HTTP 200, observed 52.89 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the route number or line name.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {},
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

### H46

Exact query: "Ordinary bus mein stage 6 aur stage 8 dono ka kiraya batao"

Manually intended family: fare_calculation. Contrast: conflicting fare stages.

Category: recognition mismatch. Selected route_stop_sequence, while the manually intended family was fare_calculation.

Actual response (HTTP 200, observed 52.56 ms):

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

### H47

Exact query: "27D aur 102 dono routes ke stops ek saath dikhao"

Manually intended family: route_stop_sequence. Contrast: conflicting routes.

Category: safe guard. Correct route-stop intent, but both supplied codes failed to populate the route slot; missing-route clarification was safe. Multiple-route scope preservation is not established by this response.

Actual response (HTTP 200, observed 52.65 ms):

```json
{
  "status": "clarification",
  "outcome_reason": "missing_execution_slot",
  "response_text": "Please provide the route number or line name.",
  "intent": "route_stop_sequence",
  "operation": "LIST_ROUTE_STOPS",
  "slots": {},
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

### H48

Exact query: "Guindy mein acchi biryani kaise banate hain?"

Manually intended family: out_of_scope. Contrast: transport-place nontransport contrast.

Category: recognition mismatch. Selected interchange_transfer, while the manually intended family was out_of_scope.

Actual response (HTTP 200, observed 52.14 ms):

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
