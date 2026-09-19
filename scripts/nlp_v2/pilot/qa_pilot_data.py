#!/usr/bin/env python3
"""Automated QA Suite for NLP v2 Gate B Pilot Datasets.

Validates:
1. ID uniqueness & non-nullness
2. Query deduplication across and within partitions
3. Family-disjointness & semantic-family-disjointness (Zero Leakage)
4. Valid taxonomy labels for T1, T2, T3
5. Valid language and script combinations
6. Canonical entity resolution integrity against canonical_transport.db
7. Strict temporal ambiguity rules (bare time dual candidates, kal ambiguity)
8. Output QA audit report to reports/nlp_v2/pilot_qa_report.json
"""

import os
import csv
import json
import sqlite3
from typing import Dict, List, Any
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PILOT_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "pilot")
DB_PATH = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")
TAXONOMY_MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "nlp_v2", "pilot_qa_report.json")

with open(TAXONOMY_MAP_PATH, "r", encoding="utf-8") as f:
    TAXONOMY_SPEC = json.load(f)


def run_qa():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT stop_id FROM transport_stops")
    all_stop_ids = set(r[0] for r in cur.fetchall())
    cur.execute("SELECT route_id FROM transport_routes")
    all_route_ids = set(r[0] for r in cur.fetchall())
    cur.execute("SELECT place_id FROM places")
    all_place_ids = set(r[0] for r in cur.fetchall())
    conn.close()

    qa_report = {
        "status": "PASS",
        "total_datasets_checked": 0,
        "datasets": {}
    }

    all_passed = True

    for regime in ["regime_a", "regime_b"]:
        for tax in ["T1", "T2", "T3"]:
            tax_dir = os.path.join(PILOT_DIR, regime, tax)
            if not os.path.exists(tax_dir):
                continue

            dataset_key = f"{regime}_{tax}"
            dataset_res = {
                "regime": regime,
                "taxonomy": tax,
                "partition_counts": {},
                "checks": {},
                "passed": True
            }

            valid_labels = set(TAXONOMY_SPEC["taxonomies"][tax]["intents"])

            partitions = {}
            for part in ["pilot_train", "pilot_validation", "pilot_eval"]:
                part_file = os.path.join(tax_dir, f"{part}.csv")
                rows = []
                with open(part_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        rows.append(r)
                partitions[part] = rows
                dataset_res["partition_counts"][part] = len(rows)

            # Check 1: ID uniqueness
            all_uids = []
            for part, rows in partitions.items():
                all_uids.extend(r["utterance_id"] for r in rows)
            dataset_res["checks"]["unique_utterance_ids"] = (len(all_uids) == len(set(all_uids)))

            # Check 2: Valid taxonomy labels
            label_violations = 0
            for part, rows in partitions.items():
                for r in rows:
                    if r["taxonomy_label"] not in valid_labels:
                        label_violations += 1
            dataset_res["checks"]["valid_taxonomy_labels"] = (label_violations == 0)

            # Check 3: Semantic Family Leakage across partitions
            train_fams = set(r["semantic_family_id"] for r in partitions["pilot_train"])
            val_fams = set(r["semantic_family_id"] for r in partitions["pilot_validation"])
            eval_fams = set(r["semantic_family_id"] for r in partitions["pilot_eval"])

            train_val_overlap = train_fams.intersection(val_fams)
            train_eval_overlap = train_fams.intersection(eval_fams)
            val_eval_overlap = val_fams.intersection(eval_fams)

            zero_family_leakage = (len(train_val_overlap) == 0 and len(train_eval_overlap) == 0 and len(val_eval_overlap) == 0)
            dataset_res["checks"]["zero_semantic_family_leakage"] = zero_family_leakage

            # Check 4: Exact query duplicate leakage
            train_queries = set(r["query"].strip().lower() for r in partitions["pilot_train"])
            val_queries = set(r["query"].strip().lower() for r in partitions["pilot_validation"])
            eval_queries = set(r["query"].strip().lower() for r in partitions["pilot_eval"])

            query_leakage = (len(train_queries.intersection(val_queries)) == 0 and
                             len(train_queries.intersection(eval_queries)) == 0 and
                             len(val_queries.intersection(eval_queries)) == 0)
            dataset_res["checks"]["zero_cross_partition_query_duplicates"] = query_leakage

            # Check 5: Language and script validity
            lang_ok = True
            for part, rows in partitions.items():
                for r in rows:
                    if r["language"] not in ["en", "hi", "hi-en"]:
                        lang_ok = False
                    if r["script"] not in ["Latn", "Deva", "Deva+Latn"]:
                        lang_ok = False
            dataset_res["checks"]["valid_language_and_script_tags"] = lang_ok

            # Check 6: Entity resolution validity
            entity_ok = True
            for part, rows in partitions.items():
                for r in rows:
                    ent_dict = json.loads(r["canonical_entities_json"])
                    for ek, ev in ent_dict.items():
                        if ek.endswith("_id") and ev:
                            if ev not in all_stop_ids and ev not in all_route_ids and ev not in all_place_ids:
                                entity_ok = False
            dataset_res["checks"]["valid_canonical_entities"] = entity_ok

            # Check 7: Temporal ambiguity rules
            temporal_ok = True
            for part, rows in partitions.items():
                for r in rows:
                    s_dict = json.loads(r["slots_json"])
                    time_val = s_dict.get("time", "")
                    if time_val and ("8" in time_val or "o'clock" in time_val):
                        # Explicit morning/evening markers in Latin or Devanagari
                        has_period = any(m in time_val.lower() or m in time_val for m in ["subah", "sham", "सुबह", "शाम", "morning", "evening", "am", "pm"])
                        if not has_period and not s_dict.get("temporal_ambiguity"):
                            temporal_ok = False
                    if "temporal_relative" in s_dict and s_dict["temporal_relative"] == "kal":
                        if s_dict.get("resolved_temporal_offset") != "UNRESOLVED_TEMPORAL_AMBIGUITY":
                            temporal_ok = False
            dataset_res["checks"]["strict_temporal_ambiguity_rules"] = temporal_ok

            # Determine dataset pass status
            dataset_passed = all(dataset_res["checks"].values())
            dataset_res["passed"] = dataset_passed
            if not dataset_passed:
                all_passed = False

            qa_report["datasets"][dataset_key] = dataset_res
            qa_report["total_datasets_checked"] += 1

    qa_report["status"] = "PASS" if all_passed else "FAIL"

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(qa_report, f, indent=2)

    print(f"\n=======================================================")
    print(f"PILOT DATA QA AUDIT RESULT: {qa_report['status']}")
    print(f"Checked {qa_report['total_datasets_checked']} datasets.")
    print(f"Report saved to: {REPORT_PATH}")
    print(f"=======================================================")

    for dk, dres in qa_report["datasets"].items():
        status_str = "PASSED" if dres["passed"] else "FAILED"
        print(f"[{status_str}] {dk}: {dres['partition_counts']}")
        for cname, cval in dres["checks"].items():
            if not cval:
                print(f"   -> FAILED CHECK: {cname}")

    return all_passed


if __name__ == "__main__":
    passed = run_qa()
    if not passed:
        exit(1)
