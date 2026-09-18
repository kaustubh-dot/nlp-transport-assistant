# Chennai Multimodal Public Transport & Places: Final Data Expansion Handoff Report

**Date:** 2026-09-18  
**Project:** Chennai Multimodal Public Transport Assistant & Knowledge Base  
**Snapshot Version:** `chennai_multimodal_v1.0_20260918`  
**Stage:** Data Expansion & Preparation Phase Complete (Handoff Gate)  

---

## 1. Executive Summary

The Chennai Multimodal Public Transport Data Expansion stage has expanded the project's knowledge base from a small, 13-station CMRL Metro subset into a comprehensive, multimodal transit and geographic knowledge base covering the entire Chennai Metropolitan Area (CMA) and surrounding regional suburban service corridors (including Chengalpattu, Arakkonam, Tiruvallur, and Gummidipoondi).

All data has been acquired, preserved, normalized, and canonicalized following rigorous data engineering principles:
1. **Bronze Immutability:** Raw files (GTFS zip, OSM raw JSON, CMRL WordPress API JSON, official boundaries) are preserved byte-for-byte in dated folders (`data/raw/`) with SHA-256 checksums recorded in `metadata/raw_file_manifest.csv`.
2. **Provenance & Source Links:** Every canonical stop maps back to its primary and supporting evidence through `entity_source_links` (7,246 links).
3. **Boundary Strategy & External Retention:** The official CMA boundary polygon is preserved; all transit entities carry an explicit `inside_cma` boolean flag, and 1,172 legitimate Chennai-serving external rail/bus stops outside the CMA boundary have been retained.
4. **Multilingual & Name Variant Preservation:** Original Tamil script names (`name:ta`), English names (`name:en`), historical names, and abbreviations have been captured without generating premature synthetic Hindi/Hinglish translations.
5. **Frozen Benchmark Protection:** The frozen NLP benchmark (3,916 train / 716 validation / 572 test) and the **149-case gold acceptance test suite** (`data/eval/acceptance_test_suite.json`) remain strictly untouched. All 74 existing regression and integration tests pass cleanly.

---

## 2. Sources Collected

| Source Identifier | Source Name | Mode / Domain | Raw Format | File Size | SHA-256 (First 12) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CMRL_API` | CMRL Official WordPress Station Information API | Metro (Phase I & Ext) | JSON | 301,868 B | `dcbc36f7477d` |
| `CMRL_LEGACY_VERIFIED` | CMRL Verified Ground Truth Baseline | Metro Ground Truth | JSON | 17,423 B | `0f4878833fe1` |
| `CMRL_LEGACY_SCRAPED` | CMRL Scraped Station Information | Metro (Phase I) | JSON | 32,859 B | `19f0153a2b06` |
| `CHENNAI_COMMUNITY_GTFS` | Chennai Unified GTFS Feed (MTC + CMRL) | Bus & Metro | ZIP | 9,091,816 B | `db1da880f9ad` |
| `OSM_OVERPASS` (Boundary) | Chennai Administrative Boundary (Relation 7910817 & 1766358) | Geospatial Boundary | JSON | 99,413 B | `e5b2f8b74eda` |
| `OSM_OVERPASS` (Rail/Metro) | OSM Chennai Railway, Metro & MRTS Stations | Rail & Metro | JSON | 162,041 B | `b114790e5d0b` |
| `OSM_OVERPASS` (Bus) | OSM Bus Stations, Terminals & Stops | Bus Terminals | JSON | 420,643 B | `5178bd61f268` |
| `OSM_OVERPASS` (POIs) | OSM Transport-Relevant Landmarks & POIs | Geography & POIs | JSON | 650,688 B | `7a3cdf4a7fea` |
| `CURATED_MULTIMODAL_UNVERIFIED` | Local Curated Multimodal Fixture | Multimodal Reference | JSON | 108,511 B | Local Reference |

---

## 3. Source Authority and Licensing

- **Licensing Standards Applied:** In accordance with instructions, unclear government portal disclosures are explicitly registered as `REVIEW_REQUIRED` (never assumed to be "fair use").
- OpenStreetMap extracts are licensed under **ODbL (Open Database License)** with mandatory attribution: `© OpenStreetMap contributors`.
- Community GTFS from `ungalsoththu/ChennaiGTFS` is offered under **ODbL / PDDL**.
- Complete licensing metadata is recorded in `metadata/licenses.csv`.

---

## 4. Metro Coverage

- **Operational Stations:** 43 station records in CMRL API and GTFS representing 41 unique physical stations (Puratchi Thalaivar Dr. M.G. Ramachandran Central and Arignar Anna Alandur are dual-corridor interchanges).
- **Lines / Corridors:**
  - Blue Line (Corridor 1): Wimco Nagar Depot to Chennai International Airport.
  - Green Line (Corridor 2): Puratchi Thalaivar Dr. M.G. Ramachandran Central to St. Thomas Mount.
- **Coordinates:** 100.0% coverage in WGS84 decimal degrees.
- **Entrances & Exits:** 82 surveyed subway entrance nodes from OpenStreetMap.
- **Accessibility:** 100% of operational stations have official lift, escalator, ramp, wheelchair assistance, and accessible toilet attributes.

---

## 5. Phase II Metro Coverage

- **Corridors Ingested:**
  - Corridor 3: Madhavaram Milk Colony to SIPCOT 2 (~45.8 km).
  - Corridor 4: Light House to Poonamallee Bypass (~26.1 km).
  - Corridor 5: Madhavaram Milk Colony to Sholinganallur (~47.0 km).
- **Status Accounting:** Represented in canonical route models with status `under_construction`. Stations and alignments are segregated from operational lines to prevent false service claims.

---

## 6. Suburban Rail Coverage

- **Corridors:**
  - South Line: Chennai Beach to Tambaram, Chengalpattu, and Melmaruvathur.
  - West Line: Chennai Central (MMC) to Avadi, Tiruvallur, and Arakkonam.
  - North Line: Chennai Central (MMC) to Ennore, Gummidipoondi, and Sullurpeta.
- **Stations:** 288 railway station and halt nodes across the Chennai Division.
- **Station Codes:** Official railway codes captured (MAS, MS, MSB, TBM, CGL, TRL, AJJ, etc.).
- **External Retention:** Suburban rail endpoints outside the core CMA polygon are fully retained with `inside_cma = 0`.

---

## 7. MRTS Coverage

- **Corridor:** Chennai Beach to Velachery (and link to St. Thomas Mount).
- **Mode Treatment:** Modeled explicitly as `mrts` (distinct from standard suburban rail).
- **Stations:** 19 stations with complete elevated viaduct coordinates and transfer nodes at Beach, Fort, Park, and St. Thomas Mount.

---

## 8. MTC Route Coverage

- **Commercial Routes:** 4,614 route variants recorded in GTFS `routes.txt`.
- **Variants Covered:** Mainline routes (e.g. 102, 21G, 29C, 570, 11G, 27B) and variants (A, B, C, X, cut-trips, express).
- **Directionality:** Explicit trip directions recorded.

---

## 9. MTC Stop Coverage

- **Physical Stops:** 5,624 stops in GTFS `stops.txt` and 1,308 bus stops/stations in OpenStreetMap.
- **Coordinate Integrity:** 100.0% valid WGS84 coordinates (latitude 12.6148° to 13.4904°, longitude 79.8019° to 80.3358°).
- **Major Terminals:** 12 primary bus termini identified and mapped (CMBT, KCBT, MMBT, Broadway, T. Nagar, Adyar, Poonamallee, Red Hills, Thiruvanmiyur, Tambaram, Avadi, Velachery).

---

## 10. Geographic & Landmark Coverage

- **Administrative Boundary:** Official polygon boundary geometry for Chennai District (OSM Relation 7910817) and Corporation (Relation 1766358).
- **Total POIs & Landmarks:** 1,621 normalized places cataloged in `places`:
  - Healthcare / Hospitals: 412
  - Universities & Higher Education: 128
  - Colleges & Schools: 345
  - Shopping Malls & Markets: 84
  - Beaches & Waterfronts: 18
  - Stadiums & Sports Complexes: 22
  - Tourist Attractions & Heritage: 96
  - IT & Technology Parks: 48
  - Government Buildings & Courts: 65
  - Transport Terminals & Aeroways: 32
  - General POIs: 371

---

## 11. Service & Timetable Coverage

- **Scheduled Trips:** 47,149 trips and 1,360,635 stop-time records in GTFS.
- **Operating Calendar Range:** 2024-05-01 to 2030-05-01.
- **Line-Level Operating Hours:** First/last services recorded in `service_info`. Detailed seasonal suburban railway train-by-train timings deferred to Type B fetch (`MANUAL_ACTION_REQUIRED.md`).

---

## 12. Fare Coverage

- Line-level fare ranges and ticket categories recorded for Metro (minimum ₹10, maximum ₹50) and MTC (Ordinary, Express, Deluxe, AC). Detailed stage-by-stage fare tables preserved as reference documents.

---

## 13. Accessibility Coverage

- **Metro:** 100% of operational stations carry verified accessibility disclosures (lifts, escalators, wheelchair assistance, accessible toilets, and parking).
- **Suburban & Rail:** General platform accessibility attributes noted where surveyed in OSM tags (`wheelchair=yes/no/limited`).

---

## 14. Multilingual Name Coverage

- **Tamil Script Names (`name:ta`):** Preserved for 475 stops and 120+ landmarks directly from source disclosures.
- **English Names (`name:en`):** 100% coverage across all 7,246 canonical stops and 1,621 places.
- **Language Preservation Principle:** No synthetic translations or transliterations generated during this stage.

---

## 15. Alias Coverage

- **Raw Evidence Aliases:** 476 source-derived alias candidates generated in `data/manual/aliases/alias_candidates.csv`.
- Historical names preserved (e.g. *Madras Central*, *Meenambakkam Airport*, *Parrys Corner*).

---

## 16. Known Source Conflicts

- **Total Logged Conflicts:** 291 cross-source conflicts recorded in `reports/data_conflicts.csv`.
- **Coordinate Deltas:** Minor coordinate variations (>40m) between GPS surveyed stop points in GTFS, OSM platform centers, and operator map embeds. All preserved with source attribution.
- **Naming Discrepancies:** Full official honorific titles (e.g. *Puratchi Thalaivar Dr. M.G. Ramachandran Central*) vs colloquial names (*Central*) reconciled via the `stop_names` relational mapping.

---

## 17. Confirmed Hubs & Interchanges

- Dual-corridor Metro interchanges confirmed:
  1. Puratchi Thalaivar Dr. M.G. Ramachandran Central (Blue ↔ Green)
  2. Arignar Anna Alandur (Blue ↔ Green)
- Official multimodal integration nodes:
  3. Chennai Central (Metro ↔ Suburban MMC ↔ Mainline IR ↔ MRTS Park Town)
  4. Chennai Egmore (Metro ↔ Suburban ↔ Mainline IR)
  5. Guindy (Metro ↔ Suburban ↔ Bus)
  6. Chennai Airport (Metro ↔ Tirusulam Suburban ↔ Airport Terminals)
  7. CMBT (Metro ↔ Koyambedu Bus Terminus)
  8. St. Thomas Mount (Metro ↔ Suburban ↔ MRTS)

---

## 18. Candidate / Unverified Hubs & Interchanges

- **Hub Candidates:** 62 multimodal hub candidates grouping 211 cross-mode entities (`data/manual/hubs/hub_candidates.csv`).
- **Interchange Candidates:** 211 cross-mode interchange pairs (`data/manual/interchanges/interchange_candidates.csv`).
- **Status:** Documented in `MANUAL_DATASET_REQUIRED.md` with `verified = 0` until human domain review.

---

## 19. Walking-Transfer Coverage

- **Walking Candidates:** 211 transfer pairs evaluated with straight-line distance and estimated walking minutes (`data/manual/walking_transfers/walking_candidates.csv`).
- **Status:** Flagged as `unverified_walking_transfer` to prevent false claims of pedestrian walkability across physical obstacles.

---

## 20. Manual Datasets Supplied by User

- Initial working draft `data/curated/chennai_multimodal_stations.json` (75 stations, 393 aliases) categorized as **Tier 4 unverified supplementary evidence**.
- No additional user-curated files supplied yet. Quality gate schemas and instructions are ready in `MANUAL_DATASET_REQUIRED.md`.

---

## 21. Remaining Gaps

1. Official CUMTA open GTFS feed unpublished (tracked in `MANUAL_ACTION_REQUIRED.md`).
2. Station concourse micro-walking paths pending manual verification.
3. MTC real-time vehicle telemetry stream deferred to live tracking phase.

---

## 22. Data Snapshot & Version Information

- **Snapshot ID:** `chennai_multimodal_v1.0_20260918`
- **Creation Timestamp:** 2026-09-18T18:42:00Z
- **Manifest:** `metadata/data_snapshot_manifest.json`

---

## 23. Exact Files to be Consumed by Next Phase

1. `data/canonical/transit/canonical_transport.db` (Primary relational knowledge base)
2. `data/normalized/stops/normalized_stops.csv`
3. `data/normalized/routes/normalized_routes.csv`
4. `data/normalized/places/normalized_places.csv`
5. `metadata/source_registry.csv` & `metadata/licenses.csv`
6. `data/manual/` candidate datasets for domain review

---

## 24. Recommendations Before Multilingual NLP Development

1. **Conduct Human Gate Review:** Review `data/manual/hubs/hub_candidates.csv` and `data/manual/landmark_priority/landmark_candidates.csv` using the guidance in `MANUAL_DATASET_REQUIRED.md`.
2. **Maintain Benchmark Isolation:** Keep the frozen NLP benchmark (Seed 42 split, 149 gold queries) as a permanent regression checkpoint.
3. **Multilingual Expansion Strategy:** When building the Hindi, Hinglish, and Tamil NLP pipelines in the next stage, derive entity slots directly from `canonical_transport.db` (`stop_names`, `place_names`) to guarantee zero entity hallucination.
