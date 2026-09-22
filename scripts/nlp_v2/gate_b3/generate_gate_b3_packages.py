#!/usr/bin/env python3
"""Generates the Blind Annotation Packages for NLP v2 Gate B.3.

Amended v3.1 Design (Resource-Feasibility Amendment):
- 1 Student blind review package (counterbalanced 175/175 order split)
- 1 Model annotator blind package (MODEL_G = Gemini 3.8 Flash, 350 queries each for T2 and T3)
- Post-lock Gold Boundary Audit Template (350 rows, 12 active columns, blank annotations)
- Fail-closed guard against overwriting frozen configuration artifacts or resurrecting retired annotators

Strict Invariants:
- ZERO gold labels, predictions, or metadata in annotator packages.
- Source 350-query blind file remains byte-identical.
- Running generator NEVER resurrects MODEL_A or MODEL_B as active annotators.
"""

import os
import sys
import csv
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional

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


def generate_blind_packages(output_dir: str = GATE_B3_DIR) -> Dict[str, str]:
    """Generates the deterministic blind annotation packages for Gate B.3.

    Outputs:
    - student_order_manifest.json
    - student_t2_first_pass.csv
    - student_t3_first_pass.csv
    - student_t2_second_pass.csv
    - student_t3_second_pass.csv
    - model_g_t2_input.jsonl (350 blind queries)
    - model_g_t3_input.jsonl (350 blind queries)
    - gold_boundary_audit_template.csv (12 active columns, 350 rows)
    """
    print("=" * 70)
    print("Generating NLP v2 Gate B.3 Blind Annotation Packages (v3.1 Amended Design)")
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

    os.makedirs(output_dir, exist_ok=True)

    # 2. Deterministic 175/175 Student Split using SHA-256
    items = [{"annotation_id": r["annotation_id"], "query": r["query"]} for r in source_rows]

    def half_hash(item):
        return hashlib.sha256(f"gate_b3_half_split:{item['annotation_id']}".encode("utf-8")).hexdigest()

    items_sorted_for_split = sorted(items, key=half_hash)
    half_a_items = items_sorted_for_split[:175]
    half_b_items = items_sorted_for_split[175:]

    def order_hash_pass1(item):
        return hashlib.sha256(f"first_pass_order:{item['annotation_id']}".encode("utf-8")).hexdigest()

    def order_hash_pass2(item):
        return hashlib.sha256(f"second_pass_order:{item['annotation_id']}".encode("utf-8")).hexdigest()

    half_a_pass1 = sorted(half_a_items, key=order_hash_pass1)
    half_a_pass2 = sorted(half_a_items, key=order_hash_pass2)

    half_b_pass1 = sorted(half_b_items, key=order_hash_pass1)
    half_b_pass2 = sorted(half_b_items, key=order_hash_pass2)

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

    student_order_manifest = [order_dict[r["annotation_id"]] for r in source_rows]
    student_order_manifest_path = os.path.join(output_dir, "student_order_manifest.json")
    with open(student_order_manifest_path, "w", encoding="utf-8") as f:
        json.dump(student_order_manifest, f, indent=2)
    print(f"Exported student order manifest to: {student_order_manifest_path}")

    # 3. Export Clean Student Blind CSVs
    student_t2_p1_path = os.path.join(output_dir, "student_t2_first_pass.csv")
    with open(student_t2_p1_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_a_pass1:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T2"})

    student_t3_p1_path = os.path.join(output_dir, "student_t3_first_pass.csv")
    with open(student_t3_p1_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_b_pass1:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T3"})

    student_t2_p2_path = os.path.join(output_dir, "student_t2_second_pass.csv")
    with open(student_t2_p2_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_b_pass2:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T2"})

    student_t3_p2_path = os.path.join(output_dir, "student_t3_second_pass.csv")
    with open(student_t3_p2_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotation_id", "query", "taxonomy_version"])
        writer.writeheader()
        for it in half_a_pass2:
            writer.writerow({"annotation_id": it["annotation_id"], "query": it["query"], "taxonomy_version": "T3"})

    print("Exported 4 student blind CSV files (175 rows each).")

    # 4. Export Model Annotator Blind JSONL Files (MODEL_G only)
    model_g_files = [
        ("model_g_t2_input.jsonl", "T2"),
        ("model_g_t3_input.jsonl", "T3"),
    ]
    generated_paths = {
        "student_order_manifest": student_order_manifest_path,
        "student_t2_first_pass": student_t2_p1_path,
        "student_t3_first_pass": student_t3_p1_path,
        "student_t2_second_pass": student_t2_p2_path,
        "student_t3_second_pass": student_t3_p2_path,
    }

    for fname, tax in model_g_files:
        fpath = os.path.join(output_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            for it in items:
                rec = {
                    "annotation_id": it["annotation_id"],
                    "query": it["query"],
                    "taxonomy_version": tax,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        generated_paths[fname.replace(".jsonl", "")] = fpath
        print(f"Exported {fname} (350 queries, {tax}).")

    # 5. Export Active Post-Lock Gold Boundary Audit Template (12 active columns)
    audit_template_path = os.path.join(output_dir, "gold_boundary_audit_template.csv")
    audit_headers = [
        "annotation_id",
        "reference_T2",
        "reference_T3",
        "student_T2",
        "student_T3",
        "model_G_T2",
        "model_G_T3",
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
                "model_G_T2": "",
                "model_G_T3": "",
                "finding_category": "",
                "affected_boundary": "",
                "operation_consequence": "",
                "resolution_status": "",
                "justification": "",
            })
    generated_paths["gold_boundary_audit_template"] = audit_template_path
    print(f"Exported active gold boundary audit template (350 rows, 12 columns) to: {audit_template_path}")

    return generated_paths


def generate_manifests(output_dir: str = GATE_B3_DIR) -> Dict[str, str]:
    """Guarded manifest generator.

    Fails closed if asked to overwrite existing frozen configuration artifacts.
    Never resurrects MODEL_A or MODEL_B as active annotators.
    """
    model_configs_path = os.path.join(output_dir, "model_annotator_configs.json")
    manifest_path = os.path.join(output_dir, "gate_b3_annotation_manifest.json")

    # Fail-closed guard
    if os.path.exists(model_configs_path):
        with open(model_configs_path, "r", encoding="utf-8") as f:
            existing_cfg = json.load(f)
        if existing_cfg.get("configuration_frozen", False) or existing_cfg.get("primary_model_annotator_source_id") == "MODEL_G":
            raise RuntimeError(
                f"Fail-closed: {model_configs_path} contains active/frozen configuration. "
                "Package generator will not overwrite active configurations or resurrect retired annotators."
            )

    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            existing_m = json.load(f)
        if existing_m.get("model_configuration_status") == "FROZEN" or existing_m.get("first_pass_locked", False):
            raise RuntimeError(
                f"Fail-closed: {manifest_path} is frozen/locked. "
                "Package generator will not overwrite active study manifest."
            )

    # If writing to a new directory, ensure amended design is enforced
    os.makedirs(output_dir, exist_ok=True)
    model_configs = {
        "study": "Gate B.3 Annotation-Stability Framework",
        "primary_model_annotator_source_id": "MODEL_G",
        "primary_model_annotator_count": 1,
        "retired_primary_model_sources": ["MODEL_A", "MODEL_B"],
        "configuration_frozen": False,
        "frozen_at": None,
        "configuration_sha256": None,
        "MODEL_G": {
            "source_id": "MODEL_G",
            "provider": "Google",
            "model": "Gemini 3.8 Flash",
            "version": "Gemini 3.8 Flash",
            "exact_version_or_revision": "NOT_EXPOSED_BY_PROVIDER",
            "status": "FROZEN_NOT_EXECUTION_READY",
            "configuration_frozen": False,
            "primary_analysis_included": True,
            "benchmark_execution_authorized": False,
        },
        "MODEL_A": {
            "source_id": "MODEL_A",
            "provider": "OpenAI",
            "model": "GPT-6 Astra",
            "status": "ABORTED_PRE_AMENDMENT_EXECUTION",
            "primary_analysis_included": False,
            "benchmark_execution_authorized": False,
        },
        "MODEL_B": {
            "source_id": "MODEL_B",
            "provider": "Anthropic",
            "model": "Claude Opus 4.6",
            "status": "RETIRED_PRE_COMPLETION",
            "primary_analysis_included": False,
            "benchmark_execution_authorized": False,
        }
    }
    with open(model_configs_path, "w", encoding="utf-8") as f:
        json.dump(model_configs, f, indent=2)

    manifest_data = {
        "study_name": "Gate B.3 Annotation-Stability and Semantic-Boundary Audit",
        "study_version": "v3.1-amended-design",
        "base_commit": "c0985bfc53ab4328589876ce7a163f7bb11d2932",
        "active_kb": "chennai_multimodal_v1.2.2",
        "source_blind_file": "data/nlp_v2/gate_b2/human_annotation_blind.csv",
        "source_blind_sha256": EXPECTED_SOURCE_SHA256,
        "source_row_count": EXPECTED_ROW_COUNT,
        "sample_type": "purposive enriched challenge sample",
        "sampling_limitation": "Purposive/enriched challenge sample from Gate B.2 stress-eval. Not a representative random sample; does not guarantee complete minimal-pair or contrast-group coverage.",
        "model_configuration_status": "PENDING",
        "model_g_execution_ready": False,
        "annotation_started": False,
        "taxonomy_decision_status": "PENDING",
        "student_source_id": "STUDENT_R1",
        "primary_model_source_id": "MODEL_G",
        "retired_primary_model_sources": ["MODEL_A", "MODEL_B"],
        "taxonomies": ["T2", "T3"],
        "reference_join_enabled": False,
        "first_pass_locked": False,
        "gold_boundary_audit_started": False,
        "created_at": datetime.now().isoformat(),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return {
        "model_annotator_configs": model_configs_path,
        "gate_b3_annotation_manifest": manifest_path,
    }


def generate_packages(output_dir: str = GATE_B3_DIR, include_configs: bool = False):
    """Generates Gate B.3 packages.

    By default, generates blind packages only and preserves frozen configurations.
    If include_configs is True, runs generate_manifests() which enforces fail-closed checks.
    """
    generate_blind_packages(output_dir=output_dir)

    if include_configs:
        generate_manifests(output_dir=output_dir)
    else:
        print("Preserved existing frozen configurations (fail-closed protection).")

    print("=" * 70)
    print("PACKAGE GENERATION COMPLETE — ZERO ANNOTATIONS EXECUTED")
    print("=" * 70)


if __name__ == "__main__":
    generate_packages()

