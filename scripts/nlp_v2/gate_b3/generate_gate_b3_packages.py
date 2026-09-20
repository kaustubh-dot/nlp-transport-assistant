#!/usr/bin/env python3
"""Generates the Blind Annotation Packages for NLP v2 Gate B.3.

Implementation of Astra-Approved Methodology Amendment:
- 1 Student blind review package (counterbalanced 175/175 order split)
- 2 Model annotator blind packages (MODEL_A and MODEL_B, 350 queries each for T2 and T3)
- Gate B.3 Annotation Manifest
- Post-lock Gold Boundary Audit Template (350 rows, blank annotations)
- Model Annotator Configuration Placeholders (PENDING)

Strict Invariant:
- ZERO gold labels, predictions, or metadata in annotator packages.
- Source 350-query blind file remains byte-identical.
"""

import os
import sys
import csv
import json
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B2_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
DOCS_B3_DIR = os.path.join(BASE_DIR, "docs", "nlp_v2", "gate_b3")

SOURCE_BLIND_CSV = os.path.join(GATE_B2_DIR, "human_annotation_blind.csv")
EXPECTED_SOURCE_SHA256 = "94fd8bb3e7f2e3bdaf274c4ee5bcf7e083e9ef2a66322fbcf7bee2cadf231999"
EXPECTED_ROW_COUNT = 350


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_packages():
    print("=" * 70)
    print("Generating NLP v2 Gate B.3 Annotation Packages")
    print("=" * 70)

    # 1. Verify Source Blind CSV Integrity
    if not os.path.exists(SOURCE_BLIND_CSV):
        raise FileNotFoundError(f"Missing source blind file: {SOURCE_BLIND_CSV}")

    actual_sha256 = compute_sha256(SOURCE_BLIND_CSV)
    if actual_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"Source blind SHA-256 mismatch!\nExpected: {EXPECTED_SOURCE_SHA256}\nActual:   {actual_sha256}"
        )
    print(f"Verified source blind file SHA-256: {actual_sha256[:16]}...")

    with open(SOURCE_BLIND_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        source_rows = list(reader)

    if len(source_rows) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Expected {EXPECTED_ROW_COUNT} rows in source blind file, got {len(source_rows)}")
    print(f"Loaded {len(source_rows)} blind challenge queries from Gate B.2.")

    os.makedirs(GATE_B3_DIR, exist_ok=True)

    # 2. Deterministic 175/175 Student Split using SHA-256
    # Each item has annotation_id "ANN_B2_xxx" and query
    items = [{"annotation_id": r["annotation_id"], "query": r["query"]} for r in source_rows]

    # Deterministic assignment to Half A vs Half B
    # Sort items by sha256(f"gate_b3_half_split:{ann_id}")
    def half_hash(item):
        return hashlib.sha256(f"gate_b3_half_split:{item['annotation_id']}".encode("utf-8")).hexdigest()

    items_sorted_for_split = sorted(items, key=half_hash)
    half_a_items = items_sorted_for_split[:175]
    half_b_items = items_sorted_for_split[175:]

    half_a_ids = {it["annotation_id"] for it in half_a_items}
    half_b_ids = {it["annotation_id"] for it in half_b_items}

    # Deterministic presentation order within Half A (first pass: T2, second pass: T3)
    def order_hash_pass1(item):
        return hashlib.sha256(f"first_pass_order:{item['annotation_id']}".encode("utf-8")).hexdigest()

    def order_hash_pass2(item):
        return hashlib.sha256(f"second_pass_order:{item['annotation_id']}".encode("utf-8")).hexdigest()

    half_a_pass1 = sorted(half_a_items, key=order_hash_pass1)
    half_a_pass2 = sorted(half_a_items, key=order_hash_pass2)

    half_b_pass1 = sorted(half_b_items, key=order_hash_pass1)
    half_b_pass2 = sorted(half_b_items, key=order_hash_pass2)

    # Build student order manifest
    order_dict = {}
    for idx, it in enumerate(half_a_pass1, start=1):
        order_dict[it["annotation_id"]] = {
            "annotation_id": it["annotation_id"],
            "half": "A",
            "first_taxonomy": "T2",
            "second_taxonomy": "T3",
            "first_pass_order": idx,
            "second_pass_order": None,
        }
    for idx, it in enumerate(half_a_pass2, start=1):
        order_dict[it["annotation_id"]]["second_pass_order"] = idx

    for idx, it in enumerate(half_b_pass1, start=1):
        order_dict[it["annotation_id"]] = {
            "annotation_id": it["annotation_id"],
            "half": "B",
            "first_taxonomy": "T3",
            "second_taxonomy": "T2",
            "first_pass_order": idx,
            "second_pass_order": None,
        }
    for idx, it in enumerate(half_b_pass2, start=1):
        order_dict[it["annotation_id"]]["second_pass_order"] = idx

    # Manifest ordered by original annotation_id
    student_order_manifest = [order_dict[r["annotation_id"]] for r in source_rows]

    student_order_manifest_path = os.path.join(GATE_B3_DIR, "student_order_manifest.json")
    with open(student_order_manifest_path, "w", encoding="utf-8") as f:
        json.dump(student_order_manifest, f, indent=2)
    print(f"Exported student order manifest to: {student_order_manifest_path}")

    # 3. Export Clean Student Blind CSVs
    # Half A: T2 First Pass
    student_t2_p1_path = os.path.join(GATE_B3_DIR, "student_t2_first_pass.csv")
    with open(student_t2_p1_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_a_pass1:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T2"})

    # Half B: T3 First Pass
    student_t3_p1_path = os.path.join(GATE_B3_DIR, "student_t3_first_pass.csv")
    with open(student_t3_p1_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_b_pass1:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T3"})

    # Half B: T2 Second Pass
    student_t2_p2_path = os.path.join(GATE_B3_DIR, "student_t2_second_pass.csv")
    with open(student_t2_p2_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_b_pass2:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T2"})

    # Half A: T3 Second Pass
    student_t3_p2_path = os.path.join(GATE_B3_DIR, "student_t3_second_pass.csv")
    with open(student_t3_p2_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_a_pass2:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T3"})

    print("Exported 4 student blind CSV files (175 rows each).")

    # 4. Export Model Annotator Blind JSONL Files (350 queries each)
    model_files = [
        ("model_a_t2_input.jsonl", "T2"),
        ("model_a_t3_input.jsonl", "T3"),
        ("model_b_t2_input.jsonl", "T2"),
        ("model_b_t3_input.jsonl", "T3"),
    ]

    for fname, tax in model_files:
        fpath = os.path.join(GATE_B3_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            for it in items:
                rec = {
                    "annotation_id": it["annotation_id"],
                    "query": it["query"],
                    "taxonomy_version": tax,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"Exported {fname} (350 queries, {tax}).")

    # 5. Export Model Annotator Configs Placeholder
    model_configs = {
        "study": "Gate B.3 Annotation-Stability Framework",
        "MODEL_A": {
            "provider": "PENDING",
            "model": "PENDING",
            "version": "PENDING",
            "status": "PENDING",
            "execution_timestamp": None,
            "decoding_parameters": {
                "temperature": 0.0,
                "max_tokens": 1024
            },
            "tool_availability": "NONE",
            "prompt_hash": None,
            "taxonomy_guide_hash": None,
            "provenance_notes": "Astra review context must never be reused. Must use clean isolated request context."
        },
        "MODEL_B": {
            "provider": "PENDING",
            "model": "PENDING",
            "version": "PENDING",
            "status": "PENDING",
            "execution_timestamp": None,
            "decoding_parameters": {
                "temperature": 0.0,
                "max_tokens": 1024
            },
            "tool_availability": "NONE",
            "prompt_hash": None,
            "taxonomy_guide_hash": None,
            "provenance_notes": "Distinct model family from MODEL_A recommended for family diversity."
        }
    }
    model_configs_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(model_configs_path, "w", encoding="utf-8") as f:
        json.dump(model_configs, f, indent=2)
    print(f"Exported model annotator configs placeholder to: {model_configs_path}")

    # 6. Export Post-Lock Gold Boundary Audit Template
    audit_template_path = os.path.join(GATE_B3_DIR, "gold_boundary_audit_template.csv")
    audit_headers = [
        "annotation_id",
        "reference_T2",
        "reference_T3",
        "student_T2",
        "student_T3",
        "model_A_T2",
        "model_A_T3",
        "model_B_T2",
        "model_B_T3",
        "finding_category",
        "affected_boundary",
        "operation_consequence",
        "resolution_status",
        "justification",
    ]
    with open(audit_template_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=audit_headers)
        writer.writeheader()
        for it in items:
            writer.writerow({
                "annotation_id": it["annotation_id"],
                "reference_T2": "",
                "reference_T3": "",
                "student_T2": "",
                "student_T3": "",
                "model_A_T2": "",
                "model_A_T3": "",
                "model_B_T2": "",
                "model_B_T3": "",
                "finding_category": "",
                "affected_boundary": "",
                "operation_consequence": "",
                "resolution_status": "",
                "justification": "",
            })
    print(f"Exported gold boundary audit template (350 rows, blank annotations) to: {audit_template_path}")

    # 7. Export Gate B.3 Annotation Manifest
    manifest_data = {
        "study_name": "Gate B.3 Annotation-Stability and Semantic-Boundary Audit",
        "study_version": "v3.0-pre-annotation",
        "base_commit": "51c7d74d6e38fef8795b5a04b711e8a17b7e2608",
        "active_kb": "chennai_multimodal_v1.2.2",
        "source_blind_file": "data/nlp_v2/gate_b2/human_annotation_blind.csv",
        "source_blind_sha256": actual_sha256,
        "source_row_count": len(source_rows),
        "sample_type": "purposive enriched challenge sample",
        "sampling_limitation": "Purposive/enriched challenge sample from Gate B.2 stress-eval. Not a representative random sample; does not guarantee complete minimal-pair or contrast-group coverage.",
        "annotation_started": False,
        "taxonomy_decision_status": "PENDING",
        "student_source_id": "STUDENT_R1",
        "model_source_a_id": "MODEL_A",
        "model_source_b_id": "MODEL_B",
        "taxonomies": ["T2", "T3"],
        "student_order_assignment_strategy": "deterministic_sha256_counterbalanced_half_split",
        "student_prior_exposure_required": True,
        "model_isolation_required": True,
        "gold_hidden_during_first_pass": True,
        "predictions_hidden_during_first_pass": True,
        "other_annotators_hidden_during_first_pass": True,
        "reference_join_enabled": False,
        "first_pass_locked": False,
        "gold_boundary_audit_started": False,
        "methodology_amendment_path": "docs/nlp_v2/gate_b3/gate_b3_annotation_methodology_amendment.md",
        "created_at": datetime.now().isoformat(),
        "packages": {
            "student_order_manifest": "data/nlp_v2/gate_b3/student_order_manifest.json",
            "student_t2_first_pass": "data/nlp_v2/gate_b3/student_t2_first_pass.csv",
            "student_t3_first_pass": "data/nlp_v2/gate_b3/student_t3_first_pass.csv",
            "student_t2_second_pass": "data/nlp_v2/gate_b3/student_t2_second_pass.csv",
            "student_t3_second_pass": "data/nlp_v2/gate_b3/student_t3_second_pass.csv",
            "model_a_t2_input": "data/nlp_v2/gate_b3/model_a_t2_input.jsonl",
            "model_a_t3_input": "data/nlp_v2/gate_b3/model_a_t3_input.jsonl",
            "model_b_t2_input": "data/nlp_v2/gate_b3/model_b_t2_input.jsonl",
            "model_b_t3_input": "data/nlp_v2/gate_b3/model_b_t3_input.jsonl",
            "model_annotator_configs": "data/nlp_v2/gate_b3/model_annotator_configs.json",
            "gold_boundary_audit_template": "data/nlp_v2/gate_b3/gold_boundary_audit_template.csv",
            "output_schema": "docs/nlp_v2/gate_b3/annotation_output_schema.json",
            "t2_annotation_guide": "docs/nlp_v2/gate_b3/t2_annotation_guide.md",
            "t3_annotation_guide": "docs/nlp_v2/gate_b3/t3_annotation_guide.md",
            "model_prompt_template": "docs/nlp_v2/gate_b3/model_annotator_prompt_template.md"
        }
    }

    manifest_path = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Exported Gate B.3 annotation manifest to: {manifest_path}")

    print("=" * 70)
    print("PACKAGE GENERATION COMPLETE — ZERO ANNOTATIONS EXECUTED")
    print("=" * 70)


if __name__ == "__main__":
    generate_packages()
