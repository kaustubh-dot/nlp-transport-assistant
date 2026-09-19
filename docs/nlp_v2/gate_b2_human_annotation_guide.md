# Gate B.2 Human Annotation Protocol and Guidelines

**Document:** `docs/nlp_v2/gate_b2_human_annotation_guide.md`  
**Version:** Gate B.2 Pre-Freeze Confirmation Protocol  
**Date:** 2026-09-19  
**Target:** Independent Human Reviewers (R1 and R2)  

---

## 1. Objective of This Annotation Study

You are participating in an independent annotation study to assess the semantic boundaries of two candidate intent taxonomies for the Chennai Multimodal Public Transport Assistant:
1. **T2 Medium Taxonomy (12 Intents)**: A coarser, modular architecture where related operations are grouped under common parent intents.
2. **T3 Fine Taxonomy (16 Intents)**: A fine-grained, direct-dispatch architecture where every distinct downstream operational API is represented as an atomic intent class.

You will annotate a blind challenge sample of **350 utterances** in `data/nlp_v2/gate_b2/human_annotation_blind.csv`. For each query, you will independently assign:
- **`T2_reviewer`**: The best fitting T2 intent (from the 12 defined classes).
- **`T3_reviewer`**: The best fitting T3 intent (from the 16 defined classes).
- **`reviewer_clarification_required`**: `true` if the query is fundamentally ambiguous or underspecified, otherwise `false`.
- **`reviewer_notes`**: Optional observations on linguistic ambiguity or boundary confusion.

---

## 2. Definitive Intent Taxonomy Definitions

### 2.1 T2 Medium Taxonomy (12 Intents)

| T2 Intent Label | Core Semantics | Illustrative Non-Evaluation Examples |
| :--- | :--- | :--- |
| **`route_query`** | Journey planning between origin and destination, single-mode or multimodal. | *"How do I get to Marina from Tambaram?"*, *"Metro route from T Nagar to Egmore"* |
| **`service_timing`** | Schedule inquiries: first/last trains, frequency/headways, or specific departure times. | *"What time does the last train leave?"*, *"How often do buses run on this corridor?"* |
| **`route_stops`** | Stop information along a route: full sequence list or checking if a route halts at a stop. | *"Show all halts on route 102"*, *"Does the 570 bus stop at Sholinganallur?"* |
| **`service_availability`** | Binary check whether direct transit service or a specific mode operates between points. | *"Is direct metro running today between Airport and Central?"*, *"Is there local train service here?"* |
| **`fare_query`** | Fare calculations, ticket prices, and distance-based fare stages. | *"How much is the ticket from Guindy to Airport?"*, *"Kitna lagega metro ka kiraya?"* |
| **`ticketing_rules`** | Ticketing options, smart cards, monthly passes, luggage limits, refund policies. | *"Can I buy a monthly pass on CMRL app?"*, *"Are bicycles permitted inside the train?"* |
| **`station_facilities`** | Amenities at stations/stops: parking, restrooms, ATMs, food stalls, cloakrooms. | *"Is two-wheeler parking available at Alandur?"*, *"Where is the drinking water booth?"* |
| **`accessibility`** | Facilities for disabled commuters, elderly passengers: elevators, ramps, wheelchairs. | *"Is there a lift for wheelchair users at Saidapet?"*, *"Are audio announcements working?"* |
| **`interchange_query`** | Station transfer details: where to switch lines/modes, walking distance, interchange platforms. | *"Where do I switch from Blue Line to Green Line?"*, *"Is there a direct foot overbridge to the railway station?"* |
| **`nearest_transport`** | Finding closest transit stops, metro stations, or bus stands relative to a landmark or GPS point. | *"Where is the nearest bus stand to Express Avenue?"*, *"Nearest metro to the High Court"* |
| **`realtime_status_query`** | Live tracking inquiries: live GPS vehicle location, current delays, crowdedness. | *"Where is bus 21G right now live?"*, *"How crowded is the 9 AM train currently?"* |
| **`out_of_scope`** | Queries unrelated to Chennai transit operations or completely outside system domain. | *"What is the cricket score today?"*, *"Book a hotel room near the airport"* |

---

### 2.2 T3 Fine Taxonomy (16 Intents)

T3 unpacks three coarse T2 classes (`route_query`, `service_timing`, `route_stops`) into direct atomic operations:

| T3 Intent Label | Parent T2 Intent | Core Semantics & Non-Evaluation Examples |
| :--- | :--- | :--- |
| **`point_to_point_route`** | `route_query` | Single-mode or unspecified general point-to-point journey inquiry. (e.g. *"Central se Guindy kaise jaun?"*) |
| **`multimodal_route`** | `route_query` | Explicitly requested multi-mode journey planning combining bus + metro + train. (e.g. *"Give me a combined bus and metro route"*) |
| **`first_and_last_service`** | `service_timing` | Inquiries regarding early morning start or late night terminus runs. (e.g. *"First train in the morning"*, *"Aakhri metro kab niklegi?"*) |
| **`service_frequency`** | `service_timing` | Inquiries regarding headways and dispatch intervals. (e.g. *"Har kitne minute me bus aati hai?"*, *"What is the peak hour frequency?"*) |
| **`scheduled_departure`** | `service_timing` | Specific timetable departure times. (e.g. *"What is the 8:30 PM departure timetable?"*, *"Next train departure time"*) |
| **`route_stop_sequence`** | `route_stops` | Requesting the complete ordered list of halts along a corridor. (e.g. *"Show all halts of 21G from start to end"*) |
| **`route_stop_membership`** | `route_stops` | Checking whether a route stops at a single specific intermediate station. (e.g. *"Does 21G stop at Saidapet?"*) |
| **`mode_availability`** | `service_availability` | Binary check if direct transit is available between two points. |
| **`fare_calculation`** | `fare_query` | Ticket price calculation between origin and destination. |
| **`ticketing_and_passes`** | `ticketing_rules` | Fare policy, passes, smart card recharge, concessions, luggage rules. |
| **`station_facilities`** | `station_facilities` | General amenities (parking, food, ATMs, restrooms). |
| **`station_accessibility`** | `accessibility` | Accessibility provisions (elevators, ramps, wheelchairs, tactile paths). |
| **`interchange_transfer`** | `interchange_query` | Line transfer stations and transfer logistics. |
| **`nearest_transport`** | `nearest_transport` | Locating nearest transit nodes relative to a place or landmark. |
| **`realtime_status_query`** | `realtime_status_query` | Live tracking, live GPS location, crowd density. |
| **`out_of_scope`** | `out_of_scope` | Non-transit questions or out-of-scope inquiries. |

---

## 3. Mandatory Boundary Decision Rules

### Rule 1: Point-to-Point Route vs Multimodal Route
> [!IMPORTANT]
> **Strict Multimodality Rule**:  
> A generic route inquiry (e.g. *"Tambaram se Anna Nagar kaise jau?"* or *"How to travel from Central to OMR?"*) MUST be labeled **`point_to_point_route`** under T3.  
> You must **ONLY** label an utterance as **`multimodal_route`** if the user explicitly uses words indicating a multi-mode combination (e.g. *"bus aur metro dono"*, *"combined train and bus route"*, *"multimodal route"*). Never assume multimodality just because the journey distance might require transfers!

### Rule 2: Route Stop Sequence vs Route Stop Membership
- If the user asks for the full sequence, corridor path, or list of stops (e.g. *"Show me all stops on route 102"*, *"102 ke saare halts dikhao"*), label as **`route_stop_sequence`**.
- If the user asks whether a specific named station is halted at (e.g. *"Does route 102 halt at Adyar?"*, *"Kya 102 Saidapet rukti hai?"*), label as **`route_stop_membership`**.
- Elliptical / shorthand queries like *"21G Guindy?"*: If the phrasing implies "does it go to/stop at Guindy", label as membership and flag `clarification_required = true` if ambiguous.

### Rule 3: Service Timing Subtypes
- If the query mentions first, last, opening, or closing runs (e.g. *"first train"*, *"last metro"*, *"pehli gadi"*, *"aakhri bus"*), label as **`first_and_last_service`**.
- If the query asks about how often, interval, gap, or frequency (e.g. *"how often"*, *"frequency"*, *"har kitni der me"*, *"kitne minute ke interval pe"*), label as **`service_frequency`**.
- If the query asks for a departure timetable at a given hour or next scheduled departure (e.g. *"next bus at 9 AM"*, *"departure timing"*), label as **`scheduled_departure`**.

### Rule 4: Facility vs Accessibility
- General commuter amenities (car/bike parking, drinking water, ATMs, food court, cloakrooms, book stalls) -> **`station_facilities`**.
- Disability / mobility accommodations (wheelchair, ramp, elevator/lift for physically challenged, tactile paving, audio braille) -> **`station_accessibility`** (T3) / **`accessibility`** (T2).

### Rule 5: Realtime Queries vs Static Schedules
- Queries demanding live dynamic GPS positions or live crowd congestion (e.g. *"where is the bus right now live?"*, *"how full is the train currently?"*) -> **`realtime_status_query`**. Note: Chennai transit static feeds do not support live GPS tracking, so these are rejected downstream.

---

## 4. Handling Ambiguity & Clarification Policy

Mark **`reviewer_clarification_required = true`** if:
1. The query is elliptical and cannot be resolved unambiguously without dialogue context (e.g. *"Central to Airport metro?"* could mean route, fare, or schedule).
2. The user names a single location with no verb or operator (e.g. *"Koyambedu CMBT"*).
3. The intent blends two conflicting primary goals equally (e.g. *"What is the fare and schedule for the next bus?"*).

In your notes column, describe the competing interpretations.

---

## 5. Submission Procedure

1. Complete columns `T2_reviewer_1`, `T3_reviewer_1`, `reviewer_1_clarification_required`, `reviewer_1_notes` (for Reviewer 1) or corresponding Reviewer 2 columns in `data/nlp_v2/gate_b2/human_annotation_blind.csv`.
2. Ensure values match the exact canonical intent names listed in Section 2.
3. Save the file. Agreement metrics (Cohen's $\kappa$, raw agreement, boundary confusion matrix) will be computed automatically against the key.
