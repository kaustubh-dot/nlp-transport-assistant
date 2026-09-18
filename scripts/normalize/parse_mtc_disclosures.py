#!/usr/bin/env python3
"""Parses official MTC Bronze HTML files into normalized Silver datasets:
  - data/normalized/fares/normalized_mtc_fares.csv / .json
  - data/normalized/stages/normalized_mtc_stages.csv / .json
  - data/normalized/routes/normalized_official_routes.csv / .json
and computes cross-references against Community GTFS transit entities.
"""

import os
import sys
import re
import csv
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

RAW_MTC_DIR = os.path.join(BASE_DIR, "data", "raw", "mtc", "2026-09-18")
ROUTES_HTML = os.path.join(RAW_MTC_DIR, "mtc_official_routes.html")
STAGES_HTML = os.path.join(RAW_MTC_DIR, "mtc_official_stages.html")
FARES_HTML = os.path.join(RAW_MTC_DIR, "mtc_official_fares.html")

NORM_FARES_DIR = os.path.join(BASE_DIR, "data", "normalized", "fares")
NORM_STAGES_DIR = os.path.join(BASE_DIR, "data", "normalized", "stages")
NORM_ROUTES_DIR = os.path.join(BASE_DIR, "data", "normalized", "routes")

os.makedirs(NORM_FARES_DIR, exist_ok=True)
os.makedirs(NORM_STAGES_DIR, exist_ok=True)
os.makedirs(NORM_ROUTES_DIR, exist_ok=True)


def parse_mtc_routes():
    """Parses 685 official MTC route numbers and classifies route variants."""
    with open(ROUTES_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    match = re.search(r"<select[^>]*name=[\"']selroute[\"'][^>]*>(.*?)</select>", html, re.DOTALL)
    if not match:
        raise ValueError("Could not locate selroute dropdown in mtc_official_routes.html")

    options = re.findall(r"<option\s+value=[\"'](.*?)[\"'][^>]*>(.*?)</option>", match.group(1), re.DOTALL)
    routes = []
    for val, text in options:
        val = val.strip()
        text = text.strip()
        if not val or val == "1":
            continue

        # Classify service suffix
        service_category = "regular"
        if "CT" in val:
            service_category = "cut_trip"
        elif val.endswith("E"):
            service_category = "express"
        elif val.endswith("X"):
            service_category = "deluxe_express"
        elif val.startswith("M") or val.startswith("S") or val.startswith("V"):
            service_category = "feeder_or_small"

        routes.append({
            "route_code": val,
            "route_label": text,
            "service_category": service_category,
            "agency_id": "MTC",
            "source_id": "MTC_OFFICIAL",
            "raw_file_id": "MTC_OFFICIAL_ROUTES_20260918",
            "disclosure_date": "2026-08-07"
        })

    csv_path = os.path.join(NORM_ROUTES_DIR, "normalized_official_routes.csv")
    json_path = os.path.join(NORM_ROUTES_DIR, "normalized_official_routes.json")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(routes[0].keys()))
        writer.writeheader()
        writer.writerows(routes)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)

    print(f"[MTC Routes] Successfully parsed {len(routes)} official routes -> {csv_path}")
    return routes


def parse_mtc_stages():
    """Parses 1,562 official MTC fare stages."""
    with open(STAGES_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    match = re.search(r"<select[^>]*name=[\"']swselfrom[\"'][^>]*>(.*?)</select>", html, re.DOTALL)
    if not match:
        raise ValueError("Could not locate swselfrom dropdown in mtc_official_stages.html")

    options = re.findall(r"<option\s+value=\"([^\"]*)\"[^>]*>(.*?)</option>", match.group(1), re.DOTALL)
    stages = []
    seen = set()

    for idx, (val, text) in enumerate(options, 1):
        stage_name = val.strip()
        if not stage_name or stage_name in seen:
            continue
        seen.add(stage_name)

        # Normalize clean name
        clean_name = re.sub(r"\s+", " ", stage_name).strip()
        slug = re.sub(r"[^A-Za-z0-9]", "_", clean_name).strip("_").upper()
        stage_id = f"MTC_STAGE_{idx:04d}_{slug[:20]}"

        stages.append({
            "stage_id": stage_id,
            "stage_name": clean_name,
            "agency_id": "MTC",
            "source_id": "MTC_OFFICIAL",
            "raw_file_id": "MTC_OFFICIAL_STAGES_20260918"
        })

    csv_path = os.path.join(NORM_STAGES_DIR, "normalized_mtc_stages.csv")
    json_path = os.path.join(NORM_STAGES_DIR, "normalized_mtc_stages.json")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(stages[0].keys()))
        writer.writeheader()
        writer.writerows(stages)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stages, f, indent=2, ensure_ascii=False)

    print(f"[MTC Stages] Successfully parsed {len(stages)} official fare stages -> {csv_path}")
    return stages


def parse_mtc_fares():
    """Parses the stage fare matrix across 11 service types and stages 1-30."""
    with open(FARES_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    tabs = re.findall(r"<a\s+href=\"#(tab\d+)\"[^>]*><strong>(.*?)</strong></a>", html)
    if not tabs:
        raise ValueError("Could not locate fare service tabs in mtc_official_fares.html")

    fares = []
    effective_date = "2018-01-29"
    gov_order = "G.O (Ms.) No.48 Dated 28.01.2018"

    for tab_id, service_name in tabs:
        clean_service = re.sub(r"\s+", " ", service_name).strip()
        service_slug = re.sub(r"[^A-Za-z0-9]", "_", clean_service).upper()

        pane_match = re.search(
            rf"<div\s+class=\"tab-pane[^\"]*\"\s+id=\"{tab_id}\">(.*?)(?=<div\s+class=\"tab-pane|</div>\s*</div>\s*</div>\s*</div>)",
            html,
            re.DOTALL
        )
        if not pane_match:
            continue

        pane_html = pane_match.group(1)
        stages = re.findall(
            r"<div\s+class=\"stage[^\"]*\">\s*(\d+)\s*<span\s+class=\"rate\">\s*([0-9.]+)\s*</span>\s*</div>",
            pane_html
        )

        for stage_str, fare_str in stages:
            stage_num = int(stage_str)
            fare_amount = float(fare_str)
            fare_id = f"FARE_MTC_{service_slug}_S{stage_num:02d}"

            fares.append({
                "fare_id": fare_id,
                "agency_id": "MTC",
                "service_type": clean_service,
                "stage_number": stage_num,
                "fare_amount": fare_amount,
                "currency": "INR",
                "effective_date": effective_date,
                "government_order": gov_order,
                "source_id": "MTC_OFFICIAL",
                "raw_file_id": "MTC_OFFICIAL_FARES_20260918"
            })

    csv_path = os.path.join(NORM_FARES_DIR, "normalized_mtc_fares.csv")
    json_path = os.path.join(NORM_FARES_DIR, "normalized_mtc_fares.json")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fares[0].keys()))
        writer.writeheader()
        writer.writerows(fares)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(fares, f, indent=2, ensure_ascii=False)

    print(f"[MTC Fares] Successfully parsed {len(fares)} stage-fare matrix entries -> {csv_path}")
    return fares


def main():
    print("Parsing official MTC Bronze disclosures into Silver datasets...")
    routes = parse_mtc_routes()
    stages = parse_mtc_stages()
    fares = parse_mtc_fares()
    print("MTC Silver normalization complete.")


if __name__ == "__main__":
    main()
