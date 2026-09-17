#!/usr/bin/env python3
"""Scrapes official Chennai Metro Rail Limited (CMRL) station data.

Queries the CMRL WordPress REST API (https://chennaimetrorail.org/wp-json/wp/v2/station-information)
to extract all 43 stations, their line assignments, and detailed amenities/facilities.

Outputs:
  - data/curated/cmrl_scraped_stations.json
"""

import os
import re
import json
import urllib.request
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "curated", "cmrl_scraped_stations.json")
API_URL = "https://chennaimetrorail.org/wp-json/wp/v2/station-information?per_page=100"


def fetch_cmrl_stations() -> List[Dict[str, Any]]:
    print(f"Fetching station list from {API_URL}...")
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        stations = json.loads(resp.read().decode("utf-8"))

    print(f"Found {len(stations)} stations from CMRL official API.")
    scraped_data = []

    for s in stations:
        title = s.get("title", {}).get("rendered", "").replace("&#8217;", "'").replace("&#038;", "&")
        slug = s.get("slug", "")
        link = s.get("link", "")
        content = s.get("content", {}).get("rendered", "")

        # Extract line details
        phase_one = s.get("phase-one", [])
        phase_two = s.get("phase-two", [])

        # Parse facility keywords from HTML content
        facilities = []
        if re.search(r"wheelchair", content, re.I):
            facilities.append("wheelchair")
        if re.search(r"lift", content, re.I):
            facilities.append("lift")
        if re.search(r"escalator", content, re.I):
            facilities.append("escalator")
        if re.search(r"ramp", content, re.I):
            facilities.append("ramp")
        if re.search(r"toilet|washroom|restroom", content, re.I):
            facilities.append("accessible_toilet")
        if re.search(r"parking", content, re.I):
            facilities.append("parking")
        if re.search(r"interchange|junction", content, re.I):
            facilities.append("interchange")

        scraped_data.append({
            "id": s.get("id"),
            "name": title,
            "slug": slug,
            "url": link,
            "phase_one_ids": phase_one,
            "phase_two_ids": phase_two,
            "detected_facilities": facilities,
            "raw_html_snippet": content[:500] if content else ""
        })

    return scraped_data


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    stations = fetch_cmrl_stations()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"total_stations": len(stations), "stations": stations}, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {len(stations)} scraped CMRL stations to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
