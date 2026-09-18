# Chennai Multimodal Public Transport & Places: Data Requirements Specification

**Document:** Data Contract & Ingestion Requirements  
**Phase:** Phase 1  
**Project:** Chennai Multimodal Public Transport Assistant & Knowledge Base  
**Coverage Target:** Chennai Metropolitan Area (CMA) + Chennai-Serving Transport Corridors  

---

## 1. Scope & System Architecture

This document establishes the source-independent schema, entity requirements, and validation rules for the expanded Chennai Multimodal Public Transport & Places Knowledge Base.

### 1.1. Core Multi-Tier Concept
The knowledge base models the physical, operational, and geographic reality of Chennai transport across four layers:
1. **Bronze (Raw Ingestion):** Verbatim, immutable, byte-for-byte source payloads (GTFS archives, OSM raw query extracts, scraped JSON/HTML, official PDFs). Never deduplicated, never cleaned.
2. **Silver (Normalized Staging):** Uniformly typed, standardized coordinates, normalized timestamps, preserved multilingual names, and source-to-source candidate matches.
3. **Gold (Canonical Transit & Geography):** Reconciled, entity-resolved knowledge graph distinguishing physical stops, transport hubs, multimodal interchanges, walking transfers, and geographic places.
4. **Metadata & Provenance:** Full end-to-end lineage mapping every canonical field back to primary evidence and licensing status.

---

## 2. Geospatial Boundary & Network Relevance Policy

### 2.1. Official CMA Boundary Polygon
- The canonical spatial filter for **Localities** and **Landmarks/POIs** is the official **Chennai Metropolitan Area (CMA)** boundary polygon established by the Chennai Metropolitan Development Authority (CMDA).
- This boundary polygon will be fetched and preserved as an official GeoJSON asset in `data/raw/government/`.

### 2.2. Transit Network Relevance Rule (The "Chennai-Serving" Principle)
- **Do NOT discard transit stations, stops, routes, or suburban endpoints merely because they lie outside the CMA polygon.**
- Key suburban rail corridors, express bus stages, and intercity interchange nodes serving daily Chennai commuters extend beyond CMA administrative limits (e.g. Arakkonam, Tiruvallur, Tiruttani, Gummidipoondi, Sullurpeta, Chengalpattu, Kanchipuram, Melmaruvathur).
- Every stop and station record will carry an explicit boolean attribute:
  ```text
  inside_cma: boolean (true | false)
  ```
- Any transit entity where `inside_cma = false` is retained in the knowledge base if it belongs to a route, corridor, or service operating into or connected to Chennai.

### 2.3. Coordinate Sanity & Physical Plausibility Filter
Instead of arbitrary rectangular bounding box clipping, coordinate validation follows this cascade:
```text
Coordinate Sanity Check
        │
        ▼
Is coordinate physically plausible for Chennai and surrounding service corridors?
(Latitude ~12.0000°N to ~14.0000°N, Longitude ~79.0000°E to ~81.0000°E)
        ├── NO  → Flag as INVALID_COORDINATE (log conflict, quarantine)
        └── YES
             │
             ▼
Is entity inside the official CMA boundary polygon?
        ├── YES → inside_cma = true
        └── NO  → inside_cma = false
                     │
                     ▼
Is entity part of a transit route, service, or corridor serving the Chennai network?
        ├── YES → KEEP (retained as valid Chennai-serving external stop/station)
        └── NO  → Investigate / exclude from canonical Chennai transit graph
```

---

## 3. Entity Schemas & Required Attributes

### 3.1. Agencies (`transport_agencies`)
Captures all official transport authorities and operating bodies.

| Field | Type | Required? | Description |
| :--- | :--- | :--- | :--- |
| `agency_source_id` | string | Yes | Source identifier (e.g. `CMRL`, `MTC`, `SR`) |
| `agency_name` | string | Yes | Full official authority name |
| `agency_code` | string | Yes | Short operational code |
| `mode` | string | Yes | Primary mode (`metro`, `bus`, `suburban_rail`, `mrts`, `multimodal`) |
| `website` | string | No | Official website URL |
| `source` | string | Yes | Registry source identifier |
| `status` | string | Yes | `active` \| `historical` \| `planned` |

Expected initial agencies:
- **CMRL**: Chennai Metro Rail Limited
- **MTC**: Metropolitan Transport Corporation (Chennai) Ltd.
- **Southern Railway**: Southern Railway Zone, Indian Railways (Chennai Suburban & MRTS)
- **CUMTA**: Chennai Unified Metropolitan Transport Authority

---

### 3.2. Stops and Stations (`transport_stops`)
Individual physical passenger boarding points.

| Field | Type | Required? | Description |
| :--- | :--- | :--- | :--- |
| `source_stop_id` | string | Yes | Upstream source identifier |
| `official_name` | string | Yes | Official Latin/English name |
| `alternate_names` | array[string] | No | Known aliases, colloquial names, abbreviations |
| `name_ta` | string | No | Official Tamil name in Tamil script |
| `name_hi` | string | No | Curated/source Hindi name (if present) |
| `mode` | string | Yes | `metro` \| `suburban_rail` \| `mrts` \| `bus` |
| `stop_type` | string | Yes | `metro_station`, `railway_station`, `mrts_station`, `bus_stop`, `bus_terminal`, `platform`, `entrance` |
| `latitude` | float | Yes | Decimal degrees WGS84 |
| `longitude` | float | Yes | Decimal degrees WGS84 |
| `inside_cma` | boolean | Yes | Whether coordinates fall inside official CMA polygon |
| `parent_station` | string | No | Reference to enclosing parent station or complex |
| `agency` | string | Yes | Operating agency source code |
| `status` | string | Yes | `operational` \| `under_construction` \| `planned` \| `proposed` \| `inactive` |
| `zone` | string | No | Fare or administrative zone |
| `wheelchair_accessibility` | int | No | `1` (accessible), `0` (not accessible), `null` (unknown) |

---

### 3.3. Metro System Data (CMRL Operational & Phase II)

#### Operational Network (Phase I & Extension Reference Expectations)
- **Corridors:**
  - Blue Line (Corridor 1): Wimco Nagar Depot / Wimco Nagar to Chennai International Airport
  - Green Line (Corridor 2): Puratchi Thalaivar Dr. M.G. Ramachandran Central to St. Thomas Mount
- **Interchanges:** Puratchi Thalaivar Dr. M.G. Ramachandran Central, Arignar Anna Alandur.
- **Reference Expectation:** ~41 unique operational stations (approx. 43 station records including multi-line platforms). Note: Acquisition will discover live official counts.
- **Required Fields:**
  - Station code (e.g. `CEN`, `AIR`, `ALN`, `GDY`)
  - Platform configuration (island, side, elevated, underground)
  - Entrance / exit gates and street orientation
  - Facilities: Lift, Escalator, Tactile Paths, Accessible Toilet, General Toilet, Parking (2-wheeler / 4-wheeler), Bicycle racks
  - First / last train departures per terminal / direction
  - Operating status (`operational`)
  - Multilingual names (English, Tamil, historical names like Madras Central)

#### Phase II Network (Under Construction & Planned Reference Expectations)
- **Corridors:**
  - Corridor 3: Madhavaram Milk Colony to SIPCOT 2 (~45.8 km)
  - Corridor 4: Light House to Poonamallee Bypass (~26.1 km)
  - Corridor 5: Madhavaram Milk Colony to Sholinganallur (~47.0 km)
- **Required Fields:**
  - Corridor number & Package identifier
  - Station alignment (underground / elevated / at-grade)
  - Construction status (`under_construction`, `planned`, `tendered`)
  - Target commissioning / expected opening year (if officially published)
  - Source date of status disclosure

---

### 3.4. Chennai Suburban Railway Network (Southern Railway)
- **Lines & Corridors:**
  1. South Line: Chennai Beach – Tambaram – Chengalpattu – Melmaruvathur
  2. West Line: Chennai Central (MMC) – Villivakkam – Avadi – Tiruvallur – Arakkonam
  3. North Line: Chennai Central (MMC) – Ennore – Gummidipoondi – Sullurpeta
  4. West-South Circular / Chengalpattu-Arakkonam link
- **Required Fields:**
  - Station code (e.g. `MSB` Beach, `MS` Egmore, `MAS` Central, `TBM` Tambaram, `CGL` Chengalpattu, `TRL` Tiruvallur, `AJJ` Arakkonam)
  - Station sequence and kilometer chainage
  - Fast Local vs Slow Local stopping patterns
  - First / last services and operational schedules
  - Tamil script names and historical colonial names

---

### 3.5. Chennai MRTS (Mass Rapid Transit System)
- **Corridor:** Chennai Beach to Velachery (and Velachery–St. Thomas Mount extension link under completion).
- **Mode Treatment:** Modeled explicitly as `mrts` (distinct rail category from broad gauge suburban).
- **Required Fields:** Station sequence, elevated viaduct coordinates, integration with suburban at Beach/Fort/Park, and integration with Metro/Suburban at St. Thomas Mount.

---

### 3.6. MTC Bus Network
- **High-Priority Acquisition Target:**
  - Route numbers and variants (e.g. `102`, `102A`, `102C`, `102K`, `102P`, `102X`, `21G`, `29C`, `570`, `570S`).
  - Directionality: Inbound, Outbound, UP, DOWN, Loop, Short-turn.
  - Ordered stop sequence from origin to terminus.
  - Stop/Stage designations (Fare stage vs ordinary stop).
  - Service categories: Ordinary (White board), Express, Deluxe, AC (Volvo).
  - First and last scheduled trips, frequency/headway.
  - Route geometry (GeoJSON shape polyline).

---

### 3.7. Major Bus Terminals & Depots
Dedicated multimodal nodes with extensive passenger facilities:
- CMBT Koyambedu, KCBT Kilambakkam (Kalaignar Centenary Bus Terminus), MMBT Madhavaram, Broadway, T. Nagar, Adyar Depot, Poonamallee, Red Hills, Thiruvanmiyur Depot, Tambaram, Avadi, Tambaram Sanatorium (MEPZ), Iyyappanthangal.
- **Fields:** Terminal name, Tamil name, geographical polygon/coordinates, bays, routes terminating/originating, nearby rail/metro connections.

---

### 3.8. Station Entrances & Exits
- Stations with multiple entry/exit points must not be collapsed into a single point.
- **Fields:** `station_id`, `entrance_id`, `gate_number` (e.g. Gate 1, Gate 2, Entry A), `latitude`, `longitude`, `street_name`, `wheelchair_ramp_available`, `lift_access`.

---

### 3.9. Localities & Neighborhoods
- **Types:** `city`, `suburb`, `neighborhood`, `locality`, `village`, `revenue_ward`.
- **Fields:** `place_id`, `name`, `name_ta`, `name_en`, `place_type`, `latitude`, `longitude`, `boundary_geojson` (where available), `inside_cma`.

---

### 3.10. Landmarks & Points of Interest (POIs)
Filtered by the official CMA polygon and transport relevance:
- **Target Categories:**
  - `hospital` (e.g. Rajiv Gandhi Government General Hospital, Apollo, MIOT, Stanley)
  - `university` / `college` (e.g. Anna University, IIT Madras, Madras University, Loyola, Pachaiyappa's)
  - `mall` / `market` (e.g. Phoenix MarketCity, Express Avenue, Koyambedu Wholesale Market, T. Nagar Ranganathan St)
  - `beach` / `tourism` (e.g. Marina Beach, Elliot's Beach, Santhome Basilica, Kapaleeshwarar Temple, Fort St. George)
  - `it_park` / `employment_hub` (e.g. TIDEL Park, Ramanujan IT City, Ascendas, DLF Cybercity, MEPZ, Siruseri SIPCOT)
  - `government_office` (e.g. Ripon Building, Secretariat Fort St. George, High Court)
  - `airport` / `stadium` (e.g. Chennai International Airport, MA Chidambaram Chepauk Stadium, Jawaharlal Nehru Stadium)
  - `major_junction` (e.g. Kathipara Junction, Madhya Kailash, Gemini Flyover, Koyambedu Roundabout)

---

### 3.11. Multilingual Names & Historical Name Variants
To prepare for eventual multilingual NLU without pre-generating artificial pipelines:
- **Fields Retained:**
  - `name`: Default source name
  - `name:en`: English name
  - `name:ta`: Tamil script name
  - `alt_name`: Alternative English/Tamil names
  - `old_name`: Historical/colonial names (e.g. *Madras*, *Meenambakkam Airport*, *Mount Road*, *Park Town*)
  - `short_name`: Recognized abbreviations (e.g. *CMBT*, *KCBT*, *MMC*, *DMS*)
  - `loc_name`: Local colloquial names

---

## 4. Quality Gates & Non-Negotiable Collection Principles

1. **Zero Raw Mutation:** Raw archives preserved byte-for-byte in dated snapshot folders (`data/raw/<source>/YYYY-MM-DD/`).
2. **Provenance Traceability:** Every canonical row maps to one or more `source_id` and `source_record_id` entries with SHA-256 validation.
3. **Licensing Safety:** Unclear licensing terms are flagged as `REVIEW_REQUIRED`. Data marked `REVIEW_REQUIRED` cannot be distributed without explicit review.
4. **Separation of Concerns:** Transport reference data collection must never overwrite or mutate the frozen NLP benchmark (`split/*.csv`, `acceptance_test_suite.json`).
