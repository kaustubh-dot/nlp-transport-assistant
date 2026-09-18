# Manual Action Required: Upstream Source Fetch Protocol (Type B)

**Document:** Manual Action Register  
**Stage:** Data Acquisition Phase  
**Project:** Chennai Multimodal Public Transport & Places Knowledge Base  

---

## Type B Dataset Register

The following official government feeds or portals either require interactive human action, have not been published publicly for open automated retrieval, or require formal institutional credentials. In accordance with the **Hard Stop Protocol (Section 2, Type B)**, these sources are recorded with exact requirements, expected placement paths, and resume points.

---

### Item 1: Official CUMTA Integrated GTFS Feed

- **Dataset Name:** CUMTA Official Integrated Public Transport GTFS (Metro + Bus + Suburban Rail)
- **Source Authority:** Chennai Unified Metropolitan Transport Authority (CUMTA) / Government of Tamil Nadu
- **Source Portal:** `https://cumta.tn.gov.in/`
- **Reason Automated Fetch is Inadequate:** The public CUMTA portal provides policy documents, acts, and web dashboards, but does not provide a direct, unauthenticated public static GTFS zip download link. If an internal or official static GTFS archive is obtained through institutional request or civic data partnership:
- **Expected File Format:** `gtfs.zip` (containing `agency.txt`, `routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`, `calendar.txt`, etc.)
- **Expected Placement Path:**
  ```text
  data/raw/cumta/2026-09-18/cumta_official_gtfs.zip
  ```
- **Fallback In Use During Autonomous Run:** Overlapping data from Tier 1 CMRL REST API (`data/raw/cmrl/2026-09-18/`), Tier 3 OpenStreetMap Overpass (`data/raw/osm/2026-09-18/`), and Tier 3 Community Open GTFS (`data/raw/community_gtfs/2026-09-18/`).
- **Resume Point:** When supplied, ingest into `data/raw/cumta/2026-09-18/` and re-run normalization in Phase 12.

---

### Item 2: MTC Official Real-Time GPS / GTFS-RT Stream

- **Dataset Name:** MTC Live Vehicle Tracking & Real-Time Schedule Feed
- **Source Authority:** Metropolitan Transport Corporation (Chennai) Ltd. / Chennai Bus App
- **Source Portal:** `https://mtcbus.tn.gov.in/`
- **Reason Automated Fetch is Inadequate:** MTC live tracking is hosted behind mobile app API endpoints requiring dynamic session tokens. Automated bulk scraping violates app terms of service.
- **Expected File Format:** JSON or GTFS-RT protobuf (`vehicle_positions.pb`, `trip_updates.pb`)
- **Expected Placement Path:**
  ```text
  data/raw/mtc/2026-09-18/mtc_official_realtime.json
  ```
- **Fallback In Use During Autonomous Run:** MTC static route and stop sequence data extracted from the community GTFS feed and OSM bus network disclosures.
- **Resume Point:** Safe to postpone to later real-time tracking phase. Static routing knowledge base is fully functional without real-time positions.

---

### Item 3: Southern Railway Complete Suburban Division Timetable Database

- **Dataset Name:** Southern Railway Chennai Suburban Official Master Timetable
- **Source Authority:** Southern Railway Zone, Indian Railways
- **Source Portal:** `https://sr.indianrailways.gov.in/`
- **Reason Automated Fetch is Inadequate:** Timetables are published primarily as seasonal PDF booklets ("Chennai Suburban Pocket Time Table") or dynamic passenger enquiry tables on NTES.
- **Expected File Format:** PDF or structured CSV
- **Expected Placement Path:**
  ```text
  data/raw/southern_railway/2026-09-18/chennai_suburban_pocket_timetable.pdf
  ```
- **Fallback In Use During Autonomous Run:** Complete OSM station network, verified corridor connections, and Southern Railway station codes.
