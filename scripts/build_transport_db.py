#!/usr/bin/env python3
"""Builds the SQLite transport database (data/processed/transport.db)

and exports the multilingual alias lookup gazetteer (data/processed/aliases.csv).

By default, builds the verified CMRL Metro dataset sourced from
data/curated/cmrl_verified_stations.json (grounded in official CMRL portal data).
"""

import os
import csv
import json
import sqlite3
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATED_JSON_PATH = os.path.join(BASE_DIR, "data", "curated", "cmrl_verified_stations.json")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(DATA_PROCESSED_DIR, "transport.db")
ALIASES_CSV_PATH = os.path.join(DATA_PROCESSED_DIR, "aliases.csv")


def load_curated_data() -> Dict[str, Any]:
    """Loads curated and verified CMRL station dataset."""
    if not os.path.exists(CURATED_JSON_PATH):
        raise FileNotFoundError(f"Verified dataset not found at {CURATED_JSON_PATH}")

    with open(CURATED_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def init_db(use_verified_only: bool = True):
    """Initializes tables in SQLite database with verified CMRL records."""
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    data = load_curated_data()
    stations = data.get("stations", [])
    aliases = data.get("aliases", [])
    facilities = data.get("facilities", [])
    connections = data.get("connections", [])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Stations table
    cursor.execute("""
        CREATE TABLE stations (
            station_id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_hi TEXT NOT NULL,
            name_ta TEXT,
            type TEXT NOT NULL,
            latitude REAL,
            longitude REAL
        )
    """)

    # 2. Station Aliases table
    cursor.execute("""
        CREATE TABLE station_aliases (
            alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            alias TEXT NOT NULL,
            language TEXT NOT NULL,
            script TEXT NOT NULL,
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        )
    """)

    # 3. Connections table
    cursor.execute("""
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
        )
    """)

    # 4. Facilities table (0 = unavailable, 1 = available, NULL = unknown)
    cursor.execute("""
        CREATE TABLE facilities (
            station_id TEXT PRIMARY KEY,
            wheelchair_available INTEGER DEFAULT NULL CHECK (wheelchair_available IN (0, 1)),
            lift_available INTEGER DEFAULT NULL CHECK (lift_available IN (0, 1)),
            tactile_paths INTEGER DEFAULT NULL CHECK (tactile_paths IN (0, 1)),
            accessible_toilet INTEGER DEFAULT NULL CHECK (accessible_toilet IN (0, 1)),
            parking_available INTEGER DEFAULT NULL CHECK (parking_available IN (0, 1)),
            notes_hi TEXT,
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        )
    """)

    # 5. Service Info table
    cursor.execute("""
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
        )
    """)

    # Insert Stations
    for s in stations:
        cursor.execute(
            "INSERT INTO stations VALUES (?, ?, ?, ?, ?, ?, ?)",
            (s["station_id"], s["name_en"], s["name_hi"], s.get("name_ta", ""), s["type"], s["lat"], s["lon"])
        )

    # Insert Aliases
    for station_id, alias, lang, script in aliases:
        cursor.execute(
            "INSERT INTO station_aliases (station_id, alias, language, script) VALUES (?, ?, ?, ?)",
            (station_id, alias, lang, script)
        )

    # Insert Connections
    for conn_data in connections:
        origin_id, dest_id, mode, line_name, direct = conn_data
        cursor.execute(
            "INSERT INTO connections (origin_id, destination_id, mode, line_name, direct) VALUES (?, ?, ?, ?, ?)",
            (origin_id, dest_id, mode, line_name, direct)
        )

    # Insert Facilities
    for f in facilities:
        cursor.execute(
            """INSERT INTO facilities (station_id, wheelchair_available, lift_available,
                                      tactile_paths, accessible_toilet, parking_available, notes_hi)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f["station_id"],
                f.get("wheelchair_available"),
                f.get("lift_available"),
                f.get("tactile_paths"),
                f.get("accessible_toilet"),
                f.get("parking_available"),
                f.get("notes_hi")
            )
        )

    conn.commit()
    conn.close()
    print(f"✅ Successfully initialized verified SQLite database ({len(stations)} stations) at: {DB_PATH}")


def export_aliases_csv():
    """Exports aliases list into data/processed/aliases.csv for gazetteer lookups."""
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    data = load_curated_data()
    aliases = data.get("aliases", [])

    with open(ALIASES_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["station_id", "alias", "language", "script"])
        for row in aliases:
            writer.writerow(row)
    print(f"✅ Successfully exported {len(aliases)} verified aliases to: {ALIASES_CSV_PATH}")


if __name__ == "__main__":
    init_db()
    export_aliases_csv()
