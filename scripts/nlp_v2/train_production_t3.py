#!/usr/bin/env python3
"""Train T3 on Gate B.2 train/validation only, outside frozen research paths.

The existing seed-42 checkpoint is the selected production artifact. This
entrypoint is for reproducible replacement runs and CPU pipeline smoke checks.
"""

from __future__ import annotations

import argparse
import csv
from importlib.metadata import version
import json
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, Dataset
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

from src.nlp_v2.model import LABEL_ORDER, MODEL_NAME, MODEL_REVISION, sha256_file


ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = ROOT / "data/nlp_v2/gate_b2/gate_b2_train.csv"
VALIDATION_PATH = ROOT / "data/nlp_v2/gate_b2/gate_b2_validation.csv"
TRAIN_SHA256 = "d92801006ecb96fd64d01e6a602697e2e8749494627964f82d002566e3d0ba94"
VALIDATION_SHA256 = "a870aea04006da25bde896f216c07313772603559cb794ad26f56eb0d8277415"
FROZEN_DIRS = (
    ROOT / "experiments/nlp_v2/gate_b2",
    ROOT / "reports/nlp_v2/gate_b2",
    ROOT / "data/nlp_v2/gate_b2",
    ROOT / "data/nlp_v2/gate_b3",
    ROOT / "reports/nlp_v2/gate_b3",
)
PRODUCTION_RUNS = ROOT / "experiments/nlp_v2/production_runs"


def load_training_splits(
    train_path: Path, validation_path: Path, *, exclude_overlaps: bool = False
) -> tuple[list[dict], list[dict]]:
    """Read development splits, rejecting or excluding overlapping validation rows."""
    def read(path: Path) -> list[dict]:
        with Path(path).open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise ValueError(f"Empty training split: {path}")
        required = {"query", "T3_label", "family_id", "semantic_family_id"}
        if not required <= rows[0].keys():
            raise ValueError(f"Missing training columns in {path}")
        for row in rows:
            if row["T3_label"] not in LABEL_ORDER or not row["query"].strip():
                raise ValueError(f"Invalid T3 row in {path}")
        return rows

    train_rows, validation_rows = read(train_path), read(validation_path)
    keys = ("family_id", "semantic_family_id", "query")
    seen = {key: {row[key].strip().casefold() for row in train_rows if row[key]} for key in keys}
    overlapping = [row for row in validation_rows if any(row[key].strip().casefold() in seen[key] for key in keys)]
    if overlapping and not exclude_overlaps:
        raise ValueError("Train/validation family or query overlap")
    if exclude_overlaps:
        validation_rows = [row for row in validation_rows if row not in overlapping]
        if not validation_rows:
            raise ValueError("No disjoint validation rows remain")
    return train_rows, validation_rows


def validate_output_dir(path: Path) -> Path:
    """Protect canonical, frozen, and source assets from training writes."""
    path = Path(path).resolve()
    if path == ROOT or any(path == parent or path.is_relative_to(parent) for parent in FROZEN_DIRS):
        raise ValueError(f"Output directory is inside a frozen research path: {path}")
    if path.is_relative_to(ROOT) and not path.is_relative_to(PRODUCTION_RUNS):
        raise ValueError(f"Output directory is inside a frozen repository path: {path}")
    return path


class Rows(Dataset):
    def __init__(self, rows: list[dict], tokenizer):
        self.rows = rows
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict:
        row = self.rows[index]
        encoded = self.tokenizer(
            row["query"], truncation=True, max_length=64,
            padding="max_length", return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(LABEL_ORDER.index(row["T3_label"]), dtype=torch.long),
        }


@dataclass(frozen=True)
class TrainConfig:
    output_dir: Path
    smoke: bool = False
    seed: int = 42
    max_epochs: int = 30
    patience: int = 3
    min_delta: float = 0.001
    batch_size: int = 16
    learning_rate: float = 2e-5


def train(config: TrainConfig) -> dict:
    output_dir = validate_output_dir(config.output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {output_dir}")
    if config.max_epochs < 1 or config.patience < 1 or config.batch_size < 1:
        raise ValueError("Epochs, patience, and batch size must be positive")
    if sha256_file(TRAIN_PATH) != TRAIN_SHA256 or sha256_file(VALIDATION_PATH) != VALIDATION_SHA256:
        raise ValueError("Train/validation CSV hash mismatch")
    train_rows, validation_rows = load_training_splits(TRAIN_PATH, VALIDATION_PATH, exclude_overlaps=True)
    if not config.smoke and {row["T3_label"] for row in train_rows} != set(LABEL_ORDER):
        raise ValueError("Full training split must cover all T3 classes")
    if config.smoke:
        train_rows = train_rows[:8]
        validation_rows = validation_rows[:8]
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.seed)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision=MODEL_REVISION, local_files_only=True)
    train_loader = DataLoader(Rows(train_rows, tokenizer), batch_size=min(config.batch_size, len(train_rows)), shuffle=True)
    validation_loader = DataLoader(Rows(validation_rows, tokenizer), batch_size=min(config.batch_size, len(validation_rows)))
    device = torch.device("cpu" if config.smoke else ("cuda" if torch.cuda.is_available() else "cpu"))
    if config.smoke:
        model_config = AutoConfig.from_pretrained(MODEL_NAME, revision=MODEL_REVISION, local_files_only=True)
        model_config.hidden_size = 64
        model_config.num_hidden_layers = 1
        model_config.num_attention_heads = 4
        model_config.intermediate_size = 128
        model_config.num_labels = len(LABEL_ORDER)
        model = AutoModelForSequenceClassification.from_config(model_config)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME, revision=MODEL_REVISION, local_files_only=True,
            num_labels=len(LABEL_ORDER),
        )
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=0.01)
    max_epochs = 1 if config.smoke else config.max_epochs
    best_f1 = -1.0
    best_epoch = 0
    wait = 0
    history = []
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / "t3_best.pt"
    for epoch in range(1, max_epochs + 1):
        model.train()
        losses = []
        for batch in train_loader:
            optimizer.zero_grad()
            output = model(**{key: value.to(device) for key, value in batch.items()})
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(output.loss.item()))
        model.eval()
        predicted, gold = [], []
        with torch.inference_mode():
            for batch in validation_loader:
                labels = batch.pop("labels")
                logits = model(**{key: value.to(device) for key, value in batch.items()}).logits
                predicted.extend(logits.argmax(dim=-1).cpu().tolist())
                gold.extend(labels.tolist())
        macro_f1 = float(f1_score(gold, predicted, average="macro", zero_division=0))
        history.append({"epoch": epoch, "train_loss": sum(losses) / len(losses), "validation_macro_f1": macro_f1})
        if macro_f1 > best_f1 + config.min_delta:
            best_f1, best_epoch, wait = macro_f1, epoch, 0
            torch.save(model.state_dict(), checkpoint)
        else:
            wait += 1
            if wait >= config.patience:
                break
    metadata = {
        "taxonomy": "T3",
        "label_order": list(LABEL_ORDER),
        "model_name": MODEL_NAME,
        "model_revision": MODEL_REVISION,
        "preprocessing": "raw_query",
        "max_length": 64,
        "seed": config.seed,
        "smoke": config.smoke,
        "production_eligible": not config.smoke,
        "configuration": {
            "seed": config.seed,
            "max_epochs": config.max_epochs,
            "effective_max_epochs": max_epochs,
            "patience": config.patience,
            "min_delta": config.min_delta,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "optimizer": "AdamW",
            "weight_decay": 0.01,
            "gradient_clip_norm": 1.0,
            "device": str(device),
            "torch_version": version("torch"),
            "transformers_version": version("transformers"),
            "numpy_version": version("numpy"),
            "scikit_learn_version": version("scikit-learn"),
        },
        "training_data": {"train_sha256": TRAIN_SHA256, "validation_sha256": VALIDATION_SHA256},
        "validation_rows_used": len(validation_rows),
        "validation_filter": "exclude_train_family_semantic_family_and_query_overlap",
        "selection": {"criterion": "validation_macro_f1_only", "best_epoch": best_epoch, "best_macro_f1": best_f1},
        "history": history,
        "checkpoint_path": checkpoint.name,
        "checkpoint_sha256": sha256_file(checkpoint),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--min-delta", type=float, default=0.001)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    args = parser.parse_args()
    result = train(TrainConfig(
        output_dir=args.output_dir, smoke=args.smoke, seed=args.seed,
        max_epochs=args.max_epochs, patience=args.patience, min_delta=args.min_delta,
        batch_size=args.batch_size, learning_rate=args.learning_rate,
    ))
    print(json.dumps({"output_dir": str(args.output_dir), "smoke": result["smoke"], "best_macro_f1": result["selection"]["best_macro_f1"]}))


if __name__ == "__main__":
    main()
