#!/usr/bin/env python3
"""Builds the canonical multimodal transport knowledge base SQLite database:

  data/canonical/transit/canonical_transport.db
and companion canonical JSON/CSV exports.

Includes full field-level provenance, source-link mapping (entity_source_links),
multilingual names (stop_names, place_names), and explicit separation between
physical stops, transport hubs, multimodal interchanges, and walking transfers.
"""

import os
import sys
import csv
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CANONICAL_DIR = os.path.join(BASE_DIR, "data", "canonical", "transit")
os.makedirs(CANONICAL_DIR, exist_ok=True)
DB_PATH = os.path.join(CANONICAL_DIR, "canonical_transport.db")

STOPS_CSV = os.path.join(BASE_DIR, "data", "normalized", "stops", "normalized_stops.csv")
ROUTES_CSV = os.path.join(BASE_DIR, "data", "normalized", "routes", "normalized_routes.csv")
PLACES_CSV = os.path.join(BASE_DIR, "data", "normalized", "places", "normalized_places.csv")
HUB_CANDIDATES_CSV = os.path.join(BASE_DIR, "data", "manual", "hubs", "hub_candidates.csv")
INT_CANDIDATES_CSV = os.path.join(BASE_DIR, "data", "manual", "interchanges", "interchange_candidates.csv")
WALK_CANDIDATES_CSV = os.path.join(BASE_DIR, "data", "manual", "walking_transfers", "walking_candidates.csv")
ALIAS_CANDIDATES_CSV = os.path.join(BASE_DIR, "data", "manual", "aliases", "alias_candidates.csv")


def build_canonical_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. transport_agencies
    cur.execute("""
        CREATE TABLE transport_agencies (
            agency_id TEXT PRIMARY KEY,
            agency_name TEXT NOT NULL,
            agency_code TEXT NOT NULL,
            mode TEXT NOT NULL,
            website TEXT,
            official_status TEXT,
            license TEXT
        );
    """)

    # 2. transport_stops
    cur.execute("""
        CREATE TABLE transport_stops (
            stop_id TEXT PRIMARY KEY,
            canonical_name TEXT NOT NULL,
            mode TEXT NOT NULL,
            stop_type TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            inside_cma INTEGER NOT NULL,
            agency_id TEXT,
            operational_status TEXT NOT NULL,
            primary_source_id TEXT NOT NULL,
            FOREIGN KEY (agency_id) REFERENCES transport_agencies(agency_id)
        );
    """)

    # 3. stop_names (Multilingual & Variants)
    cur.execute("""
        CREATE TABLE stop_names (
            name_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stop_id TEXT NOT NULL,
            name TEXT NOT NULL,
            name_type TEXT NOT NULL, -- official, tamil, abbreviation, colloquial, historical
            language TEXT NOT NULL,
            script TEXT NOT NULL,
            source_id TEXT,
            FOREIGN KEY (stop_id) REFERENCES transport_stops(stop_id)
        );
    """)

    # 4. transport_routes
    cur.execute("""
        CREATE TABLE transport_routes (
            route_id TEXT PRIMARY KEY,
            agency_id TEXT NOT NULL,
            route_short_name TEXT,
            route_long_name TEXT,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            source_id TEXT,
            FOREIGN KEY (agency_id) REFERENCES transport_agencies(agency_id)
        );
    """)

    # 5. transport_hubs
    cur.execute("""
        CREATE TABLE transport_hubs (
            hub_id TEXT PRIMARY KEY,
            hub_name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            inside_cma INTEGER NOT NULL,
            verified INTEGER DEFAULT 0,
            notes TEXT
        );
    """)

    # 6. hub_members
    cur.execute("""
        CREATE TABLE hub_members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hub_id TEXT NOT NULL,
            stop_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL, -- member_station, member_stop, member_terminal
            walking_distance_m REAL,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (hub_id) REFERENCES transport_hubs(hub_id),
            FOREIGN KEY (stop_id) REFERENCES transport_stops(stop_id)
        );
    """)

    # 7. interchanges
    cur.execute("""
        CREATE TABLE interchanges (
            interchange_id TEXT PRIMARY KEY,
            from_stop_id TEXT NOT NULL,
            to_stop_id TEXT NOT NULL,
            transfer_type TEXT NOT NULL,
            confirmed INTEGER DEFAULT 0,
            walking_distance_m REAL,
            walking_time_min REAL,
            notes TEXT,
            FOREIGN KEY (from_stop_id) REFERENCES transport_stops(stop_id),
            FOREIGN KEY (to_stop_id) REFERENCES transport_stops(stop_id)
        );
    """)

    # 8. walking_transfers
    cur.execute("""
        CREATE TABLE walking_transfers (
            transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_stop_id TEXT NOT NULL,
            to_stop_id TEXT NOT NULL,
            straight_line_distance_m REAL,
            walkable TEXT NOT NULL, -- confirmed, unverified_walking_transfer, obstacle_blocked
            estimated_walking_time_min REAL,
            notes TEXT,
            FOREIGN KEY (from_stop_id) REFERENCES transport_stops(stop_id),
            FOREIGN KEY (to_stop_id) REFERENCES transport_stops(stop_id)
        );
    """)

    # 9. places (Geographic POIs & Landmarks)
    cur.execute("""
        CREATE TABLE places (
            place_id TEXT PRIMARY KEY,
            canonical_name TEXT NOT NULL,
            category TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            inside_cma INTEGER NOT NULL,
            priority TEXT DEFAULT 'MEDIUM',
            source_id TEXT NOT NULL
        );
    """)

    # 10. place_names
    cur.execute("""
        CREATE TABLE place_names (
            name_id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT NOT NULL,
            name TEXT NOT NULL,
            language TEXT NOT NULL,
            script TEXT NOT NULL,
            FOREIGN KEY (place_id) REFERENCES places(place_id)
        );
    """)

    # 11. accessibility
    cur.execute("""
        CREATE TABLE accessibility (
            stop_id TEXT PRIMARY KEY,
            wheelchair_available INTEGER,
            lift_available INTEGER,
            escalator_available INTEGER,
            ramp_available INTEGER,
            accessible_toilet INTEGER,
            parking_available INTEGER,
            tactile_paths INTEGER,
            notes_hi TEXT,
            FOREIGN KEY (stop_id) REFERENCES transport_stops(stop_id)
        );
    """)

    # 12. entity_source_links (End-to-End Provenance)
    cur.execute("""
        CREATE TABLE entity_source_links (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL, -- stop, route, hub, place
            canonical_entity_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_record_id TEXT NOT NULL,
            raw_file_id TEXT,
            relationship TEXT NOT NULL, -- primary_evidence, supporting_evidence, historical_evidence, conflicting_evidence
            confidence REAL NOT NULL
        );
    """)

    # Populate Agencies
    agencies_data = [
        ("CMRL", "Chennai Metro Rail Limited", "CMRL", "metro", "https://chennaimetrorail.org/", "tier_1_official", "REVIEW_REQUIRED"),
        ("MTC", "Metropolitan Transport Corporation (Chennai) Ltd.", "MTC", "bus", "https://mtcbus.tn.gov.in/", "tier_1_official", "REVIEW_REQUIRED"),
        ("SOUTHERN_RAILWAY", "Southern Railway Zone, Indian Railways", "SR", "suburban_rail", "https://sr.indianrailways.gov.in/", "tier_1_official", "REVIEW_REQUIRED"),
        ("CUMTA", "Chennai Unified Metropolitan Transport Authority", "CUMTA", "multimodal", "https://cumta.tn.gov.in/", "tier_1_official", "REVIEW_REQUIRED")
    ]
    cur.executemany("INSERT INTO transport_agencies VALUES (?, ?, ?, ?, ?, ?, ?)", agencies_data)

    # Populate Stops & Source Links
    stop_count = 0
    with open(STOPS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            sid = r["normalized_id"]
            name = r["normalized_name"]
            mode = r["mode"]
            stype = r["stop_type"]
            lat = float(r["normalized_latitude"]) if r["normalized_latitude"] else None
            lon = float(r["normalized_longitude"]) if r["normalized_longitude"] else None
            in_cma = 1 if r["inside_cma"].lower() == "true" else 0
            agency = r["agency"]
            if "metro" in mode:
                aid = "CMRL"
            elif "bus" in mode:
                aid = "MTC"
            else:
                aid = "SOUTHERN_RAILWAY"

            cur.execute("""
                INSERT INTO transport_stops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid, name, mode, stype, lat, lon, in_cma, aid, r["operational_status"], r["source_id"]))

            # Insert primary source link
            cur.execute("""
                INSERT INTO entity_source_links (entity_type, canonical_entity_id, source_id, source_record_id, raw_file_id, relationship, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("stop", sid, r["source_id"], r["source_record_id"], r["raw_file_id"], "primary_evidence", 1.0))

            # Stop names (English)
            cur.execute("""
                INSERT INTO stop_names (stop_id, name, name_type, language, script, source_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sid, name, "official_english", "en", "Latn", r["source_id"]))

            # Tamil name if present
            if r["name_ta"]:
                cur.execute("""
                    INSERT INTO stop_names (stop_id, name, name_type, language, script, source_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sid, r["name_ta"], "official_tamil", "ta", "Taml", r["source_id"]))

            stop_count += 1

    # Populate Accessibility from CMRL
    cmrl_staged = os.path.join(BASE_DIR, "data", "staging", "cmrl", datetime.now().strftime("%Y-%m-%d"), "cmrl_parsed_stations.json")
    if os.path.exists(cmrl_staged):
        with open(cmrl_staged, "r", encoding="utf-8") as f:
            cdata = json.load(f)
        for s in cdata.get("stations", []):
            sid = f"CMRL_API_{s.get('source_record_id')}"
            fac = s.get("facilities", {})
            cur.execute("""
                INSERT OR REPLACE INTO accessibility VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sid,
                fac.get("wheelchair_available"),
                fac.get("lift_available"),
                fac.get("escalator_available"),
                fac.get("ramp_available"),
                fac.get("accessible_toilet"),
                fac.get("parking_available"),
                None,  # tactile paths
                "आधिकारिक CMRL पोर्टल रिकॉर्ड"
            ))

    # Populate Routes
    route_count = 0
    with open(ROUTES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rid = r["normalized_route_id"]
            aid = r["agency"]
            if aid not in ["CMRL", "MTC", "SOUTHERN_RAILWAY", "CUMTA"]:
                aid = "MTC"
            cur.execute("""
                INSERT INTO transport_routes VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rid, aid, r["route_short_name"], r["route_long_name"], r["mode"], r["status"], r["source_id"]))
            route_count += 1

    # Populate Places
    place_count = 0
    with open(PLACES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = r["place_id"]
            pname = r["name"]
            cat = r["category"]
            lat = float(r["latitude"]) if r["latitude"] else None
            lon = float(r["longitude"]) if r["longitude"] else None
            in_cma = 1 if r["inside_cma"].lower() == "true" else 0
            cur.execute("""
                INSERT INTO places VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, pname, cat, lat, lon, in_cma, "MEDIUM", r["source_id"]))

            # Place name
            cur.execute("""
                INSERT INTO place_names (place_id, name, language, script)
                VALUES (?, ?, ?, ?)
            """, (pid, pname, "en", "Latn"))

            if r.get("name_ta"):
                cur.execute("""
                    INSERT INTO place_names (place_id, name, language, script)
                    VALUES (?, ?, ?, ?)
                """, (pid, r["name_ta"], "ta", "Taml"))

            place_count += 1

    # Populate Candidate Hubs
    hub_count = 0
    seen_hubs = set()
    with open(HUB_CANDIDATES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            hid = r["hub_id"]
            if hid not in seen_hubs:
                seen_hubs.add(hid)
                cur.execute("""
                    INSERT INTO transport_hubs VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (hid, r["hub_name"], None, None, 1, 0, r["notes"]))
                hub_count += 1

            cur.execute("""
                INSERT INTO hub_members (hub_id, stop_id, relationship_type, walking_distance_m, verified)
                VALUES (?, ?, ?, ?, ?)
            """, (hid, r["member_entity_id"], "member_station", float(r["walking_distance_m"]), 0))

    # Populate Candidate Interchanges
    int_count = 0
    with open(INT_CANDIDATES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cur.execute("""
                INSERT OR REPLACE INTO interchanges VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["interchange_id"], r["from_entity"], r["to_entity"],
                r["transfer_type"], 0, float(r["walking_distance_m"]),
                float(r["walking_time_min"]), r["notes"]
            ))
            int_count += 1

    # Populate Walking Transfers
    walk_count = 0
    with open(WALK_CANDIDATES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cur.execute("""
                INSERT INTO walking_transfers (from_stop_id, to_stop_id, straight_line_distance_m, walkable, estimated_walking_time_min, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                r["from_entity"], r["to_entity"], float(r["straight_line_distance_m"]),
                r["walkable"], float(r["estimated_walking_time_min"]), r["obstacle_notes"]
            ))
            walk_count += 1

    conn.commit()
    conn.close()

    print(f"✅ Successfully built canonical database at: {DB_PATH}")
    print(f"Summary:")
    print(f"  - Stops: {stop_count}")
    print(f"  - Routes: {route_count}")
    print(f"  - Places & POIs: {place_count}")
    print(f"  - Candidate Hubs: {hub_count}")
    print(f"  - Candidate Interchanges: {int_count}")
    print(f"  - Walking Transfers: {walk_count}")


if __name__ == "__main__":
    build_canonical_database()
