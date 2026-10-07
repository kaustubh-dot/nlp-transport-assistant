"""Synthetic timetable contracts; no historical evaluation examples or labels."""

import sqlite3

import pytest

from src.nlp_v2.assistant import T3Assistant
from src.nlp_v2.contracts import IntentPrediction
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


class Classifier:
    def __init__(self, intent):
        self.intent = intent
        self.raw_queries = []

    def predict(self, query):
        self.raw_queries.append(query)
        return IntentPrediction(self.intent, (self.intent,), .9)


class Service:
    def __init__(self):
        self.calls = []

    def execute(self, operation, slots):
        self.calls.append((operation, slots))
        return ServiceResult('ok', {'first_departure':'06:00:00', 'last_departure':'23:00:00',
                                    'median_headway_minutes':10}, 'Synthetic published record.')


@pytest.mark.parametrize('intent', INTENTS)
@pytest.mark.parametrize('structure', [
    'from Alpha Terminal via Bravo Terminal to Charlie Terminal',
    'from Alpha Terminal to Charlie Terminal via Bravo Terminal',
    'to Charlie Terminal via Bravo Terminal from Alpha Terminal',
    'from Alpha Terminal via Unknown Place to Charlie Terminal',
    'from Alpha Terminal to Charlie Terminal via Unknown Place',
    'from Alpha Terminal via Bravo Terminal and Delta Terminal to Charlie Terminal',
    'from Alpha Terminal via Bravo Terminal to Charlie Terminal via Delta Terminal',
    'FROM Alpha Terminal, VIA Bravo Terminal; TO Charlie Terminal!',
    'from Alpha Terminal hote hue Bravo Terminal to Charlie Terminal',
    'from Alpha Terminal होते हुए Bravo Terminal to Charlie Terminal',
    'अल्फा स्टॉप से ब्रावो स्टॉप होते हुए चार्ली स्टॉप तक',
])
def test_waypoint_never_overwrites_destination_or_executes_partial_scope(resolver, intent, structure):
    query = f'bus route 25R schedule {structure} at 08:00 on 2026-10-06'
    extraction = T3SlotExtractor(resolver).extract(query, intent)
    assert extraction.slots['station'] == 'BUS_A'
    assert extraction.slots['destination'] == 'BUS_C'
    assert extraction.slots['route_number'] == '25R'
    assert extraction.slots['time'] == '08:00:00'
    assert extraction.slots['date'] == '2026-10-06'
    assert getattr(extraction, "unsupported_timetable_waypoint", False)
    # Every explicitly recognized mention remains ordered in extraction metadata.
    assert [s.start for s in extraction.spans] == sorted(s.start for s in extraction.spans)
    classifier, service = Classifier(intent), Service()
    reply = T3Assistant(classifier=classifier, resolver=resolver, service=service).process_query(query)
    assert reply.status == 'unavailable'
    assert 'waypoint' in reply.response_text.lower()
    assert reply.slots['destination'] == 'BUS_C'
    assert reply.data['reason'] == 'timetable_waypoint_scope_unsupported'
    assert not service.calls
    assert classifier.raw_queries == [query]


@pytest.mark.parametrize('intent', INTENTS)
@pytest.mark.parametrize('structure', [
    'from Alpha Terminal to Bravo Terminal and Charlie Terminal',
    'from Alpha Terminal to Bravo Terminal or Charlie Terminal',
    'Alpha Terminal, Bravo Terminal, Charlie Terminal',
    'अल्फा स्टॉप से ब्रावो स्टॉप और चार्ली स्टॉप',
])
def test_third_stop_requires_clarification_before_partial_timetable_dispatch(resolver, intent, structure):
    query = f'bus route 25R schedule {structure}'
    extraction = T3SlotExtractor(resolver).extract(query, intent)
    assert len(extraction.spans) == 3
    assert extraction.multiple_execution_scopes
    service = Service()
    reply = T3Assistant(classifier=Classifier(intent), resolver=resolver, service=service).process_query(query)
    assert reply.status == 'clarification'
    assert reply.clarification_reason == 'multiple_goals'
    assert not service.calls


@pytest.mark.parametrize('intent', INTENTS)
@pytest.mark.parametrize('structure', [
    'from Alpha Terminal from Bravo Terminal to Charlie Terminal via Delta Terminal',
    'from Alpha Terminal to Bravo Terminal to Charlie Terminal via Delta Terminal',
])
def test_conflicting_explicit_endpoint_roles_clarify_without_choosing_one(resolver, intent, structure):
    service = Service()
    reply = T3Assistant(classifier=Classifier(intent), resolver=resolver, service=service).process_query(
        f'bus route 25R schedule {structure}')
    assert reply.status == 'clarification'
    assert reply.clarification_reason == 'multiple_goals'
    assert not service.calls


@pytest.mark.parametrize('intent', INTENTS)
@pytest.mark.parametrize('structure,expected', [
    ('from Alpha Terminal to Charlie Terminal', {'station':'BUS_A','destination':'BUS_C'}),
    ('to Charlie Terminal from Alpha Terminal', {'station':'BUS_A','destination':'BUS_C'}),
    ('from Alpha Terminal', {'station':'BUS_A'}),
    ('अल्फा स्टॉप से चार्ली स्टॉप तक', {'station':'BUS_A','destination':'BUS_C'}),
])
def test_ordinary_timetable_dispatch_and_other_constraints_remain_unchanged(resolver, intent, structure, expected):
    query = f'bus route 25R schedule {structure} on 2026-10-06'
    extraction = T3SlotExtractor(resolver).extract(query, intent)
    for role, entity in expected.items():
        assert extraction.slots[role] == entity
    assert not extraction.multiple_execution_scopes
    service = Service()
    reply = T3Assistant(classifier=Classifier(intent), resolver=resolver, service=service).process_query(query)
    assert reply.status == 'ok'
    assert len(service.calls) == 1
    assert service.calls[0][1] == {**expected,'route_number':'25R','date':'2026-10-06','transport_mode':'bus'}


@pytest.mark.parametrize('intent', INTENTS)
def test_previous_extractor_metadata_shape_keeps_ordinary_dispatch(resolver, intent):
    from types import SimpleNamespace

    class PreviousExtractor:
        def extract(self, query, chosen_intent):
            result = T3SlotExtractor(resolver).extract(query, chosen_intent)
            return SimpleNamespace(**{key: value for key, value in vars(result).items()
                                      if key != 'unsupported_timetable_waypoint'})

    service = Service()
    reply = T3Assistant(classifier=Classifier(intent), resolver=resolver,
                        extractor=PreviousExtractor(), service=service).process_query(
                            'bus route 25R schedule from Alpha Terminal to Charlie Terminal')
    assert reply.status == 'ok'
    assert len(service.calls) == 1
