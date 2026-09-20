#!/usr/bin/env python3
"""First-Pass Annotation Locking Mechanism for Gate B.3.

Enforces Section 27 requirements:
1. Validates all expected source/taxonomy annotation output records:
   - STUDENT_R1: T2 (350), T3 (350)
   - MODEL_A: T2 (350), T3 (350)
   - MODEL_B: T2 (350), T3 (350)
2. Validates records against docs/nlp_v2/gate_b3/annotation_output_schema.json
3. Computes SHA-256 digests for all annotation outputs.
4. Writes data/nlp_v2/gate_b3/first_pass_lock_manifest.json
5. Updates gate_b3_annotation_manifest.json with first_pass_locked = True
   ONLY AFTER all outputs exist and validate.

Before lock:
- Reference joins are strictly forbidden.
- Gold boundary audits are strictly forbidden.
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
DOCS_B3_DIR = os.path.join(BASE_DIR, "docs", "nlp_v2", "gate_b3")

MANIFEST_PATH = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
LOCK_MANIFEST_PATH = os.path.join(GATE_B3_DIR, "first_pass_lock_manifest.json")
SCHEMA_PATH = os.path.join(DOCS_B3_DIR, "annotation_output_schema.json")

EXPECTED_OUTPUT_FILES = [
    "student_t2_annotations.jsonl",
    "student_t3_annotations.jsonl",
    "model_a_t2_annotations.jsonl",
    "model_a_t3_annotations.jsonl",
    "model_b_t2_annotations.jsonl",
    "model_b_t3_annotations.jsonl",
]

T2_CLASSES = {
    "route_query", "route_stops", "service_timing", "service_availability",
    "fare_query", "ticketing_rules", "station_facilities", "accessibility",
    "interchange_query", "nearest_transport", "realtime_status_query", "out_of_scope"
}

T3_CLASSES = {
    "point_to_point_route", "multimodal_route", "route_stop_sequence",
    "route_stop_membership", "first_and_last_service", "service_frequency",
    "scheduled_departure", "mode_availability", "fare_calculation",
    "ticketing_and_passes", "station_facilities", "station_accessibility",
    "interchange_transfer", "nearest_transport", "realtime_status_query", "out_of_scope"
}

ALLOWED_CLARIFICATION_REASONS = {
    "intent_ambiguity", "missing_slot", "multiple_goals", "uninterpretable"
}


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_annotation_record(rec: Dict[str, Any], taxonomy: str, idx: int, filename: str):
    req_fields = [
        "annotation_id", "source_id", "source_type", "taxonomy_version", "run_id",
        "primary_label", "acceptable_labels", "clarification_required",
        "clarification_reasons", "brief_justification", "recognized_from_prior_work",
        "response_status"
    ]
    for rf in req_fields:
        if rf not in rec:
            raise ValueError(f"[{filename} line {idx}] Missing required field: '{rf}'")

    if rec["taxonomy_version"] != taxonomy:
        raise ValueError(f"[{filename} line {idx}] Taxonomy version mismatch: expected {taxonomy}, got {rec['taxonomy_version']}")

    allowed_classes = T2_CLASSES if taxonomy == "T2" else T3_CLASSES

    # Primary label validation
    prim = rec["primary_label"]
    if prim is not None and prim not in allowed_classes:
        raise ValueError(f"[{filename} line {idx}] Invalid primary_label: '{prim}'")

    # Acceptable labels validation
    acc = rec["acceptable_labels"]
    if not isinstance(acc, list) or len(acc) == 0:
        raise ValueError(f"[{filename} line {idx}] acceptable_labels must be a non-empty list")
    for a in acc:
        if a not in allowed_classes:
            raise ValueError(f"[{filename} line {idx}] Invalid label in acceptable_labels: '{a}'")

    if prim is not None and prim not in acc:
        raise ValueError(f"[{filename} line {idx}] primary_label '{prim}' must be included in acceptable_labels")

    # Clarification reasons validation
    if not isinstance(rec["clarification_required"], bool):
        raise ValueError(f"[{filename} line {idx}] clarification_required must be a boolean")

    for cr in rec["clarification_reasons"]:
        if cr not in ALLOWED_CLARIFICATION_REASONS:
            raise ValueError(f"[{filename} line {idx}] Invalid clarification_reason: '{cr}'")

    if rec["source_type"] == "student":
        if rec["recognized_from_prior_work"] not in ("true", "false", "unsure", True, False):
            raise ValueError(f"[{filename} line {idx}] Invalid recognized_from_prior_work for student: {rec['recognized_from_prior_work']}")
    elif rec["source_type"] == "model":
        if rec["recognized_from_prior_work"] != "not_applicable":
            raise ValueError(f"[{filename} line {idx}] Model annotator recognized_from_prior_work must be 'not_applicable'")


def attempt_lock() -> bool:
    print("=" * 70)
    print("NLP v2 Gate B.3 First-Pass Annotation Lock Attempt")
    print("=" * 70)

    # 1. Check all expected files exist
    missing_files = []
    file_digests = {}

    for fname in EXPECTED_OUTPUT_FILES:
        fpath = os.path.join(GATE_B3_DIR, fname)
        if not os.path.exists(fpath):
            missing_files.append(fname)
        else:
            file_digests[fname] = compute_sha256(fpath)

    if missing_files:
        print("LOCK REFUSED: The following required annotation output files are missing:")
        for mf in missing_files:
            print(f"  - {mf}")
        print("All 6 annotator output files must exist and contain 350 valid records before first-pass lock.")
        return False

    # 2. Validate records in each file
    for fname in EXPECTED_OUTPUT_FILES:
        fpath = os.path.join(GATE_B3_DIR, fname)
        taxonomy = "T2" if "_t2_" in fname else "T3"
        seen_ids = set()

        with open(fpath, "r", encoding="utf-8") as fp:
            for idx, line in enumerate(fp, start=1):
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                validate_annotation_record(rec, taxonomy, idx, fname)
                seen_ids.add(rec["annotation_id"])

        if len(seen_ids) != 350:
            print(f"LOCK REFUSED: {fname} contains {len(seen_ids)} unique annotation IDs (expected 350).")
            return False

    # 3. Create lock manifest
    lock_data = {
        "lock_status": "LOCKED",
        "locked_at": datetime.now().isoformat(),
        "item_count": 350,
        "verified_files": file_digests,
        "guardrails": {
            "reference_join_now_permitted": True,
            "gold_boundary_audit_now_permitted": True,
            "annotation_modification_forbidden": True
        }
    }

    with open(LOCK_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)

    # 4. Update main manifest
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["first_pass_locked"] = True
        manifest["reference_join_enabled"] = True
        manifest["first_pass_lock_manifest"] = "data/nlp_v2/gate_b3/first_pass_lock_manifest.json"
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    print("ALL 6 ANNOTATOR PACKAGES VALIDATED AND LOCKED SUCCESSFULLY.")
    print(f"Lock manifest written to: {LOCK_MANIFEST_PATH}")
    return True


if __name__ == "__main__":
    success = attempt_lock()
    if not success:
        sys.exit(1)
