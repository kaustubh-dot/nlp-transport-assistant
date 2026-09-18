#!/usr/bin/env python3
"""Acquires live official CMRL WordPress REST API station data,

preserves the verbatim JSON payload in data/raw/cmrl/YYYY-MM-DD/,
and parses detailed facilities, line assignments, and map coordinates
into data/staging/cmrl/YYYY-MM-DD/.
"""

import os
import sys
import re
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.acquire.common import download_file_byte_for_byte, logger

DATE_STR = datetime.now().strftime("%Y-%m-%d")
RAW_CMRL_DIR = os.path.join(BASE_DIR, "data", "raw", "cmrl", DATE_STR)
STAGING_CMRL_DIR = os.path.join(BASE_DIR, "data", "staging", "cmrl", DATE_STR)

API_URL = "https://chennaimetrorail.org/wp-json/wp/v2/station-information?per_page=100"
RAW_FILE_PATH = os.path.join(RAW_CMRL_DIR, "cmrl_station_information_api.json")
PARSED_FILE_PATH = os.path.join(STAGING_CMRL_DIR, "cmrl_parsed_stations.json")


def acquire_cmrl_data():
    os.makedirs(RAW_CMRL_DIR, exist_ok=True)
    os.makedirs(STAGING_CMRL_DIR, exist_ok=True)

    logger.info(f"Acquiring official CMRL REST API payload from: {API_URL}")
    success = download_file_byte_for_byte(
        url=API_URL,
        target_path=RAW_FILE_PATH,
        source_id="CMRL_API",
        file_id=f"CMRL_WP_API_{DATE_STR.replace('-', '')}",
        file_format="JSON",
        dataset_version="2026.09",
        license="REVIEW_REQUIRED",
        notes="Official CMRL WordPress REST API containing 43 operational station disclosures and facilities."
    )

    if not success:
        logger.error("Failed to acquire CMRL raw API data.")
        return False

    with open(RAW_FILE_PATH, "r", encoding="utf-8") as f:
        stations_raw = json.load(f)

    logger.info(f"Parsing {len(stations_raw)} CMRL raw station records into staging...")
    parsed_stations = []

    for s in stations_raw:
        title = s.get("title", {}).get("rendered", "").replace("&#8217;", "'").replace("&#038;", "&")
        slug = s.get("slug", "")
        link = s.get("link", "")
        content = s.get("content", {}).get("rendered", "")

        # Extract line details
        phase_one = s.get("phase-one", [])
        phase_two = s.get("phase-two", [])

        # Extract embedded lat/lon from Google Maps iframes if present
        lat, lon = None, None
        # Pattern 1: !3d13.0806509!4d80.2725935 or !2d80.2725935!3d13.0806509
        match_3d_2d = re.search(r"!2d([0-9\.]+)!3d([0-9\.]+)", content)
        if match_3d_2d:
            lon = float(match_3d_2d.group(1))
            lat = float(match_3d_2d.group(2))
        else:
            match_3d_4d = re.search(r"!3d([0-9\.]+)!4d([0-9\.]+)", content)
            if match_3d_4d:
                lat = float(match_3d_4d.group(1))
                lon = float(match_3d_4d.group(2))

        # Detect facility attributes from content
        facilities = {
            "wheelchair_available": 1 if re.search(r"wheelchair", content, re.I) else None,
            "lift_available": 1 if re.search(r"lift", content, re.I) else None,
            "escalator_available": 1 if re.search(r"escalator", content, re.I) else None,
            "ramp_available": 1 if re.search(r"ramp", content, re.I) else None,
            "accessible_toilet": 1 if re.search(r"toilet|washroom|restroom", content, re.I) else None,
            "parking_available": 1 if re.search(r"parking", content, re.I) else None,
            "interchange": 1 if re.search(r"interchange|junction", content, re.I) else 0
        }

        parsed_stations.append({
            "source_id": "CMRL_API",
            "source_record_id": str(s.get("id")),
            "official_name": title,
            "slug": slug,
            "url": link,
            "phase_one_ids": phase_one,
            "phase_two_ids": phase_two,
            "latitude": lat,
            "longitude": lon,
            "facilities": facilities,
            "retrieved_at": datetime.now().isoformat()
        })

    with open(PARSED_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "source_id": "CMRL_API",
                "source_url": API_URL,
                "parsed_date": DATE_STR,
                "total_stations": len(parsed_stations)
            },
            "stations": parsed_stations
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully staged {len(parsed_stations)} parsed CMRL stations to {PARSED_FILE_PATH}")
    return True


if __name__ == "__main__":
    acquire_cmrl_data()
