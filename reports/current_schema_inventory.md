# Phase 0: Current Schema Inventory

**Generated:** 2026-09-18  
**Project:** Chennai Multimodal Public Transport Assistant & Knowledge Base  
**Status:** Complete — Phase 0 Gate  

---

## 1. Overview

This document provides the formal schema inventory of all existing data assets in the project prior to the multimodal expansion. It details table definitions, primary keys, foreign keys, nullable attributes, constraints, tabular schemas, JSON structures, and entity naming conventions.

---

## 2. SQLite Database Schemas (`data/processed/transport.db`)

The active relational store contains 5 core tables.

### 2.1. `stations` Table
Stores canonical station entities with geographic coordinates and multilingual names.

```sql
CREATE TABLE stations (
    station_id TEXT PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_hi TEXT NOT NULL,
    name_ta TEXT,
    type TEXT NOT NULL,
    latitude REAL,
    longitude REAL
);
```

- `station_id`: Canonical unique identifier (e.g. `CHENNAI_CENTRAL`, `GUINDY`).
- `name_en`: Official name in English.
- `name_hi`: Official/curated name in Hindi (Devanagari).
- `name_ta`: Official/curated name in Tamil script. Nullable.
- `type`: Station classification (`metro_station`, `metro_interchange`, `suburban_station`, `railway_terminal`, `mrts_station`, `bus_terminus`).
- `latitude`, `longitude`: WGS84 decimal degrees.

### 2.2. `station_aliases` Table
Gazetteer table mapping various lexical forms, transliterations, and colloquial names to canonical station IDs.

```sql
CREATE TABLE station_aliases (
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    language TEXT NOT NULL,
    script TEXT NOT NULL,
    FOREIGN KEY (station_id) REFERENCES stations(station_id)
);
```

- `alias_id`: Auto-incrementing integer PK.
- `station_id`: FK referencing `stations.station_id`.
- `alias`: Normalized or natural surface text string.
- `language`: Language code (`hi`, `en`, `ta`, `hinglish`).
- `script`: ISO 15924 script code (`Deva`, `Latn`, `Taml`).

### 2.3. `connections` Table
Stores explicit direct transit segments and verified corridors between station pairs.

```sql
CREATE TABLE connections (
    connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_id TEXT NOT NULL,
    destination_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    line_name TEXT NOT NULL,
    travel_time_mins INTEGER DEFAULT NULL,
    distance_km REAL DEFAULT NULL,
    direct INTEGER DEFAULT 1,
    FOREIGN KEY (origin_id) REFERENCES stations(station_id),
    FOREIGN KEY (destination_id) REFERENCES stations(station_id)
);
```

- `connection_id`: Auto-incrementing integer PK.
- `origin_id`, `destination_id`: FKs referencing `stations.station_id`.
- `mode`: Transit mode (`metro`, `suburban_rail`, `mrts`, `bus`).
- `line_name`: Descriptive route/corridor name (e.g. `Blue Line`, `Green Line`).
- `travel_time_mins`: Estimated travel time in minutes. Nullable.
- `distance_km`: Approximate distance in kilometers. Nullable.
- `direct`: Boolean flag (1 = direct service, 0 = requires interchange).

### 2.4. `facilities` Table
Station-level accessibility and amenity disclosures.

```sql
CREATE TABLE facilities (
    station_id TEXT PRIMARY KEY,
    wheelchair_available INTEGER DEFAULT NULL CHECK (wheelchair_available IN (0, 1)),
    lift_available INTEGER DEFAULT NULL CHECK (lift_available IN (0, 1)),
    tactile_paths INTEGER DEFAULT NULL CHECK (tactile_paths IN (0, 1)),
    accessible_toilet INTEGER DEFAULT NULL CHECK (accessible_toilet IN (0, 1)),
    parking_available INTEGER DEFAULT NULL CHECK (parking_available IN (0, 1)),
    notes_hi TEXT,
    FOREIGN KEY (station_id) REFERENCES stations(station_id)
);
```

- `station_id`: PK referencing `stations.station_id`.
- Tri-state flags: `1` (verified present), `0` (verified absent), `NULL` (unknown/unverified).
- `notes_hi`: Descriptive Hindi text summarizing official facilities.

### 2.5. `service_info` Table
Line-level operating hours, frequencies, and fare ranges.

```sql
CREATE TABLE service_info (
    route_id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    line_name TEXT NOT NULL,
    first_service TEXT DEFAULT NULL,
    last_service TEXT DEFAULT NULL,
    peak_frequency_mins INTEGER DEFAULT NULL,
    non_peak_frequency_mins INTEGER DEFAULT NULL,
    min_fare REAL DEFAULT NULL,
    max_fare REAL DEFAULT NULL
);
```

---

## 3. CSV Dataset Schemas

### 3.1. `data/processed/aliases.csv`
Tabular gazetteer export for fast in-memory slot extraction.

| Column | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `station_id` | string | Canonical station identifier | `CHENNAI_CENTRAL` |
| `alias` | string | Surface alias text | `chennai central` |
| `language` | string | Language code | `en` |
| `script` | string | ISO script code | `Latn` |

### 3.2. `data/processed/intents.csv` & `data/processed/split/*.csv`
Classification benchmark dataset containing 5,204 queries.

| Column | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `query` | string | Natural language question | `चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?` |
| `template_family` | string | Template generator family identifier | `route_query:how_basic` |
| `station` | string | Associated station entity (if any) | `CHENNAI_CENTRAL` |
| `intent` | string | Target intent label (7 classes) | `route_query` |
| `origin` | string | Extracted origin station ID | `CHENNAI_CENTRAL` |
| `destination` | string | Extracted destination station ID | `CHENNAI_AIRPORT` |
| `transport_mode` | string | Extracted transport mode | `metro` |
| `information_type` | string | Requested facility/information type | `wheelchair` |
| `slots_reviewed` | boolean | Whether slots are human-verified | `False` |
| `language` | string | Language of query (`hi`, `hinglish`) | `hi` |
| `script` | string | Script of query (`devanagari`, `latin_hinglish`) | `devanagari` |
| `source` | string | Generation origin (`template_combinatorial`, `hinglish_top_train`) | `template_combinatorial` |
| `split` | string | Split partition (`train`, `val`, `test`) | `train` |

---

## 4. JSON Dataset Schemas

### 4.1. Curated Station Fixture (`data/curated/cmrl_verified_stations.json`)
```json
{
  "metadata": {
    "source_agency": "string",
    "source_url": "string",
    "retrieval_date": "YYYY-MM-DD",
    "verification_status": "string",
    "license_notes": "string"
  },
  "stations": [
    {
      "station_id": "string",
      "name_en": "string",
      "name_hi": "string",
      "name_ta": "string",
      "type": "string",
      "corridor": "string",
      "lat": "float",
      "lon": "float"
    }
  ],
  "aliases": [
    ["station_id", "alias", "language", "script"]
  ],
  "facilities": [
    {
      "station_id": "string",
      "wheelchair_available": 0 | 1 | null,
      "lift_available": 0 | 1 | null,
      "tactile_paths": 0 | 1 | null,
      "accessible_toilet": 0 | 1 | null,
      "parking_available": 0 | 1 | null,
      "notes_hi": "string"
    }
  ],
  "connections": [
    ["origin_id", "destination_id", "mode", "line_name", 0 | 1]
  ]
}
```

### 4.2. Scraped Station Feed (`data/curated/cmrl_scraped_stations.json`)
```json
{
  "total_stations": 43,
  "stations": [
    {
      "id": "int",
      "name": "string",
      "slug": "string",
      "url": "string",
      "phase_one_ids": ["int"],
      "phase_two_ids": ["int"],
      "detected_facilities": ["string"],
      "raw_html_snippet": "string"
    }
  ]
}
```

### 4.3. Acceptance Gold Suite (`data/eval/acceptance_test_suite.json`)
Consists of exactly **149 gold evaluation cases**:
```json
{
  "id": "string (e.g. acc_route_001)",
  "query": "string",
  "gold_intent": "route_query | service_availability | service_timing | station_information | accessibility | ticketing | out_of_scope",
  "gold_origin": "string | null",
  "gold_destination": "string | null",
  "gold_station": "string | null",
  "gold_mode": "string | null",
  "gold_facility": "string | null",
  "expected_response_type": "string",
  "expected_substrings": ["string"],
  "forbidden_substrings": ["string"],
  "linguistic_form": "formal_hi | colloquial_hi | hinglish"
}
```

### 4.4. Split Manifest (`data/processed/split/split_manifest.json`)
```json
{
  "strategy": "family_disjoint_stratified",
  "train_ratio": 0.7,
  "validation_ratio": 0.15,
  "test_ratio": 0.15,
  "split_seed": 42,
  "num_train": 3916,
  "num_validation": 716,
  "num_test": 572,
  "total_samples": 5204,
  "intents": ["accessibility", "out_of_scope", "route_query", "service_availability", "service_timing", "station_information", "ticketing"],
  "classes_distribution": {
    "train": { "...": 0 },
    "validation": { "...": 0 },
    "test": { "...": 0 }
  }
}
```

---

## 5. Canonical Entity Naming Conventions

1. **Station Identifiers:** Uppercase snake_case representing the primary English landmark name:
   - Metro: `CHENNAI_CENTRAL`, `CHENNAI_AIRPORT`, `ALANDUR`, `WIMCO_NAGAR`
   - Suburban: `CHENNAI_BEACH`, `TAMBARAM`, `CHENGALPATTU`, `TIRUVALLUR`
   - MRTS: `CHEPAUK`, `LIGHT_HOUSE`, `THIRUMAYILAI`, `VELACHERY`
   - Bus Termini: `KCBT_KILAMBAKKAM`, `MMBT_MADHAVARAM`, `BROADWAY_BUS_TERMINUS`, `T_NAGAR_BUS_TERMINUS`
2. **Language Codes:** BCP 47 compliant (`en`, `hi`, `ta`, `hinglish`).
3. **Script Codes:** ISO 15924 (`Latn`, `Deva`, `Taml`).
4. **Transport Modes:** Internal canonical strings:
   - `metro`
   - `suburban_rail`
   - `mrts`
   - `bus`
   - `railway` (generic/intercity)
