#!/usr/bin/env python3
"""First-Pass Annotation Locking Mechanism for NLP v2 Gate B.3.

Hardens Sections 1-6 requirements:
1. Exact Frozen ID Set:
   Loads EXPECTED_ANNOTATION_IDS from data/nlp_v2/gate_b2/human_annotation_blind.csv.
   Requires seen_ids == EXPECTED_ANNOTATION_IDS for all four active primary outputs.
   Hard-fails on missing, unexpected, or duplicate IDs.
2. Exact Record Count:
   Requires exactly 350 non-empty records per file (record_count == 350 and unique_id_count == 350).
3. Validate Source Identity per File:
   - student_t2_annotations.jsonl: source_id = STUDENT_R1, source_type = student, taxonomy_version = T2
   - student_t3_annotations.jsonl: source_id = STUDENT_R1, source_type = student, taxonomy_version = T3
   - model_g_t2_annotations.jsonl: source_id = MODEL_G, source_type = model, taxonomy_version = T2
   - model_g_t3_annotations.jsonl: source_id = MODEL_G, source_type = model, taxonomy_version = T3
4. Authoritative JSON Schema Validation:
   Validates every record against docs/nlp_v2/gate_b3/annotation_output_schema.json using Draft7Validator.
5. Semantic Validation Beyond Schema:
   - Student vs Model fields (recognized_from_prior_work, active_time_seconds, rule_difficulty)
   - Strict taxonomy vocabularies
   - Primary label in acceptable_labels
   - Clarification invariant (false -> empty reasons, true -> non-empty reasons)
6. Complete Lock Manifest:
   Records path, sha256, record_count, unique_id_count, source_id, source_type, taxonomy_version
   per file, plus frozen_source_blind_sha256, expected_annotation_id_count=350, and lock_timestamp.
"""

import os
import sys
import csv
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any

from jsonschema import Draft7Validator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B2_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
DOCS_B3_DIR = os.path.join(BASE_DIR, "docs", "nlp_v2", "gate_b3")

SOURCE_BLIND_CSV = os.path.join(GATE_B2_DIR, "human_annotation_blind.csv")
EXPECTED_SOURCE_SHA256 = "94fd8bb3e7f2e3bdaf274c4ee5bcf7e083e9ef2a66322fbcf7bee2cadf231999"

MANIFEST_PATH = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
LOCK_MANIFEST_PATH = os.path.join(GATE_B3_DIR, "first_pass_lock_manifest.json")
SCHEMA_PATH = os.path.join(DOCS_B3_DIR, "annotation_output_schema.json")

EXPECTED_OUTPUT_SPECS = {
    "student_t2_annotations.jsonl": {
        "source_id": "STUDENT_R1",
        "source_type": "student",
        "taxonomy_version": "T2",
    },
    "student_t3_annotations.jsonl": {
        "source_id": "STUDENT_R1",
        "source_type": "student",
        "taxonomy_version": "T3",
    },
    "model_g_t2_annotations.jsonl": {
        "source_id": "MODEL_G",
        "source_type": "model",
        "taxonomy_version": "T2",
    },
    "model_g_t3_annotations.jsonl": {
        "source_id": "MODEL_G",
        "source_type": "model",
        "taxonomy_version": "T3",
    },
}

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


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_expected_annotation_ids() -> Tuple[Set[str], str]:
    """Loads authoritative frozen annotation IDs from source blind file."""
    if not os.path.exists(SOURCE_BLIND_CSV):
        raise FileNotFoundError(f"Missing source blind file at {SOURCE_BLIND_CSV}")

    actual_sha = compute_sha256(SOURCE_BLIND_CSV)
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"Source blind SHA mismatch! Expected {EXPECTED_SOURCE_SHA256}, got {actual_sha}"
        )

    with open(SOURCE_BLIND_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ids = {r["annotation_id"] for r in reader}

    if len(ids) != 350:
        raise ValueError(f"Expected exactly 350 IDs from source blind CSV, got {len(ids)}")

    return ids, actual_sha


def load_validator() -> Draft7Validator:
    """Loads and compiles canonical Draft7Validator from annotation_output_schema.json."""
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Missing schema file at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft7Validator(schema)


def validate_record_semantics(rec: Dict[str, Any], spec: Dict[str, str], idx: int, filename: str):
    """Enforces deep semantic validation rules beyond structural JSON schema."""
    # 1. Source Identity
    if rec["source_id"] != spec["source_id"]:
        raise ValueError(
            f"[{filename} line {idx}] source_id mismatch: expected '{spec['source_id']}', got '{rec['source_id']}'"
        )
    if rec["source_type"] != spec["source_type"]:
        raise ValueError(
            f"[{filename} line {idx}] source_type mismatch: expected '{spec['source_type']}', got '{rec['source_type']}'"
        )
    if rec["taxonomy_version"] != spec["taxonomy_version"]:
        raise ValueError(
            f"[{filename} line {idx}] taxonomy_version mismatch: expected '{spec['taxonomy_version']}', got '{rec['taxonomy_version']}'"
        )

    # 2. Source-Specific Burden and Diagnostic Fields
    if spec["source_type"] == "student":
        if rec["recognized_from_prior_work"] not in ("true", "false", "unsure"):
            raise ValueError(
                f"[{filename} line {idx}] Student recognized_from_prior_work must be 'true', 'false', or 'unsure', got '{rec['recognized_from_prior_work']}'"
            )
        if not isinstance(rec["active_time_seconds"], (int, float)) or rec["active_time_seconds"] < 0:
            raise ValueError(
                f"[{filename} line {idx}] Student active_time_seconds must be a non-negative number, got '{rec['active_time_seconds']}'"
            )
        if rec["rule_difficulty"] not in ("easy", "moderate", "hard"):
            raise ValueError(
                f"[{filename} line {idx}] Student rule_difficulty must be 'easy', 'moderate', or 'hard', got '{rec['rule_difficulty']}'"
            )
    else:  # model
        if rec["recognized_from_prior_work"] != "not_applicable":
            raise ValueError(
                f"[{filename} line {idx}] Model recognized_from_prior_work must be 'not_applicable', got '{rec['recognized_from_prior_work']}'"
            )
        if rec["active_time_seconds"] is not None:
            raise ValueError(
                f"[{filename} line {idx}] Model active_time_seconds must be null, got '{rec['active_time_seconds']}'"
            )
        if rec["rule_difficulty"] != "not_applicable":
            raise ValueError(
                f"[{filename} line {idx}] Model rule_difficulty must be 'not_applicable', got '{rec['rule_difficulty']}'"
            )

    # 3. Taxonomy Vocabularies
    allowed_classes = T2_CLASSES if spec["taxonomy_version"] == "T2" else T3_CLASSES
    prim = rec["primary_label"]
    if prim is not None and prim not in allowed_classes:
        raise ValueError(
            f"[{filename} line {idx}] Invalid primary_label '{prim}' for {spec['taxonomy_version']}"
        )
    for acc in rec["acceptable_labels"]:
        if acc not in allowed_classes:
            raise ValueError(
                f"[{filename} line {idx}] Invalid acceptable_label '{acc}' for {spec['taxonomy_version']}"
            )

    # 4. Primary-Label in Acceptable-Set Invariant
    if prim is not None and prim not in rec["acceptable_labels"]:
        raise ValueError(
            f"[{filename} line {idx}] primary_label '{prim}' must be in acceptable_labels {rec['acceptable_labels']}"
        )

    # 5. Clarification Invariant
    if rec["clarification_required"] is False:
        if len(rec["clarification_reasons"]) != 0:
            raise ValueError(
                f"[{filename} line {idx}] clarification_reasons must be empty when clarification_required is false"
            )
    else:
        if len(rec["clarification_reasons"]) == 0:
            raise ValueError(
                f"[{filename} line {idx}] clarification_reasons must be non-empty when clarification_required is true"
            )


def attempt_lock() -> bool:
    print("=" * 70)
    print("NLP v2 Gate B.3 Hardened First-Pass Annotation Lock Attempt")
    print("=" * 70)

    # 1. Load Expected Frozen IDs
    expected_ids, source_sha = load_expected_annotation_ids()
    print(f"Loaded {len(expected_ids)} expected frozen annotation IDs (Source SHA: {source_sha[:16]}...).")

    # 2. Check File Existence
    missing_files = []
    for fname in EXPECTED_OUTPUT_SPECS:
        fpath = os.path.join(GATE_B3_DIR, fname)
        if not os.path.exists(fpath):
            missing_files.append(fname)

    if missing_files:
        print("LOCK REFUSED: Required annotation output files are missing:")
        for mf in missing_files:
            print(f"  - {mf}")
        print("All 4 annotator output files must exist before locking.")
        return False

    validator = load_validator()
    file_metadata = {}

    # 3. Validate Each File Strictly
    for fname, spec in EXPECTED_OUTPUT_SPECS.items():
        fpath = os.path.join(GATE_B3_DIR, fname)
        seen_ids = set()
        record_count = 0

        with open(fpath, "r", encoding="utf-8") as fp:
            for idx, line in enumerate(fp, start=1):
                line = line.strip()
                if not line:
                    continue
                record_count += 1
                try:
                    rec = json.loads(line)
                except Exception as e:
                    raise ValueError(f"[{fname} line {idx}] Malformed JSON: {e}")

                # JSON Schema validation
                errors = list(validator.iter_errors(rec))
                if errors:
                    first_err = errors[0]
                    raise ValueError(f"[{fname} line {idx}] Schema violation at '{first_err.json_path}': {first_err.message}")

                # Semantic validation
                validate_record_semantics(rec, spec, idx, fname)

                aid = rec["annotation_id"]
                if aid in seen_ids:
                    raise ValueError(f"[{fname} line {idx}] Duplicate annotation_id detected: '{aid}'")
                seen_ids.add(aid)

        # Invariant: exactly 350 records and unique IDs
        if record_count != 350:
            print(f"LOCK REFUSED: {fname} has {record_count} records (expected exactly 350).")
            return False
        if len(seen_ids) != 350:
            print(f"LOCK REFUSED: {fname} has {len(seen_ids)} unique IDs (expected exactly 350).")
            return False

        # Invariant: seen_ids == expected_ids
        missing_ids = expected_ids - seen_ids
        unexpected_ids = seen_ids - expected_ids
        if missing_ids or unexpected_ids:
            print(f"LOCK REFUSED: {fname} ID mismatch!")
            if missing_ids:
                print(f"  Missing IDs ({len(missing_ids)}): {sorted(list(missing_ids))[:5]}...")
            if unexpected_ids:
                print(f"  Unexpected IDs ({len(unexpected_ids)}): {sorted(list(unexpected_ids))[:5]}...")
            return False

        sha256 = compute_sha256(fpath)
        file_metadata[fname] = {
            "path": os.path.relpath(fpath, BASE_DIR),
            "sha256": sha256,
            "record_count": record_count,
            "unique_id_count": len(seen_ids),
            "source_id": spec["source_id"],
            "source_type": spec["source_type"],
            "taxonomy_version": spec["taxonomy_version"]
        }
        print(f"  Verified {fname}: 350 records, IDs match frozen set, SHA-256: {sha256[:16]}...")

    # 4. Write Complete Lock Manifest
    lock_manifest_data = {
        "lock_status": "LOCKED",
        "lock_timestamp": datetime.now().isoformat(),
        "expected_annotation_id_count": 350,
        "frozen_source_blind_sha256": source_sha,
        "files": file_metadata,
        "guardrails": {
            "reference_join_now_permitted": True,
            "gold_boundary_audit_now_permitted": True,
            "annotation_modification_forbidden": True
        }
    }

    with open(LOCK_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(lock_manifest_data, f, indent=2)

    # 5. Update Main Gate B.3 Manifest
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["first_pass_locked"] = True
        manifest["reference_join_enabled"] = True
        manifest["first_pass_lock_manifest"] = "data/nlp_v2/gate_b3/first_pass_lock_manifest.json"
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    print("ALL 4 PRIMARY ANNOTATOR PACKAGES VALIDATED AND LOCKED SUCCESSFULLY.")
    print(f"Complete lock manifest written to: {LOCK_MANIFEST_PATH}")
    return True


if __name__ == "__main__":
    success = attempt_lock()
    if not success:
        sys.exit(1)
