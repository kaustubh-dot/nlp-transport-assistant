# Typed Slot Schema and Intent-Slot Contract Matrix (Phase N3)

Document: `docs/nlp_v2/slot_schema.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Slot Specification

---

## 1. Slot Design Principles

In the multimodal NLU system, slots capture structured attributes extracted from user utterances. To maintain consistency across pipelines and avoid combinatorial explosion in intent classification, we enforce:
1. **Typed Representation**: Every slot has a strict data type, canonical representation, and namespace in `canonical_transport.db`.
2. **Separation of Extraction and Resolution**: The slot span (raw surface string) is extracted first, then resolved to a canonical database ID.
3. **Strict Contract Constraints**: Slots are governed by four relationship classes per intent:
   - `REQ` (Required): Mandatory for execution; absence triggers clarification.
   - `OPT` (Optional): Valid if provided; absent default is applied.
   - `CONDITIONAL`: Required under specific contextual slot combinations.
   - `FORBIDDEN`: Semantically invalid for this intent; presence indicates misclassification.

---

## 2. Core Typed Slot Definitions

### 2.1 Spatial & Transit Entity Slots

#### `origin`
- **Type**: `EntityReference` (Station, Stop, Hub, Landmark, Locality)
- **Description**: The starting physical location or transit node of a journey.
- **Entity Namespace**: `transport_stops.stop_id`, `transport_hubs.hub_id`, `places.place_id`
- **Canonical Representation**: Uppercase alphanumeric entity ID (e.g. `HUB_GUINDY`, `BUS_5822`, `OSM_POI_7820652140`)
- **Required In**: `service_availability`
- **Optional In**: `route_query`, `service_timing`, `fare_query`
- **Forbidden In**: `station_facilities`, `accessibility`
- **Normalization**: Strip directional postpositions (`से`, `se`, `from`, `irunthu`), trim whitespace, map to canonical entity.

#### `destination`
- **Type**: `EntityReference`
- **Description**: The intended target location or terminus of a journey.
- **Entity Namespace**: `transport_stops.stop_id`, `transport_hubs.hub_id`, `places.place_id`
- **Canonical Representation**: Uppercase alphanumeric entity ID (e.g. `METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL`)
- **Required In**: `route_query` (or clarification required), `service_availability`
- **Optional In**: `service_timing`, `fare_query`
- **Forbidden In**: `station_facilities`, `accessibility`
- **Normalization**: Strip destination postpositions (`तक`, `tak`, `ko`, `ke liye`, `to`, `ku`), trim whitespace, map to canonical entity.

#### `station`
- **Type**: `EntityReference` (Transit Station or Stop)
- **Description**: A single transit facility being queried for amenities, accessibility, or schedule.
- **Entity Namespace**: `transport_stops.stop_id`, `transport_hubs.hub_id`
- **Canonical Representation**: Canonical stop ID
- **Required In**: `station_facilities`, `accessibility`, `interchange_query` (unless mode pair is supplied)
- **Optional In**: `service_timing`
- **Forbidden In**: `route_query` (must be split into `origin`/`destination`)
- **Normalization**: Strip words like `metro`, `station`, `bus stand`, resolve against canonical stop aliases.

#### `landmark` / `locality`
- **Type**: `EntityReference` (POI or Geographic Area)
- **Description**: A non-station reference point used for proximity queries.
- **Entity Namespace**: `places.place_id`
- **Canonical Representation**: Canonical place ID (e.g. `OSM_POI_7820652140`)
- **Required In**: `nearest_transport`
- **Optional In**: `route_query` (as origin/destination landmark)
- **Forbidden In**: `station_facilities`, `accessibility`
- **Normalization**: Match against `place_names` table.

---

### 2.2 Route & Transit Attribute Slots

#### `route_number`
- **Type**: `String` (Alphanumeric transit route identifier)
- **Description**: The public operational code identifying a bus route or train line.
- **Allowed Formats**: Numeric (`102`, `21`, `570`), Alpha-suffix (`102A`, `21G`, `570S`, `M1`), Express/Night (`PP66`, `102K#`, `29C-ET`)
- **Required In**: `route_stops`
- **Optional In**: `service_timing`, `route_query`
- **Forbidden In**: `station_facilities`, `accessibility`
- **Normalization Rules**:
  - Retain all meaningful alphanumeric suffixes (e.g. preserve `A`, `G`, `S`, `K#`, `ET`).
  - Strip noise tokens: `bus`, `route`, `no`, `number`, `बस`, `नंबर`.
  - Canonical format: Uppercase alphanumeric string (e.g. `102A`, `21G`).
  - Never truncate `102A` to `102` (represents a distinct operational route in MTC).

#### `transport_mode`
- **Type**: `Enum`
- **Description**: The specific transit technology or operator mode requested by the user.
- **Allowed Values**: `metro`, `bus`, `suburban_rail`, `mrts`, `any`
- **Canonical Values**:
  - `metro`: Chennai Metro Rail (CMRL)
  - `bus`: Metropolitan Transport Corporation (MTC)
  - `suburban_rail`: Southern Railway Chennai Suburban Railway (SR)
  - `mrts`: Mass Rapid Transit System Chennai (SR/MRTS)
  - `any`: No modal constraint specified
- **Required In**: None (defaults to `any` if unspecified)
- **Optional In**: `route_query`, `service_availability`, `service_timing`, `nearest_transport`, `fare_query`
- **Forbidden In**: `out_of_scope`

#### `timing_type`
- **Type**: `Enum`
- **Description**: Temporal constraint or query type for scheduled transit.
- **Allowed Values**: `first`, `last`, `frequency`, `departure`, `operating_hours`
- **Required In**: `service_timing` (defaults to `departure` if explicit time given, or `operating_hours` if general)
- **Optional In**: `route_query`
- **Forbidden In**: `fare_query`, `station_facilities`, `accessibility`

#### `time`
- **Type**: `ISO_Time` (`HH:MM:SS` or `HH:MM`)
- **Description**: Specific requested clock time of travel.
- **Canonical Format**: 24-hour format string (e.g. `08:00`, `20:30`, `14:15`)
- **Optional In**: `service_timing`, `route_query`
- **Normalization Rules**:
  - `8 baje` -> `08:00` (morning default) or context-dependent
  - `raat 8 baje` / `8 pm` -> `20:00`
  - `subah 5` / `5 am` -> `05:00`
  - Temporal relative markers (`aaj`, `kal`): Represented in separate `temporal_relative` slot; do not silently assume tomorrow for Hindi `कल`.

#### `facility_type`
- **Type**: `Enum`
- **Description**: General station amenities requested.
- **Allowed Values**: `parking`, `restroom`, `waiting_room`, `cloak_room`, `atm`, `wifi`, `drinking_water`
- **Required In**: None (optional filter for `station_facilities`)
- **Forbidden In**: `route_stops`, `fare_query`

#### `accessibility_feature`
- **Type**: `Enum`
- **Description**: Assistive accessibility amenities for passengers with disabilities.
- **Allowed Values**: `wheelchair`, `lift`, `escalator`, `ramp`, `accessible_toilet`, `tactile_paths`, `any`
- **Required In**: None (defaults to `any` accessibility check if general)
- **Optional In**: `accessibility`
- **Forbidden In**: `route_query`, `route_stops`, `fare_query`

#### `ticket_type` / `fare_type`
- **Type**: `Enum`
- **Description**: Transit fare product or payment instrument.
- **Allowed Values**: `token`, `smart_card`, `ncmc_card`, `qr_ticket`, `monthly_pass`, `tourist_pass`, `concession`
- **Optional In**: `fare_query`, `ticketing_rules`
- **Forbidden In**: `route_stops`, `station_facilities`

---

## 3. Intent-Slot Contract Matrix (Taxonomy T2)

This contract defines the validity of every slot across all 12 intents in recommended taxonomy T2.

| Intent Name | `origin` | `destination` | `station` | `landmark` | `route_number` | `transport_mode` | `timing_type` | `time` | `facility_type` | `accessibility_feature` | `ticket_type` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`route_query`** | OPT* | REQ | FORBIDDEN | OPT | OPT | OPT | OPT | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| **`route_stops`** | FORBIDDEN | FORBIDDEN | OPT | FORBIDDEN | REQ | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| **`service_timing`** | OPT | OPT | OPT | FORBIDDEN | OPT | OPT | REQ | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| **`service_availability`**| REQ | REQ | FORBIDDEN | FORBIDDEN | OPT | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| **`fare_query`** | COND1 | COND1 | FORBIDDEN | FORBIDDEN | OPT | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | OPT |
| **`ticketing_rules`** | FORBIDDEN | FORBIDDEN | OPT | FORBIDDEN | FORBIDDEN | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | REQ |
| **`station_facilities`** | FORBIDDEN | FORBIDDEN | REQ | FORBIDDEN | FORBIDDEN | OPT | FORBIDDEN | FORBIDDEN | OPT | FORBIDDEN | FORBIDDEN |
| **`accessibility`** | FORBIDDEN | FORBIDDEN | REQ | FORBIDDEN | FORBIDDEN | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | OPT | FORBIDDEN |
| **`interchange_query`** | OPT | OPT | COND2 | FORBIDDEN | OPT | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| **`nearest_transport`** | FORBIDDEN | FORBIDDEN | FORBIDDEN | REQ | FORBIDDEN | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| **`unsupported_live_status`**| OPT | OPT | OPT | OPT | OPT | OPT | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| **`out_of_scope`** | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |

*Notes on Conditions*:
- `OPT*` for `route_query`: If `origin` is missing, the query is valid but triggers a clarification prompt asking the user for their starting location.
- `COND1` for `fare_query`: Either (`origin` AND `destination`) are required, OR `stage_number` is required.
- `COND2` for `interchange_query`: Either a specific `station` is required, OR an origin-destination pair with a transfer request is required.

---

## 4. Malformed Query Handling and Dialogue Clarification

An NLU system must not hallucinate missing required slots. When an utterance is classified with an intent whose required slots are absent, the system executes an explicit clarification policy:

1. **Missing Origin in `route_query`**:
   - Query: "Airport kaise jau?"
   - Classified Intent: `route_query`
   - Extracted Slots: `{"destination": "HUB_AIRPORT", "origin": null}`
   - Action: `CLARIFY_ORIGIN`
   - Deterministic Prompt: "Aap kahan se Airport jana chahte hain? Kripya apna shuruati station ya jagah batayein." (Where are you starting from?)

2. **Missing Destination in `route_query`**:
   - Query: "Guindy se kaun si bus milegi?"
   - Classified Intent: `route_query`
   - Extracted Slots: `{"origin": "HUB_GUINDY", "destination": null}`
   - Action: `CLARIFY_DESTINATION`
   - Deterministic Prompt: "Guindy se aapko kahan jana hai? Kripya apni manzil batayein."

3. **Missing Route Number in `route_stops`**:
   - Query: "Ye bus kaun se raste se jaati hai?"
   - Extracted Slots: `{"route_number": null}`
   - Action: `CLARIFY_ROUTE`
   - Deterministic Prompt: "Aap kis bus ya train route ke stops janna chahte hain? Kripya route number batayein (jaise 102, 21G)."

4. **Missing Landmark in `nearest_transport`**:
   - Query: "Nearest bus stop batao"
   - Extracted Slots: `{"landmark": null}`
   - Action: `CLARIFY_LOCATION`
   - Deterministic Prompt: "Aap kis jagah ya landmark ke paas bus stop dhoondh rahe hain?"
