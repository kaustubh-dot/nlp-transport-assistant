#!/usr/bin/env python3
"""TF-IDF + Logistic Regression Baseline Training Harness for NLP v2 Gate B.

Trains and evaluates 18 configurations:
3 Taxonomies (T1, T2, T3) x 2 Regimes (Regime A, Regime B) x 3 Seeds (42, 101, 777).
Logs metrics.json, confusion_matrix.json, and predictions.jsonl for every run.
"""

import os
import csv
import json
import argparse
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "pilot")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "taxonomy_pilot")
MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")

with open(MAP_PATH, "r", encoding="utf-8") as f:
    TAX_SPEC = json.load(f)

# Precompute allowed operations mapping
ALLOWED_OPS = {"T1": defaultdict(set), "T2": defaultdict(set), "T3": defaultdict(set)}
for scen in TAX_SPEC["scenarios"]:
    op = scen["downstream_operation"]
    ALLOWED_OPS["T1"][scen["T1_label"]].add(op)
    ALLOWED_OPS["T2"][scen["T2_label"]].add(op)
    ALLOWED_OPS["T3"][scen["T3_label"]].add(op)


def load_split(split_path: str):
    rows = []
    with open(split_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def run_single_experiment(regime: str, taxonomy: str, seed: int):
    exp_id = f"{regime}_{taxonomy}_tfidf_seed{seed}"
    out_dir = os.path.join(EXP_DIR, exp_id)
    os.makedirs(out_dir, exist_ok=True)

    data_dir = os.path.join(DATA_DIR, regime, taxonomy)
    train_rows = load_split(os.path.join(data_dir, "pilot_train.csv"))
    val_rows = load_split(os.path.join(data_dir, "pilot_validation.csv"))
    eval_rows = load_split(os.path.join(data_dir, "pilot_eval.csv"))

    classes = sorted(list(TAX_SPEC["taxonomies"][taxonomy]["intents"]))
    label_to_idx = {l: i for i, l in enumerate(classes)}

    train_queries = [r["query"] for r in train_rows]
    train_labels = [r["taxonomy_label"] for r in train_rows]

    eval_queries = [r["query"] for r in eval_rows]
    eval_labels = [r["taxonomy_label"] for r in eval_rows]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)
    X_train = vectorizer.fit_transform(train_queries)
    y_train = [label_to_idx[l] for l in train_labels]

    X_eval = vectorizer.transform(eval_queries)
    y_eval = [label_to_idx[l] for l in eval_labels]

    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=seed, solver="lbfgs")
    clf.fit(X_train, y_train)

    y_pred_idx = clf.predict(X_eval)
    y_pred_labels = [classes[idx] for idx in y_pred_idx]

    acc = float(accuracy_score(y_eval, y_pred_idx))
    macro_f1 = float(f1_score(y_eval, y_pred_idx, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_eval, y_pred_idx, average="weighted", zero_division=0))

    per_class_f1_vals = f1_score(y_eval, y_pred_idx, average=None, labels=range(len(classes)), zero_division=0)
    per_class_f1 = {classes[i]: float(per_class_f1_vals[i]) for i in range(len(classes))}

    cm = confusion_matrix(y_eval, y_pred_idx, labels=range(len(classes))).tolist()

    # Downstream semantic operation accuracy
    correct_op_count = 0
    predictions_records = []
    allowed = ALLOWED_OPS[taxonomy]

    for i, r in enumerate(eval_rows):
        pred_label = y_pred_labels[i]
        gold_label = eval_labels[i]
        gold_op = r["semantic_operation"]

        allowed_for_pred = allowed.get(pred_label, set())
        op_correct = bool(gold_op in allowed_for_pred)
        if op_correct:
            correct_op_count += 1

        rec = {
            "utterance_id": r["utterance_id"],
            "query": r["query"],
            "language": r["language"],
            "script": r["script"],
            "gold_label": gold_label,
            "pred_label": pred_label,
            "gold_operation": gold_op,
            "op_correct": op_correct,
            "intent_correct": bool(gold_label == pred_label)
        }
        predictions_records.append(rec)

    semantic_op_accuracy = float(correct_op_count / len(eval_rows))

    metrics = {
        "experiment_id": exp_id,
        "model_family": "tfidf_logreg",
        "regime": regime,
        "taxonomy": taxonomy,
        "seed": seed,
        "num_classes": len(classes),
        "train_samples": len(train_rows),
        "val_samples": len(val_rows),
        "eval_samples": len(eval_rows),
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "semantic_op_accuracy": semantic_op_accuracy,
        "per_class_f1": per_class_f1
    }

    # Save outputs
    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(out_dir, "confusion_matrix.json"), "w", encoding="utf-8") as f:
        json.dump({"classes": classes, "matrix": cm}, f, indent=2)

    with open(os.path.join(out_dir, "predictions.jsonl"), "w", encoding="utf-8") as f:
        for rec in predictions_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[{exp_id}] Acc: {acc:.4f}, Macro-F1: {macro_f1:.4f}, SemOp-Acc: {semantic_op_accuracy:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regime", type=str, choices=["regime_a", "regime_b", "all"], default="all")
    parser.add_argument("--taxonomy", type=str, choices=["T1", "T2", "T3", "all"], default="all")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 101, 777])
    args = parser.parse_args()

    regimes = ["regime_a", "regime_b"] if args.regime == "all" else [args.regime]
    taxonomies = ["T1", "T2", "T3"] if args.taxonomy == "all" else [args.taxonomy]

    total_runs = len(regimes) * len(taxonomies) * len(args.seeds)
    print(f"Starting TF-IDF Pilot runs: {total_runs} total runs planned...")

    all_metrics = []
    for reg in regimes:
        for tax in taxonomies:
            for seed in args.seeds:
                m = run_single_experiment(reg, tax, seed)
                all_metrics.append(m)

    print(f"\nAll {len(all_metrics)} TF-IDF baseline runs successfully completed!")


if __name__ == "__main__":
    main()
