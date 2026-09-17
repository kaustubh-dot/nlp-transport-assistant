# tests/test_model_harness.py
"""Tests for multi-model GPU training harness and classifier adapters."""

import os
import pytest
from src.intent_classifier import INTENT_CLASSES, BaseIntentClassifier

EXPECTED_INTENTS = [
    "route_query",
    "service_availability",
    "service_timing",
    "station_information",
    "accessibility",
    "ticketing",
    "out_of_scope"
]


def test_intent_classes_consistency():
    assert len(INTENT_CLASSES) == 7
    assert INTENT_CLASSES == EXPECTED_INTENTS


def test_harness_script_exists():
    harness_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "train_and_compare_models.py")
    assert os.path.exists(harness_path), f"Training harness missing at {harness_path}"


def test_model_registry_available():
    from scripts.train_and_compare_models import MODEL_REGISTRY
    assert "baseline" in MODEL_REGISTRY
    assert "muril" in MODEL_REGISTRY
    assert "indicbert_v2" in MODEL_REGISTRY
    assert "indicbert" in MODEL_REGISTRY
    assert "hingbert" in MODEL_REGISTRY
    assert "xlm_roberta" in MODEL_REGISTRY
    assert "mdeberta" in MODEL_REGISTRY
    assert "minilm" in MODEL_REGISTRY
