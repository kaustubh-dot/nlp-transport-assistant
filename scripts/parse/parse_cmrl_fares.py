#!/usr/bin/env python3
"""Parser for Official CMRL Origin-Destination Fare Matrices.

Extracts:
1. Single Journey Token (SJT) fares from `cmrl_fare_chart_all_stations.pdf`
2. 20% Discounted Smart Card / QR fares from `cmrl_fare_chart_20pct_discount.pdf`

Maps all 41 stations to canonical stop IDs in `canonical_transport.db`.
Outputs:
- `data/normalized/fares/normalized_cmrl_fares.csv`
- `data/normalized/fares/normalized_cmrl_fares.json`
- Ingests into `cmrl_station_fares` table in `data/canonical/transit/canonical_transport.db`.
"""

import os
import csv
import json
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "cmrl", "2026-09-19")
NORM_DIR = os.path.join(BASE_DIR, "data", "normalized", "fares")
DB_PATH = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")

PDF_SJT = os.path.join(RAW_DIR, "cmrl_fare_chart_all_stations.pdf")
PDF_DISC = os.path.join(RAW_DIR, "cmrl_fare_chart_20pct_discount.pdf")

# The 41 stations in exact order of the PDF matrix rows & columns
STATIONS_ORDERED = [
    ("AIRPORT", "METRO_CHENNAI_INTERNATIONAL_AIRPORT", "Chennai International Airport"),
    ("MEENAMBAKKAM", "METRO_MEENAMBAKKAM", "Meenambakkam"),
    ("NANGANALLUR ROAD", "METRO_OTA_NANGANALLUR_ROAD", "OTA-Nanganallur Road"),
    ("ARIGNAR ANNA ALANDUR METRO", "METRO_ARIGNAR_ANNA_ALANDUR", "Arignar Anna Alandur Metro"),
    ("GUINDY", "METRO_GUINDY", "Guindy"),
    ("LITTLE MOUNT", "METRO_LITTLE_MOUNT", "Little Mount"),
    ("SAIDAPET", "METRO_SAIDAPET", "Saidapet Metro"),
    ("NANDANAM", "METRO_NANDANAM", "Nandanam"),
    ("TEYNAMPET", "METRO_TEYNAMPET", "Teynampet"),
    ("AG-DMS", "METRO_AG___8211__DMS", "AG – DMS"),
    ("THOUSAND LIGHTS", "METRO_THOUSAND_LIGHTS", "Thousand Lights"),
    ("LIC", "METRO_LIC", "LIC"),
    ("GOVERNMENT ESTATE", "METRO_GOVERNMENT_ESTATE", "Government Estate"),
    ("PURATCHI THALAIVAR DR.M.G.RAMACHANDRAN CENTRAL METRO", "METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL", "Puratchi Thalaivar Dr. M.G.Ramachandran Central Metro"),
    ("HIGH COURT", "METRO_HIGHCOURT", "Highcourt"),
    ("MANNADI", "METRO_MANNADI", "Mannadi"),
    ("WASHERMENPET", "METRO_WASHERMENPET", "Washermenpet"),
    ("THYAGARAYA COLLEGE", "METRO_SIR_THIYAGARAYA_COLLEGE", "Sir Theagaraya College"),
    ("TONDIARPET", "METRO_TONDIARPET", "Tondiarpet"),
    ("NEW WASHERMENPET", "METRO_NEW_WASHERMENPET", "New Washermenpet"),
    ("TOLL GATE", "METRO_TOLLGATE", "Tollgate"),
    ("KALADIPET", "METRO_KALADIPET", "Kaladipet"),
    ("THIRUVOTRIYUR THEREDI", "METRO_THIRUVOTTRIYUR_THERADI", "Thiruvottiyur Theradi"),
    ("THIRUVOTRIYUR", "METRO_THIRUVOTRIYUR", "Thiruvottriyur"),
    ("WIMCO NAGAR", "METRO_WIMCO_NAGAR_6738", "Wimco Nagar"),
    ("WIMCO NAGAR DEPOT", "METRO_WIMCO_NAGAR", "Wimco Nagar Depot"),
    ("EKKATTUTHANGAL", "METRO_EKKATTUTHANGAL", "Ekkattuthangal"),
    ("ASHOK NAGAR", "METRO_ASHOK_NAGAR", "Ashok Nagar"),
    ("VADAPALANI", "METRO_VADAPALANI", "Vadapalani"),
    ("ARUMBAKKAM", "METRO_ARUMBAKKAM", "Arumbakkam"),
    ("PURATCHI THALAIVI DR.J.JAYALALITHAA CMBT METRO", "METRO_PURATCHI_THALAIVI_DR_J_JAYALALITHAA_CMBT", "Puratchi Thalaivi Dr.J.Jayalalithaa CMBT Metro"),
    ("KOYAMBEDU", "METRO_KOYAMBEDU", "Koyambedu"),
    ("THIRUMANGALAM", "METRO_THIRUMANGALAM", "Thirumangalam"),
    ("ANNA NAGAR TOWER", "METRO_ANNA_NAGAR_TOWER", "Anna Nagar Tower"),
    ("ANNA NAGAR EAST", "METRO_ANNA_NAGAR_EAST", "Anna Nagar East"),
    ("SHENOY NAGAR", "METRO_SHENOY_NAGAR", "Shenoy Nagar"),
    ("PACHIAPPAS COLLEGE", "METRO_PACHAIYAPPA_S_COLLEGE", "Pachaiyappa's College"),
    ("KILPAUK", "METRO_KILPAUK", "Kilpauk"),
    ("NEHRU PARK", "METRO_NEHRU_PARK", "Nehru Park"),
    ("EGMORE", "METRO_EGMORE", "Egmore"),
    ("ST. THOMAS MOUNT", "METRO_ST__THOMAS_MOUNT", "St. Thomas Mount")
]


def extract_matrix_from_pdf(pdf_path: str):
    """Extract a 41x41 integer matrix from the PDF using pdftohtml."""
    cmd = ["pdftohtml", "-xml", "-stdout", "-nodrm", "-i", pdf_path]
    xml_data = subprocess.check_output(cmd)
    root = ET.fromstring(xml_data)
    page = root.find("page")
    texts = page.findall("text")

    nums = []
    for t in texts:
        txt = "".join(t.itertext()).strip()
        if txt.isdigit():
            nums.append((int(t.attrib["top"]), int(t.attrib["left"]), int(txt)))

    if len(nums) != 1681:
        raise ValueError(f"Expected 1681 cells from {pdf_path}, got {len(nums)}")

    row_map = defaultdict(list)
    for top, left, val in nums:
        row_map[top].append((left, val))

    sorted_tops = sorted(row_map.keys())
    if len(sorted_tops) != 41:
        raise ValueError(f"Expected 41 rows, got {len(sorted_tops)}")

    matrix = []
    for t in sorted_tops:
        cols = sorted(row_map[t], key=lambda x: x[0])
        if len(cols) != 41:
            raise ValueError(f"Row at top {t} has {len(cols)} cols instead of 41")
        matrix.append([c[1] for c in cols])

    # Validate zero diagonal and symmetry
    for i in range(41):
        if matrix[i][i] != 0:
            raise ValueError(f"Diagonal ({i},{i}) is non-zero: {matrix[i][i]}")
        for j in range(41):
            if matrix[i][j] != matrix[j][i]:
                raise ValueError(f"Asymmetry at ({i},{j}): {matrix[i][j]} != {matrix[j][i]}")

    return matrix


def main():
    print("Parsing SJT fare matrix...")
    matrix_sjt = extract_matrix_from_pdf(PDF_SJT)
    print("Parsing 20% discount fare matrix...")
    matrix_disc = extract_matrix_from_pdf(PDF_DISC)

    records = []
    for i in range(41):
        orig_label, orig_id, orig_cname = STATIONS_ORDERED[i]
        for j in range(41):
            dest_label, dest_id, dest_cname = STATIONS_ORDERED[j]
            sjt_fare = float(matrix_sjt[i][j])
            disc_fare = float(matrix_disc[i][j])
            fare_id = f"FARE_CMRL_{orig_id}_TO_{dest_id}"

            records.append({
                "fare_id": fare_id,
                "origin_stop_id": orig_id,
                "destination_stop_id": dest_id,
                "origin_station_name": orig_cname,
                "destination_station_name": dest_cname,
                "origin_chart_label": orig_label,
                "destination_chart_label": dest_label,
                "token_fare": sjt_fare,
                "discounted_fare": disc_fare,
                "currency": "INR",
                "agency_id": "CMRL",
                "effective_date": "2021-02-22",
                "source_id": "CMRL_OFFICIAL"
            })

    print(f"Generated {len(records)} OD fare records.")

    # Write normalized CSV
    os.makedirs(NORM_DIR, exist_ok=True)
    csv_path = os.path.join(NORM_DIR, "normalized_cmrl_fares.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved CSV: {csv_path}")

    # Write normalized JSON
    json_path = os.path.join(NORM_DIR, "normalized_cmrl_fares.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "source": "Chennai Metro Rail Limited (Official Fare Table)",
                "effective_date": "2021-02-22",
                "retrieved_at": "2026-09-19T04:47:43Z",
                "station_count": 41,
                "od_pair_count": len(records),
                "fare_types": ["Single Journey Token (SJT)", "20% Discounted Smart Card / QR"]
            },
            "fares": records
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON: {json_path}")

    # Ingest additively into canonical_transport.db
    print(f"Ingesting into {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cmrl_station_fares (
            fare_id TEXT PRIMARY KEY,
            origin_stop_id TEXT NOT NULL,
            destination_stop_id TEXT NOT NULL,
            origin_station_name TEXT NOT NULL,
            destination_station_name TEXT NOT NULL,
            token_fare REAL NOT NULL,
            discounted_fare REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'INR',
            agency_id TEXT NOT NULL DEFAULT 'CMRL',
            effective_date TEXT NOT NULL DEFAULT '2021-02-22',
            source_id TEXT NOT NULL DEFAULT 'CMRL_OFFICIAL',
            FOREIGN KEY (origin_stop_id) REFERENCES transport_stops(stop_id),
            FOREIGN KEY (destination_stop_id) REFERENCES transport_stops(stop_id)
        );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_cmrl_fares_od ON cmrl_station_fares(origin_stop_id, destination_stop_id);")

    insert_rows = [
        (
            r["fare_id"],
            r["origin_stop_id"],
            r["destination_stop_id"],
            r["origin_station_name"],
            r["destination_station_name"],
            r["token_fare"],
            r["discounted_fare"],
            r["currency"],
            r["agency_id"],
            r["effective_date"],
            r["source_id"]
        )
        for r in records
    ]

    cur.executemany("""
        INSERT OR REPLACE INTO cmrl_station_fares (
            fare_id, origin_stop_id, destination_stop_id, origin_station_name, destination_station_name,
            token_fare, discounted_fare, currency, agency_id, effective_date, source_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_rows)

    conn.commit()
    cur.execute("SELECT count(*) FROM cmrl_station_fares;")
    count = cur.fetchone()[0]
    print(f"Successfully loaded {count} rows into cmrl_station_fares in canonical DB.")
    conn.close()


if __name__ == "__main__":
    main()
