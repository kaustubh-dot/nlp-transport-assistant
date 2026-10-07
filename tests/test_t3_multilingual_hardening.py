"""Independently authored extraction regressions from canonical names/dev semantics."""
import pytest
from src.nlp_v2.contracts import IntentPrediction

@pytest.fixture(scope='module')
def resolver():
    from src.nlp_v2.entities import CanonicalResolver
    return CanonicalResolver()

@pytest.mark.parametrize('query,intent,expected', [
    ('बस रूट २५आर अलवर तिरुनगर पर रुकती है?','route_stop_membership',{'route_number':'25R','stop':'BUS_10235'}),
    ('अलवर तिरुनगर पर बस रूट २५ आर का अंतराल?','service_frequency',{'route_number':'25R','station':'BUS_10235'}),
    ('पूनमल्ली बस टर्मिनस से प्रकाशित बस समय?','scheduled_departure',{'station':'BUS_5821'}),
    ('पूनमल्ली bus terminus से आखिरी बस?','first_and_last_service',{'station':'BUS_5821'}),
    ('मरीना बीच के पास मेट्रो?','nearest_transport',{'landmark':'OSM_POI_12137617372','transport_mode':'metro'}),
    ('MARINA बीच के पास metro?','nearest_transport',{'landmark':'OSM_POI_12137617372','transport_mode':'metro'}),
    ('bs 25-r stops pls','route_stop_sequence',{'route_number':'25R','transport_mode':'bus'}),
    ('Deluxw bs stage 7 fare pls','fare_calculation',{'service_type':'Deluxe Services','stage_number':7,'transport_mode':'bus'}),
    ('mnthly pass rules pls','ticketing_and_passes',{'ticket_type':'monthly_pass'}),
])
def test_bounded_multilingual_slots(resolver,query,intent,expected):
    from src.nlp_v2.slots import T3SlotExtractor
    x=T3SlotExtractor(resolver).extract(query,intent)
    assert x.clarification_reason is None
    assert all(x.slots.get(k)==v for k,v in expected.items())

@pytest.mark.parametrize('suffix,expected',[('आर','R'),('जी','G'),('बी','B'),('सी','C'),('डी','D'),('ए','A'),('ई','E')])
def test_hindi_route_letter_names_are_bounded(suffix,expected):
    from src.nlp_v2.slots import _route_number
    assert _route_number('बस रूट २५'+suffix+' के पड़ाव?') == '25'+expected

@pytest.mark.parametrize('query',['बस रूट २५ज़ेड के पड़ाव?','बस २५क्यू के पड़ाव?', 'बस २५आर् के पड़ाव?'])
def test_unknown_route_suffix_does_not_silently_truncate(query):
    from src.nlp_v2.slots import _route_number
    assert _route_number(query) is None


def test_new_exact_alias_preserves_duplicate_physical_nodes(resolver):
    spans=resolver.find_spans('अलवर तिरुनगर')
    assert len(spans)==1
    r=resolver.resolve(spans[0],'stop','route_stop_membership',mode='bus')
    assert r.ambiguous and len(r.candidates)==3
    assert resolver.find_spans('अलवर तिरुनगx') == ()

@pytest.mark.parametrize('service',['Deluxz','Expresz','Deluxe and Ordinary'])
def test_unrecognized_or_multiple_service_classes_do_not_get_ordinary_fare(resolver,service):
    from src.nlp_v2.assistant import T3Assistant
    class Fixed:
        def predict(self,query): return IntentPrediction('fare_calculation',('fare_calculation',),.9)
    r=T3Assistant(classifier=Fixed(),resolver=resolver).process_query(f'{service} bus stage 7 fare?')
    assert r.status=='clarification'
    assert r.missing_slots==('service_type',)
    assert 'amount' not in r.data


def test_new_extraction_normalization_does_not_change_model_raw_query(resolver):
    from src.nlp_v2.assistant import T3Assistant
    class Spy:
        def __init__(self): self.seen=[]
        def predict(self,query):
            self.seen.append(query)
            return IntentPrediction('route_stop_sequence',('route_stop_sequence',),.9)
    q='बस रूट २५आर — STOPs pls!'
    spy=Spy();r=T3Assistant(classifier=spy,resolver=resolver).process_query(q)
    assert spy.seen==[q] and r.raw_query==q
    assert r.slots['route_number']=='25R'


@pytest.mark.parametrize('word',['right','light','eight'])
def test_common_words_near_night_are_not_service_spelling_errors(resolver,word):
    from src.nlp_v2.slots import T3SlotExtractor
    result=T3SlotExtractor(resolver).extract(f'{word} bus stage 7 fare please','fare_calculation')
    assert not result.missing_execution_slots


def test_non_bus_stage_scope_does_not_ask_non_actionable_service_class(resolver):
    from src.nlp_v2.assistant import T3Assistant
    class Fixed:
        def predict(self,query): return IntentPrediction('fare_calculation',('fare_calculation',),.9)
    r=T3Assistant(classifier=Fixed(),resolver=resolver).process_query('Deluxz metro stage 7 fare?')
    assert r.status=='unavailable'
    assert not r.missing_slots and 'amount' not in r.data


@pytest.mark.parametrize('query', ['बस रूट २५ आर् के पड़ाव?', 'बस रूट २५ ज़ेड के पड़ाव?',
                                   'बस रूट १०२ क्यू के पड़ाव?', 'bs 102 Rअ stops?'])
def test_spaced_unknown_route_suffix_cannot_select_shorter_route(query):
    from src.nlp_v2.slots import _route_number
    assert _route_number(query) is None


def test_normal_hindi_postposition_is_not_an_unknown_route_suffix():
    from src.nlp_v2.slots import _route_number
    assert _route_number('बस रूट २५ के पड़ाव?') == '25'
    assert _route_number('बस रूट २५ आराम से पड़ाव बताइए') == '25'


@pytest.mark.parametrize('query', [
    'mnthly pass Deluxz bus stage 7 fare?',
    'Expresz bus stage 7 distance fare?',
    'Deluxz bus fare from Island ground Terminus to Annasquare?',
])
def test_known_fare_scope_rejection_precedes_service_spelling_question(resolver,query):
    from src.nlp_v2.assistant import T3Assistant
    class Fixed:
        def predict(self,query): return IntentPrediction('fare_calculation',('fare_calculation',),.9)
    r=T3Assistant(classifier=Fixed(),resolver=resolver).process_query(query)
    assert r.status == 'unavailable'
    assert not r.missing_slots and 'amount' not in r.data


@pytest.mark.parametrize('ending', ['during this deluge', 'beside the Empress hotel', 'please do not delude me'])
def test_unrelated_words_are_not_service_class_modifiers(resolver,ending):
    from src.nlp_v2.slots import T3SlotExtractor
    x=T3SlotExtractor(resolver).extract('Bus stage 7 fare '+ending+'?', 'fare_calculation')
    assert not x.missing_execution_slots


@pytest.mark.parametrize('query', ['Deluxz ticket bus stage 7 fare?', 'stage 7 fare on a Deluxz please?',
                                   'bus stage 7 fare for Expresz please?', 'Deluxz buses stage 7 fare?'])
def test_service_spelling_guard_does_not_depend_on_immediate_bus_word(resolver,query):
    from src.nlp_v2.assistant import T3Assistant
    class Fixed:
        def predict(self,query): return IntentPrediction('fare_calculation',('fare_calculation',),.9)
    r=T3Assistant(classifier=Fixed(),resolver=resolver).process_query(query)
    assert r.status == 'clarification'
    assert r.missing_slots == ('service_type',) and 'amount' not in r.data


@pytest.mark.parametrize('query,expected', [
    ('बस २१जी।', '21G'), ('बस २५।', '25'), ('bus 25R।', '25R'),
    ('बस रूट २५आर।', '25R'), ('बस रूट २५ आर#।', '25R#'),
    ('bus 25 R# stops?', '25R#'),
])
def test_route_boundary_accepts_hindi_punctuation_preserving_hash(query, expected):
    from src.nlp_v2.slots import _route_number
    assert _route_number(query) == expected


@pytest.mark.parametrize('query', [
    'बस रूट २५ ज़ेड।', 'बस रूट २५ आर्।', 'बस रूट १०२ क्यू# के पड़ाव?',
    'बस रूट २५ ज़ेड के पड़ाव?', 'बस रूट २५ आर्)', 'बस रूट २५ आर्—के',
    'बस रूट २५ ज़ेड-X के पड़ाव?', 'बस रूट २५ आर्-X के पड़ाव?',
    'बस रूट २५ आर्#-X के पड़ाव?',
])
def test_route_suffix_rejection_survives_punctuation_and_unicode_variants(query):
    from src.nlp_v2.slots import _route_number
    assert _route_number(query) is None
