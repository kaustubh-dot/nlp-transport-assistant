# Canonical Entity Resolution and Normalization Contract (Phase N3)

Document: `docs/nlp_v2/entity_resolution_contract.md`  
Snapshot Version: `chennai_multimodal_v1.2.2`  
Date: 2026-09-19  
Status: Authoritative Entity & Normalization Specification (Corrected Methodology Patch)

---

## 1. Separation of Span Extraction and Entity Resolution

The NLU architecture maintains a strict conceptual separation between two sequential processing layers:

```
Step 1: Span Extraction (Surface Layer)
"gindi se central metro ka last train kab hai?"
      ↓
Extracted Spans:
- origin surface      = "gindi"
- destination surface = "central"
- transport_mode      = "metro"
- timing_type         = "last"

Step 2: Canonical Entity Resolution (Knowledge Base Layer)
- "gindi" + mode "metro"   → METRO_GUINDY_9011 (resolved_entity_id)
- "central" + mode "metro" → METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL
- "last"                   → timing_type: "last"
```

A correct span extraction with an incorrect canonical resolution is an **entity resolution failure**, not a span extraction failure. Evaluating them separately prevents conflating linguistic boundary detection with database gazetteer coverage.

---

## 2. Canonical Entity Namespaces in `chennai_multimodal_v1.2.2`

All language surfaces (English, Hindi Devanagari, Roman Hindi, Hinglish, Tamil) resolve into uniform canonical IDs in `canonical_transport.db`:

```
               CANONICAL ENTITY GRAPH
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   HUB_GUINDY     METRO_GUINDY_9011   RAIL_GUINDY
        │                │                │
 ┌──────┴──────┐         │                │
 ▼             ▼         ▼                ▼
"Guindy"     "गिंडी"   "Guindy Metro"  "Guindy Suburban"
(Generic)   (Generic)   (Mode-specific)  (Mode-specific)
```

| Entity Namespace | Canonical ID Format | Underlying Table | Count in v1.2.1 | Resolution Example |
| :--- | :--- | :--- | :--- | :--- |
| **Multimodal Hub** | `HUB_<NAME>` | `transport_hubs` | 62 | `HUB_GUINDY`, `HUB_CENTRAL`, `HUB_TAMBARAM` |
| **Metro Station** | `METRO_<NAME>` | `transport_stops` (`mode='metro'`) | 41 | `METRO_GUINDY_9011`, `METRO_EGMORE` |
| **Suburban Station** | `RAIL_<NAME>` | `transport_stops` (`mode='suburban_rail'`) | 107 | `RAIL_GUINDY`, `RAIL_TAMBARAM`, `RAIL_CENTRAL` |
| **MRTS Station** | `MRTS_<NAME>` | `transport_stops` (`mode='suburban_rail'`) | 19 | `MRTS_THIRUMAYILAI`, `MRTS_VELACHERY` |
| **Physical Bus Stop** | `BUS_<ID>` | `transport_stops` (`mode='bus'`) | 6,870 | `BUS_5822` (Koyambedu Bus Terminus), `BUS_11` |
| **Transit Route** | `ROUTE_<OPERATOR>_<CODE>` | `transport_routes` | 4,619 | `CMRL_BLUE_CORRIDOR_1`, `GTFS_ROUTE_23917` |
| **Official Fare Stage** | `MTC_STAGE_<ID>` | `fare_stages` | 1,562 | `MTC_STAGE_0002_100_FEET_ROAD_JN` |
| **Place / POI** | `OSM_POI_<ID>` | `places` | 1,621 | `OSM_POI_7820652140` (Shri Maruthi Hospital) |

*Station Code Qualification*: Station telegraphic codes (e.g. MAS, MS, MSB, TBM) exist in source metadata and stop IDs, but `transport_stops` lacks a dedicated `station_code` column. Resolving queries explicitly asking for station codes is marked `NOT_CURRENTLY_SUPPORTED` until an explicit canonical lookup is implemented.

---

## 3. Entity Ambiguity Policy

When a user query refers to a location without modal qualification (e.g. "Guindy", "Tambaram", "Central"), multiple valid physical nodes exist:
- `HUB_GUINDY`: High-level multimodal transfer hub.
- `METRO_GUINDY_9011`: Underground/elevated CMRL metro platform.
- `RAIL_GUINDY`: Southern Railway suburban surface platform.
- `BUS_GUINDY_RS`: MTC roadside bus stop pole pair.

### Disambiguation Precedence Rules
1. **Mode-Qualified Match**:
   If the utterance explicitly mentions a transport mode (e.g. "Guindy metro", "Central local train", "Tambaram bus stand"), resolve directly to that mode's physical stop ID (`METRO_GUINDY_9011`, `RAIL_CENTRAL`, `BUS_TAMBARAM`).
2. **Generic Multimodal Journey Match**:
   If the utterance is an open point-to-point journey query (e.g. "Guindy se Central kaise jau?"), resolve to the multimodal hub ID (`HUB_GUINDY`). The downstream router searches across all constituent member platforms.
3. **Route-Constrained Match**:
   If the query references a specific bus route (e.g. "Does 102 stop at Guindy?"), resolve to the bus stop node associated with that route's sequence in `route_stops`.
4. **Structured Ambiguity Output**:
   When resolution cannot establish a single node with confidence $\ge 0.85$, the resolver returns structured candidate candidates:

```json
{
  "surface_span": "guindy",
  "resolved_entity_id": "HUB_GUINDY",
  "resolved_entity_type": "hub",
  "resolution_confidence": 0.88,
  "is_ambiguous": true,
  "candidate_entity_ids": [
    {"entity_id": "HUB_GUINDY", "type": "hub", "score": 0.88},
    {"entity_id": "METRO_GUINDY_9011", "type": "metro_station", "score": 0.82},
    {"entity_id": "RAIL_GUINDY", "type": "suburban_station", "score": 0.80},
    {"entity_id": "BUS_GUINDY_RS", "type": "bus_stop", "score": 0.74}
  ]
}
```

---

## 4. Route Number Normalization Specification

The Chennai bus network features complex alphanumeric route naming conventions used by MTC. Naive string cleaning (e.g. regex `\W+`) corrupts operational route codes.

### Normalization Pipeline for Route Numbers:
1. **Punctuation & Delimiter Standardization**:
   - Hyphens and spaces between digits and letters are collapsed:
     - `102-A` → `102A`
     - `102 A` → `102A`
     - `21 G` → `21G`
     - `570 S` → `570S`
2. **Noise Prefix & Suffix Stripping**:
   - Strip leading/trailing tokens: `bus`, `route`, `no`, `number`, `बस`, `रूट`, `नंबर`:
     - `102 number bus` → `102`
     - `बस 21G` → `21G`
     - `route no 570` → `570`
3. **Preservation of Distinct Operational Suffixes**:
   - MTC route suffixes represent distinct itineraries and fare stages:
     - `102`: Broadway to Kelambakkam
     - `102A`: Broadway to Thiruporur
     - `102C`: Broadway to Chemmancheri
     - `102K`: Broadway to Kannagi Nagar
     - `102K#`: Express variant
   - **Strict Rule**: Never truncate alphanumeric suffixes to the base integer. `102A` must never become `102`.
4. **Script Transliteration of Indic Digits**:
   - Hindi Devanagari numerals are mapped to standard Arabic numerals:
     - `१०२` → `102`
     - `२१जी` → `21G`

---

## 5. Temporal Normalization Specification

Commuter queries express time in colloquial Hindi, Hinglish, and English with varying levels of precision and contextual ambiguity.

### Time Expression Normalization Rules:
1. **Explicit 12-Hour / 24-Hour Expressions**:
   - `8:00 pm` / `8 PM` / `20:00` → `20:00:00`
   - `8:30 am` / `8:30 AM` / `08:30` → `08:30:00`
2. **Colloquial Hindi / Hinglish Time Expressions**:
   - `raat 8 baje` / `रात 8 बजे` → `20:00:00`
   - `shaam 6 baje` / `शाम 6 बजे` → `18:00:00`
   - `dopahar 2 baje` / `दोपहर 2 बजे` → `14:00:00`
   - `subah 5 baje` / `सुबह 5 बजे` → `05:00:00`
3. **Strict Disallowance of Defaulting for Bare Times (`8 baje`, `8 बजे`)**:
   - **Do not default to 08:00**.
   - When period-of-day is unspecified, preserve dual candidates `["08:00:00", "20:00:00"]` with `temporal_ambiguity: true`. Resolution requires contextual dialogue or explicit user clarification.
4. **Strict Disallowance of Defaulting for Hindi `कल / kal`**:
   - In Hindi, `कल` (`kal`) denotes either "yesterday" or "tomorrow" based entirely on grammatical aspect and tense.
   - **Zero Default Rule**: Never default ambiguous `kal` to tomorrow.
   - Resolve to `+1` (tomorrow) or `-1` (yesterday) **only** when grammatical tense/aspect provides unambiguous proof:
     - "kal train aayi thi" (past auxiliary `thi` → yesterday, `-1`)
     - "kal train milegi kya" (future verb `milegi` → tomorrow, `+1`)
   - In ambiguous queries lacking tense markers (e.g. "kal ka schedule", "kal ki timing"), emit:
     `{"temporal_relative": "kal", "resolved_temporal_offset": "UNRESOLVED_TEMPORAL_AMBIGUITY", "requires_clarification": true}`.
   - The system must never silently normalize `कल` to `today` (`aaj`) or assume `tomorrow`.

---

## 6. Entity Resolution Evaluation Metrics

To evaluate entity extraction and resolution with rigorous separation:

1. **Span-Level Strict F1**:
   Character-exact span match and correct entity slot type label ($P, R, F_1$).
2. **Top-1 Canonical Resolution Accuracy**:
   Percentage of extracted spans where the top-ranked candidate matches the ground-truth canonical entity ID (`canonical_id`).
3. **Top-3 Canonical Resolution Accuracy**:
   Percentage where the ground-truth canonical ID is within the top 3 ranked candidates.
4. **Ambiguity Rate**:
   Percentage of queries where the entity surface references a multi-node hub requiring disambiguation.
5. **Entity Corruption Rate (under Translation)**:
   For Pipeline A (translation pivot), the percentage of canonical entities whose surface span was altered, mistranslated, or deleted during the translation step.
