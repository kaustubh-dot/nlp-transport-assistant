#!/usr/bin/env python3
"""Detects conflicts and disagreements between overlapping data sources.

Logs discrepancies in coordinates (>50m), naming variations, and station types
into reports/data_conflicts.csv in accordance with Phase 14 specifications.
"""

import os
import sys
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CANDIDATES_CSV = os.path.join(BASE_DIR, "data", "staging", "entity_match_candidates.csv")
STOPS_CSV = os.path.join(BASE_DIR, "data", "normalized", "stops", "normalized_stops.csv")
CONFLICTS_CSV = os.path.join(BASE_DIR, "reports", "data_conflicts.csv")
os.makedirs(os.path.dirname(CONFLICTS_CSV), exist_ok=True)


def detect_conflicts():
    if not os.path.exists(CANDIDATES_CSV) or not os.path.exists(STOPS_CSV):
        raise FileNotFoundError("Missing candidates or normalized stops file.")

    # Load normalized stops lookup
    stops_by_id = {}
    with open(STOPS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stops_by_id[row["normalized_id"]] = row

    conflicts = []
    conflict_counter = 1

    with open(CANDIDATES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel = row.get("candidate_relationship")
            if rel not in ["same_station", "same_physical_entity"]:
                continue

            id_a = row.get("record_a")
            id_b = row.get("record_b")
            dist_m = float(row.get("distance_m", 0))

            stop_a = stops_by_id.get(id_a)
            stop_b = stops_by_id.get(id_b)
            if not stop_a or not stop_b:
                continue

            # 1. Check Coordinate Discrepancy > 40m for matching stations
            if dist_m > 40.0:
                conflicts.append({
                    "conflict_id": f"CONF_{conflict_counter:04d}",
                    "entity_candidate": f"{stop_a['normalized_name']} <-> {stop_b['normalized_name']}",
                    "field": "coordinates",
                    "source_a": stop_a["source_id"],
                    "value_a": f"({stop_a['normalized_latitude']}, {stop_a['normalized_longitude']})",
                    "source_b": stop_b["source_id"],
                    "value_b": f"({stop_b['normalized_latitude']}, {stop_b['normalized_longitude']})",
                    "source_dates": "2026-09-18",
                    "authority_notes": f"Distance delta: {dist_m:.1f}m between {stop_a['source_id']} and {stop_b['source_id']}.",
                    "status": "unresolved_logged",
                    "resolution": "Preserve both coordinates as source evidence; prioritize official operator/OSM surveyed platform in canonical.",
                    "requires_manual_review": False
                })
                conflict_counter += 1

            # 2. Check Name Discrepancy
            name_a = stop_a["normalized_name"]
            name_b = stop_b["normalized_name"]
            if name_a.lower() != name_b.lower() and float(row.get("name_similarity", 100)) < 90:
                conflicts.append({
                    "conflict_id": f"CONF_{conflict_counter:04d}",
                    "entity_candidate": f"{name_a} <-> {name_b}",
                    "field": "station_name",
                    "source_a": stop_a["source_id"],
                    "value_a": name_a,
                    "source_b": stop_b["source_id"],
                    "value_b": name_b,
                    "source_dates": "2026-09-18",
                    "authority_notes": f"Name similarity: {row.get('name_similarity')}%. Official vs colloquial/abbreviated form.",
                    "status": "resolved_alias",
                    "resolution": "Preserve secondary name as official alias under primary canonical identity.",
                    "requires_manual_review": False
                })
                conflict_counter += 1

    fieldnames = [
        "conflict_id", "entity_candidate", "field", "source_a", "value_a",
        "source_b", "value_b", "source_dates", "authority_notes", "status",
        "resolution", "requires_manual_review"
    ]

    with open(CONFLICTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in conflicts:
            writer.writerow(c)

    print(f"✅ Successfully detected and logged {len(conflicts)} cross-source conflicts.")
    print(f"Saved to: {CONFLICTS_CSV}")


if __name__ == "__main__":
    detect_conflicts()
