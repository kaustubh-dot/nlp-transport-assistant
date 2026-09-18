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


def test_frozen_split_integrity():
    """Verifies that the frozen dataset split directory meets all disjointness, balance, and manifest requirements."""
    import json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    split_dir = os.path.join(base_dir, "data", "processed", "split")
    
    train_path = os.path.join(split_dir, "train.csv")
    val_path = os.path.join(split_dir, "validation.csv")
    test_path = os.path.join(split_dir, "test.csv")
    manifest_path = os.path.join(split_dir, "split_manifest.json")

    assert os.path.exists(train_path), "Missing train.csv in split dir"
    assert os.path.exists(val_path), "Missing validation.csv in split dir"
    assert os.path.exists(test_path), "Missing test.csv in split dir"
    assert os.path.exists(manifest_path), "Missing split_manifest.json"

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["split_seed"] == 42
    assert manifest["strategy"] == "family_disjoint_stratified"
    assert manifest["num_train"] == len(train_df)
    assert manifest["num_validation"] == len(val_df)
    assert manifest["num_test"] == len(test_df)

    # Verify all classes present in all splits
    for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        intents = set(df["intent"].unique())
        assert intents == set(INTENT_CLASSES), f"Split {name} missing classes: {set(INTENT_CLASSES) - intents}"

    # Verify zero duplicate query overlap
    train_queries = set(train_df["query"].str.strip().str.lower())
    val_queries = set(val_df["query"].str.strip().str.lower())
    test_queries = set(test_df["query"].str.strip().str.lower())

    assert len(train_queries.intersection(val_queries)) == 0, "Train and Val queries overlap"
    assert len(train_queries.intersection(test_queries)) == 0, "Train and Test queries overlap"
    assert len(val_queries.intersection(test_queries)) == 0, "Val and Test queries overlap"

    # Verify zero template family leakage
    train_families = set(train_df["template_family"].unique())
    val_families = set(val_df["template_family"].unique())
    test_families = set(test_df["template_family"].unique())

    assert len(train_families.intersection(val_families)) == 0, "Train and Val template families overlap"
    assert len(train_families.intersection(test_families)) == 0, "Train and Test template families overlap"
    assert len(val_families.intersection(test_families)) == 0, "Val and Test template families overlap"
