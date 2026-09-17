# tests/test_champion_integration.py
"""Integration tests verifying champion model deployment in the pipeline."""

import pytest
from src.pipeline import TransportAssistant
from src.intent_classifier import TransformerIntentClassifier, get_classifier


def test_champion_model_loading():
    """Verify that IndicBERT v2 (indicbert_v2) loads as a transformer classifier."""
    clf = get_classifier("indicbert_v2")
    assert isinstance(clf, TransformerIntentClassifier)
    assert clf.model_key == "indicbert_v2"


def test_pipeline_with_champion_model():
    """Verify end-to-end transport assistant pipeline using the champion model."""
    pipeline = TransportAssistant(model_type="indicbert_v2")
    
    # Route query
    res = pipeline.process_query("चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?")
    assert res["intent"] == "route_query"
    assert res["slots"]["origin"] == "CHENNAI_CENTRAL"
    assert res["slots"]["destination"] == "CHENNAI_AIRPORT"
    assert "चेन्नई सेंट्रल" in res["response_hi"]
    assert "एयरपोर्ट" in res["response_hi"]


def test_champion_model_accessibility_and_safety():
    pipeline = TransportAssistant(model_type="indicbert_v2")

    # Accessibility query
    res_acc = pipeline.process_query("क्या कोयम्बेडु स्टेशन पर लिफ्ट और व्हीलचेयर है?")
    assert res_acc["intent"] == "accessibility"
    assert res_acc["slots"]["station"] == "KOYAMBEDU"
    assert ("हाँ" in res_acc["response_hi"] or "उपलब्ध" in res_acc["response_hi"])

    # Out of scope refusal
    res_oos = pipeline.process_query("आज चेन्नई में मौसम कैसा रहेगा?")
    assert res_oos["intent"] == "out_of_scope"
    assert "केवल चेन्नई सार्वजनिक परिवहन" in res_oos["response_hi"]
