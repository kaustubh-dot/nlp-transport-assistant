#!/usr/bin/env python3
"""Generates cross-source entity matching candidates based on geographic proximity,

normalized names, and transit modes.

Strictly preserves separation between distinct physical transport entities:
Guindy Metro, Guindy Railway, and Guindy Bus Terminus are flagged as 'same_hub'
candidates, NEVER merged as the same stop.

Outputs:
  data/staging/entity_match_candidates.csv
"""

import os
import sys
import csv
import math
from typing import List, Dict, Any
from rapidfuzz import fuzz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

STOPS_CSV = os.path.join(BASE_DIR, "data", "normalized", "stops", "normalized_stops.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "staging", "entity_match_candidates.csv")
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in meters."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999.0
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def find_matching_candidates():
    if not os.path.exists(STOPS_CSV):
        raise FileNotFoundError(f"Normalized stops file missing: {STOPS_CSV}")

    with open(STOPS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_stops = list(reader)

    # Filter to rail/metro and major bus terminals for cross-source comparison to avoid O(N^2) explosion
    priority_stops = [
        s for s in all_stops
        if s.get("mode") in ["metro", "suburban_rail", "mrts"] or s.get("stop_type") in ["metro_station", "railway_station", "mrts_station", "bus_terminal"]
    ]
    print(f"Analyzing cross-source matches among {len(priority_stops)} rail, metro, and terminal entities...")

    candidates = []
    seen_pairs = set()

    for i in range(len(priority_stops)):
        s1 = priority_stops[i]
        id1 = s1["normalized_id"]
        name1 = s1["normalized_name"].lower()
        mode1 = s1["mode"]
        src1 = s1["source_id"]
        try:
            lat1 = float(s1["normalized_latitude"])
            lon1 = float(s1["normalized_longitude"])
        except (ValueError, TypeError):
            continue

        for j in range(i + 1, len(priority_stops)):
            s2 = priority_stops[j]
            id2 = s2["normalized_id"]
            name2 = s2["normalized_name"].lower()
            mode2 = s2["mode"]
            src2 = s2["source_id"]

            # Don't match entity with itself
            if id1 == id2:
                continue

            try:
                lat2 = float(s2["normalized_latitude"])
                lon2 = float(s2["normalized_longitude"])
            except (ValueError, TypeError):
                continue

            # Quick spatial filter (approx 0.006 degrees ~ 650m)
            if abs(lat1 - lat2) > 0.006 or abs(lon1 - lon2) > 0.006:
                continue

            dist_m = haversine_distance_m(lat1, lon1, lat2, lon2)
            if dist_m > 600.0:
                continue

            pair_key = tuple(sorted([id1, id2]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Name similarity
            sim = fuzz.token_set_ratio(name1, name2)

            # Determine candidate relationship
            if mode1 == mode2:
                if dist_m <= 150.0 and sim >= 75:
                    rel = "same_station"
                    conf = 0.95
                    req_review = False
                    reason = f"Same mode ({mode1}), high name similarity ({sim}%), close proximity ({dist_m:.1f}m)."
                elif dist_m <= 300.0 and sim >= 60:
                    rel = "same_physical_entity"
                    conf = 0.80
                    req_review = True
                    reason = f"Same mode ({mode1}), moderate similarity ({sim}%), distance {dist_m:.1f}m."
                else:
                    rel = "nearby_only"
                    conf = 0.60
                    req_review = False
                    reason = f"Same mode ({mode1}), separate facilities or low similarity ({sim}%), distance {dist_m:.1f}m."
            else:
                # Cross-mode match (e.g. Metro vs Rail vs Bus)
                if sim >= 70 and dist_m <= 500.0:
                    rel = "same_hub"
                    conf = 0.90
                    req_review = True  # Hub creation requires domain review
                    reason = f"Different modes ({mode1} vs {mode2}), shared name root ({sim}%), multimodal interchange distance ({dist_m:.1f}m)."
                elif dist_m <= 250.0:
                    rel = "same_hub"
                    conf = 0.75
                    req_review = True
                    reason = f"Different modes ({mode1} vs {mode2}), close physical proximity ({dist_m:.1f}m)."
                else:
                    rel = "nearby_only"
                    conf = 0.50
                    req_review = False
                    reason = f"Different modes ({mode1} vs {mode2}), distance {dist_m:.1f}m."

            candidates.append({
                "record_a": id1,
                "record_b": id2,
                "source_a": src1,
                "source_b": src2,
                "name_similarity": sim,
                "distance_m": round(dist_m, 1),
                "mode_a": mode1,
                "mode_b": mode2,
                "candidate_relationship": rel,
                "confidence": conf,
                "requires_review": req_review,
                "reason": reason
            })

    # Sort candidates by confidence descending
    candidates.sort(key=lambda x: x["confidence"], reverse=True)

    fieldnames = [
        "record_a", "record_b", "source_a", "source_b",
        "name_similarity", "distance_m", "mode_a", "mode_b",
        "candidate_relationship", "confidence", "requires_review", "reason"
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in candidates:
            writer.writerow(c)

    print(f"✅ Successfully identified {len(candidates)} match candidates across sources.")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    find_matching_candidates()
