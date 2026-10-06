#!/usr/bin/env python3
"""One-way aggregate evaluation after freezing the complete T3 assistant."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import json
from pathlib import Path
import subprocess

from src.nlp_v2.assistant import T3Assistant
from src.nlp_v2.dispatch import OPERATIONS
from src.nlp_v2.entities import DEFAULT_DB
from src.nlp_v2.domain import CanonicalTransitService
from src.nlp_v2.model import DEFAULT_MANIFEST, load_manifest, sha256_file
from scripts.nlp_v2.evaluate_production_t3 import (
    ROOT, TRAIN, STRESS, REFERENCE, TRAIN_SHA256, STRESS_SHA256,
    REFERENCE_SHA256, FROZEN_MANIFEST_SHA256, join_reference, overlap_audit,
)


FREEZE_PATHS = (
    "src/nlp_v2", "src/normalization.py", "src/entity_extractor.py",
    "app/api.py", "app/frontend_contract.py", "app/streamlit_app.py",
    "models/nlp_v2_t3_manifest.json", "requirements.txt", "requirements-nlp-v2.txt",
    "scripts/nlp_v2/evaluate_assistant.py", "scripts/nlp_v2/evaluate_production_t3.py",
    "data/canonical/transit/canonical_transport.db",
)
STATUSES = {"ok", "unavailable", "clarification", "out_of_scope", "error"}
TERMINAL_STATUSES = {"ok", "unavailable", "out_of_scope"}


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def verify_freeze(commit: str) -> str:
    """Require evaluated production code and data to match a committed freeze."""
    revision = git_output("rev-parse", "--verify", f"{commit}^{{commit}}")
    if git_output("status", "--porcelain", "--", *FREEZE_PATHS):
        raise ValueError("Assistant freeze paths have uncommitted changes")
    if git_output("diff", "--name-only", revision, "--", *FREEZE_PATHS):
        raise ValueError("Assistant source differs from the requested freeze")
    return revision


def score_replies(rows: list[dict]) -> dict:
    """Score actual reply contracts; answer factual correctness has no gold here."""
    if not rows:
        raise ValueError("Cannot score an empty evaluation set")
    for row in rows:
        if row["status"] not in STATUSES:
            raise ValueError("Unknown assistant status")
        if row["gold"] not in OPERATIONS or row["intent"] not in {*OPERATIONS, None}:
            raise ValueError("Unknown T3 intent")
        if not isinstance(row["gold_clarification"], bool):
            raise ValueError("Invalid clarification gold")
    selected = [row["operation"] == OPERATIONS[row["gold"]] for row in rows]
    dispatched = [correct and row["status"] in TERMINAL_STATUSES for row, correct in zip(rows, selected)]
    tp = sum(row["gold_clarification"] and row["status"] == "clarification" for row in rows)
    fp = sum(not row["gold_clarification"] and row["status"] == "clarification" for row in rows)
    fn = sum(row["gold_clarification"] and row["status"] != "clarification" for row in rows)
    tn = len(rows) - tp - fp - fn
    strata = {}
    for field in ("gold", "language_class", "code_switch_level", "noise_level"):
        groups = defaultdict(list)
        for index, row in enumerate(rows):
            if row.get(field):
                groups[row[field]].append(index)
        strata[field] = {
            value: {"count": len(indices),
                    "terminal_dispatch_accuracy": sum(dispatched[i] for i in indices) / len(indices),
                    "status_counts": dict(sorted(Counter(rows[i]["status"] for i in indices).items()))}
            for value, indices in sorted(groups.items())
        }
    return {
        "count": len(rows),
        "strict_intent_accuracy": sum(row["gold"] == row["intent"] for row in rows) / len(rows),
        "selected_operation_accuracy": sum(selected) / len(rows),
        "terminal_dispatch_accuracy": sum(dispatched) / len(rows),
        "status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
        "clarification": {"true_positive": tp, "false_positive": fp, "false_negative": fn,
                          "true_negative": tn, "precision": tp / (tp + fp) if tp + fp else None,
                          "recall": tp / (tp + fn) if tp + fn else None},
        "strata": strata,
    }


def evaluate(output_dir: Path, *, freeze_commit: str, reference_date: date | None = None) -> dict:
    output_dir = Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Evaluation output exists: {output_dir}")
    if any(output_dir.is_relative_to(ROOT / path) for path in (
        "data", "experiments/nlp_v2/gate_b2", "reports/nlp_v2/gate_b2", "reports/nlp_v2/gate_b3",
    )):
        raise ValueError("Cannot write into frozen assets")
    revision = verify_freeze(freeze_commit)
    inputs = {"train_sha256": sha256_file(TRAIN), "stress_sha256": sha256_file(STRESS),
              "reference_sha256": sha256_file(REFERENCE), "manifest_sha256": sha256_file(DEFAULT_MANIFEST)}
    if inputs != {"train_sha256": TRAIN_SHA256, "stress_sha256": STRESS_SHA256,
                  "reference_sha256": REFERENCE_SHA256, "manifest_sha256": FROZEN_MANIFEST_SHA256}:
        raise ValueError("Frozen evaluation input hash mismatch")
    with STRESS.open(newline="", encoding="utf-8") as stream:
        stress = list(csv.DictReader(stream))
    with TRAIN.open(newline="", encoding="utf-8") as stream:
        train = list(csv.DictReader(stream))
    reference = join_reference(stress, json.loads(REFERENCE.read_text(encoding="utf-8")))
    if len(stress) != 706 or len(reference) != 350:
        raise ValueError("Unexpected frozen evaluation sizes")
    service = CanonicalTransitService(reference_date=reference_date)
    chosen_reference_date = service.reference_date
    assistant = T3Assistant(service=CanonicalTransitService(reference_date=chosen_reference_date))
    replies = {}
    for index, row in enumerate(stress, 1):
        reply = assistant.process_query(row["query"])
        flag = str(row["clarification_required"]).lower()
        if flag not in {"true", "false"}:
            raise ValueError("Unknown clarification gold flag")
        replies[row["utterance_id"]] = {
            "gold": row["T3_label"], "intent": reply.intent, "operation": reply.operation,
            "status": reply.status, "gold_clarification": flag == "true",
            **{field: row.get(field) for field in ("language_class", "code_switch_level", "noise_level")},
        }
        if index % 100 == 0:
            print(f"Evaluated {index}/{len(stress)} frozen queries", flush=True)
    report = {
        "evaluation_type": "frozen_complete_assistant_contracts", "assistant_freeze_commit": revision,
        "checkpoint_sha256": load_manifest()["checkpoint_sha256"], "input_hashes": inputs,
        "canonical_database_sha256": sha256_file(DEFAULT_DB),
        "temporal_reference_date": chosen_reference_date.isoformat(),
        "stress": score_replies(list(replies.values())),
        "human_reference_subset": score_replies([replies[row["utterance_id"]] for row in reference]),
        "split_integrity": {"stress_vs_train": overlap_audit(train, stress),
                            "human_reference_vs_train": overlap_audit(train, reference)},
        "limitations": [
            "Terminal dispatch accuracy counts correct operation with ok, unavailable, or out_of_scope; it does not establish a correct transport answer.",
            "Selected operation accuracy includes missing-slot clarifications carrying an operation; entity clarifications may carry no operation.",
            "Clarification gold is the frozen query annotation. Canonical entity ambiguity, missing KB coverage, and conservative runtime requirements can cause additional clarifications.",
            "The 350-row human subset is nested in stress. Both sets have train-family overlap; full scores are descriptive, not independent family-held-out estimates.",
            "No gold domain answers or aligned canonical slot IDs are supplied by this evaluator; slot accuracy and factual answer accuracy are not claimed.",
            "No model, extractor, dispatcher, or service tuning is permitted from this final evaluation.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "assistant_evaluation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Frozen complete T3 assistant evaluation", "", f"Assistant freeze: `{revision}`.", "",
             "| Set | Queries | Intent accuracy | Selected operation accuracy | Terminal dispatch accuracy |",
             "|---|---:|---:|---:|---:|"]
    for key, title in (("stress", "Stress"), ("human_reference_subset", "Human subset")):
        result = report[key]
        lines.append(f"| {title} | {result['count']} | {result['strict_intent_accuracy']:.4f} | {result['selected_operation_accuracy']:.4f} | {result['terminal_dispatch_accuracy']:.4f} |")
        lines.extend(["", f"{title} statuses: `{result['status_counts']}`. Clarification: `{result['clarification']}`."])
    lines.extend(["", "Per-class and language/code-switch/noise aggregates, source hashes, and overlap counts are in `assistant_evaluation.json`.", "", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    (output_dir / "assistant_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--reference-date", type=date.fromisoformat, help="Fixed Chennai date for reproducible relative-day interpretation")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/nlp_v2/assistant_eval")
    args = parser.parse_args()
    report = evaluate(args.output_dir, freeze_commit=args.freeze_commit, reference_date=args.reference_date)
    print(json.dumps(report["stress"]["status_counts"]))


if __name__ == "__main__":
    main()
