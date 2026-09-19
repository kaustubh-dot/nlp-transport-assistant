# Typed Slot Schema and Intent-Slot Contract Matrix (Phase N3)

Document: `docs/nlp_v2/slot_schema.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Slot Specification (Corrected Methodology Patch)

---

## 1. Slot Design Principles

In the multimodal NLU system, slots capture structured attributes extracted from user utterances. To maintain consistency across pipelines, benchmark splits, and downstream retrieval, we enforce:
1. **Typed Representation**: Every slot has a strict data type, canonical representation, and namespace in `canonical_transport.db`.
2. **Separation of Extraction and Resolution**: The slot span (raw surface string) is extracted first, then resolved to a canonical database ID.
3. **Canonical Shared Vocabulary**: Every slot referenced in any taxonomy (T1, T2, T3), dataset schema, or evaluation protocol must be explicitly defined in this ontology.
4. **Strict Contract Constraints**: Slots are governed by four relationship classes per intent:
   - `REQ` (Required): Mandatory for execution; absence triggers dialogue clarification.
   - `OPT` (Optional): Valid if provided; absent default is applied.
   - `CONDITIONAL`: Required under specific contextual slot combinations.
   - `FORBIDDEN`: Semantically invalid for this intent; presence indicates misclassification.

---

## 2. Definitive Canonical Slot Ontology

The authoritative multimodal transport assistant ontology defines exactly **23 canonical slots** organized across four operational categories:

### 2.1 Spatial & Geographic Entity Slots

#### `origin`
- **Type**: `EntityReference` (Station, Stop, Hub, Landmark, Locality)
- **Description**: The starting physical location or transit node of a journey.
- **Entity Namespace**: `transport_stops.stop_id`, `transport_hubs.hub_id`, `places.place_id`
- **Canonical Representation**: Uppercase alphanumeric entity ID (e.g. `HUB_GUINDY`, `BUS_5822`, `OSM_POI_7820652140`)
- **Required In**: `service_availability`
- **Optional In**: `route_query`, `service_timing`, `fare_query`, `realtime_status_query`
- **Forbidden In**: `station_facilities`, `accessibility`
- **Normalization**: Strip directional postpositions (`से`, `se`, `from`, `irunthu`), trim whitespace, map to canonical entity.

#### `destination`
- **Type**: `EntityReference`
- **Description**: The intended target location or terminus of a journey.
- **Entity Namespace**: `transport_stops.stop_id`, `transport_hubs.hub_id`, `places.place_id`
- **Canonical Representation**: Uppercase alphanumeric entity ID (e.g. `METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL`)
- **Required In**: `route_query` (absence triggers clarification prompt), `service_availability`
- **Optional In**: `service_timing`, `fare_query`, `realtime_status_query`
- **Forbidden In**: `station_facilities`, `accessibility`
- **Normalization**: Strip destination postpositions (`तक`, `tak`, `ko`, `ke liye`, `to`, `ku`), trim whitespace, map to canonical entity.

#### `via`
- **Type**: `EntityReference`
- **Description**: An explicit intermediate waypoint, junction, or station through which the user wishes to travel.
- **Entity Namespace**: `transport_stops.stop_id`, `transport_hubs.hub_id`, `places.place_id`
- **Canonical Representation**: Canonical entity ID
- **Optional In**: `route_query`
- **Forbidden In**: `service_timing`, `station_facilities`, `accessibility`, `fare_query`
- **Normalization**: Strip routing markers (`via`, `hote hue`, `se hokar`).

#### `station`
- **Type**: `EntityReference` (Transit Station or Stop)
- **Description**: A single transit station or stop being queried for amenities, accessibility, or schedule.
- **Entity Namespace**: `transport_stops.stop_id`, `transport_hubs.hub_id`
- **Canonical Representation**: Canonical stop ID
- **Required In**: `station_facilities`, `accessibility`, `interchange_query` (unless mode pair is supplied)
- **Optional In**: `service_timing`, `realtime_status_query`, `ticketing_rules`
- **Forbidden In**: `route_query` (must be split into `origin`/`destination`)
- **Normalization**: Strip words like `metro`, `station`, `bus stand`, resolve against canonical stop aliases.

#### `stop`
- **Type**: `EntityReference` (Route Stop Reference)
- **Description**: A specific bus stop or station referenced when checking membership on a route (e.g. "Does 102 stop at Adyar?").
- **Entity Namespace**: `transport_stops.stop_id`
- **Canonical Representation**: Canonical stop ID (e.g. `BUS_2820`)
- **Optional In**: `route_stops`
- **Forbidden In**: `service_availability`, `station_facilities`, `accessibility`
- **Normalization**: Same as `station`.

#### `landmark` / `locality`
- **Type**: `EntityReference` (POI or Geographic Locality)
- **Description**: A non-station reference point used for proximity queries.
- **Entity Namespace**: `places.place_id`
- **Canonical Representation**: Canonical place ID (e.g. `OSM_POI_7820652140`)
- **Required In**: `nearest_transport`
- **Optional In**: `route_query` (as origin/destination landmark), `realtime_status_query`
- **Forbidden In**: `station_facilities`, `accessibility`
- **Normalization**: Match against `place_names` table.

---

### 2.2 Route, Mode & Transfer Slots

#### `route_number`
- **Type**: `String` (Alphanumeric transit route identifier)
- **Description**: The public operational code identifying a bus route or train line.
- **Allowed Formats**: Numeric (`102`, `21`, `570`), Alpha-suffix (`102A`, `21G`, `570S`, `M1`), Express/Night (`PP66`, `102K#`, `29C-ET`)
- **Required In**: `route_stops`
- **Optional In**: `service_timing`, `route_query`, `realtime_status_query`
- **Forbidden In**: `station_facilities`, `accessibility`, `ticketing_rules`
- **Normalization Rules**:
  - Retain all meaningful alphanumeric suffixes (preserve `A`, `G`, `S`, `K#`, `ET`).
  - Strip noise tokens: `bus`, `route`, `no`, `number`, `बस`, `नंबर`.
  - Canonical format: Uppercase alphanumeric string (e.g. `102A`, `21G`).
  - Never truncate `102A` to `102` (represents a distinct operational route in MTC).

#### `line_name`
- **Type**: `String` (Transit Corridor Name)
- **Description**: The public corridor or transit line name.
- **Allowed Values**: `Blue Line`, `Green Line`, `Corridor 1`, `Corridor 2`, `MRTS`, `North Line`, `South Line`, `West Line`
- **Optional In**: `route_stops`, `service_timing`, `route_query`, `service_availability`
- **Forbidden In**: `ticketing_rules`, `station_facilities`

#### `transport_mode`
- **Type**: `Enum`
- **Description**: The specific transit technology or operator mode requested by the user.
- **Allowed Values**: `metro`, `bus`, `suburban_rail`, `mrts`, `any`
- **Canonical Values**:
  - `metro`: Chennai Metro Rail (CMRL)
  - `bus`: Metropolitan Transport Corporation (MTC)
  - `suburban_rail`: Southern Railway Chennai Suburban Railway (SR)
  - `mrts`: Mass Rapid Transit System Chennai (SR/MRTS)
  - `any`: No modal constraint specified (default)
- **Optional In**: `route_query`, `service_availability`, `service_timing`, `nearest_transport`, `fare_query`, `interchange_query`
- **Forbidden In**: `out_of_scope`

#### `mode_from` / `mode_to`
- **Type**: `Enum` (Allowed values same as `transport_mode`)
- **Description**: The departure mode and arrival mode in an interchange transfer query (e.g. "Can I transfer from Metro to Suburban rail?").
- **Optional In**: `interchange_query`
- **Forbidden In**: All other intents.

#### `preference`
- **Type**: `Enum`
- **Description**: Commuter travel preference constraint.
- **Allowed Values**: `fastest`, `cheapest`, `least_transfers`, `direct_only`
- **Optional In**: `route_query`
- **Forbidden In**: All other intents.

---

### 2.3 Temporal Slots & Strict Ambiguity Handling

#### `timing_type`
- **Type**: `Enum`
- **Description**: Temporal constraint or query type for scheduled transit.
- **Allowed Values**: `first`, `last`, `frequency`, `departure`, `operating_hours`
- **Required In**: `service_timing` (defaults to `departure` if explicit time given, or `operating_hours` if general)
- **Optional In**: `route_query`
- **Forbidden In**: `fare_query`, `station_facilities`, `accessibility`

#### `time`
- **Type**: `ISO_Time` (`HH:MM:SS`) or `TimeCandidateSet`
- **Description**: Specific requested clock time of travel.
- **Strict Ambiguity Handling for Bare Times**:
  - For explicit times: `8:00 pm` / `8 PM` / `20:00` → `20:00:00`; `8:00 am` / `8 AM` → `08:00:00`.
  - For bare numbers (`8 baje`, `8 बजे`, `8 o'clock`): **Do not default to 08:00**. The system must record dual candidates `["08:00:00", "20:00:00"]` with `temporal_ambiguity: true` and require contextual or dialogue resolution.

#### `temporal_relative`
- **Type**: `String`
- **Description**: Relative day expression in query (`aaj`, `kal`, `parso`, `today`, `tomorrow`, `yesterday`).
- **Strict Ambiguity Handling for Hindi `कल / kal`**:
  - **Zero Default Rule**: Remove any default mapping of `kal` to tomorrow.
  - Resolve to `+1` (tomorrow) or `-1` (yesterday) **only** when grammatical tense, aspect, or dialogue context provides unambiguous proof (e.g. past tense "kal train aayi thi" vs future "kal train milegi kya").
  - In queries lacking tense markers (e.g. "kal ka schedule"), the system must emit `resolved_temporal_offset: UNRESOLVED_TEMPORAL_AMBIGUITY` and trigger clarification.

#### `date`
- **Type**: `ISO_Date` (`YYYY-MM-DD`)
- **Description**: Explicit calendar date if provided by the user.
- **Optional In**: `service_timing`, `route_query`

---

### 2.4 Fare, Ticket & Facility Slots

#### `ticket_type`
- **Type**: `Enum`
- **Description**: Physical or digital transit ticketing instrument.
- **Allowed Values**: `token`, `smart_card`, `ncmc_card`, `qr_ticket`, `monthly_pass`, `tourist_pass`, `season_pass`
- **Required In**: `ticketing_rules`
- **Optional In**: `fare_query`
- **Forbidden In**: `route_stops`, `station_facilities`

#### `fare_type`
- **Type**: `Enum`
- **Description**: Tariff category or pricing scheme.
- **Allowed Values**: `stage_fare`, `distance_fare`, `concession`, `pass_fare`
- **Optional In**: `fare_query`
- **Forbidden In**: `route_stops`, `station_facilities`

#### `stage_number`
- **Type**: `Integer` (Range: 1 to 30)
- **Description**: Official statutory bus fare stage index from MTC Tamil Nadu Gazette disclosures (G.O. Ms 48).
- **Conditional In**: `fare_query` (mandatory if origin and destination are absent)
- **Forbidden In**: All other intents.

#### `service_type`
- **Type**: `Enum`
- **Description**: Official bus service tariff category.
- **Allowed Values**: `Ordinary Services`, `Express Services`, `Deluxe Services`, `Night Services`, `Air Conditioned Services`
- **Optional In**: `fare_query`
- **Forbidden In**: `station_facilities`, `accessibility`

#### `facility_type`
- **Type**: `Enum`
- **Description**: Station amenity requested.
- **Allowed Values**: `parking`, `interchange`, `restroom`, `waiting_room`, `cloak_room`, `atm`, `wifi`, `drinking_water`
- **KB Answerability Caveat**:
  - `parking` for Metro is `ANSWERABLE_NOW` (via `accessibility.parking_available`).
  - `interchange` is `ANSWERABLE_AFTER_MANUAL_VERIFICATION`.
  - General commercial amenities (`waiting_room`, `cloak_room`, `atm`, `wifi`, `drinking_water`) are `NOT_CURRENTLY_SUPPORTED` in the database.
- **Optional In**: `station_facilities`
- **Forbidden In**: `route_stops`, `fare_query`

#### `accessibility_feature`
- **Type**: `Enum`
- **Description**: Assistive accessibility amenities for passengers with disabilities.
- **Allowed Values**: `wheelchair`, `lift`, `escalator`, `ramp`, `accessible_toilet`, `tactile_paths`, `any`
- **Optional In**: `accessibility`
- **Forbidden In**: `route_query`, `route_stops`, `fare_query`

---

## 3. Comprehensive Intent-Slot Contract Matrix (Taxonomy T2)

This matrix defines the validity of every canonical slot across all 12 candidate intents in Taxonomy T2.

| Canonical Slot | `route_query` | `route_stops` | `service_timing` | `service_availability` | `fare_query` | `ticketing_rules` | `station_facilities` | `accessibility` | `interchange_query` | `nearest_transport` | `realtime_status_query` | `out_of_scope` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `origin` | OPT* | - | OPT | REQ | COND1 | - | - | - | OPT | - | OPT | OPT |
| `destination` | REQ | - | OPT | REQ | COND1 | - | - | - | OPT | - | OPT | OPT |
| `via` | OPT | - | - | - | - | - | - | - | - | - | - | - |
| `station` | - | - | OPT | - | - | OPT | REQ | REQ | COND2 | - | OPT | OPT |
| `stop` | - | OPT | - | - | - | - | - | - | - | - | - | - |
| `landmark` | OPT | - | - | - | - | - | - | - | - | REQ | OPT | OPT |
| `locality` | OPT | - | - | - | - | - | - | - | - | REQ | OPT | OPT |
| `route_number` | OPT | REQ | OPT | - | OPT | - | - | - | OPT | - | OPT | OPT |
| `line_name` | OPT | OPT | OPT | OPT | - | - | - | - | OPT | - | OPT | OPT |
| `transport_mode`| OPT | OPT | OPT | OPT | OPT | OPT | OPT | OPT | OPT | OPT | OPT | - |
| `mode_from` | - | - | - | - | - | - | - | - | OPT | - | - | - |
| `mode_to` | - | - | - | - | - | - | - | - | OPT | - | - | - |
| `preference` | OPT | - | - | - | - | - | - | - | - | - | - | - |
| `timing_type` | OPT | - | REQ | - | - | - | - | - | - | - | - | - |
| `time` | OPT | - | OPT | - | - | - | - | - | - | - | - | - |
| `temporal_relative`| OPT | - | OPT | OPT | - | - | - | - | - | - | OPT | - |
| `date` | OPT | - | OPT | OPT | - | - | - | - | - | - | - | - |
| `ticket_type` | - | - | - | - | OPT | REQ | - | - | - | - | - | - |
| `fare_type` | - | - | - | - | OPT | - | - | - | - | - | - | - |
| `stage_number` | - | - | - | - | COND1 | - | - | - | - | - | - | - |
| `service_type` | - | - | - | - | OPT | - | - | - | - | - | - | - |
| `facility_type`| - | - | - | - | - | - | OPT | - | - | - | - | - |
| `accessibility_feature`| - | - | - | - | - | - | - | OPT | - | - | - | - |

*Legend*:
- `REQ`: Mandatory. If missing, clarification required.
- `OPT`: Valid optional slot.
- `OPT*`: If missing, query is accepted but prompts for origin.
- `COND1`: Either (`origin` AND `destination`) are required, OR `stage_number` is required.
- `COND2`: Either `station` is required, OR (`mode_from` AND `mode_to`) are required.
- `-`: Forbidden. If present, indicates extraction or classification boundary error.
- `out_of_scope` Entity Allowance: Out-of-scope queries may contain valid transit entities (`origin`, `destination`, `station`, `landmark`, `route_number`). Annotations are preserved.
