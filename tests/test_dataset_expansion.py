# tests/test_dataset_expansion.py
"""Tests for scaled and balanced intent dataset."""

import os
import pandas as pd
import pytest

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed", "intents.csv")


def test_expanded_dataset_scale_and_balance():
    """Dataset must have at least 3,500 samples, all 7 intents, and at least 450 per intent."""
    assert os.path.exists(DATASET_PATH), f"Dataset missing at {DATASET_PATH}"
    df = pd.read_csv(DATASET_PATH)
    assert len(df) >= 3500, f"Expected >= 3500 samples, got {len(df)}"

    expected_intents = {
        "route_query",
        "service_availability",
        "service_timing",
        "station_information",
        "accessibility",
        "ticketing",
        "out_of_scope"
    }
    assert set(df["intent"].unique()) == expected_intents, f"Unexpected intents: {set(df['intent'].unique())}"

    for intent in expected_intents:
        count = len(df[df["intent"] == intent])
        assert count >= 450, f"Intent '{intent}' only has {count} samples, expected >= 450"


def test_split_disjointness():
    """Train, validation, and test splits must exist and be completely disjoint."""
    df = pd.read_csv(DATASET_PATH)
    assert "split" in df.columns, "Missing 'split' column in dataset"
    assert set(df["split"].unique()) == {"train", "val", "test"}

    train_queries = set(df[df["split"] == "train"]["query"].str.strip().str.lower())
    test_queries = set(df[df["split"] == "test"]["query"].str.strip().str.lower())
    val_queries = set(df[df["split"] == "val"]["query"].str.strip().str.lower())

    train_test_overlap = train_queries.intersection(test_queries)
    train_val_overlap = train_queries.intersection(val_queries)

    assert len(train_test_overlap) == 0, f"Data leakage between train and test: {len(train_test_overlap)} overlapping queries"
    assert len(train_val_overlap) == 0, f"Data leakage between train and val: {len(train_val_overlap)} overlapping queries"


def test_script_coverage():
    """Dataset must contain both Devanagari Hindi and Romanized Hinglish samples."""
    df = pd.read_csv(DATASET_PATH)
    assert "script" in df.columns, "Missing 'script' column"
    scripts = set(df["script"].unique())
    assert "devanagari" in scripts
    assert "latin_hinglish" in scripts

    deva_count = len(df[df["script"] == "devanagari"])
    hinglish_count = len(df[df["script"] == "latin_hinglish"])
    assert deva_count >= 1500, f"Expected >= 1500 Devanagari samples, got {deva_count}"
    assert hinglish_count >= 1000, f"Expected >= 1000 Hinglish samples, got {hinglish_count}"
