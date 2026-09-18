#!/usr/bin/env python3
"""Frozen Gold Acceptance Suite Evaluation for Selected Champion Architecture.

Protocol:
  - Runs ONLY after champion model selection.
  - Frozen 149-case gold acceptance suite (data/eval/acceptance_test_suite.json).
  - Never used for training, early stopping, or hyperparameter tuning.
  - Evaluates Intent Accuracy, Macro-F1, Slot Exact Match, and Factual E2E Success.
  - Honest reporting (does not artificially optimize to force 100%).
"""

import os
import sys
import time
import json
import argparse
import statistics
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.pipeline import TransportAssistant
from src.intent_classifier import INTENT_CLASSES
from sklearn.metrics import f1_score

ACCEPTANCE_SUITE_PATH = BASE_DIR / "data/eval/acceptance_test_suite.json"
BENCHMARK_RESULTS_PATH = BASE_DIR / "docs/benchmarks/current_multi_seed_5seed_results.json"
LEGACY_BENCHMARK_RESULTS_PATH = BASE_DIR / "docs/benchmarks/multi_seed_benchmark_results.json"
OUTPUT_GOLD_JSON = BASE_DIR / "docs/benchmarks/gold_acceptance_results.json"


def get_default_champion_model() -> str:
    """Reads champion from current_multi_seed_5seed_results.json if available, else defaults to indicbert_v2."""
    target_path = BENCHMARK_RESULTS_PATH if BENCHMARK_RESULTS_PATH.exists() else LEGACY_BENCHMARK_RESULTS_PATH
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            champ = data.get("champion")
            if champ and "model_key" in champ:
                return champ["model_key"]
        except Exception:
            pass
    return "indicbert_v2"


def evaluate_gold_suite(model_type: str = "indicbert_v2", suite_path: Optional[Path] = None) -> Dict[str, Any]:
    target_path = suite_path or ACCEPTANCE_SUITE_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Acceptance suite not found at {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        suite = json.load(f)

    print(f"\n=================================================================")
    print(f"EVALUATING FROZEN GOLD ACCEPTANCE SUITE (N={len(suite)} CASES)")
    print(f"Target Architecture: [{model_type}]")
    print(f"Suite Source: {target_path}")
    print(f"=================================================================\n")

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
        latency_ms = (time.perf_counter() - t0) * 1000.0
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
                "id": item["id"],
                "query": item["query"],
                "gold_intent": gold_intent,
                "pred_intent": pred_intent,
                "exp_ok": exp_ok,
                "forb_ok": forb_ok,
                "response": resp
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
    macro_f1 = float(f1_score(y_true, y_pred, labels=INTENT_CLASSES, average="macro", zero_division=0))
    mean_latency = statistics.mean(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

    print(f"Total Test Cases:               {total}")
    print(f"Intent Classification Accuracy: {intent_acc * 100:.2f}% ({sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)}/{total})")
    print(f"Intent Macro-F1:                {macro_f1:.4f}")
    print(f"Slot Exact Match:               {exact_match / total * 100:.2f}% ({exact_match}/{total})")
    print(f"Factual Task Success (E2E):     {factual_success / total * 100:.2f}% ({factual_success}/{total})")
    print(f"Pipeline Latency:               Mean={mean_latency:.1f}ms, P95={p95_latency:.1f}ms")

    print("\nBreakdown by Linguistic Form:")
    for form, stats in sorted(by_form.items()):
        cnt = stats["count"]
        i_pct = stats["intent_ok"] / cnt * 100
        t_pct = stats["task_ok"] / cnt * 100
        print(f"  - {form:<22}: n={cnt:>2}, Intent Acc={i_pct:>5.1f}%, E2E Success={t_pct:>5.1f}%")

    if failures:
        print(f"\nDiscrepancy Samples ({len(failures)} total):")
        for f in failures[:5]:
            print(f"  [ID {f['id']}] Query: '{f['query']}' | Gold Intent: {f['gold_intent']} vs Pred: {f['pred_intent']} | E2E Match: {f['exp_ok'] and f['forb_ok']}")
    else:
        print("\nAll 149 acceptance test queries succeeded perfectly.")

    results = {
        "model_type": model_type,
        "total_cases": total,
        "intent_accuracy": round(intent_acc, 4),
        "intent_macro_f1": round(macro_f1, 4),
        "slot_exact_match_pct": round(exact_match / total * 100, 2),
        "factual_task_success_pct": round(factual_success / total * 100, 2),
        "mean_latency_ms": round(mean_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "by_form": by_form,
        "num_failures": len(failures),
        "failures": failures
    }

    os.makedirs(OUTPUT_GOLD_JSON.parent, exist_ok=True)
    with open(OUTPUT_GOLD_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nGold evaluation results saved to {OUTPUT_GOLD_JSON}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate champion model on frozen gold acceptance suite")
    parser.add_argument("--model", type=str, default=None, help="Model key (defaults to champion from benchmark results)")
    parser.add_argument("--suite", type=str, default=None, help="Custom path to acceptance test suite JSON")
    args = parser.parse_args()

    model_key = args.model or get_default_champion_model()
    suite_p = Path(args.suite) if args.suite else None
    evaluate_gold_suite(model_type=model_key, suite_path=suite_p)
