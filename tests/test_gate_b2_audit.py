"""Automated Regression & Audit Tests for NLP v2 Gate B.2.

Verifies:
1. Egmore resolves to HUB_EGMORE and never to Central.
2. Every declared canonical ID strictly exists in its designated DB table.
3. T2 and T3 ambiguity-aware secondary mapping consistency.
4. Human blind CSV integrity (350 rows, blank reviewer fields, no gold labels).
5. 1:1 bijection between blind annotation IDs and gold key IDs.
6. Convergence report values match metric JSON files.
7. Text surface stability between frozen stress_eval and versioned metadata v2.
"""

import os
import csv
import json
import sqlite3
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "gate_b2")
REPORT_DIR = os.path.join(BASE_DIR, "reports", "nlp_v2", "gate_b2")
DB_PATH = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")


def test_egmore_resolution_not_central():
    """Verify Egmore maps to HUB_EGMORE and not Central."""
    import scripts.nlp_v2.gate_b2.ground_entities as ge
    gazetteer = ge.CanonicalGazetteer(DB_PATH)

    egmore_meta = gazetteer.alias_map.get("egmore")
    assert egmore_meta is not None, "Egmore alias not found in gazetteer!"
    assert egmore_meta["canonical_id"] == "HUB_EGMORE", f"Egmore canonical_id is {egmore_meta['canonical_id']}, expected HUB_EGMORE"
    assert "CENTRAL" not in egmore_meta["canonical_id"], "Egmore mistakenly resolved to Central!"

    # Test query extraction
    extracted = gazetteer.extract_entities_from_text("Alandur to Egmore route guidance", "point_to_point")
    egmore_ents = [e for e in extracted if "egmore" in e["surface"].lower()]
    assert len(egmore_ents) == 1
    assert egmore_ents[0]["canonical_id"] == "HUB_EGMORE"
    assert egmore_ents[0]["canonical_name"] == "Egmore"


def test_all_declared_canonical_ids_exist_in_db():
    """Verify all manually declared IDs exist in their specific target DB tables."""
    import scripts.nlp_v2.gate_b2.audit_entity_grounding as aeg
    summary, _ = aeg.run_gazetteer_audit()

    assert summary["status_counts"]["AMBIGUOUS"] == 0, f"Found unresolved ambiguous entities: {summary['status_counts']['AMBIGUOUS']}"
    assert summary["mode_operator_validation"]["failed"] == 0, "Found mode/operator validation failures!"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT hub_id FROM transport_hubs")
    valid_hubs = set(r[0] for r in cur.fetchall())

    cur.execute("SELECT stop_id FROM transport_stops")
    valid_stops = set(r[0] for r in cur.fetchall())

    cur.execute("SELECT place_id FROM places")
    valid_places = set(r[0] for r in cur.fetchall())

    cur.execute("SELECT route_id FROM transport_routes")
    valid_routes = set(r[0] for r in cur.fetchall())

    table_sets = {
        "transport_hub": valid_hubs,
        "transport_stop": valid_stops,
        "place": valid_places,
        "transport_route": valid_routes
    }

    for rec in summary["records"]:
        cid = rec["declared_canonical_id"]
        etype = rec["declared_entity_type"]
        assert cid in table_sets[etype], f"ID '{cid}' does not exist in target DB table for {etype}"


def test_ambiguity_aware_secondary_mapping_consistency():
    """Verify T3 -> Operation -> T2 mapping completeness."""
    from scripts.nlp_v2.gate_b2.evaluate_gate_b2 import T3_TO_OP, T3_TO_T2
    from scripts.nlp_v2.gate_b2.qa_gate_b2_data import T2_ALLOWED, T3_ALLOWED, VALID_OPERATIONS

    assert len(T3_TO_OP) == 16, f"Expected 16 T3 classes mapped to operations, got {len(T3_TO_OP)}"
    assert len(T3_TO_T2) == 16, f"Expected 16 T3 classes mapped to T2 intents, got {len(T3_TO_T2)}"

    for t3_label in T3_ALLOWED:
        assert t3_label in T3_TO_OP, f"T3 label '{t3_label}' missing from T3_TO_OP"
        assert t3_label in T3_TO_T2, f"T3 label '{t3_label}' missing from T3_TO_T2"
        assert T3_TO_OP[t3_label] in VALID_OPERATIONS, f"Mapped operation '{T3_TO_OP[t3_label]}' not in VALID_OPERATIONS"
        assert T3_TO_T2[t3_label] in T2_ALLOWED, f"Mapped T2 intent '{T3_TO_T2[t3_label]}' not in T2_ALLOWED"


def test_human_annotation_blind_csv_integrity():
    """Verify human blind CSV contains 350 rows, blank reviewer fields, and no gold columns."""
    blind_path = os.path.join(DATA_DIR, "human_annotation_blind.csv")
    assert os.path.exists(blind_path), f"Missing {blind_path}"

    with open(blind_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = list(reader)

    assert len(rows) == 350, f"Expected exactly 350 rows, got {len(rows)}"

    # Check forbidden gold fields
    forbidden_gold = ["T2_label", "T3_label", "semantic_operation", "gold_T2_intent", "gold_T3_intent", "gold_operation"]
    for fg in forbidden_gold:
        assert fg not in fields, f"Forbidden gold field '{fg}' exposed in blind CSV!"

    # Check reviewer fields are 100% blank
    reviewer_fields = [
        "T2_reviewer_1", "T2_reviewer_2", "T3_reviewer_1", "T3_reviewer_2",
        "reviewer_1_clarification_required", "reviewer_2_clarification_required",
        "reviewer_1_notes", "reviewer_2_notes"
    ]
    for row in rows:
        for rf in reviewer_fields:
            val = str(row.get(rf, "")).strip()
            assert val == "", f"Reviewer field '{rf}' must be blank, found '{val}' in {row.get('annotation_id')}"


def test_annotation_ids_map_uniquely_to_gold_key():
    """Verify 1:1 bijection between blind annotation IDs and gold key."""
    blind_path = os.path.join(DATA_DIR, "human_annotation_blind.csv")
    key_path = os.path.join(DATA_DIR, "human_annotation_key.json")
    manifest_path = os.path.join(DATA_DIR, "human_annotation_manifest.json")

    assert os.path.exists(key_path), f"Missing {key_path}"
    assert os.path.exists(manifest_path), f"Missing {manifest_path}"

    with open(blind_path, "r", encoding="utf-8") as f:
        blind_rows = list(csv.DictReader(f))

    with open(key_path, "r", encoding="utf-8") as f:
        key_data = json.load(f)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert len(blind_rows) == 350
    assert len(key_data) == 350
    assert manifest["sample_size"] == 350
    assert manifest["status"] == "AWAITING_HUMAN_REVIEW"

    for r in blind_rows:
        ann_id = r["annotation_id"]
        assert ann_id in key_data, f"Annotation ID '{ann_id}' missing from gold key!"
        assert r["utterance_id"] == key_data[ann_id]["utterance_id"]
        assert r["query"] == key_data[ann_id]["query"]


def test_convergence_report_matches_metric_jsons():
    """Verify reported convergence values in markdown match authoritative metric JSONs."""
    report_path = os.path.join(REPORT_DIR, "convergence_report.md")
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    # T2-H Seed 42, 101, 777
    expected_values = {
        42: (9, 0.8563),
        101: (10, 0.8723),
        777: (11, 0.8883)
    }

    for s, (exp_epoch, exp_f1) in expected_values.items():
        json_path = os.path.join(EXP_DIR, f"metrics_t2h_muril_seed{s}.json")
        with open(json_path, "r", encoding="utf-8") as f:
            m = json.load(f)

        assert m["best_epoch"] == exp_epoch
        assert round(m["best_val_op_f1"], 4) == exp_f1

        # Check markdown contains the value
        assert f"Val Op-F1: {exp_f1:.4f}" in report_text, f"Val Op-F1: {exp_f1:.4f} not found in convergence report!"


def test_stress_eval_surface_stability_and_v2_alignment():
    """Verify 706 stress queries have 0 text drift between frozen eval and metadata v2."""
    orig_path = os.path.join(DATA_DIR, "gate_b2_stress_eval.csv")
    v2_path = os.path.join(DATA_DIR, "gate_b2_stress_eval_metadata_v2.csv")

    with open(orig_path, "r", encoding="utf-8") as f_orig, open(v2_path, "r", encoding="utf-8") as f_v2:
        r_orig = list(csv.DictReader(f_orig))
        r_v2 = list(csv.DictReader(f_v2))

    assert len(r_orig) == 706
    assert len(r_v2) == 706

    for ro, rv in zip(r_orig, r_v2):
        assert ro["utterance_id"] == rv["utterance_id"]
        assert ro["query"] == rv["query"]
        assert ro["clean_query"] == rv["clean_query"]
        assert ro["T2_label"] == rv["T2_label"]
        assert ro["T3_label"] == rv["T3_label"]
        assert ro["semantic_operation"] == rv["semantic_operation"]
        assert ro["contrast_group_id"] == rv["contrast_group_id"]
