# Collection Completeness Audit & Gap Analysis Report (v1.2)

**Date:** 2026-09-18  
**Project:** Chennai Multimodal Public Transport & Places Knowledge Base  
**Knowledge Base Version:** `chennai_multimodal_v1.2` (Provisional Multisource Knowledge Base with Route Topology & Services)  
**Status:** Ingestion & Canonical Topology Complete  

---

## 1. Executive Summary

This report delivers the comprehensive collection audit and gap analysis across all public transport modes and geographic intelligence for the Chennai Metropolitan Area. In accordance with the data expansion specifications, every source and data category is evaluated for actual raw ingestion into Bronze, official provenance, and verified downstream coverage across Silver normalized records and Gold canonical tables.

---

## 2. Ingestion Audit by Mode & Category

### 2.1. Chennai Metro (CMRL)
- **Operational Stations:**
  - *Source 1 (CMRL WordPress REST API):* 43 station disclosures (representing 41 unique physical stations, with dual-corridor listings for Central and Alandur). Ingested into `data/raw/cmrl/2026-09-18/cmrl_station_information_api.json`.
  - *Source 2 (OSM Overpass):* 178 subway platform, entrance, and station nodes.
  - *Source 3 (Community GTFS):* 35 metro station stop entries.
  - *Canonicalization Status:* All 3 sources canonicalized into 41 core physical stations in `transport_stops`, with multi-source links in `entity_source_links`.
- **Accessibility & Facilities:**
  - 100% of core CMRL stations have official lift, escalator, ramp, wheelchair assistance, and accessible toilet disclosures populated in `accessibility`.
- **Phase II Corridors (Corridors 3, 4, 5):**
  - Acquired official CMRL Phase II disclosure HTML (`cmrl_phase2_corridor_status.html`) and official map PDF (`cmrl_phase2_map_official.pdf`, 3.34 MB).
  - Corridors 3, 4, and 5 (118.9 km, 128 planned stations, target 2028) dynamically parsed into `transport_routes` with `under_construction` status and explicit provenance to `CMRL_OFFICIAL`.

### 2.2. Chennai Suburban Railway (Southern Railway)
- **Stations & Network:**
  - 107 physical stations and halts across Chennai Division canonicalized in `transport_stops`.
  - Covers South Line (Beach to Chengalpattu), West Line (Central MMC to Arakkonam), and North Line (Central MMC to Gummidipoondi/Sullurpeta).
  - Preserves authoritative station codes (MAS, MS, MSB, TBM, CGL, TRL, AJJ).
  - 95 external railway stations outside the expanded CMA boundary are retained with `inside_cma = 0` to preserve complete commuter transit corridors.
- **Timetable Gaps:**
  - Official static bulk GTFS is not published by Southern Railway. Line-level operating spans are captured; dynamic trip enquiries rely on NTES/UTS. Documented as Type B in `MANUAL_ACTION_REQUIRED.md`.

### 2.3. Chennai MRTS (Mass Rapid Transit System)
- **Corridor & Stations:**
  - Elevated viaduct corridor from Chennai Beach to Velachery (and link to St. Thomas Mount).
  - 19 viaduct stations with verified platform coordinates and physical interchange connections at Chennai Beach, Chennai Fort, Chennai Park, and St. Thomas Mount.

### 2.4. MTC City Bus Network
- **Official Ingestion:**
  - Acquired official MTC fare table (`mtc_official_fares.html`), 685 official route codes (`mtc_official_routes.html`), and 1,562 official bus stages (`mtc_official_stages.html`).
  - Parsed into Silver layers (`normalized_official_routes.csv`, `normalized_mtc_stages.csv`, `normalized_mtc_fares.csv`) and loaded into Gold tables `fare_stages` (1,562 rows) and `fares` (305 rows).
- **Commercial Routes & Sequences:**
  - 4,614 commercial route variants in canonical `transport_routes`.
  - 6,870 canonical physical bus stops in `transport_stops`.
  - 96,025 ordered route-stop sequence observations across 3,940 route-directions in `route_stops`.
  - 47,143 scheduled operational trips in `trips`.
  - 1,360,635 scheduled stop-time observations in `stop_times`.
- **Major Bus Terminals:**
  - Dedicated terminals cataloged: CMBT Koyambedu, KCBT Kilambakkam, MMBT Madhavaram, Broadway, T. Nagar, Adyar, Poonamallee, Red Hills, Thiruvanmiyur, Tambaram, Avadi, Velachery.

### 2.5. Geographic Intelligence & POIs
- **Official CMA Boundary:**
  - Acquired official OpenCity-hosted Government of Tamil Nadu dataset; source: CUMTA boundary MultiPolygon (`cumta_cma_boundary_official.geojson`, 7,157 vertices, bounding box ~12.468°N to 13.563°N).
  - Replaced hardcoded bounding box with exact ray-casting point-in-polygon classification.
- **Places & POIs:**
  - 1,621 normalized places in `places` catalog (1,282 inside CMA, 339 outside CMA).
  - High-value categories: 412 hospitals, 345 colleges/schools, 128 universities, 96 tourist attractions, 84 malls, 65 government offices, 48 IT parks, 32 transport terminals, 22 stadiums, 18 beaches.

---

## 3. Upstream Gaps & Handling Strategy

| Gap Item | Agency | Root Cause | Handling Strategy |
| :--- | :--- | :--- | :--- |
| **CUMTA Open Data GTFS** | CUMTA | `opendata.cumta.org` returns `NXDOMAIN`; `cumta.org` is an internal WebGIS dashboard requiring government login/captcha. | Logged technical blocker in `MANUAL_ACTION_REQUIRED.md`. Official CMA boundary acquired via OpenCity-hosted Government of Tamil Nadu dataset; source: CUMTA. Retained 8.7MB community GTFS as Tier-3 overlapping evidence. |
| **Southern Railway Static GTFS** | Southern Railway | Indian Railways does not publish static machine-readable bulk GTFS timetables. | Retained complete station network, lines, codes, and commuter sequences via OSM and GTFS. Logged in `MANUAL_ACTION_REQUIRED.md`. |
| **MTC Real-Time Telemetry** | MTC | Live GPS feeds are hosted behind dynamic mobile app session tokens. | Static route directory (685 routes), fare stages (1,562), stage fares (305), and static GTFS schedule sequences (1,360,635 stop times) fully ingested into Gold tables. Deferred real-time telemetry to downstream phase. |
| **Devanagari Hindi Station Names** | All Agencies | Raw government sources publish English and Tamil strings, but do not provide Hindi strings for Chennai transit stations. | Corrected coverage claim from 100% to 0%. Deferred synthetic translation and transliteration to the multilingual NLP phase. |
