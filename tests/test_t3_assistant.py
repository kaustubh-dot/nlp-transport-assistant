"""T3 assistant contract tests using synthetic commuter questions."""

import pytest

from src.nlp_v2.contracts import IntentPrediction


class FixedClassifier:
    def __init__(self, intent):
        self.intent = intent
        self.queries = []

    def predict(self, query):
        self.queries.append(query)
        return IntentPrediction(self.intent, (self.intent,), 0.9)


@pytest.mark.parametrize('query', [
    'Guindy metro to Nandanam route please, fare nahi pooch raha',
    'गिंडी से Nandanam मेट्रो का रास्ता चाहिए, किराया नहीं पूछ रहा।',
    'Guindy to Nandanam metro route please, not asking for fare.',
])
def test_negated_selected_goal_cannot_execute_a_factual_answer(resolver, query):
    from src.nlp_v2.assistant import T3Assistant

    classifier = FixedClassifier('fare_calculation')
    reply = T3Assistant(classifier=classifier, resolver=resolver).process_query(query)
    assert classifier.queries == [query]
    assert reply.status == 'clarification'
    assert reply.operation is None
    assert reply.clarification_reason == 'intent_ambiguity'
    assert 'amount' not in reply.data


def test_positive_fare_is_not_blocked_by_negated_live_goal(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier('fare_calculation'), resolver=resolver).process_query(
        'Deluxe bus stage 4 fare please, live status nahi chahiye')
    assert reply.status == 'ok'
    assert reply.data['amount'] == 17


def test_multiple_hindi_goals_keep_live_location_with_intervening_mode(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier('route_stop_sequence'), resolver=resolver).process_query(
        '२७डी बस के सभी स्टॉप बताओ और अभी बस कहाँ है यह भी बताओ')
    assert reply.status == 'clarification'
    assert reply.clarification_reason == 'multiple_goals'
    assert set(reply.candidate_intents) == {'route_stop_sequence', 'realtime_status_query'}
    assert reply.operation is None


@pytest.fixture(scope="module")
def resolver():
    from src.nlp_v2.entities import CanonicalResolver

    return CanonicalResolver()


@pytest.mark.parametrize("query", [
    "Which bus route 102 stops at Guindy?",
    "बस 102 गिंडी पर रुकती है क्या?",
    "102 bus gindi pe rukti hai kya?",
    "बस 102 Guindy पर रुकती है?",
    "bus 102 gindi stop pls",
])
def test_multilingual_queries_follow_one_t3_path(resolver, query):
    from src.nlp_v2.assistant import T3Assistant

    classifier = FixedClassifier("route_stop_membership")
    assistant = T3Assistant(classifier=classifier, resolver=resolver)
    reply = assistant.process_query(query)
    assert classifier.queries == [query]
    assert reply.intent == "route_stop_membership"
    if reply.clarification_reason == "entity_ambiguity":
        assert reply.operation is None and reply.candidate_entities
    else:
        assert reply.operation == "CHECK_STOP_ON_ROUTE"
    assert reply.status in {"ok", "clarification", "unavailable"}
    assert reply.response_text


def test_missing_origin_prompts_for_exact_slot(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("point_to_point_route"), resolver=resolver).process_query(
        "How do I travel to Guindy?"
    )
    assert reply.status == "clarification"
    assert "origin" in reply.missing_slots


def test_entity_ambiguity_precedes_missing_slot(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("point_to_point_route"), resolver=resolver).process_query(
        "How to go from Guindy to Central?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "entity_ambiguity"
    assert reply.candidate_entities


def test_out_of_scope_and_realtime_are_terminal(resolver):
    from src.nlp_v2.assistant import T3Assistant

    oos = T3Assistant(classifier=FixedClassifier("out_of_scope"), resolver=resolver).process_query("Tell me a joke")
    live = T3Assistant(classifier=FixedClassifier("realtime_status_query"), resolver=resolver).process_query("Live bus status?")
    assert oos.status == "out_of_scope"
    assert live.status == "unavailable"
    assert "live" in live.response_text.lower()


def test_empty_query_is_structured_error(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("out_of_scope"), resolver=resolver).process_query("  ")
    assert reply.status == "error"
    assert reply.intent is None


def test_deluxe_fare_is_not_silently_ordinary(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("fare_calculation"), resolver=resolver).process_query("What is the deluxe bus fare for stage 4?")
    assert reply.status == "ok"
    assert reply.data["service_type"] == "Deluxe Services"
    assert reply.data["amount"] == 17


def test_timing_incompatible_destination_is_not_ignored(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("first_and_last_service"), resolver=resolver).process_query("Last bus from Poonamallee Bus Terminus to Chennai Beach?")
    assert reply.slots["destination"] == "RAIL_CHENNAI_BEACH"
    assert reply.status == "unavailable"


def test_explicit_off_route_stop_is_preserved_with_incomplete_variant(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("route_stop_membership"), resolver=resolver).process_query("Does bus 102 stop at Poonamallee Bus Terminus?")
    assert reply.slots['stop'] == 'BUS_5821'
    assert reply.status == 'unavailable'
    assert reply.data['reason'] == 'membership_topology_incomplete'


@pytest.mark.parametrize("query", [
    "What is the bus fare for stage 4 and when is the last bus from Poonamallee Bus Terminus?",
    "बस का किराया और आखिरी बस कब है?",
    "bus kiraya aur last bus kab hai?",
])
def test_explicit_conjoined_transport_goals_require_choice(resolver, query):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("fare_calculation"), resolver=resolver).process_query(query)
    assert reply.status == "clarification"
    assert reply.clarification_reason == "multiple_goals"
    assert set(reply.candidate_intents) == {"fare_calculation", "first_and_last_service"}


def test_coordinated_location_names_do_not_create_multiple_goals(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("fare_calculation"), resolver=resolver).process_query("What is the metro fare between Guindy and Central?")
    assert reply.clarification_reason != "multiple_goals"


@pytest.mark.parametrize("query", [
    "List all stops on bus route 102 and indicate the first and last stops.",
    "List stops on bus route 102 and show the first bus stop.",
])
def test_route_endpoint_qualifiers_are_not_service_time_goals(resolver, query):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier("route_stop_sequence"), resolver=resolver).process_query(query)
    assert reply.status == "ok"
    assert reply.operation == "LIST_ROUTE_STOPS"


@pytest.mark.parametrize('query', [
    'List stops on bus route 102 and list stops on bus route 25R',
    'List stops on bus route 102 and show stops on bus route 25R',
    'बस रूट १०२ के सभी स्टॉप बताइए और बस रूट २५आर के सभी स्टॉप बताइए',
    'list stops bs 102 aur list stops bs 25R',
    'List stops on bus route 102 and 25R',
    'बस रूट १०२ के सभी स्टॉप बताइए और २५आर',
])
def test_repeated_explicit_same_operation_requests_cannot_drop_second_goal(resolver, query):
    from src.nlp_v2.assistant import T3Assistant
    r=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),resolver=resolver).process_query(query)
    assert r.status=='clarification' and r.clarification_reason=='multiple_goals'
    assert r.intent is None and r.operation is None and not r.data
    assert r.candidate_intents==('route_stop_sequence',)


def test_single_request_with_repeated_fare_noun_is_not_two_explicit_questions(resolver):
    from src.nlp_v2.assistant import T3Assistant
    r=T3Assistant(classifier=FixedClassifier('fare_calculation'),resolver=resolver).process_query(
        'What is the ordinary bus stage 7 fare and the fare class?')
    assert r.clarification_reason!='multiple_goals'


def test_relative_day_ambiguity_is_kept_separate_from_missing_slots(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("first_and_last_service"), resolver=resolver).process_query(
        "Last bus kal?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "temporal_ambiguity"


def test_classifier_multi_goal_clarification_is_preserved(resolver):
    from src.nlp_v2.assistant import T3Assistant

    class MultipleGoals:
        def predict(self, query):
            return IntentPrediction(None, ("fare_calculation", "scheduled_departure"), 0.5, "multiple_goals")

    reply = T3Assistant(classifier=MultipleGoals(), resolver=resolver).process_query(
        "What is the fare and when does the bus leave?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "multiple_goals"
    assert reply.candidate_intents == ("fare_calculation", "scheduled_departure")


def test_primary_label_with_multiple_goals_precedes_entity_extraction(resolver):
    from src.nlp_v2.assistant import T3Assistant

    class PrimaryWithMultipleGoals:
        def predict(self, query):
            return IntentPrediction(
                "point_to_point_route", ("point_to_point_route", "fare_calculation"),
                0.72, "multiple_goals",
            )

    reply = T3Assistant(classifier=PrimaryWithMultipleGoals(), resolver=resolver).process_query(
        "How to go from Guindy to Central and what is the fare?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "multiple_goals"


def test_service_failure_becomes_safe_error(resolver):
    from src.nlp_v2.assistant import T3Assistant

    class BrokenService:
        def execute(self, operation, slots):
            raise OSError("internal secret path")

    reply = T3Assistant(
        classifier=FixedClassifier("nearest_transport"), resolver=resolver, service=BrokenService(),
    ).process_query("Where is the nearest metro station to Marina Beach?")
    assert reply.status == "error"
    assert "secret" not in reply.response_text


def test_departure_text_preserves_route_time_associations():
    from src.nlp_v2.assistant import _answer
    from src.nlp_v2.dispatch import DispatchResult

    result = DispatchResult(
        intent="scheduled_departure", operation="GET_SCHEDULED_DEPARTURES", status="ok",
        slots={}, acceptable_labels=("scheduled_departure",), confidence=0.9,
        message="Published only; verify with operator.",
        data={"departures": [
            {"route_name": "70G", "time": "02:47:00"},
            {"route_name": "11G R", "time": "04:35:00"},
        ]},
    )
    text = _answer(result)
    assert "70G at 02:47:00" in text
    assert "11G R at 04:35:00" in text
    assert "verify with operator" in text


@pytest.mark.parametrize('intent,query,operation',[
    ('ticketing_and_passes','Monthly bus pass renewal rules at Guindy?', 'GET_TICKETING_POLICY'),
    ('station_facilities','Where are the metro cloak rooms?', 'GET_STATION_FACILITY'),
    ('station_accessibility','Which metro stations have verified lifts?', 'GET_ACCESSIBILITY_INFO'),
    ('interchange_transfer','Verified metro to suburban transfer at Guindy?', 'GET_INTERCHANGE_DETAILS'),
    ('multimodal_route','Bus plus metro from Guindy to Chennai Beach?', 'PLAN_MULTIMODAL_ROUTE'),
])
def test_absent_capability_does_not_ask_for_non_actionable_entities(resolver,intent,query,operation):
    from src.nlp_v2.assistant import T3Assistant
    r=T3Assistant(classifier=FixedClassifier(intent),resolver=resolver).process_query(query)
    assert r.status == 'unavailable'
    assert r.operation == operation
    assert not r.missing_slots and not r.candidate_entities
    assert r.data.get('reason')


def test_capability_preflight_preserves_explicit_multiple_goals(resolver):
    from src.nlp_v2.assistant import T3Assistant
    r=T3Assistant(classifier=FixedClassifier('ticketing_and_passes'),resolver=resolver).process_query(
        'Monthly pass rules and the bus fare for stage 7 please')
    assert r.status == 'clarification' and r.clarification_reason == 'multiple_goals'


def test_capability_database_failure_returns_safe_error(tmp_path,resolver):
    from src.nlp_v2.assistant import T3Assistant
    from src.nlp_v2.domain import CanonicalTransitService
    import sqlite3
    p=tmp_path/'empty.db'; sqlite3.connect(p).close()
    r=T3Assistant(classifier=FixedClassifier('station_accessibility'),resolver=resolver,
                  service=CanonicalTransitService(p)).process_query('Lift at Guindy?')
    assert r.status == 'error'
    assert 'sqlite' not in r.response_text.lower() and str(p) not in r.response_text


@pytest.mark.parametrize('override', ['handler', 'execute'])
def test_extended_canonical_service_is_not_vetoed_by_base_preflight(resolver, override):
    from src.nlp_v2.assistant import T3Assistant
    from src.nlp_v2.domain import CanonicalTransitService
    from src.nlp_v2.dispatch import ServiceResult

    class ExtendedService(CanonicalTransitService):
        pass

    def supported(*args):
        return ServiceResult('ok', {'policy': 'Synthetic test policy', 'source': 'test'}, 'Policy found.')
    setattr(ExtendedService, '_ticketing' if override == 'handler' else 'execute', supported)
    reply = T3Assistant(classifier=FixedClassifier('ticketing_and_passes'), resolver=resolver,
                        service=ExtendedService()).process_query('Monthly bus pass rules?')
    assert reply.status == 'ok'
    assert reply.data['source'] == 'test'


@pytest.mark.parametrize('message', [{'unexpected': 'dictionary'}, None, 42])
def test_malformed_preflight_message_is_safe_error(resolver, message):
    from src.nlp_v2.assistant import T3Assistant
    from src.nlp_v2.dispatch import ServiceResult

    class MalformedService:
        def preflight(self, operation):
            return ServiceResult('unavailable', {}, message)

    reply = T3Assistant(classifier=FixedClassifier('ticketing_and_passes'), resolver=resolver,
                        service=MalformedService()).process_query('Monthly bus pass rules?')
    assert reply.status == 'error'
    assert isinstance(reply.response_text, str)
    assert reply.intent == 'ticketing_and_passes'
    assert reply.operation == 'GET_TICKETING_POLICY'


@pytest.mark.parametrize('intent,query', [
    ('point_to_point_route', 'Bus and metro route from Island ground Terminus to Annasquare?'),
    ('nearest_transport', 'Nearest bus and metro station to Marina Beach?'),
    ('mode_availability', 'Are bus and metro available from Island ground Terminus to Annasquare?'),
])
def test_atomic_operation_preserves_multiple_requested_modes(resolver, intent, query):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier(intent), resolver=resolver).process_query(query)
    assert reply.status == 'clarification'
    assert 'transport_mode' in reply.missing_slots
    assert set(reply.data['requested_modes']) == {'bus', 'metro'}


def test_exact_stop_name_is_a_nearest_anchor_not_a_target_mode_filter(resolver):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('nearest_transport'), resolver=resolver).process_query(
        'Nearest metro station to Poonamallee Bus Terminus?')
    assert reply.status == 'ok'
    assert reply.slots['landmark'] == 'BUS_5821'
    assert all(row['mode'] == 'metro' for row in reply.data['stops'])


@pytest.mark.parametrize('clock', ['10 pm', '22:00'])
def test_availability_preserves_requested_clock_scope(resolver, clock):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('mode_availability'), resolver=resolver).process_query(
        f'Is bus available from Island ground Terminus to Annasquare at {clock}?')
    assert reply.status == 'unavailable'
    assert reply.slots['time'] == '22:00:00'


def test_invalid_availability_clock_cannot_become_static_success(resolver):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('mode_availability'), resolver=resolver).process_query(
        'Is bus available from Island ground Terminus to Annasquare at 25:30 AM?')
    assert reply.status == 'clarification'
    assert reply.clarification_reason == 'temporal_ambiguity'


@pytest.mark.parametrize('route,status', [('999', 'unavailable'), ('102', 'ok')])
def test_availability_preserves_explicit_route_constraint(resolver, route, status):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('mode_availability'), resolver=resolver).process_query(
        f'Is bus {route} available from Island ground Terminus to Annasquare?')
    assert reply.slots.get('route_number') == route
    assert reply.status == status
    if status == 'ok':
        assert all(r['route_name'].replace(' ', '') == route for r in reply.data['routes'])


def test_availability_via_does_not_replace_destination(resolver):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('mode_availability'), resolver=resolver).process_query(
        'Is bus available from Island ground Terminus to Annasquare via Kelambakkam Bus Terminal?')
    assert reply.slots.get('destination') == 'BUS_11192'
    assert reply.slots.get('via') == 'BUS_6099'
    assert reply.status == 'unavailable'


@pytest.mark.parametrize('intent,query', [
    ('route_stop_sequence', 'List stops on bus route 102 and bus 25R'),
    ('fare_calculation', 'What is the ordinary bus fare for stage 4 and stage 7?'),
    ('fare_calculation', 'Ordinary bus fare for stage 4 and 7?'),
    ('route_stop_membership', 'Does bus 102 stop at Island ground Terminus and Annasquare?'),
    ('scheduled_departure', 'Show bus departures at 8 AM and 9 AM from Poonamallee Bus Terminus'),
    ('scheduled_departure', 'Show bus departures at 8 and 9 AM from Poonamallee Bus Terminus'),
    ('scheduled_departure', 'बस पूनमल्ली बस टर्मिनस से सुबह ८ बजे और ९ बजे कब छूटेगी?'),
    ('scheduled_departure', 'Show bus departures at 08:00 and 09:00 from Poonamallee Bus Terminus'),
    ('scheduled_departure', 'Show bus departures on 2026-10-06 and 2026-10-07 from Poonamallee Bus Terminus'),
    ('route_stop_sequence', 'List stops on bus 102 and bus २५क्यू'),
    ('scheduled_departure', 'Show bus departures today and tomorrow from Poonamallee Bus Terminus'),
    ('scheduled_departure', 'Show bus departures आज और कल from Poonamallee Bus Terminus'),
    ('route_stop_sequence', 'List stops on bus 102 and Blue Line'),
    ('route_stop_sequence', 'List stops on Blue Line and Green Line'),
    ('fare_calculation', 'Ordinary bus fare for stage 4 or stage 7?'),
    ('nearest_transport', 'Where is the nearest metro station to Marina Beach and Poonamallee Bus Terminus?'),
])
def test_single_operation_never_drops_coordinated_scopes(resolver, intent, query):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier(intent), resolver=resolver).process_query(query)
    assert reply.status == 'clarification'
    assert reply.clarification_reason == 'multiple_goals'
    assert not reply.data.get('amount') and not reply.data.get('departures')


@pytest.mark.parametrize('marker', ['via', 'होते हुए', 'hote hue'])
def test_unknown_explicit_waypoint_is_required_not_dropped(resolver, marker):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('point_to_point_route'), resolver=resolver).process_query(
        f'Bus route from Island ground Terminus to Annasquare {marker} Unknownville?')
    assert reply.status == 'clarification'
    assert reply.missing_slots == ('via',)
    assert 'waypoint' in reply.response_text
    assert reply.slots['destination'] == 'BUS_11192'


@pytest.mark.parametrize('intent', ['point_to_point_route', 'mode_availability', 'scheduled_departure', 'first_and_last_service'])
@pytest.mark.parametrize('code', ['१०२ क्यू', '१०२क्यू', '102 Rजी', '102#Q'])
def test_unparseable_explicit_optional_route_cannot_widen_results(resolver, intent, code):
    from src.nlp_v2.assistant import T3Assistant
    query = (f'Is bus {code} available from Island ground Terminus to Annasquare?' if intent in {'point_to_point_route', 'mode_availability'}
             else f'Last bus {code} departures from Poonamallee Bus Terminus?')
    reply = T3Assistant(classifier=FixedClassifier(intent), resolver=resolver).process_query(query)
    assert reply.status == 'clarification'
    assert reply.missing_slots == ('route_number',)
    assert 'route number' in reply.response_text
    assert not reply.data.get('routes')


@pytest.mark.parametrize('scope', ['before 8 AM', 'between 8 AM and 9 AM', '8 बजे से पहले', '8 baje se pehle'])
def test_unsupported_temporal_comparator_cannot_become_after_departures(resolver, scope):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('scheduled_departure'), resolver=resolver).process_query(
        f'Show bus departures {scope} from Poonamallee Bus Terminus')
    assert reply.status in {'unavailable', 'clarification'}
    assert not reply.data.get('departures')


def test_unknown_waypoint_does_not_prompt_for_absent_metro_topology(resolver):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('point_to_point_route'), resolver=resolver).process_query(
        'Metro route from Central to Airport via Unknownville?')
    assert reply.status == 'unavailable'


def test_repeated_scope_value_still_answers_one_stage(resolver):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('fare_calculation'), resolver=resolver).process_query(
        'What is the ordinary bus fare for stage 4 (stage 4)?')
    assert reply.status == 'ok' and reply.data['amount'] == 8


@pytest.mark.parametrize('code', ['१०२क्यू bus', '१०२ क्यू बस'])
def test_rejected_route_before_mode_preserves_unicode_suffix(resolver, code):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('mode_availability'), resolver=resolver).process_query(
        f'{code} available from Island ground Terminus to Annasquare?')
    assert reply.status == 'clarification' and reply.missing_slots == ('route_number',)


@pytest.mark.parametrize('scope', ['2026-10-06', '08:00'])
def test_temporal_number_before_bus_is_not_a_route_code(resolver, scope):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('scheduled_departure'), resolver=resolver).process_query(
        f'Show departures at {scope} bus from Poonamallee Bus Terminus')
    assert reply.status == 'ok'
    assert 'route_number' not in reply.slots


def test_repeated_aliases_of_one_nearest_anchor_are_one_scope(resolver):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('nearest_transport'), resolver=resolver).process_query(
        'Nearest metro station to Marina Beach (मरीना बीच)?')
    assert reply.status == 'ok'
    assert reply.data['anchor'] == 'OSM_POI_12137617372'

@pytest.mark.parametrize('query', [
    'क्या Cedar Quay से bus नहीं चलती?',
    'Cedar Quay bus chalti nahi kya?',
])
def test_negative_availability_question_is_not_a_negated_user_goal(query):
    from src.nlp_v2.assistant import selected_goal_negated
    assert selected_goal_negated(query, 'mode_availability') is False


def test_negated_route_stop_list_cannot_answer_live_location_request(resolver):
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=FixedClassifier('route_stop_sequence'), resolver=resolver).process_query(
        '83C ka current location chahiye, route stops mat bhejna')
    assert reply.status == 'clarification'
    assert reply.operation is None
    assert reply.data['reason'] == 'negated_selected_goal'
