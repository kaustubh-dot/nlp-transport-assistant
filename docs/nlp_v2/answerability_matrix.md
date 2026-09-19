# Chennai Transit Knowledge Base Answerability Matrix (v2 Contract)

Document: `docs/nlp_v2/answerability_matrix.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Reference Contract

---

## 1. Overview and Allowed Statuses

To prevent model hallucination and preserve factual integrity across all NLU evaluation layers, every user conversational capability is assigned an explicit answerability status under `chennai_multimodal_v1.2.1`.

The seven allowed answerability statuses:
1. `ANSWERABLE_NOW`: Supported directly by confirmed ground truth tables (e.g. CMRL operational network, official MTC stage tariffs, Southern Railway station codes).
2. `ANSWERABLE_WITH_PROVISIONAL_DATA`: Supported by provisional multisource tables (e.g. community GTFS longest-trip route stops, static timetables, 579 matched bus fare stages). Must be returned with appropriate data version qualification.
3. `ANSWERABLE_AFTER_ROUTING_GRAPH`: Computable once graph traversal and multi-leg route assembly are executed over canonical nodes and edges.
4. `ANSWERABLE_AFTER_MANUAL_VERIFICATION`: Depends on candidate relationships currently flagged as unverified (`confirmed=0` or `verified=0`), such as candidate interchanges and walking transfers.
5. `REQUIRES_REALTIME_DATA`: Depends on live vehicle telemetry (GTFS-RT), dynamic headway tracking, or live disruption feeds. The system must explicitly refuse with a factual refusal response.
6. `NOT_CURRENTLY_SUPPORTED`: Static transit information that is not cataloged in official disclosures or community feeds (e.g. suburban platform allocations, station gate inventories, bus stop accessibility). The system must state the specific data limitation.
7. `OUT_OF_SCOPE`: Queries outside Chennai Metropolitan Area public transit (e.g. intercity flights, ride-hailing cabs, weather, general conversation). The system must trigger out-of-scope handling.

---

## 2. Comprehensive Answerability Matrix

| Candidate Transit Capability | Example User Query | Answerability Status | Underlying DB Tables | Pipeline / Response Contract |
| :--- | :--- | :--- | :--- | :--- |
| **Point-to-Point Route Planning (Single Mode)** | "Central se Airport metro kaise jau?" | `ANSWERABLE_NOW` | `transport_stops`, `route_stops`, `transport_routes` | Return direct route and terminal directions. |
| **Point-to-Point Multimodal Route Planning** | "Tambaram se Anna Nagar via bus aur metro route batao" | `ANSWERABLE_AFTER_ROUTING_GRAPH` | `transport_stops`, `route_stops`, `interchanges` | Compute shortest multimodal path across graph edges. |
| **Route Stop Sequence Listing** | "102 bus kaha kaha rukti hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `route_stops`, `transport_routes`, `transport_stops` | Return ordered stop names from representative longest trip. |
| **Route Stop Membership / Verification** | "Kya 21G bus Guindy se hokar jaati hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `route_stops`, `transport_routes` | Verify if canonical stop ID exists in route sequence. |
| **First Service Departure** | "Central se Airport ka first metro kitne baje hai?" | `ANSWERABLE_NOW` (Metro) / `ANSWERABLE_WITH_PROVISIONAL_DATA` (Bus) | `stop_times`, `trips`, `service_calendars` | Return earliest scheduled departure time for requested corridor. |
| **Last Service Departure** | "Beach se Tambaram ki aakhiri train kab hai?" | `ANSWERABLE_NOW` (Metro) / `ANSWERABLE_WITH_PROVISIONAL_DATA` (Rail/Bus) | `stop_times`, `trips`, `service_calendars` | Return latest scheduled departure time for requested corridor. |
| **Service Frequency / Headway** | "Green Line metro kitni der me aati hai?" | `ANSWERABLE_NOW` (Metro) / `ANSWERABLE_WITH_PROVISIONAL_DATA` (Bus) | `stop_times`, `trips`, `service_calendars` | Return scheduled headway interval (e.g. every 5 to 10 mins). |
| **Official Stage Fare Lookup** | "MTC Ordinary bus me 5 stages ka kitna kiraya hai?" | `ANSWERABLE_NOW` | `fares` | Return statutory fare amount from G.O. Ms 48 tariff table. |
| **Bus Point-to-Point Fare (Matched Stages)** | "Broadway se Adyar bus ka fare kitna hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `fares`, `fare_stages` | Compute stage delta between matched canonical stages. |
| **Bus Point-to-Point Fare (Unmatched Stages)** | "Rural stop X se Junction Y ka bus kiraya?" | `NOT_CURRENTLY_SUPPORTED` | `fare_stages` (983 unmatched) | Inform user that stage number is unlinked; provide tariff scale. |
| **Metro Distance-Tier Fare** | "Central se Guindy metro ka ticket kitne ka hai?" | `ANSWERABLE_NOW` | `fares` (CMRL rules) | Return verified fixed fare tier (INR 10-50). |
| **Station Accessibility (Metro)** | "Kya Guindy metro me wheelchair aur lift hai?" | `ANSWERABLE_NOW` | `accessibility` | Return confirmed lift, ramp, tactile, and toilet status. |
| **Station Accessibility (Bus / Suburban)** | "Tambaram local station me lift hai kya?" | `NOT_CURRENTLY_SUPPORTED` | `accessibility` (0 rows for bus/rail) | State clearly that accessibility records exist only for Metro. |
| **Interchange / Transfer Feasibility** | "Central par metro se suburban train badal sakte hain?" | `ANSWERABLE_AFTER_MANUAL_VERIFICATION` | `interchanges`, `hub_members` | Return candidate transfer with estimated distance; qualify as provisional. |
| **Walking Transfer Feasibility** | "Wimco Nagar metro se bus stand tak chalkar ja sakte hain?" | `ANSWERABLE_AFTER_MANUAL_VERIFICATION` | `walking_transfers` | Return straight-line / walk estimate; qualify as unverified walking path. |
| **Nearest Transport to Landmark** | "IIT Madras ke sabse paas kaun sa bus stop hai?" | `ANSWERABLE_AFTER_ROUTING_GRAPH` | `places`, `transport_stops` | Spatial Haversine search around landmark coordinates. |
| **Intermediate Next Stop (Static Topology)** | "Bus 102 me Adyar ke baad agla stop kaun sa hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `route_stops` | Look up next stop sequence on specified route-direction. |
| **Current Vehicle Location (Live Tracking)** | "102 number bus abhi kahan pahunchi hai?" | `REQUIRES_REALTIME_DATA` | None (telemetry absent) | Refuse deterministically: live tracking unavailable. |
| **Live Delays & Running Status** | "Metro train late hai kya abhi?" | `REQUIRES_REALTIME_DATA` | None (telemetry absent) | Refuse deterministically: live disruption tracking unavailable. |
| **Real-Time Crowd / Occupancy** | "Central metro me abhi bheed hai kya?" | `REQUIRES_REALTIME_DATA` | None (occupancy absent) | Refuse deterministically: live crowd tracking unavailable. |
| **Suburban Rail Platform Number** | "Tambaram local train kaun se platform par aayegi?" | `NOT_CURRENTLY_SUPPORTED` | None (rail platform absent) | Inform user platform assignments are displayed at station. |
| **Metro Station Gate / Entrance Exit** | "High Court metro se nikalne ke liye kaun sa gate le?" | `NOT_CURRENTLY_SUPPORTED` | None (gate inventory absent) | Inform user gate wayfinding is not cataloged in knowledge base. |
| **Ticket Booking / Seat Reservation** | "Mere liye 2 metro ticket book kar do" | `NOT_CURRENTLY_SUPPORTED` | None (transaction API absent) | Clarify assistant provides transit guidance, not ticket purchasing. |
| **Ride-Hailing / Cab Services** | "Airport ke liye Uber ya Ola cab book karo" | `OUT_OF_SCOPE` | None | Classify as out-of-scope; transit assistant does not support cabs. |
| **Intercity Flights / Private Buses** | "Delhi ki flight ka status kya hai?" | `OUT_OF_SCOPE` | None | Classify as out-of-scope; transit assistant covers CMA transit. |
| **General Non-Transit Conversations** | "Aaj Chennai me mausam kaisa hai?" | `OUT_OF_SCOPE` | None | Classify as out-of-scope; reject gracefully. |

---

## 3. Strict Rules for Utterance Generation and Evaluation

1. **Negative Sampling for Unsupported Requests**:
   Utterances asking for `REQUIRES_REALTIME_DATA` (e.g. "live bus status", "train late hai kya") must NOT be labeled with factual fulfillment intents (`route_query`, `service_timing`). They must be labeled either as `out_of_scope` (if broad taxonomy) or as an explicit `unsupported_live_status` refusal intent, and evaluated on rejection accuracy.

2. **No Hallucinated Slot Annotations**:
   Do not synthesize utterances with slot annotations for `platform_number` or `gate_number` when evaluating factual retrieval, because the canonical database cannot fulfill them.

3. **Qualification Flags on Provisional Retrievals**:
   Any retrieval operation that queries `route_stops`, `stop_times`, `interchanges`, or unlinked `fare_stages` must tag the response object with `"provisional_data": true` to maintain transparent system lineage.
