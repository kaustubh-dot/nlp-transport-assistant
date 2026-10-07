"""Synthetic response policy regressions; no evaluation/reference inputs."""
import pytest
from src.nlp_v2.contracts import IntentPrediction
from src.nlp_v2.dispatch import ServiceResult, dispatch

class FixedClassifier:
    def __init__(self, intent): self.intent = intent
    def predict(self, query): return IntentPrediction(self.intent, (self.intent,), .9)

@pytest.fixture(scope='module')
def resolver():
    from src.nlp_v2.entities import CanonicalResolver
    return CanonicalResolver()

@pytest.mark.parametrize('intent,query,reason', [
    ('point_to_point_route', 'How to go to Guindy?', 'missing_execution_slot'),
    ('point_to_point_route', 'How to go from Guindy to Central?', 'entity_ambiguity'),
    ('first_and_last_service', 'Last bus kal?', 'temporal_ambiguity'),
    ('fare_calculation', 'Bus fare and last bus time please', 'multiple_goals'),
    ('ticketing_and_passes', 'Monthly bus pass rules?', 'unsupported_source'),
    ('realtime_status_query', 'Live bus delay?', 'external_source_required'),
    ('out_of_scope', 'Tell me a poem', 'out_of_scope'),
    ('fare_calculation', 'Bus stage 7 fare?', 'answered'),
])
def test_public_outcome_categories(resolver,intent,query,reason):
    from src.nlp_v2.assistant import T3Assistant
    from app.api import public_reply
    reply=T3Assistant(classifier=FixedClassifier(intent),resolver=resolver).process_query(query)
    assert public_reply(reply)['outcome_reason'] == reason

@pytest.mark.parametrize('query', ['', '?!...'])
def test_malformed_request_is_distinct_from_temporary_failure(resolver,query):
    from src.nlp_v2.assistant import T3Assistant
    from app.api import public_reply
    classifier=FixedClassifier('fare_calculation')
    reply=T3Assistant(classifier=classifier,resolver=resolver).process_query(query)
    assert reply.status == 'error'
    assert public_reply(reply)['outcome_reason'] == 'malformed_request'

@pytest.mark.parametrize('intent,query,phrase', [
    ('point_to_point_route', 'How to go to Guindy?', 'starting stop'),
    ('service_frequency', 'Bus route 25R frequency?', 'boarding stop'),
    ('route_stop_sequence', 'List bus stops?', 'route number or line name'),
    ('nearest_transport', 'Nearest metro station?', 'nearby landmark'),
    ('fare_calculation', 'Bus fare?', 'fare stage number'),
])
def test_missing_prompts_name_actionable_inputs(resolver,intent,query,phrase):
    from src.nlp_v2.assistant import T3Assistant
    reply=T3Assistant(classifier=FixedClassifier(intent),resolver=resolver).process_query(query)
    assert reply.status == 'clarification'
    assert phrase in reply.response_text.lower()
    assert '_or_' not in reply.response_text

@pytest.mark.parametrize('marker',['parso','परसों'])
def test_direct_dispatch_preserves_ambiguous_two_day_marker(marker):
    result=dispatch(IntentPrediction('scheduled_departure',('scheduled_departure',),.9),
                    {'station':'BUS_A','temporal_relative':marker})
    assert result.status == 'clarification' and result.reason == 'temporal_ambiguity'

@pytest.mark.parametrize('message',[{},None,42])
def test_invalid_service_message_is_safe_known_operation_error(message):
    class Service:
        def execute(self,operation,slots): return ServiceResult('unavailable',{},message)
    result=dispatch(IntentPrediction('scheduled_departure',('scheduled_departure',),.9),
                    {'station':'BUS_A'},Service())
    assert result.status == 'error'
    assert result.operation == 'GET_SCHEDULED_DEPARTURES' and isinstance(result.message,str)


def test_frequency_requests_destination_only_when_it_can_filter_direction():
    class Service:
        def execute(self,operation,slots):
            return ServiceResult('unavailable',{'reason':'frequency_direction_or_stop_ambiguous'},'Ambiguous timetable scope.')
    p=IntentPrediction('service_frequency',('service_frequency',),.9)
    slots={'station':'BUS_A','route_number':'88'}
    r=dispatch(p,slots,Service())
    assert r.status == 'clarification' and r.reason == 'missing_slot'
    assert r.missing_slots == ('destination',)
    assert dispatch(p,{**slots,'destination':'BUS_B'},Service()).status == 'unavailable'


def test_first_last_does_not_discard_explicit_clock_scope():
    from src.nlp_v2.domain import CanonicalTransitService
    r=CanonicalTransitService().execute('GET_FIRST_LAST_SERVICE',{'station':'BUS_5821','time':'08:00:00'})
    assert r.status == 'unavailable'
    assert r.data['reason'] == 'first_last_clock_scope_unsupported'


def test_frontend_rejects_unknown_or_nonstring_outcome_reasons():
    from app.frontend_contract import valid_reply
    base={'status':'unavailable','response_text':'Unavailable'}
    assert valid_reply({**base,'outcome_reason':'unsupported_source'})
    assert not valid_reply({**base,'outcome_reason':{'secret':42}})
    assert not valid_reply({**base,'outcome_reason':'guess'})
    assert not valid_reply({**base,'outcome_reason':None})


def test_intent_uncertainty_and_temporary_failure_are_distinct(resolver):
    from src.nlp_v2.assistant import T3Assistant
    from app.api import public_reply
    class Uncertain:
        def predict(self,query):
            return IntentPrediction(None,('point_to_point_route','fare_calculation'),.5,'intent_ambiguity')
    class Broken:
        def predict(self,query): raise OSError('secret path')
    uncertain=T3Assistant(classifier=Uncertain(),resolver=resolver).process_query('Transport options?')
    broken=T3Assistant(classifier=Broken(),resolver=resolver).process_query('Transport options?')
    assert public_reply(uncertain)['outcome_reason'] == 'intent_ambiguity'
    assert public_reply(broken)['outcome_reason'] == 'temporary_service_unavailability'
    assert 'secret' not in broken.response_text


def test_malformed_api_query_uses_client_error_not_service_outage(resolver):
    import json
    from app.api import handle_request
    from src.nlp_v2.assistant import T3Assistant
    class MustNotPredict:
        def predict(self,query): raise AssertionError('Malformed request reached inference')
    body=json.dumps({'query':'?!...'}).encode()
    status,reply=handle_request('POST','/api/v2/query',{
        'content-type':'application/json','content-length':str(len(body))},body,
        T3Assistant(classifier=MustNotPredict(),resolver=resolver))
    assert status == 422
    assert reply['outcome_reason'] == 'malformed_request'


@pytest.mark.parametrize('intent,query', [
    ('point_to_point_route','Metro route from Guindy to Central?'),
    ('mode_availability','Is metro available from Guindy to Central?'),
    ('scheduled_departure','Published metro departure at Guindy?'),
])
def test_absent_mode_source_does_not_request_non_actionable_entities(resolver,intent,query):
    from src.nlp_v2.assistant import T3Assistant
    reply=T3Assistant(classifier=FixedClassifier(intent),resolver=resolver).process_query(query)
    assert reply.status == 'unavailable'
    assert reply.outcome_reason == 'unsupported_source'
    assert not reply.missing_slots and not reply.candidate_entities


def test_mode_capability_does_not_veto_extended_service(resolver):
    from src.nlp_v2.assistant import T3Assistant
    from src.nlp_v2.domain import CanonicalTransitService
    class Extended(CanonicalTransitService):
        def execute(self, operation, slots): return ServiceResult('ok',{},'Synthetic extension result.')
    reply=T3Assistant(classifier=FixedClassifier('scheduled_departure'),resolver=resolver,
                      service=Extended()).process_query('Metro departure at Chennai International Airport?')
    assert reply.status == 'ok'


def test_mode_capability_database_failure_is_safe_temporary_error(tmp_path,resolver):
    import sqlite3
    from src.nlp_v2.assistant import T3Assistant
    from src.nlp_v2.domain import CanonicalTransitService
    path=tmp_path/'empty.db';sqlite3.connect(path).close()
    reply=T3Assistant(classifier=FixedClassifier('point_to_point_route'),resolver=resolver,
                      service=CanonicalTransitService(path)).process_query('Metro route from Guindy to Central?')
    assert reply.status == 'error'
    assert reply.operation == 'PLAN_ROUTE'
    assert reply.outcome_reason == 'temporary_service_unavailability'
    assert str(path) not in reply.response_text


def test_mode_schedule_capability_requires_usable_departure(tmp_path):
    import sqlite3
    from src.nlp_v2.domain import CanonicalTransitService
    path=tmp_path/'null_schedule.db'
    with sqlite3.connect(path) as conn:
        conn.executescript('''
            CREATE TABLE transport_routes(route_id,mode,status);
            CREATE TABLE transport_stops(stop_id,mode);
            CREATE TABLE trips(trip_id,route_id);
            CREATE TABLE stop_times(trip_id,canonical_stop_id,departure_time);
            INSERT INTO transport_routes VALUES('R','metro','operational');
            INSERT INTO transport_stops VALUES('METRO_A','metro');
            INSERT INTO trips VALUES('T','R');
            INSERT INTO stop_times VALUES('T','METRO_A',NULL);
        ''')
    result=CanonicalTransitService(path).preflight_mode('GET_SCHEDULED_DEPARTURES','metro')
    assert result is not None and result.status == 'unavailable'
