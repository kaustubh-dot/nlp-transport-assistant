#!/usr/bin/env python3
"""Intent benchmark on held-out template families; no inferred factual E2E score."""
from pathlib import Path
import argparse
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from src.intent_classifier import get_classifier, INTENT_CLASSES

INTENTS_CSV = Path(__file__).resolve().parents[1] / "data/processed/intents.csv"


def validate_splits(df):
    if not {"query", "intent", "split", "template_family"}.issubset(df.columns):
        raise ValueError("Regenerate the dataset with template-family splits.")
    if df.groupby("template_family")["split"].nunique().gt(1).any():
        raise ValueError("Template family leakage across splits")
    if df.groupby("query")["split"].nunique().gt(1).any():
        raise ValueError("Duplicate query leakage across splits")
    if not {"train", "val", "test"}.issubset(set(df["split"])):
        raise ValueError("Explicit train, val and test splits are required")


def evaluate_system(model_type="baseline"):
    df = pd.read_csv(INTENTS_CSV)
    validate_splits(df)
    classifier = get_classifier(model_type)
    if classifier.model is None:
        raise ValueError(f"No trained {model_type} model: refusing to benchmark heuristic fallback")
    test_df = df[df["split"] == "test"]
    predicted = [classifier.predict(q) for q in test_df["query"]]
    print(classification_report(test_df.intent, predicted, labels=INTENT_CLASSES, zero_division=0))
    print("Confusion matrix; label order:", INTENT_CLASSES)
    print(confusion_matrix(test_df.intent, predicted, labels=INTENT_CLASSES))
    for language, subset in test_df.assign(predicted=predicted).groupby("language"):
        print(f"{language}: n={len(subset)}, accuracy={(subset.intent == subset.predicted).mean():.3f}")
    print("Slot and factual end-to-end scores: not measured. Require independently reviewed gold cases.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["baseline", "muril"], default="baseline")
    evaluate_system(parser.parse_args().model)
