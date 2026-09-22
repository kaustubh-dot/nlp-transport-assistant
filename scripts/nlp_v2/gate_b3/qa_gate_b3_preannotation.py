#!/usr/bin/env python3
"""Pre-Annotation QA Gatekeeper for NLP v2 Gate B.3.

Enforces Section 55 requirements, as amended by Resource-Feasibility Amendment:
Hard-fails if:
1. Any annotation output file already contains labels
2. Model config is claimed completed before execution
3. Reference joins enabled before lock
4. Gold fields appear in annotator packages
5. Model predictions appear in annotator packages
6. Source blind SHA-256 changed or row count != 350
7. Taxonomy decision != PENDING
"""

import os
import sys
import csv
import json
import hashlib
import glob
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B2_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
REPORTS_B3_DIR = os.path.join(BASE_DIR, "reports", "nlp_v2", "gate_b3")

SOURCE_BLIND_CSV = os.path.join(GATE_B2_DIR, "human_annotation_blind.csv")
EXPECTED_SOURCE_SHA256 = "94fd8bb3e7f2e3bdaf274c4ee5bcf7e083e9ef2a66322fbcf7bee2cadf231999"
EXPECTED_ROW_COUNT = 350

MANIFEST_PATH = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
CONFIGS_PATH = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
AUDIT_TEMPLATE_PATH = os.path.join(GATE_B3_DIR, "gold_boundary_audit_template.csv")
DECISION_DOC_PATH = os.path.join(REPORTS_B3_DIR, "TAXONOMY_B3_DECISION_REQUIRED.md")

FORBIDDEN_FIELDS = {
    "utterance_id", "gold_T2_intent", "gold_T3_intent", "gold_subtype",
    "gold_operation", "T2_label", "T3_label", "semantic_operation",
    "semantic_subtype", "predictions", "prediction", "clean_query"
}


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_qa_checks():
    print("=" * 70)
    print("NLP v2 Gate B.3 Pre-Annotation QA Verification")
    print("=" * 70)

    failures = []

    # 1. Source Blind File Invariant
    print("\n1. Verifying Gate B.2 Source Blind CSV Invariant...")
    if not os.path.exists(SOURCE_BLIND_CSV):
        failures.append(f"Missing source blind file: {SOURCE_BLIND_CSV}")
    else:
        sha = compute_sha256(SOURCE_BLIND_CSV)
        if sha != EXPECTED_SOURCE_SHA256:
            failures.append(f"Source blind SHA-256 changed! Expected {EXPECTED_SOURCE_SHA256}, got {sha}")
        with open(SOURCE_BLIND_CSV, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != EXPECTED_ROW_COUNT:
            failures.append(f"Source blind row count != {EXPECTED_ROW_COUNT} (got {len(rows)})")
        print(f"  Source blind CSV verified: {EXPECTED_ROW_COUNT} rows, SHA-256 intact.")

    # 2. Manifest Gate Flags
    print("\n2. Verifying Manifest Pre-Annotation Guardrails...")
    if not os.path.exists(MANIFEST_PATH):
        failures.append(f"Missing manifest file: {MANIFEST_PATH}")
    else:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            m = json.load(f)

        if m.get("annotation_started") is not False:
            failures.append("Manifest annotation_started must be false prior to execution.")
        if m.get("first_pass_locked") is not False:
            failures.append("Manifest first_pass_locked must be false prior to execution.")
        if m.get("reference_join_enabled") is not False:
            failures.append("Manifest reference_join_enabled must be false prior to execution.")
        if m.get("gold_boundary_audit_started") is not False:
            failures.append("Manifest gold_boundary_audit_started must be false prior to execution.")
        if m.get("taxonomy_decision_status") != "PENDING":
            failures.append(f"Manifest taxonomy_decision_status must be PENDING (got '{m.get('taxonomy_decision_status')}')")
        if m.get("primary_model_source_id") != "MODEL_G":
            failures.append(f"Manifest primary_model_source_id must be MODEL_G (got '{m.get('primary_model_source_id')}')")
        print("  Manifest gate flags verified: annotation_started=False, locked=False, ref_join=False, decision=PENDING, primary=MODEL_G.")

    # 3. Model Annotator Configs Check
    print("\n3. Verifying Model Annotator Configs Pre-Execution Status...")
    if not os.path.exists(CONFIGS_PATH):
        failures.append(f"Missing model configs file: {CONFIGS_PATH}")
    else:
        with open(CONFIGS_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        ALLOWED_STATUSES = (
            "PENDING",
            "FROZEN_NOT_EXECUTION_READY",
            "FROZEN_EXECUTION_READY_NOT_AUTHORIZED",
            "FROZEN_EXECUTION_AUTHORIZED",
            "ABORTED_PRE_AMENDMENT_EXECUTION",
            "RETIRED_PRE_COMPLETION",
        )

        # Check Active Model MODEL_G
        if "MODEL_G" not in cfg:
            failures.append("Missing config section for MODEL_G")
        else:
            g_status = cfg["MODEL_G"].get("status")
            if g_status not in ALLOWED_STATUSES:
                failures.append(f"MODEL_G status must be one of {ALLOWED_STATUSES} (got '{g_status}')")
            if cfg["MODEL_G"].get("execution_timestamp") is not None:
                failures.append("MODEL_G execution_timestamp must be null")
            if cfg["MODEL_G"].get("benchmark_execution_authorized") is not False:
                failures.append("MODEL_G benchmark_execution_authorized must be false prior to sterile preflight and smoke test")

        # Check Historical Retired Models
        for m in ["MODEL_A", "MODEL_B"]:
            if m not in cfg:
                failures.append(f"Missing historical config section for {m}")
            else:
                m_status = cfg[m].get("status")
                if m_status not in ALLOWED_STATUSES:
                    failures.append(f"{m} status must be one of {ALLOWED_STATUSES} (got '{m_status}')")
                if cfg[m].get("primary_analysis_included") is not False:
                    failures.append(f"{m} primary_analysis_included must be false")
                if cfg[m].get("execution_timestamp") is not None:
                    failures.append(f"{m} execution_timestamp must be null")
        print("  Model configs verified: MODEL_G active pre-execution status valid, MODEL_A/B retired provenance preserved.")

    # 4. Check Annotator Packages for Leakage of Gold or Predictions
    print("\n4. Verifying Annotator Input Packages for Gold/Prediction Leakage...")
    packages = [
        os.path.join(GATE_B3_DIR, "student_t2_first_pass.csv"),
        os.path.join(GATE_B3_DIR, "student_t3_first_pass.csv"),
        os.path.join(GATE_B3_DIR, "student_t2_second_pass.csv"),
        os.path.join(GATE_B3_DIR, "student_t3_second_pass.csv"),
    ]
    for p in packages:
        if not os.path.exists(p):
            failures.append(f"Missing student package: {p}")
            continue
        with open(p, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            fields = set(r.fieldnames or [])
            leaked = fields & FORBIDDEN_FIELDS
            if leaked:
                failures.append(f"Forbidden fields {leaked} in {os.path.basename(p)}")
            if fields != {"annotation_id", "query", "taxonomy_version"}:
                failures.append(f"Unexpected fields in {os.path.basename(p)}: {fields}")

    model_packages = [
        os.path.join(GATE_B3_DIR, "model_g_t2_input.jsonl"),
        os.path.join(GATE_B3_DIR, "model_g_t3_input.jsonl"),
        os.path.join(GATE_B3_DIR, "model_a_t2_input.jsonl"),
        os.path.join(GATE_B3_DIR, "model_a_t3_input.jsonl"),
        os.path.join(GATE_B3_DIR, "model_b_t2_input.jsonl"),
        os.path.join(GATE_B3_DIR, "model_b_t3_input.jsonl"),
    ]
    for mp in model_packages:
        if not os.path.exists(mp):
            failures.append(f"Missing model package: {mp}")
            continue
        with open(mp, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                rec = json.loads(line)
                keys = set(rec.keys())
                leaked = keys & FORBIDDEN_FIELDS
                if leaked:
                    failures.append(f"Forbidden keys {leaked} in {os.path.basename(mp)} line {idx}")
                    break
                if keys != {"annotation_id", "query", "taxonomy_version"}:
                    failures.append(f"Unexpected keys in {os.path.basename(mp)} line {idx}: {keys}")
                    break
    print("  Annotator input packages verified: strictly blind, no gold, no predictions, no utterance IDs.")

    # 5. Check No Annotation Outputs Already Contain Labels
    print("\n5. Verifying Zero Pre-Filled Annotation Labels...")
    output_files = glob.glob(os.path.join(GATE_B3_DIR, "*_annotations.jsonl"))
    if output_files:
        failures.append(f"Annotation output files detected before execution: {output_files}")

    if not os.path.exists(AUDIT_TEMPLATE_PATH):
        failures.append(f"Missing audit template file: {AUDIT_TEMPLATE_PATH}")
    else:
        with open(AUDIT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, r in enumerate(reader, start=1):
                for col in ["student_T2", "student_T3", "model_G_T2", "model_G_T3", "model_A_T2", "model_A_T3", "model_B_T2", "model_B_T3"]:
                    if r.get(col, "").strip():
                        failures.append(f"Audit template line {idx} contains non-empty value in '{col}'!")
                        break
    print("  Zero pre-filled annotation labels verified.")

    # 6. Check Taxonomy Decision Artifact Status
    print("\n6. Verifying Taxonomy Decision Document Status...")
    if not os.path.exists(DECISION_DOC_PATH):
        failures.append(f"Missing taxonomy decision document: {DECISION_DOC_PATH}")
    else:
        with open(DECISION_DOC_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        if "GATE B.3 TAXONOMY DECISION: PENDING" not in content:
            failures.append("TAXONOMY_B3_DECISION_REQUIRED.md must explicitly declare 'GATE B.3 TAXONOMY DECISION: PENDING'")
        if "GATE C: NO" not in content and "status remains strictly PENDING" not in content and "PENDING" not in content:
            failures.append("TAXONOMY_B3_DECISION_REQUIRED.md decision status corrupted.")
        print("  Taxonomy decision document verified: status = PENDING.")

    # Summary
    print("\n" + "=" * 70)
    if failures:
        print(f"PRE-ANNOTATION QA FAILED WITH {len(failures)} ERROR(S):")
        for fail in failures:
            print(f"  [HARD-FAIL] {fail}")
        print("=" * 70)
        sys.exit(1)
    else:
        print("ALL GATE B.3 PRE-ANNOTATION QA CHECKS PASSED SUCCESSFULLY (6/6)")
        print("=" * 70)


if __name__ == "__main__":
    run_qa_checks()
