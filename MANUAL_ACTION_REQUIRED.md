# Manual Action Required: Upstream Source Fetch Protocol (Type B)

**Document:** Manual Action Register  
**Stage:** Data Acquisition Phase (Corrective Audit)  
**Project:** Chennai Multimodal Public Transport & Places Knowledge Base  
**Status:** `chennai_multimodal_v1.1` (Provisional Multisource Knowledge Base)  

---

## Type B Dataset Register

The following official government feeds or portals either require interactive human action, have not been published publicly for open automated retrieval, or require formal institutional credentials. In accordance with the **Hard Stop Protocol (Section 2, Type B)**, these sources are recorded with exact technical investigation findings, expected placement paths, and resume points.

---

### Item 1: Official CUMTA Integrated Open Data GTFS Feed

- **Dataset Name:** CUMTA Official Integrated Public Transport Static GTFS (Metro + Bus + Suburban Rail)
- **Source Authority:** Chennai Unified Metropolitan Transport Authority (CUMTA) / Government of Tamil Nadu
- **Target Portal Investigated:** `https://opendata.cumta.org/` and `https://cumta.org/`
- **Technical Investigation Findings & Blocker Details:**
  1. **Public DNS Probe:** Probed `opendata.cumta.org` against public DNS resolvers (Google `8.8.8.8` and Cloudflare `1.1.1.1` via DNS-over-HTTPS). Both return `Status: 3` (`NXDOMAIN`), confirming the subdomain is not registered on public DNS.
  2. **Direct IP & Virtual Host Probe:** Inspected `164.164.197.47` (`cumta.org`) on port 443 with Host header `opendata.cumta.org`. The server returns the default virtual host for `cumta.org`, which is an internal administrative WebGIS Dashboard (`<title>WebGIS Dashboard</title>`).
  3. **Authentication Barrier:** The dashboard requires email, password, and a numeric captcha (`id="captcha_val"`, `generate-captcha`) for all access. Unauthenticated public downloads for static GTFS are not exposed.
  4. **Primary Government Portal:** `https://cumta.tn.gov.in/` is a single landing page with policy announcements and acts, but provides no static GTFS download links.
- **Expected File Format:** `gtfs.zip` (containing `agency.txt`, `routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`, `calendar.txt`, etc.)
- **Expected Placement Path:**
  ```text
  data/raw/cumta/2026-09-18/cumta_official_gtfs.zip
  ```
- **Current Operational Fallback:** Retained the 8.7MB unified GTFS (`data/raw/community_gtfs/2026-09-18/chennai-unified-gtfs.zip`) as independent Tier-3 overlapping evidence, combined with Tier-1 CMRL WordPress REST API (`data/raw/cmrl/2026-09-18/`) and Tier-3 OpenStreetMap Overpass datasets.
- **Resume Point:** If official CUMTA GTFS is released publicly or obtained via institutional credentials, place the archive byte-for-byte in the above path, register its SHA-256 in `metadata/raw_file_manifest.csv`, and rerun the normalization pipeline.

---

### Item 2: MTC Official Real-Time GPS / GTFS-RT Stream

- **Dataset Name:** MTC Live Vehicle Tracking & Real-Time Schedule Feed
- **Source Authority:** Metropolitan Transport Corporation (Chennai) Ltd. / Chennai Bus App
- **Source Portal:** `https://mtcbus.tn.gov.in/`
- **Reason Automated Fetch is Inadequate:** MTC live tracking is hosted behind mobile app API endpoints requiring dynamic session tokens. Bulk automated scraping is not permitted.
- **Expected File Format:** JSON or GTFS-RT protobuf (`vehicle_positions.pb`, `trip_updates.pb`)
- **Expected Placement Path:**
  ```text
  data/raw/mtc/2026-09-18/mtc_official_realtime.json
  ```
- **Fallback In Use During Autonomous Run:** Official MTC fare tables, 685 route codes, and 1,562 stages acquired into `data/raw/mtc/2026-09-18/`, supplemented by GTFS `stop_times.txt` and OSM bus network disclosures.
- **Resume Point:** Safe to postpone to downstream real-time tracking phase. Static routing knowledge base is fully functional without real-time telemetry.

---

### Item 3: Southern Railway Complete Suburban Division Timetable Database

- **Dataset Name:** Southern Railway Chennai Suburban Official Master Timetable
- **Source Authority:** Southern Railway Zone, Indian Railways
- **Source Portal:** `https://sr.indianrailways.gov.in/`
- **Reason Automated Fetch is Inadequate:** Timetables are published primarily as seasonal PDF booklets ("Chennai Suburban Pocket Time Table") or dynamic passenger enquiry tables on NTES. Static bulk GTFS is not published.
- **Expected File Format:** PDF or structured CSV
- **Expected Placement Path:**
  ```text
  data/raw/southern_railway/2026-09-18/chennai_suburban_pocket_timetable.pdf
  ```
- **Fallback In Use During Autonomous Run:** Complete OSM station network (288 stations/halts), verified corridor connections, and Southern Railway station codes (MAS, MS, TBM, etc.).
