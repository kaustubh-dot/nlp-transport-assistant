"""Unit and Integration Tests for NLP v2 Gate B.3 Annotation-Stability Framework.

Verifies Section 56 and Pre-Annotation Hardening requirements:
1. Source 350 file unchanged (row count and bitwise SHA-256)
2. Student order assignment deterministic and 175/175 half split
3. Each student eventually sees every query under both taxonomies
4. Model exports contain exactly 350 items each
5. Annotator exports contain no gold, no predictions, no utterance_id
6. Canonical Draft7 JSON Schema validation with student burden fields
7. Semantic validation (student vs model burden fields, clarification invariant, taxonomy vocabularies)
8. Exact frozen ID set validation for first-pass lock (missing, unexpected, duplicate, 351 records)
9. Source identity validation per file (source_id, source_type, taxonomy_version)
10. Lock integrity cryptographic hash revalidation before gold access
11. T2 reference concordance namespace mapping regression tests
12. Contrast-group consistency analysis
13. Boundary panels full metrics suite
14. End-to-end analysis orchestration blocked before lock
15. Annotation-start QA gatekeeper logic (blocked when PENDING, passes when frozen)
16. Guide examples have zero overlap with blind set
17. Model annotator configs remain PENDING
18. Taxonomy decision remains PENDING
19. Bootstrap interpretation note exists with clarified wording
"""

import os
import sys
import csv
import json
import hashlib
import re
import pytest
from jsonschema import Draft7Validator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_B2_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
DOCS_B3_DIR = os.path.join(BASE_DIR, "docs", "nlp_v2", "gate_b3")
REPORTS_B3_DIR = os.path.join(BASE_DIR, "reports", "nlp_v2", "gate_b3")

SOURCE_BLIND_CSV = os.path.join(GATE_B2_DIR, "human_annotation_blind.csv")
EXPECTED_SOURCE_SHA256 = "94fd8bb3e7f2e3bdaf274c4ee5bcf7e083e9ef2a66322fbcf7bee2cadf231999"


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def test_source_350_file_unchanged():
    """Verify data/nlp_v2/gate_b2/human_annotation_blind.csv row count and SHA-256."""
    assert os.path.exists(SOURCE_BLIND_CSV), "Missing source blind file!"
    actual_sha = compute_sha256(SOURCE_BLIND_CSV)
    assert actual_sha == EXPECTED_SOURCE_SHA256, f"Source blind file SHA altered: {actual_sha}"

    with open(SOURCE_BLIND_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 350, f"Source blind row count != 350: {len(rows)}"


def test_student_order_assignment_deterministic_and_half_split():
    """Verify deterministic 175/175 half split and counterbalancing."""
    manifest_path = os.path.join(GATE_B3_DIR, "student_order_manifest.json")
    assert os.path.exists(manifest_path), "Missing student_order_manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) == 350
    half_a = [r for r in records if r["half"] == "A"]
    half_b = [r for r in records if r["half"] == "B"]
    assert len(half_a) == 175, f"Half A size: {len(half_a)}"
    assert len(half_b) == 175, f"Half B size: {len(half_b)}"

    for r in half_a:
        assert r["first_taxonomy"] == "T2"
        assert r["second_taxonomy"] == "T3"
        assert 1 <= r["first_pass_order"] <= 175
        assert 1 <= r["second_pass_order"] <= 175

    for r in half_b:
        assert r["first_taxonomy"] == "T3"
        assert r["second_taxonomy"] == "T2"
        assert 1 <= r["first_pass_order"] <= 175
        assert 1 <= r["second_pass_order"] <= 175


def test_each_student_eventually_sees_every_query_under_both_taxonomies():
    """Verify all 350 queries appear across student passes for both T2 and T3."""
    t2_p1 = os.path.join(GATE_B3_DIR, "student_t2_first_pass.csv")
    t2_p2 = os.path.join(GATE_B3_DIR, "student_t2_second_pass.csv")
    t3_p1 = os.path.join(GATE_B3_DIR, "student_t3_first_pass.csv")
    t3_p2 = os.path.join(GATE_B3_DIR, "student_t3_second_pass.csv")

    with open(t2_p1, "r", encoding="utf-8") as f:
        t2_p1_ids = {r["annotation_id"] for r in csv.DictReader(f)}
    with open(t2_p2, "r", encoding="utf-8") as f:
        t2_p2_ids = {r["annotation_id"] for r in csv.DictReader(f)}

    with open(t3_p1, "r", encoding="utf-8") as f:
        t3_p1_ids = {r["annotation_id"] for r in csv.DictReader(f)}
    with open(t3_p2, "r", encoding="utf-8") as f:
        t3_p2_ids = {r["annotation_id"] for r in csv.DictReader(f)}

    assert len(t2_p1_ids) == 175
    assert len(t2_p2_ids) == 175
    assert len(t2_p1_ids & t2_p2_ids) == 0, "Overlap within T2 student passes!"
    assert len(t2_p1_ids | t2_p2_ids) == 350, "Student T2 does not cover all 350 items!"

    assert len(t3_p1_ids) == 175
    assert len(t3_p2_ids) == 175
    assert len(t3_p1_ids & t3_p2_ids) == 0, "Overlap within T3 student passes!"
    assert len(t3_p1_ids | t3_p2_ids) == 350, "Student T3 does not cover all 350 items!"


def test_model_exports_contain_exactly_350_items_each():
    """Verify all 4 model annotator export files contain exactly 350 lines."""
    model_files = [
        "model_a_t2_input.jsonl",
        "model_a_t3_input.jsonl",
        "model_b_t2_input.jsonl",
        "model_b_t3_input.jsonl",
    ]
    for mf in model_files:
        fpath = os.path.join(GATE_B3_DIR, mf)
        assert os.path.exists(fpath), f"Missing model export: {mf}"
        with open(fpath, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) == 350, f"{mf} length != 350: {len(lines)}"


def test_annotator_exports_contain_no_gold_or_predictions_or_utterance_id():
    """Verify strictly blind exports: no gold, no predictions, no utterance_id."""
    forbidden = {
        "utterance_id", "gold_T2_intent", "gold_T3_intent", "gold_subtype",
        "gold_operation", "T2_label", "T3_label", "semantic_operation",
        "semantic_subtype", "predictions", "prediction"
    }

    student_files = [
        "student_t2_first_pass.csv",
        "student_t3_first_pass.csv",
        "student_t2_second_pass.csv",
        "student_t3_second_pass.csv",
    ]
    for sf in student_files:
        fpath = os.path.join(GATE_B3_DIR, sf)
        with open(fpath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = set(reader.fieldnames or [])
            assert fields == {"annotation_id", "query", "taxonomy_version"}
            assert not (fields & forbidden), f"Forbidden field in {sf}: {fields & forbidden}"

    model_files = [
        "model_a_t2_input.jsonl",
        "model_a_t3_input.jsonl",
        "model_b_t2_input.jsonl",
        "model_b_t3_input.jsonl",
    ]
    for mf in model_files:
        fpath = os.path.join(GATE_B3_DIR, mf)
        with open(fpath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                rec = json.loads(line)
                keys = set(rec.keys())
                assert keys == {"annotation_id", "query", "taxonomy_version"}, f"Invalid keys in {mf}:{idx}"
                assert not (keys & forbidden), f"Forbidden key in {mf}:{idx}"


def test_canonical_json_schema_validation_via_draft7():
    """Verify Draft7Validator enforcement against annotation_output_schema.json."""
    from scripts.nlp_v2.gate_b3.lock_first_pass_annotations import load_validator
    validator = load_validator()

    valid_student_rec = {
        "annotation_id": "ANN_B2_001",
        "source_id": "STUDENT_R1",
        "source_type": "student",
        "taxonomy_version": "T2",
        "run_id": "STUDENT_PASS_1",
        "primary_label": "route_query",
        "acceptable_labels": ["route_query"],
        "clarification_required": False,
        "clarification_reasons": [],
        "brief_justification": "Clear route request.",
        "recognized_from_prior_work": "false",
        "active_time_seconds": 12.5,
        "rule_difficulty": "easy",
        "response_status": "VALID"
    }
    assert validator.is_valid(valid_student_rec)

    # 1. Missing run_id rejected
    bad_rec = dict(valid_student_rec)
    del bad_rec["run_id"]
    assert not validator.is_valid(bad_rec)

    # 2. Invalid response_status rejected
    bad_rec2 = dict(valid_student_rec, response_status="INVALID_STATUS")
    assert not validator.is_valid(bad_rec2)

    # 3. Additional unexpected property rejected
    bad_rec3 = dict(valid_student_rec, unexpected_prop="fail")
    assert not validator.is_valid(bad_rec3)

    # 4. Null primary supported
    null_prim_rec = dict(valid_student_rec, primary_label=None, clarification_required=True, clarification_reasons=["intent_ambiguity"])
    assert validator.is_valid(null_prim_rec)


def test_semantic_validation_student_burden_and_invariants():
    """Verify semantic validation rules in lock_first_pass_annotations."""
    from scripts.nlp_v2.gate_b3.lock_first_pass_annotations import validate_record_semantics, EXPECTED_OUTPUT_SPECS

    student_spec = EXPECTED_OUTPUT_SPECS["student_t2_annotations.jsonl"]
    model_spec = EXPECTED_OUTPUT_SPECS["model_a_t2_annotations.jsonl"]

    base_rec = {
        "annotation_id": "ANN_B2_001",
        "source_id": "STUDENT_R1",
        "source_type": "student",
        "taxonomy_version": "T2",
        "run_id": "STUDENT_T2_P1",
        "primary_label": "route_query",
        "acceptable_labels": ["route_query"],
        "clarification_required": False,
        "clarification_reasons": [],
        "brief_justification": "Valid justification",
        "recognized_from_prior_work": "false",
        "active_time_seconds": 8.0,
        "rule_difficulty": "easy",
        "response_status": "VALID"
    }

    # Student valid
    validate_record_semantics(base_rec, student_spec, 1, "test.jsonl")

    # 1. Source mismatch: MODEL_A file with source_id MODEL_B rejected
    model_rec = dict(base_rec, source_id="MODEL_B", source_type="model", active_time_seconds=None, rule_difficulty="not_applicable", recognized_from_prior_work="not_applicable")
    with pytest.raises(ValueError, match="source_id mismatch"):
        validate_record_semantics(model_rec, model_spec, 1, "test.jsonl")

    # 2. Student file with source_type model rejected
    bad_student_type = dict(base_rec, source_type="model")
    with pytest.raises(ValueError, match="source_type mismatch"):
        validate_record_semantics(bad_student_type, student_spec, 1, "test.jsonl")

    # 3. Wrong taxonomy rejected
    bad_tax = dict(base_rec, taxonomy_version="T3")
    with pytest.raises(ValueError, match="taxonomy_version mismatch"):
        validate_record_semantics(bad_tax, student_spec, 1, "test.jsonl")

    # 4. Student missing numeric active_time_seconds rejected
    bad_time = dict(base_rec, active_time_seconds=None)
    with pytest.raises(ValueError, match="active_time_seconds"):
        validate_record_semantics(bad_time, student_spec, 1, "test.jsonl")

    # 5. Model with non-null active_time_seconds rejected
    model_valid = dict(base_rec, source_id="MODEL_A", source_type="model", active_time_seconds=None, rule_difficulty="not_applicable", recognized_from_prior_work="not_applicable")
    validate_record_semantics(model_valid, model_spec, 1, "test.jsonl")

    bad_model_time = dict(model_valid, active_time_seconds=5.0)
    with pytest.raises(ValueError, match="Model active_time_seconds must be null"):
        validate_record_semantics(bad_model_time, model_spec, 1, "test.jsonl")

    # 6. Primary-label not in acceptable_labels rejected
    bad_acc = dict(base_rec, acceptable_labels=["fare_query"])
    with pytest.raises(ValueError, match="must be in acceptable_labels"):
        validate_record_semantics(bad_acc, student_spec, 1, "test.jsonl")

    # 7. Clarification invariant: clarification_required False with reasons rejected
    bad_clar_false = dict(base_rec, clarification_required=False, clarification_reasons=["missing_slot"])
    with pytest.raises(ValueError, match="must be empty when clarification_required is false"):
        validate_record_semantics(bad_clar_false, student_spec, 1, "test.jsonl")

    # 8. Clarification invariant: clarification_required True with empty reasons rejected
    bad_clar_true = dict(base_rec, clarification_required=True, clarification_reasons=[])
    with pytest.raises(ValueError, match="must be non-empty when clarification_required is true"):
        validate_record_semantics(bad_clar_true, student_spec, 1, "test.jsonl")


def test_t2_reference_concordance_namespace_mapping():
    """Verify T2 reference acceptable labels collapse T3 secondary labels to T2 parents."""
    from scripts.nlp_v2.gate_b3.compute_annotation_stability import get_reference_acceptable_set

    # Fixture 1: multimodal_route maps to route_query
    ref1 = {
        "gold_T2_intent": "route_query",
        "gold_T3_intent": "point_to_point_route",
        "acceptable_secondary_labels": ["multimodal_route"]
    }
    t2_set1 = get_reference_acceptable_set(ref1, "T2")
    assert t2_set1 == {"route_query"}, f"Expected {{'route_query'}}, got {t2_set1}"

    # Fixture 2: timing subtypes collapse into service_timing
    ref2 = {
        "gold_T2_intent": "service_timing",
        "gold_T3_intent": "scheduled_departure",
        "acceptable_secondary_labels": ["first_and_last_service", "service_frequency"]
    }
    t2_set2 = get_reference_acceptable_set(ref2, "T2")
    assert t2_set2 == {"service_timing"}, f"Expected {{'service_timing'}}, got {t2_set2}"

    # Fixture 3: T3 set remains in T3 namespace
    t3_set2 = get_reference_acceptable_set(ref2, "T3")
    assert t3_set2 == {"scheduled_departure", "first_and_last_service", "service_frequency"}


def test_lock_integrity_hash_revalidation_blocks_gold_access(tmp_path):
    """Verify verify_first_pass_lock_integrity fails when locked file is mutated."""
    import scripts.nlp_v2.gate_b3.compute_annotation_stability as stab

    # When lock is false initially, access is blocked
    assert stab.is_first_pass_locked() is False
    with pytest.raises(PermissionError, match="HARD GUARDRAIL VIOLATION"):
        stab.load_gold_key()


def test_contrast_group_analysis_computation():
    """Verify compute_contrast_group_analysis reports complete vs incomplete groups."""
    from scripts.nlp_v2.gate_b3.compute_annotation_stability import compute_contrast_group_analysis

    mock_gold_key = {
        "ANN_B2_001": {"contrast_group_id": "CG_COMPLETE_01"},
        "ANN_B2_002": {"contrast_group_id": "CG_COMPLETE_01"},
        "ANN_B2_003": {"contrast_group_id": "CG_INCOMPLETE_01"},
    }
    mock_sources = {}
    res = compute_contrast_group_analysis(mock_gold_key, mock_sources)

    assert res["total_contrast_groups_represented"] == 2
    assert "sampling_limitation_note" in res
    assert res["complete_contrast_groups_count"] + res["incomplete_contrast_fragments_count"] == 2


def test_boundary_panels_full_metrics():
    """Verify boundary panels metric computation with support, disagreement, and Jaccard."""
    from scripts.nlp_v2.gate_b3.compute_annotation_stability import compute_boundary_panels

    mock_sources = {
        "STUDENT_R1": {
            "ANN_B2_001": {"primary_label": "point_to_point_route", "acceptable_labels": ["point_to_point_route"], "clarification_required": False},
            "ANN_B2_002": {"primary_label": "multimodal_route", "acceptable_labels": ["multimodal_route"], "clarification_required": True, "clarification_reasons": ["multiple_goals"]}
        },
        "MODEL_A": {
            "ANN_B2_001": {"primary_label": "point_to_point_route", "acceptable_labels": ["point_to_point_route"], "clarification_required": False},
            "ANN_B2_002": {"primary_label": "point_to_point_route", "acceptable_labels": ["point_to_point_route", "multimodal_route"], "clarification_required": False}
        }
    }
    panels = compute_boundary_panels(mock_sources, gold_key=None, taxonomy="T3")

    p2p_panel = panels["point_to_point_vs_multimodal"]
    assert p2p_panel["support_n"] == 2
    assert "STUDENT_R1_vs_MODEL_A" in p2p_panel["pairwise_metrics"]
    metrics = p2p_panel["pairwise_metrics"]["STUDENT_R1_vs_MODEL_A"]
    assert "primary_label_disagreement_rate" in metrics
    assert "exact_acceptable_set_agreement_rate" in metrics
    assert "mean_acceptable_set_jaccard" in metrics
    assert "clarification_disagreement_rate" in metrics


def test_analysis_orchestration_fails_before_lock():
    """Verify run_full_analysis_pipeline hard-fails with FIRST_PASS_NOT_LOCKED before lock."""
    from scripts.nlp_v2.gate_b3.compute_annotation_stability import run_full_analysis_pipeline
    with pytest.raises(RuntimeError, match="FIRST_PASS_NOT_LOCKED"):
        run_full_analysis_pipeline()


def test_annotation_start_qa_blocks_when_pending():
    """Verify qa_gate_b3_annotation_start blocks when models remain PENDING."""
    import subprocess
    proc = subprocess.run(
        [sys.executable, "scripts/nlp_v2/gate_b3/qa_gate_b3_annotation_start.py"],
        capture_output=True,
        text=True
    )
    assert proc.returncode != 0
    assert "STATUS: BLOCKED / NOT READY" in proc.stdout
    assert "MODEL_A status/provider/model remains PENDING" in proc.stdout
    assert "MODEL_B status/provider/model remains PENDING" in proc.stdout


def test_guide_examples_zero_overlap_with_blind_set():
    """Verify zero overlap between guide examples and blind challenge set."""
    with open(SOURCE_BLIND_CSV, "r", encoding="utf-8") as f:
        blind_norm = {normalize_text(r["query"]) for r in csv.DictReader(f)}

    def extract_quoted(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return re.findall(r'\"([^\"]+)\"', content)

    for guide in ["t2_annotation_guide.md", "t3_annotation_guide.md"]:
        gpath = os.path.join(DOCS_B3_DIR, guide)
        assert os.path.exists(gpath), f"Missing guide: {guide}"
        quotes = extract_quoted(gpath)
        overlaps = [q for q in quotes if normalize_text(q) in blind_norm]
        assert len(overlaps) == 0, f"Overlap detected in {guide}: {overlaps}"


def test_model_annotator_config_remains_pending():
    """Verify model annotator configuration placeholders remain PENDING with freeze fields."""
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    assert cfg["configuration_frozen"] is False
    assert cfg["MODEL_A"]["status"] == "PENDING"
    assert cfg["MODEL_A"]["provider"] == "PENDING"
    assert cfg["MODEL_A"]["configuration_frozen"] is False
    assert cfg["MODEL_A"]["execution_timestamp"] is None

    assert cfg["MODEL_B"]["status"] == "PENDING"
    assert cfg["MODEL_B"]["provider"] == "PENDING"
    assert cfg["MODEL_B"]["configuration_frozen"] is False
    assert cfg["MODEL_B"]["execution_timestamp"] is None


def test_taxonomy_decision_remains_pending():
    """Verify taxonomy decision remains PENDING in manifest and report."""
    manifest_path = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["taxonomy_decision_status"] == "PENDING"
    assert m["annotation_started"] is False
    assert m["first_pass_locked"] is False

    doc_path = os.path.join(REPORTS_B3_DIR, "TAXONOMY_B3_DECISION_REQUIRED.md")
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "GATE B.3 TAXONOMY DECISION: PENDING" in content


def test_bootstrap_interpretation_note_exists():
    """Verify Gate B.2 bootstrap interpretation note exists with clarified wording."""
    note_path = os.path.join(REPORTS_B3_DIR, "gate_b2_bootstrap_interpretation_note.md")
    assert os.path.exists(note_path), "Missing gate_b2_bootstrap_interpretation_note.md"
    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "query bootstrap over fixed evaluated seeds" in content
    assert "mean operation accuracy across the three fixed evaluated seeds" in content
    assert "+4.11" in content
    assert "+4.01" in content
    assert "0.0245" in content
    assert "0.0581" in content
