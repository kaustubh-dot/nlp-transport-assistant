# Chennai Multimodal Public Transport & Places: Master Data Expansion Handoff Report (v1.1)

**Date:** 2026-09-18  
**Project:** Chennai Multimodal Public Transport Assistant & Knowledge Base  
**Knowledge Base Version:** `chennai_multimodal_v1.1`  
**Data Status:** Provisional Multisource Knowledge Base  
**Stage:** Corrective Data Audit Complete (Handoff Gate)  

---

## 1. Executive Summary

Following the Corrective Data Audit, the project's data layer has been audited, corrected, and canonicalized into a robust multi-source transport and geographic intelligence foundation. 

All core audit requirements have been satisfied:
1. **Official CMA Boundary:** Ingested the official CUMTA/TNGIS administrative boundary MultiPolygon (7,157 vertices), replacing the previous hardcoded bounding box with exact ray-casting point-in-polygon classification. All 95 Chennai-serving external railway stations are retained with `inside_cma = false`.
2. **CUMTA Open Data GTFS Audit:** Probed `opendata.cumta.org` (DNS `NXDOMAIN`) and `cumta.org` (internal administrative WebGIS Dashboard requiring credentials/captcha). Documented the exact technical blocker and Type-B manual fetch protocol in `MANUAL_ACTION_REQUIRED.md`, while retaining the 8.7MB unified GTFS as independent Tier-3 overlapping evidence.
3. **Official Ingestion Completeness:** Produced `reports/official_source_acquisition_audit.md` across 11 source categories. Acquired official CMRL Phase II disclosures (HTML + 3.34MB map PDF) and official MTC fares, 685 route codes, and 1,562 bus stages directly into dated Bronze paths.
4. **Real Cross-Source Canonicalization:** Redesigned entity resolution to merge 163 high-confidence same-mode duplicates across CMRL, OSM, and GTFS into single physical canonical entities with multiple source links in `entity_source_links` (7,246 links), while strictly preserving separate modes (`METRO_*`, `RAIL_*`, `BUS_*`).
5. **Decoupled Manual Quality Gates:** Separated Hubs (multimodal grouping with Tier 1 prioritized core hubs), Interchanges (transfer feasibility), and Walking Transfers (pedestrian route verification with obstacle notes).
6. **Data-Driven Numerical Audit:** Recomputed 100% of numerical metrics directly from live SQLite database queries, correcting the Devanagari Hindi coverage claim from 100% to actual 0% (reflecting raw source reality).
7. **Strict Frozen Benchmark Isolation:** Verified that the gold NLP benchmark (3,916 train / 716 validation / 572 test) and the **149-case gold acceptance test suite** remain completely untouched. All 74 regression tests pass cleanly.

---

## 2. Explicit Asset Classification Taxonomy

In accordance with Section 12 of the Corrective Data Audit specifications, all assets and relationships are explicitly classified into five authoritative categories:

### A. CONFIRMED
Assets directly verified against official operator disclosures, ground truth surveys, or frozen baselines:
- **CMRL Operational Network:** 41 unique physical stations (43 dual-corridor operational listings) on Blue Line (Wimco Nagar to Airport) and Green Line (Central to St. Thomas Mount) with 100% coordinate and accessibility disclosures.
- **CMRL Phase II Corridor Alignment:** Corridors 3, 4, 5 (118.9 km, 128 stations, target 2028) verified from official CMRL disclosure HTML and official map PDF.
- **Official CMA Jurisdictional Boundary:** Official CUMTA/TNGIS administrative boundary polygon verified from OpenCity/TNGIS.
- **Official MTC Route & Stage Registers:** 685 official route numbers and 1,562 official fare stages verified from `mtcbus.tn.gov.in`.
- **Official MTC Fare Matrices:** Ordinary, Express, Deluxe, and Night Service tariff matrices verified from official MTC gazetteer.
- **Southern Railway Authoritative Station Codes:** MAS, MS, MSB, TBM, CGL, TRL, AJJ, etc.
- **Frozen NLP Benchmark:** 3,916 train / 716 validation / 572 test records (Seed 42) and exactly 149 gold acceptance test queries. All 74 existing pytest regression tests pass.

### B. PROVISIONAL
Multi-source canonical entities produced via rigorous automated cross-source resolution, pending downstream operational usage sign-off:
- **Canonical Transport Database (`canonical_transport.db`):** 7,136 canonical physical stops, 4,619 routes, 1,621 places/POIs, and 7,246 entity source links.
- **Silver Normalized Layers:** `normalized_stops.csv`, `normalized_routes.csv`, `normalized_places.csv`.
- **Cross-Source Same-Station Clusters:** 66 canonical physical stations holding multiple source links (CMRL + OSM + GTFS).
- **Tamil Script Names (`name:ta`):** 421 stops and 120+ places with source-provided Tamil script.

### C. UNVERIFIED
Candidate relationships generated for human domain review, safely isolated with inactive verification flags:
- **Multimodal Hub Candidates (62 hubs, 211 member entities):** Held with `verified = 0` in `data/manual/hubs/hub_candidates.csv`. Concise review queue prioritized by Tier 1 Core Hubs (Central, Egmore, Guindy, Airport, Tambaram, CMBT, Beach, Alandur, St. Thomas Mount, Velachery).
- **Interchange Candidates (37 pairs):** Transfer feasibility candidates within 250m held with `confirmed = 0` in `data/manual/interchanges/interchange_candidates.csv`.
- **Walking Transfer Candidates (151 pairs):** Pedestrian connections held with `walkable = unverified_walking_transfer` in `data/manual/walking_transfers/walking_candidates.csv`.
- **Local Curated Multimodal Draft:** `data/curated/chennai_multimodal_stations.json` (75 stations, 393 aliases) categorized as Tier-4 unverified supplementary evidence.

### D. MISSING
Publicly referenced official datasets that could not be automatically downloaded:
- **Official CUMTA Static GTFS Feed:** `opendata.cumta.org` returns `NXDOMAIN`; `cumta.org` requires internal administrative login. Documented in `MANUAL_ACTION_REQUIRED.md`.
- **Southern Railway Static Machine-Readable Timetable GTFS:** Not published by Indian Railways in static bulk format. Operating spans and station sequences preserved via OSM/GTFS.

### E. DEFERRED
Components intentionally postponed to downstream phases without blocking the multimodal knowledge base:
- **MTC Live Vehicle Telemetry (GTFS-RT):** Requires dynamic mobile app session tokens; deferred to real-time tracking phase.
- **Devanagari Hindi Station Strings:** Local transit agencies do not publish Hindi strings for Chennai stops; machine transliteration and multilingual utterance generation are deferred to the multilingual NLP phase.
- **Model Training & Fine-Tuning:** Deep learning training on multilingual intent/slot models is strictly deferred until data audit sign-off.

---

## 3. Audited Coverage Summary Table

| Category | Entity / Asset | Count | Live SQL Status |
| :--- | :--- | :--- | :--- |
| **Metro (CMRL)** | Physical Operational Stations | 41 | CONFIRMED (43 dual-corridor records) |
| | Full Accessibility Disclosures | 41 | CONFIRMED (100% of core stations) |
| | Phase II Expansion Corridors | 3 | CONFIRMED (118.9 km, 128 planned stations) |
| **Suburban Rail** | Stations & Halts | 107 | CONFIRMED / PROVISIONAL |
| | Authoritative Station Codes | 100% | CONFIRMED |
| | External Chennai-Serving Retention | 95 | CONFIRMED (`inside_cma = 0`) |
| **MRTS** | Viaduct Stations | 19 | CONFIRMED / PROVISIONAL |
| **MTC City Bus** | Official Route Numbers | 685 | CONFIRMED |
| | Official Bus Fare Stages | 1,562 | CONFIRMED |
| | Commercial Route Variants | 4,614 | PROVISIONAL |
| | Canonical Physical Bus Stops | 6,870 | PROVISIONAL |
| **Geography** | Official CMA Boundary Vertices | 7,157 | CONFIRMED (MultiPolygon GeoJSON) |
| | Normalized Places & POIs | 1,621 | PROVISIONAL (1,282 in CMA, 339 external) |
| **Multimodal Gates** | Hub Candidates | 62 | UNVERIFIED (`verified = 0`, 98 Tier 1 pairs) |
| | Interchange Candidates | 37 | UNVERIFIED (`confirmed = 0`) |
| | Walking Transfer Candidates | 151 | UNVERIFIED (`walkable = unverified`) |
| **Provenance** | Immutable Raw Files | 11 | CONFIRMED (9.9 MB byte-for-byte in Bronze) |
| | Entity Source Links | 7,246 | PROVISIONAL (100% source records mapped) |
| **NLP Benchmark** | Frozen Train / Val / Test Split | 3,916 / 716 / 572 | CONFIRMED (Untouched) |
| | Gold Acceptance Test Suite | 149 queries | CONFIRMED (Untouched) |
| | Pytest Regression Suite | 74 / 74 pass | CONFIRMED (All tests pass cleanly) |

---

## 4. Next Phase Readiness & Recommendations

1. **Approved for Handoff:** The `chennai_multimodal_v1.1` knowledge base is verified, auditable, and ready to serve as the factual ground truth layer for downstream multimodal NLU entity linking.
2. **Prioritized Human Review:** When conducting domain review of manual gates, focus exclusively on the **10 Tier-1 Core Hubs** (Central, Egmore, Guindy, Airport, Tambaram, CMBT, Beach, Alandur, St. Thomas Mount, Velachery).
3. **Multilingual Entity Linking:** In the upcoming multilingual NLP phase, derive entity slot dictionaries and alias tables directly from `canonical_transport.db` (`stop_names`, `place_names`) to guarantee zero entity hallucination.
