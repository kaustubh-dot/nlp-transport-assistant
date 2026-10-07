"""Strict production loader for the selected frozen-taxonomy T3 classifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .contracts import ContractError, IntentPrediction, T3_INTENTS


LABEL_ORDER = (
    "point_to_point_route", "multimodal_route", "first_and_last_service",
    "service_frequency", "scheduled_departure", "route_stop_sequence",
    "route_stop_membership", "mode_availability", "fare_calculation",
    "ticketing_and_passes", "station_facilities", "station_accessibility",
    "interchange_transfer", "nearest_transport", "realtime_status_query",
    "out_of_scope",
)
DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "models/nlp_v2_t3_manifest.json"
MODEL_NAME = "google/muril-base-cased"
MODEL_REVISION = "afd9f36c7923d54e97903922ff1b260d091d202f"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict:
    """Validate the immutable class and preprocessing contract before weight loading."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContractError("T3 manifest must be a JSON object")
    if data.get("taxonomy") != "T3":
        raise ContractError("Production intent model must use T3 taxonomy")
    if data.get("label_order") != list(LABEL_ORDER) or set(LABEL_ORDER) != T3_INTENTS:
        raise ContractError("T3 checkpoint label order does not match the frozen index order")
    if data.get("model_name") != MODEL_NAME or data.get("model_revision") != MODEL_REVISION:
        raise ContractError("Unexpected MuRIL model name or pinned revision")
    if data.get("preprocessing") != "raw_query" or data.get("max_length") != 64:
        raise ContractError("Unexpected T3 preprocessing contract")
    checksum = data.get("checkpoint_sha256", "")
    if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
        raise ContractError("Invalid checkpoint SHA-256")
    if not isinstance(data.get("checkpoint_path"), str) or not data["checkpoint_path"]:
        raise ContractError("Missing checkpoint path")
    return data


class T3IntentClassifier:
    """CPU-safe, strict 16-class checkpoint inference with no legacy fallback."""

    def __init__(self, manifest_path: str | Path = DEFAULT_MANIFEST):
        import torch
        from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

        manifest_path = Path(manifest_path).resolve()
        manifest = load_manifest(manifest_path)
        checkpoint = Path(manifest["checkpoint_path"])
        if not checkpoint.is_absolute():
            checkpoint = manifest_path.parent / checkpoint
        checkpoint = checkpoint.resolve()
        if not checkpoint.is_file():
            raise FileNotFoundError(f"T3 checkpoint missing: {checkpoint}")
        if sha256_file(checkpoint) != manifest["checkpoint_sha256"]:
            raise ContractError(f"T3 checkpoint SHA-256 mismatch: {checkpoint}")

        self.label_order = LABEL_ORDER
        self.max_length = manifest["max_length"]
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, revision=MODEL_REVISION, local_files_only=True
        )
        config = AutoConfig.from_pretrained(MODEL_NAME, revision=MODEL_REVISION, local_files_only=True)
        config.num_labels = len(LABEL_ORDER)
        config.id2label = {i: label for i, label in enumerate(LABEL_ORDER)}
        config.label2id = {label: i for i, label in enumerate(LABEL_ORDER)}
        self.model = AutoModelForSequenceClassification.from_config(config)
        state = torch.load(checkpoint, map_location="cpu", weights_only=True, mmap=True)
        self.model.load_state_dict(state, strict=True)
        self.model.eval()

    def predict(self, query: str) -> IntentPrediction:
        import torch

        if not isinstance(query, str) or not query.strip():
            raise ContractError("Query must be nonempty text")
        encoded = self.tokenizer(
            query, truncation=True, max_length=self.max_length,
            padding="max_length", return_tensors="pt",
        )
        with torch.inference_mode():
            logits = self.model(**encoded).logits[0]
            probabilities = torch.softmax(logits, dim=-1)
            index = int(probabilities.argmax().item())
        label = self.label_order[index]
        return IntentPrediction(label, (label,), float(probabilities[index].item()))
