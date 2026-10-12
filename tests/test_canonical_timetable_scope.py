"""Synthetic timetable contracts; no historical evaluation examples or labels."""

import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from src.nlp_v2.dispatch import ServiceResult
from src.nlp_v2.entities import CanonicalResolver
from src.nlp_v2.slots import T3SlotExtractor


INTENTS = ('scheduled_departure', 'first_and_last_service', 'service_frequency')


@pytest.fixture
def resolver(tmp_path):
    path = tmp_path / 'timetable.db'
    with sqlite3.connect(path) as conn:
        conn.executescript('''
            CREATE TABLE transport_hubs (hub_id TEXT, hub_name TEXT);
            CREATE TABLE transport_stops (stop_id TEXT, canonical_name TEXT, mode TEXT);
            CREATE TABLE stop_names (stop_id TEXT, name TEXT);
            CREATE TABLE places (place_id TEXT, canonical_name TEXT);
            CREATE TABLE place_names (place_id TEXT, name TEXT);
            CREATE TABLE transport_routes (route_id TEXT, route_short_name TEXT, mode TEXT, status TEXT);
            CREATE TABLE route_stops (route_id TEXT, canonical_stop_id TEXT);
            INSERT INTO transport_stops VALUES
              ('BUS_A','Alpha Terminal','bus'),('BUS_B','Bravo Terminal','bus'),
              ('BUS_C','Charlie Terminal','bus'),('BUS_D','Delta Terminal','bus');
            INSERT INTO stop_names VALUES ('BUS_A','अल्फा स्टॉप'),('BUS_B','ब्रावो स्टॉप'),('BUS_C','चार्ली स्टॉप');
            INSERT INTO transport_routes VALUES ('R25R','25R','bus','operational');
            INSERT INTO route_stops VALUES ('R25R','BUS_A'),('R25R','BUS_B'),('R25R','BUS_C'),('R25R','BUS_D');
        ''')
    return CanonicalResolver(path)
























