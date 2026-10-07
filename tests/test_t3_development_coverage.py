"""Development evaluator tests; all input records are synthetic."""

import json
from dataclasses import replace

import pytest

from src.nlp_v2.assistant import AssistantReply


def case(**changes):
    return {
        'id': 'dev-001', 'query': 'A fresh synthetic development question ' + changes.get('id', 'dev-001'),
        'language': 'EN', 'noise': 'clean', 'scenario': 'answerable',
        'provenance': 'Manually authored from canonical contract; no held-out targets',
        'intent': 'fare_calculation', 'operation': 'CALCULATE_FARE',
        'status': 'ok', 'slots': {'stage_number': 3}, 'evidence': 'fare',
        **changes,
    }


def reply(**changes):
    return AssistantReply(**{
        'status': 'ok', 'response_text': 'Published fare', 'raw_query': '',
        'normalized_query': '', 'intent': 'fare_calculation',
        'operation': 'CALCULATE_FARE', 'confidence': .9,
        'slots': {'stage_number': 3},
        'data': {'amount': 10, 'currency':'INR', 'source': 'SYNTHETIC_OFFICIAL',
                 'effective_date': '2020-01-01', 'provisional': True},
        **changes,
    })


def test_scoring_rejects_success_with_wrong_operation_entity_or_no_source():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    cases = [case(id=f'dev-{i}') for i in range(4)]
    replies = [reply(), reply(operation='LIST_ROUTE_STOPS'),
               reply(slots={'stage_number': 4}), reply(data={'amount': 10})]
    scores = score_cases(cases, replies)
    assert scores['intent_contract']['success'] == 4
    assert scores['operation_selection']['success'] == 3
    assert scores['slot_resolution'] == {'success': 3, 'count': 4, 'rate': .75}
    assert scores['answerable_coverage'] == {'success': 1, 'count': 4, 'rate': .25}
    assert scores['terminal_behavior']['success'] == 1
    assert scores['status_counts']['ok'] == 4


def test_clarification_metrics_use_gold_denominators_and_check_reason_inputs():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    cases = [case(status='clarification', clarification_reason='missing_slot',
                  missing_slots=['origin'], slots={}, evidence=None),
             case(id='dev-002'), case(id='dev-003')]
    replies = [reply(status='clarification', clarification_reason='entity_ambiguity'),
               reply(status='clarification'), reply()]
    scores = score_cases(cases, replies)
    assert scores['false_positive_clarification'] == {'success': 1, 'count': 2, 'rate': .5}
    assert scores['clarification_rate'] == pytest.approx(2/3)
    assert scores['terminal_behavior']['success'] == 1


def test_ambiguity_requires_candidates_and_temporal_candidates_are_gold_slots():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    c = case(status='clarification', clarification_reason='entity_ambiguity',
             require_candidates=True, slots={}, evidence=None)
    r = reply(status='clarification', clarification_reason='entity_ambiguity')
    assert score_cases([c], [r])['terminal_behavior']['success'] == 0
    assert score_cases([c], [replace(r, candidate_entities=('STOP_A', 'STOP_B'))])['terminal_behavior']['success'] == 1


def test_scoring_rejects_empty_unaligned_or_unknown_states():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    with pytest.raises(ValueError):
        score_cases([], [])
    with pytest.raises(ValueError):
        score_cases([case()], [])
    with pytest.raises(ValueError):
        score_cases([case()], [reply(status='invented')])


def test_fingerprint_guard_is_normalized_opaque_and_does_not_return_text(tmp_path):
    from scripts.nlp_v2.evaluate_development_coverage import heldout_fingerprints, fingerprint

    stress = tmp_path/'stress.csv'
    stress.write_text('query,T3_label\n"SYNTHETIC secret query!",fare_calculation\n')
    reference = tmp_path/'reference.json'
    reference.write_text(json.dumps({'a': {'query': 'Another synthetic query', 'gold': 'unused'}}))
    hashes = heldout_fingerprints(stress, reference)
    assert fingerprint('synthetic SECRET query') in hashes
    assert len(hashes) == 2
    assert all(len(value) == 64 and 'query' not in value for value in hashes)


def test_suite_rejects_hash_drift_and_duplicate_or_invalid_contract(tmp_path):
    from scripts.nlp_v2.evaluate_development_coverage import load_suite, validate_cases
    from src.nlp_v2.model import sha256_file

    path = tmp_path/'suite.json'
    path.write_text(json.dumps([case()]))
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'version': 1, 'suite_sha256': sha256_file(path),
        'canonical_database_sha256':'a'*64,'reference_date':'2026-10-07','count':1}))
    assert len(load_suite(path, manifest)) == 1
    path.write_text(json.dumps([case(query='Changed')]))
    with pytest.raises(ValueError, match='hash'):
        load_suite(path, manifest)
    for cases in ([case(), case()], [case(status='fabricated')],
                  [case(operation='PLAN_ROUTE')], [case(slots={'stage_number': 999})]):
        with pytest.raises(ValueError):
            validate_cases(cases)


def test_output_guard_refuses_existing_and_frozen_destination_before_model(tmp_path):
    from scripts.nlp_v2.evaluate_development_coverage import evaluate, ROOT

    (tmp_path/'existing.json').write_text('{}')
    with pytest.raises(ValueError, match='exists'):
        evaluate(tmp_path)
    with pytest.raises(ValueError, match='destination'):
        evaluate(ROOT/'reports/nlp_v2/gate_b2/forbidden')


def test_multiple_goals_preserve_null_primary_and_candidate_intents():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    c = case(intent=None, operation=None, status='clarification', slots={}, evidence=None,
             clarification_reason='multiple_goals',
             candidate_intents=['fare_calculation', 'first_and_last_service'])
    r = reply(status='clarification', intent=None, operation=None,
              clarification_reason='multiple_goals',
              candidate_intents=('fare_calculation', 'first_and_last_service'))
    assert score_cases([c], [r])['terminal_behavior']['success'] == 1
    assert score_cases([c], [replace(r,candidate_intents=('fare_calculation',))])['terminal_behavior']['success'] == 0


def test_gold_intent_diagnostic_handles_ambiguous_intents_without_loading_weights(tmp_path, monkeypatch):
    from scripts.nlp_v2 import evaluate_development_coverage as evaluator
    from src.nlp_v2.model import sha256_file

    c = case(intent=None, operation=None, status='clarification', slots={}, evidence=None,
             clarification_reason='intent_ambiguity',
             candidate_intents=['scheduled_departure','mode_availability'])
    suite = tmp_path/'suite.json'; suite.write_text(json.dumps([c]))
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'version':1,'suite_sha256':sha256_file(suite),
        'canonical_database_sha256':sha256_file(evaluator.DEFAULT_DB),'reference_date':'2026-10-07','count':1}))
    monkeypatch.setattr(evaluator,'SUITE',suite)
    monkeypatch.setattr(evaluator,'MANIFEST',manifest)
    monkeypatch.setattr(evaluator,'load_suite',lambda: [c])
    monkeypatch.setattr(evaluator,'heldout_fingerprints',lambda *args: set())
    report = evaluator.evaluate(tmp_path/'output',gold_intent=True)
    assert report['mode'] == 'gold_intent_downstream_diagnostic'
    assert report['classifier_accuracy_measured'] is False
    assert report['scores']['terminal_behavior']['success'] == 1


def test_production_coverage_labels_reply_intent_as_distinct_from_raw_accuracy(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from scripts.nlp_v2 import evaluate_development_coverage as evaluator
    monkeypatch.setattr(evaluator, 'load_suite', lambda: [case()])
    monkeypatch.setattr(evaluator, 'heldout_fingerprints', lambda *args: set())
    monkeypatch.setattr(evaluator, 'T3Assistant', lambda **kwargs: SimpleNamespace(process_query=lambda q: reply()))
    report = evaluator.evaluate(tmp_path/'output')
    assert report['classifier_accuracy_measured'] is False
    assert report['reply_intent_contract_measured'] is True


def test_membership_requires_source_provenance_not_just_route_ids():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    c=case(intent='route_stop_membership',operation='CHECK_STOP_ON_ROUTE',slots={},evidence='membership')
    r=reply(intent='route_stop_membership',operation='CHECK_STOP_ON_ROUTE',
            data={'on_route':True,'route_ids':['R1'],'provisional':True})
    assert score_cases([c],[r])['answerable_coverage']['success'] == 0
    r=replace(r,data={**r.data,'source':['SYNTHETIC_PUBLISHED']})
    assert score_cases([c],[r])['answerable_coverage']['success'] == 1


def test_clarification_does_not_accept_an_incompatible_selected_operation():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    c=case(status='clarification',clarification_reason='missing_slot',slots={},evidence=None)
    r=reply(status='clarification',clarification_reason='missing_slot',operation='PLAN_ROUTE')
    assert score_cases([c],[r])['terminal_behavior']['success'] == 0
    assert score_cases([c],[replace(r,operation=None)])['terminal_behavior']['success'] == 1


def test_real_suite_has_all_intents_in_all_language_classes():
    from scripts.nlp_v2.evaluate_development_coverage import load_suite
    from src.nlp_v2.contracts import T3_INTENTS

    cases=load_suite()
    for intent in T3_INTENTS:
        assert {c['language'] for c in cases if c['intent']==intent} >= {
            'EN','HI_DEVA','HI_LATN','HINGLISH_LATN','MIXED_SCRIPT_CS'}
    assert {c['status'] for c in cases} >= {'ok','clarification','unavailable','out_of_scope'}


@pytest.mark.parametrize('kind,data',[
    ('sequences',{'sequences':[{'source':'PUBLISHED'}],'provisional':True}),
    ('bounds',{'first_departure':None,'last_departure':None,'source':['PUBLISHED'],'provisional':True}),
    ('frequency',{'median_headway_minutes':None,'source':['PUBLISHED'],'provisional':True}),
    ('fare',{'amount':float('nan'),'source':'PUBLISHED','effective_date':'2020-01-01','provisional':True}),
    ('fare',{'amount':True,'source':'PUBLISHED','effective_date':'2020-01-01','provisional':True}),
])
def test_malformed_evidence_cannot_count_as_a_terminal_answer(kind,data):
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    intent,operation={
        'sequences':('route_stop_sequence','LIST_ROUTE_STOPS'),
        'bounds':('first_and_last_service','GET_FIRST_LAST_SERVICE'),
        'frequency':('service_frequency','GET_SERVICE_FREQUENCY'),
        'fare':('fare_calculation','CALCULATE_FARE'),
    }[kind]
    c=case(evidence=kind,slots={},intent=intent,operation=operation)
    assert score_cases([c],[reply(data=data,intent=intent,operation=operation)])['answerable_coverage']['success'] == 0


def test_negative_membership_checks_the_boolean_answer():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    c=case(intent='route_stop_membership',operation='CHECK_STOP_ON_ROUTE',slots={},
           evidence='membership',expected_data={'on_route':False})
    r=reply(intent='route_stop_membership',operation='CHECK_STOP_ON_ROUTE',
            data={'on_route':True,'route_ids':['R1'],'source':['PUBLISHED'],'provisional':True})
    assert score_cases([c],[r])['terminal_behavior']['success'] == 0
    assert score_cases([c],[replace(r,data={**r.data,'on_route':False})])['terminal_behavior']['success'] == 1


def test_nearest_answer_must_honor_anchor_and_requested_mode():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    c=case(intent='nearest_transport',operation='FIND_NEAREST_STATION',
           slots={'landmark':'BUS_ANCHOR','transport_mode':'metro'},evidence='nearest')
    data={'anchor':'BUS_OTHER','distance_type':'straight_line','provisional':True,
          'stops':[{'stop_id':'BUS_OTHER','name':'Wrong bus','mode':'bus','distance_m':10,'source':'PUBLISHED'}]}
    r=reply(intent='nearest_transport',operation='FIND_NEAREST_STATION',slots=c['slots'],data=data)
    assert score_cases([c],[r])['terminal_behavior']['success'] == 0
    assert score_cases([c],[replace(r,data={**data,'anchor':'BUS_ANCHOR'})])['terminal_behavior']['success'] == 0


@pytest.mark.parametrize('changes',[
    {'intent':None,'operation':None,'status':'clarification','clarification_reason':'multiple_goals',
     'candidate_intents':['fare_calculation','first_and_last_service','fare_calculation']},
    {'intent':'station_facilities','operation':'GET_STATION_FACILITY','slots':{'stage_number':3}},
])
def test_suite_rejects_duplicate_intents_and_forbidden_gold_slots(changes):
    from scripts.nlp_v2.evaluate_development_coverage import validate_cases

    with pytest.raises(ValueError):
        validate_cases([case(**changes)])


@pytest.mark.parametrize('changes',[
    {'version':True}, {'count':2}, {'canonical_database_sha256':None},
    {'reference_date':'2026-02-30'}, {'reference_date':None},
])
def test_suite_rejects_malformed_manifest_metadata(tmp_path,changes):
    from scripts.nlp_v2.evaluate_development_coverage import load_suite
    from src.nlp_v2.model import sha256_file

    suite=tmp_path/'suite.json'; suite.write_text(json.dumps([case()]))
    m={'version':1,'suite_sha256':sha256_file(suite),'count':1,
       'canonical_database_sha256':'a'*64,'reference_date':'2026-10-07',**changes}
    manifest=tmp_path/'manifest.json'; manifest.write_text(json.dumps(m))
    with pytest.raises(ValueError):
        load_suite(suite,manifest)


def test_evidence_kind_must_match_the_expected_operation():
    from scripts.nlp_v2.evaluate_development_coverage import validate_cases

    with pytest.raises(ValueError):
        validate_cases([case(evidence='sequences')])


def test_sequence_answer_requires_renderer_route_identity_and_mode():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    c=case(intent='route_stop_sequence',operation='LIST_ROUTE_STOPS',
           slots={'transport_mode':'bus'},evidence='sequences')
    row={'source':'PUBLISHED','stops':[{'stop_id':'STOP_A','name':'A','sequence':1},
                                   {'stop_id':'STOP_B','name':'B','sequence':2}]}
    r=reply(intent=c['intent'],operation=c['operation'],slots=c['slots'],
            data={'sequences':[row],'provisional':True})
    assert score_cases([c],[r])['terminal_behavior']['success'] == 0
    valid={**row,'route_name':'25R','route_id':'R25','mode':'bus'}
    assert score_cases([c],[replace(r,data={'sequences':[valid],'provisional':True})])['terminal_behavior']['success'] == 1
    assert score_cases([c],[replace(r,data={'sequences':[{**valid,'mode':'metro'}],'provisional':True})])['terminal_behavior']['success'] == 0


def test_fare_answer_requires_currency_for_renderer():
    from scripts.nlp_v2.evaluate_development_coverage import score_cases

    r=reply(); r=replace(r,data={k:v for k,v in r.data.items() if k!='currency'})
    assert score_cases([case()],[r])['terminal_behavior']['success'] == 0
