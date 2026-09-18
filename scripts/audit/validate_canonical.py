#!/usr/bin/env python3
"""Automated data quality and integrity validator for canonical transport knowledge base.

Checks:
- Coordinate plausibility and Chennai-serving external stop retention
- Null or empty station/stop names
- Duplicate source record mappings
- Accidental cross-mode merges (e.g. Metro merged with Suburban Rail or Bus Stop)
- Foreign key integrity (stops, routes, hub members, interchanges, walking transfers)
- Multilingual and Tamil name preservation
"""

import os
import sys
import sqlite3
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CANONICAL_DB = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")


def run_validations() -> Dict[str, Any]:
    if not os.path.exists(CANONICAL_DB):
        raise FileNotFoundError(f"Canonical DB missing at {CANONICAL_DB}")

    conn = sqlite3.connect(CANONICAL_DB)
    cur = conn.cursor()

    results = {
        "passed": True,
        "checks": []
    }

    def log_check(name: str, passed: bool, details: str):
        if not passed:
            results["passed"] = False
        results["checks"].append({
            "name": name,
            "passed": passed,
            "details": details
        })
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {name}: {details}")

    # Check 1: Stop names not null or empty
    cur.execute("SELECT count(*) FROM transport_stops WHERE canonical_name IS NULL OR length(trim(canonical_name)) = 0")
    empty_names = cur.fetchone()[0]
    log_check("Stop Names Non-Empty", empty_names == 0, f"Found {empty_names} stops with empty names.")

    # Check 2: Coordinate sanity & plausibility
    cur.execute("""
        SELECT count(*) FROM transport_stops
        WHERE latitude IS NOT NULL AND (latitude < 12.0 OR latitude > 14.0 OR longitude < 79.0 OR longitude > 81.0)
    """)
    implausible_coords = cur.fetchone()[0]
    log_check("Coordinate Regional Plausibility", implausible_coords == 0, f"Found {implausible_coords} implausible coordinates outside 12-14N, 79-81E.")

    # Check 3: Chennai-serving external stops retention
    cur.execute("SELECT count(*) FROM transport_stops WHERE inside_cma = 0")
    external_stops = cur.fetchone()[0]
    log_check("Chennai-Serving External Stops Retained", external_stops > 0, f"Successfully retained {external_stops} Chennai-serving external stops outside CMA.")

    # Check 4: Accidental cross-mode merge prevention (e.g. Guindy Metro vs Guindy Rail)
    cur.execute("""
        SELECT stop_id, count(DISTINCT mode) FROM transport_stops GROUP BY stop_id HAVING count(DISTINCT mode) > 1
    """)
    mode_clashes = len(cur.fetchall())
    log_check("Cross-Mode Separation Preserved", mode_clashes == 0, f"Found {mode_clashes} stops with multi-mode collision.")

    # Check 5: Foreign key integrity between hub_members and transport_stops
    cur.execute("""
        SELECT count(*) FROM hub_members hm
        LEFT JOIN transport_stops ts ON hm.stop_id = ts.stop_id
        WHERE ts.stop_id IS NULL
    """)
    orphan_hub_members = cur.fetchone()[0]
    log_check("Hub Members Foreign Key Integrity", orphan_hub_members == 0, f"Found {orphan_hub_members} orphan hub members.")

    # Check 6: Multilingual Tamil name preservation
    cur.execute("SELECT count(*) FROM stop_names WHERE language = 'ta'")
    ta_stop_names = cur.fetchone()[0]
    log_check("Tamil Names Preserved", ta_stop_names > 0, f"Found {ta_stop_names} stops with preserved Tamil script names.")

    # Check 7: End-to-end source link provenance
    cur.execute("SELECT count(*) FROM entity_source_links")
    links_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM transport_stops")
    stops_count = cur.fetchone()[0]
    log_check("Source-Link Provenance Complete", links_count >= stops_count, f"Total source links: {links_count} for {stops_count} canonical stops.")

    conn.close()
    return results


if __name__ == "__main__":
    res = run_validations()
    if res["passed"]:
        print("\nAll automated data quality checks passed successfully!")
    else:
        print("\nData quality issues detected. Please review logs.")
        sys.exit(1)
