# Gate B.3 T3 Intent Annotation Guide

**Document:** `docs/nlp_v2/gate_b3/t3_annotation_guide.md`  
**Taxonomy Version:** T3 (Fine-Grained Direct-Dispatch Taxonomy — 16 Classes)  
**Target Audience:** Semantic Annotators (Student and Model Annotators)  

---

## 1. Purpose and Neutral Semantic Framing

This document provides semantic annotation guidelines for classifying Chennai public transport commuter utterances under the **T3 Fine-Grained Intent Taxonomy (16 Classes)**.

Your task is to classify **only the expressed meaning** communicated by the user's natural language surface text.
- Do **not** infer labels based on what journey plan or transit route would physically be optimal in Chennai.
- Classify strictly what the user is asking, requesting, or stating.
- Maintain completely neutral semantic judgment.

---

## 2. T3 Intent Class Definitions

The T3 taxonomy unpacks route inquiries, route stops, and timing operations into 16 direct functional classes:

| Class Name | Definition | Illustrative Non-Evaluation Examples |
| :--- | :--- | :--- |
| **`point_to_point_route`** | Inquiries seeking journey planning between an origin and destination without explicit multi-mode constraints, even if the physical journey may require transfers. | *"How can I travel from Guindy to Central station?"*, *"Best transit route to reach Koyambedu from Tambaram"* |
| **`multimodal_route`** | Inquiries explicitly requesting, constraining, or asking for a combined multi-mode route (e.g. bus + metro, train and bus). | *"Please suggest a combined bus and metro route from Thiruvanmiyur to Kilpauk"*, *"How to reach Airport using both local train and metro?"* |
| **`route_stop_sequence`** | Inquiries requesting the complete ordered list or corridor sequence of stops along a designated route. | *"Show the ordered sequence of all stops on bus route 29C"*, *"Give me the complete list of halts for suburban train route MS-TBM"* |
| **`route_stop_membership`** | Inquiries checking whether a specific stop or station is served by a given transit route. | *"Does the 23C bus stop at Vadapalani junction?"*, *"Will this suburban service halt at Mambalam?"* |
| **`first_and_last_service`** | Inquiries regarding opening, early morning, closing, or late-night service operating limits. | *"What is the departure time of the earliest morning metro train from Airport?"*, *"When does the last night bus leave CMBT?"* |
| **`service_frequency`** | Inquiries regarding service headway, dispatch intervals, or how frequently vehicles run along a corridor. | *"What is the peak hour frequency of trains on the Green Line?"*, *"How many minutes between consecutive buses on route 102?"* |
| **`scheduled_departure`** | Inquiries requesting scheduled timetable departure times at a specific hour or next timetable run. | *"Provide the scheduled 9:15 AM bus timetable from Broadway"*, *"What are the morning departure timings for suburban trains?"* |
| **`mode_availability`** | Binary or operational inquiries checking whether a specific transit mode or direct transit operates on a corridor. | *"Are direct suburban local trains operating between Beach and Tambaram today?"*, *"Is there an operational bus service connecting these two hubs?"* |
| **`fare_calculation`** | Inquiries regarding fare computation, ticket prices, stage fares, or total trip costs. | *"What is the passenger ticket cost from Guindy to Airport?"*, *"How much does a single token cost between Central and Wimco Nagar?"* |
| **`ticketing_and_passes`** | Inquiries regarding ticketing policies, smart card recharges, travel passes, luggage allowances, and concession rules. | *"How can I recharge my CMRL travel pass online?"*, *"Are folding bicycles permitted inside metro carriages?"* |
| **`station_facilities`** | Inquiries regarding general passenger amenities located at transit stations (parking, restrooms, cloakrooms, ATMs, food stalls). | *"Is car parking available at St Thomas Mount station?"*, *"Where can I locate a water fountain at Chennai Central?"* |
| **`station_accessibility`** | Inquiries regarding infrastructure for disabled, elderly, or mobility-impaired passengers (elevators, ramps, wheelchairs, tactile paths). | *"Is there a step-free ramp for wheelchair users at Saidapet?"*, *"Does the station have elevators accessible for physically challenged commuters?"* |
| **`interchange_transfer`** | Inquiries regarding line transfers or mode interchange logistics at hub stations (transfer platforms, walkways, connection concourses). | *"Where do I change trains from the Blue Line to the Green Line at Alandur?"*, *"Which footbridge connects the local train platform to the metro concourse?"* |
| **`nearest_transport`** | Inquiries seeking the closest transit stop, bus shelter, or railway station relative to a landmark or location. | *"Which is the closest metro station to Express Avenue mall?"*, *"Find the nearest bus stop within walking distance of Marina Beach"* |
| **`realtime_status_query`** | Inquiries demanding live, current-state dynamic information (live GPS location, active delays, live vehicle crowding). | *"Where is bus 19B located right now on its live GPS feed?"*, *"Is the suburban train currently running on time or delayed?"* |
| **`out_of_scope`** | Inquiries completely outside the transit assistant domain or unrelated to Chennai public transportation. | *"What is the score in today's cricket match?"*, *"Can you suggest a quiet hotel near Central station?"* |

---

## 3. Mandatory Fine-Grained Boundary Rules

### 3.1 Point-to-Point Route vs. Multimodal Route (`point_to_point_route` vs. `multimodal_route`)
> [!IMPORTANT]
> **Expressed Multimodality Requirement**:
> A journey that may physically or logically require multiple transit modes in Chennai is **NOT** `multimodal_route` unless the user's explicit wording asks for, constrains, or mentions multiple modes.
> - **`point_to_point_route`**: *"How do I get to Sholinganallur from Central?"* (The commuter asks for transit directions. Even if the journey requires a suburban train plus an MTC bus, the user did not specify multimodal constraints).
> - **`multimodal_route`**: *"How to travel from Central to Sholinganallur using both train and bus?"*, *"Suggest a combined metro plus feeder route"* (The commuter explicitly mentions multiple transit modes).

### 3.2 Route Stop Sequence vs. Route Stop Membership (`route_stop_sequence` vs. `route_stop_membership`)
- **`route_stop_sequence`**: The commuter requests the **ordered sequence or full list** of halts (e.g. *"Show all stops on route 102"*, *"List the stop sequence from start to finish"*).
- **`route_stop_membership`**: The commuter inquires whether a **specific named halt is served** by the route (e.g. *"Does bus 102 halt at Adyar?"*, *"Is Saidapet on route 21G?"*).
- Do **not** use route feasibility or database lookup to decide this boundary; decide strictly from whether the inquiry asks for a sequence/list or asks about an individual stop's membership.

### 3.3 Timing Subtypes: `first_and_last_service` vs. `service_frequency` vs. `scheduled_departure`
- **`first_and_last_service`**: Specifically targets operating boundary limits—earliest opening service or latest night termination (e.g. *"When is the first metro in the morning?"*, *"What time does the last bus depart?"*).
- **`service_frequency`**: Specifically targets headways, dispatch rates, or time intervals between vehicles (e.g. *"How often do trains run on this line?"*, *"What is the headway during off-peak hours?"*).
- **`scheduled_departure`**: Targets specific timetable departure moments or schedule tables (e.g. *"What are the afternoon departure timings?"*, *"Timetable for the 10:00 AM train"*).
- An underspecified timing inquiry (e.g. *"Train timings?"*) may legitimately require clarification.

### 3.4 Route vs. Mode Availability (`point_to_point_route` vs. `mode_availability`)
- Journey planning inquiries (*"How to go..."*, *"Directions to..."*) $\rightarrow$ **`point_to_point_route`**.
- Inquiries checking transit existence or operational status between points (*"Is there direct metro service between Airport and Central?"*) $\rightarrow$ **`mode_availability`**.

### 3.5 Facilities vs. Accessibility (`station_facilities` vs. `station_accessibility`)
- General amenities (parking spaces, ATMs, food court, restrooms) $\rightarrow$ **`station_facilities`**.
- Specialized provisions for disabled or mobility-impaired commuters (wheelchair ramps, step-free access, tactile paths, disability elevators) $\rightarrow$ **`station_accessibility`**.

### 3.6 Static Timing vs. Realtime (`scheduled_departure` / `first_and_last_service` vs. `realtime_status_query`)
> [!IMPORTANT]
> **Temporal Words Alone Do Not Imply Realtime**:
> Queries mentioning times or dates (*"today's 9 PM train"*, *"early morning timetable"*) seek static schedule data and belong in timing classes.
>
> A query is **`realtime_status_query`** ONLY if it demands current-state dynamic tracking:
> - Live GPS coordinates (*"live position of bus 21G"*)
> - Current operational delay or disruption (*"live delay status right now"*)
> - Realtime vehicle crowding (*"how crowded is the upcoming coach"*)

---

## 4. Ambiguity and Clarification Policy

### 4.1 Representing Genuine Semantic Ambiguity
Do not force a single primary label where a query is genuinely ambiguous.
- If no single primary label is defensible, set:
  - `primary_label = null`
  - `acceptable_labels = ["candidate_1", "candidate_2"]`
  - `clarification_required = true`
- If a single primary interpretation is preferred but valid secondary interpretations exist:
  - `primary_label = "candidate_1"`
  - `acceptable_labels = ["candidate_1", "candidate_2"]`
  - `clarification_required = false` (or `true` if confirmation is necessary)

### 4.2 Semantic Ambiguity vs. Execution Incompleteness
- **Execution Incompleteness (`missing_slot`)**: An inquiry like *"How do I go to Airport?"* has an unambiguous routing intent (`point_to_point_route`), but lacks an origin station. This is an execution gap (`missing_slot`), **not** an intent ambiguity.
- **Semantic Ambiguity (`intent_ambiguity`)**: An underspecified inquiry like *"8 baje train?"* is semantically indeterminate between a schedule timetable (`scheduled_departure`), service availability (`mode_availability`), or journey route (`point_to_point_route`). This is genuine `intent_ambiguity`.

### 4.3 Multiple Goals vs. Alternative Interpretations
- When a user explicitly requests two distinct operations (e.g. *"Tell me the fare and the last metro departure time"*), classify this as **`multiple_goals`**.
- Both labels should appear in `acceptable_labels: ["fare_calculation", "first_and_last_service"]`.
- Clarification reason must include `"multiple_goals"`.
