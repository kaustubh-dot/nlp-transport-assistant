#!/usr/bin/env python3
"""Normalizes geographic places, landmarks, and POIs from OpenStreetMap.

Categorizes entities into transport-relevant classes:
hospital, university, college, mall, beach, tourism, it_park, government, stadium, airport.
Computes inside_cma flag and preserves all multilingual tags.
"""

import os
import sys
import csv
import json
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATE_STR = datetime.now().strftime("%Y-%m-%d")
NORMALIZED_DIR = os.path.join(BASE_DIR, "data", "normalized", "places")
os.makedirs(NORMALIZED_DIR, exist_ok=True)

OUTPUT_CSV = os.path.join(NORMALIZED_DIR, "normalized_places.csv")
OUTPUT_JSON = os.path.join(NORMALIZED_DIR, "normalized_places.json")

CMA_LAT_MIN, CMA_LAT_MAX = 12.82, 13.28
CMA_LON_MIN, CMA_LON_MAX = 80.00, 80.35


def is_inside_cma(lat: float, lon: float) -> bool:
    if lat is None or lon is None:
        return False
    return (CMA_LAT_MIN <= lat <= CMA_LAT_MAX) and (CMA_LON_MIN <= lon <= CMA_LON_MAX)


def categorize_poi(tags: dict) -> str:
    amenity = tags.get("amenity", "")
    shop = tags.get("shop", "")
    tourism = tags.get("tourism", "")
    natural = tags.get("natural", "")
    leisure = tags.get("leisure", "")
    aeroway = tags.get("aeroway", "")
    office = tags.get("office", "")
    name = tags.get("name", "").lower()

    if aeroway in ["aerodrome", "terminal"] or "airport" in name:
        return "airport"
    if amenity == "hospital":
        return "hospital"
    if amenity == "university":
        return "university"
    if amenity in ["college", "school"]:
        return "college"
    if shop == "mall" or "mall" in name:
        return "mall"
    if natural == "beach" or "beach" in name:
        return "beach"
    if leisure in ["stadium", "sports_centre"] or "stadium" in name:
        return "stadium"
    if "tech park" in name or "it park" in name or "tidel" in name or "sipcot" in name:
        return "it_park"
    if office == "government" or "court" in name or "secretariat" in name:
        return "government_office"
    if tourism == "attraction" or "memorial" in name or "museum" in name:
        return "tourist_attraction"

    return "general_poi"


def normalize_all_places():
    osm_pois_path = os.path.join(BASE_DIR, "data", "raw", "osm", DATE_STR, "osm_transport_pois.json")
    if not os.path.exists(osm_pois_path):
        raise FileNotFoundError(f"OSM POI payload not found: {osm_pois_path}")

    with open(osm_pois_path, "r", encoding="utf-8") as f:
        osm_data = json.load(f)

    places = []
    seen_ids = set()

    for el in osm_data.get("elements", []):
        el_id = str(el.get("id"))
        if el_id in seen_ids:
            continue
        seen_ids.add(el_id)

        tags = el.get("tags", {})
        name = tags.get("name", tags.get("name:en", ""))
        if not name or len(name) < 2:
            continue

        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        category = categorize_poi(tags)
        in_cma = is_inside_cma(lat, lon)

        places.append({
            "place_id": f"OSM_POI_{el_id}",
            "source_id": "OSM_OVERPASS",
            "source_record_id": el_id,
            "raw_file_id": f"OSM_TRANSPORT_POIS_{DATE_STR.replace('-', '')}",
            "name": name,
            "name_en": tags.get("name:en", name),
            "name_ta": tags.get("name:ta", ""),
            "alt_name": tags.get("alt_name", ""),
            "category": category,
            "latitude": lat,
            "longitude": lon,
            "inside_cma": in_cma,
            "wheelchair": tags.get("wheelchair", "")
        })

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "normalized_date": DATE_STR,
                "total_places": len(places),
                "normalization_version": "1.0"
            },
            "places": places
        }, f, indent=2, ensure_ascii=False)

    fieldnames = [
        "place_id", "source_id", "source_record_id", "raw_file_id",
        "name", "name_en", "name_ta", "alt_name", "category",
        "latitude", "longitude", "inside_cma", "wheelchair"
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in places:
            writer.writerow(p)

    print(f"✅ Successfully normalized {len(places)} places & POIs. Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    normalize_all_places()
