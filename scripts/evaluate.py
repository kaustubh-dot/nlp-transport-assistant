#!/usr/bin/env python3
"""Intent benchmark on held-out template families; no inferred factual E2E score."""
import sys
from pathlib import Path
import argparse
import pandas as pd
import json
import time
import statistics
from typing import Optional

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from sklearn.metrics import classification_report, confusion_matrix, f1_score
from src.intent_classifier import get_classifier, INTENT_CLASSES
from src.pipeline import TransportAssistant

INTENTS_CSV = BASE_DIR / "data/processed/intents.csv"
ACCEPTANCE_SUITE_PATH = BASE_DIR / "data/eval/acceptance_test_suite.json"


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


def evaluate_acceptance(suite_path: Optional[Path] = None, model_type: str = "baseline"):
    """Evaluates the full pipeline against the independent acceptance test suite."""
    target_path = suite_path or ACCEPTANCE_SUITE_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Acceptance suite not found at {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        suite = json.load(f)

    assistant = TransportAssistant(model_type=model_type)

    y_true = []
    y_pred = []
    o_ok = 0
    d_ok = 0
    s_ok = 0
    m_ok = 0
    f_ok = 0
    exact_match = 0
    factual_success = 0
    latencies = []
    failures = []
    by_form = {}

    for item in suite:
        t0 = time.perf_counter()
        res = assistant.process_query(item["query"])
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)

        pred_intent = res["intent"]
        gold_intent = item["gold_intent"]
        y_true.append(gold_intent)
        y_pred.append(pred_intent)

        slots = res["slots"]
        o_match = (slots.get("origin") == item.get("gold_origin"))
        d_match = (slots.get("destination") == item.get("gold_destination"))
        s_match = (slots.get("station") == item.get("gold_station"))
        m_match = (slots.get("transport_mode") == item.get("gold_mode"))
        fac = slots.get("facility") or slots.get("information_type")
        f_match = (fac == item.get("gold_facility"))

        if o_match:
            o_ok += 1
        if d_match:
            d_ok += 1
        if s_match:
            s_ok += 1
        if m_match:
            m_ok += 1
        if f_match:
            f_ok += 1

        all_slots_match = (o_match and d_match and s_match and m_match and f_match)
        if all_slots_match:
            exact_match += 1

        resp = res["response_hi"]
        exp_ok = all(sub in resp for sub in item.get("expected_substrings", []))
        forb_ok = not any(sub in resp for sub in item.get("forbidden_substrings", []))
        task_success = (pred_intent == gold_intent) and exp_ok and forb_ok

        if task_success:
            factual_success += 1
        else:
            failures.append({
                "id": item["id"], "query": item["query"],
                "gold_intent": gold_intent, "pred_intent": pred_intent,
                "exp_ok": exp_ok, "forb_ok": forb_ok, "response": resp
            })

        form = item.get("linguistic_form", "unknown")
        if form not in by_form:
            by_form[form] = {"count": 0, "intent_ok": 0, "task_ok": 0}
        by_form[form]["count"] += 1
        if pred_intent == gold_intent:
            by_form[form]["intent_ok"] += 1
        if task_success:
            by_form[form]["task_ok"] += 1

    total = len(suite)
    intent_acc = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp) / total
    macro_f1 = f1_score(y_true, y_pred, labels=INTENT_CLASSES, average="macro", zero_division=0)
    mean_latency = statistics.mean(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

    print("=" * 65)
    print("INDEPENDENT ACCEPTANCE TEST SUITE EVALUATION (PRD GATES)")
    print("=" * 65)
    print(f"Total Test Cases:               {total}")
    print(f"Intent Classification Accuracy: {intent_acc:.2%} ({sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)}/{total})")
    print(f"Intent Macro-F1:                {macro_f1:.4f}")
    print(f"Origin Entity Accuracy:         {o_ok/total:.2%} ({o_ok}/{total})")
    print(f"Destination Entity Accuracy:    {d_ok/total:.2%} ({d_ok}/{total})")
    print(f"Station Entity Accuracy:        {s_ok/total:.2%} ({s_ok}/{total})")
    print(f"Transport Mode Accuracy:        {m_ok/total:.2%} ({m_ok}/{total})")
    print(f"Facility / Info Accuracy:       {f_ok/total:.2%} ({f_ok}/{total})")
    print(f"Applicable Slots Exact Match:   {exact_match/total:.2%} ({exact_match}/{total})")
    print(f"Factual Task Success (E2E):     {factual_success/total:.2%} ({factual_success}/{total})  [PRD Gate: >=85%]")
    print(f"Latency Mean:                   {mean_latency:.2f} ms")
    print(f"Latency P95:                    {p95_latency:.2f} ms")
    print("-" * 65)
    print("Breakdown by Linguistic Form:")
    for form, stats in sorted(by_form.items()):
        cnt = stats["count"]
        i_pct = stats["intent_ok"] / cnt
        t_pct = stats["task_ok"] / cnt
        print(f"  {form:<20} n={cnt:<3} intent_acc={i_pct:.2%}  task_success={t_pct:.2%}")
    print("=" * 65)

    if failures:
        print(f"Failures ({len(failures)}):")
        for f_item in failures:
            print(f"  [{f_item['id']}] {f_item['query']}")
            print(f"    Gold: {f_item['gold_intent']} | Pred: {f_item['pred_intent']}")
            print(f"    Response: {f_item['response']}")
    else:
        print("All acceptance criteria satisfied! PRD compliance gate PASSED.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["baseline", "muril"], default="baseline")
    parser.add_argument("--acceptance", action="store_true", help="Run independent acceptance evaluation")
    parser.add_argument("--suite", type=Path, default=None, help="Path to acceptance suite JSON")
    args = parser.parse_args()

    if args.acceptance:
        evaluate_acceptance(suite_path=args.suite, model_type=args.model)
    else:
        evaluate_system(args.model)
