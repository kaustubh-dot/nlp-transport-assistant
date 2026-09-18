#!/usr/bin/env python3
"""Generates candidate datasets for human review and curation across the 5 manual gates:

1. Hub Candidates (data/manual/hubs/hub_candidates.csv)
2. Interchange Candidates (data/manual/interchanges/interchange_candidates.csv)
3. Walking Transfer Candidates (data/manual/walking_transfers/walking_candidates.csv)
4. Alias Candidates (data/manual/aliases/alias_candidates.csv)
5. Landmark Priority Candidates (data/manual/landmark_priority/landmark_candidates.csv)

Follows Hard Stop Protocol Type C (Section 47, 49, 51, 53, 55).
"""

import os
import sys
import csv
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CANDIDATES_CSV = os.path.join(BASE_DIR, "data", "staging", "entity_match_candidates.csv")
STOPS_CSV = os.path.join(BASE_DIR, "data", "normalized", "stops", "normalized_stops.csv")
PLACES_CSV = os.path.join(BASE_DIR, "data", "normalized", "places", "normalized_places.csv")

MANUAL_DIR = os.path.join(BASE_DIR, "data", "manual")
os.makedirs(os.path.join(MANUAL_DIR, "hubs"), exist_ok=True)
os.makedirs(os.path.join(MANUAL_DIR, "interchanges"), exist_ok=True)
os.makedirs(os.path.join(MANUAL_DIR, "walking_transfers"), exist_ok=True)
os.makedirs(os.path.join(MANUAL_DIR, "aliases"), exist_ok=True)
os.makedirs(os.path.join(MANUAL_DIR, "landmark_priority"), exist_ok=True)


def generate_candidates():
    # Load normalized stops
    stops_by_id = {}
    with open(STOPS_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stops_by_id[row["normalized_id"]] = row

    # 1. Generate Hub Candidates & Interchange Candidates & Walking Candidates
    hub_candidates = []
    interchange_candidates = []
    walking_candidates = []

    seen_hub_pairs = set()

    with open(CANDIDATES_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rel = row.get("candidate_relationship")
            dist_m = float(row.get("distance_m", 999))
            id_a = row.get("record_a")
            id_b = row.get("record_b")

            stop_a = stops_by_id.get(id_a)
            stop_b = stops_by_id.get(id_b)
            if not stop_a or not stop_b:
                continue

            name_a = stop_a["normalized_name"]
            name_b = stop_b["normalized_name"]
            mode_a = stop_a["mode"]
            mode_b = stop_b["mode"]

            if rel == "same_hub" or (mode_a != mode_b and dist_m <= 450.0):
                # Proposed hub name
                hub_root = re.sub(r"(?i)\s+(metro|railway|station|bus|terminus|depot|r\.s\.).*", "", name_a).strip()
                hub_id = f"HUB_{re.sub(r'[^A-Z0-9]', '_', hub_root.upper())}"

                hub_candidates.append({
                    "hub_id": hub_id,
                    "hub_name": hub_root,
                    "member_entity_id": id_a,
                    "member_name": name_a,
                    "member_mode": mode_a,
                    "paired_entity_id": id_b,
                    "paired_name": name_b,
                    "paired_mode": mode_b,
                    "walking_distance_m": dist_m,
                    "confidence": row.get("confidence"),
                    "requires_review": True,
                    "verified": False,
                    "notes": f"Cross-mode candidate: {mode_a} <-> {mode_b} at {dist_m:.1f}m."
                })

                # Interchange candidate
                interchange_candidates.append({
                    "interchange_id": f"INT_{id_a[:12]}_{id_b[:12]}",
                    "from_entity": id_a,
                    "from_name": name_a,
                    "to_entity": id_b,
                    "to_name": name_b,
                    "transfer_type": "walking_interchange" if dist_m > 30 else "integrated_interchange",
                    "walking_distance_m": dist_m,
                    "walking_time_min": round(dist_m / 75.0, 1),  # ~4.5 km/h walking speed
                    "confirmed": False,
                    "notes": f"Multimodal candidate between {mode_a} and {mode_b}."
                })

                # Walking candidate
                walking_candidates.append({
                    "from_entity": id_a,
                    "from_name": name_a,
                    "to_entity": id_b,
                    "to_name": name_b,
                    "straight_line_distance_m": dist_m,
                    "walkable": "unverified_walking_transfer",
                    "estimated_walking_time_min": round(dist_m / 75.0, 1),
                    "obstacle_notes": "Straight line distance; requires pedestrian network check for tracks/highways/walls.",
                    "requires_human_confirmation": True
                })

    # Save Hub Candidates
    hub_file = os.path.join(MANUAL_DIR, "hubs", "hub_candidates.csv")
    with open(hub_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hub_id", "hub_name", "member_entity_id", "member_name", "member_mode",
            "paired_entity_id", "paired_name", "paired_mode", "walking_distance_m",
            "confidence", "requires_review", "verified", "notes"
        ])
        writer.writeheader()
        for h in hub_candidates:
            writer.writerow(h)
    print(f"✅ Generated {len(hub_candidates)} hub candidates -> {hub_file}")

    # Save Interchange Candidates
    int_file = os.path.join(MANUAL_DIR, "interchanges", "interchange_candidates.csv")
    with open(int_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "interchange_id", "from_entity", "from_name", "to_entity", "to_name",
            "transfer_type", "walking_distance_m", "walking_time_min", "confirmed", "notes"
        ])
        writer.writeheader()
        for ic in interchange_candidates:
            writer.writerow(ic)
    print(f"✅ Generated {len(interchange_candidates)} interchange candidates -> {int_file}")

    # Save Walking Candidates
    walk_file = os.path.join(MANUAL_DIR, "walking_transfers", "walking_candidates.csv")
    with open(walk_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "from_entity", "from_name", "to_entity", "to_name", "straight_line_distance_m",
            "walkable", "estimated_walking_time_min", "obstacle_notes", "requires_human_confirmation"
        ])
        writer.writeheader()
        for wc in walking_candidates:
            writer.writerow(wc)
    print(f"✅ Generated {len(walking_candidates)} walking candidates -> {walk_file}")

    # 2. Generate Alias Candidates
    alias_candidates = []
    seen_aliases = set()
    for sid, s in stops_by_id.items():
        norm_name = s["normalized_name"]
        name_ta = s["name_ta"]
        orig_name = s["original_name"]

        # If name has Tamil script, record as Tamil candidate alias
        if name_ta and (sid, name_ta) not in seen_aliases:
            alias_candidates.append({
                "entity_id": sid,
                "canonical_name": norm_name,
                "candidate_alias": name_ta,
                "candidate_type": "official_tamil",
                "language": "ta",
                "source_if_any": s["source_id"],
                "requires_human_confirmation": False
            })
            seen_aliases.add((sid, name_ta))

        # Check for abbreviation or alternate form in original name
        if orig_name != norm_name and (sid, orig_name) not in seen_aliases:
            alias_candidates.append({
                "entity_id": sid,
                "canonical_name": norm_name,
                "candidate_alias": orig_name,
                "candidate_type": "source_spelling",
                "language": "en",
                "source_if_any": s["source_id"],
                "requires_human_confirmation": False
            })
            seen_aliases.add((sid, orig_name))

    alias_file = os.path.join(MANUAL_DIR, "aliases", "alias_candidates.csv")
    with open(alias_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "entity_id", "canonical_name", "candidate_alias", "candidate_type",
            "language", "source_if_any", "requires_human_confirmation"
        ])
        writer.writeheader()
        for ac in alias_candidates:
            writer.writerow(ac)
    print(f"✅ Generated {len(alias_candidates)} alias candidates -> {alias_file}")

    # 3. Generate Landmark Priority Candidates
    landmark_candidates = []
    if os.path.exists(PLACES_CSV):
        with open(PLACES_CSV, "r", encoding="utf-8") as f:
            for p in csv.DictReader(f):
                cat = p["category"]
                # Default priority based on objective category
                if cat in ["airport", "stadium", "beach", "it_park", "mall"]:
                    priority = "HIGH"
                elif cat in ["hospital", "university", "college", "government_office"]:
                    priority = "MEDIUM"
                else:
                    priority = "LOW"

                landmark_candidates.append({
                    "place_id": p["place_id"],
                    "canonical_name": p["name"],
                    "category": cat,
                    "inside_cma": p["inside_cma"],
                    "proposed_priority": priority,
                    "include_in_nlp": True if priority in ["HIGH", "MEDIUM"] else False,
                    "requires_review": True,
                    "notes": f"OSM surveyed {cat}."
                })

    lm_file = os.path.join(MANUAL_DIR, "landmark_priority", "landmark_candidates.csv")
    with open(lm_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "place_id", "canonical_name", "category", "inside_cma",
            "proposed_priority", "include_in_nlp", "requires_review", "notes"
        ])
        writer.writeheader()
        for lm in landmark_candidates:
            writer.writerow(lm)
    print(f"✅ Generated {len(landmark_candidates)} landmark priority candidates -> {lm_file}")


if __name__ == "__main__":
    generate_candidates()
