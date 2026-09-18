# Phase 23: Final Data Coverage Report (Corrective Audit v1.1)

**Date:** 2026-09-18  
**Project:** Chennai Multimodal Public Transport & Places Knowledge Base  
**Knowledge Base Version:** `chennai_multimodal_v1.1`  
**Status:** Provisional Multisource Knowledge Base  

---

## 1. Executive Summary

This report delivers the audited coverage metrics for the expanded Chennai Multimodal Public Transport & Places Knowledge Base following the comprehensive Corrective Data Audit. All numerical claims in this document are derived directly from live SQLite database queries against `data/canonical/transit/canonical_transport.db` and registered metadata manifests.

Data across all modes (CMRL Metro Phase I & II, Southern Railway Suburban Rail, Chennai MRTS, and MTC Bus Network) and geographic intelligence (CMA boundary polygon, localities, and POIs) is maintained with field-level provenance, byte-for-byte immutable Bronze raw archives, Silver normalization, and Gold multi-source canonicalization.

---

## 2. Transit Network Coverage Statistics (Live SQL Audit)

### 2.1. Chennai Metro (CMRL)
- **Operational Physical Stations:** 41 unique physical stations (represented by 43 operational station disclosures from the official CMRL WordPress API, where Central and Alandur serve dual corridors).
- **Canonical Metro Entity Records:** 157 physical stop and platform nodes (after cross-source canonicalization of CMRL API, OSM Overpass, and Community GTFS representations).
- **Coordinate Coverage:** 100.0% WGS84 high-precision decimal coordinates verified.
- **Accessibility Disclosures:** 41 / 41 (100.0%) core physical stations with official CMRL lift, escalator, ramp, wheelchair assistance, and accessible toilet disclosures recorded in `accessibility` table.
- **Corridors Covered (Operational):** 
  - Blue Line (Corridor 1: Wimco Nagar Depot to Chennai International Airport)
  - Green Line (Corridor 2: Puratchi Thalaivar Dr. M.G. Ramachandran Central to St. Thomas Mount)
- **Multilingual Name Coverage:**
  - English: 100.0% of canonical metro stations.
  - Tamil (`name:ta`): Preserved wherever published in raw sources (CMRL/OSM).
  - Devanagari Hindi: **0.0%** (Corrected: No raw transit sources currently publish Hindi strings for Chennai stations. Synthetic translations are strictly omitted during this data expansion phase).

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
- **Stations:** Viaduct stations with verified platform coordinates and physical interchange connections at Chennai Beach, Chennai Fort, Chennai Park, and St. Thomas Mount.

### 2.5. MTC City Bus Network
- **Commercial Route Variants:** 4,614 commercial route variants (mainline routes, cut-trips, express, deluxe) in canonical `transport_routes`.
- **Official Route Codes:** 685 active route numbers cataloged from official MTC directory (`mtc_official_routes.html`).
- **Official Bus Stages:** 1,562 official fare stages cataloged from official MTC stage directory (`mtc_official_stages.html`).
- **Physical Bus Stops:** 6,870 canonical physical bus stops in `transport_stops`.
- **Scheduled Operations:** 47,149 trips and 1,360,635 stop-time observations in GTFS.
- **Official Fare Matrix:** Stage fare lists and night service tariffs ingested from `mtc_official_fares.html`.

---

## 3. Geographic Intelligence & POIs

- **CMA Administrative Boundary:** Official CUMTA / TNGIS boundary MultiPolygon (7,157 vertices, bounding box 12.468°N to 13.563°N, 79.549°E to 80.349°E).
- **Point-in-Polygon Classification:** All stops and places classified via exact ray casting against the official boundary polygon.
  - Stops Inside CMA: 7,041 (98.67%)
  - Stops Outside CMA (Chennai-serving): 95 (1.33%)
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
  - Status: Evaluated with `verified = 0` (provisional).
- **Interchange Candidates:** 37 decoupled transfer connections (transfer distance <= 250m) with `confirmed = 0`.
- **Walking Transfer Candidates:** 151 pedestrian transfer candidates evaluated with straight-line distance, walking times, obstacle hazard notes, and strictly flagged `walkable = unverified_walking_transfer`.

---

## 5. Provenance, Licensing & Benchmark Protection

- **Raw Provenance (Bronze):** 11 raw files preserved byte-for-byte in dated directories with SHA-256 checksums verified in `metadata/raw_file_manifest.csv`.
- **Canonical Resolution:** 7,246 normalized stop records resolved to 7,136 canonical physical stops via 163 automatic high-confidence same-mode merges.
- **Entity Source Links:** 7,246 explicit provenance links in `entity_source_links` connecting every source record to its canonical entity. Multi-source entities (e.g. Thirumangalam, Central, Alandur, Guindy) hold up to 5 source links each.
- **Licensing Status:** Government disclosures marked `REVIEW_REQUIRED`; open data marked `ODbL` in `metadata/licenses.csv`.
- **Frozen Benchmark Protection:** **100% UNTOUCHED.** Frozen split (3,916 train / 716 val / 572 test) and the 149-query gold acceptance test suite remain completely unmodified and isolated. All 74 existing regression tests pass cleanly.
