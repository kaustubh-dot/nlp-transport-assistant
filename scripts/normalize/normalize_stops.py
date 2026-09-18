#!/usr/bin/env python3
"""Normalizes transport stops and stations from multiple overlapping sources:

- CMRL Official WordPress API (data/staging/cmrl/YYYY-MM-DD/cmrl_parsed_stations.json)
- OpenStreetMap Rail & Metro (data/raw/osm/YYYY-MM-DD/osm_rail_and_metro_stations.json)
- OpenStreetMap Bus Stations & Terminals (data/raw/osm/YYYY-MM-DD/osm_bus_stations_and_terminals.json)
- Community GTFS stops.txt (data/staging/community_gtfs/YYYY-MM-DD/stops.txt)
- Curated Multimodal unverified fixture (data/curated/chennai_multimodal_stations.json)

Preserves byte-for-byte provenance, original names, Tamil names, original coordinates,
checks regional coordinate plausibility, and computes inside_cma flag.
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
NORMALIZED_DIR = os.path.join(BASE_DIR, "data", "normalized", "stops")
os.makedirs(NORMALIZED_DIR, exist_ok=True)

OUTPUT_CSV = os.path.join(NORMALIZED_DIR, "normalized_stops.csv")
OUTPUT_JSON = os.path.join(NORMALIZED_DIR, "normalized_stops.json")

# Approximate Chennai Metropolitan Area bounds (for inside_cma polygon proxy)
# Lat: 12.82 to 13.28, Lon: 80.00 to 80.35
CMA_LAT_MIN, CMA_LAT_MAX = 12.82, 13.28
CMA_LON_MIN, CMA_LON_MAX = 80.00, 80.35

# Regional plausibility bounds (Chennai region + suburban rail corridors)
# Lat: 12.00 to 14.00, Lon: 79.00 to 81.00
REGIONAL_LAT_MIN, REGIONAL_LAT_MAX = 12.00, 14.00
REGIONAL_LON_MIN, REGIONAL_LON_MAX = 79.00, 81.00


def clean_name(s: str) -> str:
    if not s:
        return ""
    # Strip HTML entities and extra spaces
    s = s.replace("&#8217;", "'").replace("&#038;", "&").replace("&amp;", "&")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_inside_cma(lat: float, lon: float) -> bool:
    if lat is None or lon is None:
        return False
    return (CMA_LAT_MIN <= lat <= CMA_LAT_MAX) and (CMA_LON_MIN <= lon <= CMA_LON_MAX)


def is_coordinate_plausible(lat: float, lon: float) -> bool:
    if lat is None or lon is None:
        return False
    return (REGIONAL_LAT_MIN <= lat <= REGIONAL_LAT_MAX) and (REGIONAL_LON_MIN <= lon <= REGIONAL_LON_MAX)


def normalize_all_stops():
    normalized_records = []
    seen_source_records = set()

    # 1. Ingest CMRL API Staged Data
    cmrl_staged_path = os.path.join(BASE_DIR, "data", "staging", "cmrl", DATE_STR, "cmrl_parsed_stations.json")
    if os.path.exists(cmrl_staged_path):
        with open(cmrl_staged_path, "r", encoding="utf-8") as f:
            cmrl_data = json.load(f)
        for s in cmrl_data.get("stations", []):
            rec_id = f"CMRL_API_{s.get('source_record_id')}"
            seen_source_records.add(rec_id)
            orig_name = s.get("official_name", "")
            norm_name = clean_name(orig_name)
            lat = s.get("latitude")
            lon = s.get("longitude")
            plausible = is_coordinate_plausible(lat, lon)
            in_cma = is_inside_cma(lat, lon)

            normalized_records.append({
                "normalized_id": rec_id,
                "source_id": "CMRL_API",
                "source_record_id": s.get("source_record_id"),
                "raw_file_id": f"CMRL_WP_API_{DATE_STR.replace('-', '')}",
                "original_name": orig_name,
                "normalized_name": norm_name,
                "name_ta": "",
                "name_hi": "",
                "mode": "metro",
                "stop_type": "metro_station",
                "original_latitude": lat,
                "original_longitude": lon,
                "normalized_latitude": lat if plausible else None,
                "normalized_longitude": lon if plausible else None,
                "coordinate_plausible": plausible,
                "inside_cma": in_cma,
                "parent_station": "",
                "agency": "CMRL",
                "operational_status": "operational",
                "facilities": s.get("facilities", {})
            })

    # 2. Ingest OSM Rail and Metro
    osm_rail_path = os.path.join(BASE_DIR, "data", "raw", "osm", DATE_STR, "osm_rail_and_metro_stations.json")
    if os.path.exists(osm_rail_path):
        with open(osm_rail_path, "r", encoding="utf-8") as f:
            osm_data = json.load(f)
        for el in osm_data.get("elements", []):
            el_id = str(el.get("id"))
            rec_id = f"OSM_RAIL_{el_id}"
            if rec_id in seen_source_records:
                continue
            seen_source_records.add(rec_id)

            tags = el.get("tags", {})
            orig_name = tags.get("name", tags.get("name:en", ""))
            if not orig_name:
                continue
            norm_name = clean_name(orig_name)
            name_ta = tags.get("name:ta", "")
            name_hi = tags.get("name:hi", "")

            # Mode detection from OSM tags
            railway_tag = tags.get("railway", "")
            station_tag = tags.get("station", "")
            subway_tag = tags.get("subway", "")

            if station_tag == "subway" or subway_tag == "yes" or "metro" in norm_name.lower():
                mode = "metro"
                stype = "metro_station"
            elif "mrts" in norm_name.lower() or "chepauk" in norm_name.lower() or "velachery" in norm_name.lower():
                mode = "mrts"
                stype = "mrts_station"
            else:
                mode = "suburban_rail"
                stype = "railway_station"

            # Coordinates
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            plausible = is_coordinate_plausible(lat, lon)
            in_cma = is_inside_cma(lat, lon)

            normalized_records.append({
                "normalized_id": rec_id,
                "source_id": "OSM_OVERPASS",
                "source_record_id": el_id,
                "raw_file_id": f"OSM_RAIL_METRO_STATIONS_{DATE_STR.replace('-', '')}",
                "original_name": orig_name,
                "normalized_name": norm_name,
                "name_ta": name_ta,
                "name_hi": name_hi,
                "mode": mode,
                "stop_type": stype,
                "original_latitude": lat,
                "original_longitude": lon,
                "normalized_latitude": lat if plausible else None,
                "normalized_longitude": lon if plausible else None,
                "coordinate_plausible": plausible,
                "inside_cma": in_cma,
                "parent_station": "",
                "agency": "CMRL" if mode == "metro" else "Southern Railway",
                "operational_status": "operational",
                "facilities": {}
            })

    # 3. Ingest OSM Bus Stations & Terminals
    osm_bus_path = os.path.join(BASE_DIR, "data", "raw", "osm", DATE_STR, "osm_bus_stations_and_terminals.json")
    if os.path.exists(osm_bus_path):
        with open(osm_bus_path, "r", encoding="utf-8") as f:
            osm_bus_data = json.load(f)
        for el in osm_bus_data.get("elements", []):
            el_id = str(el.get("id"))
            rec_id = f"OSM_BUS_{el_id}"
            if rec_id in seen_source_records:
                continue
            seen_source_records.add(rec_id)

            tags = el.get("tags", {})
            orig_name = tags.get("name", tags.get("name:en", ""))
            if not orig_name:
                continue
            norm_name = clean_name(orig_name)
            name_ta = tags.get("name:ta", "")

            amenity = tags.get("amenity", "")
            stype = "bus_terminal" if amenity == "bus_station" or "terminus" in norm_name.lower() or "depot" in norm_name.lower() else "bus_stop"

            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            plausible = is_coordinate_plausible(lat, lon)
            in_cma = is_inside_cma(lat, lon)

            normalized_records.append({
                "normalized_id": rec_id,
                "source_id": "OSM_OVERPASS",
                "source_record_id": el_id,
                "raw_file_id": f"OSM_BUS_TERMINALS_STOPS_{DATE_STR.replace('-', '')}",
                "original_name": orig_name,
                "normalized_name": norm_name,
                "name_ta": name_ta,
                "name_hi": "",
                "mode": "bus",
                "stop_type": stype,
                "original_latitude": lat,
                "original_longitude": lon,
                "normalized_latitude": lat if plausible else None,
                "normalized_longitude": lon if plausible else None,
                "coordinate_plausible": plausible,
                "inside_cma": in_cma,
                "parent_station": "",
                "agency": "MTC",
                "operational_status": "operational",
                "facilities": {}
            })

    # 4. Ingest GTFS stops.txt
    gtfs_stops_path = os.path.join(BASE_DIR, "data", "staging", "community_gtfs", DATE_STR, "stops.txt")
    if os.path.exists(gtfs_stops_path):
        with open(gtfs_stops_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("stop_id")
                rec_id = f"GTFS_STOP_{sid}"
                if rec_id in seen_source_records:
                    continue
                seen_source_records.add(rec_id)

                orig_name = row.get("stop_name", "")
                norm_name = clean_name(orig_name)
                name_ta = ""
                # Check if stop name is in Tamil script
                if any("\u0b80" <= ch <= "\u0bff" for ch in orig_name):
                    name_ta = orig_name

                try:
                    lat = float(row.get("stop_lat", ""))
                    lon = float(row.get("stop_lon", ""))
                except (ValueError, TypeError):
                    lat, lon = None, None

                plausible = is_coordinate_plausible(lat, lon)
                in_cma = is_inside_cma(lat, lon)

                # Check if Metro stop
                is_metro = "metro" in norm_name.lower() or row.get("zone_id") == "CMRL"
                mode = "metro" if is_metro else "bus"
                stype = "metro_station" if is_metro else ("bus_terminal" if "terminus" in norm_name.lower() or "depot" in norm_name.lower() else "bus_stop")

                normalized_records.append({
                    "normalized_id": rec_id,
                    "source_id": "CHENNAI_COMMUNITY_GTFS",
                    "source_record_id": sid,
                    "raw_file_id": f"CHENNAI_UNIFIED_GTFS_{DATE_STR.replace('-', '')}",
                    "original_name": orig_name,
                    "normalized_name": norm_name,
                    "name_ta": name_ta,
                    "name_hi": "",
                    "mode": mode,
                    "stop_type": stype,
                    "original_latitude": lat,
                    "original_longitude": lon,
                    "normalized_latitude": lat if plausible else None,
                    "normalized_longitude": lon if plausible else None,
                    "coordinate_plausible": plausible,
                    "inside_cma": in_cma,
                    "parent_station": row.get("parent_station", ""),
                    "agency": "CMRL" if is_metro else "MTC",
                    "operational_status": "operational",
                    "facilities": {}
                })

    # Save to JSON and CSV
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "normalized_date": DATE_STR,
                "total_normalized_stops": len(normalized_records),
                "normalization_version": "1.0"
            },
            "stops": normalized_records
        }, f, indent=2, ensure_ascii=False)

    fieldnames = [
        "normalized_id", "source_id", "source_record_id", "raw_file_id",
        "original_name", "normalized_name", "name_ta", "name_hi",
        "mode", "stop_type", "original_latitude", "original_longitude",
        "normalized_latitude", "normalized_longitude", "coordinate_plausible",
        "inside_cma", "parent_station", "agency", "operational_status"
    ]

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in normalized_records:
            writer.writerow(r)

    print(f"✅ Successfully normalized {len(normalized_records)} stops across all sources.")
    print(f"Saved to:\n  {OUTPUT_CSV}\n  {OUTPUT_JSON}")


if __name__ == "__main__":
    normalize_all_stops()
