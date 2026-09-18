# Manual Dataset Creation & Domain Curation Protocol (Type C)

**Document:** Manual Dataset Creation Register  
**Stage:** Manual Quality Gates (Phases 16–20)  
**Project:** Chennai Multimodal Public Transport & Places Knowledge Base  

---

## Overview

In accordance with **Hard Stop Protocol (Section 2, Type C)** and **Phases 16–20**, automated inference is unsafe for asserting definitive multimodal hubs, physical pedestrian walking connectivity, colloquial alias factual equivalence, or subjective landmark importance.

The candidate datasets have been automatically extracted from overlapping spatial and lexical evidence and stored in `data/manual/`. This register provides the required schemas, examples, and human decision criteria for each gate.

---

## 1. Manual Hub Creation Gate (Phase 16)

### Why Automation is Inadequate
A shared name root (e.g. "Guindy") and spatial proximity (<500m) indicates that a Metro Station, Suburban Railway Station, and Bus Stop form a multimodal node. However, grouping them must not collapse them into a single stop. Domain verification is required to confirm whether physical entities belong to an official integrated transit hub.

### Required Schema: `data/manual/hubs/manual_hubs.csv`
```csv
hub_id,hub_name,member_entity_id,relationship_type,walking_distance_m,verified,notes
```

### Fields Requiring Human Decisions
- `hub_id`: Canonical hub identifier (e.g. `HUB_GUINDY`, `HUB_CENTRAL`).
- `relationship_type`: `member_station` \| `member_stop` \| `member_terminal`.
- `verified`: `true` (human approved) \| `false` (rejected / not part of hub).

### Example
```csv
hub_id,hub_name,member_entity_id,relationship_type,walking_distance_m,verified,notes
HUB_GUINDY,Guindy Multimodal Hub,CMRL_API_6694,member_station,0,true,Guindy Metro Station
HUB_GUINDY,Guindy Multimodal Hub,OSM_RAIL_315259463,member_station,120.5,true,Guindy Southern Railway Station
HUB_GUINDY,Guindy Multimodal Hub,OSM_BUS_48192039,member_stop,65.0,true,Guindy R.S. MTC Bus Stop
```

**Candidates for Review:** `data/manual/hubs/hub_candidates.csv` (211 candidates).

---

## 2. Manual Multimodal Interchange Gate (Phase 17)

### Why Automation is Inadequate
Straight-line proximity does not establish whether an interchange between two modes is officially integrated (cross-platform, fare-integrated, direct skywalk) or requires street-level navigation.

### Required Schema: `data/manual/interchanges/manual_interchanges.csv`
```csv
interchange_id,from_entity,to_entity,transfer_type,confirmed,walking_distance_m,walking_time_min,notes
```

### Fields Requiring Human Decisions
- `transfer_type`: `integrated_interchange` \| `pedestrian_skywalk` \| `street_level_walking` \| `unsupported`.
- `confirmed`: `true` \| `false`.

### Example
```csv
interchange_id,from_entity,to_entity,transfer_type,confirmed,walking_distance_m,walking_time_min,notes
INT_CENTRAL_METRO_RAIL,CMRL_CENTRAL,SR_CENTRAL_MMC,pedestrian_subway,true,180.0,3.0,Direct underground subway linking Central Metro and suburban MMC terminal.
INT_ALANDUR_INTERCHANGE,CMRL_ALANDUR_L1,CMRL_ALANDUR_L2,integrated_interchange,true,30.0,1.0,Elevated multi-level cross-corridor metro interchange.
```

**Candidates for Review:** `data/manual/interchanges/interchange_candidates.csv` (211 candidates).

---

## 3. Manual Walking Transfers Gate (Phase 18)

### Why Automation is Inadequate
Straight-line distance is **not** sufficient evidence of walkability. Obstacles such as active railway tracks, limited-access arterial expressways (e.g. GST Road, Inner Ring Road), perimeter security walls, and grade separations may physically block pedestrians.

### Required Schema: `data/manual/walking_transfers/manual_walking_transfers.csv`
```csv
from_entity,to_entity,walkable,walking_distance_m,walking_time_min,verification_source,notes
```

### Fields Requiring Human Decisions
- `walkable`: `true` (verified pedestrian path exists) \| `false` (severed by physical obstacle).
- `verification_source`: `survey` \| `pedestrian_map` \| `field_knowledge`.

### Example
```csv
from_entity,to_entity,walkable,walking_distance_m,walking_time_min,verification_source,notes
CMRL_GUINDY,SR_GUINDY,true,120.0,2.0,pedestrian_subway,Direct pedestrian subway beneath GST Road connects Metro concourse to railway platform.
```

**Candidates for Review:** `data/manual/walking_transfers/walking_candidates.csv` (211 candidates).

---

## 4. Manual Alias Curation Gate (Phase 19)

### Why Automation is Inadequate
Colloquial acronyms, historical colonial names, and popular neighbourhood monikers (e.g. *Central* for *Puratchi Thalaivar Dr. M.G. Ramachandran Central*, *Parrys* for *Broadway Bus Terminus*, *Meenambakkam* for *Chennai Airport*) require factual verification so incorrect slang is not elevated to canonical facts.

### Required Schema: `data/manual/aliases/manual_aliases.csv`
```csv
entity_id,canonical_name,candidate_alias,candidate_type,language,approved,notes
```

### Fields Requiring Human Decisions
- `candidate_type`: `official_historical` \| `popular_colloquial` \| `abbreviation` \| `transliteration`.
- `approved`: `true` \| `false`.

**Candidates for Review:** `data/manual/aliases/alias_candidates.csv` (476 candidates).

---

## 5. Manual Landmark Whitelist & Priority Gate (Phase 20)

### Why Automation is Inadequate
OpenStreetMap contains thousands of micro-amenities. Determining which major landmarks are transport-relevant destinations for passenger NLU involves domain selection.

### Required Schema: `data/manual/landmark_priority/manual_landmark_priority.csv`
```csv
place_id,canonical_name,category,priority,include_in_nlp,notes
```

### Fields Requiring Human Decisions
- `priority`: `HIGH` \| `MEDIUM` \| `LOW`.
- `include_in_nlp`: `true` \| `false`.

**Candidates for Review:** `data/manual/landmark_priority/landmark_candidates.csv` (1,621 candidates).
