# Data and model source register

## Current data status
`scripts/build_transport_db.py` contains manually entered **unverified demo fixtures**. No official GTFS/OSM ingestion is implemented. The bundled records lack per-record source evidence and must not be presented as verified current transport facts. No verified-on date or feed version has been established.

The UI and pipeline therefore label factual record responses as demo data. Timetables and ticketing are unsupported. The current synthetic intent dataset uses local authored templates; it does not incorporate MASSIVE.

## Candidate resources (not a completed acquisition register)
| Resource | Candidate location | Status |
| --- | --- | --- |
| Official Metro station/route information | https://chennaimetrorail.org/ | Identify exact pages/files, effective dates and applicable reuse terms before ingestion |
| CUMTA transit data | https://cumta.tn.gov.in/ | Exact downloadable feed, coverage, version and terms unverified |
| Community GTFS | https://github.com/ChennaiGTFS | Exact repository/feed and license unverified; not a reliable fallback until checked |
| OpenStreetMap | https://www.openstreetmap.org/copyright | Candidate coordinate/alias source; record exact extract and applicable attribution/ODbL obligations before use |
| MASSIVE Hindi | https://huggingface.co/datasets/AmazonScience/massive | Candidate seed corpus; dataset card lists CC-BY-4.0. Not downloaded/integrated; validate loading compatibility, label mapping and original partitions |
| MuRIL | https://huggingface.co/google/muril-base-cased | Optional later comparison; checkpoint revision and artifact license must be recorded when acquired |

## Small verification checklist
Before releasing any factual dataset, maintain one row per source artifact below and a mapping from its supported record IDs to that artifact. A CSV or table is sufficient; no provenance service is needed.

| Artifact / exact URL | Record IDs supported | Retrieved on | Version / effective date | Terms evidence | Verified by / on |
| --- | --- | --- | --- | --- | --- |
| None yet | — | — | — | — | — |

Public visibility is not itself a reuse license. Keep MIT code licensing separate from data/model terms. Optional speech/translation models are not used and have no verified licensing or runtime claims here.
