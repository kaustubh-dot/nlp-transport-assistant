"""Fresh synthetic parser minimal pairs; no trained/frozen query fixtures."""

import sqlite3

import pytest


@pytest.fixture
def extractor(tmp_path):
    from src.nlp_v2.entities import CanonicalResolver
    from src.nlp_v2.slots import T3SlotExtractor

    path = tmp_path / 'language_extraction.db'
    with sqlite3.connect(path) as conn:
        conn.executescript('''
            CREATE TABLE transport_hubs (hub_id TEXT, hub_name TEXT);
            CREATE TABLE transport_stops (stop_id TEXT, canonical_name TEXT, mode TEXT);
            CREATE TABLE stop_names (stop_id TEXT, name TEXT);
            CREATE TABLE places (place_id TEXT, canonical_name TEXT);
            CREATE TABLE place_names (place_id TEXT, name TEXT);
            CREATE TABLE transport_routes (route_id TEXT, route_short_name TEXT, mode TEXT, status TEXT);
            CREATE TABLE route_stops (route_id TEXT, canonical_stop_id TEXT);
            INSERT INTO transport_stops VALUES ('BUS_CEDAR','Cedar Quay','bus');
            INSERT INTO transport_routes VALUES ('ROUTE_31B','31B','bus','operational');
            INSERT INTO route_stops VALUES ('ROUTE_31B','BUS_CEDAR');
        ''')
    return T3SlotExtractor(CanonicalResolver(path))


@pytest.mark.parametrize('query,code', [
    ('31B ki aakhri bus Cedar Quay se', '31B'),
    ('83C ke stops bus route me dikhao', '83C'),
    ('bus route me ८३सी के स्टॉप बताओ', '83C'),
    ('Bus context: 31-B ki pehli bus', '31B'),
    ('31B# ki bus ke stops', '31B#'),
    ('Bus route 83 ke stops', '83'),
])
def test_possessive_route_codes_preserve_bus_context_and_suffix(extractor, query, code):
    result = extractor.extract(query, 'route_stop_sequence')
    assert result.slots['route_number'] == code


@pytest.mark.parametrize('query', [
    '83C ke stops dikhao', '83 ke stops chahiye', '83 ka price kya hai',
    'Bus ka 8:15 AM departure', 'Bus departure on 2026-11-13',
    'bus ticket for 6 passengers',
])
def test_possessive_route_extension_does_not_promote_unrelated_numbers(extractor, query):
    result = extractor.extract(query, 'route_stop_sequence')
    assert 'route_number' not in result.slots


def test_possessive_competing_routes_are_not_silently_reduced(extractor):
    result = extractor.extract('31B ki bus stops aur 83C ke stops', 'route_stop_sequence')
    assert result.multiple_execution_scopes is True


@pytest.mark.parametrize('query,stage', [
    ('Express bus fare for stage 14', 14),
    ('Express bus fare for 14 stages', 14),
    ('Express bus १४ stage ka kiraya', 14),
    ('Express bus चौदह स्टेज का किराया', 14),
    ('Express bus चौदह चरण का किराया', 14),
    ('Express bus stage number १४ fare', 14),
])
def test_stage_count_order_script_and_unit_preserve_tariff_scope(extractor, query, stage):
    result = extractor.extract(query, 'fare_calculation')
    assert result.slots['stage_number'] == stage
    assert result.slots['service_type'] == 'Express Services'
    assert result.multiple_execution_scopes is False


# Independent literal cardinals, not expectations calculated by parser helpers.
CARDINALS = [
    (1, 'one', 'एक', 'ek'), (2, 'two', 'दो', 'do'),
    (3, 'three', 'तीन', 'teen'), (4, 'four', 'चार', 'chaar'),
    (5, 'five', 'पाँच', 'paanch'), (6, 'six', 'छह', 'chhe'),
    (7, 'seven', 'सात', 'saat'), (8, 'eight', 'आठ', 'aath'),
    (9, 'nine', 'नौ', 'nau'), (10, 'ten', 'दस', 'das'),
    (11, 'eleven', 'ग्यारह', 'gyarah'), (12, 'twelve', 'बारह', 'barah'),
    (13, 'thirteen', 'तेरह', 'terah'), (14, 'fourteen', 'चौदह', 'chaudah'),
    (15, 'fifteen', 'पंद्रह', 'pandrah'), (16, 'sixteen', 'सोलह', 'solah'),
    (17, 'seventeen', 'सत्रह', 'satrah'), (18, 'eighteen', 'अठारह', 'atharah'),
    (19, 'nineteen', 'उन्नीस', 'unnis'), (20, 'twenty', 'बीस', 'bees'),
    (21, 'twenty one', 'इक्कीस', 'ikkis'), (22, 'twenty two', 'बाईस', 'baais'),
    (23, 'twenty three', 'तेईस', 'teis'), (24, 'twenty four', 'चौबीस', 'chaubis'),
    (25, 'twenty five', 'पच्चीस', 'pachis'), (26, 'twenty six', 'छब्बीस', 'chabbis'),
    (27, 'twenty seven', 'सत्ताईस', 'sattais'), (28, 'twenty eight', 'अट्ठाईस', 'atthais'),
    (29, 'twenty nine', 'उनतीस', 'untees'), (30, 'thirty', 'तीस', 'tees'),
]


@pytest.mark.parametrize('stage,en,hi,roman', CARDINALS)
@pytest.mark.parametrize('language', ['en', 'hi', 'roman'])
def test_spelled_stage_cardinals_one_through_thirty(extractor, stage, en, hi, roman, language):
    number = {'en': en, 'hi': hi, 'roman': roman}[language]
    result = extractor.extract(f'Ordinary bus {number} stage ka kiraya', 'fare_calculation')
    assert result.slots['stage_number'] == stage
    assert result.slots['service_type'] == 'Ordinary Services'
    assert result.multiple_execution_scopes is False


@pytest.mark.parametrize('query,stage', [
    ('Ordinary bus पहला स्टेज किराया', 1),
    ('Ordinary bus दूसरे चरण का किराया', 2),
    ('Ordinary bus तीसरे स्टेज का किराया', 3),
    ('Ordinary bus सातवें चरण का किराया', 7),
    ('Ordinary bus ग्यारहवें स्टेज का किराया', 11),
    ('Ordinary bus इक्कीसवें चरण का किराया', 21),
    ('Ordinary bus तीसवाँ स्टेज किराया', 30),
    ('Ordinary bus twenty-five stages ka fare', 25),
])
def test_explicit_stage_ordinals_and_compound_cardinals(extractor, query, stage):
    assert extractor.extract(query, 'fare_calculation').slots['stage_number'] == stage


@pytest.mark.parametrize('query', [
    'Ordinary bus stage 14 aur 18 fare',
    'Ordinary bus fourteen stages aur eighteen stages fare',
    'Ordinary bus चौदह और अठारह स्टेज किराया',
    'Ordinary bus chaudah stage ya atharah stage kiraya',
    'Ordinary bus stage fourteen and eighteen fare',
    'Ordinary bus चौदह स्टेज या stage 18 fare',
    'Ordinary bus stage 14 nahi, stage 18 ka fare',
])
def test_competing_stage_values_never_select_one_tariff(extractor, query):
    result = extractor.extract(query, 'fare_calculation')
    assert result.multiple_execution_scopes is True
    assert 'stage_number' not in result.slots


@pytest.mark.parametrize('query', [
    'Ordinary bus stage 0 ka fare', 'Ordinary bus 31 stages ka fare',
    'Ordinary bus stage १२३ fare', 'Ordinary bus -3 stages fare',
    'Ordinary bus thirty one stages fare', 'Ordinary bus stage thirty one fare',
    'Ordinary bus not stage fourteen fare',
    'Ordinary bus chaudah stage nahi fare',
])
def test_invalid_or_negated_stage_never_executes_tariff(extractor, query):
    result = extractor.extract(query, 'fare_calculation')
    assert 'stage_number' not in result.slots
    assert 'stage_number' in result.missing_execution_slots


def test_stage_negation_does_not_promote_english_do_to_two(extractor):
    result = extractor.extract('Please do stage calculation for Ordinary bus', 'fare_calculation')
    assert 'stage_number' not in result.slots


@pytest.mark.parametrize('query,time', [
    ('Cedar Quay departures shaam 5:45', '17:45:00'),
    ('Cedar Quay departures शाम ५:४५', '17:45:00'),
    ('Cedar Quay departures dopahar 3:25', '15:25:00'),
    ('Cedar Quay departures दोपहर ३:२५', '15:25:00'),
    ('Cedar Quay departures subah 9:35', '09:35:00'),
    ('Cedar Quay departures सुबह ९:३५', '09:35:00'),
    ('Cedar Quay departures raat 11:40', '23:40:00'),
    ('Cedar Quay departures रात ११:४०', '23:40:00'),
    ('Cedar Quay departures shaam 5:45 baje', '17:45:00'),
    ('Cedar Quay departures shaam 5:45 PM', '17:45:00'),
])
def test_numeric_clock_prefix_daypart_is_honored_without_baje(extractor, query, time):
    result = extractor.extract(query, 'scheduled_departure')
    assert result.slots['time'] == time
    assert result.clarification_reason is None


@pytest.mark.parametrize('query', [
    'Cedar Quay departures subah 9:35 PM',
    'Cedar Quay departures shaam 5:45 AM',
    'Cedar Quay departures dopahar 3:85',
    'Cedar Quay departures raat 25:40',
])
def test_conflicting_or_invalid_daypart_clock_clarifies(extractor, query):
    result = extractor.extract(query, 'scheduled_departure')
    assert 'time' not in result.slots
    assert result.clarification_reason == 'temporal_ambiguity'


def test_bare_baje_keeps_daypart_ambiguity(extractor):
    result = extractor.extract('Cedar Quay departures 9:35 baje', 'scheduled_departure')
    assert result.slots['time'] == ['09:35:00', '21:35:00']
    assert result.clarification_reason == 'temporal_ambiguity'


def test_daypart_change_preserves_explicit_clock_date_and_service_day_guard(extractor):
    explicit = extractor.extract('Cedar Quay bus 31B departure on 2026-11-13 at 19:05:30', 'scheduled_departure')
    assert explicit.slots['time'] == '19:05:30'
    assert explicit.slots['date'] == '2026-11-13'
    assert explicit.slots['route_number'] == '31B'
    service_day = extractor.extract('Cedar Quay departure at 25:10', 'scheduled_departure')
    assert 'time' not in service_day.slots
    assert service_day.clarification_reason == 'temporal_ambiguity'

@pytest.mark.parametrize('word', ['बसें', 'बसों'])
def test_hindi_bus_inflections_keep_explicit_mode(extractor, word):
    result = extractor.extract(f'Cedar Quay से {word} का अंतराल बताओ', 'service_frequency')
    assert result.slots['transport_mode'] == 'bus'

@pytest.mark.parametrize('word', ['लोकल रेल', 'लोकल ट्रेन'])
def test_hindi_local_rail_phrase_is_explicit_suburban_mode(extractor, word):
    result = extractor.extract(f'Cedar Quay से {word} का समय बताओ', 'scheduled_departure')
    assert result.slots['transport_mode'] == 'suburban_rail'
    assert 'temporal_relative' not in result.slots


def test_hindi_night_service_cannot_fall_back_to_ordinary(extractor):
    result = extractor.extract('रात्रि सेवा की बस में पाँच स्टेज का भाड़ा', 'fare_calculation')
    assert result.slots['service_type'] == 'Night Services'
    assert result.slots['stage_number'] == 5


def test_explicitly_unknown_service_class_requires_class_clarification(extractor):
    result = extractor.extract('बस में ४ स्टेज के पैसे, सेवा का प्रकार नहीं मालूम', 'fare_calculation')
    assert result.slots['stage_number'] == 4
    assert 'service_type' in result.missing_execution_slots
    assert 'service_type' not in result.slots
