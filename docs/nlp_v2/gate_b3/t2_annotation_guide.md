# Gate B.3 T2 Intent Annotation Guide

**Document:** `docs/nlp_v2/gate_b3/t2_annotation_guide.md`  
**Taxonomy Version:** T2 (Medium Coarse Taxonomy — 12 Classes)  
**Target Audience:** Semantic Annotators (Student and Model Annotators)  

---

## 1. Purpose and Neutral Semantic Framing

This document provides semantic annotation guidelines for classifying Chennai public transport commuter utterances under the **T2 Medium Intent Taxonomy (12 Classes)**.

Your task is to classify **only the expressed meaning** communicated by the user's natural language surface text.
- Do **not** infer labels based on what journey plan or transit route would physically be optimal in Chennai.
- Classify strictly what the user is asking, requesting, or stating.
- Maintain completely neutral semantic judgment.

---

## 2. T2 Intent Class Definitions

The T2 taxonomy groups transit operations into 12 functional classes:

| Class Name | Definition | Illustrative Non-Evaluation Examples |
| :--- | :--- | :--- |
| **`route_query`** | Inquiries seeking transit directions or journey planning between an origin and destination, whether single-mode, multi-mode, or unspecified. | *"Can you guide me on traveling from Adyar to Anna Nagar?"*, *"Fastest route to reach Koyambedu from Guindy"* |
| **`route_stops`** | Inquiries regarding intermediate stations or bus stops along a designated transit route (stop listings or stop membership checks). | *"List all intermediary stops along bus route 23C"*, *"Does the 570 bus halt at Thoraipakkam?"* |
| **`service_timing`** | Inquiries regarding timetable schedule information, including first/last service hours, service frequency, or scheduled departures. | *"What time does the earliest morning metro train depart?"*, *"How frequently do buses run between Broadway and Tambaram?"* |
| **`service_availability`** | Binary or operational inquiries checking whether transit service or a specific transit mode currently operates on a corridor or date. | *"Are direct suburban trains operating to Chengalpattu today?"*, *"Is there any direct bus operating along this highway?"* |
| **`fare_query`** | Inquiries regarding fare calculation, passenger ticket prices, stage fares, or trip costs. | *"How much is the one-way metro ticket from Central to Airport?"*, *"Kitna paisa lagega local train ticket ka?"* |
| **`ticketing_rules`** | Inquiries regarding fare policies, passes, smartcard recharges, luggage allowances, concessions, and ticketing terms. | *"Where can I renew my monthly suburban rail pass?"*, *"Can passengers carry bicycles inside metro coaches?"* |
| **`station_facilities`** | Inquiries regarding general passenger amenities and infrastructure located at transit stations or bus interchanges. | *"Is two-wheeler parking available at Meenambakkam station?"*, *"Where can I locate a drinking water dispenser at Central?"* |
| **`accessibility`** | Inquiries regarding provisions for disabled, elderly, or mobility-impaired passengers (elevators, ramps, wheelchairs, tactile guides). | *"Does Saidapet metro station have working wheelchair elevators?"*, *"Are there barrier-free ramps available for disabled commuters?"* |
| **`interchange_query`** | Inquiries regarding transferring between lines or modes at designated transit hubs (transfer platforms, walking paths, concourses). | *"How do I transfer from the Blue Line to the Green Line at Alandur?"*, *"Which footbridge connects the suburban station to the metro?"* |
| **`nearest_transport`** | Inquiries seeking the closest transit stop, bus terminus, or railway station relative to a landmark or location. | *"Which is the closest metro station to Kapaleeshwarar Temple?"*, *"Find the nearest MTC bus stop near Express Avenue mall"* |
| **`realtime_status_query`** | Inquiries demanding live, current-state dynamic information such as live vehicle tracking, active delays, or instantaneous crowd levels. | *"What is the live tracking position of bus 21G right now?"*, *"Is the suburban train currently running on time or delayed?"* |
| **`out_of_scope`** | Inquiries completely outside the transit assistant domain or unrelated to Chennai public transportation. | *"What is the weather forecast for Chennai tomorrow?"*, *"Can you recommend a good restaurant in T Nagar?"* |

---

## 3. Crucial Semantic Boundary Rules

### 3.1 Route vs. Service Availability (`route_query` vs. `service_availability`)
- If the user asks **how to travel** from point A to point B, or requests a journey path, label as **`route_query`** (e.g. *"How do I travel to Central from Velachery?"*).
- If the user asks a binary check whether service **exists or operates** between points or on a mode, label as **`service_availability`** (e.g. *"Is there direct train service from Velachery to Beach?"*).

### 3.2 Route vs. Interchange (`route_query` vs. `interchange_query`)
- Inquiries about traveling across town are **`route_query`**.
- Inquiries focusing specifically on **how or where to switch lines/modes at a hub** (e.g. transfer concourses, interchange platforms) are **`interchange_query`** (e.g. *"Where do I switch from Suburban to Metro at Chennai Park?"*).

### 3.3 Facilities vs. Accessibility (`station_facilities` vs. `accessibility`)
- General commuter amenities (parking lots, ATMs, restrooms, luggage cloakrooms, food kiosks) are **`station_facilities`**.
- Specialized provisions for disabled or mobility-impaired commuters (wheelchair ramps, step-free access, tactile paths, disability elevators) are **`accessibility`**.
- If a general feature like an elevator or escalator is asked in a general amenity context without mobility-impairment cues, default to `station_facilities`; if asked with disability or mobility context, label as `accessibility`.

### 3.4 Static Timing vs. Realtime (`service_timing` vs. `realtime_status_query`)
> [!IMPORTANT]
> **Temporal Words Alone Do Not Imply Realtime**:
> Expressions like *"today's last metro"*, *"train at 8 PM"*, or *"morning timetable"* refer to **static timetable information** and MUST be classified as **`service_timing`**.
>
> A query is **`realtime_status_query`** ONLY if it contains explicit current-state dynamic semantics such as:
> - Live GPS coordinates or vehicle location (*"where is the bus right now"*, *"live location"*)
> - Current operational delay or disruption (*"is the train delayed right now"*, *"live status"*)
> - Current vehicle crowdedness (*"is the train crowded right now"*)

### 3.5 Transit-Adjacent vs. Out of Scope (`out_of_scope`)
- Queries seeking general commercial recommendations, non-transit navigation, personal chat, or non-transport tasks are **`out_of_scope`** (e.g. *"Book me a hotel room"*).
- General questions about Chennai transit infrastructure are in-scope.

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
- **Execution Incompleteness (`missing_slot`)**: An inquiry like *"How do I go to Airport?"* has a clear transit intent (`route_query`), but lacks an origin station. This is an execution gap (`missing_slot`), **not** an intent ambiguity. Do not mark `primary_label = null` for clear intents with missing slots.
- **Semantic Ambiguity (`intent_ambiguity`)**: An underspecified inquiry like *"8 baje train?"* is semantically indeterminate between schedule inquiry (`service_timing`), service availability (`service_availability`), or route inquiry (`route_query`). This is genuine `intent_ambiguity`.

### 4.3 Multiple Goals vs. Alternative Interpretations
- When a user explicitly requests two distinct services (e.g. *"Tell me the ticket price and the last metro timetable"*), this is **`multiple_goals`**.
- Both labels should appear in `acceptable_labels: ["fare_query", "service_timing"]`.
- Clarification reason must include `"multiple_goals"`.
