# Chennai Transit Knowledge Base Answerability Matrix (v2 Contract)

Document: `docs/nlp_v2/answerability_matrix.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Database Structure: 19 application tables + SQLite internal `sqlite_sequence`  
Date: 2026-09-19  
Status: Authoritative Reference Contract (Corrected Methodology Patch)

---

## 1. Overview and Allowed Statuses

To prevent model hallucination and preserve factual integrity across all NLU evaluation layers, every user conversational capability is assigned an explicit answerability status under `chennai_multimodal_v1.2.1`.

The canonical database contains 19 application-domain tables (`transport_agencies`, `transport_stops`, `stop_names`, `transport_routes`, `route_stops`, `trips`, `stop_times`, `service_calendars`, `service_exceptions`, `fare_stages`, `fares`, `interchanges`, `walking_transfers`, `transport_hubs`, `hub_members`, `places`, `place_names`, `accessibility`, `entity_source_links`) plus the SQLite internal system table `sqlite_sequence`.

The seven allowed answerability statuses:
1. `ANSWERABLE_NOW`: Supported directly by confirmed ground truth tables (e.g. CMRL operational network, official MTC stage tariffs G.O. Ms 48).
2. `ANSWERABLE_WITH_PROVISIONAL_DATA`: Supported by provisional multisource tables (e.g. community GTFS longest-trip route stops, static timetables, 579 matched bus fare stages, direct spatial coordinate distance lookups). Returned with provisional data version qualification.
3. `ANSWERABLE_AFTER_ROUTING_GRAPH`: Computable once graph traversal and multi-leg route assembly are executed over walkable networks and transfer edges.
4. `ANSWERABLE_AFTER_MANUAL_VERIFICATION`: Depends on candidate relationships currently flagged as unverified (`confirmed=0` or `verified=0`), such as candidate interchanges and walking transfers.
5. `REQUIRES_REALTIME_DATA`: Depends on live vehicle telemetry (GTFS-RT), dynamic headway tracking, or live disruption feeds. The system must refuse deterministically without inventing live coordinates.
6. `NOT_CURRENTLY_SUPPORTED`: Transit information absent from official disclosures or community feeds (e.g. suburban platform allocations, station gate wayfinding, bus stop accessibility, station amenities like cloak rooms or ATMs). The system must report the specific data limitation.
7. `OUT_OF_SCOPE`: Queries outside Chennai Metropolitan Area public transit (e.g. intercity flights, ride-hailing cabs, weather, general conversation). The system triggers domain rejection.

---

## 2. Comprehensive Answerability Matrix

| Candidate Transit Capability | Example User Query | Answerability Status | Underlying DB Tables | Pipeline / Response Contract |
| :--- | :--- | :--- | :--- | :--- |
| **Point-to-Point Route Planning (Single Mode)** | "Central se Airport metro kaise jau?" | `ANSWERABLE_NOW` | `transport_stops`, `route_stops`, `transport_routes` | Return direct route and terminal directions. |
| **Point-to-Point Multimodal Route Planning** | "Tambaram se Anna Nagar via bus aur metro route batao" | `ANSWERABLE_AFTER_ROUTING_GRAPH` | `transport_stops`, `route_stops`, `interchanges` | Compute shortest multimodal path across graph edges. |
| **Route Stop Sequence Listing** | "102 bus kaha kaha rukti hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `route_stops`, `transport_routes`, `transport_stops` | Return ordered stop names from representative longest trip. |
| **Route Stop Membership / Verification** | "Kya 21G bus Guindy se hokar jaati hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `route_stops`, `transport_routes` | Verify if canonical stop ID exists in route sequence. |
| **Scheduled First Service Departure** | "Central se Airport ka first metro kitne baje hai?" | `ANSWERABLE_NOW` (Metro) / `ANSWERABLE_WITH_PROVISIONAL_DATA` (Bus) | `stop_times`, `trips`, `service_calendars` | Return earliest scheduled departure time for requested corridor. |
| **Scheduled Last Service Departure** | "Beach se Tambaram ki aakhiri train kab hai?" | `ANSWERABLE_NOW` (Metro) / `ANSWERABLE_WITH_PROVISIONAL_DATA` (Rail/Bus) | `stop_times`, `trips`, `service_calendars` | Return latest scheduled departure time for requested corridor. |
| **Service Frequency / Headway** | "Green Line metro kitni der me aati hai?" | `ANSWERABLE_NOW` (Metro) / `ANSWERABLE_WITH_PROVISIONAL_DATA` (Bus) | `stop_times`, `trips`, `service_calendars` | Return scheduled headway interval (e.g. every 5 to 10 mins). |
| **Service Availability (Connectivity Check)** | "Guindy se Central metro ya bus chalti hai kya?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `route_stops`, `trips`, `service_calendars` | Confirm scheduled operational connection from GTFS/CMRL tables. |
| **Official MTC Bus Stage Fare** | "MTC Ordinary bus me 5 stages ka kitna kiraya hai?" | `ANSWERABLE_NOW` | `fares` | Return statutory fare amount from G.O. Ms 48 tariff table. |
| **Bus Point-to-Point Fare (Matched Stages)** | "Broadway se Adyar bus ka fare kitna hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `fares`, `fare_stages` | Compute stage delta between matched canonical stages. |
| **Bus Point-to-Point Fare (Unmatched Stages)** | "Rural stop X se Junction Y ka bus kiraya?" | `NOT_CURRENTLY_SUPPORTED` | `fare_stages` (983 unmatched) | Inform user that stage number is unlinked; provide tariff scale. |
| **Metro Point-to-Point Fare** | "Central se Guindy metro ka ticket kitne ka hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | CMRL Distance-Tier Rules | Compute fare via CMRL statutory distance tiers; canonical `fares` table currently holds MTC stage records only. |
| **Station Accessibility (Metro)** | "Kya Guindy metro me wheelchair aur lift hai?" | `ANSWERABLE_NOW` | `accessibility` | Return confirmed lift, escalator, ramp, tactile, and toilet status. |
| **Station Accessibility (Bus / Suburban)** | "Tambaram local station me lift hai kya?" | `NOT_CURRENTLY_SUPPORTED` | `accessibility` (0 rows for bus/rail) | State clearly that accessibility records exist only for Metro. |
| **Station Parking Facility (Metro)** | "Central metro me parking facility hai kya?" | `ANSWERABLE_NOW` | `accessibility.parking_available` | Return confirmed parking availability status for Metro stations. |
| **Other Station Amenities (Waiting rooms, ATMs, Wi-Fi, Cloak rooms, Drinking water)** | "Egmore station me cloak room ya ATM hai kya?" | `NOT_CURRENTLY_SUPPORTED` | None | Inform user that general commercial amenities are not systematically cataloged in current knowledge base. |
| **Southern Railway Station Code Lookup** | "Tambaram station ka railway code kya hai?" | `NOT_CURRENTLY_SUPPORTED` | `transport_stops` (no dedicated code column) | Station codes exist in source IDs/curated metadata, but lack an explicit canonical table column lookup. |
| **Interchange / Transfer Feasibility** | "Central par metro se suburban train badal sakte hain?" | `ANSWERABLE_AFTER_MANUAL_VERIFICATION` | `interchanges`, `hub_members` | Return candidate transfer with estimated distance; qualify as provisional. |
| **Walking Transfer Feasibility** | "Wimco Nagar metro se bus stand tak chalkar ja sakte hain?" | `ANSWERABLE_AFTER_MANUAL_VERIFICATION` | `walking_transfers` | Return straight-line / walk estimate; qualify as unverified walking path. |
| **Nearest Transport (Simple Spatial Coordinates)** | "IIT Madras ke sabse paas kaun sa bus stop hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `places`, `transport_stops` | Direct Euclidean / Haversine spatial proximity lookup over coordinates. |
| **Nearest Transport (Walkable Network / Route-Based)** | "Apollo Hospital se shortest walking route wala metro station?" | `ANSWERABLE_AFTER_ROUTING_GRAPH` | `places`, `transport_stops`, `walking_transfers` | Requires pedestrian network routing graph traversal. |
| **Intermediate Next Stop (Static Topology)** | "Bus 102 me Adyar ke baad agla stop kaun sa hai?" | `ANSWERABLE_WITH_PROVISIONAL_DATA` | `route_stops` | Look up next stop sequence on specified route-direction. |
| **Current Vehicle Location (Live Tracking)** | "102 number bus abhi kahan pahunchi hai?" | `REQUIRES_REALTIME_DATA` | None (telemetry absent) | Intent is `realtime_status_query`; refuse deterministically without live tracking. |
| **Live Delays & Running Status** | "Metro train late hai kya abhi?" | `REQUIRES_REALTIME_DATA` | None (telemetry absent) | Intent is `realtime_status_query`; refuse deterministically: live disruption tracking unavailable. |
| **Real-Time Crowd / Occupancy** | "Central metro me abhi bheed hai kya?" | `REQUIRES_REALTIME_DATA` | None (occupancy absent) | Intent is `realtime_status_query`; refuse deterministically: live crowd tracking unavailable. |
| **Suburban Rail Platform Number** | "Tambaram local train kaun se platform par aayegi?" | `NOT_CURRENTLY_SUPPORTED` | None (rail platform absent) | Inform user platform assignments are displayed at station. |
| **Metro Station Gate / Entrance Exit** | "High Court metro se nikalne ke liye kaun sa gate le?" | `NOT_CURRENTLY_SUPPORTED` | None (gate inventory absent) | Inform user gate wayfinding is not cataloged in knowledge base. |
| **Ticket Booking / Seat Reservation** | "Mere liye 2 metro ticket book kar do" | `NOT_CURRENTLY_SUPPORTED` | None (transaction API absent) | Clarify assistant provides transit guidance, not ticket purchasing. |
| **Ride-Hailing / Cab Services** | "Airport ke liye Uber ya Ola cab book karo" | `OUT_OF_SCOPE` | None | Classify as out-of-scope; transit assistant does not support cabs. |
| **Intercity Flights / Private Buses** | "Delhi ki flight ka status kya hai?" | `OUT_OF_SCOPE` | None | Classify as out-of-scope; transit assistant covers CMA transit. |
| **General Non-Transit Conversations** | "Aaj Chennai me mausam kaisa hai?" | `OUT_OF_SCOPE` | None | Classify as out-of-scope; reject gracefully. |

---

## 3. Strict Rules for Utterance Generation and Evaluation

1. **Semantic Separation of Intent and Capability**:
   The user goal for live tracking queries is `realtime_status_query`. The system capability is `REQUIRES_REALTIME_DATA`. Do not name the intent after system failure (e.g. `unsupported_live_status`). In T1 (Broad), real-time status queries may be pooled with `out_of_scope` for taxonomy comparison; in T2 and T3, they form a distinct intent evaluated for safe refusal.

2. **Negative Sampling for Unsupported Requests**:
   Utterances with intent `realtime_status_query` must NOT be labeled as static fulfillment intents (`route_query`, `service_timing`). They must be evaluated on deterministic refusal accuracy.

3. **Entity Annotation Preservation in Out-of-Scope Queries**:
   Out-of-scope queries that mention real transit locations (e.g. "Order food near Guindy station", "Book Uber from Central") MUST retain entity span and canonical entity annotations. OOS status describes unsupported domain actions, not absence of transit entities.

4. **Qualification Flags on Provisional Retrievals**:
   Any retrieval operation querying `route_stops`, `stop_times`, `interchanges`, unlinked `fare_stages`, or coordinate proximity lookups must tag the response object with `"provisional_data": true` to maintain factual transparency.
