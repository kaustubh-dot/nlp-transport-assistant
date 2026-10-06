"""Synthetic contract tests for T3 slot extraction and canonical resolution."""

import sqlite3

import pytest


@pytest.fixture
def canonical_db(tmp_path):
    path = tmp_path / "canonical.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE transport_hubs (hub_id TEXT, hub_name TEXT);
            CREATE TABLE transport_stops (stop_id TEXT, canonical_name TEXT, mode TEXT);
            CREATE TABLE stop_names (stop_id TEXT, name TEXT);
            CREATE TABLE places (place_id TEXT, canonical_name TEXT);
            CREATE TABLE place_names (place_id TEXT, name TEXT);
            CREATE TABLE transport_routes (route_id TEXT, route_short_name TEXT, mode TEXT);
            CREATE TABLE route_stops (route_id TEXT, canonical_stop_id TEXT);
            INSERT INTO transport_hubs VALUES ('HUB_GUINDY','Guindy'),('HUB_CENTRAL','Chennai Central'),('HUB_TAMBARAM','Tambaram');
            INSERT INTO transport_stops VALUES
                ('METRO_GUINDY','Guindy','metro'),('RAIL_GUINDY','Guindy','suburban_rail'),
                ('BUS_GUINDY_1','Guindy','bus'),('BUS_GUINDY_2','Guindy','bus'),
                ('METRO_CENTRAL','Chennai Central','metro'),('RAIL_CENTRAL','Chennai Central','suburban_rail');
            INSERT INTO stop_names VALUES
                ('METRO_GUINDY','Guindy Metro'),('METRO_CENTRAL','Central Metro'),
                ('RAIL_GUINDY','Guindy Railway Station');
            INSERT INTO places VALUES ('PLACE_MARINA','Marina Beach');
            INSERT INTO place_names VALUES ('PLACE_MARINA','Marina Beach');
            INSERT INTO transport_routes VALUES ('ROUTE_29C','29C','bus');
            INSERT INTO route_stops VALUES ('ROUTE_29C','BUS_GUINDY_1');
        """)
    return str(path)


def test_generic_route_location_uses_canonical_hub(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver

    resolver = CanonicalResolver(canonical_db)
    spans = resolver.find_spans("guindy se chennai central kaise jau")
    guindy = next(span for span in spans if span.surface == "guindy")
    resolution = resolver.resolve(guindy, "origin", "point_to_point_route")
    assert resolution.entity_id == "HUB_GUINDY"
    assert resolution.ambiguous is False


def test_mode_qualified_station_selects_physical_node(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver

    resolver = CanonicalResolver(canonical_db)
    span = resolver.find_spans("guindy metro station")[0]
    resolution = resolver.resolve(span, "station", "station_accessibility", mode="metro")
    assert resolution.entity_id == "METRO_GUINDY"
    assert resolution.ambiguous is False


def test_unqualified_station_keeps_ambiguity(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver

    resolver = CanonicalResolver(canonical_db)
    span = resolver.find_spans("guindy")[0]
    resolution = resolver.resolve(span, "station", "station_facilities")
    assert resolution.entity_id is None
    assert resolution.ambiguous is True
    assert {candidate.entity_id for candidate in resolution.candidates} >= {"METRO_GUINDY", "RAIL_GUINDY"}


def test_route_constrained_stop_selects_unique_on_route_node(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver

    resolver = CanonicalResolver(canonical_db)
    span = resolver.find_spans("29C bus stop at guindy")[-1]
    resolution = resolver.resolve(span, "stop", "route_stop_membership", route_number="29C")
    assert resolution.entity_id == "BUS_GUINDY_1"


def test_hindi_alias_resolves_to_current_db_id_and_unknown_does_not_guess(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver

    resolver = CanonicalResolver(canonical_db)
    spans = resolver.find_spans("गिंडी से central")
    hindi_span = next(span for span in spans if span.surface == "गिंडी")
    assert resolver.resolve(hindi_span, "origin", "point_to_point_route").entity_id == "HUB_GUINDY"
    assert resolver.find_spans("unknownlandmark") == ()


@pytest.mark.parametrize("query", [
    "गिंडी से सेंट्रल कैसे जाऊँ?",
    "gindi se central kaise jau?",
    "गिंडी se central kaise jau?",
])
def test_hindi_roman_and_mixed_route_locations(canonical_db, query):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(query, "point_to_point_route")
    assert result.slots["origin"] == "HUB_GUINDY"
    assert result.slots["destination"] == "HUB_CENTRAL"
    assert result.clarification_reason is None


def test_explicit_metro_route_selects_metro_stops(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "from Guindy to Chennai Central by metro", "point_to_point_route")
    assert result.slots == {"origin": "METRO_GUINDY", "destination": "METRO_CENTRAL", "transport_mode": "metro"}


def test_reversed_direction_cues_assign_origin_and_destination(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "to Central from Guindy by metro", "point_to_point_route")
    assert result.slots["origin"] == "METRO_GUINDY"
    assert result.slots["destination"] == "METRO_CENTRAL"


def test_route_membership_preserves_code_and_resolves_on_route_stop(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    extractor = T3SlotExtractor(CanonicalResolver(canonical_db))
    result = extractor.extract("Does bus 29C stop at Guindy?", "route_stop_membership")
    assert result.slots["route_number"] == "29C"
    assert result.slots["stop"] == "BUS_GUINDY_1"
    assert result.slots["transport_mode"] == "bus"
    suffix = extractor.extract("Show all stops on bus 102K#", "route_stop_sequence")
    assert suffix.slots["route_number"] == "102K#"


def test_ambiguous_physical_station_is_not_guessed(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract("parking at Guindy station", "station_facilities")
    assert "station" not in result.slots
    assert result.clarification_reason == "entity_ambiguity"
    assert {candidate.entity_id for candidate in result.unresolved[0].candidates} >= {"METRO_GUINDY", "RAIL_GUINDY"}
    assert result.slots["facility_type"] == "parking"


def test_facility_accessibility_ticket_fare_and_nearest_slots(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    extractor = T3SlotExtractor(CanonicalResolver(canonical_db))
    facilities = extractor.extract("parking at Guindy metro", "station_facilities")
    assert facilities.slots == {"station": "METRO_GUINDY", "transport_mode": "metro", "facility_type": "parking"}
    access = extractor.extract("गिंडी metro पर wheelchair सुविधा?", "station_accessibility")
    assert access.slots["accessibility_feature"] == "wheelchair"
    assert access.slots["station"] == "METRO_GUINDY"
    ticket = extractor.extract("smart card policy for metro", "ticketing_and_passes")
    assert ticket.slots["ticket_type"] == "smart_card"
    fare = extractor.extract("bus fare for stage 4", "fare_calculation")
    assert fare.slots["stage_number"] == 4
    nearest = extractor.extract("nearest metro to Marina Beach", "nearest_transport")
    assert nearest.slots["landmark"] == "PLACE_MARINA"
    assert nearest.slots["transport_mode"] == "metro"


def test_explicit_and_ambiguous_time_are_separate(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    extractor = T3SlotExtractor(CanonicalResolver(canonical_db))
    explicit = extractor.extract("metro departure at Guindy at 8 PM", "scheduled_departure")
    assert explicit.slots["time"] == "20:00:00"
    assert explicit.clarification_reason is None
    bare = extractor.extract("metro departure at Guindy at 8 baje", "scheduled_departure")
    assert bare.slots["time"] == ["08:00:00", "20:00:00"]
    assert bare.clarification_reason == "temporal_ambiguity"
    kal = extractor.extract("kal ka schedule at Guindy metro", "scheduled_departure")
    assert kal.slots["temporal_relative"] == "kal"
    assert kal.clarification_reason == "temporal_ambiguity"


def test_first_and_last_requests_keep_distinguishing_timing_type(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    extractor = T3SlotExtractor(CanonicalResolver(canonical_db))
    first = extractor.extract("first metro from Guindy", "first_and_last_service")
    last = extractor.extract("last metro from Guindy", "first_and_last_service")
    assert first.slots["timing_type"] == "first"
    assert last.slots["timing_type"] == "last"


@pytest.mark.parametrize("query,want", [
    ("raat 12 baje", "00:00:00"),
    ("raat 1 baje", "01:00:00"),
    ("raat 8 baje", "20:00:00"),
])
def test_night_time_never_turns_overnight_into_daytime(canonical_db, query, want):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        f"Guindy metro {query} departure", "scheduled_departure")
    assert result.slots["time"] == want


def test_english_bare_oclock_asks_for_am_pm(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "Guindy metro departure at 8 o'clock", "scheduled_departure")
    assert result.slots["time"] == ["08:00:00", "20:00:00"]
    assert result.clarification_reason == "temporal_ambiguity"


def test_multimodal_modes_are_preserved_without_inventing_one_mode(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "bus and metro from Guindy to Central", "multimodal_route")
    assert result.requested_modes == ("bus", "metro")
    assert "transport_mode" not in result.slots
    assert result.slots["origin"] == "HUB_GUINDY"


def test_interchange_mode_pair_is_extracted_in_order(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "transfer from metro to bus", "interchange_transfer")
    assert result.slots == {"mode_from": "metro", "mode_to": "bus"}


def test_unknown_landmark_has_no_canonical_slot(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "nearest bus to unknownlandmark", "nearest_transport")
    assert "landmark" not in result.slots
    assert "locality" not in result.slots


@pytest.mark.parametrize("query,want", [
    ("बस २१जी के स्टॉप", "21G"),
    ("route 102-A stops", "102A"),
    ("bus 29C-ET stops", "29C-ET"),
])
def test_route_code_normalization_preserves_meaningful_suffixes(canonical_db, query, want):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(query, "route_stop_sequence")
    assert result.slots["route_number"] == want


@pytest.mark.parametrize("query", ["route 102 stops", "bus 102 to Guindy", "bus 102 from Guindy"])
def test_route_number_does_not_absorb_following_word(canonical_db, query):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(query, "route_stop_sequence")
    assert result.slots["route_number"] == "102"


def test_via_waypoint_is_not_mistaken_for_destination(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "from Guindy via Tambaram to Marina Beach", "point_to_point_route")
    assert result.slots["origin"] == "HUB_GUINDY"
    assert result.slots["via"] == "HUB_TAMBARAM"
    assert result.slots["destination"] == "PLACE_MARINA"


def test_trailing_via_waypoint_does_not_replace_destination(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(
        "from Guindy to Marina Beach via Tambaram", "point_to_point_route")
    assert result.slots["origin"] == "HUB_GUINDY"
    assert result.slots["destination"] == "PLACE_MARINA"
    assert result.slots["via"] == "HUB_TAMBARAM"


@pytest.mark.parametrize("query", ["bus 102 - A stops", "102 A bus stops"])
def test_spaced_route_suffix_remains_distinct(canonical_db, query):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    result = T3SlotExtractor(CanonicalResolver(canonical_db)).extract(query, "route_stop_sequence")
    assert result.slots["route_number"] == "102A"


def test_contextual_evening_and_line_name_normalize(canonical_db):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    extractor = T3SlotExtractor(CanonicalResolver(canonical_db))
    evening = extractor.extract("Guindy metro raat 8 baje departure", "scheduled_departure")
    assert evening.slots["time"] == "20:00:00"
    assert evening.clarification_reason is None
    frequency = extractor.extract("Green Line frequency", "service_frequency")
    assert frequency.slots["line_name"] == "Green Line"


def test_extracted_slots_conform_to_dispatch_contract(canonical_db):
    from src.nlp_v2.contracts import validate_intent_slots, validate_slots
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    extractor = T3SlotExtractor(CanonicalResolver(canonical_db))
    for query, intent in [
        ("from Guindy to Central by metro", "point_to_point_route"),
        ("Does bus 29C stop at Guindy?", "route_stop_membership"),
        ("parking at Guindy metro", "station_facilities"),
        ("smart card for metro", "ticketing_and_passes"),
        ("nearest metro to Marina Beach", "nearest_transport"),
        ("Guindy metro at 8 baje", "scheduled_departure"),
    ]:
        result = extractor.extract(query, intent)
        validate_slots(result.slots)
        validate_intent_slots(intent, result.slots)


def test_shipped_kb_central_alias_does_not_silently_become_rail_only():
    from src.nlp_v2.entities import CanonicalResolver

    resolver = CanonicalResolver()
    span = resolver.find_spans("central")[0]
    result = resolver.resolve(span, "destination", "point_to_point_route")
    assert result.candidates
    assert all(candidate.kind == "hub" for candidate in result.candidates)


def test_shipped_kb_place_with_city_suffix_matches_common_name():
    from src.nlp_v2.entities import CanonicalResolver

    resolver = CanonicalResolver()
    spans = resolver.find_spans("nearest metro to Marina Beach")
    place_span = next(span for span in spans if span.surface == "marina beach")
    result = resolver.resolve(place_span, "landmark", "nearest_transport")
    assert result.entity_id == "OSM_POI_12137617372"
