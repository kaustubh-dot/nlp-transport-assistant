# Final Data Coverage Report (Snapshot v1.2.1: Consistency Patch)

**Date:** 2026-09-19  
**Project:** Chennai Multimodal Public Transport & Places Knowledge Base  
**Knowledge Base Version:** `chennai_multimodal_v1.2.1`  
**Status:** Provisional Multisource Knowledge Base with Route Topology & Services (Consistency Patch v1.2.1)  

---

## 1. Executive Summary

This report delivers the audited coverage metrics for the expanded Chennai Multimodal Public Transport & Places Knowledge Base following the ingestion of official MTC administrative datasets, the integration of canonical route topology, trip schedules, and stage fare tables into `canonical_transport.db`, and the final consistency patch across manifests and crosswalks.

All metrics cited in this report derive directly from live SQLite queries against `data/canonical/transit/canonical_transport.db` and registered metadata manifests. All four urban transit modes (CMRL Metro Phase I & II, Southern Railway Suburban Rail, Chennai MRTS, and MTC Bus Network) and geographic intelligence (CMA administrative boundary polygon, localities, and POIs) are represented with full field-level provenance, byte-for-byte immutable Bronze raw archives, Silver normalization, and Gold multi-source canonicalization.

---

## 2. Transit Network Coverage Statistics (Live SQL Audit)

### 2.1. Chennai Metro (CMRL)
- **Operational Physical Stations:** 41 unique physical stations (represented by 43 operational station disclosures from the official CMRL WordPress API, where Central and Alandur serve dual corridors).
- **Canonical Metro Entity Records:** 157 physical stop and platform nodes (after cross-source canonicalization of CMRL API, OSM Overpass, and Community GTFS representations).
- **Coordinate Coverage:** 100.0% WGS84 high-precision decimal coordinates verified.
- **Accessibility Disclosures:** 41 / 41 (100.0%) core physical stations with official CMRL lift, escalator, ramp, wheelchair assistance, and accessible toilet disclosures recorded in the `accessibility` table.
- **Corridors Covered (Operational):**
  - Blue Line (Corridor 1: Wimco Nagar Depot to Chennai International Airport)
  - Green Line (Corridor 2: Puratchi Thalaivar Dr. M.G. Ramachandran Central to St. Thomas Mount)

### 2.2. Future / Phase II Metro (Official CMRL Disclosures)
- **Corridors Ingested:** 3 regional corridor packages derived dynamically from official CMRL disclosure HTML (`cmrl_phase2_corridor_status.html`):
  - Corridor 3 (Purple Line): Madhavaram to SIPCOT (45.8 km)
  - Corridor 4 (Orange Line): Lighthouse to Poonamallee Bypass (26.1 km)
  - Corridor 5 (Red Line): Madhavaram to Sholinganallur (47.0 km)
- **Total Network Length:** 118.9 km
- **Planned Station Count:** 128 stations (target completion: 2028)
- **Status:** Officially marked `under_construction` with raw provenance linked to `CMRL_PHASE2_STATUS_20260918`.

### 2.3. Chennai Suburban Railway (Southern Railway)
- **Canonical Stations & Halts:** 107 physical stations and halts across Chennai Division.
- **Lines Represented:**
  - South Line: Chennai Beach to Chengalpattu & Melmaruvathur
  - West Line: Chennai Central (MMC) to Tiruvallur & Arakkonam
  - North Line: Chennai Central (MMC) to Gummidipoondi & Sullurpeta
- **Station Codes:** Authoritative codes preserved (e.g. MAS, MS, MSB, TBM, CGL, TRL, AJJ).
- **Chennai-Serving External Retention:** 95 external railway stations and halts outside the expanded CMA boundary are retained with `inside_cma = 0` to preserve complete commuter routes.

### 2.4. Chennai MRTS (Mass Rapid Transit System)
- **Corridor:** Elevated viaduct corridor from Chennai Beach to Velachery (and link to St. Thomas Mount).
- **Stations:** 19 viaduct stations with verified platform coordinates and physical interchange connections at Chennai Beach, Chennai Fort, Chennai Park, and St. Thomas Mount.

### 2.5. MTC City Bus Network & Route Crosswalk
- **Official Route Numbers:** 685 active route codes cataloged from official MTC directory disclosures (`mtc_official_routes.html` -> `normalized_official_routes.csv`).
- **Official-to-GTFS Route Crosswalk (`mtc_official_to_gtfs_crosswalk.csv`):**
  - Matched Route Codes: 605 / 685 (88.32%) linking to 2,444 operational GTFS route variants.
    - One-to-one exact matches: 27 (3.94%)
    - One-to-many operational variant matches: 578 (84.38%)
  - Unmatched Route Codes: 80 / 685 (11.68%) transparently preserved without forced mappings.
- **Official Fare Stages:** 1,562 official fare stages cataloged from official MTC stage directory disclosures (`mtc_official_stages.html` -> `normalized_mtc_stages.csv`).
- **Fare-Stage Canonical Stop Linkage:**
  - Matched Stages: 579 (37.07%) — 94 unique stop matches, 485 directional pole-pair / same-name cluster matches.
  - Unmatched Stages: 983 (62.93%) — administrative timing points / rural landmarks not present in GTFS stop posts.
  - Ambiguous Stages: 0 (0.00%) — fully resolved via bus mode prioritization and alphanumeric canonical keys.
- **Official Stage Fares:** 305 stage fare matrix records across 11 service types (Ordinary, Express, Deluxe, Night Services, etc. for stages 1 to 30) from `mtc_official_fares.html` -> `normalized_mtc_fares.csv`.
- **Commercial Route Variants:** 4,614 commercial bus route variants in `transport_routes` (4,619 total routes across all transport modes).
- **Canonical Physical Bus Stops:** 6,870 canonical physical bus stops in `transport_stops`.

### 2.6. Route Topology, Schedule & Tariff Tables (Gold Schema v1.2.1)
- **`route_stops` (96,025 rows):** Ordered stop sequence observations across 3,940 route-directions, mapped to canonical stop IDs with sequence indices. Captures the **representative longest-trip topology per route-direction**. Multi-pattern variant topologies (`route_patterns` / `route_pattern_stops`) are explicitly deferred before full routing implementation.
- **`trips` (47,143 rows):** Scheduled operational trips linking `route_id`, `service_id`, and `trip_headsign`. Community GTFS column shifts on CMRL trips have been corrected, and trailing calendar/test rows filtered out.
- **`stop_times` (1,360,635 rows):** Exact scheduled arrival and departure timestamps mapped to canonical stop IDs. Preserves service hours spanning past midnight ($\ge 24:00:00$) as valid operational offsets. Clustered via `WITHOUT ROWID` on `(trip_id, stop_sequence)` to keep database storage under the GitHub 100 MB limit.
- **`service_calendars` (9 rows):** Weekly operational service profiles (days of week, validity spans).
- **`service_exceptions` (0 rows):** Schema prepared for specific calendar exception dates. Verified that `calendar_dates.txt` is absent from the community GTFS archive.
- **`fare_stages` (1,562 rows):** Official MTC fare stages cross-referenced to canonical physical stops where identifiable (579 matched, 983 unmatched, 0 ambiguous).
- **`fares` (305 rows):** Official statutory stage fare tariffs (G.O. Ms No. 48) covering 11 service classifications and 30 fare stages.

---

## 3. Geographic Intelligence & POIs

- **CMA Administrative Boundary:** Official OpenCity-hosted Government of Tamil Nadu dataset; source: CUMTA MultiPolygon (7,157 vertices, bounding box 12.468°N to 13.563°N, 79.549°E to 80.349°E).
- **Point-in-Polygon Classification:** All stops and places classified via exact ray casting against the official boundary polygon.
  - Stops Inside CMA: 7,041 (98.67%)
  - Stops Outside CMA (Chennai-serving railway/commuter stops): 95 (1.33%)
  - Total Physical Stops: 7,136
- **Total Places & POIs:** 1,621 normalized places in `places` catalog.
  - Places Inside CMA: 1,282 (79.09%)
  - Places Outside CMA: 339 (20.91%)
- **Category Breakdown:**
  - Hospitals & Healthcare: 412
  - Colleges & Schools: 345
  - Universities & Higher Education: 128
  - Tourist Attractions & Cultural Heritage: 96
  - Shopping Malls & Commercial Markets: 84
  - Government Offices & Courts: 65
  - IT Parks & Major Corridors: 48
  - Transport Terminals & Aerodromes: 32
  - Stadiums & Sports Complexes: 22
  - Beaches & Waterfronts: 18
  - General Landmarks: 371

---

## 4. Multimodal Hubs, Interchanges & Walking Transfers (Decoupled Gates)

- **Multimodal Hub Candidates:** 62 candidate hub groupings (grouping 211 member entities).
  - **Tier 1 Core Hubs (98 pairs):** Central, Egmore, Guindy, St. Thomas Mount, Airport/Tirusulam, Tambaram, CMBT/Koyambedu, Chennai Beach, Velachery, Alandur.
  - Status: Evaluated with `verified = 0` (provisional review queue).
- **Interchange Candidates:** 45 collision-free interchange connections (transfer distance $\le 250\text{m}$) assigned unique SHA-256 pair-hashed IDs (`INT_<hash>`), evaluated with `confirmed = 0`.
- **Walking Transfer Candidates:** 151 pedestrian transfer candidates evaluated with straight-line distance, walking times, obstacle hazard notes, and strictly flagged `walkable = unverified_walking_transfer`.

---

## 5. Multilingual Name Coverage Breakdown

- **English (`en`):** 100.0% coverage across canonical stops, routes, and places.
- **Tamil (`ta`):** 421 distinct canonical stops have source-provided Tamil script names recorded in `stop_names` (422 total Tamil name rows). 120+ places carry source-provided Tamil names.
- **Devanagari Hindi (`hi`):** **0.0%** across all raw transit sources. Local transport authorities in Chennai do not publish Hindi strings in their open disclosures. Synthetic translations and transliterations are omitted during the data expansion phase to preserve source truth.

---

## 6. Provenance, Storage Footprint & Benchmark Protection

- **Raw Provenance (Bronze):** 11 raw files preserved byte-for-byte in dated directories with SHA-256 checksums verified in `metadata/raw_file_manifest.csv`.
- **Canonical Resolution:** 7,246 normalized stop records resolved to 7,136 canonical physical stops via 163 automatic high-confidence same-mode merges.
- **Entity Source Links:** 9,695 explicit provenance links in `entity_source_links` (7,246 stop links connecting every source record to its canonical entity, and 2,449 route links connecting official MTC and CMRL routes to canonical routes).
- **Database Storage Footprint:** `canonical_transport.db` is 81.27 MB, safely below the 100 MB GitHub file size limit.
- **Frozen Benchmark Protection:** **100% UNTOUCHED.** The frozen NLP split (3,916 train / 716 val / 572 test, frozen 70/15/15 split, Seed 42) and the 149-query gold acceptance test suite remain completely unmodified. All 74 existing regression tests pass cleanly.
