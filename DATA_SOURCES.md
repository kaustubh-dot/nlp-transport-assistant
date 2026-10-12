# Data sources

The academic demo recognizes names from the full [canonical SQLite snapshot](data/canonical/transit/canonical_transport.db) and existing Hindi/Hinglish aliases. It reads the small [case-study catalog](data/project/chennai_case_study.json) for curated demonstrations and reuses the existing canonical service for additional route/timetable lookups. Neither fetches live transit data. The snapshot contains published routes, stops, trips, calendars, stop times, stage tariffs, metro fare pairs, places and source links collected in September 2026. Dates describe the stored records, not current validity.

Name coverage comprises 6,870 bus-stop records, 157 Metro records, 107 suburban-rail records, two MRTS records and 1,621 places/landmarks. These are records, including duplicates, not a complete inventory of unique operational stations. Route tables contain bus and limited Metro sequences; there are no suburban-rail or MRTS route sequences. Station names and route/timetable coverage are separate. Exact canonical names and stored aliases are recognized; arbitrary spelling variants and every Hindi transliteration are not guaranteed. See [data coverage](docs/DATA_COVERAGE.md).

| Stored source | Content used | Published source |
| --- | --- | --- |
| `CHENNAI_COMMUNITY_GTFS` | Community GTFS route/stop sequences, schedules and service calendars | [ChennaiGTFS feed](https://github.com/ungalsoththu/ChennaiGTFS) |
| `CMRL_API` | Metro station information and names | [CMRL station API](https://chennaimetrorail.org/wp-json/wp/v2/station-information?per_page=100) |
| `CMRL_OFFICIAL` | Metro disclosures and dated station-to-station fare matrix | [CMRL portal](https://chennaimetrorail.org/) |
| `MTC_OFFICIAL` | Official route/stage disclosures and dated bus stage fares | [MTC portal](https://mtcbus.tn.gov.in/) |
| `OSM_OVERPASS` | Station, stop and landmark geography | [OpenStreetMap](https://www.openstreetmap.org/) |

`entity_source_links` retains source IDs and original record IDs for canonical entities. Fare tables retain source IDs and effective dates: the stored MTC tariffs are dated 2018-01-29 and CMRL fares 2021-02-22. The API/UI preserve provenance and provisional coverage indicators where supported. The database is shipped as a fixed snapshot; startup does not rebuild it.

Published route candidates and timetable records do not confirm current service operation. Curated hub/interchange records do not constitute a verified transfer network, and stored facility/accessibility entries do not establish supported answers for all requests. See [known limitations](docs/KNOWN_LIMITATIONS.md).

## Small academic catalog

The selected published Metro connections reference the [CMRL line map](https://chennaimetrorail.org/wp-content/uploads/2023/11/Line-Map.pdf). Central Metro airport-direction and lift/wheelchair records reference its [official station page](https://chennaimetrorail.org/station-information/puratchi-thalaivar-dr-m-g-ramachandran-central-metro/), checked on 2026-10-12. These are Metro records, not claims about the railway station or current facility operation.

Two bus connections reference ordered stop sequences in the stored community GTFS snapshot: route `GTFS_ROUTE_14515` / 51A from Tambaram East Bus Stop to Guindy Railway Station, and `GTFS_ROUTE_19246` / 55K CT1 from Tambaram West Bus Stand to Airport Metro. These were checked against the local route/direction/stop records. They are not fresh official confirmations of current service. Airport Metro stop is not the airport terminal.

One historical timing illustration uses the [CMRL publication dated 16 October 2024](https://chennaimetrorail.org/wp-content/uploads/2024/10/Press-Release-16.10.2024-English.pdf). It records weekday terminal departures of 05:00 and 23:00 and is labeled historical in every response. The [current official timetable page](https://wcag.chennaimetrorail.org/time-table/) is linked for confirmation; its linked July 2026 PDF could not be retrieved during this work, so no current times were transcribed. The old terminal window cannot establish a specific route's first/last departure.

Missing current timetable, route, walking and accessibility information stays unknown. The five Hindi–Tamil phrases are prototype text; Tamil-speaker review remains necessary.

Two supplementary Central/Velachery MRTS guidance records use Southern Railway's [published MRTS table](https://sr.indianrailways.gov.in/uploads/files/1345106736152-MRTS%20WEEK.pdf). Park Town and Velachery are listed on the same line. The guidance identifies the separate boarding/alighting station; it does not confirm the Central-to-Park-Town access path or a current service. Timetable validity was not established and no departure times were transcribed. Additional Central-area bus options use the snapshot's `BUS_83` boarding record, keeping its General Hospital/Central stop name visible.

The [official Guindy Metro page](https://chennaimetrorail.org/station-information/guindy/) lists associated bus stops under entrance/access information. The app uses this named-stop fallback when Guindy's coordinates disagree across snapshot sources, while withholding an unreliable distance. The list does not establish a shortest walking route or current bus operation.

## Model and licensing

The classifier uses `google/muril-base-cased` at the pinned revision in the [model manifest](models/hindi_project_manifest.json). Its seed encoder and adapted layers are distributed as versioned release assets. The academic experiment adapts its final two encoder layers and a separate nine-intent head; the baseline uses the same teaching dataset. See the [MuRIL paper](https://arxiv.org/abs/2103.10730) and [model setup](docs/MODEL_SETUP.md). Prior transport training and development-exposed synthetic evaluation prevent a population-level accuracy claim.

Code is [MIT licensed](LICENSE). OpenStreetMap and the collected community GTFS records carry ODbL attribution obligations in the source records. Official disclosures have source-specific terms that require review before redistribution. MuRIL is Apache 2.0 licensed; the model attribution and license copy are in [model notices](models/NOTICE.md).
