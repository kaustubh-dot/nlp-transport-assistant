#!/usr/bin/env python3
"""Prepares the Blind Human Annotation Study Package for Gate B.2.

Samples 350 hard challenge utterances from gate_b2_stress_eval.csv across:
- Minimal pair contrast groups
- Ambiguous / multi-intent queries
- Implicit intent queries
- Route vs Multimodal boundaries
- Sequence vs Membership boundaries
- Timing subtypes (first/last vs frequency vs departure)
- Facility vs Accessibility boundaries

Outputs:
1. data/nlp_v2/gate_b2/human_annotation_blind.csv (Strictly blind: NO gold labels)
2. data/nlp_v2/gate_b2/human_annotation_key.json (Internal reference for agreement calculation)
"""

import os
import sys
import csv
import json
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STRESS_EVAL_CSV = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2", "gate_b2_stress_eval.csv")
OUTPUT_BLIND_CSV = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2", "human_annotation_blind.csv")
OUTPUT_KEY_JSON = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2", "human_annotation_key.json")

SEED = 42

def prepare_annotation_package():
    print("Loading stress_eval queries from:", STRESS_EVAL_CSV)
    with open(STRESS_EVAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    print(f"Total stress_eval candidate pool: {len(all_rows)} rows.")

    # Stratify challenge subsets
    minimal_pairs = [r for r in all_rows if r.get("contrast_group_id")]
    ambiguous = [r for r in all_rows if r.get("ambiguity_type") and r.get("ambiguity_type") != "none"]
    implicit = [r for r in all_rows if r.get("author_source") == "CURATED_HARD_CASE"]
    timing = [r for r in all_rows if r.get("T2_label") == "service_timing"]
    stops = [r for r in all_rows if r.get("T2_label") == "route_stops"]
    routes = [r for r in all_rows if r.get("T2_label") == "route_query"]
    facilities = [r for r in all_rows if r.get("T2_label") in ("station_facilities", "accessibility")]

    # Sample deterministically to reach 350 challenging cases
    rng = random.Random(SEED)
    selected_uids = set()
    selected_rows = []

    # Priority 1: All minimal pair items in stress eval (up to 150)
    rng.shuffle(minimal_pairs)
    for r in minimal_pairs:
        if len(selected_rows) < 150 and r["utterance_id"] not in selected_uids:
            selected_uids.add(r["utterance_id"])
            selected_rows.append(r)

    # Priority 2: Ambiguous cases (up to 70)
    rng.shuffle(ambiguous)
    for r in ambiguous:
        if len(selected_rows) < 220 and r["utterance_id"] not in selected_uids:
            selected_uids.add(r["utterance_id"])
            selected_rows.append(r)

    # Priority 3: Implicit cases (up to 60)
    rng.shuffle(implicit)
    for r in implicit:
        if len(selected_rows) < 280 and r["utterance_id"] not in selected_uids:
            selected_uids.add(r["utterance_id"])
            selected_rows.append(r)

    # Priority 4: Timing & Stops & Routes boundaries (up to 350)
    combined_pool = timing + stops + routes + facilities + all_rows
    rng.shuffle(combined_pool)
    for r in combined_pool:
        if len(selected_rows) < 350 and r["utterance_id"] not in selected_uids:
            selected_uids.add(r["utterance_id"])
            selected_rows.append(r)

    # Deterministically shuffle the selected 350 so annotators don't see grouping order
    rng.shuffle(selected_rows)
    print(f"Selected {len(selected_rows)} challenging utterances for blind human study.")

    # 1. Export Blind CSV (Strictly NO gold labels)
    blind_fields = [
        "annotation_id",
        "utterance_id",
        "query",
        "T2_reviewer_1",
        "T2_reviewer_2",
        "T3_reviewer_1",
        "T3_reviewer_2",
        "reviewer_1_clarification_required",
        "reviewer_2_clarification_required",
        "reviewer_1_notes",
        "reviewer_2_notes"
    ]

    blind_records = []
    key_records = {}

    for idx, row in enumerate(selected_rows, start=1):
        ann_id = f"ANN_B2_{idx:03d}"
        blind_records.append({
            "annotation_id": ann_id,
            "utterance_id": row["utterance_id"],
            "query": row["query"],
            "T2_reviewer_1": "",
            "T2_reviewer_2": "",
            "T3_reviewer_1": "",
            "T3_reviewer_2": "",
            "reviewer_1_clarification_required": "",
            "reviewer_2_clarification_required": "",
            "reviewer_1_notes": "",
            "reviewer_2_notes": ""
        })

        # Save gold key separately
        key_records[ann_id] = {
            "utterance_id": row["utterance_id"],
            "query": row["query"],
            "clean_query": row["clean_query"],
            "gold_T2_intent": row["T2_label"],
            "gold_T3_intent": row["T3_label"],
            "gold_subtype": row["semantic_subtype"],
            "gold_operation": row["semantic_operation"],
            "clarification_required": row["clarification_required"],
            "acceptable_secondary_labels": json.loads(row.get("acceptable_secondary_labels", "[]")),
            "contrast_group_id": row.get("contrast_group_id", "")
        }

    with open(OUTPUT_BLIND_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=blind_fields)
        writer.writeheader()
        writer.writerows(blind_records)

    with open(OUTPUT_KEY_JSON, "w", encoding="utf-8") as f:
        json.dump(key_records, f, indent=2, ensure_ascii=False)

    print(f"Exported blind annotation file to: {OUTPUT_BLIND_CSV}")
    print(f"Exported internal reference key to: {OUTPUT_KEY_JSON}")

if __name__ == "__main__":
    prepare_annotation_package()
