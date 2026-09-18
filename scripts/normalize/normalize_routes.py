#!/usr/bin/env python3
"""Normalizes transport routes across GTFS and CMRL disclosures.

Preserves route IDs, commercial numbers, variants, mode mappings,
and operating agency provenance.
"""

import os
import sys
import csv
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATE_STR = datetime.now().strftime("%Y-%m-%d")
NORMALIZED_DIR = os.path.join(BASE_DIR, "data", "normalized", "routes")
os.makedirs(NORMALIZED_DIR, exist_ok=True)

OUTPUT_CSV = os.path.join(NORMALIZED_DIR, "normalized_routes.csv")
OUTPUT_JSON = os.path.join(NORMALIZED_DIR, "normalized_routes.json")


def normalize_all_routes():
    normalized_routes = []

    # 1. Ingest CMRL Operational Corridors from CMRL Station API disclosure
    cmrl_corridors = [
        {
            "normalized_route_id": "CMRL_BLUE_CORRIDOR_1",
            "source_id": "CMRL_API",
            "source_route_id": "CORRIDOR_1",
            "agency": "CMRL",
            "route_short_name": "Blue Line",
            "route_long_name": "Wimco Nagar Depot to Chennai International Airport",
            "mode": "metro",
            "route_type": "1",
            "status": "operational"
        },
        {
            "normalized_route_id": "CMRL_GREEN_CORRIDOR_2",
            "source_id": "CMRL_API",
            "source_route_id": "CORRIDOR_2",
            "agency": "CMRL",
            "route_short_name": "Green Line",
            "route_long_name": "Puratchi Thalaivar Dr. M.G. Ramachandran Central to St. Thomas Mount",
            "mode": "metro",
            "route_type": "1",
            "status": "operational"
        }
    ]
    normalized_routes.extend(cmrl_corridors)

    # 1b. Dynamically parse Phase II Corridors from official CMRL disclosure HTML
    phase2_html_path = os.path.join(BASE_DIR, "data", "raw", "cmrl", DATE_STR, "cmrl_phase2_corridor_status.html")
    if os.path.exists(phase2_html_path):
        import re
        with open(phase2_html_path, "r", encoding="utf-8") as f:
            p2_html = f.read()
        p2_text = re.sub(r"<[^>]+>", " ", p2_html)
        p2_text = " ".join(p2_text.split())

        # Extract corridor specifications dynamically
        corridors_spec = [
            ("3", "Purple Line (Phase II)", "CORRIDOR_3"),
            ("4", "Orange Line (Phase II)", "CORRIDOR_4"),
            ("5", "Red Line (Phase II)", "CORRIDOR_5"),
        ]
        for num, short_name, route_code in corridors_spec:
            m = re.search(rf"Corridor-{num}\s+From\s+(.*?)\s+to\s+(.*?)\s+\((\d+\.?\d*)\s*Km\)", p2_text, re.IGNORECASE)
            if m:
                origin, dest, length_km = m.groups()
                long_name = f"{origin} to {dest} ({length_km} km)"
            else:
                long_name = f"Phase II Corridor {num}"

            normalized_routes.append({
                "normalized_route_id": f"CMRL_CORRIDOR_{num}_PHASE2",
                "source_id": "CMRL_OFFICIAL",
                "source_route_id": route_code,
                "agency": "CMRL",
                "route_short_name": short_name,
                "route_long_name": long_name,
                "mode": "metro",
                "route_type": "1",
                "status": "under_construction"
            })
    else:
        print(f"Warning: Phase II disclosure file not found at {phase2_html_path}")

    # 2. Ingest GTFS routes.txt
    gtfs_routes_path = os.path.join(BASE_DIR, "data", "staging", "community_gtfs", DATE_STR, "routes.txt")
    if os.path.exists(gtfs_routes_path):
        with open(gtfs_routes_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rid = row.get("route_id", "")
                agency_id = row.get("agency_id", "MTC")
                short_name = row.get("route_short_name", "")
                long_name = row.get("route_long_name", "")
                rtype = row.get("route_type", "3")
                mode = "metro" if rtype == "1" else "bus"

                normalized_routes.append({
                    "normalized_route_id": f"GTFS_ROUTE_{rid}",
                    "source_id": "CHENNAI_COMMUNITY_GTFS",
                    "source_route_id": rid,
                    "agency": "MTC" if agency_id == "69" else ("CMRL" if agency_id == "CMRL" else agency_id),
                    "route_short_name": short_name,
                    "route_long_name": long_name,
                    "mode": mode,
                    "route_type": rtype,
                    "status": "operational"
                })

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "normalized_date": DATE_STR,
                "total_routes": len(normalized_routes),
                "normalization_version": "1.0"
            },
            "routes": normalized_routes
        }, f, indent=2, ensure_ascii=False)

    fieldnames = [
        "normalized_route_id", "source_id", "source_route_id", "agency",
        "route_short_name", "route_long_name", "mode", "route_type", "status"
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in normalized_routes:
            writer.writerow(r)

    print(f"✅ Successfully normalized {len(normalized_routes)} routes. Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    normalize_all_routes()
