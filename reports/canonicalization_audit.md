# Canonicalization & Entity Resolution Audit (v1.2)

**Date:** 2026-09-19  
**Knowledge Base Version:** `chennai_multimodal_v1.2` (Provisional Multisource Knowledge Base with Route Topology & Services)  
**Database:** `data/canonical/transit/canonical_transport.db`  

---

## 1. Resolution Metrics Summary

| Metric | Count | Description |
|--------|-------|-------------|
| **Normalized source stop records** | 7,246 | Total normalized stops in Silver layer (`normalized_stops.csv`) |
| **Canonical physical stops** | 7,136 | Unique physical stops and stations in Gold `transport_stops` table |
| **Canonical stops inside CMA** | 7,041 | Physical entities within official CUMTA/TNGIS CMA MultiPolygon |
| **Canonical stops outside CMA (Chennai-serving)** | 95 | Retained commuter rail and bus stops outside boundary serving Chennai network |
| **Automatic high-confidence merges** | 163 | Accepted high-confidence same-mode pairwise merge edges |
| **Clustering net reduction** | 110 | Source record reduction achieved through multi-link connected component clustering |
| **Unresolved same-mode matches** | 464 | Ambiguous candidate pairs kept separate for human review |
| **Deliberately kept separate (cross-mode)** | 282 | Cross-mode candidate pairs (Metro ↔ Rail ↔ Bus) strictly kept as separate physical entities |
| **Total entity_source_links** | 9,695 | Comprehensive provenance links connecting canonical entities to upstream source records (7,246 stop links, 2,449 route links) |

---

## 2. Multilingual Name Coverage Definition

- **Canonical Entities with at least one Tamil name:** 421 / 7,136 (5.90%)
- **Total Tamil Name Rows:** Recorded in `stop_names` with script `Taml` and language `ta`.
- **Devanagari Hindi Coverage:** 0.00% (No raw sources publish native Hindi strings for Chennai stations; synthetic translations are omitted).

---

## 3. Interchange Candidate Resolution & ID Collision Fix

- **Raw Candidate Rows:** 45
- **Unique Logical Candidate Pairs:** 45
- **Duplicate Logical Pairs Removed:** 0
- **Unique Interchange IDs Generated (SHA-256):** 45
- **Canonical Interchanges DB Rows:** 45
- **Methodology:** Generated collision-resistant stable identifiers `INT_{pair_hash}` from sorted unordered entity pairs `(min(a,b), max(a,b))`, eliminating previous truncation collisions. All 45 candidate pairs are inserted without relying on `INSERT OR REPLACE`.

---

## 4. Route Topology & Service Schedules (Gold Layer)

| Table Name | Row Count | Primary Function |
|------------|-----------|------------------|
| `route_stops` | 96,025 | Ordered stop topology for each route and direction, mapped to canonical stop IDs |
| `trips` | 47,143 | Operational trips with direction, route FK, and service calendar FK |
| `stop_times` | 1,360,635 | Precise scheduled arrival and departure times (times ≥ 24:00 preserved) |
| `service_calendars` | 9 | Weekly operating calendar days and validity periods |
| `service_exceptions` | 0 | Service exceptions table (schema ready for calendar_dates updates) |
| `fare_stages` | 1,562 | Official MTC fare stages with cross-references to canonical physical stops |
| `fares` | 305 | Official MTC stage fare matrix (11 service categories, stages 1–30) |

---

## 5. Canonical Resolution Policy

1. **Multi-Source Station Clustering (Metro & Rail):**
   - Matching station representations across CMRL API, OSM Overpass, and GTFS are canonicalized into single physical stations (`METRO_*`, `RAIL_*`, `MRTS_*`).
   - Criteria: exact mode match (`mode_a == mode_b`), name token similarity >= 85%, and spatial distance <= 120m (with coordinate precedence given to official CMRL and surveyed OSM nodes).
   - Every contributing source record is preserved as an independent row in `entity_source_links`.

2. **Cross-Mode Physical Separation:**
   - Entities of differing modes (e.g. `METRO_GUINDY`, `RAIL_GUINDY`, `BUS_GUINDY`) are **NEVER** merged into a single stop record.
   - They remain distinct physical stops and are grouped logically under `HUB_GUINDY` via `hub_members`.

3. **Bus Stop Deduplication Policy:**
   - Only cross-source identical stops (OSM surveyed terminal vs GTFS stop) within <= 35m and name similarity >= 90% are auto-merged.
   - Directional pairs within GTFS on opposite sides of roadways remain distinct physical stops to preserve trip scheduling sequences.
