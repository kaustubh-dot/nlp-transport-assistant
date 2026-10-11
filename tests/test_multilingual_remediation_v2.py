"""Independent v2 literal cases; never import frozen challenge/reference data."""
import json
from pathlib import Path
import pytest
from scripts.nlp_v2.evaluate_multilingual import FixedClassifier
from src.nlp_v2.assistant import T3Assistant
from src.nlp_v2.entities import CanonicalResolver
from src.nlp_v2.slots import T3SlotExtractor

CASES=json.loads((Path(__file__).resolve().parents[1]/'data/nlp_v2/remediation_v2/cases.json').read_text())['cases']
@pytest.fixture(scope='module')
def extractor():
    return T3SlotExtractor(CanonicalResolver())

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id']+'-'+c['category']+'-'+c['language'])
def test_independent_extraction_invariants(extractor,case):
    result=extractor.extract(case['query'],case['expected_intent'],default_transport_mode=case.get('default_mode'))
    for key,value in case['expected_slots'].items():
        assert result.slots.get(key)==value
    for key in case.get('absent_slots',[]):
        assert key not in result.slots
    for key,values in case.get('forbidden_slots',{}).items():
        assert result.slots.get(key) not in values
    if 'requested_modes' in case:
        assert list(result.requested_modes)==case['requested_modes']
    if 'excluded_modes' in case:
        assert list(result.excluded_modes)==case['excluded_modes']
    if 'multiple' in case:
        assert result.multiple_execution_scopes==case['multiple']

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id']+'-'+c['category']+'-'+c['language'])
def test_independent_intent_injected_state_and_safety(extractor,case):
    reply=T3Assistant(classifier=FixedClassifier(case['expected_intent']),resolver=extractor.resolver,extractor=extractor).process_query(case['query'],default_transport_mode=case.get('default_mode'))
    assert reply.status==case['expected_status']
    for key,values in case.get('forbidden_slots',{}).items():
        assert reply.slots.get(key) not in values
    if case['category'] in {'route-excluded-only','route-contradiction'}:
        assert 'route_number' not in reply.slots
    assert reply.raw_query==case['query']
    if reply.status=='ok':
        assert reply.data.get('source') or any(r.get('source') for r in reply.data.get('routes',[]))

def test_suite_metadata_and_language_separation():
    assert len({c['id'] for c in CASES})==len(CASES)
    assert len({c['family_id'] for c in CASES})==len(CASES)
    assert {c['language'] for c in CASES}=={'EN','HI_DEVA','HI_LATN','HINGLISH'}
    for case in CASES:
        assert case['safety_constraint'] and case['expected_status'] in {'ok','clarification','unavailable','out_of_scope'}

@pytest.mark.parametrize('query',[
 'Do not use bus 54; show its stops.', 'Please avoid the bus 54; list its stops.',
 'List bus 54 stops; do not take bus 54.', 'List bus 54 stops, not the route 54.',
 'बस ५४ को छोड़कर उसके सभी स्टॉप दिखाओ।', 'bus 54 ko chhodo; stops dikhao.',
 'List stops for bus 54, not 54.', 'Not 54; show bus 54 stops.',
 '54 nahi; bus 54 ke stops batao.', '५४ नहीं; बस ५४ के सभी स्टॉप बताओ।',
])
def test_independently_reviewed_route_exclusions_never_dispatch(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert 'route_number' not in result.slots
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'route_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'List stops for routes 54/73.', 'List bus 54 plus 73 stops.',
 'List bus 54 as well as 73 stops.', 'List bus 54 + 73 stops.',
 'List bus 54/73/91 stops.', 'List stops for 73 or bus 54.',
])
def test_independently_reviewed_route_cardinality_never_chooses_first(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert result.multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'Do not board bus 54; list its stops.', 'List stops for any bus other than bus 54.',
 'Omit bus 54; list stops.', 'I do not want bus 54; list stops.',
 'Do not show bus 54 stops.', 'Bus 54 is excluded; list stops.',
 'bus 54 ke alawa stops batao.', 'bus 54 ke bina stops batao.',
 'List stops for buses except bus 54 and 73.', 'Exclude routes 54 and 73; show stops.',
])
def test_exclusion_predicates_and_coordinated_exclusions(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert 'route_number' not in result.slots
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',['List stops for routes 54;73.', 'List stops for routes 54;73;91.'])
def test_semicolon_numeric_route_list_requires_one_scope(extractor,query):
    assert extractor.extract(query,'route_stop_sequence').multiple_execution_scopes

@pytest.mark.parametrize('query', ['List stops for bus 54 आऱ.', 'List stops for bus 54 AB.',
 'List stops for bus 54 C-.', 'List stops for bus 54 आर5.'])
def test_unrepresentable_suffix_cannot_dispatch_truncated_parent_route(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert 'route_number' not in result.slots
    assert 'route_number' in result.missing_execution_slots


def test_explicit_passenger_count_does_not_become_route_operand(extractor):
    result=extractor.extract('List stops for bus 54, 2 passengers.','route_stop_sequence')
    assert result.slots['route_number']=='54'
    assert not result.multiple_execution_scopes


def test_numeric_route_range_cannot_dispatch_first_route(extractor):
    result=extractor.extract('List stops for routes 54 through 73.','route_stop_sequence')
    assert result.multiple_execution_scopes and 'route_number' not in result.slots

@pytest.mark.parametrize('query',[
 'Never use bus 54; list stops.', 'Please do not ever use bus 54; show stops.',
 'bus 54 na lena; stops dikhao.', 'बस ५४ ना लेना; सभी स्टॉप दिखाओ।',
 'List stops for bus 54 that is not wanted.', 'List bus 54 stops; it is not wanted.',
 'I do not want to take bus 54; list stops.', 'bus 54 ko avoid karo; stops batao.',
])
def test_exclusion_instruction_and_reference_cannot_dispatch(extractor,query):
    assert 'route_number' not in extractor.extract(query,'route_stop_sequence').slots
    assert T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query).status=='clarification'

@pytest.mark.parametrize('query',[
 'List stops for route 54 ab.', 'List stops for route 54 C D.',
 'List stops for bus 54 C जी.', 'List stops for bus 54–C.',
 'List stops for bus 54.1.', 'List stops for routes 54–73.',
 'List stops for routes 54 -> 73.', 'List bus 54 along with 73 stops.',
])
def test_complete_identifier_or_scope_must_not_dispatch_parent(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert 'route_number' not in result.slots
    assert T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query).status=='clarification'

@pytest.mark.parametrize('query,code',[
 ('List stops for bus 54, except routes 73 and 91.','54'),
 ('List stops for bus 54C not bus 54.','54C'),
 ('List bus 54 stops and 2.5 km away.','54'),
])
def test_unique_positive_route_survives_constraints_and_units(extractor,query,code):
    result=extractor.extract(query,'route_stop_sequence')
    assert result.slots['route_number']==code and not result.multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['route_number']==code

@pytest.mark.parametrize('query',[
 "Don't list stops for bus 54.", 'Never show stops for bus 54.',
 'Please do not show all stops for bus 54.', "I won't take bus 54; show stops.",
 'Bus 54 must not be used; list stops.', 'बस ५४ कभी नहीं लेना; सभी स्टॉप दिखाओ।',
 'List stops for route 54 together with 73.', 'List stops for route 54 versus 73.',
 'List stops for route 54.C.',
])
def test_negative_goal_operator_and_complete_route_scope(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 '164P nahi; 281 ke stops batao.', 'Not 164P; list stops for 281.',
 '१६४आर नहीं; २८१ के स्टॉप बताओ।',
])
def test_explicit_positive_numeric_operand_after_exclusion(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert result.slots['route_number']=='281'
    assert not result.multiple_execution_scopes

@pytest.mark.parametrize('query',[
 'I am not requesting the stop sequence for bus 54.',
 'Please do not take any bus 54; show stops.', 'Do not consider route 54; list stops.',
 'bus 54 bilkul nahi lena; list stops.', 'List stops for bus 54 – C.',
 'List stops for route 54 — C.',
])
def test_reviewed_operator_modifier_and_spaced_identifier_boundary(extractor,query):
    assert T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query).status=='clarification'

@pytest.mark.parametrize('query',[
 'Not bus 54-C; list stops for route 54.',
 'Not bus 54C#; list stops for route 54.',
])
def test_supported_route_exclusion_never_excludes_whole_bus_mode(extractor,query):
    result=extractor.extract(query,'route_stop_sequence',default_transport_mode='bus')
    assert result.slots['route_number']=='54'
    assert result.excluded_modes==() and result.requested_modes==('bus',)

@pytest.mark.parametrize('query',[
 'List stops for bus 54; show fare for bus 54.',
 'List stops for bus 54, plus show fare for bus 54.',
 'List stops for bus 54 along with fare for bus 54.',
])
def test_distinct_operations_separated_by_explicit_connectors_clarify(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and reply.clarification_reason=='multiple_goals'

@pytest.mark.parametrize('query,intent',[
 ('Do not calculate fare for 4 stages on an ordinary bus.','fare_calculation'),
 ('Never compute the ordinary bus fare for 4 stages.','fare_calculation'),
 ('Do not provide the fare for ordinary bus stage 4.','fare_calculation'),
 ('Bus 54 should not be used; show stops.','route_stop_sequence'),
 ("Bus 54 shouldn't be used; show stops.",'route_stop_sequence'),
 ('bus 54 ka istemal nahi karna; stops dikhao.','route_stop_sequence'),
 ('बस ५४ का इस्तेमाल नहीं करना; स्टॉप दिखाओ।','route_stop_sequence'),
 ('Show stops for bus 54 compared with 73.','route_stop_sequence'),
 ('Show stops for bus 54 then 73.','route_stop_sequence'),
 ('List stops for bus 54 . C.','route_stop_sequence'),
 ('List stops for bus 54 : C.','route_stop_sequence'),
])
def test_bounded_negative_operator_and_identifier_grammar(extractor,query,intent):
    reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query,code',[
 ('Bus 25R — STOPs pls!','25R'), ('Bus 54 — stops please.','54'),
 ('Bus 54 : stops please.','54'), ('Bus 54 . Stops please.','54'),
])
def test_prose_punctuation_after_complete_route_does_not_erase_code(extractor,query,code):
    assert extractor.extract(query,'route_stop_sequence').slots['route_number']==code

@pytest.mark.parametrize('query',[
 'List stops for bus 54 / C.', 'List stops for bus 54/C.',
 'List stops for bus 54, show fare for bus 54.',
 'List stops for bus 54. Show fare for bus 54.',
])
def test_complete_scope_around_slash_and_punctuated_goals(extractor,query):
    assert T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query).status=='clarification'


def test_native_hyphen_suffix_exclusion_preserves_bus_default(extractor):
    result=extractor.extract('Not bus ५४-सी; show stops for route 54.','route_stop_sequence',default_transport_mode='bus')
    assert result.slots['route_number']=='54'
    assert result.excluded_modes==() and result.requested_modes==('bus',)


def test_negative_second_operation_does_not_negate_positive_goal(extractor):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query('Show bus 54 stop list, not fare.')
    assert reply.status=='ok' and reply.slots['route_number']=='54'

@pytest.mark.parametrize('query',[
 'All stops are not requested for bus 54.',
 'Please refrain from showing all stops for bus 54.',
 'I refuse to use bus 54; show stops.',
])
def test_negative_auxiliary_and_refusal_scope_cannot_execute(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query,intent',[
 ('Bus 73 should not be taken; list stops for bus 54.','route_stop_sequence'),
 ('Bus 73 should not be used. List stops for bus 54.','route_stop_sequence'),
 ('Ordinary bus stage 4 fare please, live status nahi chahiye.','fare_calculation'),
 ('Ordinary bus stage 4 fare please; live status not requested.','fare_calculation'),
])
def test_clause_local_negation_preserves_separate_positive_goal(extractor,query,intent):
    reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok'
    if intent=='route_stop_sequence':
        assert reply.slots['route_number']=='54'
    else:
        assert reply.data['amount']==8

@pytest.mark.parametrize('modifier',[
 'first and last departure times', 'first and last bus timings',
 'first departure time and last departure time', 'first bus and last bus',
])
def test_numeric_route_reference_and_schedule_modifier_are_one_goal(extractor,modifier):
    from src.nlp_v2.assistant import explicit_multiple_goals
    assert explicit_multiple_goals('Bus route 54 from Poonamallee to Guindy, '+modifier)==()

@pytest.mark.parametrize('query,intent',[
 ('Do not calculate a 5 stage fare by ordinary bus.','fare_calculation'),
 ('मत ५ स्टेज का साधारण बस किराया बताओ।','fare_calculation'),
 ('The stop sequence is not wanted for bus 54.','route_stop_sequence'),
 ("Don't take the ordinary bus 54; display its stop sequence.",'route_stop_sequence'),
 ("Bus 54 shouldn't ever be used; show stops.",'route_stop_sequence'),
 ('Show stops for bus 54 followed by 73.','route_stop_sequence'),
 ('Show stops for route 54; after that 73.','route_stop_sequence'),
 ('Show stops for bus 54:C1.','route_stop_sequence'),
 ('Show stops for bus 54 . सी.','route_stop_sequence'),
 ('Show stops for bus 54 / सी.','route_stop_sequence'),
 ('Show stops for bus 54 सीं.','route_stop_sequence'),
])
def test_independent_sixth_review_negative_and_complete_operand_contract(extractor,query,intent):
    reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'Bus 73 must never be chosen; show stops for bus 54.',
 'Show stops for bus 54 — all stops please.',
 'Show stops for bus 54. do not quote the fare.',
 'Show stops for bus 54 vs 54.', 'Show stops for bus 54 or 54.',
])
def test_sixth_review_positive_scope_and_prose_controls(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['route_number']=='54'

def test_hyphenated_stage_quantity_is_not_an_explicit_route(extractor):
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query('Calculate the 5-stage ordinary bus fare.')
    assert reply.status=='ok' and reply.data['amount']==9 and 'route_number' not in reply.slots

def test_first_last_departure_time_modifier_is_one_goal(extractor):
    reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query('First and last buses from Poonamallee Bus Terminus, departure times please.')
    assert reply.status=='ok' and reply.operation=='GET_FIRST_LAST_SERVICE'

@pytest.mark.parametrize('query,intent',[
 ("Bus 54 shouldn't actually be chosen; list stops.",'route_stop_sequence'),
 ('बस ५४ : सी। सभी स्टॉप दिखाओ।','route_stop_sequence'),
 ('Show stops for route 54 and then 27.','route_stop_sequence'),
 ('Ordinary bus fare for a 6.5-stage journey.','fare_calculation'),
 ('साधारण बस का ६.५-स्टेज किराया बताओ।','fare_calculation'),
])
def test_seventh_review_exclusion_suffix_sequence_and_decimal_safety(extractor,query,intent):
    reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'Show stops for bus 54. I need its stop sequence.',
 'Show stops for bus 54. Can you list all stops?',
 'List stops for bus 54; tell me the whole stop sequence.',
])
def test_seventh_review_prose_and_same_scope_restatement(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['route_number']=='54'

def test_stage_count_does_not_absorb_next_clause_imperative(extractor):
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query('Ordinary bus fare for 6 stages; do not show live status.')
    assert reply.status=='ok' and reply.data['amount']==10 and reply.slots['stage_number']==6

@pytest.mark.parametrize('query',[
 'Ordinary bus 5 stage fare is not wanted but list stops for bus 54.',
 'Ordinary bus 5 stage fare is not requested alongside the stop sequence for bus 54.',
 'Ordinary bus 5 stage fare not wanted; show stops for bus 54.',
])
def test_negative_goal_predicate_is_not_cancelled_by_later_positive_goal(extractor,query):
    from src.nlp_v2.assistant import selected_goal_negated
    assert selected_goal_negated(query,'fare_calculation')
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'Show bus 54 stop list not fare.',
 'Show bus 54 stop list but not fare.',
])
def test_goal_complement_negation_preserves_positive_stop_request(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['route_number']=='54'

@pytest.mark.parametrize('query',[
 'Bus 54 should not be used and bus 27 should be chosen; list stops.',
 'Avoid bus 54 but show stops for bus 27.',
])
def test_affirmative_route_clause_resets_negative_operator(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert result.slots['route_number']=='27'
    assert result.request_constraints['excluded_routes']==['54']
    assert result.request_constraints['required_routes']==['27']

@pytest.mark.parametrize('query',[
 'Please calculate the ordinary bus fare for 8 stages, do not request live data.',
 'Show the fare for 8 ordinary bus stages; tell me the price for those same 8 stages.',
])
def test_stage_clause_and_modifier_prose_preserves_unique_quantity(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['stage_number']==8
    assert reply.data['amount']==12 and 'route_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'Show first and last buses from Poonamallee Bus Terminus; tell me first and last buses from Poonamallee Bus Terminus.',
 'First and last buses from Poonamallee Bus Terminus, first and last buses from Poonamallee Bus Terminus please.',
])
def test_identical_timetable_source_restatement_is_one_scope(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['station']=='BUS_5821'
    assert 'destination' not in reply.slots

@pytest.mark.parametrize('query',[
 'Tell me about wheelchair access at Guindy metro; tell me about lift access at Guindy metro.',
 'Tell me about lift access at Guindy metro; tell me about lift access at Alandur metro.',
])
def test_distinct_accessibility_operands_clarify_before_source_preflight(extractor,query):
    assert extractor.extract(query,'station_accessibility').multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier('station_accessibility'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and reply.clarification_reason=='multiple_goals'

@pytest.mark.parametrize('query',[
 'Tell me about wheelchair access at Guindy metro; repeat wheelchair access at Guindy metro.',
 'Tell me about lift access at Guindy metro.',
])
def test_same_accessibility_scope_keeps_truthful_source_limitation(extractor,query):
    assert not extractor.extract(query,'station_accessibility').multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier('station_accessibility'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='unavailable' and reply.data['reason']=='accessibility_values_absent'

@pytest.mark.parametrize('query,expected',[
 ('Metro Blue Line train and local train route please.',('metro','suburban_rail')),
 ('MRTS electric train and rail route please.',('mrts','suburban_rail')),
 ('Not Metro Blue Line train; bus route please.',('bus',)),
])
def test_qualified_train_attachment_preserves_independent_and_excluded_modes(extractor,query,expected):
    result=extractor.extract(query,'point_to_point_route')
    assert result.requested_modes==expected
    if query.startswith('Not'):
        assert result.excluded_modes==('metro',)

@pytest.mark.parametrize('query',[
 'Does bus 54 not stop at Poonamallee Bus Terminus?',
 'क्या बस ५४ नहीं रुकती Poonamallee Bus Terminus पर?',
 'bus 54 nahi rukti Poonamallee Bus Terminus par kya?',
])
def test_negative_membership_proposition_retains_queried_route(extractor,query):
    result=extractor.extract(query,'route_stop_membership')
    assert result.slots['route_number']=='54' and result.slots['transport_mode']=='bus'
    assert not result.request_constraints.get('excluded_routes')
    reply=T3Assistant(classifier=FixedClassifier('route_stop_membership'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='unavailable' and reply.data['reason']=='membership_topology_incomplete'

@pytest.mark.parametrize('query',[
 'The Ordinary bus fare for 6 stages is not required.',
 'The Ordinary bus fare for 6 stages is not required lekin list stops for bus 54.',
])
def test_negative_goal_predicate_after_operand_cannot_execute(extractor,query):
    from src.nlp_v2.assistant import selected_goal_negated
    assert selected_goal_negated(query,'fare_calculation')
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'The Ordinary bus fare for 6 stages is definitely not required.',
 'Ordinary bus fare for 6 stages nahi chahiye.',
 'Ordinary bus fare for 6 stages not wanted.',
])
def test_negative_goal_operand_predicates_preserve_modifiers_and_hindi_polarity(extractor,query):
    from src.nlp_v2.assistant import selected_goal_negated
    assert selected_goal_negated(query,'fare_calculation')
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 "Ordinary bus fare for stage 7 isn't requested.",
 "Ordinary bus fare for stage 7 won't be needed.",
 'The Ordinary bus fare price for stage 7 is not requested.',
 'The Ordinary bus fare and price for stage 7 is not requested.',
 'Ordinary bus fare cost for stage 7 nahi chahiye.',
 'Do not give the Ordinary bus fare price for stage 7.',
])
def test_contracted_and_synonymous_negative_goal_predicates_cannot_execute(extractor,query):
    from src.nlp_v2.assistant import selected_goal_negated
    assert selected_goal_negated(query,'fare_calculation')
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'List stops for bus 54 but do not give fare details.',
 'List stops for bus 54 not please quote the Ordinary bus fare.',
 'Ordinary bus fare is not wanted show all stops for bus 54.',
 'Ordinary bus fare nahi chahiye show all stops for bus 54.',
])
def test_positive_stop_goal_survives_other_goal_completed_predicate(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['route_number']=='54'

@pytest.mark.parametrize('query',[
 'List stops for buses 54 and 27 for comparison.',
 'Show all stops for buses 54 / 27.',
])
def test_plural_bus_route_list_keeps_each_positive_operand(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert result.multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and reply.clarification_reason=='multiple_goals'


def test_complete_published_multiword_route_code_is_preserved(extractor):
    query='Show the complete stop sequence for bus 29A CT.'
    result=extractor.extract(query,'route_stop_sequence')
    assert result.slots['route_number']=='29ACT'
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['route_number']=='29ACT'
    assert all(row['route_name']=='29A CT' for row in reply.data['sequences'])

@pytest.mark.parametrize('query',[
 "The fare plus price for stage 9 on an Ordinary bus isn't wanted.",
 'I require neither fare nor price for stage 9 on an Ordinary bus.',
 'Ordinary bus fares for stage 9 are not wanted.',
 'Ordinary bus prices for stage 9 are not wanted.',
])
def test_coordinated_and_plural_negative_goal_nouns_cannot_execute(extractor,query):
    from src.nlp_v2.assistant import selected_goal_negated
    assert selected_goal_negated(query,'fare_calculation')
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'Ordinary bus stage 8 fare na batana.',
 'साधारण बस का ८ स्टेज का किराया ना बताना।',
 'Without the Ordinary bus fare for stage 8 please.',
 'Please omit the Ordinary bus stage 8 fare.',
 'Avoid calculating the Ordinary bus stage 8 fare.',
 'No need to give the Ordinary bus stage 8 fare.',
])
def test_negative_goal_operators_and_stage_first_operands_cannot_execute(extractor,query):
    from src.nlp_v2.assistant import selected_goal_negated
    assert selected_goal_negated(query,'fare_calculation')
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification'

@pytest.mark.parametrize('query',[
 'List all stops for bus 54 ABसी.',
 'List all stops for bus 54 ABCD1.',
 'List all stops for bus 54: ABसी.',
 'List all stops for bus 54—ABCD1.',
])
def test_complete_mixed_or_extended_suffix_cannot_dispatch_parent_route(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'route_number' not in reply.slots

@pytest.mark.parametrize('query,expected,excluded',[
 ('Metro Blue Line train nahi; bus route please.',('bus',),('metro',)),
 ('एमआरटीएस इलेक्ट्रिक ट्रेन नहीं; बस का रास्ता बताओ।',('bus',),('mrts',)),
 ('Metro train or suburban train route please.',('metro','suburban_rail'),()),
 ('MRTS electric train and metro train route please.',('mrts','metro'),()),
])
def test_qualified_mode_head_negation_and_independent_modes(extractor,query,expected,excluded):
    result=extractor.extract(query,'point_to_point_route',default_transport_mode='metro')
    assert result.requested_modes==expected and result.excluded_modes==excluded

@pytest.mark.parametrize('query,intent',[
 ('Do not use metro; tell me whether bus is available.','mode_availability'),
 ('Avoid bus 54; does bus 27 stop at Poonamallee Bus Terminus?','route_stop_membership'),
])
def test_question_does_not_erase_separate_avoidance_instruction(extractor,query,intent):
    result=extractor.extract(query,intent,default_transport_mode='metro')
    if intent=='mode_availability':
        assert result.excluded_modes==('metro',) and result.requested_modes==('bus',)
    else:
        assert result.slots['route_number']=='27'
        assert result.request_constraints['excluded_routes']==['54']

@pytest.mark.parametrize('query',[
 'Show the Ordinary bus fare for 8 ordinary bus stages.',
 'साधारण बस का ८ साधारण बस स्टेज किराया बताओ।',
])
def test_service_qualified_stage_quantity_keeps_exact_tariff(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.data['amount']==12
    assert reply.slots['stage_number']==8 and 'route_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'Show the Ordinary bus fare for 8.5 ordinary bus stages.',
 'Show the Ordinary bus fare for 8 and 9 ordinary bus stages.',
])
def test_qualified_stage_quantity_never_truncates_or_chooses_one_count(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'stage_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'Show first and last buses from Poonamallee Bus Terminus and from Island ground Terminus.',
 'Show first and last buses from Poonamallee Bus Terminus and from Imaginary Junction.',
])
def test_repeated_timetable_role_retains_distinct_or_unknown_operand_guard(extractor,query):
    result=extractor.extract(query,'first_and_last_service')
    assert result.multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and reply.clarification_reason=='multiple_goals'

@pytest.mark.parametrize('query',[
 'List all stops for bus 29A CT and bus 54.',
 'List all stops for bus 29A CT1.',
 'List all stops for bus 29A CT सी.',
])
def test_published_multiword_route_never_hides_competing_or_extended_code(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'route_number' not in reply.slots

@pytest.mark.parametrize('query,intent',[
 ('Parking and restroom at Guindy metro please.','station_facilities'),
 ('Monthly pass and smart card rules please.','ticketing_and_passes'),
])
def test_distinct_singleton_parameters_clarify_before_global_source_refusal(extractor,query,intent):
    assert extractor.extract(query,intent).multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and reply.clarification_reason=='multiple_goals'

@pytest.mark.parametrize('query',[
 'Show the Ordinary bus fare for half eight ordinary bus stages.',
 'Show the Ordinary bus fare for minus eight ordinary bus stages.',
 'साधारण बस का आधे आठ साधारण बस स्टेज किराया बताओ।',
 'Show the Ordinary bus fare for eighty eight ordinary bus stages.',
])
def test_qualified_count_modifiers_never_select_partial_tariff(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'stage_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'Calculate the Ordinary bus fare for 8 stages; do not take bus 54.',
 'साधारण बस का ८ स्टेज किराया बताओ; bus 54 nahi lena.',
])
def test_stage_fare_does_not_require_operand_of_separate_excluded_goal(extractor,query):
    result=extractor.extract(query,'fare_calculation')
    assert result.request_constraints['excluded_routes']==['54']
    reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.data['amount']==12 and 'route_number' not in reply.slots

REGRESSIONS=json.loads((Path(__file__).resolve().parents[1]/'data/nlp_v2/remediation_v2/cases.json').read_text())['additional_regressions']
@pytest.mark.parametrize('case',REGRESSIONS,ids=lambda c:c['id'])
def test_supplemental_case_contract_matches_authored_regression(extractor,case):
    result=extractor.extract(case['query'],case['expected_intent'],default_transport_mode=case.get('default_mode'))
    for name,value in case['expected_slots'].items():
        assert result.slots.get(name)==value
    if case['expected_mode'] is not None:
        assert result.slots.get('transport_mode')==case['expected_mode']
    reply=T3Assistant(classifier=FixedClassifier(case['expected_intent']),extractor=extractor,resolver=extractor.resolver).process_query(case['query'],default_transport_mode=case.get('default_mode'))
    assert reply.status==case['expected_status'] and reply.raw_query==case['query']
    assert case['family_id'] and case['safety_constraint'] and case['provenance']

@pytest.mark.parametrize('query',[
 'Show the published stops of route 54 QWER please.',
 'Show the published stops of route 54 qwer please.',
 'Show the published stops of route 54: QWER please.',
 'Show the published stops of route 54 / qwer please.',
])
def test_unknown_pure_latin_suffix_never_dispatches_parent_identifier(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'route_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'Show all stops for bus 54 please.',
 'Bus 54 stops please.',
 'List stops for bus 54 without fare details.',
 'List stops for bus 54 but do not give fare details.',
])
def test_complete_route_reference_preserves_following_request_prose(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok' and reply.slots['route_number']=='54'

@pytest.mark.parametrize('query',[
    'Is bus 54 not stopping at Poonamallee Bus Terminus please?',
    'Does bus 54 not halt at Poonamallee Bus Terminus?',
    'Is bus 54 not halting at Poonamallee Bus Terminus?',
])
def test_negative_membership_predicate_inflections_preserve_operand(extractor,query):
    result=extractor.extract(query,'route_stop_membership')
    assert result.slots.get('route_number')=='54'
    assert '54' not in result.request_constraints.get('excluded_routes',())
    reply=T3Assistant(classifier=FixedClassifier('route_stop_membership'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='unavailable' and reply.data.get('reason')=='membership_topology_incomplete'

@pytest.mark.parametrize('query',[
    'Is the Metro electric train not operating from Guindy to Alandur?',
    'Is the MRTS train not operating from Guindy to Alandur?',
])
def test_negative_availability_predicate_inflections_preserve_mode(extractor,query):
    result=extractor.extract(query,'mode_availability',default_transport_mode='bus')
    mode='mrts' if 'MRTS' in query else 'metro'
    assert result.requested_modes==(mode,) and result.excluded_modes==()
    reply=T3Assistant(classifier=FixedClassifier('mode_availability'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='bus')
    assert reply.status=='unavailable' and reply.slots.get('transport_mode')==mode

@pytest.mark.parametrize('query',[
    'MRTS new electric train from Guindy to Alandur please.',
    'Metro fast new train from Guindy to Alandur please.',
    'MRTS new train from Guindy to Alandur please.',
])
def test_specific_train_modifiers_are_not_place_operands(extractor,query):
    result=extractor.extract(query,'point_to_point_route')
    assert not result.multiple_execution_scopes
    assert all(span.surface!='new' for span in result.spans)
    reply=T3Assistant(classifier=FixedClassifier('point_to_point_route'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='unavailable' and reply.data.get('reason')=='published_mode_topology_absent'

@pytest.mark.parametrize('query',[
    'MRTS train from New to Guindy please.',
    'Metro train from New to Alandur please.',
])
def test_modifier_named_place_after_origin_role_is_preserved(extractor,query):
    result=extractor.extract(query,'point_to_point_route')
    assert any(span.surface=='new' for span in result.spans)

@pytest.mark.parametrize('query',[
    "Isn't bus 54 stopping at Poonamallee Bus Terminus please?",
    "Isn't bus 54 halting at Poonamallee Bus Terminus please?",
    "Doesn't bus 54 halt at Poonamallee Bus Terminus please?",
    "Doesn't bus 54 stop at Poonamallee Bus Terminus please?",
    'Is bus 54 stopping at Poonamallee Bus Terminus please?',
    'Is bus 54 halting at Poonamallee Bus Terminus please?',
])
def test_membership_predicate_after_route_is_request_prose(extractor,query):
    result=extractor.extract(query,'route_stop_membership')
    assert result.slots.get('route_number')=='54'
    reply=T3Assistant(classifier=FixedClassifier('route_stop_membership'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='unavailable' and reply.data.get('reason')=='membership_topology_incomplete'

@pytest.mark.parametrize('query,intent',[
    ("Isn't bus 54 stopping at Poonamallee Bus Terminus?",'route_stop_sequence'),
    ("Doesn't bus 54 halt at Poonamallee Bus Terminus?",'route_stop_sequence'),
    ('Is bus 54 halting at Poonamallee Bus Terminus?','route_stop_sequence'),
    ('Does bus 54 stop at Poonamallee Bus Terminus?','route_stop_sequence'),
    ("Isn't bus 54 stopping at Poonamallee Bus Terminus?",'fare_calculation'),
    ("Doesn't bus 54 halt at Poonamallee Bus Terminus?",'fare_calculation'),
    ('Is bus 54 halting at Poonamallee Bus Terminus?','scheduled_departure'),
    ('Does bus 54 stop at Poonamallee Bus Terminus?','scheduled_departure'),
])
def test_membership_question_never_executes_conflicting_prediction(extractor,query,intent):
    reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and reply.clarification_reason=='intent_ambiguity'
    assert reply.operation is None and reply.data.get('reason')=='predicted_operation_conflict'
    assert reply.raw_query==query

@pytest.mark.parametrize('query',[
    'Bus 29 ACT: show its published stops please.',
    'बस २९ ACT के प्रकाशित स्टॉप दिखाओ।',
    'bus 29 ACT ke published stops batao.',
])
def test_complete_route_suffix_cannot_be_masked_as_place(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert result.slots.get('route_number')=='29ACT'
    assert all(span.surface!='act' for span in result.spans)
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='ok'
    assert all(row['route_name'].replace(' ','')=='29ACT' for row in reply.data['sequences'])

@pytest.mark.parametrize('query',[
    'Bus 54 ACT: show its published stops please.',
    'Bus ५४ ACT: show its published stops please.',
])
def test_short_named_suffix_cannot_dispatch_unknown_parent(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert 'route_number' not in result.slots
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'route_number' not in reply.slots

@pytest.mark.parametrize('query',[
    'Does bus 54 stop at ACT?',
    'बस ५४ ACT पर रुकती है?',
])
def test_explicit_stop_role_keeps_suffix_named_place(extractor,query):
    result=extractor.extract(query,'route_stop_membership')
    assert result.slots.get('route_number')=='54'
    assert any(span.surface=='act' for span in result.spans)

@pytest.mark.parametrize('query,intent',[
 ('Please tell me whether bus 54 halts at Poonamallee Bus Terminus.','route_stop_sequence'),
 ('Tell us if bus 54 stops at Poonamallee Bus Terminus.','route_stop_sequence'),
 ('क्या बस ५४ पूनमल्ली बस टर्मिनस पर रुकती है?','route_stop_sequence'),
 ('kya bus 54 Poonamallee Bus Terminus par rukti hai?','route_stop_sequence'),
 ('Bus 54 stops at Poonamallee Bus Terminus?','route_stop_sequence'),
 ('बस ५४ पूनमल्ली बस टर्मिनस पर रुकती है क्या?','route_stop_sequence'),
 ('Please tell me whether bus 54 halts at Poonamallee Bus Terminus.','fare_calculation'),
 ('Tell us if bus 54 stops at Poonamallee Bus Terminus.','fare_calculation'),
 ('क्या बस ५४ पूनमल्ली बस टर्मिनस पर रुकती है?','fare_calculation'),
 ('kya bus 54 Poonamallee Bus Terminus par rukti hai?','fare_calculation'),
 ('Bus 54 stops at Poonamallee Bus Terminus?','fare_calculation'),
 ('बस ५४ पूनमल्ली बस टर्मिनस पर रुकती है क्या?','fare_calculation'),
])
def test_embedded_native_and_tag_membership_guard(extractor,query,intent):
 reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='clarification' and reply.operation is None
 assert reply.data.get('reason')=='predicted_operation_conflict'
 assert reply.raw_query==query
@pytest.mark.parametrize('query',[
 'kya bus 54 ACT par rukti hai?',
 'kya bus 54 ACT mein rukti hai?',
 'bus 54 ACT se jaati hai kya?',
 'bus 54 ACT tak jaati hai kya?',
])
def test_explicit_roman_place_postposition_keeps_complete_route(extractor,query):
 result=extractor.extract(query,'route_stop_membership')
 assert result.slots.get('route_number')=='54'
 assert any(span.surface=='act' for span in result.spans)
 reply=T3Assistant(classifier=FixedClassifier('route_stop_membership'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='clarification' and reply.clarification_reason=='entity_ambiguity'
@pytest.mark.parametrize('query',[
 'बस ५४ की स्टॉप सूची बताओ; बस २७ को छोड़िए।',
 'बस ५४ की स्टॉप सूची बताओ; बस २७ को छोड़िये।',
 'बस ५४ की स्टॉप सूची बताओ; बस २७ को छोडिए।',
 'बस ५४ की स्टॉप सूची बताओ; बस २७ को छोडिये।',
])
def test_polite_native_route_exclusion_keeps_positive_operand(extractor,query):
 result=extractor.extract(query,'route_stop_sequence')
 assert result.slots.get('route_number')=='54'
 assert result.request_constraints.get('excluded_routes')==['27']
 assert not result.multiple_execution_scopes
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='ok' and reply.slots['route_number']=='54'
@pytest.mark.parametrize('query',[
 'At Poonamallee Bus Terminus, show first and last bus departure times.',
 'At Poonamallee Bus Terminus, give the first and last bus timings.',
 'At Poonamallee Bus Terminus, tell me the first and last bus times please.',
 'At Poonamallee Bus Terminus, list first and last buses please.',
])
def test_timetable_request_after_boarding_location_comma_is_one_scope(extractor,query):
 result=extractor.extract(query,'first_and_last_service',default_transport_mode='bus')
 assert not result.multiple_execution_scopes
 assert result.slots.get('station')=='BUS_5821'
 reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='bus')
 assert reply.status=='ok' and reply.data['first_departure']=='00:18:00'
@pytest.mark.parametrize('query',[
 'Not bus; show a route from Poonamallee Bus Terminus to Island ground Terminus.',
 'बस नहीं; पूनमल्ली बस टर्मिनस से Island ground Terminus तक रास्ता बताओ।',
 'bus nahi; Poonamallee Bus Terminus se Island ground Terminus tak raasta batao.',
])
def test_excluded_mode_with_qualified_anchor_still_requires_positive_mode(extractor,query):
 result=extractor.extract(query,'point_to_point_route',default_transport_mode='bus')
 assert result.excluded_modes==('bus',)
 # A mode-qualified canonical anchor is an explicit conflicting mention.
 # The safety contract requires clarification before any operation.
 assert not result.requested_modes or 'bus' in result.requested_modes
 reply=T3Assistant(classifier=FixedClassifier('point_to_point_route'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='bus')
 assert reply.status=='clarification' and reply.operation is None
 assert reply.data['excluded_modes']==['bus']
 assert reply.missing_slots==('transport_mode',)

@pytest.mark.parametrize('query',[
 'Please tell me whether bus 54 halts at Poonamallee Bus Terminus.',
 'क्या बस ५४ पूनमल्ली बस टर्मिनस पर रुकती है?',
 'kya bus 54 Poonamallee Bus Terminus par rukti hai?',
 'बस ५४ पूनमल्ली बस टर्मिनस पर रुकती है क्या?',
])
def test_same_membership_question_with_matching_intent_keeps_operands(extractor,query):
    result=extractor.extract(query,'route_stop_membership')
    assert result.slots.get('route_number')=='54' and result.slots.get('stop')=='BUS_5821'
    reply=T3Assistant(classifier=FixedClassifier('route_stop_membership'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='unavailable' and reply.data.get('reason')=='membership_topology_incomplete'

@pytest.mark.parametrize('query',[
 'At Poonamallee Bus Terminus, give first and last buses from Golden Pebble Depot.',
 'At Poonamallee Bus Terminus, show first and last buses and Golden Pebble Depot.',
])
def test_timetable_comma_request_cannot_hide_extra_unknown_location(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='bus')
    assert reply.status=='clarification' and reply.clarification_reason=='multiple_goals'

@pytest.mark.parametrize('query',[
 'At Poonamallee Bus Terminus, give first and last buses from Island ground Terminus.',
 'Poonamallee Bus Terminus se first and last bus, from Island ground Terminus first and last bus please.',
])
def test_timetable_boarding_roles_cannot_be_reinterpreted_as_endpoints(extractor,query):
    result=extractor.extract(query,'first_and_last_service',default_transport_mode='bus')
    assert result.multiple_execution_scopes
    reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='bus')
    assert reply.status=='clarification' and reply.operation is None

@pytest.mark.parametrize('query,excluded',[
 ('मेट्रो को छोड़िए; Marina Beach के पास स्टेशन बताओ।','metro'),
 ('बस को छोड़ो; Marina Beach के पास स्टेशन बताओ।','bus'),
 ('metro ko chhodo; Marina Beach nearest station batao.','metro'),
 ('एमआरटीएस को छोड़कर; Marina Beach के पास स्टेशन बताओ।','mrts'),
])
def test_native_avoidance_operator_excludes_mode_before_default(extractor,query,excluded):
 result=extractor.extract(query,'nearest_transport',default_transport_mode=excluded)
 assert result.excluded_modes==(excluded,) and result.requested_modes==()
 reply=T3Assistant(classifier=FixedClassifier('nearest_transport'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode=excluded)
 assert reply.status=='clarification' and reply.operation is None
 assert excluded not in reply.slots.values()
@pytest.mark.parametrize('query',[
 'साधारण बस का ४ स्टेज का किराया छोड़िए।',
 'Ordinary bus stage 4 fare ko chhodo.',
 'साधारण बस के चार स्टेज का किराया छोड़ो।',
])
def test_native_avoidance_operator_cannot_execute_negated_fare(extractor,query):
 reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='clarification' and reply.operation is None
 assert reply.data.get('reason')=='negated_selected_goal'
@pytest.mark.parametrize('query',[
 'बस ५४ के सभी स्टॉप बताओ, बस २७ को छोड़िए।',
 'Bus 54 stop list please, bus 27 ko chhodo.',
 'साधारण बस का ४ स्टेज का किराया बताओ, बस २७ को छोड़िए।',
])
def test_avoidance_owned_by_other_route_keeps_positive_goal(extractor,query):
 intent='fare_calculation' if 'किराया' in query else 'route_stop_sequence'
 reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='ok'
 if intent=='fare_calculation':assert reply.data['amount']==8
 else:assert reply.slots['route_number']=='54'

@pytest.mark.parametrize('query',[
 'bus 54 chhodo; bus 27 ke stops batao.',
 'bus 54 chodkar; bus 27 ke stops batao.',
])
def test_native_avoidance_after_route_is_functional_prose(extractor,query):
    result=extractor.extract(query,'route_stop_sequence')
    assert result.slots.get('route_number')=='27'
    assert result.request_constraints.get('excluded_routes')==['54']
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='unavailable' and reply.slots.get('route_number')=='27'

@pytest.mark.parametrize('query',[
 'Poonamallee Bus Terminus par, pehli aur aakhiri bus ka time batao.',
 'पूनमल्ली बस टर्मिनस पर, पहली और आखिरी बस का समय बताओ।',
 'पूनमल्ली बस टर्मिनस से, पहली बस और आखिरी बस का समय दिखाइए।',
 'Poonamallee Bus Terminus se, pehli bus aur aakhiri bus ke timings dikhao.',
 'पूनमल्ली बस टर्मिनस पर, कृपया पहली और आखिरी बस का समय बताइए।',
 'Poonamallee Bus Terminus par, please pehli aur aakhiri bus ka time bataiye.',
 'At Poonamallee Bus Terminus, show the first and last bus times please.',
 'पूनमल्ली बस टर्मिनस पर, पहली और आखिरी बस का समय चाहिए।',
 'Poonamallee Bus Terminus par, pehli aur aakhiri bus ka time chahiye.',
])
def test_native_fronted_timetable_request_is_complete_modifier(extractor,query):
 result=extractor.extract(query,'first_and_last_service',default_transport_mode='bus')
 assert not result.multiple_execution_scopes
 assert result.slots.get('station')=='BUS_5821'
 reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='bus')
 assert reply.status=='ok'
 assert reply.data['first_departure']=='00:18:00' and reply.data['last_departure']=='25:16:00'
@pytest.mark.parametrize('query',[
 'साधारण बस का ४ स्टेज का किराया छोड़िए; बस ५४ के सभी स्टॉप बताओ।',
 'Ordinary bus 4 stage fare ko chhodo; bus 54 ke sabhi stops batao.',
 'साधारण बस का किराया छोड़ो, बस ५४ की स्टॉप सूची दिखाओ।',
 'Ordinary bus fare chhodkar bus 54 stop list dikhao.',
 'साधारण बस का किराया छोड़िए; मेट्रो से Egmore जाना है।',
])
def test_postfix_avoidance_owned_by_goal_does_not_exclude_next_mode(extractor,query):
 intent='point_to_point_route' if 'Egmore' in query else 'route_stop_sequence'
 result=extractor.extract(query,intent)
 mode='metro' if 'Egmore' in query else 'bus'
 assert mode in result.requested_modes and mode not in result.excluded_modes
 if intent=='route_stop_sequence':
  assert result.slots.get('route_number')=='54'
  reply=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver).process_query(query)
  assert reply.status=='ok' and reply.slots['route_number']=='54'
@pytest.mark.parametrize('query',[
 'Ordinary bus fare ko chhodo.', 'साधारण बस का किराया छोड़िए।',
])
def test_postfix_avoidance_still_refuses_its_fare_goal(extractor,query):
 reply=T3Assistant(classifier=FixedClassifier('fare_calculation'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='clarification' and reply.operation is None
 assert reply.data.get('reason')=='negated_selected_goal'
@pytest.mark.parametrize('query',[
 'पूनमल्ली बस टर्मिनस पर, पहली और आखिरी बस का समय Golden Pebble बताओ।',
 'Poonamallee Bus Terminus par, pehli aur aakhiri bus ka time Golden Pebble batao.',
 'पूनमल्ली बस टर्मिनस पर, पहली और आखिरी बस का समय Island ground Terminus से बताओ।',
 'Poonamallee Bus Terminus par, pehli aur aakhiri bus ka time Island ground Terminus se batao.',
])
def test_fronted_native_request_cannot_hide_unknown_or_distinct_boarding(extractor,query):
 result=extractor.extract(query,'first_and_last_service',default_transport_mode='bus')
 assert result.multiple_execution_scopes
 reply=T3Assistant(classifier=FixedClassifier('first_and_last_service'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='bus')
 assert reply.status=='clarification' and reply.operation is None

@pytest.mark.parametrize('query',[
 'साधारण बस के चार स्टेज किराये को छोड़ो; बस ५४ के सभी स्टॉप बताओ।',
 'ordinary bus stage 4 kiraye ko chhodo; bus 54 all stops batao.',
 'साधारण बस के किराए छोड़िए, बस ५४ की स्टॉप सूची बताओ।',
 'ordinary bus kiraye chhodkar bus 54 all stops dikhao.',
])
def test_shared_supported_fare_inflections_own_postfix_avoidance(extractor,query):
 result=extractor.extract(query,'route_stop_sequence')
 assert result.requested_modes==('bus',) and result.excluded_modes==()
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='ok' and reply.slots['route_number']=='54'
@pytest.mark.parametrize('query',[
 'छोड़ो बस ५४; बस 54C के सभी स्टॉप बताओ।',
 'मत चुनो बस ५४; बस 54C का स्टॉप क्रम दिखाइए।',
 'chhodo bus 54; bus 54C ke sabhi stops bataiye.',
 'Exclude bus 54; bus 54C ke stops dikhao.',
])
def test_new_postfix_request_after_semicolon_resets_route_list_exclusion(extractor,query):
 result=extractor.extract(query,'route_stop_sequence')
 assert result.slots.get('route_number')=='54C'
 assert result.request_constraints.get('excluded_routes')==['54']
 assert result.requested_modes==('bus',) and not result.multiple_execution_scopes
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='ok' and reply.slots['route_number']=='54C'
@pytest.mark.parametrize('query',[
 'बस ५४ नहीं; बस ५४सी के सभी स्टॉप बताओ।',
 'बस ५४ नहीं; बस 54सी के सभी स्टॉप बताओ।',
 'बस ५४ को छोड़ो। बस ५४सी की स्टॉप सूची बताओ।',
 'Not bus 54; बस ५४सी के सभी स्टॉप बताओ।',
])
@pytest.mark.parametrize('default',[None,'metro'])
def test_native_attached_route_suffix_preserves_explicit_bus_over_default(extractor,query,default):
 result=extractor.extract(query,'route_stop_sequence',default_transport_mode=default)
 assert result.slots.get('route_number')=='54C'
 assert result.requested_modes==('bus',) and result.slots.get('transport_mode')=='bus'
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode=default)
 assert reply.status=='ok' and reply.slots['transport_mode']=='bus' and reply.slots['route_number']=='54C'
@pytest.mark.parametrize('query',[
 'Exclude bus 54; bus 54C.', 'छोड़ो बस ५४; बस 54C.',
 'Exclude bus 54 and bus 54C.', 'छोड़ो बस ५४ और बस 54C।',
])
def test_operand_only_exclusion_list_does_not_become_positive_request(extractor,query):
 result=extractor.extract(query,'route_stop_sequence')
 assert 'route_number' not in result.slots
 assert set(result.request_constraints.get('excluded_routes',[]))=={'54','54C'}
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='clarification' and 'route_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'Exclude bus 54; bus 54C ke stops mat dikhao.',
 'छोड़ो बस ५४; बस 54C के सभी स्टॉप मत बताओ।',
 'Exclude bus 54; show all stops for bus 54.',
])
def test_semicolon_reset_cannot_dispatch_negated_or_contradictory_route(extractor,query):
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
    assert reply.status=='clarification' and 'route_number' not in reply.slots

@pytest.mark.parametrize('query',[
 'Not bus 54; बस ५४सीसीसीसी के सभी स्टॉप बताओ।',
 'Not bus 54; bus 54 ABCD stops please.',
])
def test_unknown_attached_suffix_never_reintroduces_parent_or_ui_default(extractor,query):
    result=extractor.extract(query,'route_stop_sequence',default_transport_mode='metro')
    assert result.slots.get('transport_mode')=='bus'
    assert result.slots.get('route_number')!='54'
    reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='metro')
    assert reply.status=='clarification' and reply.slots.get('route_number')!='54'

@pytest.mark.parametrize('query',[
 'मेट्रो का किराया छोड़ो; बस ५४ की स्टॉप सूची बताओ।',
 'Metro prices ko chhodo; bus 54 all stops dikhao.',
 'एमआरटीएस का किराया छोड़िए; बस 54C के सभी स्टॉप दिखाइए।',
 'MRTS fare chhodkar; bus 54C stop list please.',
 'Blue Line metro fare is not wanted; show all stops for bus 54.',
 'Green Line metro prices chhodo; bus 54C all stops batao.',
])
def test_discarded_goal_mode_and_line_cannot_constrain_positive_bus(extractor,query):
 result=extractor.extract(query,'route_stop_sequence',default_transport_mode='metro')
 assert result.requested_modes==('bus',) and not result.excluded_modes
 assert 'line_name' not in result.slots and not result.multiple_execution_scopes
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='metro')
 assert reply.status=='ok' and reply.slots['transport_mode']=='bus'
@pytest.mark.parametrize('query',[
 'First bus departure ko chhodo; bus 54 all stops batao.',
 'Last bus departure chhodo; bus 54C stop list dikhao.',
 'First train timetable is not wanted; list stops for bus 54.',
 'पहली बस का departure छोड़िए; बस 54C के सभी स्टॉप बताओ।',
])
def test_same_timetable_request_attributes_share_postfix_rejection(extractor,query):
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='ok' and reply.slots['transport_mode']=='bus'
@pytest.mark.parametrize('query',[
 'Exclude bus 27; bus 54 ke all stops chahiye.',
 'छोड़ो बस २७; बस ५४ के सभी स्टॉप चाहिए।',
 'Avoid bus 27; bus 54C ki stop list chahiye.',
 'मत चुनो बस २७; बस 54C की स्टॉप सूची चाहिए।',
])
def test_affirmative_wanted_request_resets_semicolon_list_polarity(extractor,query):
 result=extractor.extract(query,'route_stop_sequence')
 assert result.slots.get('route_number') in {'54','54C'}
 assert result.request_constraints.get('excluded_routes')==['27']
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='ok' and reply.slots['transport_mode']=='bus'
@pytest.mark.parametrize('query',[
 'Exclude bus 27; bus 54 ke all stops nahi chahiye.',
 'छोड़ो बस २७; बस ५४ के सभी स्टॉप नहीं चाहिए।',
 'Exclude bus 54; bus 54 ke all stops chahiye.',
 'Exclude bus 27; bus 54.',
 'First bus departure please; bus 54 all stops batao.',
 'First bus departure and bus 54 stop list please.',
 'Metro fare please; bus 54 all stops dikhao.',
])
def test_discarded_goal_repairs_keep_negative_and_multiple_scope_guards(extractor,query):
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query)
 assert reply.status=='clarification' and not reply.data.get('routes')

@pytest.mark.parametrize('query',[
 'बस २७डी छोड़ो; बस ५४ के सभी स्टॉप बताओ।',
 'बस २७ डी छोड़िए; बस 54C की सभी स्टॉप चाहिए।',
 'बस 27डी को छोड़िए; बस ५४ की स्टॉप सूची दिखाइए।',
 'बस २७-डी छोड़कर; बस 54C के सभी स्टॉप बताओ।',
 'bus 27D ko chhodo; bus 54 all stops dikhao.',
 'Bus 27 D chhodo; bus 54C all stops chahiye.',
])
def test_native_complete_route_owns_avoidance_before_next_mode(extractor,query):
 result=extractor.extract(query,'route_stop_sequence',default_transport_mode='metro')
 assert result.requested_modes==('bus',) and not result.excluded_modes
 assert result.slots.get('route_number') in {'54','54C'}
 assert result.request_constraints.get('excluded_routes')==['27D']
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='metro')
 assert reply.status=='ok' and reply.slots['transport_mode']=='bus'
@pytest.mark.parametrize('query',[
 'बस २७डीडीडीडी छोड़िए; बस ५४ के सभी स्टॉप बताओ।',
 'bus 27ABCD ko chhodo; bus 54 all stops batao.',
])
def test_unknown_excluded_suffix_cannot_execute_parent_over_positive_operand(extractor,query):
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='metro')
 assert reply.status=='ok' and reply.slots['route_number']=='54'
 assert reply.slots['transport_mode']=='bus' and reply.slots['route_number']!='27'
@pytest.mark.parametrize('query',[
 'बस ५४सी छोड़िए; बस 54C के सभी स्टॉप चाहिए।',
 'बस छोड़िए; बस ५४ के सभी स्टॉप बताओ।',
])
def test_suffix_ownership_never_weakens_contradictory_constraints(extractor,query):
 reply=T3Assistant(classifier=FixedClassifier('route_stop_sequence'),extractor=extractor,resolver=extractor.resolver).process_query(query,default_transport_mode='metro')
 assert reply.status=='clarification' and not reply.data.get('routes')
