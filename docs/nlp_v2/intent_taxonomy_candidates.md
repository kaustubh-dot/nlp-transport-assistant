# Intent Taxonomy Candidates for Chennai Multimodal Transport NLU (Phase N2)

Document: `docs/nlp_v2/intent_taxonomy_candidates.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Proposal for Gate A Review & Phase N8 Consolidation

---

## 1. Intent Taxonomy Design Philosophy

The historical 7-intent CMRL benchmark was developed for a single operator network with 41 underground and elevated metro stations. In that setting, intents like `station_information` and `service_timing` were sufficient because routing was trivial (two intersecting lines) and fares were simple distance matrices.

In the Chennai multimodal network, commuters interact with 7,136 bus stops, 4,619 bus route variants, 126 suburban and MRTS railway stations, 1,562 bus fare stages, and multimodal transfer hubs. 

To determine the appropriate intent taxonomy, an intent must satisfy four criteria:
1. **Distinct User Goal**: Represents a distinct communicative objective from the passenger's perspective.
2. **Linguistic Separability**: Has distinct lexical, syntactic, and semantic markers in English, Hindi, and Hinglish that a classifier can learn without chronic confusion.
3. **Downstream Action**: Triggers a distinct database query, computation, or policy workflow.
4. **Factual Answerability**: Maps to information that `canonical_transport.db` can either fulfill or explicitly refuse.

Where a distinction can be represented as an attribute (slot) without altering the downstream query pattern, we favor the slot representation to prevent intent fragmentation.

---

## 2. Candidate Taxonomy Architectures

We specify three alternative taxonomies representing Broad (T1), Medium (T2), and Fine (T3) granularity.

```
TAXONOMY GRANULARITY SPECTRUM:

T1 (Broad: 9 Intents)          T2 (Medium: 12 Intents)         T3 (Fine: 16 Intents)
-----------------------------------------------------------------------------------------
route_query                 -> route_query                  -> point_to_point_route
                                                            -> multimodal_route
route_stops                 -> route_stops                  -> route_stop_sequence
                                                            -> route_stop_membership
service_timing              -> service_timing               -> first_and_last_service
                                                            -> service_frequency
                                                            -> scheduled_departure
service_availability        -> service_availability         -> mode_availability
fare_and_ticketing          -> fare_query                   -> fare_calculation
                            -> ticketing_rules              -> ticketing_and_passes
station_and_facilities      -> station_facilities           -> station_facilities
accessibility               -> accessibility                -> station_accessibility
[merged in T1 facilities]   -> interchange_query            -> interchange_transfer
nearest_transport           -> nearest_transport            -> nearest_transport
out_of_scope                -> unsupported_live_status      -> unsupported_live_status
                            -> out_of_scope                 -> out_of_scope
```

---

## 3. Taxonomy Candidate T1: Broad Granularity (9 Intents)

Taxonomy T1 maximizes sample efficiency and semantic separability by keeping intent classes coarse and delegating specific operational parameters to typed slots.

### T1 Intent Catalog

#### 1. `route_query`
- **User Goal**: Find a travel route or instructions to get from an origin to a destination.
- **Positive Examples**:
  - EN: "How do I get from Guindy to Chennai Airport?"
  - HI: "ताम्बरम से सेन्ट्रल जाने के लिए कौन सा रास्ता सही है?"
  - Hinglish: "koyambedu se marina beach kaise pauche bus ya metro se?"
- **Hard Negatives**:
  - "102 bus Guindy se jaati hai kya?" (This is `route_stops`, checking route coverage, not route planning).
  - "Is there a direct metro from Egmore to Central?" (This is `service_availability`).
- **Boundary Cases**:
  - "Can I take a bus to Adyar?" without origin. Boundary rule: If only destination is provided, classify as `route_query` with missing origin (system prompts for origin).
- **Required Slots**: `destination`
- **Optional Slots**: `origin`, `transport_mode`, `preference`
- **Downstream Action**: Executes routing graph traversal or direct connection query.
- **KB Answerability**: `ANSWERABLE_NOW` (Metro/direct), `ANSWERABLE_AFTER_ROUTING_GRAPH` (Multimodal).
- **Known Confusions**: Confused with `service_availability` when queries use modal verbs ("train milegi kya").
- **Reason to Include**: Core user journey capability.
- **Reason Not to Merge**: Fundamental navigational purpose; cannot merge with timetable or fare queries.

#### 2. `route_stops`
- **User Goal**: Query intermediate stops, stop sequence, or stop membership of a known route number or transit line.
- **Positive Examples**:
  - EN: "What stops does bus route 102 pass through?"
  - HI: "21G बस कौन-कौन से स्टॉप पर रुकती है?"
  - Hinglish: "blue line metro me guindy ke baad kaun sa station aata hai?"
- **Hard Negatives**:
  - "Airport jaane ke liye 102 bus sahi hai kya?" (This is `route_query` using route context).
- **Boundary Cases**:
  - "Does route 23C go to Besant Nagar?" (Checks stop membership; classified as `route_stops`).
- **Required Slots**: `route_number` or `line_name`
- **Optional Slots**: `station`, `stop`, `transport_mode`
- **Downstream Action**: SELECT from `route_stops` ordered by `stop_sequence`.
- **KB Answerability**: `ANSWERABLE_WITH_PROVISIONAL_DATA` (from longest-trip topology).
- **Reason to Include**: Essential for Chennai bus network with 4,619 route variants.
- **Reason Not to Merge**: Distinct from route planning; user already knows the route number.

#### 3. `service_timing`
- **User Goal**: Ask for operating hours, scheduled departure times, first or last train/bus, or running frequency.
- **Positive Examples**:
  - EN: "What time is the first metro from Chennai Central to Airport?"
  - HI: "बीच से ताम्बरम के लिए आखिरी लोकल ट्रेन कितने बजे छूटती है?"
  - Hinglish: "570 bus kitni der me aati hai schedule batao"
- **Hard Negatives**:
  - "102 bus abhi kahan hai?" (This is `out_of_scope` live tracking, not scheduled timing).
- **Boundary Cases**:
  - "Is metro running at 11 PM?" (Combines availability and timing; classified as `service_timing` with `time="23:00"`).
- **Required Slots**: At least one of `station`, `origin`, `route_number`, `transport_mode`
- **Optional Slots**: `timing_type` (first, last, frequency, schedule), `time`, `destination`
- **Downstream Action**: Queries `stop_times`, `trips`, and `service_calendars`.
- **KB Answerability**: `ANSWERABLE_NOW` (Metro), `ANSWERABLE_WITH_PROVISIONAL_DATA` (Bus/Rail).
- **Reason to Include**: High frequency commuter question.
- **Reason Not to Merge**: Separate timetable lookup from station amenities or ticket pricing.

#### 4. `service_availability`
- **User Goal**: Confirm whether public transport or a specific mode operates between two locations or at a station.
- **Positive Examples**:
  - EN: "Is there a direct train from Tambaram to Beach?"
  - HI: "क्या गिंडी से सेन्ट्रल तक मेट्रो उपलब्ध है?"
  - Hinglish: "adyar ke liye direct bus service hai ya nahi?"
- **Hard Negatives**:
  - "Guindy se airport kaise jau?" (Open route planning, `route_query`).
  - "Is the metro running late today?" (Live disruption tracking, `out_of_scope`).
- **Boundary Cases**:
  - "Tambaram se local train milegi kya?" (Closed yes/no availability check; classified as `service_availability`).
- **Required Slots**: `origin`, `destination`
- **Optional Slots**: `transport_mode`
- **Downstream Action**: Checks graph edge connectivity or direct route existence.
- **KB Answerability**: `ANSWERABLE_NOW`.
- **Reason to Include**: Direct connectivity verification without requesting complete routing itinerary.

#### 5. `fare_and_ticketing`
- **User Goal**: Ask for ticket prices, stage fares, payment methods, travel passes, or ticketing rules.
- **Positive Examples**:
  - EN: "What is the bus fare for 6 stages on MTC ordinary service?"
  - HI: "चेन्नई सेन्ट्रल से एयरपोर्ट का मेट्रो टिकट कितने का है?"
  - Hinglish: "metro smart card me minimum kitna recharge hota hai?"
- **Hard Negatives**:
  - "Can I book 2 tickets right now?" (Unsupported transactional query; `out_of_scope` or clarification).
- **Boundary Cases**:
  - "How much does it cost to travel from Guindy to Central by metro?" (Classified as `fare_and_ticketing` with `origin` and `destination`).
- **Required Slots**: Either (`origin` and `destination`) or `stage_number` or `ticket_type`
- **Optional Slots**: `transport_mode`, `service_type`
- **Downstream Action**: Queries `fares` table and ticketing policy data.
- **KB Answerability**: `ANSWERABLE_NOW`.
- **Reason to Include**: Consolidates tariff calculation and card rules under broad taxonomy.

#### 6. `station_and_facilities`
- **User Goal**: Inquire about physical station information, general facilities, parking, transfers, or platform layouts.
- **Positive Examples**:
  - EN: "Does Guindy station have two-wheeler parking available?"
  - HI: "क्या चेन्नई सेंट्रल पर क्लॉक रूम और वेटिंग हॉल है?"
  - Hinglish: "koyambedu metro station me interchange facility hai kya?"
- **Hard Negatives**:
  - "Does Egmore station have wheelchair ramps?" (Dedicated `accessibility`).
- **Boundary Cases**:
  - "Can I transfer from metro to train at Guindy?" (Interchange question; folded into `station_and_facilities` in T1 with `facility="interchange"`).
- **Required Slots**: `station`
- **Optional Slots**: `facility_type`, `transport_mode`
- **Downstream Action**: Queries `transport_stops`, `interchanges`, and station metadata.
- **KB Answerability**: `ANSWERABLE_NOW` (Metro facilities), `ANSWERABLE_AFTER_MANUAL_VERIFICATION` (Interchanges).
- **Reason to Include**: General station physical layout queries.

#### 7. `accessibility`
- **User Goal**: Inquire about facilities for persons with disabilities, reduced mobility, or visual impairment.
- **Positive Examples**:
  - EN: "Is wheelchair assistance available at Puratchi Thalaivar Central metro?"
  - HI: "क्या शेनॉय नगर स्टेशन पर दिव्यांगों के लिए लिफ्ट और स्पर्श पथ है?"
  - Hinglish: "vadapalani metro me wheelchair accessibility hai?"
- **Hard Negatives**:
  - "Central station me parking hai kya?" (`station_and_facilities`).
- **Boundary Cases**:
  - "Does the station have a lift?" (Lifts are primary accessibility assets; classified as `accessibility`).
- **Required Slots**: `station`
- **Optional Slots**: `accessibility_feature` (wheelchair, lift, tactile_paths, accessible_toilet, ramp)
- **Downstream Action**: Queries confirmed `accessibility` table records.
- **KB Answerability**: `ANSWERABLE_NOW` (Metro only).
- **Reason to Include**: Statutory public service obligation; distinct accessibility vocabulary.

#### 8. `nearest_transport`
- **User Goal**: Identify the closest public transport stop, station, or hub relative to a named landmark or locality.
- **Positive Examples**:
  - EN: "Which is the closest bus stop to Apollo Hospital Greams Road?"
  - HI: "आईआईटी मद्रास के सबसे पास कौन सा मेट्रो स्टेशन है?"
  - Hinglish: "marina beach ke nearest local train station batao"
- **Hard Negatives**:
  - "How do I get to Apollo Hospital from Central?" (`route_query`).
  - "Where am I right now?" (`out_of_scope` device GPS request).
- **Boundary Cases**:
  - "Nearest bus stop" without landmark. Boundary rule: Requires landmark/locality slot; system prompts for location if absent.
- **Required Slots**: `landmark` or `locality`
- **Optional Slots**: `transport_mode`
- **Downstream Action**: Executes spatial proximity lookup on `places` and `transport_stops`.
- **KB Answerability**: `ANSWERABLE_AFTER_ROUTING_GRAPH`.
- **Reason to Include**: Critical multimodal use case linking Chennai's 1,621 POIs to 7,136 transit stops.

#### 9. `out_of_scope`
- **User Goal**: Non-supported transit questions, real-time tracking requests, booking transactions, or general conversation.
- **Positive Examples**:
  - EN: "What is the live location of bus 21G right now?"
  - HI: "आज चेन्नई में मौसम कैसा रहेगा?"
  - Hinglish: "airport ke liye uber cab book kar do"
- **Hard Negatives**:
  - "Tambaram se Beach train timings?" (`service_timing`).
- **Downstream Action**: Returns standardized graceful rejection or clarification response.
- **KB Answerability**: `OUT_OF_SCOPE` / `REQUIRES_REALTIME_DATA`.
- **Reason to Include**: Rejection boundary safeguard against hallucination.

---

## 4. Taxonomy Candidate T2: Medium Granularity (12 Intents - Recommended Candidate)

Taxonomy T2 addresses key operational distinctions discovered in Phase N1 without creating redundant linguistic fragmentation.

### Key Refinements in T2:
1. **Splits Fare Calculation from Ticketing Policies**:
   - `fare_query`: Algorithmic lookup against statutory stage tariff matrices (`fares`, `fare_stages`).
   - `ticketing_rules`: Static policies regarding smart cards, passes, discounts, and payment methods.
2. **Elevates Multimodal Interchange to First-Class Intent**:
   - `interchange_query`: Queries specifically asking about transfers, physical connections, and transfer feasibility between modes or corridors.
3. **Separates Live Status Refusal from General Chit-Chat**:
   - `unsupported_live_status`: Commuter transit requests that fail solely due to lack of real-time telemetry (bus tracking, live delays, crowd levels). Allows specialized, helpful factual refusal ("Live GPS tracking is not currently supported; scheduled timetable is available").
   - `out_of_scope`: True domain rejections (weather, food, ride-hailing cabs, flights, conversational chit-chat).

### T2 Intent Catalog Summary

| T2 Intent Name | Definition & Core Purpose | Required Slots | Downstream Action | KB Answerability |
| :--- | :--- | :--- | :--- | :--- |
| **`route_query`** | Point-to-point pathfinding and travel guidance | `destination`, (`origin` opt) | Multimodal graph pathfinding | `ANSWERABLE_NOW` / `ANSWERABLE_AFTER_ROUTING_GRAPH` |
| **`route_stops`** | Listing or checking intermediate stops on a known route | `route_number` or `line_name` | Query `route_stops` by sequence | `ANSWERABLE_WITH_PROVISIONAL_DATA` |
| **`service_timing`** | Operating hours, first/last trips, scheduled timetable | At least one transit entity | Query `stop_times` & `service_calendars` | `ANSWERABLE_NOW` / `ANSWERABLE_WITH_PROVISIONAL_DATA` |
| **`service_availability`**| Confirming operational connectivity between points | `origin`, `destination` | Graph connectivity check | `ANSWERABLE_NOW` |
| **`fare_query`** | Computing monetary ticket prices and stage fares | `origin` & `dest`, or `stage_num` | Tariff lookup in `fares` table | `ANSWERABLE_NOW` / `ANSWERABLE_WITH_PROVISIONAL_DATA` |
| **`ticketing_rules`** | Inquiries about smart cards, monthly passes, recharge rules | `ticket_type` | Static transit policy retrieval | `ANSWERABLE_NOW` |
| **`station_facilities`** | Station amenities (parking, restrooms, waiting rooms) | `station` | Query `transport_stops` metadata | `ANSWERABLE_NOW` |
| **`accessibility`** | Special needs facilities (wheelchairs, lifts, tactile paths) | `station` | Query `accessibility` table | `ANSWERABLE_NOW` (Metro only) |
| **`interchange_query`** | Mode transfer locations, walking connections, transfer hubs | `station` or (`mode_from`, `mode_to`)| Query `interchanges` & `transport_hubs`| `ANSWERABLE_AFTER_MANUAL_VERIFICATION` |
| **`nearest_transport`** | Finding nearest transit stop relative to a named landmark | `landmark` or `locality` | Spatial distance query over `places` | `ANSWERABLE_AFTER_ROUTING_GRAPH` |
| **`unsupported_live_status`**| Refusing requests for live vehicle positions & delays | Transit entity reference | Deterministic live tracking refusal | `REQUIRES_REALTIME_DATA` |
| **`out_of_scope`** | Refusing non-transit, non-CMA, or transactional requests | None | Standard out-of-scope rejection | `OUT_OF_SCOPE` |

---

## 5. Taxonomy Candidate T3: Fine Granularity (16 Intents)

Taxonomy T3 breaks down capabilities into atomic intents, suitable for pipelines where individual ML models handle specialized tasks.

### T3 Intent Catalog
1. `point_to_point_route`: Single mode travel itinerary ("Metro se Guindy se Airport kaise jau").
2. `multimodal_route`: Cross-mode travel itinerary ("Bus aur train combine karke Central se Thiruvanmiyur route").
3. `route_stop_sequence`: Complete ordered sequence of stops on a route ("102 bus ke saare stop batao").
4. `route_stop_membership`: Verification if a route passes through a stop ("Kya 21G Guindy par rukti hai?").
5. `first_and_last_service`: Specifically asking for day's earliest or latest departure ("First metro kab hai").
6. `service_frequency`: Frequency or headway intervals ("Kitni kitni der me bus aati hai").
7. `scheduled_departure`: Timetable departure at a specific time of day ("Subah 8 baje Tambaram se bus").
8. `mode_availability`: Operational connectivity check on a corridor ("Direct train service available hai?").
9. `fare_calculation`: Point-to-point and stage-based ticket price calculation.
10. `ticketing_and_passes`: Smart card policies, recharge limits, travel passes.
11. `station_facilities`: Parking, Wi-Fi, waiting halls, clock rooms.
12. `station_accessibility`: Wheelchair, lift, ramp, tactile path.
13. `interchange_transfer`: Feasibility and directions for transferring between modes.
14. `nearest_transport`: Finding transit stops closest to a POI.
15. `unsupported_live_status`: In-domain live tracking refusal.
16. `out_of_scope`: Out-of-domain rejection.

### Risks and Trade-offs of T3:
- High boundary overlap: Distinguishing `first_and_last_service` from `scheduled_departure` relies heavily on subtle lexical triggers ("aakhiri" vs "8 baje") that confuse sequence classifiers.
- Distinguishing `route_stop_sequence` from `route_stop_membership` is better modeled by slot presence (`stop` present vs absent).
- Higher data annotation cost and risk of lower Macro-F1.

---

## 6. Granularity Mapping Across Taxonomies

| T1 Intent (Broad: 9) | T2 Intent (Medium: 12) | T3 Intent (Fine: 16) | Slot-Based Representation in Coarser Taxonomies |
| :--- | :--- | :--- | :--- |
| `route_query` | `route_query` | `point_to_point_route` | `preferred_mode = "metro"` / `"single"` |
| `route_query` | `route_query` | `multimodal_route` | `preferred_mode = "multimodal"` |
| `route_stops` | `route_stops` | `route_stop_sequence` | `stop = null` |
| `route_stops` | `route_stops` | `route_stop_membership` | `stop != null` |
| `service_timing` | `service_timing` | `first_and_last_service` | `timing_type = "first"` or `"last"` |
| `service_timing` | `service_timing` | `service_frequency` | `timing_type = "frequency"` |
| `service_timing` | `service_timing` | `scheduled_departure` | `time != null` |
| `service_availability` | `service_availability` | `mode_availability` | N/A |
| `fare_and_ticketing` | `fare_query` | `fare_calculation` | `inquiry_type = "fare"` |
| `fare_and_ticketing` | `ticketing_rules` | `ticketing_and_passes` | `inquiry_type = "policy"` |
| `station_and_facilities` | `station_facilities` | `station_facilities` | N/A |
| `accessibility` | `accessibility` | `station_accessibility` | N/A |
| `station_and_facilities` | `interchange_query` | `interchange_transfer` | `facility_type = "interchange"` |
| `nearest_transport` | `nearest_transport` | `nearest_transport` | `transport_mode = any | bus | metro` |
| `out_of_scope` | `unsupported_live_status` | `unsupported_live_status` | Handled by live status regex filter |
| `out_of_scope` | `out_of_scope` | `out_of_scope` | N/A |

---

## 7. Recommended Taxonomy for Pilot Study: **T2 (Medium, 12 Intents)**

**Justification for Recommending T2**:
1. **Separation of Operational Workflows**: `fare_query` (tariff calculation) and `ticketing_rules` (static FAQ) hit completely different backend endpoints. Merging them in T1 creates ambiguity in the response generation layer.
2. **First-Class Interchange Handling**: With 45 candidate interchanges and 62 multimodal hubs in `canonical_transport.db`, interchange questions are frequent in Chennai. Treating them as a dedicated intent allows explicit provisional qualification ("provisional walking transfer: ~85m").
3. **Safety Through Explicit Live Status Refusal**: Commuters regularly ask for live bus tracking. Folding these into generic `out_of_scope` gives the user an unhelpful message ("I cannot help with that"). Classifying as `unsupported_live_status` allows the assistant to state: "Live GPS tracking for MTC buses is not yet available; scheduled timetable departure is 17:15."
4. **Avoids T3 Over-Fragmentation**: Avoids splitting timing queries into 3 brittle classes where a single slot (`timing_type`) cleanly resolves the difference.
