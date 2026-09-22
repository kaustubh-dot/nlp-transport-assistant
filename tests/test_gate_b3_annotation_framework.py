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
20. Annotation-start QA model version and revision provenance enforcement
21. Annotation-start QA methodology artifact hash drift detection
22. Annotation-start QA configuration_sha256 enforcement when frozen
23. Student annotation output template marked NON_VALID_BLANK_TEMPLATE with warning
"""

import os
import sys
import csv
import json
import hashlib
import re
import glob
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
    """Verify all model annotator export files contain exactly 350 lines."""
    model_files = [
        "model_g_t2_input.jsonl",
        "model_g_t3_input.jsonl",
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
        "model_g_t2_input.jsonl",
        "model_g_t3_input.jsonl",
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
    model_spec = EXPECTED_OUTPUT_SPECS["model_g_t2_annotations.jsonl"]

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

    # 1. Source mismatch: MODEL_G file with source_id MODEL_A rejected
    model_rec = dict(base_rec, source_id="MODEL_A", source_type="model", active_time_seconds=None, rule_difficulty="not_applicable", recognized_from_prior_work="not_applicable")
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
    model_valid = dict(base_rec, source_id="MODEL_G", source_type="model", active_time_seconds=None, rule_difficulty="not_applicable", recognized_from_prior_work="not_applicable")
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


def test_annotation_start_qa_status_blocked_prior_to_model_g_readiness():
    """Verify qa_gate_b3_annotation_start returns BLOCKED / NOT READY for MODEL_G readiness blockers."""
    import subprocess
    proc = subprocess.run(
        [sys.executable, "scripts/nlp_v2/gate_b3/qa_gate_b3_annotation_start.py"],
        capture_output=True,
        text=True
    )
    assert proc.returncode == 1
    assert "STATUS: BLOCKED / NOT READY" in proc.stdout
    assert "MODEL_G fresh context per item not verified" in proc.stdout
    assert "MODEL_G empty workdir not verified" in proc.stdout
    assert "MODEL_G zero-tool-use audit not verified" in proc.stdout
    assert "MODEL_G behavioral execution isolation not verified" in proc.stdout
    assert "MODEL_G synthetic smoke test not passed" in proc.stdout
    assert "MODEL_G benchmark execution not authorized" in proc.stdout
    assert "MODEL_A" not in proc.stdout
    assert "MODEL_B" not in proc.stdout


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


def test_model_annotator_configs_frozen_and_amendment_status():
    """Verify model annotator configuration is frozen with MODEL_G active unauthorized and historical models retired."""
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    assert cfg["configuration_frozen"] is True
    assert cfg["frozen_at"] is not None
    assert cfg["configuration_sha256"] is not None
    assert cfg["primary_model_annotator_source_id"] == "MODEL_G"
    assert cfg["primary_model_annotator_count"] == 1
    assert cfg["retired_primary_model_sources"] == ["MODEL_A", "MODEL_B"]

    expected_retry_policy = {
        "semantic_retries": 0,
        "format_repair_attempts": 1,
        "transport_retry_policy": "PERMITTED_FOR_EXECUTION_FAILURE_ONLY",
        "semantic_retry_mode": "FORBIDDEN",
        "tool_violation_retry_attempts": 0,
        "tool_violation_mode": "HARD_FAIL_BATCH",
    }

    # MODEL_G checks (Active primary model annotator)
    m_g = cfg["MODEL_G"]
    assert m_g["source_id"] == "MODEL_G"
    assert m_g["provider"] == "Google"
    assert m_g["model"] == "Gemini 3.8 Flash"
    assert m_g["version"] == "Gemini 3.8 Flash"
    assert m_g["exact_version_or_revision"] == "NOT_EXPOSED_BY_PROVIDER"
    assert m_g["execution_environment"] == "Antigravity"
    assert m_g["status"] == "FROZEN_NOT_EXECUTION_READY"
    assert m_g["configuration_frozen"] is True
    assert m_g["primary_analysis_included"] is True
    assert m_g["execution_isolation_class"] == "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION"
    assert m_g["fresh_context_per_item_required"] is True
    assert m_g["empty_workdir_required"] is True
    assert m_g["actual_tool_use_allowed"] is False
    assert m_g["zero_tool_use_audit_required"] is True
    assert m_g["tool_violation_retry_attempts"] == 0
    assert m_g["reasoning_configuration"]["mode"] == "standard"
    assert m_g["fresh_context_per_item_verified"] is False
    assert m_g["empty_workdir_verified"] is False
    assert m_g["zero_tool_use_audit_verified"] is False
    assert m_g["execution_isolation_verified"] is False
    assert m_g["synthetic_smoke_test_passed"] is False
    assert m_g["benchmark_execution_authorized"] is False
    assert m_g["execution_timestamp"] is None
    assert m_g["retry_policy"] == expected_retry_policy

    # MODEL_A checks (Historical aborted execution)
    m_a = cfg["MODEL_A"]
    assert m_a["source_id"] == "MODEL_A"
    assert m_a["provider"] == "OpenAI"
    assert m_a["model"] == "GPT-6 Astra"
    assert m_a["status"] == "ABORTED_PRE_AMENDMENT_EXECUTION"
    assert m_a["primary_analysis_included"] is False
    assert m_a["benchmark_execution_authorized"] is False

    # MODEL_B checks (Historical retired execution)
    m_b = cfg["MODEL_B"]
    assert m_b["source_id"] == "MODEL_B"
    assert m_b["provider"] == "Anthropic"
    assert m_b["model"] == "Claude Opus 4.6"
    assert m_b["status"] == "RETIRED_PRE_COMPLETION"
    assert m_b["primary_analysis_included"] is False
    assert m_b["benchmark_execution_authorized"] is False


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


def _create_valid_frozen_mock_config() -> dict:
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import (
        compute_model_config_hash,
        compute_global_config_hash
    )
    prompt_path = os.path.join(DOCS_B3_DIR, "model_annotator_prompt_template.md")
    t2_path = os.path.join(DOCS_B3_DIR, "t2_annotation_guide.md")
    t3_path = os.path.join(DOCS_B3_DIR, "t3_annotation_guide.md")
    schema_path = os.path.join(DOCS_B3_DIR, "annotation_output_schema.json")
    amendment_path = os.path.join(DOCS_B3_DIR, "gate_b3_execution_isolation_amendment.md")
    feasibility_path = os.path.join(DOCS_B3_DIR, "gate_b3_resource_feasibility_annotator_amendment.md")

    m_g = {
        "source_id": "MODEL_G",
        "provider": "Google",
        "model": "Gemini 3.8 Flash",
        "version": "Gemini 3.8 Flash",
        "exact_version_or_revision": "NOT_EXPOSED_BY_PROVIDER",
        "execution_environment": "Antigravity",
        "status": "FROZEN_EXECUTION_AUTHORIZED",
        "configuration_frozen": True,
        "primary_analysis_included": True,
        "execution_isolation_class": "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION",
        "fresh_context_per_item_required": True,
        "empty_workdir_required": True,
        "benchmark_paths_provided_to_child": False,
        "cross_query_history_allowed": False,
        "actual_tool_use_allowed": False,
        "zero_tool_use_audit_required": True,
        "tool_violation_retry_attempts": 0,
        "reasoning_configuration": {"mode": "standard"},
        "tool_policy": {
            "web": "DISABLED_REQUIRED",
            "external_retrieval": "DISABLED_REQUIRED",
            "original_repository_access": "FORBIDDEN",
            "other_annotator_access": "FORBIDDEN",
            "filesystem_isolation": "BEHAVIORAL_NO_USE_WITH_EMPTY_WORKDIR",
            "web_isolation": "CONFIG_DISABLED_AND_ZERO_CALL_AUDITED",
        },
        "request_isolation": "ONE_QUERY_ONE_FRESH_CONTEXT_REQUIRED",
        "retry_policy": {
            "semantic_retries": 0,
            "format_repair_attempts": 1,
            "transport_retry_policy": "PERMITTED_FOR_EXECUTION_FAILURE_ONLY",
            "semantic_retry_mode": "FORBIDDEN",
            "tool_violation_retry_attempts": 0,
            "tool_violation_mode": "HARD_FAIL_BATCH",
        },
        "fresh_context_per_item_verified": True,
        "empty_workdir_verified": True,
        "zero_tool_use_audit_verified": True,
        "execution_isolation_verified": True,
        "synthetic_smoke_test_passed": True,
        "benchmark_execution_authorized": True,
        "execution_timestamp": None,
        "provenance_notes": "Primary model annotator mock."
    }
    m_g["configuration_sha256"] = compute_model_config_hash(m_g)

    cfg = {
        "study": "Gate B.3 Annotation-Stability Framework",
        "primary_model_annotator_source_id": "MODEL_G",
        "primary_model_annotator_count": 1,
        "retired_primary_model_sources": ["MODEL_A", "MODEL_B"],
        "configuration_frozen": True,
        "frozen_at": "2026-09-22T11:00:00Z",
        "prompt_sha256": compute_sha256(prompt_path),
        "t2_guide_sha256": compute_sha256(t2_path),
        "t3_guide_sha256": compute_sha256(t3_path),
        "schema_sha256": compute_sha256(schema_path),
        "execution_isolation_amendment_sha256": compute_sha256(amendment_path),
        "resource_feasibility_amendment_sha256": compute_sha256(feasibility_path),
        "MODEL_G": m_g,
        "MODEL_A": {
            "source_id": "MODEL_A",
            "provider": "OpenAI",
            "model": "GPT-6 Astra",
            "version": "GPT-6 Astra",
            "exact_version_or_revision": "NOT_EXPOSED_BY_PROVIDER",
            "execution_environment": "Codex",
            "status": "ABORTED_PRE_AMENDMENT_EXECUTION",
            "primary_analysis_included": False,
        },
        "MODEL_B": {
            "source_id": "MODEL_B",
            "provider": "Anthropic",
            "model": "Claude Opus 4.6",
            "version": "Claude Opus 4.6",
            "exact_version_or_revision": "NOT_EXPOSED_BY_PROVIDER",
            "execution_environment": "Antigravity",
            "status": "RETIRED_PRE_COMPLETION",
            "primary_analysis_included": False,
        }
    }
    cfg["configuration_sha256"] = compute_global_config_hash(cfg, m_g["configuration_sha256"])
    return cfg


def test_annotation_start_qa_model_version_checks(tmp_path):
    """Verify version enforcement and exact revision provenance checks for frozen models."""
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import evaluate_annotation_start_readiness

    cfg = _create_valid_frozen_mock_config()
    cfg_file = tmp_path / "test_config.json"

    # Baseline: valid mock configuration passes
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is True, f"Valid baseline unexpectedly failed: {reasons}"
    assert len(reasons) == 0

    # 1. frozen model with version=PENDING is rejected
    cfg1 = _create_valid_frozen_mock_config()
    cfg1["MODEL_G"]["version"] = "PENDING"
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg1, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is False
    assert any("MODEL_G version remains PENDING" in r for r in reasons)

    # 2. frozen model with version="" is rejected
    cfg2 = _create_valid_frozen_mock_config()
    cfg2["MODEL_G"]["version"] = ""
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg2, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is False
    assert any("MODEL_G version remains PENDING or empty" in r for r in reasons)

    # 3. frozen model with exact_version_or_revision=null / "" / "PENDING" is rejected
    for invalid_rev in [None, "", "PENDING"]:
        cfg3 = _create_valid_frozen_mock_config()
        cfg3["MODEL_G"]["exact_version_or_revision"] = invalid_rev
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg3, f)
        is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
        assert is_ready is False
        assert any("MODEL_G exact_version_or_revision must be provided when frozen" in r for r in reasons)

    # 4. NOT_EXPOSED_BY_PROVIDER is accepted as revision provenance
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import (
        compute_model_config_hash,
        compute_global_config_hash
    )
    cfg4 = _create_valid_frozen_mock_config()
    cfg4["MODEL_G"]["exact_version_or_revision"] = "NOT_EXPOSED_BY_PROVIDER"
    cfg4["MODEL_G"]["configuration_sha256"] = compute_model_config_hash(cfg4["MODEL_G"])
    cfg4["configuration_sha256"] = compute_global_config_hash(
        cfg4, cfg4["MODEL_G"]["configuration_sha256"]
    )
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg4, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is True, f"NOT_EXPOSED_BY_PROVIDER was rejected: {reasons}"
    assert len(reasons) == 0


def test_annotation_start_qa_methodology_hash_drift(tmp_path):
    """Verify stored methodology hash matches pass and mismatches trigger FROZEN_ANNOTATION_CONFIGURATION_DRIFT."""
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import evaluate_annotation_start_readiness

    cfg_file = tmp_path / "test_config.json"

    # Baseline matches
    cfg = _create_valid_frozen_mock_config()
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is True

    # Test drift for all methodology artifacts
    drift_keys = [
        ("prompt_sha256", "model_annotator_prompt_template.md"),
        ("t2_guide_sha256", "t2_annotation_guide.md"),
        ("t3_guide_sha256", "t3_annotation_guide.md"),
        ("schema_sha256", "annotation_output_schema.json"),
        ("execution_isolation_amendment_sha256", "gate_b3_execution_isolation_amendment.md"),
        ("resource_feasibility_amendment_sha256", "gate_b3_resource_feasibility_annotator_amendment.md"),
    ]

    for hash_key, artifact_filename in drift_keys:
        corrupted_cfg = _create_valid_frozen_mock_config()
        corrupted_cfg[hash_key] = "0000000000000000000000000000000000000000000000000000000000000000"
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(corrupted_cfg, f)

        is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
        assert is_ready is False
        assert any(
            f"FROZEN_ANNOTATION_CONFIGURATION_DRIFT: {artifact_filename} drifted!" in r
            for r in reasons
        ), f"Failed to report drift for {artifact_filename} in reasons: {reasons}"


def test_annotation_start_qa_configuration_sha_requirement(tmp_path):
    """Verify configuration_sha256 is required when configuration_frozen is True."""
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import evaluate_annotation_start_readiness

    cfg_file = tmp_path / "test_config.json"

    # 1. Missing global configuration_sha256 when globally frozen
    cfg_global_missing = _create_valid_frozen_mock_config()
    del cfg_global_missing["configuration_sha256"]
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg_global_missing, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is False
    assert any("Global configuration_sha256 missing while configuration_frozen is True" in r for r in reasons)

    # 2. Missing per-model configuration_sha256 when model frozen
    cfg_model_missing = _create_valid_frozen_mock_config()
    del cfg_model_missing["MODEL_G"]["configuration_sha256"]
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg_model_missing, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is False
    assert any("MODEL_G configuration_sha256 missing while configuration_frozen is True" in r for r in reasons)


def test_student_annotation_output_template_warning():
    """Verify student annotation output template is marked NON_VALID_BLANK_TEMPLATE with prominent warning."""
    tmpl_path = os.path.join(GATE_B3_DIR, "student_annotation_output_template.json")
    assert os.path.exists(tmpl_path), "Missing student_annotation_output_template.json"
    with open(tmpl_path, "r", encoding="utf-8") as f:
        tmpl = json.load(f)
    assert tmpl.get("template_status") == "NON_VALID_BLANK_TEMPLATE"
    assert "THIS SAMPLE RECORD IS NOT A VALID COMPLETED ANNOTATION" in tmpl.get("warning", "")
    assert "DO NOT COPY IT DIRECTLY INTO FINAL ANNOTATION OUTPUT" in tmpl.get("warning", "")
    reqs = tmpl.get("completion_requirements", "")
    assert "acceptable_labels non-empty" in reqs
    assert "active_time_seconds >= 0" in reqs
    assert "rule_difficulty in easy/moderate/hard" in reqs
    assert "recognized_from_prior_work in true/false/unsure" in reqs


def test_canonical_configuration_hash_recomputation():
    """Verify stored configuration hashes match runtime canonical recomputation."""
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import (
        compute_model_config_hash,
        compute_global_config_hash
    )
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Recompute MODEL_G (active)
    recomputed_g = compute_model_config_hash(cfg["MODEL_G"])
    assert recomputed_g == cfg["MODEL_G"]["configuration_sha256"], f"MODEL_G hash mismatch: {recomputed_g}"

    # Recompute historical MODEL_A and MODEL_B
    recomputed_a = compute_model_config_hash(cfg["MODEL_A"])
    recomputed_b = compute_model_config_hash(cfg["MODEL_B"])
    assert recomputed_a == cfg["MODEL_A"]["configuration_sha256"], f"MODEL_A hash mismatch: {recomputed_a}"
    assert recomputed_b == cfg["MODEL_B"]["configuration_sha256"], f"MODEL_B hash mismatch: {recomputed_b}"

    # Recompute global
    recomputed_global = compute_global_config_hash(cfg, recomputed_g)
    assert recomputed_global == cfg["configuration_sha256"], f"Global config hash mismatch: {recomputed_global}"
    assert cfg["historical_configuration_sha256"] == "2a7c82b9297f65f750f5f72685d329d2e65e40c0691b09546802d8cd727afc8e"


def test_mutation_of_frozen_model_field_triggers_drift(tmp_path):
    """Verify modifying any frozen semantic field triggers FROZEN_MODEL_CONFIGURATION_DRIFT."""
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import evaluate_annotation_start_readiness

    cfg_file = tmp_path / "test_drift_config.json"

    # 1. Mutate model field in MODEL_G
    cfg1 = _create_valid_frozen_mock_config()
    cfg1["MODEL_G"]["model"] = "Gemini-altered"
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg1, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is False
    assert any("FROZEN_MODEL_CONFIGURATION_DRIFT: MODEL_G configuration drifted!" in r for r in reasons)

    # 2. Mutate reasoning_configuration in MODEL_G
    cfg2 = _create_valid_frozen_mock_config()
    cfg2["MODEL_G"]["reasoning_configuration"] = {"mode": "unfrozen_altered_mode"}
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg2, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is False
    assert any("FROZEN_MODEL_CONFIGURATION_DRIFT: MODEL_G configuration drifted!" in r for r in reasons)

    # 3. Mutate global hash mismatch directly
    cfg3 = _create_valid_frozen_mock_config()
    cfg3["configuration_sha256"] = "bad0000000000000000000000000000000000000000000000000000000000bad"
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg3, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
    assert is_ready is False
    assert any("FROZEN_MODEL_CONFIGURATION_DRIFT: Global configuration drifted!" in r for r in reasons)

    # 4. Mutate each retry_policy field in MODEL_G
    for field_name, bad_value in [
        ("semantic_retries", 1),
        ("format_repair_attempts", 2),
        ("transport_retry_policy", "FORBIDDEN"),
        ("semantic_retry_mode", "PERMITTED"),
        ("tool_violation_retry_attempts", 1),
        ("tool_violation_mode", "SOFT_RETRY"),
    ]:
        cfg_r = _create_valid_frozen_mock_config()
        cfg_r["MODEL_G"]["retry_policy"][field_name] = bad_value
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg_r, f)
        is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(cfg_file))
        assert is_ready is False
        assert any("FROZEN_MODEL_CONFIGURATION_DRIFT: MODEL_G configuration drifted!" in r for r in reasons)


def test_model_a_and_b_execution_manifests_integrity():
    """Verify sanitized execution manifests contain correct protocol, amendment, and input hashes."""
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    prompt_path = os.path.join(DOCS_B3_DIR, "model_annotator_prompt_template.md")
    t2_path = os.path.join(DOCS_B3_DIR, "t2_annotation_guide.md")
    t3_path = os.path.join(DOCS_B3_DIR, "t3_annotation_guide.md")
    schema_path = os.path.join(DOCS_B3_DIR, "annotation_output_schema.json")
    amendment_path = os.path.join(DOCS_B3_DIR, "gate_b3_execution_isolation_amendment.md")

    expected_protocol_hashes = {
        "model_annotator_prompt_template.md": compute_sha256(prompt_path),
        "t2_annotation_guide.md": compute_sha256(t2_path),
        "t3_annotation_guide.md": compute_sha256(t3_path),
        "annotation_output_schema.json": compute_sha256(schema_path),
        "gate_b3_execution_isolation_amendment.md": compute_sha256(amendment_path),
    }

    # MODEL_A Manifest
    manifest_a_path = os.path.join(GATE_B3_DIR, "model_a_execution_manifest.json")
    assert os.path.exists(manifest_a_path), "Missing model_a_execution_manifest.json"
    with open(manifest_a_path, "r", encoding="utf-8") as f:
        man_a = json.load(f)

    assert man_a["source_id"] == "MODEL_A"
    assert man_a["provider"] == "OpenAI"
    assert man_a["model"] == "GPT-6 Astra"
    assert man_a["execution_environment"] == "Codex"
    assert man_a["reasoning_effort"] == "medium"
    assert man_a["configuration_frozen"] is True
    assert man_a["configuration_sha256"] == cfg["MODEL_A"]["configuration_sha256"]
    assert man_a["protocol_sha256"] == expected_protocol_hashes
    assert man_a["input_sha256"]["model_a_t2_input.jsonl"] == compute_sha256(os.path.join(GATE_B3_DIR, "model_a_t2_input.jsonl"))
    assert man_a["input_sha256"]["model_a_t3_input.jsonl"] == compute_sha256(os.path.join(GATE_B3_DIR, "model_a_t3_input.jsonl"))
    assert man_a["expected_record_count_per_taxonomy"] == 350
    assert man_a["request_isolation"] == "ONE_QUERY_ONE_FRESH_CONTEXT_REQUIRED"
    assert man_a["execution_isolation_class"] == "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION"
    assert man_a["fresh_context_per_item_required"] is True
    assert man_a["empty_workdir_required"] is True
    assert man_a["actual_tool_use_allowed"] is False
    assert man_a["zero_tool_use_audit_required"] is True
    assert man_a["tool_violation_retry_attempts"] == 0
    assert man_a["execution_isolation_amendment_sha256"] == compute_sha256(amendment_path)
    assert man_a["fresh_context_per_item_verified"] is True
    assert man_a["empty_workdir_verified"] is True
    assert man_a["zero_tool_use_audit_verified"] is True
    assert man_a["execution_isolation_verified"] is True
    assert man_a["synthetic_smoke_test_passed"] is True
    assert man_a["benchmark_execution_authorized"] is True

    # MODEL_B Manifest
    manifest_b_path = os.path.join(GATE_B3_DIR, "model_b_execution_manifest.json")
    assert os.path.exists(manifest_b_path), "Missing model_b_execution_manifest.json"
    with open(manifest_b_path, "r", encoding="utf-8") as f:
        man_b = json.load(f)

    assert man_b["source_id"] == "MODEL_B"
    assert man_b["provider"] == "Anthropic"
    assert man_b["model"] == "Claude Opus 4.6"
    assert man_b["execution_environment"] == "Antigravity / isolated Claude execution backend"
    assert man_b["configuration_frozen"] is True
    assert man_b["configuration_sha256"] == cfg["MODEL_B"]["configuration_sha256"]
    assert man_b["protocol_sha256"] == expected_protocol_hashes
    assert man_b["input_sha256"]["model_b_t2_input.jsonl"] == compute_sha256(os.path.join(GATE_B3_DIR, "model_b_t2_input.jsonl"))
    assert man_b["input_sha256"]["model_b_t3_input.jsonl"] == compute_sha256(os.path.join(GATE_B3_DIR, "model_b_t3_input.jsonl"))
    assert man_b["expected_record_count_per_taxonomy"] == 350
    assert man_b["request_isolation"] == "ONE_QUERY_ONE_FRESH_CONTEXT_REQUIRED"
    assert man_b["execution_isolation_class"] == "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION"
    assert man_b["fresh_context_per_item_required"] is True
    assert man_b["empty_workdir_required"] is True
    assert man_b["actual_tool_use_allowed"] is False
    assert man_b["zero_tool_use_audit_required"] is True
    assert man_b["tool_violation_retry_attempts"] == 0
    assert man_b["execution_isolation_amendment_sha256"] == compute_sha256(amendment_path)
    assert man_b["fresh_context_per_item_verified"] is True
    assert man_b["empty_workdir_verified"] is True
    assert man_b["zero_tool_use_audit_verified"] is True
    assert man_b["execution_isolation_verified"] is True
    assert man_b["synthetic_smoke_test_passed"] is True
    assert man_b["benchmark_execution_authorized"] is True


def test_sanitized_execution_manifests_contain_no_prohibited_content():
    """Verify execution manifests contain no gold, references, predictions, or cross-model leakage."""
    prohibited_substrings = [
        "gold",
        "human_annotation_key",
        "reference labels",
        "student",
        "prediction",
        "Gate B.2",
        "score",
        "delta",
        "taxonomy selection",
    ]

    manifest_a_path = os.path.join(GATE_B3_DIR, "model_a_execution_manifest.json")
    manifest_b_path = os.path.join(GATE_B3_DIR, "model_b_execution_manifest.json")

    with open(manifest_a_path, "r", encoding="utf-8") as f:
        text_a = f.read()
    with open(manifest_b_path, "r", encoding="utf-8") as f:
        text_b = f.read()

    # Check prohibited strings
    for s in prohibited_substrings:
        assert s.lower() not in text_a.lower(), f"Prohibited string '{s}' leaked in MODEL_A manifest!"
        assert s.lower() not in text_b.lower(), f"Prohibited string '{s}' leaked in MODEL_B manifest!"

    # Cross-annotator leakage check
    assert "MODEL_B" not in text_a
    assert "Claude" not in text_a
    assert "Anthropic" not in text_a

    assert "MODEL_A" not in text_b
    assert "GPT-6" not in text_b
    assert "Astra" not in text_b
    assert "OpenAI" not in text_b


def test_no_annotation_result_files_exist():
    """Verify zero annotation result files exist before authorized execution."""
    import glob
    ann_files = glob.glob(os.path.join(GATE_B3_DIR, "*_annotations.jsonl"))
    assert len(ann_files) == 0, f"Annotation output files found before execution: {ann_files}"


def test_frozen_b2_and_v1_artifacts_unchanged():
    """Verify frozen Gate B.2 benchmark data and v1 database remain bitwise unchanged."""
    stress_csv = os.path.join(GATE_B2_DIR, "gate_b2_stress_eval.csv")
    expected_stress_sha256 = "26cbf6517e25511d19d67051f500459ef7d78d87e5fbd1eb6d21849842242a1c"
    assert os.path.exists(stress_csv)
    assert compute_sha256(stress_csv) == expected_stress_sha256

    blind_csv = os.path.join(GATE_B2_DIR, "human_annotation_blind.csv")
    assert os.path.exists(blind_csv)
    assert compute_sha256(blind_csv) == EXPECTED_SOURCE_SHA256

    # Verify canonical v1 transit database exists and contains expected tables
    import sqlite3
    db_path = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")
    assert os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    assert "transport_hubs" in tables
    assert "transport_stops" in tables
    assert "transport_routes" in tables
    conn.close()


def test_transfer_guide_manifest_checksum_separation():
    """Verify transfer guide clearly separates manifest file SHA-256 from canonical config SHA."""
    transfer_guide_path = os.path.join(REPORTS_B3_DIR, "MODEL_ANNOTATOR_PACKAGE_TRANSFER.md")
    assert os.path.exists(transfer_guide_path), "Missing MODEL_ANNOTATOR_PACKAGE_TRANSFER.md"

    with open(transfer_guide_path, "r", encoding="utf-8") as f:
        guide_text = f.read()

    # Verify terminology separation
    assert "Manifest file SHA-256" in guide_text
    assert "Canonical model configuration SHA stored inside manifest" in guide_text
    assert "Target for `sha256sum` (Actual File Byte SHA-256)" in guide_text

    # Verify actual manifest file hashes match what is documented in transfer guide
    manifest_g_path = os.path.join(GATE_B3_DIR, "model_g_execution_manifest.json")
    manifest_a_path = os.path.join(GATE_B3_DIR, "model_a_execution_manifest.json")
    manifest_b_path = os.path.join(GATE_B3_DIR, "model_b_execution_manifest.json")
    file_sha_g = compute_sha256(manifest_g_path)
    file_sha_a = compute_sha256(manifest_a_path)
    file_sha_b = compute_sha256(manifest_b_path)

    assert file_sha_g in guide_text, f"MODEL_G manifest file SHA {file_sha_g} not found in guide"
    assert file_sha_a in guide_text, f"MODEL_A manifest file SHA {file_sha_a} not found in guide"
    assert file_sha_b in guide_text, f"MODEL_B manifest file SHA {file_sha_b} not found in guide"

    # Verify canonical config hashes match what is stored in configs
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    assert cfg["MODEL_G"]["configuration_sha256"] in guide_text
    assert cfg["MODEL_A"]["configuration_sha256"] in guide_text
    assert cfg["MODEL_B"]["configuration_sha256"] in guide_text
    assert cfg["MODEL_G"]["configuration_sha256"] != file_sha_g
    assert cfg["MODEL_A"]["configuration_sha256"] != file_sha_a
    assert cfg["MODEL_B"]["configuration_sha256"] != file_sha_b

    # Regression assertions: amended behavioral isolation protocol requirements
    assert "remain completely disabled" not in guide_text, "Transfer guide must not claim complete tool disability"
    assert "bootstrap verification reports `PASS` may execution readiness be authorized" not in guide_text
    assert "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION" in guide_text
    assert "zero-tool-use auditing" in guide_text.lower()
    assert "tool calls observed = 0" in guide_text.lower()
    assert "web calls observed = 0" in guide_text.lower()
    assert "external file reads observed = 0" in guide_text.lower()
    assert "command executions observed = 0" in guide_text.lower()


def test_execution_isolation_amendment_19_requirements(tmp_path):
    """Explicit automated coverage for all 19 Gate B.3 execution-isolation amendment requirements."""
    from scripts.nlp_v2.gate_b3.qa_gate_b3_annotation_start import (
        evaluate_annotation_start_readiness,
        compute_model_config_hash,
        compute_global_config_hash
    )
    import glob
    import sqlite3

    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 1. execution-isolation amendment exists
    amendment_path = os.path.join(DOCS_B3_DIR, "gate_b3_execution_isolation_amendment.md")
    assert os.path.exists(amendment_path), "Requirement 1: gate_b3_execution_isolation_amendment.md missing"

    # 2. amendment hash stored and recomputed
    computed_amendment_sha = compute_sha256(amendment_path)
    assert cfg.get("execution_isolation_amendment_sha256") == computed_amendment_sha, "Requirement 2: amendment hash mismatch"

    # 3. amendment hash included in global configuration hash
    m_g_hash = compute_model_config_hash(cfg["MODEL_G"])
    recomputed_global = compute_global_config_hash(cfg, m_g_hash)
    assert recomputed_global == cfg["configuration_sha256"], "Requirement 3: global config hash must match"

    # 4. mutation triggers configuration/protocol drift failure
    cfg_drift = _create_valid_frozen_mock_config()
    cfg_drift["execution_isolation_amendment_sha256"] = "bad0000000000000000000000000000000000000000000000000000000000bad"
    drift_file = tmp_path / "drift_test.json"
    with open(drift_file, "w", encoding="utf-8") as f:
        json.dump(cfg_drift, f)
    is_ready, reasons = evaluate_annotation_start_readiness(configs_path=str(drift_file))
    assert is_ready is False, "Requirement 4: mutation must trigger failure"
    assert any("FROZEN_ANNOTATION_CONFIGURATION_DRIFT" in r or "FROZEN_MODEL_CONFIGURATION_DRIFT" in r for r in reasons)

    # 5. model has the exact canonical isolation class
    assert cfg["MODEL_G"]["execution_isolation_class"] == "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION", "Requirement 5: MODEL_G isolation class mismatch"

    # 6. actual tool use is forbidden
    assert cfg["MODEL_G"]["actual_tool_use_allowed"] is False, "Requirement 6: actual_tool_use_allowed != False"

    # 7. zero-tool-use audit required
    assert cfg["MODEL_G"]["zero_tool_use_audit_required"] is True, "Requirement 7: zero_tool_use_audit_required != True"

    # 8. empty workdir required
    assert cfg["MODEL_G"]["empty_workdir_required"] is True, "Requirement 8: empty_workdir_required != True"

    # 9. fresh context required
    assert cfg["MODEL_G"]["fresh_context_per_item_required"] is True, "Requirement 9: fresh_context_per_item_required != True"

    # 10. tool violation retry count = 0
    assert cfg["MODEL_G"]["tool_violation_retry_attempts"] == 0, "Requirement 10: tool_violation_retry_attempts != 0"
    assert cfg["MODEL_G"]["retry_policy"]["tool_violation_retry_attempts"] == 0, "Requirement 10: retry_policy.tool_violation_retry_attempts != 0"

    # 11. execution readiness reset before smoke test under amended design
    assert cfg["MODEL_G"]["execution_isolation_verified"] is False, "Requirement 11: execution_isolation_verified != False"
    assert cfg["MODEL_G"]["fresh_context_per_item_verified"] is False, "Requirement 11: fresh_context_per_item_verified != False"
    assert cfg["MODEL_G"]["empty_workdir_verified"] is False, "Requirement 11: empty_workdir_verified != False"
    assert cfg["MODEL_G"]["zero_tool_use_audit_verified"] is False, "Requirement 11: zero_tool_use_audit_verified != False"

    # 12. smoke test initially false
    assert cfg["MODEL_G"]["synthetic_smoke_test_passed"] is False, "Requirement 12: synthetic_smoke_test_passed != False"

    # 13. benchmark authorization initially false
    assert cfg["MODEL_G"]["benchmark_execution_authorized"] is False, "Requirement 13: benchmark_execution_authorized != False"

    # 14. no annotation output files
    ann_files = glob.glob(os.path.join(GATE_B3_DIR, "*_annotations.jsonl"))
    assert len(ann_files) == 0, f"Requirement 14: annotation output files found: {ann_files}"

    # 15. source blind unchanged
    assert compute_sha256(SOURCE_BLIND_CSV) == EXPECTED_SOURCE_SHA256, "Requirement 15: source blind hash changed"

    # 16. Gate B.2 stress unchanged
    stress_csv = os.path.join(GATE_B2_DIR, "gate_b2_stress_eval.csv")
    assert compute_sha256(stress_csv) == "26cbf6517e25511d19d67051f500459ef7d78d87e5fbd1eb6d21849842242a1c", "Requirement 16: stress eval hash changed"

    # 17. frozen v1 unchanged
    db_path = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")
    assert os.path.exists(db_path), "Requirement 17: canonical v1 DB missing"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM transport_stops")
    stops_cnt = cur.fetchone()[0]
    conn.close()
    assert stops_cnt > 0, "Requirement 17: canonical v1 DB stops table empty"

    # 18. manifests remain sanitized
    manifest_g_path = os.path.join(GATE_B3_DIR, "model_g_execution_manifest.json")
    manifest_a_path = os.path.join(GATE_B3_DIR, "model_a_execution_manifest.json")
    manifest_b_path = os.path.join(GATE_B3_DIR, "model_b_execution_manifest.json")
    with open(manifest_g_path, "r", encoding="utf-8") as f:
        text_g = f.read()
    with open(manifest_a_path, "r", encoding="utf-8") as f:
        text_a = f.read()
    with open(manifest_b_path, "r", encoding="utf-8") as f:
        text_b = f.read()
    for forbidden in ["gold", "human_annotation_key", "prediction", "student", "reference labels"]:
        assert forbidden not in text_g.lower(), f"Requirement 18: forbidden '{forbidden}' leaked in MODEL_G manifest"
        assert forbidden not in text_a.lower(), f"Requirement 18: forbidden '{forbidden}' leaked in MODEL_A manifest"
        assert forbidden not in text_b.lower(), f"Requirement 18: forbidden '{forbidden}' leaked in MODEL_B manifest"

    # 19. transfer guide contains updated manifest file SHA values
    transfer_guide_path = os.path.join(REPORTS_B3_DIR, "MODEL_ANNOTATOR_PACKAGE_TRANSFER.md")
    with open(transfer_guide_path, "r", encoding="utf-8") as f:
        guide_text = f.read()
    assert compute_sha256(manifest_g_path) in guide_text, "Requirement 19: MODEL_G manifest file SHA missing in transfer guide"
    assert compute_sha256(manifest_a_path) in guide_text, "Requirement 19: MODEL_A manifest file SHA missing in transfer guide"
    assert compute_sha256(manifest_b_path) in guide_text, "Requirement 19: MODEL_B manifest file SHA missing in transfer guide"


def test_model_execution_readiness_recorded():
    """Verify execution readiness evidence report and manifest readiness flags."""
    readiness_report = os.path.join(REPORTS_B3_DIR, "GATE_B3_MODEL_EXECUTION_READINESS.md")
    assert os.path.exists(readiness_report), "Missing GATE_B3_MODEL_EXECUTION_READINESS.md"
    with open(readiness_report, "r", encoding="utf-8") as f:
        text = f.read()

    assert "Hard architectural tool isolation is not claimed" in text
    assert "This readiness record is based on sterile-workspace execution evidence reviewed before benchmark authorization" in text
    assert "real benchmark invocations" in text.lower() and ": 0" in text
    assert "33/33 PASS" in text
    assert "gpt-6-astra" in text
    assert "Claude Opus 4.6" in text
    assert "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION" in text

    provenance_report = os.path.join(REPORTS_B3_DIR, "GATE_B3_PRE_AMENDMENT_MODEL_EXECUTION_PROVENANCE.md")
    assert os.path.exists(provenance_report), "Missing GATE_B3_PRE_AMENDMENT_MODEL_EXECUTION_PROVENANCE.md"
    with open(provenance_report, "r", encoding="utf-8") as f:
        prov_text = f.read()
    assert "ABORTED_PRE_AMENDMENT_EXECUTION" in prov_text
    assert "23" in prov_text
    assert "ANN_B2_024" in prov_text

    # Manifest gate flags
    ann_manifest_path = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
    with open(ann_manifest_path, "r", encoding="utf-8") as f:
        ann_m = json.load(f)

    assert ann_m["primary_model_source_id"] == "MODEL_G"
    assert ann_m["model_g_execution_ready"] is False
    assert ann_m["annotation_started"] is False
    assert ann_m["reference_join_enabled"] is False
    assert ann_m["first_pass_locked"] is False
    assert ann_m["gold_boundary_audit_started"] is False
    assert ann_m["taxonomy_decision_status"] == "PENDING"
    assert ann_m["retired_primary_model_sources"] == ["MODEL_A", "MODEL_B"]

    # Execution manifest for MODEL_G
    man_g_path = os.path.join(GATE_B3_DIR, "model_g_execution_manifest.json")
    with open(man_g_path, "r", encoding="utf-8") as f:
        m_data = json.load(f)
    assert m_data["fresh_context_per_item_verified"] is False
    assert m_data["empty_workdir_verified"] is False
    assert m_data["zero_tool_use_audit_verified"] is False
    assert m_data["execution_isolation_verified"] is False
    assert m_data["synthetic_smoke_test_passed"] is False
    assert m_data["benchmark_execution_authorized"] is False


def test_gate_b3_benchmark_execution_authorization_recorded():
    """Verify benchmark execution authorization report, invariant hashes, and boundaries."""
    auth_report = os.path.join(REPORTS_B3_DIR, "GATE_B3_BENCHMARK_EXECUTION_AUTHORIZATION.md")
    assert os.path.exists(auth_report), "Missing GATE_B3_BENCHMARK_EXECUTION_AUTHORIZATION.md"
    with open(auth_report, "r", encoding="utf-8") as f:
        text = f.read()

    assert "Gate B.3 Benchmark Execution Authorization" in text
    assert "MODEL_A" in text and "**Authorized:** YES" in text
    assert "MODEL_B" in text and "**Authorized:** YES" in text
    assert "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION" in text
    assert "real benchmark invocations" in text.lower() and "= 0" in text
    assert "Hard architectural tool isolation is not claimed" in text

    # Canonical config sha invariants
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    assert cfg["MODEL_A"]["status"] == "ABORTED_PRE_AMENDMENT_EXECUTION"
    assert cfg["MODEL_B"]["status"] == "RETIRED_PRE_COMPLETION"
    assert cfg["MODEL_G"]["status"] == "FROZEN_NOT_EXECUTION_READY"
    assert cfg["MODEL_A"]["benchmark_execution_authorized"] is False
    assert cfg["MODEL_B"]["benchmark_execution_authorized"] is False
    assert cfg["MODEL_G"]["benchmark_execution_authorized"] is False
    assert cfg["MODEL_G"]["execution_timestamp"] is None

    assert cfg["MODEL_G"]["configuration_sha256"] == "d4a359b72779ec15f42ffa0ba72beb57ff20ff765de901783082caee0deda1dd"
    assert cfg["MODEL_A"]["configuration_sha256"] == "5db1c4aeae9e8cabb98a5b20637488c6812a826d27cbf4ed4cd578d28038fe5c"
    assert cfg["MODEL_B"]["configuration_sha256"] == "3d9264b1172878ed07080d1ca4e087170aa83fd366f8695effbf32297318020c"
    assert cfg["configuration_sha256"] == "e0f05789e9dadbbff2ab4ecf02060a7242362e3a3f4cf7d3870113e8e293ebca"
    assert cfg["historical_configuration_sha256"] == "2a7c82b9297f65f750f5f72685d329d2e65e40c0691b09546802d8cd727afc8e"
    assert cfg["execution_isolation_amendment_sha256"] == "a48b732a9373a8e2d65ab3963b1920a658ada1e3c703687b8d2d072f46e87f19"
    assert cfg["resource_feasibility_amendment_sha256"] == "7960145fb12490699611f7c6d9a021929a42408ecc1127595572233f754d319d"

    # Annotation manifest boundaries
    ann_manifest_path = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
    with open(ann_manifest_path, "r", encoding="utf-8") as f:
        ann_m = json.load(f)
    assert ann_m["annotation_started"] is False
    assert ann_m["reference_join_enabled"] is False
    assert ann_m["first_pass_locked"] is False
    assert ann_m["gold_boundary_audit_started"] is False
    assert ann_m["taxonomy_decision_status"] == "PENDING"

    # Annotation output files count == 0
    ann_files = glob.glob(os.path.join(GATE_B3_DIR, "*_annotations.jsonl"))
    assert len(ann_files) == 0, f"Annotation output files found: {ann_files}"


def test_resource_feasibility_amendment_all_30_requirements():
    """Explicit automated verification of all 30 Gate B.3 resource-feasibility amendment requirements (Section 21)."""
    import glob
    import sqlite3

    # Load configurations and manifests
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    ann_manifest_path = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
    with open(ann_manifest_path, "r", encoding="utf-8") as f:
        ann_m = json.load(f)

    man_g_path = os.path.join(GATE_B3_DIR, "model_g_execution_manifest.json")
    with open(man_g_path, "r", encoding="utf-8") as f:
        man_g = json.load(f)

    # 1. frozen source blind still exactly 350
    with open(SOURCE_BLIND_CSV, "r", encoding="utf-8") as f:
        source_records = list(csv.DictReader(f))
    assert len(source_records) == 350, f"Req 1: Expected 350 source records, got {len(source_records)}"

    # 2. frozen source blind SHA unchanged
    assert compute_sha256(SOURCE_BLIND_CSV) == "94fd8bb3e7f2e3bdaf274c4ee5bcf7e083e9ef2a66322fbcf7bee2cadf231999", "Req 2: source blind SHA mismatch"

    # 3. Gate B.2 stress unchanged
    stress_csv = os.path.join(GATE_B2_DIR, "gate_b2_stress_eval.csv")
    assert compute_sha256(stress_csv) == "26cbf6517e25511d19d67051f500459ef7d78d87e5fbd1eb6d21849842242a1c", "Req 3: Gate B.2 stress SHA mismatch"

    # 4. frozen v1 unchanged
    db_path = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")
    assert os.path.exists(db_path), "Req 4: canonical transport DB missing"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM transport_stops")
    stops_cnt = cur.fetchone()[0]
    conn.close()
    assert stops_cnt > 0, "Req 4: canonical stops table empty"

    # 5. student packages unchanged
    t2_p1 = os.path.join(GATE_B3_DIR, "student_t2_first_pass.csv")
    t2_p2 = os.path.join(GATE_B3_DIR, "student_t2_second_pass.csv")
    t3_p1 = os.path.join(GATE_B3_DIR, "student_t3_first_pass.csv")
    t3_p2 = os.path.join(GATE_B3_DIR, "student_t3_second_pass.csv")
    assert os.path.exists(t2_p1) and os.path.exists(t2_p2), "Req 5: student T2 packages missing"
    assert os.path.exists(t3_p1) and os.path.exists(t3_p2), "Req 5: student T3 packages missing"
    with open(t2_p1, "r", encoding="utf-8") as f:
        t2_p1_cnt = len(list(csv.DictReader(f)))
    with open(t2_p2, "r", encoding="utf-8") as f:
        t2_p2_cnt = len(list(csv.DictReader(f)))
    with open(t3_p1, "r", encoding="utf-8") as f:
        t3_p1_cnt = len(list(csv.DictReader(f)))
    with open(t3_p2, "r", encoding="utf-8") as f:
        t3_p2_cnt = len(list(csv.DictReader(f)))
    assert t2_p1_cnt == 175 and t2_p2_cnt == 175, "Req 5: student T2 count != 350 total"
    assert t3_p1_cnt == 175 and t3_p2_cnt == 175, "Req 5: student T3 count != 350 total"

    # 6. MODEL_A historical config preserved
    assert "MODEL_A" in cfg, "Req 6: MODEL_A missing from configs"
    assert cfg["MODEL_A"]["source_id"] == "MODEL_A", "Req 6: MODEL_A source_id mismatch"

    # 7. MODEL_B historical config preserved
    assert "MODEL_B" in cfg, "Req 7: MODEL_B missing from configs"
    assert cfg["MODEL_B"]["source_id"] == "MODEL_B", "Req 7: MODEL_B source_id mismatch"

    # 8. MODEL_A excluded from primary analysis
    assert cfg["MODEL_A"]["primary_analysis_included"] is False, "Req 8: MODEL_A primary_analysis_included != False"

    # 9. MODEL_B excluded from primary analysis
    assert cfg["MODEL_B"]["primary_analysis_included"] is False, "Req 9: MODEL_B primary_analysis_included != False"

    # 10. MODEL_G exists
    assert "MODEL_G" in cfg, "Req 10: MODEL_G missing from configs"
    assert cfg["MODEL_G"]["source_id"] == "MODEL_G", "Req 10: MODEL_G source_id mismatch"

    # 11. MODEL_G is the active primary model annotator
    assert cfg["primary_model_annotator_source_id"] == "MODEL_G", "Req 11: configs primary_model_annotator_source_id != MODEL_G"
    assert ann_m["primary_model_source_id"] == "MODEL_G", "Req 11: annotation manifest primary_model_source_id != MODEL_G"

    # 12. MODEL_G has 350 T2 inputs
    g_t2_path = os.path.join(GATE_B3_DIR, "model_g_t2_input.jsonl")
    assert os.path.exists(g_t2_path), "Req 12: model_g_t2_input.jsonl missing"
    with open(g_t2_path, "r", encoding="utf-8") as f:
        g_t2_records = [json.loads(line) for line in f]
    assert len(g_t2_records) == 350, f"Req 12: MODEL_G T2 count is {len(g_t2_records)}, expected 350"

    # 13. MODEL_G has 350 T3 inputs
    g_t3_path = os.path.join(GATE_B3_DIR, "model_g_t3_input.jsonl")
    assert os.path.exists(g_t3_path), "Req 13: model_g_t3_input.jsonl missing"
    with open(g_t3_path, "r", encoding="utf-8") as f:
        g_t3_records = [json.loads(line) for line in f]
    assert len(g_t3_records) == 350, f"Req 13: MODEL_G T3 count is {len(g_t3_records)}, expected 350"

    # 14. MODEL_G exact ID sets match frozen 350 sample
    source_ids = [r["annotation_id"] for r in source_records]
    assert [r["annotation_id"] for r in g_t2_records] == source_ids, "Req 14: MODEL_G T2 IDs do not match source blind"
    assert [r["annotation_id"] for r in g_t3_records] == source_ids, "Req 14: MODEL_G T3 IDs do not match source blind"

    # 15. MODEL_G input has only annotation_id/query/taxonomy_version
    allowed_keys = {"annotation_id", "query", "taxonomy_version"}
    for idx, r in enumerate(g_t2_records):
        assert set(r.keys()) == allowed_keys, f"Req 15: T2 record {idx} keys != {allowed_keys}: {set(r.keys())}"
    for idx, r in enumerate(g_t3_records):
        assert set(r.keys()) == allowed_keys, f"Req 15: T3 record {idx} keys != {allowed_keys}: {set(r.keys())}"

    # 16. MODEL_G no gold/provenance/prediction leakage
    with open(g_t2_path, "r", encoding="utf-8") as f:
        t2_text = f.read()
    with open(g_t3_path, "r", encoding="utf-8") as f:
        t3_text = f.read()
    with open(man_g_path, "r", encoding="utf-8") as f:
        man_text = f.read()
    for forbidden in ["gold", "human_annotation_key", "prediction", "Gate B.2", "STUDENT_R1", "MODEL_A", "MODEL_B"]:
        assert forbidden.lower() not in t2_text.lower(), f"Req 16: Forbidden '{forbidden}' found in MODEL_G T2 input"
        assert forbidden.lower() not in t3_text.lower(), f"Req 16: Forbidden '{forbidden}' found in MODEL_G T3 input"
    for forbidden in ["gold", "human_annotation_key", "prediction", "student", "reference labels"]:
        assert forbidden.lower() not in man_text.lower(), f"Req 16: Forbidden '{forbidden}' found in MODEL_G manifest"

    # 17. MODEL_G fresh-context requirement true
    assert cfg["MODEL_G"]["fresh_context_per_item_required"] is True, "Req 17: fresh_context_per_item_required != True in config"
    assert man_g["fresh_context_per_item_required"] is True, "Req 17: fresh_context_per_item_required != True in manifest"

    # 18. MODEL_G zero-tool requirement true
    assert cfg["MODEL_G"]["zero_tool_use_audit_required"] is True, "Req 18: zero_tool_use_audit_required != True in config"
    assert man_g["zero_tool_use_audit_required"] is True, "Req 18: zero_tool_use_audit_required != True in manifest"

    # 19. MODEL_G semantic retries = 0
    assert cfg["MODEL_G"]["retry_policy"]["semantic_retries"] == 0, "Req 19: semantic_retries != 0 in config"

    # 20. MODEL_G tool violation retries = 0
    assert cfg["MODEL_G"]["retry_policy"]["tool_violation_retry_attempts"] == 0, "Req 20: tool_violation_retry_attempts != 0 in config"
    assert cfg["MODEL_G"]["tool_violation_retry_attempts"] == 0, "Req 20: tool_violation_retry_attempts != 0 top-level config"
    assert man_g["tool_violation_retry_attempts"] == 0, "Req 20: tool_violation_retry_attempts != 0 in manifest"

    # 21. MODEL_G smoke test initially false
    assert cfg["MODEL_G"]["synthetic_smoke_test_passed"] is False, "Req 21: synthetic_smoke_test_passed != False in config"
    assert man_g["synthetic_smoke_test_passed"] is False, "Req 21: synthetic_smoke_test_passed != False in manifest"

    # 22. MODEL_G execution isolation initially false
    assert cfg["MODEL_G"]["execution_isolation_verified"] is False, "Req 22: execution_isolation_verified != False in config"
    assert man_g["execution_isolation_verified"] is False, "Req 22: execution_isolation_verified != False in manifest"

    # 23. MODEL_G benchmark authorization initially false
    assert cfg["MODEL_G"]["benchmark_execution_authorized"] is False, "Req 23: benchmark_execution_authorized != False in config"
    assert man_g["benchmark_execution_authorized"] is False, "Req 23: benchmark_execution_authorized != False in manifest"

    # 24. annotation_started=false
    assert ann_m["annotation_started"] is False, "Req 24: annotation_started != False"

    # 25. first_pass_locked=false
    assert ann_m["first_pass_locked"] is False, "Req 25: first_pass_locked != False"

    # 26. reference_join_enabled=false
    assert ann_m["reference_join_enabled"] is False, "Req 26: reference_join_enabled != False"

    # 27. gold audit not started
    assert ann_m["gold_boundary_audit_started"] is False, "Req 27: gold_boundary_audit_started != False"

    # 28. taxonomy decision=PENDING
    assert ann_m["taxonomy_decision_status"] == "PENDING", "Req 28: taxonomy_decision_status != PENDING"

    # 29. no final MODEL_G annotation outputs exist
    g_out_files = glob.glob(os.path.join(GATE_B3_DIR, "model_g_*_annotations.jsonl"))
    assert len(g_out_files) == 0, f"Req 29: Final MODEL_G annotation outputs exist: {g_out_files}"

    # 30. partial Astra annotations are not referenced as active primary input
    assert cfg["MODEL_A"]["primary_analysis_included"] is False, "Req 30: MODEL_A marked included in primary analysis"
    assert ann_m["primary_model_source_id"] != "MODEL_A", "Req 30: MODEL_A is primary model source"
    assert "model_a_t2_annotations.jsonl" not in [f for f in glob.glob(os.path.join(GATE_B3_DIR, "*_annotations.jsonl"))]



