# Data sources

The application reads the tracked [canonical SQLite snapshot](data/canonical/transit/canonical_transport.db). It does not fetch live transit data. The snapshot contains published routes, stops, trips, calendars, stop times, stage tariffs, metro fare pairs, places and source links collected in September 2026. Dates describe the stored records, not current validity.

| Stored source | Content used | Published source |
| --- | --- | --- |
| `CHENNAI_COMMUNITY_GTFS` | Community GTFS route/stop sequences, schedules and service calendars | [ChennaiGTFS feed](https://github.com/ungalsoththu/ChennaiGTFS) |
| `CMRL_API` | Metro station information and names | [CMRL station API](https://chennaimetrorail.org/wp-json/wp/v2/station-information?per_page=100) |
| `CMRL_OFFICIAL` | Metro disclosures and dated station-to-station fare matrix | [CMRL portal](https://chennaimetrorail.org/) |
| `MTC_OFFICIAL` | Official route/stage disclosures and dated bus stage fares | [MTC portal](https://mtcbus.tn.gov.in/) |
| `OSM_OVERPASS` | Station, stop and landmark geography | [OpenStreetMap](https://www.openstreetmap.org/) |

`entity_source_links` retains source IDs and original record IDs for canonical entities. Fare tables retain source IDs and effective dates: the stored MTC tariffs are dated 2018-01-29 and CMRL fares 2021-02-22. The API/UI preserve provenance and provisional coverage indicators where supported. The database is shipped as a fixed snapshot; startup does not rebuild it.

Published route candidates and timetable records do not confirm current service operation. Curated hub/interchange records do not constitute a verified transfer network, and stored facility/accessibility entries do not establish supported answers for all requests. See [known limitations](docs/KNOWN_LIMITATIONS.md).

## Model and licensing

The classifier uses `google/muril-base-cased` at the pinned revision in the [model manifest](models/nlp_v2_t3_manifest.json), plus separately supplied selected weights. [Model setup](docs/MODEL_SETUP.md) describes byte validation and offline loading. Original validation contains train-family overlap; the stored metrics are selection provenance and do not establish population-level accuracy.

Code is [MIT licensed](LICENSE). OpenStreetMap and the collected community GTFS records carry ODbL attribution obligations in the source records. Official disclosures have source-specific terms that require review before redistribution. The MuRIL base model and supplied checkpoint also have separate model terms. Public access alone is not permission to redistribute data or weights.
