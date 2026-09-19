# Gate B.2 Entity Grounding & Hardcoded Gazetteer Audit Report

**Date:** 2026-09-19  
**Database Snapshot:** `chennai_multimodal_v1.2.2` (`data/canonical/transit/canonical_transport.db`)  
**Scope:** Complete verification of all 55 manually declared entries in `scripts/nlp_v2/gate_b2/ground_entities.py`.

---

## 1. Audit Summary & Resolution Status

| Audit Metric | Count | Percentage |
| :--- | :---: | :---: |
| **Total Gazetteer Entries Audited** | **55** | 100.0% |
| **PASS (Exact DB & Name Correspondence)** | **41** | 74.5% |
| **FAIL_FIXED (Egmore Central Mapping Corrected)** | **1** | 1.8% |
| **PROVISIONAL (Base Route / Stop Sub-name Variations)** | **8** | 14.5% |
| **DB_METADATA_MISMATCH_REVIEW_REQUIRED (Rail/MRTS Agency MTC in DB)** | **5** | 9.1% |
| **AMBIGUOUS (Unresolved or Missing from DB)** | **0** | 0.0% |

### Mode / Operator Validation Breakdown

| Category | Count | Status Description |
| :--- | :---: | :--- |
| **Directly DB Validated** | 31 | Mode and agency confirmed via `transport_stops` or `transport_routes` table |
| **Validated via Hub Members** | 10 | Mode and agency confirmed via member stops in `hub_members` |
| **Not Directly Verifiable** | 9 | `transport_hubs` and `places` tables do not have native mode/agency columns; hub member stops lack direct mode/agency match |
| **DB Metadata Mismatches** | 5 | Declared `SR` / `suburban_rail` / `mrts`, but canonical DB `transport_stops.agency_id` is `MTC` (Case A) |
| **Hard Failures** | 0 | Zero records failed validation |

---

## 2. Rail / MRTS Southern Railway (SR) vs DB MTC Finding (Case A)

> [!WARNING]
> **Canonical DB Metadata Anomaly (Case A — Review Required)**:
> - **Affected Records (5 Stops):** `Chennai Beach` (`RAIL_CHENNAI_BEACH`), `Chepauk` (`MRTS_CHEPAUK`), `Velachery` (`MRTS_VELACHERY`), `Tiruvottiyur` (`RAIL_TIRUVOTTIYUR`), `Chromepet` (`RAIL_CHROMEPET`).
> - **Declared Operator / Mode:** `operator = SR`, `mode = suburban_rail` / `mrts`.
> - **Database Record:** `canonical_transport.db` (`chennai_multimodal_v1.2.2`) lists `mode = suburban_rail` / `mrts`, but `agency_id = 'MTC'`.
> - **Investigation Finding:** In `canonical_transport.db`, all 107 `suburban_rail` stops and 2 `mrts` stops ingested from OSM Overpass defaulted to `agency_id = 'MTC'`. In reality, Suburban Rail and MRTS services in Chennai are operated by Southern Railway (`SOUTHERN_RAILWAY`, code `SR`), while MTC operates buses.
> - **Protocol Handling:** Per frozen KB policy, database contents are NOT modified in this patch. Instead of silently marking these as `PASS` or obscuring them as 'not directly verifiable', the audit explicitly records them as **`DB_METADATA_MISMATCH_REVIEW_REQUIRED`**.

---

## 3. Egmore Grounding Rectification

> [!IMPORTANT]
> **Egmore Resolution Correction**:
> - **Pre-Audit State (BUG):** `ground_entities.py` previously mapped "Egmore" / "Chennai Egmore" to `HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL` (Chennai Central).
> - **Audit Finding:** `canonical_transport.db` possesses explicit Egmore records: `HUB_EGMORE` (hub_name: "Egmore", member stop: `METRO_EGMORE`) and `HUB_CHENNAI_EGMORE` (hub_name: "Chennai Egmore", member stop: `RAIL_CHENNAI_EGMORE`).
> - **Corrective Action:** Mapped "Egmore" / "Chennai Egmore" to `HUB_EGMORE` (canonical name "Egmore", entity type `transport_hub`, operator `CMRL`, mode `metro`).
> - **Audit Status:** **FAIL_FIXED** (100% verified in database).

---

## 4. Complete Gazetteer Audit Table

| Surface / Name | Declared Canonical ID | DB Table | ID in DB? | DB Canonical Name | Mode / Operator Validation | Audit Status | Notes |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| **Central** | `HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL` | `transport_hubs` | YES | Puratchi Thalaivar Dr. M.G.Ramachandran Central | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PROVISIONAL` | Canonical name alias variance: DB 'Puratchi Thalaivar Dr. M.G.Ramachandran Central' vs declared 'Puratchi Thalaivar Dr. M. G. Ramachandran Central' |
| **Airport** | `HUB_CHENNAI_INTERNATIONAL_AIRPORT` | `transport_hubs` | YES | Chennai International Airport | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **Guindy** | `HUB_GUINDY` | `transport_hubs` | YES | Guindy | NOT_DIRECTLY_VALIDATABLE / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Koyambedu** | `METRO_KOYAMBEDU` | `transport_stops` | YES | Koyambedu | VALIDATED / VALIDATED | `PASS` |  |
| **Alandur** | `HUB_ALANDUR` | `transport_hubs` | YES | Alandur | NOT_DIRECTLY_VALIDATABLE / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Egmore** | `HUB_EGMORE` | `transport_hubs` | YES | Egmore | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `FAIL_FIXED` | Pre-audit mapped to HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL (Chennai Central). Corrected to HUB_EGMORE. |
| **Thirumangalam** | `METRO_THIRUMANGALAM` | `transport_stops` | YES | Thirumangalam | VALIDATED / VALIDATED | `PASS` |  |
| **Saidapet** | `HUB_SAIDAPET` | `transport_hubs` | YES | Saidapet | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **CMBT** | `HUB_CMBT` | `transport_hubs` | YES | CMBT | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **Anna Nagar Tower** | `METRO_ANNA_NAGAR_TOWER` | `transport_stops` | YES | Anna Nagar Tower | VALIDATED / VALIDATED | `PASS` |  |
| **Washermenpet** | `HUB_WASHERMANPET` | `transport_hubs` | YES | Washermanpet | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **Kilpauk** | `METRO_KILPAUK` | `transport_stops` | YES | Kilpauk | VALIDATED / VALIDATED | `PASS` |  |
| **Vadapalani** | `HUB_VADAPALANI` | `transport_hubs` | YES | Vadapalani | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **High Court** | `METRO_HIGH_COURT` | `transport_stops` | YES | High Court | VALIDATED / VALIDATED | `PASS` |  |
| **St. Thomas Mount** | `HUB_ST__THOMAS_MOUNT` | `transport_hubs` | YES | St. Thomas Mount | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **Shenoy Nagar** | `METRO_SHENOY_NAGAR` | `transport_stops` | YES | Shenoy Nagar | VALIDATED / VALIDATED | `PASS` |  |
| **Meenambakkam** | `HUB_MEENAMBAKKAM` | `transport_hubs` | YES | Meenambakkam | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **Tambaram** | `HUB_TAMBARAM` | `transport_hubs` | YES | Tambaram | VALIDATED_VIA_HUB_MEMBERS / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Broadway** | `BUS_840` | `transport_stops` | YES | Broadway | VALIDATED / VALIDATED | `PASS` |  |
| **Adyar Depot** | `BUS_2587520213` | `transport_stops` | YES | Adyar Depot | VALIDATED / VALIDATED | `PASS` |  |
| **Siruseri IT Park** | `BUS_9966` | `transport_stops` | YES | It Park Siruseri Or Muttukadu | VALIDATED / VALIDATED | `PROVISIONAL` | Canonical name alias variance: DB 'It Park Siruseri Or Muttukadu' vs declared 'Siruseri IT Park' |
| **Red Hills** | `BUS_10951278204` | `transport_stops` | YES | Red Hills MTC Bus Terminus | VALIDATED / VALIDATED | `PASS` |  |
| **Besant Nagar** | `BUS_417750654` | `transport_stops` | YES | Besant Nagar | VALIDATED / VALIDATED | `PASS` |  |
| **Mylapore Tank** | `BUS_410614397` | `transport_stops` | YES | Mylapore Tank | VALIDATED / VALIDATED | `PASS` |  |
| **Poonamallee** | `HUB_POONAMALLEE` | `transport_hubs` | YES | Poonamallee | NOT_DIRECTLY_VALIDATABLE / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Porur** | `METRO_PORUR_JUNCTION` | `transport_stops` | YES | Porur Junction | VALIDATED / VALIDATED | `PASS` |  |
| **Thiruvanmiyur** | `BUS_3247310920` | `transport_stops` | YES | Thiruvanmiyur RTO | VALIDATED / VALIDATED | `PROVISIONAL` | Canonical name alias variance: DB 'Thiruvanmiyur RTO' vs declared 'Thiruvanmiyur' |
| **Kelambakkam** | `BUS_1065815351` | `transport_stops` | YES | Vandalur Kelambakkam Bus Terminus | VALIDATED / VALIDATED | `PROVISIONAL` | Canonical name alias variance: DB 'Vandalur Kelambakkam Bus Terminus' vs declared 'Kelambakkam Bus Station' |
| **Chennai Beach** | `RAIL_CHENNAI_BEACH` | `transport_stops` | YES | Chennai Beach | VALIDATED / DB_METADATA_MISMATCH_REVIEW_REQUIRED | `DB_METADATA_MISMATCH_REVIEW_REQUIRED` | declared operator = SR, DB agency value = MTC, mode = suburban_rail/mrts. In canonical_transport.db v1.2.2, all 107 suburban_rail and 2 mrts stops from OSM ingestion defaulted to agency_id='MTC' instead of 'SOUTHERN_RAILWAY'/'SR' (Case A: KB metadata review required). |
| **Mambalam** | `HUB_MAMBALAM` | `transport_hubs` | YES | Mambalam | VALIDATED_VIA_HUB_MEMBERS / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Chepauk** | `MRTS_CHEPAUK` | `transport_stops` | YES | Chepauk | VALIDATED / DB_METADATA_MISMATCH_REVIEW_REQUIRED | `DB_METADATA_MISMATCH_REVIEW_REQUIRED` | declared operator = SR, DB agency value = MTC, mode = suburban_rail/mrts. In canonical_transport.db v1.2.2, all 107 suburban_rail and 2 mrts stops from OSM ingestion defaulted to agency_id='MTC' instead of 'SOUTHERN_RAILWAY'/'SR' (Case A: KB metadata review required). |
| **Thirumayilai** | `HUB_THIRUMAYILAI` | `transport_hubs` | YES | Thirumayilai | NOT_DIRECTLY_VALIDATABLE / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Velachery** | `MRTS_VELACHERY` | `transport_stops` | YES | Velachery | VALIDATED / DB_METADATA_MISMATCH_REVIEW_REQUIRED | `DB_METADATA_MISMATCH_REVIEW_REQUIRED` | declared operator = SR, DB agency value = MTC, mode = suburban_rail/mrts. In canonical_transport.db v1.2.2, all 107 suburban_rail and 2 mrts stops from OSM ingestion defaulted to agency_id='MTC' instead of 'SOUTHERN_RAILWAY'/'SR' (Case A: KB metadata review required). |
| **T. Nagar** | `BUS_28089412` | `transport_stops` | YES | Thyagaraya Nagar Bus Terminus | VALIDATED / VALIDATED | `PASS` |  |
| **Marina Beach** | `OSM_POI_12137617372` | `places` | YES | Marina Beach,Chennai | NOT_DIRECTLY_VALIDATABLE / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Avadi** | `HUB_AVADI` | `transport_hubs` | YES | Avadi | VALIDATED_VIA_HUB_MEMBERS / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Tiruvottiyur** | `RAIL_TIRUVOTTIYUR` | `transport_stops` | YES | Tiruvottiyur | VALIDATED / DB_METADATA_MISMATCH_REVIEW_REQUIRED | `DB_METADATA_MISMATCH_REVIEW_REQUIRED` | declared operator = SR, DB agency value = MTC, mode = suburban_rail/mrts. In canonical_transport.db v1.2.2, all 107 suburban_rail and 2 mrts stops from OSM ingestion defaulted to agency_id='MTC' instead of 'SOUTHERN_RAILWAY'/'SR' (Case A: KB metadata review required). |
| **Chromepet** | `RAIL_CHROMEPET` | `transport_stops` | YES | Chromepet | VALIDATED / DB_METADATA_MISMATCH_REVIEW_REQUIRED | `DB_METADATA_MISMATCH_REVIEW_REQUIRED` | declared operator = SR, DB agency value = MTC, mode = suburban_rail/mrts. In canonical_transport.db v1.2.2, all 107 suburban_rail and 2 mrts stops from OSM ingestion defaulted to agency_id='MTC' instead of 'SOUTHERN_RAILWAY'/'SR' (Case A: KB metadata review required). |
| **Perambur** | `HUB_PERAMBUR` | `transport_hubs` | YES | Perambur | VALIDATED_VIA_HUB_MEMBERS / NOT_DIRECTLY_VALIDATABLE | `PASS` |  |
| **Nandanam** | `METRO_NANDANAM` | `transport_stops` | YES | Nandanam | VALIDATED / VALIDATED | `PASS` |  |
| **Nehru Park** | `METRO_NEHRU_PARK` | `transport_stops` | YES | Nehru Park | VALIDATED / VALIDATED | `PASS` |  |
| **Arumbakkam** | `HUB_ARUMBAKKAM` | `transport_hubs` | YES | Arumbakkam | VALIDATED_VIA_HUB_MEMBERS / VALIDATED_VIA_HUB_MEMBERS | `PASS` |  |
| **Ashok Nagar** | `METRO_ASHOK_NAGAR` | `transport_stops` | YES | Ashok Nagar | VALIDATED / VALIDATED | `PASS` |  |
| **Ekkattuthangal** | `METRO_EKKATTUTHANGAL` | `transport_stops` | YES | Ekkattuthangal | VALIDATED / VALIDATED | `PASS` |  |
| **Anna Nagar** | `METRO_ANNA_NAGAR_TOWER` | `transport_stops` | YES | Anna Nagar Tower | VALIDATED / VALIDATED | `PASS` |  |
| **Blue Line** | `CMRL_BLUE_CORRIDOR_1` | `transport_routes` | YES | Blue Line | VALIDATED / VALIDATED | `PASS` |  |
| **Green Line** | `CMRL_GREEN_CORRIDOR_2` | `transport_routes` | YES | Green Line | VALIDATED / VALIDATED | `PASS` |  |
| **21G** | `GTFS_ROUTE_23750` | `transport_routes` | YES | 21G CT2 | VALIDATED / VALIDATED | `PROVISIONAL` | Variant route pattern short_name in GTFS: DB has '21G CT2', query uses base route '21G' |
| **102** | `GTFS_ROUTE_16861` | `transport_routes` | YES | 102 | VALIDATED / VALIDATED | `PASS` |  |
| **570** | `GTFS_ROUTE_17967` | `transport_routes` | YES | 570 | VALIDATED / VALIDATED | `PASS` |  |
| **114** | `GTFS_ROUTE_17800` | `transport_routes` | YES | 114 | VALIDATED / VALIDATED | `PASS` |  |
| **29C** | `GTFS_ROUTE_18789` | `transport_routes` | YES | 29C CT | VALIDATED / VALIDATED | `PROVISIONAL` | Variant route pattern short_name in GTFS: DB has '29C CT', query uses base route '29C' |
| **54** | `GTFS_ROUTE_23854` | `transport_routes` | YES | 54 CT1 | VALIDATED / VALIDATED | `PROVISIONAL` | Variant route pattern short_name in GTFS: DB has '54 CT1', query uses base route '54' |
| **A1** | `GTFS_ROUTE_23869` | `transport_routes` | YES | A1 CT11 | VALIDATED / VALIDATED | `PROVISIONAL` | Variant route pattern short_name in GTFS: DB has 'A1 CT11', query uses base route 'A1' |
| **19B** | `GTFS_ROUTE_10696` | `transport_routes` | YES | 19B | VALIDATED / VALIDATED | `PASS` |  |
