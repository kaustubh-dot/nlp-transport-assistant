"""End-to-end integration tests for the full TransportAssistant pipeline."""

import pytest
from src.pipeline import TransportAssistant
from scripts.build_transport_db import init_db, export_aliases_csv


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    export_aliases_csv()


@pytest.fixture
def assistant(tmp_path):
    # Integration fixtures use deterministic heuristics; trained-model quality is
    # measured separately on the held-out benchmark, not these four examples.
    from src.intent_classifier import TfidfBaselineClassifier
    assistant = TransportAssistant(model_type="baseline")
    assistant.classifier = TfidfBaselineClassifier(str(tmp_path / "absent.pkl"))
    return assistant


def test_e2e_route_query(assistant):
    res = assistant.process_query("चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?")
    assert res["intent"] == "route_query"
    assert res["slots"]["origin"] == "CHENNAI_CENTRAL"
    assert res["slots"]["destination"] == "CHENNAI_AIRPORT"
    assert "चेन्नई सेंट्रल" in res["response_hi"]
    assert "एयरपोर्ट" in res["response_hi"]
    assert "मेट्रो" in res["response_hi"]


def test_e2e_service_availability(assistant):
    res = assistant.process_query("सेंट्रल से गिंडी के लिए मेट्रो उपलब्ध है क्या?")
    assert res["intent"] == "service_availability"
    assert res["slots"]["transport_mode"] == "metro"
    assert "हाँ" in res["response_hi"]


def test_e2e_accessibility(assistant):
    res = assistant.process_query("कोयम्बेडु स्टेशन पर व्हीलचेयर मिलेगी क्या?")
    assert res["intent"] == "accessibility"
    assert res["slots"]["station"] == "KOYAMBEDU"
    assert "व्हीलचेयर" in res["response_hi"]


def test_e2e_out_of_scope(assistant):
    res = assistant.process_query("आज चेन्नई में मौसम कैसा है?")
    assert res["intent"] == "out_of_scope"
    assert "सार्वजनिक परिवहन" in res["response_hi"]
