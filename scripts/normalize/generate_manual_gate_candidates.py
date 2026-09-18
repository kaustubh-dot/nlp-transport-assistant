#!/usr/bin/env python3
"""Generates decoupled candidate datasets for human review and curation across manual gates:

1. Hub Candidates (data/manual/hubs/hub_candidates.csv)
   - Question: Do these separate physical transport entities belong to the same user-facing multimodal hub?
   - Prioritized into Tier 1 (Core Multimodal Hubs), Tier 2 (Secondary Hubs), Tier 3 (Local Nodes).

2. Interchange Candidates (data/manual/interchanges/interchange_candidates.csv)
   - Question: Is transferring between services actually supported and meaningful?
   - Retains confirmed = False until transfer feasibility is validated.

3. Walking Transfer Candidates (data/manual/walking_transfers/walking_candidates.csv)
   - Question: Is there a confirmed pedestrian path between physical access points?
   - Strictly sets walkable = 'unverified_walking_transfer' (not assumed from proximity).

4. Alias Candidates (data/manual/aliases/alias_candidates.csv)
5. Landmark Priority Candidates (data/manual/landmark_priority/landmark_candidates.csv)
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

# High-Value Priority Tiers for Multimodal Hubs
TIER_1_CORE_HUBS = {
    "CENTRAL": "Chennai Central / Puratchi Thalaivar Dr. M.G.R Hub (Metro + Suburban + Bus)",
    "EGMORE": "Chennai Egmore Hub (Metro + Suburban Rail + Bus)",
    "GUINDY": "Guindy Multimodal Hub (Metro + Suburban Rail + Bus Terminus)",
    "ST_THOMAS_MOUNT": "St. Thomas Mount Multimodal Interchange (Metro Line 1/2 + Suburban + MRTS)",
    "AIRPORT": "Chennai International Airport / Tirusulam Hub (Metro + Suburban + Airport)",
    "TAMBARAM": "Tambaram Multimodal Transport Terminal (Suburban Rail + MTC Bus)",
    "CMBT": "CMBT Koyambedu Intercity & Metro Transit Hub (Metro + Intercity Bus)",
    "CHENNAI_BEACH": "Chennai Beach Northern Terminal Hub (Suburban + MRTS + MTC Bus)",
    "VELACHERY": "Velachery Terminal Hub (MRTS + MTC Bus Terminus)",
    "ALANDUR": "Alandur Metro Dual-Corridor Junction (Blue Line + Green Line)"
}

TIER_2_SECONDARY_HUBS = {
    "PERAMBUR", "AVADI", "THIRUVANMIYUR", "BROADWAY", "ADYAR",
    "KILAMBAKKAM", "MADHAVARAM", "RED_HILLS", "POONAMALLEE", "T_NAGAR"
}


def get_priority_tier(hub_root: str) -> str:
    clean = re.sub(r"[^A-Z0-9]", "_", hub_root.upper()).strip("_")
    for k in TIER_1_CORE_HUBS:
        if k in clean or clean in k:
            return "TIER_1_CORE"
    for k in TIER_2_SECONDARY_HUBS:
        if k in clean or clean in k:
            return "TIER_2_SECONDARY"
    return "TIER_3_LOCAL"


def generate_candidates():
    # Load normalized stops lookup
    stops_by_id = {}
    with open(STOPS_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stops_by_id[row["normalized_id"]] = row

    hub_candidates = []
    interchange_candidates = []
    walking_candidates = []

    seen_hub_pairs = set()
    seen_int_pairs = set()
    seen_walk_pairs = set()

    with open(CANDIDATES_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
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
            sim = float(row.get("name_similarity", 0))

            # --- 1. HUB CANDIDATES ---
            # Question: Do these separate physical transport entities belong to the same multimodal hub?
            # Evaluated for cross-mode pairs within 450m or same_hub flag
            if mode_a != mode_b and (dist_m <= 450.0 or row.get("candidate_relationship") == "same_hub"):
                hub_root = re.sub(r"(?i)\s+(metro|railway|station|bus|terminus|depot|r\.s\.).*", "", name_a).strip()
                if not hub_root:
                    hub_root = name_a[:12]
                hub_id = f"HUB_{re.sub(r'[^A-Z0-9]', '_', hub_root.upper())}"
                tier = get_priority_tier(hub_root)

                hub_key = (hub_id, id_a, id_b)
                if hub_key not in seen_hub_pairs:
                    seen_hub_pairs.add(hub_key)
                    hub_candidates.append({
                        "hub_id": hub_id,
                        "hub_name": hub_root,
                        "priority_tier": tier,
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
                        "notes": f"Cross-mode candidate in {tier}: {mode_a} <-> {mode_b} at {dist_m:.1f}m."
                    })

            # --- 2. INTERCHANGE CANDIDATES ---
            # Question: Is transferring between services actually supported/meaningful?
            # Evaluated strictly for passenger connections where distance <= 250m
            if mode_a != mode_b and dist_m <= 250.0 and sim >= 65:
                int_key = tuple(sorted([id_a, id_b]))
                if int_key not in seen_int_pairs:
                    seen_int_pairs.add(int_key)
                    hub_root = re.sub(r"(?i)\s+(metro|railway|station|bus|terminus|depot|r\.s\.).*", "", name_a).strip()
                    tier = get_priority_tier(hub_root)
                    transfer_type = (
                        "direct_facility_interchange" if dist_m <= 30.0
                        else ("short_corridor_transfer" if dist_m <= 100.0 else "street_transfer")
                    )
                    interchange_candidates.append({
                        "interchange_id": f"INT_{id_a[:12]}_{id_b[:12]}",
                        "from_entity": id_a,
                        "from_name": name_a,
                        "to_entity": id_b,
                        "to_name": name_b,
                        "priority_tier": tier,
                        "transfer_type": transfer_type,
                        "walking_distance_m": dist_m,
                        "walking_time_min": round(dist_m / 75.0, 1),
                        "confirmed": False,
                        "notes": f"Multimodal transfer candidate ({transfer_type}) requiring validation."
                    })

            # --- 3. WALKING TRANSFER CANDIDATES ---
            # Question: Is there a confirmed pedestrian path between physical access points?
            # Evaluated for pairs <= 350m, strictly marked unverified_walking_transfer
            if mode_a != mode_b and dist_m <= 350.0:
                walk_key = tuple(sorted([id_a, id_b]))
                if walk_key not in seen_walk_pairs:
                    seen_walk_pairs.add(walk_key)
                    # Obstacle check heuristics
                    obstacles = []
                    if "rail" in mode_a or "rail" in mode_b:
                        obstacles.append("potential railway track crossing")
                    if dist_m > 150.0:
                        obstacles.append("arterial road / median barrier check needed")
                    obstacle_text = "; ".join(obstacles) if obstacles else "direct sidewalk verification needed"

                    walking_candidates.append({
                        "from_entity": id_a,
                        "from_name": name_a,
                        "to_entity": id_b,
                        "to_name": name_b,
                        "straight_line_distance_m": dist_m,
                        "walkable": "unverified_walking_transfer",
                        "estimated_walking_time_min": round(dist_m / 75.0, 1),
                        "obstacle_notes": obstacle_text,
                        "requires_human_confirmation": True
                    })

    # Sort Hub Candidates by Priority Tier (Tier 1 Core first)
    tier_order = {"TIER_1_CORE": 0, "TIER_2_SECONDARY": 1, "TIER_3_LOCAL": 2}
    hub_candidates.sort(key=lambda x: (tier_order.get(x["priority_tier"], 3), x["hub_name"]))
    interchange_candidates.sort(key=lambda x: (tier_order.get(x["priority_tier"], 3), x["walking_distance_m"]))
    walking_candidates.sort(key=lambda x: x["straight_line_distance_m"])

    # Write Hub Candidates
    hub_file = os.path.join(MANUAL_DIR, "hubs", "hub_candidates.csv")
    with open(hub_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hub_id", "hub_name", "priority_tier", "member_entity_id", "member_name",
            "member_mode", "paired_entity_id", "paired_name", "paired_mode",
            "walking_distance_m", "confidence", "requires_review", "verified", "notes"
        ])
        writer.writeheader()
        for h in hub_candidates:
            writer.writerow(h)
    print(f"✅ Generated {len(hub_candidates)} decoupled hub candidates (Tier 1: {sum(1 for h in hub_candidates if h['priority_tier'] == 'TIER_1_CORE')}) -> {hub_file}")

    # Write Interchange Candidates
    int_file = os.path.join(MANUAL_DIR, "interchanges", "interchange_candidates.csv")
    with open(int_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "interchange_id", "from_entity", "from_name", "to_entity", "to_name",
            "priority_tier", "transfer_type", "walking_distance_m", "walking_time_min",
            "confirmed", "notes"
        ])
        writer.writeheader()
        for ic in interchange_candidates:
            writer.writerow(ic)
    print(f"✅ Generated {len(interchange_candidates)} decoupled interchange candidates -> {int_file}")

    # Write Walking Candidates
    walk_file = os.path.join(MANUAL_DIR, "walking_transfers", "walking_candidates.csv")
    with open(walk_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "from_entity", "from_name", "to_entity", "to_name", "straight_line_distance_m",
            "walkable", "estimated_walking_time_min", "obstacle_notes", "requires_human_confirmation"
        ])
        writer.writeheader()
        for wc in walking_candidates:
            writer.writerow(wc)
    print(f"✅ Generated {len(walking_candidates)} decoupled walking candidates -> {walk_file}")

    # 4. Generate Alias Candidates
    alias_candidates = []
    seen_aliases = set()
    for sid, s in stops_by_id.items():
        norm_name = s["normalized_name"]
        name_ta = s["name_ta"]
        orig_name = s["original_name"]

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

    # 5. Generate Landmark Priority Candidates
    landmark_candidates = []
    if os.path.exists(PLACES_CSV):
        with open(PLACES_CSV, "r", encoding="utf-8") as f:
            for p in csv.DictReader(f):
                cat = p["category"]
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
