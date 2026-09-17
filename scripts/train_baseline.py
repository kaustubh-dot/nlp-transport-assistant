#!/usr/bin/env python3
"""Trains baseline TF-IDF + Logistic Regression intent classifier.

Outputs: models/baseline/model.pkl
"""
import os
import sys
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.intent_classifier import TfidfBaselineClassifier, INTENT_CLASSES
from scripts.evaluate import validate_splits

INTENTS_CSV = BASE_DIR / "data/processed/intents.csv"
MODEL_PKL = BASE_DIR / "models/baseline/model.pkl"


def train_baseline(data_path: Path = INTENTS_CSV, model_out: Path = MODEL_PKL):
    """Fits word+char n-gram TF-IDF and Logistic Regression on train+val splits."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    df = pd.read_csv(data_path)
    validate_splits(df)

    # Train on train split, evaluate on val split
    train_df = df[df["split"].isin(["train", "val"])]

    vectorizer = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 3), analyzer="word")),
        ("char", TfidfVectorizer(ngram_range=(2, 5), analyzer="char_wb"))
    ])

    print(f"Vectorizing {len(train_df)} samples...")
    X_train = vectorizer.fit_transform(train_df["query"])
    y_train = train_df["intent"]

    print("Fitting Logistic Regression...")
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    clf.fit(X_train, y_train)

    baseline_classifier = TfidfBaselineClassifier(str(model_out))
    baseline_classifier.model = clf
    baseline_classifier.vectorizer = vectorizer
    baseline_classifier.classes_ = INTENT_CLASSES
    baseline_classifier.save(str(model_out))
    print(f"Model saved successfully to {model_out}")


if __name__ == "__main__":
    train_baseline()
