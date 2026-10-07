"""Canonical transport service tests with controlled operation inputs."""

import pytest

from src.nlp_v2.dispatch import OPERATIONS


@pytest.fixture(scope="module")
def service():
    from src.nlp_v2.domain import CanonicalTransitService

    return CanonicalTransitService()


def test_every_t3_operation_has_explicit_service_handler(service):
    assert set(OPERATIONS.values()) == set(service.handlers)


def test_bus_route_sequence_and_membership_use_real_ordered_stops(service):
    result = service.execute("LIST_ROUTE_STOPS", {"route_number": "102", "transport_mode": "bus"})
    assert result.status == "ok"
    assert result.data["sequences"]
    sequence = next(item for item in result.data["sequences"] if item["route_id"] == "GTFS_ROUTE_24079")
    assert len(sequence["stops"]) > 1
    assert all(a["sequence"] < b["sequence"] for a, b in zip(sequence["stops"], sequence["stops"][1:]))
    stop_id = sequence["stops"][0]["stop_id"]
    membership = service.execute("CHECK_STOP_ON_ROUTE", {"route_number": "102", "stop": stop_id})
    assert membership.status == "ok" and membership.data["on_route"] is True


def test_direct_route_respects_direction_and_uses_published_sequence(service):
    sequence = service.execute("LIST_ROUTE_STOPS", {"route_number": "102", "transport_mode": "bus"}).data["sequences"][0]
    first, second = sequence["stops"][0], sequence["stops"][1]
    forward = service.execute("PLAN_ROUTE", {"origin": first["stop_id"], "destination": second["stop_id"], "transport_mode": "bus"})
    assert forward.status == "ok"
    assert forward.data["routes"][0]["source"]
    assert forward.data["provisional"] is True


def test_official_metro_fare_includes_effective_date_and_is_not_current_claim(service):
    result = service.execute("CALCULATE_FARE", {
        "origin": "METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL",
        "destination": "METRO_CHENNAI_INTERNATIONAL_AIRPORT",
    })
    assert result.status == "ok"
    assert result.data["amount"] == 40.0
    assert result.data["effective_date"] == "2021-02-22"
    assert result.data["provisional"] is True


def test_nearest_is_geometric_and_has_distance_not_walk_time(service):
    result = service.execute("FIND_NEAREST_STATION", {"landmark": "OSM_POI_12137617372", "transport_mode": "metro"})
    assert result.status == "ok"
    assert result.data["distance_type"] == "straight_line"
    assert result.data["stops"][0]["distance_m"] >= 0
    assert "walking_time_min" not in result.data["stops"][0]


def test_published_departures_and_bounds_remain_provisional(service):
    slots = {"station": "BUS_5821", "date": "2026-10-06"}
    bounds = service.execute("GET_FIRST_LAST_SERVICE", slots)
    assert bounds.status == "ok"
    assert bounds.data["time_format"] == "gtfs_service_day"
    assert bounds.data["provisional"] is True
    departures = service.execute("GET_SCHEDULED_DEPARTURES", {**slots, "time": "08:00:00"})
    assert departures.status == "ok"
    assert all(item["time"] >= "08:00:00" for item in departures.data["departures"])
    assert departures.data["provisional"] is True


def test_frequency_needs_specific_route_or_line(service):
    result = service.execute("GET_SERVICE_FREQUENCY", {"station": "BUS_5821"})
    assert result.status == "unavailable"


def test_relative_day_schedule_uses_chennai_reference_date():
    from datetime import date
    from src.nlp_v2.domain import CanonicalTransitService

    service = CanonicalTransitService(reference_date=date(2026, 10, 6))
    today = service.execute("GET_FIRST_LAST_SERVICE", {"station": "BUS_5821", "temporal_relative": "today"})
    explicit = service.execute("GET_FIRST_LAST_SERVICE", {"station": "BUS_5821", "date": "2026-10-06"})
    assert today == explicit
    unknown = service.execute("GET_FIRST_LAST_SERVICE", {"station": "BUS_5821", "temporal_relative": "kal"})
    assert unknown.status == "unavailable"
    future = CanonicalTransitService(reference_date=date(2040, 1, 1))
    assert future.execute("GET_FIRST_LAST_SERVICE", {"station": "BUS_5821", "temporal_relative": "tomorrow"}).status == "unavailable"


def test_default_chennai_reference_date_advances_across_midnight(monkeypatch):
    from datetime import datetime
    import src.nlp_v2.domain as domain

    dates = iter((datetime(2026, 10, 6, 23, 59), datetime(2026, 10, 7, 0, 1)))
    class Clock:
        @staticmethod
        def now(zone):
            assert str(zone) == "Asia/Kolkata"
            return next(dates)
    monkeypatch.setattr(domain, "datetime", Clock)
    service = domain.CanonicalTransitService()
    assert service.reference_date.isoformat() == "2026-10-06"
    assert service.reference_date.isoformat() == "2026-10-07"


def test_nearest_mrts_does_not_return_suburban_rail(service):
    result = service.execute("FIND_NEAREST_STATION", {"landmark": "OSM_POI_12137617372", "transport_mode": "mrts"})
    assert result.status == "ok"
    assert all(row["mode"] == "mrts" for row in result.data["stops"])


def test_normalized_route_code_matches_spaced_canonical_code(service):
    result = service.execute("GET_SERVICE_FREQUENCY", {"station": "BUS_10235", "route_number": "25R"})
    assert result.status == "ok"
    assert result.data["median_headway_minutes"] > 0
    assert result.data["provisional"] is True


def test_mismatched_metro_route_stop_snapshot_does_not_claim_negative_membership(service):
    result = service.execute("CHECK_STOP_ON_ROUTE", {
        "route_number": "Blue Line", "stop": "METRO_EGMORE", "transport_mode": "metro",
    })
    assert result.status == "unavailable"


def test_fare_does_not_substitute_token_amount_for_unverified_ticket_type(service):
    result = service.execute("CALCULATE_FARE", {
        "origin": "METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL",
        "destination": "METRO_CHENNAI_INTERNATIONAL_AIRPORT",
        "ticket_type": "smart_card",
    })
    assert result.status == "unavailable"


def test_schedule_does_not_ignore_requested_destination(service):
    result = service.execute("GET_SCHEDULED_DEPARTURES", {
        "origin": "BUS_5821", "destination": "METRO_EGMORE",
    })
    assert result.status == "unavailable"


def test_stage_fare_does_not_ignore_metro_mode(service):
    result = service.execute("CALCULATE_FARE", {"stage_number": 2, "transport_mode": "metro"})
    assert result.status == "unavailable"


def test_frequency_does_not_ignore_requested_time(service):
    result = service.execute("GET_SERVICE_FREQUENCY", {
        "station": "BUS_10235", "route_number": "25R", "time": "23:00:00",
    })
    assert result.status == "unavailable"


def test_missing_schema_degrades_to_error(tmp_path):
    import sqlite3
    from src.nlp_v2.domain import CanonicalTransitService

    empty_db = tmp_path / "empty.db"
    sqlite3.connect(empty_db).close()
    result = CanonicalTransitService(empty_db).execute("LIST_ROUTE_STOPS", {"route_number": "102"})
    assert result.status == "error"


@pytest.mark.parametrize("operation,slots", [
    ("GET_TICKETING_POLICY", {"ticket_type": "smart_card"}),
    ("GET_ACCESSIBILITY_INFO", {"station": "METRO_EGMORE", "accessibility_feature": "lift"}),
    ("GET_STATION_FACILITY", {"station": "METRO_EGMORE", "facility_type": "parking"}),
    ("GET_INTERCHANGE_DETAILS", {"station": "HUB_GUINDY"}),
    ("PLAN_MULTIMODAL_ROUTE", {"origin": "HUB_GUINDY", "destination": "HUB_TAMBARAM"}),
    ("REJECT_UNSUPPORTED_REALTIME", {}),
])
def test_unverified_or_absent_facts_are_unavailable(service, operation, slots):
    assert service.execute(operation, slots).status == "unavailable"


def test_positive_availability_is_sourced_published_connectivity(service):
    result = service.execute('CHECK_SERVICE_AVAILABILITY', {
        'origin': 'BUS_11159', 'destination': 'BUS_11192', 'transport_mode': 'bus'})
    assert result.status == 'ok'
    assert result.data['scope'] == 'published_connectivity_not_current_operation'
    assert result.data['current_operation_confirmed'] is False
    assert result.data['provisional'] is True
    assert all(row['source'] and row['origin_sequence'] < row['destination_sequence']
               for row in result.data['routes'])


def test_availability_does_not_infer_negative_or_ignore_date(service):
    for slots in (
        {'origin': 'BUS_11159', 'destination': 'METRO_EGMORE'},
        {'origin': 'BUS_11159', 'destination': 'BUS_11192', 'date': '2040-01-01'},
        {'origin': 'BUS_11159', 'destination': 'BUS_11192', 'time': '22:00:00'},
    ):
        assert service.execute('CHECK_SERVICE_AVAILABILITY', slots).status == 'unavailable'


@pytest.mark.parametrize('constraint', [{'date': '2040-01-01'}, {'time': '22:00:00'}, {'temporal_relative': 'tomorrow'}])
def test_static_route_does_not_ignore_temporal_constraint(service, constraint):
    result = service.execute('PLAN_ROUTE', {'origin': 'BUS_11159', 'destination': 'BUS_11192', **constraint})
    assert result.status == 'unavailable'
    assert result.data['reason'] == 'route_temporal_scope_unsupported'


def test_night_tariff_uses_exact_category_with_case_normalization(service):
    result = service.execute('CALCULATE_FARE', {
        'stage_number': 7, 'transport_mode': 'bus', 'service_type': 'Night Services'})
    assert result.status == 'ok'
    assert result.data['service_type'] == 'Night Services'
    assert result.data['source'] and result.data['effective_date']
    assert service.execute('CALCULATE_FARE', {
        'stage_number': 7, 'service_type': 'Air Conditioned Services'}).status == 'unavailable'


def test_stop_coordinates_can_anchor_another_mode_without_access_claim(service):
    result = service.execute('FIND_NEAREST_STATION', {'landmark': 'BUS_5821', 'transport_mode': 'metro'})
    assert result.status == 'ok'
    assert result.data['anchor'] == 'BUS_5821'
    assert all(row['mode'] == 'metro' for row in result.data['stops'])
    assert result.data['distance_type'] == 'straight_line'


def test_membership_preserves_canonical_provenance(service):
    result = service.execute('CHECK_STOP_ON_ROUTE', {'route_number': '25R', 'stop': 'BUS_10235'})
    assert result.status == 'ok'
    assert result.data['source']


def test_frequency_does_not_merge_opposing_directions(service, monkeypatch):
    rows = [dict(departure_time=t, route_id='R', direction_id=d, canonical_stop_id='S', source_id='test')
            for d, t in [(0, '08:00:00'), (1, '08:10:00'), (0, '08:20:00'), (1, '08:30:00')]]
    monkeypatch.setattr(service, '_scheduled_rows', lambda conn, slots: rows)
    result = service.execute('GET_SERVICE_FREQUENCY', {'station': 'S', 'route_number': 'R'})
    assert result.status == 'unavailable'
    assert result.data['reason'] == 'frequency_direction_or_stop_ambiguous'


def test_incomplete_topology_is_disclosed_and_cannot_prove_absence(service):
    import sqlite3
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE transport_routes(route_id,route_short_name,mode,source_id,status);
        CREATE TABLE transport_stops(stop_id,canonical_name,mode);
        CREATE TABLE route_stops(route_id,direction_id,stop_sequence,canonical_stop_id);
        INSERT INTO transport_routes VALUES('R','88','bus','synthetic','operational');
        INSERT INTO transport_stops VALUES('BUS_A','A','bus'),('BUS_B','B','bus'),
            ('METRO_C','C','metro'),('BUS_OTHER','Other','bus');
        INSERT INTO route_stops VALUES('R',0,1,'BUS_A'),('R',0,2,'METRO_C'),('R',0,3,'BUS_B');
    ''')
    sequence = service._list_route_stops(conn, {'route_number': '88'})
    assert sequence.status == 'ok'
    assert sequence.data['partial_topology'] is True
    assert sequence.data['excluded_unusable_rows'] == 1
    negative = service._check_stop_on_route(conn, {'route_number': '88', 'stop': 'BUS_OTHER'})
    assert negative.status == 'unavailable'
    positive = service._check_stop_on_route(conn, {'route_number': '88', 'stop': 'BUS_A'})
    assert positive.status == 'ok' and positive.data['on_route'] is True
    via = service._plan_route(conn, {'origin': 'BUS_A', 'destination': 'BUS_B', 'via': 'METRO_C'})
    assert via.status == 'unavailable'
    for handler in (service._plan_route, service._availability):
        result = handler(conn, {'origin': 'BUS_A', 'destination': 'BUS_B'})
        assert result.status == 'ok'
        assert 'partial' in result.message.lower()
    conn.close()


def test_empty_same_code_variant_prevents_negative_membership(service):
    import sqlite3
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE transport_routes(route_id,route_short_name,mode,source_id,status);
        CREATE TABLE transport_stops(stop_id,canonical_name,mode);
        CREATE TABLE route_stops(route_id,direction_id,stop_sequence,canonical_stop_id);
        INSERT INTO transport_routes VALUES('R_FULL','88','bus','synthetic','operational'),
            ('R_EMPTY','88','bus','synthetic','operational');
        INSERT INTO transport_stops VALUES('BUS_A','A','bus'),('BUS_B','B','bus'),('BUS_OTHER','Other','bus');
        INSERT INTO route_stops VALUES('R_FULL',0,1,'BUS_A'),('R_FULL',0,2,'BUS_B');
    ''')
    result = service._check_stop_on_route(conn, {'route_number': '88', 'stop': 'BUS_OTHER'})
    assert result.status == 'unavailable'
    positive = service._check_stop_on_route(conn, {'route_number': '88', 'stop': 'BUS_A'})
    assert positive.status == 'ok'
    assert positive.data['partial_topology'] is True
    assert positive.data['matched_route_ids'] == ['R_FULL']
    sequence = service._list_route_stops(conn, {'route_number': '88'})
    assert sequence.data['partial_topology'] is True
    assert sequence.data['uncovered_route_ids'] == ['R_EMPTY']
    conn.close()
