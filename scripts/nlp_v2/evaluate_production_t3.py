#!/usr/bin/env python3
"""One-way aggregate evaluation of the frozen production T3 checkpoint."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from src.nlp_v2.dispatch import OPERATIONS
from src.nlp_v2.model import (
    DEFAULT_MANIFEST, LABEL_ORDER, T3IntentClassifier, load_manifest, sha256_file,
)


ROOT = Path(__file__).resolve().parents[2]
STRESS = ROOT / "data/nlp_v2/gate_b2/gate_b2_stress_eval.csv"
TRAIN = ROOT / "data/nlp_v2/gate_b2/gate_b2_train.csv"
REFERENCE = ROOT / "data/nlp_v2/gate_b2/human_annotation_key.json"
TRAIN_SHA256 = "d92801006ecb96fd64d01e6a602697e2e8749494627964f82d002566e3d0ba94"
STRESS_SHA256 = "26cbf6517e25511d19d67051f500459ef7d78d87e5fbd1eb6d21849842242a1c"
REFERENCE_SHA256 = "8fb55e863cfbdd1bbc2cf068050757d4d6bd58092fb6c3aea1f389c5c520e1c6"
FROZEN_MANIFEST_SHA256 = "447a120090c33ba1259cad06ce9f216d80832d2540727c3330f14be3ec04dc39"


def join_reference(stress_rows: list[dict], reference: dict) -> list[dict]:
    """Return the keyed human subset only if its T3 gold matches the stress row."""
    by_id = {row["utterance_id"]: row for row in stress_rows}
    if len(by_id) != len(stress_rows):
        raise ValueError("Duplicate stress utterance IDs")
    joined = []
    seen = set()
    for entry in reference.values():
        utterance_id = entry["utterance_id"]
        if utterance_id in seen:
            raise ValueError("Duplicate reference utterance ID")
        seen.add(utterance_id)
        if utterance_id not in by_id:
            raise ValueError(f"Reference utterance missing from stress set: {utterance_id}")
        row = by_id[utterance_id]
        if row["T3_label"] != entry["gold_T3_intent"]:
            raise ValueError(f"Reference gold mismatch: {utterance_id}")
        joined.append({**row, "acceptable_secondary_labels": entry.get("acceptable_secondary_labels", [])})
    return joined


def overlap_audit(train_rows: list[dict], evaluation_rows: list[dict]) -> dict:
    """Count train-family overlap using metadata only; never select a checkpoint."""
    keys = ("family_id", "semantic_family_id", "query")
    seen = {key: {row[key].strip().casefold() for row in train_rows if row[key]} for key in keys}
    flags = [
        {key: bool(row[key] and row[key].strip().casefold() in seen[key]) for key in keys}
        for row in evaluation_rows
    ]
    return {
        "total_rows": len(evaluation_rows),
        "family_overlap_rows": sum(item["family_id"] for item in flags),
        "semantic_family_overlap_rows": sum(item["semantic_family_id"] for item in flags),
        "exact_query_overlap_rows": sum(item["query"] for item in flags),
        "any_overlap_rows": sum(any(item.values()) for item in flags),
    }


def group_coverage(stress_rows: list[dict], subset_rows: list[dict]) -> dict:
    """Describe how many subset contrast groups are complete in the full stress set."""
    full, subset = defaultdict(int), defaultdict(int)
    for row in stress_rows:
        if row.get("contrast_group_id"):
            full[row["contrast_group_id"]] += 1
    for row in subset_rows:
        if row.get("contrast_group_id"):
            subset[row["contrast_group_id"]] += 1
    return {
        "observed_groups": len(subset),
        "complete_groups": sum(subset[group] == full[group] for group in subset),
        "partial_groups": sum(subset[group] < full[group] for group in subset),
    }


def score_records(rows: list[dict]) -> dict:
    """Score predicted and gold T3 labels without changing evaluation inputs."""
    if not rows:
        raise ValueError("Cannot score an empty evaluation set")
    labels = set(LABEL_ORDER)
    for row in rows:
        if row["gold"] not in labels or row["predicted"] not in labels:
            raise ValueError("Unknown T3 label in evaluation")
        if any(label not in labels for label in row["secondary"]):
            raise ValueError("Unknown secondary T3 label in evaluation")
    gold = [row["gold"] for row in rows]
    predicted = [row["predicted"] for row in rows]
    strict = [int(g == p) for g, p in zip(gold, predicted)]
    aware = [int(row["predicted"] == row["gold"] or row["predicted"] in row["secondary"]) for row in rows]
    operations = [int(OPERATIONS[row["gold"]] == OPERATIONS[row["predicted"]]) for row in rows]
    precision, recall, f1, support = precision_recall_fscore_support(
        gold, predicted, labels=list(LABEL_ORDER), zero_division=0,
    )
    per_class = {
        label: {"support": int(support[i]), "precision": float(precision[i]),
                "recall": float(recall[i]), "f1": float(f1[i])}
        for i, label in enumerate(LABEL_ORDER)
    }
    grouped = defaultdict(list)
    for row, correct in zip(rows, operations):
        if row.get("contrast_group_id"):
            grouped[row["contrast_group_id"]].append(correct)
    strata = {}
    for field in ("language_class", "code_switch_level", "noise_level"):
        by_value = defaultdict(list)
        for index, row in enumerate(rows):
            if row.get(field):
                by_value[row[field]].append(index)
        strata[field] = {
            value: {
                "count": len(indices),
                "strict_intent_accuracy": sum(strict[i] for i in indices) / len(indices),
                "ambiguity_aware_accuracy": sum(aware[i] for i in indices) / len(indices),
            }
            for value, indices in sorted(by_value.items())
        }
    return {
        "count": len(rows),
        "strict_intent_accuracy": float(accuracy_score(gold, predicted)),
        "strict_intent_macro_f1": float(sum(f1) / len(LABEL_ORDER)),
        "ambiguity_aware_accuracy": sum(aware) / len(aware),
        "operation_accuracy": sum(operations) / len(operations),
        "contrast_group_count": len(grouped),
        "contrast_group_exact_accuracy": (
            sum(all(results) for results in grouped.values()) / len(grouped) if grouped else None
        ),
        "per_class": per_class,
        "strata": strata,
    }


def evaluate(output_dir: Path) -> dict:
    """Read frozen sources once and emit only aggregate model metrics."""
    output_dir = Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Evaluation output exists: {output_dir}")
    if (output_dir.is_relative_to(ROOT / "data")
            or output_dir.is_relative_to(ROOT / "experiments/nlp_v2/gate_b2")
            or output_dir.is_relative_to(ROOT / "reports/nlp_v2/gate_b2")
            or output_dir.is_relative_to(ROOT / "reports/nlp_v2/gate_b3")):
        raise ValueError("Cannot write evaluation output into frozen assets")
    input_hashes = {
        "train_sha256": sha256_file(TRAIN),
        "stress_sha256": sha256_file(STRESS),
        "human_reference_sha256": sha256_file(REFERENCE),
        "manifest_sha256": sha256_file(DEFAULT_MANIFEST),
    }
    if input_hashes != {
        "train_sha256": TRAIN_SHA256,
        "stress_sha256": STRESS_SHA256,
        "human_reference_sha256": REFERENCE_SHA256,
        "manifest_sha256": FROZEN_MANIFEST_SHA256,
    }:
        raise ValueError("Frozen evaluation or model manifest hash mismatch")
    manifest = load_manifest(DEFAULT_MANIFEST)
    with STRESS.open(newline="", encoding="utf-8") as stream:
        stress_rows = list(csv.DictReader(stream))
    with TRAIN.open(newline="", encoding="utf-8") as stream:
        train_rows = list(csv.DictReader(stream))
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    reference_rows = join_reference(stress_rows, reference)
    if len(stress_rows) != 706 or len(reference_rows) != 350:
        raise ValueError("Unexpected frozen evaluation sizes")
    classifier = T3IntentClassifier(DEFAULT_MANIFEST)
    predictions = {row["utterance_id"]: classifier.predict(row["query"]).primary_label for row in stress_rows}

    def records(rows: list[dict]) -> list[dict]:
        result = []
        for row in rows:
            secondary = row.get("acceptable_secondary_labels", [])
            if isinstance(secondary, str):
                secondary = json.loads(secondary or "[]")
            result.append({
                "gold": row["T3_label"], "predicted": predictions[row["utterance_id"]],
                "secondary": secondary,
                "language_class": row.get("language_class"),
                "code_switch_level": row.get("code_switch_level"),
                "noise_level": row.get("noise_level"),
                "contrast_group_id": row.get("contrast_group_id"),
            })
        return result

    report = {
        "evaluation_type": "frozen_production_model_only",
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "input_hashes": input_hashes,
        "split_integrity": {
            "stress_vs_train": overlap_audit(train_rows, stress_rows),
            "human_reference_vs_train": overlap_audit(train_rows, reference_rows),
            "human_reference_contrast_coverage": group_coverage(stress_rows, reference_rows),
        },
        "stress": score_records(records(stress_rows)),
        "human_reference_subset": score_records(records(reference_rows)),
        "limitations": [
            "Scores measure T3 intent and mapped operation selection only; domain execution is not included.",
            "The classifier emits one label, so ambiguity-aware acceptance is retrospective; clarification behavior requires end-to-end evaluation.",
            "The human reference subset is 350 of the 706 stress examples, not an independent set.",
            "Contrast-group exact accuracy on the human subset is calculated only among subset members of each group; 17 of 73 observed groups are partial.",
            "The frozen stress and human-reference sets include rows sharing train families; their full-set scores are not independent family-held-out estimates.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "production_t3_evaluation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown = [
        "# Frozen production T3 model evaluation", "",
        f"Checkpoint SHA-256: `{report['checkpoint_sha256']}`. Model and evaluation inputs were hash checked before scoring.", "",
        "| Set | Count | Intent accuracy | Intent Macro-F1 | Ambiguity-aware accuracy | Mapped operation accuracy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, title in (("stress", "Frozen stress"), ("human_reference_subset", "Human reference subset")):
        value = report[key]
        markdown.append(f"| {title} | {value['count']} | {value['strict_intent_accuracy']:.4f} | {value['strict_intent_macro_f1']:.4f} | {value['ambiguity_aware_accuracy']:.4f} | {value['operation_accuracy']:.4f} |")
    markdown.extend(["", "Full per-class and language/code-switch/noise aggregates are in `production_t3_evaluation.json`.", "", "## Limits", ""])
    for key, title in (("stress_vs_train", "Stress"), ("human_reference_vs_train", "Human reference subset")):
        integrity = report["split_integrity"][key]
        markdown.append(f"{title}: {integrity['any_overlap_rows']} of {integrity['total_rows']} rows share a train family, semantic family, or exact query (exact query overlaps: {integrity['exact_query_overlap_rows']}).")
    markdown.append("")
    markdown.extend(f"- {item}" for item in report["limitations"])
    markdown.append("")
    (output_dir / "production_t3_evaluation.md").write_text("\n".join(markdown), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/nlp_v2/production_eval")
    args = parser.parse_args()
    report = evaluate(args.output_dir)
    print(json.dumps({"stress_count": report["stress"]["count"], "intent_accuracy": report["stress"]["strict_intent_accuracy"], "intent_macro_f1": report["stress"]["strict_intent_macro_f1"]}))


if __name__ == "__main__":
    main()
