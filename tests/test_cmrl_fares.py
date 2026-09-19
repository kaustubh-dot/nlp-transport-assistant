"""Tests for Official CMRL Origin-Destination Fares."""

import os
import sqlite3
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL_DB = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")


@pytest.fixture
def db_conn():
    if not os.path.exists(CANONICAL_DB):
        pytest.skip(f"Canonical DB not found at {CANONICAL_DB}")
    conn = sqlite3.connect(CANONICAL_DB)
    yield conn
    conn.close()


def test_cmrl_fares_row_count_and_completeness(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) FROM cmrl_station_fares;")
    count = cur.fetchone()[0]
    assert count == 1681, f"Expected 1681 CMRL OD pairs (41x41), got {count}"


def test_cmrl_fares_zero_diagonals(db_conn):
    cur = db_conn.cursor()
    cur.execute("""
        SELECT count(*) FROM cmrl_station_fares
        WHERE origin_stop_id = destination_stop_id AND (token_fare != 0 OR discounted_fare != 0);
    """)
    non_zero_diags = cur.fetchone()[0]
    assert non_zero_diags == 0, f"Found {non_zero_diags} non-zero diagonal entries"


def test_cmrl_fares_symmetry(db_conn):
    cur = db_conn.cursor()
    cur.execute("""
        SELECT f1.origin_stop_id, f1.destination_stop_id, f1.token_fare, f2.token_fare
        FROM cmrl_station_fares f1
        JOIN cmrl_station_fares f2
          ON f1.origin_stop_id = f2.destination_stop_id
         AND f1.destination_stop_id = f2.origin_stop_id
        WHERE f1.token_fare != f2.token_fare;
    """)
    asymmetric_pairs = cur.fetchall()
    assert len(asymmetric_pairs) == 0, f"Found asymmetric fare pairs: {asymmetric_pairs[:5]}"


def test_cmrl_fares_known_sample_routes(db_conn):
    cur = db_conn.cursor()

    # Airport to Central
    cur.execute("""
        SELECT token_fare, discounted_fare FROM cmrl_station_fares
        WHERE origin_stop_id = 'METRO_CHENNAI_INTERNATIONAL_AIRPORT'
          AND destination_stop_id = 'METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL';
    """)
    row = cur.fetchone()
    assert row is not None, "Airport to Central fare record missing"
    assert row[0] == 40.0, f"Airport to Central token fare expected 40.0, got {row[0]}"
    assert row[1] == 32.0, f"Airport to Central discounted fare expected 32.0, got {row[1]}"

    # Airport to Alandur
    cur.execute("""
        SELECT token_fare, discounted_fare FROM cmrl_station_fares
        WHERE origin_stop_id = 'METRO_CHENNAI_INTERNATIONAL_AIRPORT'
          AND destination_stop_id = 'METRO_ARIGNAR_ANNA_ALANDUR';
    """)
    row = cur.fetchone()
    assert row is not None, "Airport to Alandur fare record missing"
    assert row[0] == 20.0, f"Airport to Alandur token fare expected 20.0, got {row[0]}"
    assert row[1] == 16.0, f"Airport to Alandur discounted fare expected 16.0, got {row[1]}"


def test_cmrl_fares_foreign_key_integrity(db_conn):
    cur = db_conn.cursor()
    cur.execute("""
        SELECT count(*) FROM cmrl_station_fares f
        LEFT JOIN transport_stops ts ON f.origin_stop_id = ts.stop_id
        WHERE ts.stop_id IS NULL;
    """)
    orphan_origins = cur.fetchone()[0]
    assert orphan_origins == 0, f"Found {orphan_origins} orphan origin stops"

    cur.execute("""
        SELECT count(*) FROM cmrl_station_fares f
        LEFT JOIN transport_stops ts ON f.destination_stop_id = ts.stop_id
        WHERE ts.stop_id IS NULL;
    """)
    orphan_destinations = cur.fetchone()[0]
    assert orphan_destinations == 0, f"Found {orphan_destinations} orphan destination stops"
