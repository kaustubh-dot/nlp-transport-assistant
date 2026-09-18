#!/usr/bin/env python3
"""Acquires OpenStreetMap transit entities, boundary polygon, and POIs

for the Chennai Metropolitan Area and regional service corridors.
Preserves raw query payloads byte-for-byte in data/raw/osm/YYYY-MM-DD/ and
data/raw/government/YYYY-MM-DD/, calculating SHA-256 and updating manifest.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.acquire.common import register_raw_file, compute_sha256, logger

DATE_STR = datetime.now().strftime("%Y-%m-%d")
RAW_OSM_DIR = os.path.join(BASE_DIR, "data", "raw", "osm", DATE_STR)
RAW_GOV_DIR = os.path.join(BASE_DIR, "data", "raw", "government", DATE_STR)
os.makedirs(RAW_OSM_DIR, exist_ok=True)
os.makedirs(RAW_GOV_DIR, exist_ok=True)

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

# Regional bounds covering CMA and Chennai-serving suburban corridors
# (Chengalpattu, Arakkonam, Tiruvallur, Gummidipoondi)
BBOX = "12.5,79.7,13.5,80.4"


def query_overpass(query_str: str, max_retries: int = 3) -> bytes:
    """Executes Overpass query with mirror failover, rate limiting, and exponential backoff."""
    for attempt in range(max_retries):
        for mirror in OVERPASS_MIRRORS:
            try:
                time.sleep(3.0)  # Respect Overpass rate limits
                url = mirror + "?data=" + urllib.parse.quote(query_str)
                req = urllib.request.Request(url, headers={"User-Agent": "ChennaiTransitKnowledgeBase/1.0 (Research NLP Data)"})
                with urllib.request.urlopen(req, timeout=45) as resp:
                    payload = resp.read()
                    logger.info(f"Overpass query succeeded via {mirror} ({len(payload)} bytes)")
                    return payload
            except Exception as e:
                logger.warning(f"Overpass query attempt {attempt+1} failed on {mirror}: {e}")
                time.sleep(4.0 * (attempt + 1))

    raise RuntimeError("All Overpass mirrors failed after retries.")


def save_raw_osm(payload: bytes, target_path: str, file_id: str, source_id: str, notes: str):
    """Saves raw Overpass payload byte-for-byte and updates manifest."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "wb") as f:
        f.write(payload)

    file_size = len(payload)
    sha256 = compute_sha256(target_path)
    rel_path = os.path.relpath(target_path, BASE_DIR)

    register_raw_file(
        file_id=file_id,
        relative_path=rel_path,
        source_id=source_id,
        download_url="https://overpass-api.de/api/interpreter",
        retrieved_at=datetime.now().isoformat(),
        file_format="JSON",
        file_size=file_size,
        checksum_sha256=sha256,
        dataset_version="2026.09",
        license="ODbL",
        notes=notes
    )


def fetch_official_boundary():
    """Fetches official administrative boundary for Chennai (District & Corporation) from OSM."""
    logger.info("Fetching official administrative boundary for Chennai...")
    target_path = os.path.join(RAW_GOV_DIR, "chennai_administrative_boundary_osm.json")
    query = """
    [out:json][timeout:35];
    (
      relation(7910817);
      relation(1766358);
    );
    out geom;
    """
    payload = query_overpass(query)
    save_raw_osm(
        payload, target_path,
        file_id=f"OSM_CHENNAI_BOUNDARY_{DATE_STR.replace('-', '')}",
        source_id="OSM_OVERPASS",
        notes="Official administrative boundaries for Chennai District (7910817) and Corporation (1766358) with geometry."
    )


def fetch_rail_and_metro():
    """Fetches all operational and planned rail, metro, and MRTS stations."""
    logger.info("Fetching rail, metro, and MRTS stations from OpenStreetMap...")
    target_path = os.path.join(RAW_OSM_DIR, "osm_rail_and_metro_stations.json")
    query = f"""
    [out:json][timeout:40];
    (
      node["railway"="station"]({BBOX});
      way["railway"="station"]({BBOX});
      relation["railway"="station"]({BBOX});
      node["station"="subway"]({BBOX});
      way["station"="subway"]({BBOX});
      node["railway"="halt"]({BBOX});
      node["subway"="yes"]({BBOX});
    );
    out body geom;
    """
    payload = query_overpass(query)
    save_raw_osm(
        payload, target_path,
        file_id=f"OSM_RAIL_METRO_STATIONS_{DATE_STR.replace('-', '')}",
        source_id="OSM_OVERPASS",
        notes="All railway, metro, and MRTS stations and halts in Chennai region with tags and geometry."
    )


def fetch_bus_terminals_and_stops():
    """Fetches major bus stations, terminals, and stops."""
    logger.info("Fetching bus stations and major terminals from OpenStreetMap...")
    target_path = os.path.join(RAW_OSM_DIR, "osm_bus_stations_and_terminals.json")
    query = f"""
    [out:json][timeout:40];
    (
      node["amenity"="bus_station"]({BBOX});
      way["amenity"="bus_station"]({BBOX});
      node["public_transport"="station"]({BBOX});
      node["highway"="bus_stop"]["name"]({BBOX});
    );
    out body geom qt 5000;
    """
    payload = query_overpass(query)
    save_raw_osm(
        payload, target_path,
        file_id=f"OSM_BUS_TERMINALS_STOPS_{DATE_STR.replace('-', '')}",
        source_id="OSM_OVERPASS",
        notes="Bus stations, terminals, and named bus stops in Chennai region."
    )


def fetch_pois():
    """Fetches transport-relevant landmarks and POIs."""
    logger.info("Fetching transport-relevant POIs from OpenStreetMap...")
    target_path = os.path.join(RAW_OSM_DIR, "osm_transport_pois.json")
    query = f"""
    [out:json][timeout:45];
    (
      node["amenity"~"hospital|university|college"]({BBOX});
      way["amenity"~"hospital|university|college"]({BBOX});
      node["shop"~"mall"]({BBOX});
      way["shop"~"mall"]({BBOX});
      node["tourism"~"attraction"]({BBOX});
      node["natural"="beach"]({BBOX});
      node["leisure"~"stadium"]({BBOX});
      way["leisure"~"stadium"]({BBOX});
      node["aeroway"="aerodrome"]({BBOX});
      node["office"~"government|company"]({BBOX});
    );
    out body qt 4000;
    """
    payload = query_overpass(query)
    save_raw_osm(
        payload, target_path,
        file_id=f"OSM_TRANSPORT_POIS_{DATE_STR.replace('-', '')}",
        source_id="OSM_OVERPASS",
        notes="Transport-relevant POIs: hospitals, universities, colleges, malls, beaches, stadiums, aerodromes."
    )


def main():
    logger.info("Starting OpenStreetMap and Boundary Acquisition...")
    try:
        fetch_official_boundary()
    except Exception as e:
        logger.error(f"Boundary fetch failed: {e}")

    try:
        fetch_rail_and_metro()
    except Exception as e:
        logger.error(f"Rail/metro fetch failed: {e}")

    try:
        fetch_bus_terminals_and_stops()
    except Exception as e:
        logger.error(f"Bus terminals fetch failed: {e}")

    try:
        fetch_pois()
    except Exception as e:
        logger.error(f"POIs fetch failed: {e}")

    logger.info("OpenStreetMap acquisition stage complete.")


if __name__ == "__main__":
    main()
