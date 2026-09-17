"""Regression cases for known fabricated/misattributed answers (not a release benchmark)."""
import pytest
from src.response_generator import ResponseGenerator
from src.retrieval import TransitRetriever


@pytest.fixture
def generator():
    return ResponseGenerator()


@pytest.mark.parametrize('intent,data', [
    ('service_timing', {}),
    ('service_timing', {'timings': [{'first_service':'05:00', 'last_service':'23:00'}]}),
    ('ticketing', {}),
    ('ticketing', {'estimated_fare': 50, 'min_fare': 10, 'max_fare': 60}),
])
def test_unsupported_financial_and_schedule_claims(generator, intent, data):
    response = generator.generate(intent, {'transport_mode': 'bus'}, data)
    assert 'उपलब्ध नहीं' in response
    assert not any(x in response for x in ['05:00', '23:00', '₹', '20%'])


def test_tactile_absence_is_not_overridden_by_lift(generator):
    response = generator.generate('accessibility', {'station':'TAMBARAM', 'information_type':'tactile_paths'},
        {'facilities': {'tactile_paths':0, 'lift_available':1, 'wheelchair_available':1}})
    assert 'उपलब्ध नहीं' in response
    assert 'मेट्रो स्टेशन' not in response


@pytest.mark.parametrize('facilities', [None, {}, {'lift_available': None}])
def test_missing_facilities_remain_unknown(generator, facilities):
    response = generator.generate('accessibility', {'station':'GUINDY','information_type':'lift'}, {'facilities':facilities})
    assert 'जानकारी उपलब्ध नहीं' in response


def test_route_does_not_invent_fare_or_duration(generator):
    response = generator.generate('route_query', {'origin':'A','destination':'B'},
        {'routes':[{'line_name':'Blue Line','mode':'metro','distance_km':20}]})
    assert 'Blue Line' in response
    assert '₹' not in response and 'मिनट' not in response


def test_unknown_route_is_not_service_denial(generator):
    response = generator.generate('service_availability', {'origin':'A','destination':'B','transport_mode':'metro'}, {'available':False})
    assert 'जानकारी डेटाबेस में नहीं मिली' in response


def test_transfer_is_not_direct(generator):
    response = generator.generate('service_availability', {'origin':'A','destination':'B'},
        {'available':True,'routes':[{'direct':0}]})
    assert 'बदलाव' in response
    assert 'सीधी सेवा' not in response


def test_missing_station_record_does_not_invent_amenities(generator):
    response = generator.generate('station_information', {'station':'A'}, {'station_info':None})
    assert 'जानकारी डेटाबेस में उपलब्ध नहीं' in response
    assert 'लिफ्ट' not in response


def test_ticket_retrieval_never_synthesizes_prices(tmp_path):
    retriever = TransitRetriever(str(tmp_path / 'missing.db'))
    assert retriever.get_ticketing_info('A','B','bus') == {}
