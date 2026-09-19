#!/usr/bin/env python3
"""Trains the 16-Class T3 Direct Classifier MuRIL Model for Gate B.2.

Architecture:
- Backbone: google/muril-base-cased (16-class direct sequence classifier)
- max_epochs = 30, patience = 3, min_delta = 0.001
- Seeds: [42, 101, 777]
- BF16 mixed precision on GPU
"""

import os
import sys
import csv
import copy
import json
import time
import random
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, f1_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "gate_b2")
MODEL_NAME = "google/muril-base-cased"
MODEL_REVISION = "afd9f36c7923d54e97903922ff1b260d091d202f"

os.makedirs(EXP_DIR, exist_ok=True)

T3_CLASSES = [
    "point_to_point_route", "multimodal_route", "first_and_last_service",
    "service_frequency", "scheduled_departure", "route_stop_sequence",
    "route_stop_membership", "mode_availability", "fare_calculation",
    "ticketing_and_passes", "station_facilities", "station_accessibility",
    "interchange_transfer", "nearest_transport", "realtime_status_query", "out_of_scope"
]

T3_TO_OP = {
    "point_to_point_route": "PLAN_ROUTE",
    "multimodal_route": "PLAN_MULTIMODAL_ROUTE",
    "first_and_last_service": "GET_FIRST_LAST_SERVICE",
    "service_frequency": "GET_SERVICE_FREQUENCY",
    "scheduled_departure": "GET_SCHEDULED_DEPARTURES",
    "route_stop_sequence": "LIST_ROUTE_STOPS",
    "route_stop_membership": "CHECK_STOP_ON_ROUTE",
    "mode_availability": "CHECK_SERVICE_AVAILABILITY",
    "fare_calculation": "CALCULATE_FARE",
    "ticketing_and_passes": "GET_TICKETING_POLICY",
    "station_facilities": "GET_STATION_FACILITY",
    "station_accessibility": "GET_ACCESSIBILITY_INFO",
    "interchange_transfer": "GET_INTERCHANGE_DETAILS",
    "nearest_transport": "FIND_NEAREST_STATION",
    "realtime_status_query": "REJECT_UNSUPPORTED_REALTIME",
    "out_of_scope": "REJECT_OUT_OF_SCOPE"
}

T3_TO_IDX = {c: i for i, c in enumerate(T3_CLASSES)}


class T3Dataset(Dataset):
    def __init__(self, rows, tokenizer, max_len=64, text_transform=None):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.text_transform = text_transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        text = row["query"]
        if self.text_transform:
            text = self.text_transform(row)

        t3_idx = T3_TO_IDX[row["T3_label"]]

        enc = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt"
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "label": torch.tensor(t3_idx, dtype=torch.long),
            "utterance_id": row["utterance_id"]
        }


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_split(split_name: str):
    path = os.path.join(DATA_DIR, f"gate_b2_{split_name}.csv")
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def train_t3(seed: int, max_epochs: int = 30, patience: int = 3, min_delta: float = 0.001, lr: float = 2e-5, batch_size: int = 16):
    print(f"\n{'='*70}\nStarting T3 Fine Direct Training (Seed {seed})\n{'='*70}")
    set_seed(seed)
    start_time = time.time()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)
    train_rows = load_split("train")
    val_rows = load_split("validation")
    stress_rows = load_split("stress_eval")

    train_ds = T3Dataset(train_rows, tokenizer)
    val_ds = T3Dataset(val_rows, tokenizer)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        revision=MODEL_REVISION,
        num_labels=len(T3_CLASSES)
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * max_epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)

    best_val_f1 = -1.0
    best_epoch = -1
    best_weights = None
    no_improve_epochs = 0
    early_stopped = False

    history = []

    for epoch in range(1, max_epochs + 1):
        model.train()
        total_loss = 0.0

        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)

        # Validation
        model.eval()
        val_preds, val_golds = [], []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["label"].to(device)

                with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                    logits = outputs.logits

                preds = torch.argmax(logits, dim=-1).cpu().tolist()
                val_preds.extend(preds)
                val_golds.extend(labels.cpu().tolist())

        val_acc = accuracy_score(val_golds, val_preds)
        val_f1 = f1_score(val_golds, val_preds, average="macro")

        print(f"Epoch {epoch:02d}/{max_epochs:02d} | Train Loss: {avg_train_loss:.4f} | Val T3 Acc: {val_acc:.4f} | Val T3 Macro-F1: {val_f1:.4f}")

        history.append({
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_acc": val_acc,
            "val_macro_f1": val_f1
        })

        if val_f1 > best_val_f1 + min_delta:
            best_val_f1 = val_f1
            best_epoch = epoch
            best_weights = copy.deepcopy(model.state_dict())
            no_improve_epochs = 0
        else:
            no_improve_epochs += 1
            if no_improve_epochs >= patience:
                print(f"Early stopping triggered at epoch {epoch}. Best epoch was {best_epoch} with Val Macro-F1: {best_val_f1:.4f}")
                early_stopped = True
                break

    stopping_epoch = epoch
    print(f"Restoring best checkpoint from epoch {best_epoch}...")
    model.load_state_dict(best_weights)

    # Save checkpoint
    ckpt_path = os.path.join(EXP_DIR, f"t3_muril_seed{seed}_best.pt")
    torch.save(best_weights, ckpt_path)

    # Predict on stress_eval
    stress_ds = T3Dataset(stress_rows, tokenizer)
    stress_loader = DataLoader(stress_ds, batch_size=batch_size, shuffle=False)

    model.eval()
    all_predictions = []

    with torch.no_grad():
        row_idx = 0
        for batch in stress_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits

            probs = torch.softmax(logits, dim=-1).cpu()
            preds = torch.argmax(probs, dim=-1).tolist()

            for i in range(len(preds)):
                row = stress_rows[row_idx]
                row_idx += 1

                pred_t3 = T3_CLASSES[preds[i]]
                pred_op = T3_TO_OP[pred_t3]

                gold_t3 = row["T3_label"]
                gold_op = row["semantic_operation"]

                confidence = float(probs[i][preds[i]])
                exact_op_correct = (pred_op == gold_op)
                intent_correct = (pred_t3 == gold_t3)

                sec_labels = json.loads(row.get("acceptable_secondary_labels", "[]"))
                ambig_correct = exact_op_correct or (pred_t3 in sec_labels) or (pred_op in sec_labels)

                pred_record = {
                    "experiment_id": f"muril_t3_seed{seed}",
                    "architecture": "direct_sequence_classification",
                    "seed": seed,
                    "utterance_id": row["utterance_id"],
                    "semantic_scenario_id": row["semantic_scenario_id"],
                    "contrast_group_id": row.get("contrast_group_id", ""),
                    "query": row["query"],
                    "clean_query": row["clean_query"],
                    "language_class": row["language_class"],
                    "script": row["script"],
                    "code_switch_level": row["code_switch_level"],
                    "noise_level": row["noise_level"],
                    "gold_T2_intent": row["T2_label"],
                    "pred_T2_intent": None,
                    "gold_subtype": row["semantic_subtype"],
                    "pred_subtype": None,
                    "gold_T3_intent": gold_t3,
                    "pred_T3_intent": pred_t3,
                    "gold_operation": gold_op,
                    "pred_operation": pred_op,
                    "exact_operation_correct": exact_op_correct,
                    "intent_correct": intent_correct,
                    "clarification_required": (str(row.get("clarification_required", "")).lower() == "true"),
                    "acceptable_secondary_labels": sec_labels,
                    "ambiguity_aware_correct": ambig_correct,
                    "confidence": confidence,
                    "canonical_entities_json": row.get("canonical_entities_json", "[]"),
                    "author_source": row.get("author_source", "")
                }
                all_predictions.append(pred_record)

    pred_out_path = os.path.join(EXP_DIR, f"predictions_t3_muril_seed{seed}.jsonl")
    with open(pred_out_path, "w", encoding="utf-8") as f:
        for p in all_predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    runtime = time.time() - start_time
    print(f"T3 Seed {seed} completed in {runtime:.1f}s. Saved {len(all_predictions)} predictions to {pred_out_path}")

    summary = {
        "seed": seed,
        "taxonomy": "T3",
        "architecture": "direct_classifier",
        "epochs_completed": len(history),
        "best_epoch": best_epoch,
        "stopping_epoch": stopping_epoch,
        "early_stop_triggered": early_stopped,
        "distance_from_ceiling": max_epochs - best_epoch,
        "best_val_macro_f1": best_val_f1,
        "runtime_seconds": runtime,
        "checkpoint_path": ckpt_path,
        "predictions_path": pred_out_path,
        "history": history
    }

    sum_out_path = os.path.join(EXP_DIR, f"metrics_t3_muril_seed{seed}.json")
    with open(sum_out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=3)
    args = parser.parse_args()

    train_t3(seed=args.seed, max_epochs=args.max_epochs, patience=args.patience)
