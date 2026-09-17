"""Unit tests for SQLite transit retrieval module."""

import os
import pytest
from src.retrieval import TransitRetriever
from scripts.build_transport_db import init_db, export_aliases_csv


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Initialize database before tests
    init_db()
    export_aliases_csv()


@pytest.fixture
def retriever():
    return TransitRetriever()


def test_station_lookup(retriever):
    info = retriever.get_station_info("CHENNAI_CENTRAL")
    assert info is not None
    assert info["name_en"] == "Chennai Central"
    assert "चेन्नई" in info["name_hi"]


def test_route_retrieval_direct(retriever):
    routes = retriever.get_route("CHENNAI_CENTRAL", "CHENNAI_AIRPORT", mode="metro")
    assert len(routes) > 0
    route = routes[0]
    assert route["mode"] == "metro"
    assert route["travel_time_mins"] == 40


def test_accessibility_retrieval(retriever):
    fac = retriever.get_accessibility_info("KOYAMBEDU")
    assert fac is not None
    assert fac["wheelchair_available"] == 1
    assert fac["lift_available"] == 1


def test_service_timing(retriever):
    timings = retriever.get_service_timing(mode="metro")
    assert len(timings) > 0
    assert timings[0]["first_service"] == "05:00"
    assert timings[0]["last_service"] == "23:00"
