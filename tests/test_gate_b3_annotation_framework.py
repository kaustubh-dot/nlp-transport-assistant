"""Unit and Integration Tests for NLP v2 Gate B.3 Annotation-Stability Framework.

Verifies Section 56 requirements:
1. Source 350 file unchanged (row count and bitwise SHA-256)
2. Student order assignment deterministic
3. 175/175 deterministic half split
4. Each student eventually sees every query under both taxonomies
5. First/second taxonomy order is counterbalanced
6. Model exports contain exactly 350 items each
7. Annotator exports contain no gold
8. Annotator exports contain no predictions
9. Annotator exports contain no utterance_id
10. Annotation schema validation
11. Acceptable set rules
12. Null primary supported
13. Clarification reason validation
14. First-pass lock blocks incomplete outputs
15. Gold join blocked before lock
16. Guide examples have zero overlap with blind set
17. Model annotator config remains PENDING
18. Taxonomy decision remains PENDING
19. Bootstrap interpretation note exists
"""

import os
import sys
import csv
import json
import hashlib
import re
import pytest

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

    # Counterbalancing check
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

    # Student CSVs
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

    # Model JSONLs
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


def test_annotation_schema_validation_and_acceptable_set_rules():
    """Verify annotation output schema rules."""
    schema_path = os.path.join(DOCS_B3_DIR, "annotation_output_schema.json")
    assert os.path.exists(schema_path), "Missing annotation_output_schema.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    props = schema["properties"]
    # 1. acceptable_labels non-empty array
    assert props["acceptable_labels"]["type"] == "array"
    assert props["acceptable_labels"]["minItems"] >= 1

    # 2. null primary supported
    prim_type = props["primary_label"]["type"]
    assert "null" in prim_type, f"primary_label must support null, got {prim_type}"

    # 3. clarification reasons validation
    enum_reasons = props["clarification_reasons"]["items"]["enum"]
    expected_reasons = {"intent_ambiguity", "missing_slot", "multiple_goals", "uninterpretable"}
    assert set(enum_reasons) == expected_reasons, f"Clarification reasons mismatch: {enum_reasons}"

    # 4. response status validation
    enum_status = props["response_status"]["enum"]
    assert set(enum_status) == {"VALID", "FORMAT_REPAIRED", "FAILED"}


def test_first_pass_lock_blocks_incomplete_outputs():
    """Verify lock_first_pass_annotations.py refuses to lock when outputs are missing."""
    from scripts.nlp_v2.gate_b3.lock_first_pass_annotations import attempt_lock
    success = attempt_lock()
    assert success is False, "Lock should NOT succeed when annotation files are missing!"


def test_gold_join_blocked_before_lock():
    """Verify compute_annotation_stability.py refuses gold key access prior to lock."""
    import scripts.nlp_v2.gate_b3.compute_annotation_stability as stab
    assert stab.is_first_pass_locked() is False
    with pytest.raises(PermissionError) as exc_info:
        stab.load_gold_key()
    assert "HARD GUARDRAIL VIOLATION" in str(exc_info.value)


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
    """Verify model annotator configuration placeholders remain PENDING."""
    cfg_path = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    assert cfg["MODEL_A"]["status"] == "PENDING"
    assert cfg["MODEL_A"]["provider"] == "PENDING"
    assert cfg["MODEL_A"]["execution_timestamp"] is None

    assert cfg["MODEL_B"]["status"] == "PENDING"
    assert cfg["MODEL_B"]["provider"] == "PENDING"
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
    """Verify Gate B.2 bootstrap interpretation note exists and preserves metrics."""
    note_path = os.path.join(REPORTS_B3_DIR, "gate_b2_bootstrap_interpretation_note.md")
    assert os.path.exists(note_path), "Missing gate_b2_bootstrap_interpretation_note.md"
    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "query bootstrap over fixed evaluated seeds" in content
    assert "+4.11" in content
    assert "+4.01" in content
    assert "0.0245" in content
    assert "0.0581" in content
