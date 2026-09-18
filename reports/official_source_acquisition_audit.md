# Official Source Acquisition Completeness Audit

**Date:** 2026-09-18  
**Audit Scope:** Chennai Multimodal Public Transport & Places Knowledge Base  
**Knowledge Base Version:** `chennai_multimodal_v1.2` (Provisional Multisource Knowledge Base with Route Topology & Services)  

---

## 1. Official Source Acquisition Inventory

In accordance with Section 3 of the Corrective Data Audit requirements, every transport agency and data category is audited for actual raw data acquisition into the Bronze layer (`data/raw/`).

Every category is assigned strictly one authoritative status from the required taxonomy:
- `COLLECTED_AND_INGESTED`: Raw file preserved byte-for-byte in Bronze and fully parsed/ingested into the Silver/Gold knowledge base.
- `COLLECTED_NOT_YET_PARSED`: Raw file acquired byte-for-byte in Bronze, registered in manifest, pending downstream parsing script.
- `PARTIAL`: Ingested through secondary or multi-source proxy (e.g. OSM/GTFS), but official agency bulk source is partial or incomplete.
- `PUBLIC_BUT_FETCH_FAILED`: Domain or endpoint is publicly cited, but direct fetch failed due to DNS/network/endpoint error.
- `MANUAL_FETCH_REQUIRED`: Service is behind an authenticated portal, captcha, or manual export mechanism requiring human credentials/intervention.
- `NOT_PUBLICLY_AVAILABLE`: Agency does not publish static bulk data in any machine-readable or downloadable format.
- `DEFERRED_OUT_OF_SCOPE`: Static real-time telemetry or non-transit data deferred for downstream phases.

---

## 2. Acquisition Status Table

| # | Data Category / Source | Raw Ingestion Path | Authoritative Status | Evidence & Audit Findings |
|---|------------------------|--------------------|----------------------|---------------------------|
| 1 | **CUMTA Official Open-Data GTFS** | `data/raw/cumta/2026-09-18/` | `PUBLIC_BUT_FETCH_FAILED` | `https://opendata.cumta.org/` is referenced in publications (FOSS United, Bharat Oraon Fellowship), but returns `NXDOMAIN` across public DNS resolvers (Google 8.8.8.8 and Cloudflare 1.1.1.1). Direct probe against server IP `164.164.197.47` (`cumta.org`) revealed an internal administrative WebGIS Dashboard requiring email/password credentials and captcha. Retained 8.7MB community GTFS as Tier-3 overlapping evidence. See `MANUAL_ACTION_REQUIRED.md`. Official CMA boundary polygon was acquired via OpenCity-hosted Government of Tamil Nadu dataset; source: CUMTA. |
| 2 | **CMRL Official API** | `data/raw/cmrl/2026-09-18/cmrl_station_information_api.json` | `COLLECTED_AND_INGESTED` | Scraped and parsed directly from official WordPress REST API (`https://chennaimetrorail.org/wp-json/wp/v2/station-information?per_page=100`). Contains 43 operational station disclosures, facilities, entrances, and coordinates. |
| 3 | **CMRL Phase II Official Documentation** | `data/raw/cmrl/2026-09-18/cmrl_phase2_corridor_status.html`<br>`data/raw/cmrl/2026-09-18/cmrl_phase2_map_official.pdf` | `COLLECTED_AND_INGESTED` | Acquired official project status page (`https://chennaimetrorail.org/project-status-2/`) and official 3.34MB route map PDF (`Phase-II-Map-Updated-Map-PHASE-2.pdf`). Corridor specifications (Corridors 3, 4, 5, 118.9 km, 128 stations, target 2028) derived dynamically from official disclosure. |
| 4 | **MTC Official Route / Stage Information** | `data/raw/mtc/2026-09-18/mtc_official_routes.html`<br>`data/raw/mtc/2026-09-18/mtc_official_stages.html` | `COLLECTED_AND_INGESTED` | Acquired official MTC route directory (685 routes) and official stage directory (1,562 stages) directly from `https://mtcbus.tn.gov.in/Home/routewiseinfo` and `https://mtcbus.tn.gov.in/Home/stagewiseinfo`. Normalized into Silver (`normalized_official_routes.csv`, `normalized_mtc_stages.csv`) and Gold (`fare_stages`). |
| 5 | **MTC Official Schedules** | `data/raw/mtc/2026-09-18/` | `PARTIAL` | Route-by-route and stage timings exist via interactive query form (`https://mtcbus.tn.gov.in/Home/bustimingsearch`), but MTC does not publish a bulk downloadable static timetable file. Scheduled trips are supplemented via GTFS `stop_times.txt` (47,143 trips). |
| 6 | **MTC Official Fare Information** | `data/raw/mtc/2026-09-18/mtc_official_fares.html` | `COLLECTED_AND_INGESTED` | Ingested official MTC fare list and stage fare matrix directly from `https://mtcbus.tn.gov.in/Home/fares`. Normalized into Silver (`normalized_mtc_fares.csv`) and Gold (`fares` table, 305 stage fare tariffs). |
| 7 | **Southern Railway Suburban Timetable Documents** | `data/raw/southern_railway/2026-09-18/` | `NOT_PUBLICLY_AVAILABLE` | Southern Railway Chennai Division does not publish static machine-readable bulk GTFS or open CSV timetables. Timetables are provided only via dynamic NTES / UTS queries and ad-hoc operational circulars. |
| 8 | **Southern Railway Station / Route Data** | `data/raw/osm/2026-09-18/osm_rail_and_metro_stations.json` | `PARTIAL` | 288 railway stations across Chennai Division with codes (MAS, MS, TBM, etc.), lines, and tracks ingested via OSM and community GTFS. Official direct static bulk dump from Indian Railways is unavailable. |
| 9 | **Chennai MRTS Official Information** | `data/raw/osm/2026-09-18/osm_rail_and_metro_stations.json` | `PARTIAL` | 19 MRTS viaduct stations from Chennai Beach to Velachery ingested with verified coordinates and physical interchange connections via OSM. Standalone MRTS static agency feed is merged into Southern Railway operations. |
| 10 | **OpenStreetMap (OSM)** | `data/raw/osm/2026-09-18/` | `COLLECTED_AND_INGESTED` | Ingested rail/metro stations, bus terminals/stops, and 1,621 geographic POIs via Overpass API queries with full tag and coordinate preservation. |
| 11 | **Community GTFS** | `data/raw/community_gtfs/2026-09-18/chennai-unified-gtfs.zip` | `COLLECTED_AND_INGESTED` | 8.7MB unified GTFS (ODbL) containing 5,624 stops, 4,614 route variants, 47,143 clean trips, and 1,360,635 stop times preserved as independent Tier-3 overlapping evidence and loaded into Gold topology tables. |

---

## 3. Provenance Verification & Checksums

All collected raw artifacts are checksummed with SHA-256 and immutably preserved in `metadata/raw_file_manifest.csv`:

| File ID | Byte Size | Format | SHA-256 Checksum | Provenance Source |
|---------|-----------|--------|------------------|-------------------|
| `CUMTA_CMA_BOUNDARY_20260918` | 156,235 | GeoJSON | `0e5416833cebddd9f22810e7c3cac97e8693d0b388fd17ce067153b716fc7d8c` | OpenCity-hosted Government of Tamil Nadu dataset; source: CUMTA |
| `CMRL_WP_API_20260918` | 301,868 | JSON | `dcbc36f7477d770bc4cadfe19c18eadef508b4b9073d50265da4ec48c1d9ba58` | Official CMRL WordPress REST API |
| `CMRL_PHASE2_STATUS_20260918` | 88,589 | HTML | `aef283a4b3183636f1c42f0a597a159f807eaec20853580572e816a2ef86ca84` | Official CMRL Phase II Project Status |
| `CMRL_PHASE2_MAP_20260918` | 3,342,142 | PDF | `d2f0bef6f35c848ae424076e036e4f346e91ea6b67fe19a3b93f2f01ebae2cb8` | Official CMRL Phase II Route Map |
| `MTC_FARES_20260918` | 110,759 | HTML | `3abb45898ee0c773e34b9d034db1b453a233b87fe2e4a42b10221379ec68ea13` | Official MTC Fare Stage Tariff Register |
| `MTC_ROUTES_20260918` | 88,683 | HTML | `15966686d915d2745cf6b48a04b12738fa09ee068be41369eb3c3b0be25c8d08` | Official MTC Route Directory |
| `MTC_STAGES_20260918` | 304,439 | HTML | `738b1c05c8a1908e3328e36780c109fcfe7a35fe6398f8045934526019b78e47` | Official MTC Stage Directory |
| `CHENNAI_UNIFIED_GTFS_20260918` | 9,091,816 | ZIP | `db1da880f9ad93e352f6658df0e94a8b2d71cd1dc8bdfbb60fa3968a9b0ad3e6` | GitHub community GTFS mirror (ungalsoththu) |
| `OSM_RAIL_METRO_STATIONS_20260918` | 162,041 | JSON | `b114790e5d0bd221b7feea4455a9a510181468b79f540310d040cbf37499cc5b` | Overpass API railway/metro extraction |
| `OSM_BUS_TERMINALS_STOPS_20260918` | 420,643 | JSON | `5178bd61f268477ce55a365b30203ab3512c515a7649d15fbafd205f9f8fb3d9` | Overpass API bus stop/terminal extraction |
| `OSM_TRANSPORT_POIS_20260918` | 650,688 | JSON | `7a3cdf4a7feafaa5531072e38b88ca92fa35775b2a90aa7fae7c5396c395d2cb` | Overpass API geographic POI extraction |
