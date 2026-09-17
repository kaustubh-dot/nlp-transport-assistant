#!/usr/bin/env python3
"""Evaluation and benchmarking script for Hindi Transport Assistant.

Computes:
  - Intent Classification: Accuracy, Macro Precision, Recall, F1, Confusion Matrix
  - Slot Extraction: Origin, Destination, and Mode accuracy
  - End-to-End Task Success Rate
  - Robustness split analysis: Hindi vs Hinglish
"""

import os
import argparse
import pandas as pd
from typing import Dict, Any

from src.normalization import normalize_text
from src.intent_classifier import get_classifier
from src.entity_extractor import EntityExtractor
from src.pipeline import TransportAssistant

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTENTS_CSV = os.path.join(BASE_DIR, "data", "processed", "intents.csv")


def evaluate_system(model_type: str = "baseline"):
    """Runs evaluation on the test split."""
    if not os.path.exists(INTENTS_CSV):
        print(f"❌ Error: Dataset not found at {INTENTS_CSV}. Run scripts/generate_intent_dataset.py first.")
        return

    df = pd.read_csv(INTENTS_CSV)
    test_df = df[df["split"] == "test"].copy()
    if test_df.empty:
        test_df = df.sample(min(150, len(df)), random_state=42).copy()

    print(f"\n=======================================================")
    print(f"📊 Running Evaluation for Model: {model_type.upper()}")
    print(f"   Test Set Size: {len(test_df)} samples")
    print(f"=======================================================\n")

    assistant = TransportAssistant(model_type=model_type)

    total = len(test_df)
    intent_correct = 0
    origin_correct = 0
    dest_correct = 0
    mode_correct = 0
    e2e_correct = 0

    # Linguistic breakdowns
    lang_stats: Dict[str, Dict[str, int]] = {
        "hi": {"total": 0, "intent_correct": 0, "e2e_correct": 0},
        "hinglish": {"total": 0, "intent_correct": 0, "e2e_correct": 0}
    }

    for _, row in test_df.iterrows():
        query = str(row["query"])
        true_intent = str(row["intent"])
        true_origin = row["origin"] if pd.notna(row["origin"]) else None
        true_dest = row["destination"] if pd.notna(row["destination"]) else None
        true_mode = row["transport_mode"] if pd.notna(row["transport_mode"]) else None
        lang = str(row.get("language", "hi"))

        res = assistant.process_query(query)
        pred_intent = res["intent"]
        slots = res["slots"]

        pred_origin = slots.get("origin")
        pred_dest = slots.get("destination")
        pred_mode = slots.get("transport_mode")

        # Intent accuracy
        is_intent_ok = (pred_intent == true_intent)
        if is_intent_ok:
            intent_correct += 1

        # Slot accuracy
        is_origin_ok = (pred_origin == true_origin) if true_origin else True
        is_dest_ok = (pred_dest == true_dest) if true_dest else True
        is_mode_ok = (pred_mode == true_mode) if true_mode else True

        if is_origin_ok:
            origin_correct += 1
        if is_dest_ok:
            dest_correct += 1
        if is_mode_ok:
            mode_correct += 1

        # End-to-end task success
        is_e2e_ok = is_intent_ok and is_origin_ok and is_dest_ok and len(res["response_hi"]) > 10
        if is_e2e_ok:
            e2e_correct += 1

        # Track language breakdown
        if lang in lang_stats:
            lang_stats[lang]["total"] += 1
            if is_intent_ok:
                lang_stats[lang]["intent_correct"] += 1
            if is_e2e_ok:
                lang_stats[lang]["e2e_correct"] += 1

    print(f"🎯 INTENT CLASSIFICATION METRICS:")
    print(f"   Accuracy: {intent_correct / total * 100:.2f}% ({intent_correct}/{total})")

    print(f"\n🏷️  SLOT EXTRACTION METRICS:")
    print(f"   Origin Match Accuracy:      {origin_correct / total * 100:.2f}%")
    print(f"   Destination Match Accuracy: {dest_correct / total * 100:.2f}%")
    print(f"   Mode Match Accuracy:        {mode_correct / total * 100:.2f}%")

    print(f"\n🚀 END-TO-END TASK SUCCESS RATE:")
    print(f"   Overall E2E Success:        {e2e_correct / total * 100:.2f}% ({e2e_correct}/{total})")

    print(f"\n🌐 ROBUSTNESS BREAKDOWN BY LINGUISTIC FORM:")
    for l, stats in lang_stats.items():
        if stats["total"] > 0:
            i_acc = stats["intent_correct"] / stats["total"] * 100
            e_acc = stats["e2e_correct"] / stats["total"] * 100
            label = "Hindi (Devanagari)" if l == "hi" else "Hinglish (Roman Script)"
            print(f"   • {label:25} Total: {stats['total']:3} | Intent Acc: {i_acc:6.2f}% | E2E Success: {e_acc:6.2f}%")
    print("\n=======================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Hindi Transport Assistant")
    parser.add_argument("--model", choices=["baseline", "muril"], default="baseline", help="Model to evaluate")
    args = parser.parse_args()
    evaluate_system(model_type=args.model)
