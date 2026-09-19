# Knowledge Base Answerability Audit (Phase N1)

Date: 2026-09-19  
Status: Complete  
Knowledge Base Version: `chennai_multimodal_v1.2.1`  
Canonical Database: `data/canonical/transit/canonical_transport.db` (81.27 MB SQLite)  
Starting Reference Commit: `755f5754d9adb2ac7ea8358f5e7ae404ce942909`

---

## 1. Purpose & Audit Scope

This audit systematically evaluates the transit information capabilities of snapshot `chennai_multimodal_v1.2.1` against user conversational goals. 

The primary rule of this NLP research program is:
**Never create training labels or pipeline behaviors that imply factual capability where underlying transit data does not exist.**

An NLU system that accepts a user query such as "Where is bus 102 right now?" and classifies it as an active retrieval intent produces hallucinated outputs. This audit maps what the local transit knowledge base can answer today, what it can answer with provisional data, what requires graph routing or human verification, and what must be refused as unsupported or out-of-scope.

---

## 2. Canonical Knowledge Base Asset Inventory

The audited SQLite database contains 20 relational tables totaling 81.27 MB:

| Relational Table | Row Count | Authoritative Source | Asset Tier | Capability Scope |
| :--- | :--- | :--- | :--- | :--- |
| `transport_agencies` | 4 | CMRL, MTC, SR, MRTS | CONFIRMED | Agency metadata, operating jurisdiction |
| `transport_stops` | 7,136 | CMRL API, Community GTFS, OSM | CONFIRMED / PROVISIONAL | Physical stops: 41 Metro, 107 Suburban, 19 MRTS, 6,870 Bus stops |
| `stop_names` | 7,571 | CMRL, GTFS, OSM | CONFIRMED / PROVISIONAL | Multilingual aliases: English (7,136), Tamil (421), Hindi (14) |
| `transport_routes` | 4,619 | CMRL API, Community GTFS | PROVISIONAL | 2 Metro lines, 4,614 bus route operational variants, 3 rail corridors |
| `route_stops` | 96,025 | Community GTFS | PROVISIONAL | Representative longest-trip topology per route-direction |
| `trips` | 47,143 | Community GTFS | PROVISIONAL | Operational scheduled trips linked to service calendars |
| `stop_times` | 1,360,635 | Community GTFS | PROVISIONAL | Static scheduled arrival/departure times at stop sequences |
| `service_calendars` | 9 | Community GTFS | PROVISIONAL | Weekly service patterns (Regular, Weekend, Special) |
| `service_exceptions` | 0 | Community GTFS | PROVISIONAL | Feed omits `calendar_dates.txt`; zero service exceptions recorded |
| `fare_stages` | 1,562 | Official MTC Disclosures | CONFIRMED / PROVISIONAL | 1,562 official fare stages; 579 linked to canonical stop IDs |
| `fares` | 305 | Official Tamil Nadu Gazette (G.O. Ms 48) | CONFIRMED | Statutory stage fare tariffs across 11 bus service types |
| `interchanges` | 45 | Spatial clustering (<250m) | UNVERIFIED (`confirmed=0`) | Transfer feasibility candidates between metro/rail/bus |
| `walking_transfers` | 151 | Spatial clustering (<150m) | UNVERIFIED (`walkable=unverified`) | Candidate pedestrian transfers across roads/tracks |
| `transport_hubs` | 62 | Spatial clustering & topology | UNVERIFIED (`verified=0`) | 62 provisional multimodal hubs (211 member entities) |
| `hub_members` | 211 | Spatial clustering | UNVERIFIED (`verified=0`) | Stop memberships linked to hub entities |
| `places` | 1,621 | OSM Overpass | PROVISIONAL | POIs, hospitals, colleges, tech parks, shopping centers |
| `place_names` | 1,670 | OSM Overpass | PROVISIONAL | English and Tamil names for CMA POIs |
| `accessibility` | 41 | CMRL Official API | CONFIRMED (Metro only) | Lifts, escalators, ramps, tactile paths, wheelchair toilets for 41 Metro stations |
| `entity_source_links` | 9,695 | Ingestion lineage | PROVISIONAL | 7,246 stop source links + 2,449 route source links |
| `sqlite_sequence` | 5 | Internal SQLite | SYSTEM | Auto-increment sequences |

---

## 3. Detailed Capability Assessment by Transit Domain

### 3.1 Route Stop Listing & Topology
- Available Data: `route_stops` contains 96,025 rows representing the ordered stop sequence for every commercial route-direction.
- Capability:
  - The system can answer: "What stops does bus 102 pass through?", "Does route 21G stop at Guindy?", "Which metro line serves Vadapalani?".
  - It can determine intermediate stops between two named points on the same route.
- Qualification & Limitation:
  - `route_stops` stores the **longest representative trip topology**. Route branches, short-working trips, and express skip-stop variants are not modeled separately (`route_patterns` deferred).
  - Queries expecting exact pattern variations (e.g. "Does 102 cut short at Sholinganallur?") cannot be verified deterministically.

### 3.2 Scheduled Service Timings & Operating Spans
- Available Data: `stop_times` contains 1,360,635 records; `trips` contains 47,143 records; `service_calendars` contains 9 active weekly patterns.
- Capability:
  - The system can answer: "What is the first metro from Central to Airport?", "What is the scheduled departure of the last train from Beach to Tambaram?", "What is the scheduled frequency of Green Line metro during morning hours?".
- Qualification & Limitation:
  - These are **scheduled static timetable entries** from the community GTFS feed.
  - Indian Railways suburban timetables are static approximations from OSM/GTFS, not official live CRIS/IRCTC feeds.
  - The community GTFS lacks `calendar_dates.txt` (`service_exceptions` has 0 rows); holiday variations cannot be computed.

### 3.3 Statutory Fares & Stage Fares
- Available Data: `fares` contains 305 rows from official G.O. Ms No. 48 across 11 service types (Ordinary, Express, Deluxe, Night, AC, etc.); `fare_stages` contains 1,562 official MTC stages, of which 579 are linked to canonical GTFS bus stops. CMRL distance-tier fare rules are verified.
- Capability:
  - The system can answer: "What is the Ordinary bus fare for 5 stages?", "What is the Deluxe fare for stage 12?", "What is the minimum metro token fare?".
  - It can compute point-to-point bus fares between the 579 matched stages.
- Qualification & Limitation:
  - 983 official fare stages (62.93%) remain unlinked to physical GTFS stops because they refer to administrative junctions or rural staging posts absent in community bus stop coordinates.
  - If a user asks for a bus fare between two stops where one is unlinked to an official stage, the system cannot compute the exact bus fare. It must refuse or report estimated stage distance rather than inventing an arbitrary fare.

### 3.4 Multimodal Transfers & Interchange Guidance
- Available Data: 45 candidate interchanges, 151 walking transfer pairs, and 62 provisional multimodal hubs.
- Capability:
  - The system can identify candidate transfers at the 10 Tier-1 Core Hubs (Central, Egmore, Guindy, Airport, Tambaram, CMBT, Beach, Alandur, St. Thomas Mount, Velachery).
- Qualification & Limitation:
  - Every candidate interchange in `canonical_transport.db` has `confirmed = 0` and every hub has `verified = 0`.
  - Pedestrian walking paths have not undergone physical ground audits (some walking candidates cross active rail tracks or fenced arterial dividers).
  - The system must qualify transfer advice as provisional: "Provisional transfer candidate: walking distance estimated at ~85m." It must not claim surveyed physical walkways.

### 3.5 Accessibility Amenities
- Available Data: `accessibility` contains 41 confirmed rows covering 100% of operational CMRL metro stations.
- Capability:
  - The system can answer: "Is wheelchair assistance available at Guindy Metro?", "Does Egmore Metro have a lift?", "Are tactile paths installed at Central Metro?".
- Qualification & Limitation:
  - Bus stops (6,870 stops) and Suburban railway halts have **zero accessibility disclosures**.
  - The system must explicitly state: "Accessibility data is verified for CMRL Metro stations; accessibility information is not currently recorded for MTC bus stops or Suburban rail platforms."

### 3.6 Landmarks, Localities & POIs
- Available Data: `places` contains 1,621 canonical POIs inside and adjacent to the CMA; `place_names` contains 1,670 names.
- Capability:
  - The system can resolve landmark and locality references: "Which bus goes to IIT Madras?", "Nearest station to Apollo Hospital Greams Road".
- Qualification & Limitation:
  - Proximity queries ("nearest transport") require an explicit reference entity (landmark, locality, or POI). The system does not possess the user's GPS device coordinates.

### 3.7 Critical Absent Capabilities (Strict Boundaries)
Underlying sources do NOT support:
1. Live vehicle tracking: No GPS telemetry, GTFS-RT feed, or live bus coordinates exist.
2. Real-time delays & disruptions: No live incident or headway monitoring feed is integrated.
3. Platform and gate numbers: Suburban rail platform allocations and CMRL station gate numbers are not systematically cataloged.
4. Ticket purchasing and transactions: The assistant does not interface with UTS, CMRL WhatsApp ticketing, or banking gateways.
5. Private transport modes: Autos, cabs, ride-hailing (Ola, Uber, Rapido), and intercity private buses are not in the transport database.

---

## 4. Operational Classification Criteria for Taxonomy Design

Every candidate intent and capability in Phase N2 must be evaluated against this knowledge base audit:

1. If an intent requires data classified as CONFIRMED:
   Assign status `ANSWERABLE_NOW`.
2. If an intent requires data classified as PROVISIONAL (e.g. GTFS longest-trip topology, static stop times, 579 matched fare stages):
   Assign status `ANSWERABLE_WITH_PROVISIONAL_DATA`.
3. If an intent requires multi-hop pathfinding across graph edges:
   Assign status `ANSWERABLE_AFTER_ROUTING_GRAPH`.
4. If an intent depends on UNVERIFIED candidate relationships (interchanges, walking transfers, hubs):
   Assign status `ANSWERABLE_AFTER_MANUAL_VERIFICATION`.
5. If an intent relies on dynamic bus telemetry or live train tracking:
   Assign status `REQUIRES_REALTIME_DATA` (System must refuse with factual refusal template).
6. If an intent asks for static data absent from all feeds (gate numbers, suburban platform numbers, bus stop accessibility):
   Assign status `NOT_CURRENTLY_SUPPORTED` (System must clarify data limitation).
7. If an intent requests services outside Chennai CMA public transit (weather, food, ride-hailing, flights, jokes):
   Assign status `OUT_OF_SCOPE` (System must politely reject or redirect).
