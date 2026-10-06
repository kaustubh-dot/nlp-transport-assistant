"""Production T3 checkpoint and train/validation boundary tests."""

import json
from pathlib import Path

import pytest


MANIFEST = Path(__file__).resolve().parents[1] / "models/nlp_v2_t3_manifest.json"


def test_selected_checkpoint_manifest_is_t3_and_validation_selected():
    from src.nlp_v2.model import load_manifest

    data = load_manifest(MANIFEST)
    assert data["taxonomy"] == "T3"
    assert len(data["label_order"]) == 16
    assert data["label_order"][13] == "nearest_transport"
    assert data["selection"]["criterion"] == "validation_macro_f1_only"
    assert data["selection"]["seed"] == 42
    assert data["preprocessing"] == "raw_query"
    assert data["max_length"] == 64


def test_manifest_rejects_wrong_label_order_before_loading_weights(tmp_path):
    from src.nlp_v2.model import load_manifest
    from src.nlp_v2.contracts import ContractError

    data = json.loads(MANIFEST.read_text())
    data["label_order"][0], data["label_order"][1] = data["label_order"][1], data["label_order"][0]
    path = tmp_path / "bad_manifest.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ContractError, match="label order"):
        load_manifest(path)


def test_missing_or_hash_mismatched_weights_fail_without_fallback(tmp_path):
    from src.nlp_v2.model import T3IntentClassifier
    from src.nlp_v2.contracts import ContractError

    data = json.loads(MANIFEST.read_text())
    path = tmp_path / "manifest.json"
    data["checkpoint_path"] = str(tmp_path / "missing.pt")
    path.write_text(json.dumps(data))
    with pytest.raises(FileNotFoundError):
        T3IntentClassifier(path)

    tiny = tmp_path / "tiny.pt"
    tiny.write_bytes(b"not a checkpoint")
    data["checkpoint_path"] = str(tiny)
    path.write_text(json.dumps(data))
    with pytest.raises(ContractError, match="SHA-256"):
        T3IntentClassifier(path)


def test_existing_t3_checkpoint_loads_strictly_and_predicts_synthetic_query():
    from src.nlp_v2.model import T3IntentClassifier
    from src.nlp_v2.contracts import T3_INTENTS

    classifier = T3IntentClassifier(MANIFEST)
    result = classifier.predict("Where is the nearest bus stop?")
    assert result.primary_label == "nearest_transport"
    assert result.primary_label in T3_INTENTS
    assert result.acceptable_labels == ("nearest_transport",)
    assert 0 < result.confidence <= 1
    from src.nlp_v2.assistant import T3Assistant
    reply = T3Assistant(classifier=classifier).process_query(
        "What is the bus fare for stage 4 and when is the last bus from Poonamallee Bus Terminus?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "multiple_goals"
    assert set(reply.candidate_intents) == {"fare_calculation", "first_and_last_service"}


def test_training_loader_reads_only_train_and_validation_and_rejects_overlap(tmp_path):
    from scripts.nlp_v2.train_production_t3 import load_training_splits

    fieldnames = "query,T3_label,family_id,semantic_family_id\n"
    train = tmp_path / "train.csv"
    validation = tmp_path / "validation.csv"
    train.write_text(fieldnames + "route A,point_to_point_route,family_a,semantic_a\n")
    validation.write_text(fieldnames + "route B,point_to_point_route,family_b,semantic_b\n")
    rows = load_training_splits(train, validation)
    assert rows[0][0]["query"] == "route A"
    assert rows[1][0]["query"] == "route B"

    validation.write_text(fieldnames + "route B,point_to_point_route,family_a,semantic_b\n")
    with pytest.raises(ValueError, match="family"):
        load_training_splits(train, validation)

    validation.write_text(
        fieldnames
        + "route B,point_to_point_route,family_a,semantic_b\n"
        + "route C,point_to_point_route,family_c,semantic_c\n"
    )
    _, clean_validation = load_training_splits(train, validation, exclude_overlaps=True)
    assert [row["query"] for row in clean_validation] == ["route C"]


def test_training_output_rejects_frozen_research_directory():
    from scripts.nlp_v2.train_production_t3 import validate_output_dir

    root = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="frozen"):
        validate_output_dir(root / "experiments/nlp_v2/gate_b2/new_run")
    with pytest.raises(ValueError, match="frozen"):
        validate_output_dir(root / "models/new_run")
    assert validate_output_dir(root / "experiments/nlp_v2/production_runs/new_run") == (
        root / "experiments/nlp_v2/production_runs/new_run"
    )


def test_smoke_train_marks_checkpoint_nonproduction(tmp_path):
    from scripts.nlp_v2.train_production_t3 import TrainConfig, train

    output = tmp_path / "smoke"
    result = train(TrainConfig(output_dir=output, smoke=True, batch_size=4, patience=5))
    assert result["taxonomy"] == "T3"
    assert result["smoke"] is True
    assert result["production_eligible"] is False
    assert result["validation_filter"] == "exclude_train_family_semantic_family_and_query_overlap"
    assert result["selection"]["criterion"] == "validation_macro_f1_only"
    assert result["configuration"]["batch_size"] == 4
    assert result["configuration"]["patience"] == 5
    assert result["configuration"]["device"] == "cpu"
    assert (output / "metadata.json").is_file()
    assert (output / "t3_best.pt").is_file()
