# Canonicalization & Entity Resolution Audit

**Date:** 2026-09-18  
**Knowledge Base Version:** `chennai_multimodal_v1.1` (Provisional Multisource Knowledge Base)  
**Database:** `data/canonical/transit/canonical_transport.db`  

---

## 1. Resolution Metrics Summary

| Metric | Count | Description |
|--------|-------|-------------|
| **Raw source stop records** | 7,246 | Total raw stop records ingested across CMRL API, OSM Overpass, and Community GTFS |
| **Normalized source records** | 7,246 | Total normalized stops in Silver layer (`normalized_stops.csv`) |
| **Canonical physical entities** | 7,136 | Unique physical stops and stations in Gold `transport_stops` table |
| **Automatic high-confidence merges** | 163 | Same-mode station pairs meeting strict name similarity and spatial thresholds |
| **Manually reviewed merges** | 0 | Pending manual domain gate confirmation (all candidate merges tracked provisionally) |
| **Unresolved matches** | 464 | Ambiguous same-mode candidate pairs kept separate for human review |
| **Deliberately kept separate** | 282 | Cross-mode candidate pairs (Metro ↔ Rail ↔ Bus) strictly kept as separate physical entities |
| **Total entity_source_links** | 7,246 | Comprehensive provenance links connecting every canonical entity to its upstream source records |

---

## 2. Canonical Resolution Policy

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
