"""Intent classification module for Chennai Transport Assistant.

Provides:
  - Baseline: Word + Char n-gram TF-IDF with Logistic Regression
  - Transformer: Fine-tuned MuRIL (google/muril-base-cased)
  - Rule-based heuristic fallback when weights are not yet saved
"""

import os
import re
import pickle
from typing import Dict, List, Tuple, Optional, Any

from src.normalization import normalize_text

# Supported 7 intent labels
INTENT_CLASSES = [
    "route_query",
    "service_availability",
    "service_timing",
    "station_information",
    "accessibility",
    "ticketing",
    "out_of_scope"
]


class BaseIntentClassifier:
    """Base interface for intent classifiers."""

    def predict(self, query: str) -> str:
        raise NotImplementedError

    def predict_with_confidence(self, query: str) -> Tuple[str, float]:
        raise NotImplementedError


class RuleBasedFallbackClassifier(BaseIntentClassifier):
    """Robust heuristic classifier used before model weights are serialized."""

    def predict_with_confidence(self, query: str) -> Tuple[str, float]:
        text = normalize_text(query)

        # Accessibility
        if any(w in text for w in ["व्हीलचेयर", "wheelchair", "रैंप", "ramp", "लिफ्ट", "lift", "एलिवेटर", "elevator", "दिव्यांग", "स्पर्श पथ", "tactile"]):
            return "accessibility", 0.92

        # Service Timing
        if any(w in text for w in ["आखिरी", "पहली", "समय", "timing", "first", "last", "टाइम", "कितने बजे", "operating hours", "शेड्यूल", "schedule", "frequency"]):
            return "service_timing", 0.88

        # Ticketing & Fare
        if any(w in text for w in ["किराया", "fare", "टिकट", "ticket", "स्मार्ट कार्ड", "smart card", "पास", "pass", "टोकन", "token", "रुपये", "price"]):
            return "ticketing", 0.90

        # Service Availability
        if any(w in text for w in ["उपलब्ध", "available", "मिलेगी", "चलती है", "direct", "सीधी", "कनेक्टिविटी", "connectivity"]):
            return "service_availability", 0.89

        # Route Query
        if any(w in text for w in ["कैसे जाऊँ", "कैसे जाएँ", "जाना है", "रास्ता", "route", "how to go", "kaise jaye", "मार्ग", "पहुंच"]):
            return "route_query", 0.91

        # Station Information
        if any(w in text for w in ["सुविधा", "facility", "facilities", "जंक्शन", "junction", "इंटरचेंज", "interchange", "प्लेटफॉर्म", "platform", "स्टेशन पर"]):
            return "station_information", 0.85

        # Check if query has origin/destination words (default to route_query if transit locations exist)
        if any(w in text for w in ["से", "to", "तक", "from"]):
            return "route_query", 0.75

        # Out of scope defaults (weather, food, chit-chat)
        if any(w in text for w in ["मौसम", "weather", "क्रिकेट", "cricket", "मैच", "होटल", "hotel", "रेस्टोरेंट", "खाना", "चुटकुला", "joke"]):
            return "out_of_scope", 0.95

        return "route_query", 0.50

    def predict(self, query: str) -> str:
        intent, _ = self.predict_with_confidence(query)
        return intent


class TfidfBaselineClassifier(BaseIntentClassifier):
    """Word + Character n-gram TF-IDF with Logistic Regression."""

    def __init__(self, model_path: Optional[str] = None):
        self.fallback = RuleBasedFallbackClassifier()
        self.model = None
        self.vectorizer = None
        self.classes_ = INTENT_CLASSES

        if model_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, "models", "baseline", "model.pkl")
        self.model_path = model_path

        if os.path.exists(self.model_path):
            self.load(self.model_path)

    def load(self, path: str):
        """Loads serialized model and vectorizer."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.model = data.get("model")
            self.vectorizer = data.get("vectorizer")
            self.classes_ = data.get("classes", INTENT_CLASSES)

    def save(self, path: str):
        """Serializes model and vectorizer."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "vectorizer": self.vectorizer,
                "classes": self.classes_
            }, f)

    def predict_with_confidence(self, query: str) -> Tuple[str, float]:
        norm_text = normalize_text(query)
        if self.model is None or self.vectorizer is None:
            return self.fallback.predict_with_confidence(norm_text)

        X = self.vectorizer.transform([norm_text])
        probs = self.model.predict_proba(X)[0]
        max_idx = probs.argmax()
        intent = self.model.classes_[max_idx]
        confidence = float(probs[max_idx])
        return intent, confidence

    def predict(self, query: str) -> str:
        intent, _ = self.predict_with_confidence(query)
        return intent


class MurilIntentClassifier(BaseIntentClassifier):
    """Transformer classifier using fine-tuned MuRIL (google/muril-base-cased)."""

    def __init__(self, model_dir: Optional[str] = None):
        self.fallback = RuleBasedFallbackClassifier()
        self.model = None
        self.tokenizer = None
        self.device = "cpu"

        if model_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_dir, "models", "muril")
        self.model_dir = model_dir

        if os.path.exists(os.path.join(self.model_dir, "config.json")):
            self._load_transformer()

    def _load_transformer(self):
        """Loads Hugging Face tokenizer and model weights."""
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
            self.model.to(self.device)
            self.model.eval()
        except Exception:
            self.model = None

    def predict_with_confidence(self, query: str) -> Tuple[str, float]:
        norm_text = normalize_text(query)
        if self.model is None or self.tokenizer is None:
            return self.fallback.predict_with_confidence(norm_text)

        import torch
        inputs = self.tokenizer(
            norm_text,
            return_tensors="pt",
            truncation=True,
            max_length=64,
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0]
            max_idx = int(torch.argmax(probs).item())
            confidence = float(probs[max_idx].item())
            intent = self.model.config.id2label.get(max_idx, INTENT_CLASSES[max_idx % len(INTENT_CLASSES)])

        return intent, confidence

    def predict(self, query: str) -> str:
        intent, _ = self.predict_with_confidence(query)
        return intent


def get_classifier(model_type: str = "baseline") -> BaseIntentClassifier:
    """Factory function returning the desired classifier."""
    if model_type == "muril":
        return MurilIntentClassifier()
    return TfidfBaselineClassifier()


def train_baseline():
    """Train only on the explicit training partition; leave holdouts untouched."""
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import FeatureUnion
    from sklearn.linear_model import LogisticRegression
    from scripts.evaluate import validate_splits

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df = pd.read_csv(os.path.join(root, "data", "processed", "intents.csv"))
    validate_splits(df)
    train = df[df["split"] == "train"]
    if set(train.intent) != set(INTENT_CLASSES):
        raise ValueError("Training split must contain all intent classes")
    classifier = TfidfBaselineClassifier()
    classifier.vectorizer = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 3))),
        ("char", TfidfVectorizer(analyzer="char", ngram_range=(2, 5))),
    ])
    features = classifier.vectorizer.fit_transform(train["query"].map(normalize_text))
    classifier.model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    classifier.model.fit(features, train.intent)
    classifier.classes_ = list(classifier.model.classes_)
    classifier.save(classifier.model_path)
    print(f"Saved baseline trained on {len(train)} rows to {classifier.model_path}")
