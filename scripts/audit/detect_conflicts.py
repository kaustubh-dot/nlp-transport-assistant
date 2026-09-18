#!/usr/bin/env python3
"""Detects and audits discrepancies between overlapping transit data sources.

Logs discrepancies into reports/data_conflicts.csv with explicit four-tier resolution status:
- AUTO_RESOLVED: Deterministically resolved by canonical precedence policy (e.g. surveyed coordinates over street interpolation).
- HUMAN_RESOLVED: Resolved by explicit domain rule or verified curation.
- UNRESOLVED_NONBLOCKING: Known minor discrepancy (e.g. multi-entrance span) safe for routing.
- UNRESOLVED_BLOCKING: High-impact ambiguous discrepancy requiring human review before operational use.

Generates aggregated summary counts by:
- Conflict Field
- Source Pair
- Transport Mode
- Resolution Status
"""

import os
import sys
import csv
from collections import Counter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CANDIDATES_CSV = os.path.join(BASE_DIR, "data", "staging", "entity_match_candidates.csv")
STOPS_CSV = os.path.join(BASE_DIR, "data", "normalized", "stops", "normalized_stops.csv")
CONFLICTS_CSV = os.path.join(BASE_DIR, "reports", "data_conflicts.csv")
SUMMARY_MD = os.path.join(BASE_DIR, "reports", "data_conflicts_summary.md")
os.makedirs(os.path.dirname(CONFLICTS_CSV), exist_ok=True)


def detect_conflicts():
    if not os.path.exists(CANDIDATES_CSV) or not os.path.exists(STOPS_CSV):
        raise FileNotFoundError("Missing candidates or normalized stops file.")

    stops_by_id = {}
    with open(STOPS_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stops_by_id[row["normalized_id"]] = row

    conflicts = []
    conflict_counter = 1

    with open(CANDIDATES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel = row.get("candidate_relationship")
            id_a = row.get("record_a")
            id_b = row.get("record_b")
            dist_m = float(row.get("distance_m", 0))
            sim = float(row.get("name_similarity", 100))

            stop_a = stops_by_id.get(id_a)
            stop_b = stops_by_id.get(id_b)
            if not stop_a or not stop_b:
                continue

            mode_a = stop_a["mode"]
            mode_b = stop_b["mode"]
            src_a = stop_a["source_id"]
            src_b = stop_b["source_id"]
            src_pair = f"{src_a} <-> {src_b}"

            # Only analyze same-mode entities for station-level conflicts
            if mode_a != mode_b:
                continue

            # 1. Coordinate Discrepancy Analysis (> 35m for matching stations)
            if dist_m > 35.0 and rel in ["same_station", "same_physical_entity"]:
                if dist_m > 500.0:
                    status = "UNRESOLVED_BLOCKING"
                    res_note = "Major coordinate discrepancy (>500m). Retained as separate candidates pending human field verification."
                    req_review = True
                elif dist_m > 100.0:
                    status = "UNRESOLVED_NONBLOCKING"
                    res_note = "Facility span / multi-entrance coordinate variation (100m-500m). Surveyed OSM/operator coordinates preferred."
                    req_review = True
                else:
                    status = "AUTO_RESOLVED"
                    res_note = "Resolved to authoritative operator / surveyed platform coordinates over street interpolation."
                    req_review = False

                conflicts.append({
                    "conflict_id": f"CONF_{conflict_counter:04d}",
                    "entity_candidate": f"{stop_a['normalized_name']} <-> {stop_b['normalized_name']}",
                    "transport_mode": mode_a,
                    "conflict_field": "coordinates",
                    "source_pair": src_pair,
                    "source_a": src_a,
                    "value_a": f"({stop_a['normalized_latitude']}, {stop_a['normalized_longitude']})",
                    "source_b": src_b,
                    "value_b": f"({stop_b['normalized_latitude']}, {stop_b['normalized_longitude']})",
                    "delta_metric": f"{dist_m:.1f}m",
                    "resolution_status": status,
                    "resolution_action": res_note,
                    "requires_manual_review": req_review
                })
                conflict_counter += 1

            # 2. Station Name Discrepancy Analysis
            name_a = stop_a["normalized_name"]
            name_b = stop_b["normalized_name"]
            if name_a.lower() != name_b.lower() and sim < 90 and rel in ["same_station", "same_physical_entity"]:
                if sim < 60:
                    status = "UNRESOLVED_BLOCKING"
                    res_note = "Low name similarity (<60%). Kept separate to prevent erroneous cross-station merge."
                    req_review = True
                else:
                    status = "AUTO_RESOLVED"
                    res_note = "Preserved secondary spelling/variant as searchable alias under canonical name."
                    req_review = False

                conflicts.append({
                    "conflict_id": f"CONF_{conflict_counter:04d}",
                    "entity_candidate": f"{name_a} <-> {name_b}",
                    "transport_mode": mode_a,
                    "conflict_field": "station_name",
                    "source_pair": src_pair,
                    "source_a": src_a,
                    "value_a": name_a,
                    "source_b": src_b,
                    "value_b": name_b,
                    "delta_metric": f"similarity={sim:.1f}%",
                    "resolution_status": status,
                    "resolution_action": res_note,
                    "requires_manual_review": req_review
                })
                conflict_counter += 1

    fieldnames = [
        "conflict_id", "entity_candidate", "transport_mode", "conflict_field",
        "source_pair", "source_a", "value_a", "source_b", "value_b",
        "delta_metric", "resolution_status", "resolution_action", "requires_manual_review"
    ]

    with open(CONFLICTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in conflicts:
            writer.writerow(c)

    # Compute aggregation counts
    status_counts = Counter(c["resolution_status"] for c in conflicts)
    field_counts = Counter(c["conflict_field"] for c in conflicts)
    mode_counts = Counter(c["transport_mode"] for c in conflicts)
    pair_counts = Counter(c["source_pair"] for c in conflicts)

    print(f"✅ Successfully detected {len(conflicts)} cross-source conflicts.")
    print(f"Status breakdown: {dict(status_counts)}")
    print(f"Conflict fields: {dict(field_counts)}")
    print(f"Transport modes: {dict(mode_counts)}")
    print(f"Source pairs: {dict(pair_counts)}")
    print(f"Saved to: {CONFLICTS_CSV}")


if __name__ == "__main__":
    detect_conflicts()
