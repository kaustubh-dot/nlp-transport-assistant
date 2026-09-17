"""Unit tests for gazetteer and slot extraction module."""

import pytest
from src.entity_extractor import EntityExtractor


@pytest.fixture
def extractor():
    return EntityExtractor()


def test_extract_origin_destination_hindi(extractor):
    query = "चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?"
    slots = extractor.extract(query)
    assert slots["origin"] == "CHENNAI_CENTRAL"
    assert slots["destination"] == "CHENNAI_AIRPORT"


def test_extract_origin_destination_hinglish(extractor):
    query = "central se airport kaise jaye"
    slots = extractor.extract(query)
    assert slots["origin"] == "CHENNAI_CENTRAL"
    assert slots["destination"] == "CHENNAI_AIRPORT"


def test_extract_mode(extractor):
    query = "सेंट्रल से गिंडी जाने के लिए मेट्रो उपलब्ध है क्या?"
    slots = extractor.extract(query)
    assert slots["transport_mode"] == "metro"
    assert slots["origin"] == "CHENNAI_CENTRAL"
    assert slots["destination"] == "GUINDY"


def test_extract_single_station_accessibility(extractor):
    query = "कोयम्बेडु पर व्हीलचेयर उपलब्ध है क्या?"
    slots = extractor.extract(query)
    assert slots["station"] == "KOYAMBEDU"
    assert slots["information_type"] == "wheelchair"


def test_fuzzy_matching_station(extractor):
    # Slight typo in Chennai Airport: एयरपोट
    query = "सेंट्रल से एयरपोट कैसे जाएं"
    slots = extractor.extract(query)
    assert slots["origin"] == "CHENNAI_CENTRAL"
    assert slots["destination"] == "CHENNAI_AIRPORT"
