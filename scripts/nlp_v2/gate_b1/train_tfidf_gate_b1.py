#!/usr/bin/env python3
"""TF-IDF Baseline Training Harness for NLP v2 Gate B.1 Hard-Boundary Taxonomy Stress Test.

Evaluates two feature representations:
1. TFIDF-WORD: word unigrams + bigrams (ngram_range=(1,2), max_features=10000, sublinear_tf=True)
2. TFIDF-WORDCHAR: FeatureUnion of word (1,2) + char (3,5) (max_features=10000 word, 15000 char)

Tested across:
- 2 Taxonomies: T2 (12 intents), T3 (16 intents)
- 3 Seeds: 42, 101, 777
Total = 12 baseline configurations.

Outputs per experiment to experiments/nlp_v2/gate_b1/<exp_id>/:
- metrics.json
- confusion_matrix.json
- predictions.jsonl
"""

import os
import csv
import json
import argparse
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b1")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "gate_b1")
MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")

with open(MAP_PATH, "r", encoding="utf-8") as f:
    TAX_SPEC = json.load(f)

# Build operation mapping
T3_TO_OP = {}
for scen in TAX_SPEC["scenarios"]:
    T3_TO_OP[scen["T3_label"]] = scen["downstream_operation"]

ALLOWED_OPS = {"T2": defaultdict(set), "T3": defaultdict(set)}
for scen in TAX_SPEC["scenarios"]:
    op = scen["downstream_operation"]
    ALLOWED_OPS["T2"][scen["T2_label"]].add(op)
    ALLOWED_OPS["T3"][scen["T3_label"]].add(op)


def load_split(split_name: str):
    path = os.path.join(DATA_DIR, f"gate_b1_{split_name}.csv")
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def get_vectorizer(model_family: str):
    if model_family == "tfidf_word":
        return TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)
    elif model_family == "tfidf_wordchar":
        return FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)),
            ("char", TfidfVectorizer(ngram_range=(3, 5), analyzer="char", max_features=15000, sublinear_tf=True)),
        ])
    else:
        raise ValueError(f"Unknown model_family: {model_family}")


def run_experiment(model_family: str, taxonomy: str, seed: int, train_rows, val_rows, eval_rows):
    exp_id = f"{model_family}_{taxonomy}_seed{seed}"
    out_dir = os.path.join(EXP_DIR, exp_id)
    os.makedirs(out_dir, exist_ok=True)

    label_col = "T2_label" if taxonomy == "T2" else "T3_label"
    classes = sorted(list(TAX_SPEC["taxonomies"][taxonomy]["intents"]))
    label_to_idx = {l: i for i, l in enumerate(classes)}

    train_queries = [r["query"] for r in train_rows]
    train_labels = [label_to_idx[r[label_col]] for r in train_rows]

    eval_queries = [r["query"] for r in eval_rows]
    eval_labels = [label_to_idx[r[label_col]] for r in eval_rows]

    val_queries = [r["query"] for r in val_rows]
    val_labels = [label_to_idx[r[label_col]] for r in val_rows]

    vec = get_vectorizer(model_family)
    X_train = vec.fit_transform(train_queries)
    y_train = np.array(train_labels)

    X_val = vec.transform(val_queries)
    y_val = np.array(val_labels)

    X_eval = vec.transform(eval_queries)
    y_eval = np.array(eval_labels)

    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=seed, solver="lbfgs")
    clf.fit(X_train, y_train)

    val_preds_idx = clf.predict(X_val)
    val_macro_f1 = float(f1_score(y_val, val_preds_idx, average="macro", zero_division=0))
    val_acc = float(accuracy_score(y_val, val_preds_idx))

    eval_preds_idx = clf.predict(X_eval)
    eval_probs = clf.predict_proba(X_eval)
    eval_pred_labels = [classes[idx] for idx in eval_preds_idx]

    acc = float(accuracy_score(y_eval, eval_preds_idx))
    macro_f1 = float(f1_score(y_eval, eval_preds_idx, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_eval, eval_preds_idx, average="weighted", zero_division=0))

    per_class_f1_vals = f1_score(y_eval, eval_preds_idx, average=None, labels=range(len(classes)), zero_division=0)
    per_class_f1 = {classes[i]: float(per_class_f1_vals[i]) for i in range(len(classes))}
    cm = confusion_matrix(y_eval, eval_preds_idx, labels=range(len(classes))).tolist()

    # Predictions and operation compatibility
    predictions_records = []
    allowed = ALLOWED_OPS[taxonomy]
    compatible_op_count = 0

    for i, r in enumerate(eval_rows):
        pred_label = eval_pred_labels[i]
        gold_label = r[label_col]
        gold_op = r["semantic_operation"]

        allowed_for_pred = allowed.get(pred_label, set())
        op_compatible = bool(gold_op in allowed_for_pred)
        if op_compatible:
            compatible_op_count += 1

        top_prob = float(eval_probs[i][eval_preds_idx[i]])
        rec = {
            "utterance_id": r["utterance_id"],
            "query": r["query"],
            "clean_query": r.get("clean_query", r["query"]),
            "language": r.get("language", ""),
            "language_class": r.get("language_class", ""),
            "script": r.get("script", ""),
            "author_source": r.get("author_source", ""),
            "generation_method": r.get("generation_method", ""),
            "contrast_group_id": r.get("contrast_group_id", ""),
            "is_implicit": "implicit" in r.get("generation_method", "") or "implicit" in r.get("author_source", "") or "implicit" in r.get("family_id", ""),
            "is_ambiguous": r.get("ambiguity_type", "none") != "none" or r.get("clarification_required", "False") == "True",
            "clarification_required": r.get("clarification_required", "False") == "True",
            "ambiguity_type": r.get("ambiguity_type", "none"),
            "noise_level": r.get("noise_level", "N0"),
            "code_switch_level": r.get("code_switch_level", "CS0"),
            "gold_label": gold_label,
            "pred_label": pred_label,
            "gold_operation": gold_op,
            "intent_correct": bool(gold_label == pred_label),
            "op_compatible": op_compatible,
            "confidence": top_prob,
            "probs": {classes[j]: float(eval_probs[i][j]) for j in range(len(classes))}
        }
        predictions_records.append(rec)

    op_compat_acc = float(compatible_op_count / len(eval_rows))

    metrics = {
        "experiment_id": exp_id,
        "model_family": model_family,
        "taxonomy": taxonomy,
        "seed": seed,
        "num_classes": len(classes),
        "train_samples": len(train_rows),
        "val_samples": len(val_rows),
        "eval_samples": len(eval_rows),
        "val_accuracy": val_acc,
        "val_macro_f1": val_macro_f1,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "op_compatible_accuracy": op_compat_acc,
        "per_class_f1": per_class_f1,
    }

    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(out_dir, "confusion_matrix.json"), "w", encoding="utf-8") as f:
        json.dump({"classes": classes, "matrix": cm}, f, indent=2)

    with open(os.path.join(out_dir, "predictions.jsonl"), "w", encoding="utf-8") as f:
        for rec in predictions_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[{exp_id}] Acc: {acc:.4f}, Macro-F1: {macro_f1:.4f}, OpCompat: {op_compat_acc:.4f} (Val-F1: {val_macro_f1:.4f})")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-family", type=str, choices=["tfidf_word", "tfidf_wordchar", "all"], default="all")
    parser.add_argument("--taxonomy", type=str, choices=["T2", "T3", "all"], default="all")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 101, 777])
    args = parser.parse_args()

    train_rows = load_split("train")
    val_rows = load_split("validation")
    eval_rows = load_split("stress_eval")

    families = ["tfidf_word", "tfidf_wordchar"] if args.model_family == "all" else [args.model_family]
    taxonomies = ["T2", "T3"] if args.taxonomy == "all" else [args.taxonomy]

    print(f"Loaded {len(train_rows)} train, {len(val_rows)} val, {len(eval_rows)} stress_eval rows.")
    total_runs = len(families) * len(taxonomies) * len(args.seeds)
    print(f"Executing {total_runs} TF-IDF baseline runs on Gate B.1...")

    all_metrics = []
    for fam in families:
        for tax in taxonomies:
            for seed in args.seeds:
                m = run_experiment(fam, tax, seed, train_rows, val_rows, eval_rows)
                all_metrics.append(m)

    print(f"\nAll {len(all_metrics)} TF-IDF baseline runs completed successfully!")


if __name__ == "__main__":
    main()
