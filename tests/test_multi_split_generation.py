"""Tests for multi-split dataset generation with seed control."""

import os
import pytest
import pandas as pd
from scripts.generate_intent_dataset import generate_dataset
from src.intent_classifier import INTENT_CLASSES


def test_multi_split_generation_disjointness_and_balance():
    """Verifies that generate_dataset produces balanced, disjoint splits for any given seed."""
    df_42 = generate_dataset(seed=42, samples_per_intent=200)

    assert len(df_42) >= 1400
    assert set(df_42["split"].unique()) == {"train", "val", "test"}

    # Verify all classes present in all splits
    for s in ["train", "val", "test"]:
        split_intents = set(df_42[df_42["split"] == s]["intent"].unique())
        assert split_intents == set(INTENT_CLASSES), f"Split {s} missing classes: {set(INTENT_CLASSES) - split_intents}"

    # Verify zero query overlap between train and test/val
    train_queries = set(df_42[df_42["split"] == "train"]["query"].str.strip().str.lower())
    val_queries = set(df_42[df_42["split"] == "val"]["query"].str.strip().str.lower())
    test_queries = set(df_42[df_42["split"] == "test"]["query"].str.strip().str.lower())

    assert len(train_queries.intersection(val_queries)) == 0, "Found overlap between train and val queries"
    assert len(train_queries.intersection(test_queries)) == 0, "Found overlap between train and test queries"


def test_different_seeds_produce_different_test_splits():
    """Verifies that distinct seeds produce distinct holdout test family allocations."""
    df_42 = generate_dataset(seed=42, samples_per_intent=200)
    df_1337 = generate_dataset(seed=1337, samples_per_intent=200)

    test_families_42 = set(df_42[df_42["split"] == "test"]["template_family"].unique())
    test_families_1337 = set(df_1337[df_1337["split"] == "test"]["template_family"].unique())

    assert test_families_42 != test_families_1337, "Expected different test template families for different seeds"
