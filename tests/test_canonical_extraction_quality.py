"""Independent linguistic safety families; no observed challenge wording."""
import pytest
from src.nlp_v2.entities import CanonicalResolver
from src.nlp_v2.slots import T3SlotExtractor

@pytest.fixture(scope='module')
def extractor():return T3SlotExtractor(CanonicalResolver())


@pytest.mark.parametrize('query,positive,excluded', [
 ('Nathapettai se Pattaravakkam bus nahi local train raasta','suburban_rail','bus'),
 ('Nathapettai से Pattaravakkam मेट्रो नहीं बस से जाना है','bus','metro'),
 ('Nathapettai to Pattaravakkam no bus, rail route','suburban_rail','bus'),
 ('Nathapettai to Pattaravakkam train mat lena, metro route','metro','suburban_rail'),
 ('Nathapettai se Pattaravakkam local nahi bus route','bus','suburban_rail'),
])
def test_negated_mode_is_excluded_with_positive_override(extractor,query,positive,excluded):
    result=extractor.extract(query,'point_to_point_route',default_transport_mode=excluded)
    assert result.requested_modes == (positive,)
    assert result.slots['transport_mode']==positive
    assert excluded in result.excluded_modes

@pytest.mark.parametrize('query', ['bus nahi','बस मत लेना','not by bus','no bus'])
def test_ui_default_cannot_reintroduce_negated_only_mode(extractor,query):
    result=extractor.extract('Nathapettai to Pattaravakkam '+query,'point_to_point_route',default_transport_mode='bus')
    assert not result.requested_modes and 'transport_mode' not in result.slots
    assert result.excluded_modes == ('bus',)

@pytest.mark.parametrize('query', [
 'Nathapettai se Pattaravakkam local train ka raasta Padi hote hue batao',
 'Nathapettai से Pattaravakkam लोकल ट्रेन का रास्ता Padi होते हुए बताओ',
 'Local train from Nathapettai via Padi to Pattaravakkam',
])
def test_waypoint_postposition_and_preposition_keep_roles(extractor,query):
    result=extractor.extract(query,'point_to_point_route')
    assert result.slots['origin']=='RAIL_NATHAPETTAI'
    assert result.slots['destination']=='RAIL_PATTARAVAKKAM'
    assert result.slots['via']=='RAIL_PADI'
    assert not result.multiple_execution_scopes and not result.missing_execution_slots

@pytest.mark.parametrize('query,time', [
 ('बस 54 रात दस बजे के बाद','22:00:00'), ('bus 54 shaam paanch baje ke baad','17:00:00'),
 ('bus 54 dopahar do baje ke baad','14:00:00'), ('bus 54 subah nau baje','09:00:00'),
 ('bus 54 after eleven AM','11:00:00'), ('bus 54 सुबह ९ बजे','09:00:00'),
])
def test_bounded_number_word_and_native_clocks(extractor,query,time):
    result=extractor.extract(query+' at Adyar','scheduled_departure')
    assert result.slots['time']==time and not result.clarification_reason

@pytest.mark.parametrize('query', ['bus 54 saadhe das baje','bus 54 साढ़े दस बजे','bus 54 thirteen AM'])
def test_unsupported_clock_is_not_silently_reduced(extractor,query):
    result=extractor.extract(query+' at Adyar','scheduled_departure')
    assert 'time' not in result.slots and result.clarification_reason=='temporal_ambiguity'

@pytest.mark.parametrize('query,relative', [('aane wale kal','tomorrow'),('आने वाले कल','tomorrow'),('beete kal','yesterday'),('बीते कल','yesterday')])
def test_explicit_relative_day_keeps_direction(extractor,query,relative):
    result=extractor.extract('bus 54 at Adyar '+query,'scheduled_departure')
    assert result.slots['temporal_relative']==relative and result.clarification_reason is None


def test_native_iso_date_normalizes_with_calendar_validation(extractor):
    result=extractor.extract('बस 54 Adyar २०२६-११-०७','scheduled_departure')
    assert result.slots['date']=='2026-11-07' and not result.clarification_reason

@pytest.mark.parametrize('query,code', [('M81 ke sab stops','M81'),('29C kab chalegi','29C'),('क्रमांक २९सी की सूची','29C')])
def test_explicit_alphanumeric_route_does_not_require_bus_word(extractor,query,code):
    assert extractor.extract(query,'route_stop_sequence').slots['route_number']==code

@pytest.mark.parametrize('query', ['I have 7 passengers','after nine AM','2026-11-07','मार्ग शब्द'])
def test_ordinary_counts_and_times_are_not_routes(extractor,query):
    assert 'route_number' not in extractor.extract(query,'route_stop_sequence').slots

@pytest.mark.parametrize('query', ['Adyar bus route 54 evening frequency','Adyar पर बस 54 की शाम वाली आवृत्ति'])
def test_period_only_scope_does_not_become_unfiltered_schedule(extractor,query):
    result=extractor.extract(query,'service_frequency')
    assert result.request_constraints['day_period']=='evening'
    assert result.unsupported_temporal_scope


def test_walking_metric_is_preserved_as_unsupported_scope(extractor):
    result=extractor.extract('Nehru Park metro station ke paas nearest bus stop walking distance se batao','nearest_transport')
    assert result.request_constraints['distance_metric']=='walking_network'



@pytest.mark.parametrize('query,mode',[('metro train','metro'),('MRTS train','mrts'),('मेट्रो ट्रेन','metro'),('एमआरटीएस ट्रेन','mrts')])
def test_specific_train_kind_does_not_duplicate_generic_rail(extractor,query,mode):
    assert extractor.extract('Nathapettai to Pattaravakkam '+query,'point_to_point_route').requested_modes==(mode,)

@pytest.mark.parametrize('query',['after forty AM','ढाई बजे','quarter past ten AM','sawa ten AM','सवा दस बजे'])
def test_unbounded_clock_words_always_require_clarification(extractor,query):
    result=extractor.extract('bus 54 at Adyar '+query,'scheduled_departure')
    assert 'time' not in result.slots and result.clarification_reason=='temporal_ambiguity'

@pytest.mark.parametrize('query',['wait 10min for stops','route information 4km away','7 passengers then 10min'])
def test_bare_numeric_units_are_not_route_codes(extractor,query):
    assert 'route_number' not in extractor.extract(query,'route_stop_sequence').slots


def test_route_code_after_a_passenger_count_is_not_missed(extractor):
    assert extractor.extract('7 passengers M81 ke stops','route_stop_sequence').slots['route_number']=='M81'


def test_unknown_postfix_waypoint_never_captures_following_endpoint(extractor):
    result=extractor.extract('Local train from Nathapettai se Unknown Junction hote hue Padi to Pattaravakkam route','point_to_point_route')
    assert 'via' in result.missing_execution_slots and result.slots.get('via')!='RAIL_PADI'

@pytest.mark.parametrize('query',[
 'Nathapettai se Pattaravakkam local train after nine AM and eleven AM',
 'Nathapettai se Pattaravakkam local train after nine AM, eleven AM',
 'Nathapettai se Pattaravakkam local train beete kal aur aane wale kal',
 'M81, 29C ke stops batao',
])
def test_multiple_literal_constraints_are_not_reduced_to_first(extractor,query):
    intent='route_stop_sequence' if query.startswith('M81') else 'point_to_point_route'
    assert extractor.extract(query,intent).multiple_execution_scopes

@pytest.mark.parametrize('query',[
 'Nehru Park metro station se nearest bus stop paidal chal kar batao',
 'Nehru Park मेट्रो स्टेशन से पैदल चलकर सबसे पास का बस स्टॉप',
 'nearest bus stop within a five minute walk of Nehru Park metro station',
])
def test_walking_access_forms_do_not_become_straight_line(extractor,query):
    result=extractor.extract(query,'nearest_transport')
    assert result.request_constraints['distance_metric']=='walking_network'

@pytest.mark.parametrize('phrase,excluded',[('metro train nahi','metro'),('मेट्रो ट्रेन नहीं','metro'),('MRTS train nahi','mrts')])
def test_compound_train_mode_negation_applies_to_modifier(extractor,phrase,excluded):
    result=extractor.extract('Nathapettai to Pattaravakkam '+phrase,'point_to_point_route',default_transport_mode='bus')
    assert excluded in result.excluded_modes and excluded not in result.requested_modes


def test_contradictory_period_clock_preserves_temporal_clarification(extractor):
    result=extractor.extract('bus 54 at Adyar शाम 9 AM','scheduled_departure')
    assert result.clarification_reason=='temporal_ambiguity' and not result.unsupported_temporal_scope

@pytest.mark.parametrize('clock',["evening half past ten oclock","evening quarter to ten o'clock"])
def test_fractional_english_oclock_is_not_truncated(extractor,clock):
    result=extractor.extract('Nathapettai se Pattaravakkam local train '+clock,'point_to_point_route')
    assert 'time' not in result.slots and result.clarification_reason=='temporal_ambiguity'


def test_ordinary_ordinal_does_not_hide_later_route_code(extractor):
    assert extractor.extract('3rd stop on M81','route_stop_sequence').slots['route_number']=='M81'

@pytest.mark.parametrize('query',['83C़X ke stops','prefix़M81 ke stops'])
def test_bare_route_never_splits_unicode_marked_word(extractor,query):
    assert 'route_number' not in extractor.extract(query,'route_stop_sequence').slots

@pytest.mark.parametrize('query',['I am at Adyar waiting for bus 54','I am looking for the bus 54 departure at Adyar'])
def test_english_auxiliary_am_is_not_a_clock(extractor,query):
    assert extractor.extract(query,'scheduled_departure').clarification_reason is None


def test_plural_route_cue_preserves_coordinated_numeric_routes(extractor):
    result=extractor.extract('List bus routes 94 and 107Z stop sequences','route_stop_sequence')
    assert result.multiple_execution_scopes
