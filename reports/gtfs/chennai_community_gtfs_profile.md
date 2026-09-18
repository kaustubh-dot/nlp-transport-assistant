# GTFS Profiling Report: CHENNAI_COMMUNITY_GTFS

**Profile Generated:** 2026-09-18 18:33:08  
**Feed Identifier:** `CHENNAI_COMMUNITY_GTFS`  
**Source Path:** `data/raw/community_gtfs/2026-09-18/chennai-unified-gtfs.zip`  
**Staged Extraction:** `data/staging/community_gtfs/2026-09-18/`  
**Publisher:** Ithu Ungal Soththu  
**Language:** ta  
**Feed Version:** 2025.03.25  

---

## 1. Core Feed Statistics

| GTFS Table | Record Count | Description |
| :--- | :--- | :--- |
| `agency.txt` | 2 | Operating agencies |
| `routes.txt` | 4614 | Commercial routes (MTC bus + CMRL metro) |
| `stops.txt` | 5624 | Physical passenger stop points |
| `trips.txt` | 47149 | Scheduled trips |
| `stop_times.txt` | 1360635 | Timed stop arrivals and departures |
| `calendar.txt` | 9 | Service calendar patterns |
| `shapes.txt` | 88 rows (4 unique shapes) | Route geometry waypoints |
| `feed_info.txt` | 1 | Feed publisher metadata |

---

## 2. Agency & Multimodal Composition

### Agencies Represented
- **Metropolitan Transport Corporation** (`69`): https://mtcbus.tn.gov.in/, Timezone: Asia/Kolkata
- **Chennai Metro Rail Limited** (`CMRL`): https://chennaimetrorail.org/, Timezone: Asia/Kolkata

### Route Types Breakdown
- Route type `1` (Subway / Metro): 0 routes
- Route type `3` (Bus): 4611 routes
- Total routes: 4614

### Routes by Agency
- Agency `69`: 4611 routes
- Agency `1`: 3 routes

---

## 3. Spatial & Coordinate Coverage

- **Total Stops:** 5624
- **Stops with Valid Coordinates:** 5624 (100.00%)
- **Stops Missing Coordinates:** 0
- **Duplicate Stop IDs:** 0
- **Coordinate Extents:**
  - Latitude Range: 12.6148°N to 13.4904°N
  - Longitude Range: 79.8019°E to 80.3358°E

---

## 4. Service Schedules & Calendar Range

- **Valid Calendar Date Range:** 20240501 to 20300501
- **Total Scheduled Trips:** 47149
- **Total Stop Time Observations:** 1360635
- **Unique Shape Geometry Traces:** 4

---

## 5. Architectural Assessment for Knowledge Base Integration

1. **Multimodal Composition:** The community feed combines MTC city bus routes and CMRL metro lines into a single unified specification. MTC routes represent the vast majority (4611 routes, 5624 stops).
2. **Quality & Limitations:**
   - MTC shapes are straight-line connections between scheduled stops, requiring map matching against OSM for precise road alignment.
   - CMRL metro stations in this feed match standard operational stations and provide clean cross-validation against CMRL official API records.
3. **Hierarchy & Status:**
   - Classified as **Tier 3 Community Open Data (ODbL)**.
   - Serves as primary structural evidence for MTC bus routes and stop sequences, while official CMRL portal disclosures take precedence for Metro station facilities and accessibility.
