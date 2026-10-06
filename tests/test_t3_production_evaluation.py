"""Synthetic scoring tests; no frozen evaluation rows are used here."""

import pytest


def test_scoring_distinguishes_strict_secondary_and_operation_accuracy():
    from scripts.nlp_v2.evaluate_production_t3 import score_records

    rows = [
        {"gold": "fare_calculation", "predicted": "fare_calculation", "secondary": [], "language_class": "EN", "code_switch_level": "CS0", "noise_level": "N0", "contrast_group_id": "A"},
        {"gold": "point_to_point_route", "predicted": "multimodal_route", "secondary": ["multimodal_route"], "language_class": "EN", "code_switch_level": "CS1", "noise_level": "N1", "contrast_group_id": "A"},
    ]
    result = score_records(rows)
    assert result["count"] == 2
    assert result["strict_intent_accuracy"] == 0.5
    assert result["strict_intent_macro_f1"] == 1 / 16
    assert result["per_class"]["fare_calculation"]["f1"] == 1.0
    assert result["ambiguity_aware_accuracy"] == 1.0
    assert result["operation_accuracy"] == 0.5
    assert result["contrast_group_exact_accuracy"] == 0.0
    assert result["strata"]["language_class"]["EN"]["count"] == 2


def test_reference_join_rejects_gold_mismatch_and_missing_ids():
    from scripts.nlp_v2.evaluate_production_t3 import join_reference

    stress = [{"utterance_id": "X", "T3_label": "fare_calculation", "query": "synthetic"}]
    reference = {"R": {"utterance_id": "X", "gold_T3_intent": "nearest_transport"}}
    with pytest.raises(ValueError, match="gold mismatch"):
        join_reference(stress, reference)
    reference["R"]["gold_T3_intent"] = "fare_calculation"
    assert join_reference(stress, reference)[0]["utterance_id"] == "X"
    reference["R"]["utterance_id"] = "MISSING"
    with pytest.raises(ValueError, match="missing"):
        join_reference(stress, reference)


def test_overlap_audit_counts_metadata_without_labels():
    from scripts.nlp_v2.evaluate_production_t3 import overlap_audit

    train = [{"family_id": "f1", "semantic_family_id": "s1", "query": "route a"}]
    evaluation = [
        {"family_id": "f1", "semantic_family_id": "s1", "query": "route b"},
        {"family_id": "f2", "semantic_family_id": "s2", "query": "route c"},
    ]
    assert overlap_audit(train, evaluation) == {
        "total_rows": 2,
        "family_overlap_rows": 1,
        "semantic_family_overlap_rows": 1,
        "exact_query_overlap_rows": 0,
        "any_overlap_rows": 1,
    }


def test_partial_contrast_groups_are_counted():
    from scripts.nlp_v2.evaluate_production_t3 import group_coverage

    full = [{"contrast_group_id": "A"}, {"contrast_group_id": "A"}, {"contrast_group_id": "B"}]
    assert group_coverage(full, full[:2]) == {
        "observed_groups": 1, "complete_groups": 1, "partial_groups": 0,
    }
    assert group_coverage(full, full[:1]) == {
        "observed_groups": 1, "complete_groups": 0, "partial_groups": 1,
    }


def test_evaluation_rejects_frozen_output_and_input_hash_drift(tmp_path, monkeypatch):
    from scripts.nlp_v2 import evaluate_production_t3 as evaluator

    with pytest.raises(ValueError, match="frozen assets"):
        evaluator.evaluate(evaluator.ROOT / "reports/nlp_v2/gate_b2/new_evaluation")
    fake_stress = tmp_path / "fake.csv"
    fake_stress.write_text("synthetic")
    monkeypatch.setattr(evaluator, "STRESS", fake_stress)
    with pytest.raises(ValueError, match="hash mismatch"):
        evaluator.evaluate(tmp_path / "output")
