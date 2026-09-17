# Data and model source register

## Current data status
The active database (`data/processed/transport.db`) is compiled by `scripts/build_transport_db.py` from the curated fixture `data/curated/cmrl_verified_stations.json`.

This fixture covers a verified subset of 13 Chennai Metro stations on Corridor 1 (Blue Line) and Corridor 2 (Green Line), their documented physical accessibility features, and direct transit connections.

Timetables, fares, live delays, and bus/suburban rail coverage are explicitly deferred and marked as unsupported/unknown.

## Verified source register
| Artifact / exact URL | Record IDs supported | Retrieved on | Version / effective date | Terms evidence | Verified by / on |
| --- | --- | --- | --- | --- | --- |
| https://chennaimetrorail.org/station-facilities/ | CHENNAI_CENTRAL, CHENNAI_EGMORE, CHENNAI_AIRPORT, ALANDUR, GUINDY, KOYAMBEDU, CMBT, VADAPALANI, SHENOY_NAGAR, NANDANAM, WASHERMANPET, WIMCO_NAGAR, ST_THOMAS_MOUNT (facilities: lift, wheelchair, tactile_paths, accessible_toilet, parking) | 2026-09-17 | Phase 1 & 2 operational network | Public informational disclosure of universal accessibility features on official CMRL portal | Automated review & curation, 2026-09-17 |
| https://chennaimetrorail.org/ (Corridors & Interchanges) | Blue Line (Wimco Nagar to Airport), Green Line (Central to St. Thomas Mount), Alandur & Central interchanges | 2026-09-17 | Current operational network | Official network map and station directory | Automated review & curation, 2026-09-17 |

## Candidate resources (for future phases)
| Resource | Candidate location | Status |
| --- | --- | --- |
| CUMTA transit data | https://cumta.tn.gov.in/ | Exact downloadable static GTFS feed, coverage, version and terms to be verified for bus/suburban additions |
| Community GTFS | https://github.com/ChennaiGTFS | Candidate GTFS representation for MTC bus routes; ODbL license |
| OpenStreetMap | https://www.openstreetmap.org/copyright | Candidate station entrance coordinates and landmarks; ODbL attribution required |
| MASSIVE Hindi | https://huggingface.co/datasets/AmazonScience/massive | Candidate seed corpus (CC-BY-4.0); optional intent augmentation |
| MuRIL | https://huggingface.co/google/muril-base-cased | Apache-2.0 pretrained Indic transformer for Phase 6 research comparison |

Public visibility is not itself a reuse license. Keep MIT code licensing separate from data/model terms. Optional speech/translation models are not used in the text MVP and have no verified licensing or runtime claims here.
