#!/usr/bin/env python3
"""Trains the Capacity-Matched T2-H Multitask MuRIL Model for Gate B.2.

Architecture:
- Backbone: google/muril-base-cased (shared encoder)
- Head 1: 12-class T2 intent classification
- Head 2: 16-class semantic subtype classification
- Loss: L_intent + lambda_subtype * L_subtype (lambda_subtype = 1.0)
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
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, f1_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "gate_b2")
MODEL_NAME = "google/muril-base-cased"

os.makedirs(EXP_DIR, exist_ok=True)

T2_CLASSES = [
    "route_query", "service_timing", "route_stops", "service_availability",
    "fare_query", "ticketing_rules", "station_facilities", "accessibility",
    "interchange_query", "nearest_transport", "realtime_status_query", "out_of_scope"
]

SUBTYPE_CLASSES = [
    "point_to_point", "explicit_multimodal", "first_last", "frequency",
    "scheduled_departure", "sequence", "membership", "availability",
    "fare", "ticketing", "facilities", "accessibility", "interchange",
    "nearest", "realtime", "out_of_scope"
]

T2_TO_IDX = {c: i for i, c in enumerate(T2_CLASSES)}
SUBTYPE_TO_IDX = {c: i for i, c in enumerate(SUBTYPE_CLASSES)}

def resolve_operation(t2_intent: str, subtype: str) -> str:
    """Maps T2 intent + subtype to exact atomic downstream operation."""
    if t2_intent == "route_query":
        return "PLAN_MULTIMODAL_ROUTE" if subtype == "explicit_multimodal" else "PLAN_ROUTE"
    elif t2_intent == "route_stops":
        return "CHECK_STOP_ON_ROUTE" if subtype == "membership" else "LIST_ROUTE_STOPS"
    elif t2_intent == "service_timing":
        if subtype == "first_last":
            return "GET_FIRST_LAST_SERVICE"
        elif subtype == "frequency":
            return "GET_SERVICE_FREQUENCY"
        else:
            return "GET_SCHEDULED_DEPARTURES"
    elif t2_intent == "service_availability":
        return "CHECK_SERVICE_AVAILABILITY"
    elif t2_intent == "fare_query":
        return "CALCULATE_FARE"
    elif t2_intent == "ticketing_rules":
        return "GET_TICKETING_POLICY"
    elif t2_intent == "station_facilities":
        return "GET_STATION_FACILITY"
    elif t2_intent == "accessibility":
        return "GET_ACCESSIBILITY_INFO"
    elif t2_intent == "interchange_query":
        return "GET_INTERCHANGE_DETAILS"
    elif t2_intent == "nearest_transport":
        return "FIND_NEAREST_STATION"
    elif t2_intent == "realtime_status_query":
        return "REJECT_UNSUPPORTED_REALTIME"
    elif t2_intent == "out_of_scope":
        return "REJECT_OUT_OF_SCOPE"
    return "REJECT_OUT_OF_SCOPE"


class MultitaskDataset(Dataset):
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

        t2_idx = T2_TO_IDX[row["T2_label"]]
        st_idx = SUBTYPE_TO_IDX[row["semantic_subtype"]]

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
            "t2_label": torch.tensor(t2_idx, dtype=torch.long),
            "subtype_label": torch.tensor(st_idx, dtype=torch.long),
            "utterance_id": row["utterance_id"]
        }


class MultitaskMurilT2H(nn.Module):
    def __init__(self, model_name: str, num_t2: int = 12, num_subtype: int = 16):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(0.1)
        self.t2_head = nn.Linear(hidden_size, num_t2)
        self.subtype_head = nn.Linear(hidden_size, num_subtype)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_rep = outputs[0][:, 0, :]
        cls_rep = self.dropout(cls_rep)
        t2_logits = self.t2_head(cls_rep)
        subtype_logits = self.subtype_head(cls_rep)
        return t2_logits, subtype_logits


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


def train_t2h(seed: int, max_epochs: int = 30, patience: int = 3, min_delta: float = 0.001, lr: float = 2e-5, batch_size: int = 16, lambda_subtype: float = 1.0):
    print(f"\n{'='*70}\nStarting T2-H Multitask Training (Seed {seed})\n{'='*70}")
    set_seed(seed)
    start_time = time.time()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_rows = load_split("train")
    val_rows = load_split("validation")
    stress_rows = load_split("stress_eval")

    train_ds = MultitaskDataset(train_rows, tokenizer)
    val_ds = MultitaskDataset(val_rows, tokenizer)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = MultitaskMurilT2H(MODEL_NAME, num_t2=len(T2_CLASSES), num_subtype=len(SUBTYPE_CLASSES)).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * max_epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)

    criterion = nn.CrossEntropyLoss()

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
            t2_labels = batch["t2_label"].to(device)
            st_labels = batch["subtype_label"].to(device)

            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                t2_logits, st_logits = model(input_ids, attention_mask)
                loss_t2 = criterion(t2_logits, t2_labels)
                loss_st = criterion(st_logits, st_labels)
                loss = loss_t2 + lambda_subtype * loss_st

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)

        # Validation
        model.eval()
        val_t2_preds, val_t2_golds = [], []
        val_st_preds, val_st_golds = [], []
        val_op_preds, val_op_golds = [], []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                t2_labels = batch["t2_label"].to(device)
                st_labels = batch["subtype_label"].to(device)

                with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                    t2_logits, st_logits = model(input_ids, attention_mask)

                p_t2 = torch.argmax(t2_logits, dim=-1).cpu().tolist()
                p_st = torch.argmax(st_logits, dim=-1).cpu().tolist()
                g_t2 = t2_labels.cpu().tolist()
                g_st = st_labels.cpu().tolist()

                val_t2_preds.extend(p_t2)
                val_t2_golds.extend(g_t2)
                val_st_preds.extend(p_st)
                val_st_golds.extend(g_st)

                for t2_idx, st_idx, gt2_idx, gst_idx in zip(p_t2, p_st, g_t2, g_st):
                    pred_op = resolve_operation(T2_CLASSES[t2_idx], SUBTYPE_CLASSES[st_idx])
                    gold_op = resolve_operation(T2_CLASSES[gt2_idx], SUBTYPE_CLASSES[gst_idx])
                    val_op_preds.append(pred_op)
                    val_op_golds.append(gold_op)

        val_t2_f1 = f1_score(val_t2_golds, val_t2_preds, average="macro")
        val_st_f1 = f1_score(val_st_golds, val_st_preds, average="macro")
        val_op_acc = accuracy_score(val_op_golds, val_op_preds)
        val_op_f1 = f1_score(val_op_golds, val_op_preds, average="macro")

        print(f"Epoch {epoch:02d}/{max_epochs:02d} | Train Loss: {avg_train_loss:.4f} | Val T2-F1: {val_t2_f1:.4f} | Val Subtype-F1: {val_st_f1:.4f} | Val Op Acc: {val_op_acc:.4f} | Val Op F1: {val_op_f1:.4f}")

        history.append({
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_t2_f1": val_t2_f1,
            "val_subtype_f1": val_st_f1,
            "val_op_acc": val_op_acc,
            "val_op_f1": val_op_f1
        })

        if val_op_f1 > best_val_f1 + min_delta:
            best_val_f1 = val_op_f1
            best_epoch = epoch
            best_weights = copy.deepcopy(model.state_dict())
            no_improve_epochs = 0
        else:
            no_improve_epochs += 1
            if no_improve_epochs >= patience:
                print(f"Early stopping triggered at epoch {epoch}. Best epoch was {best_epoch} with Val Op-F1: {best_val_f1:.4f}")
                early_stopped = True
                break

    stopping_epoch = epoch
    print(f"Restoring best checkpoint from epoch {best_epoch}...")
    model.load_state_dict(best_weights)

    # Save model state dict
    ckpt_path = os.path.join(EXP_DIR, f"t2h_muril_seed{seed}_best.pt")
    torch.save(best_weights, ckpt_path)

    # Evaluate on stress_eval
    stress_ds = MultitaskDataset(stress_rows, tokenizer)
    stress_loader = DataLoader(stress_ds, batch_size=batch_size, shuffle=False)

    model.eval()
    all_predictions = []

    with torch.no_grad():
        row_idx = 0
        for batch in stress_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                t2_logits, st_logits = model(input_ids, attention_mask)

            t2_probs = torch.softmax(t2_logits, dim=-1).cpu()
            st_probs = torch.softmax(st_logits, dim=-1).cpu()

            t2_preds = torch.argmax(t2_probs, dim=-1).tolist()
            st_preds = torch.argmax(st_probs, dim=-1).tolist()

            for i in range(len(t2_preds)):
                row = stress_rows[row_idx]
                row_idx += 1

                pred_t2 = T2_CLASSES[t2_preds[i]]
                pred_st = SUBTYPE_CLASSES[st_preds[i]]
                pred_op = resolve_operation(pred_t2, pred_st)

                gold_t2 = row["T2_label"]
                gold_st = row["semantic_subtype"]
                gold_op = row["semantic_operation"]

                conf_t2 = float(t2_probs[i][t2_preds[i]])
                conf_st = float(st_probs[i][st_preds[i]])
                confidence = float(conf_t2 * conf_st)

                exact_op_correct = (pred_op == gold_op)
                intent_correct = (pred_t2 == gold_t2)

                sec_labels = json.loads(row.get("acceptable_secondary_labels", "[]"))
                ambig_correct = exact_op_correct or (pred_t2 in sec_labels) or (pred_op in sec_labels)

                pred_record = {
                    "experiment_id": f"muril_t2h_seed{seed}",
                    "architecture": "multitask_shared_encoder",
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
                    "gold_T2_intent": gold_t2,
                    "pred_T2_intent": pred_t2,
                    "gold_subtype": gold_st,
                    "pred_subtype": pred_st,
                    "gold_T3_intent": row["T3_label"],
                    "pred_T3_intent": None,
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

    pred_out_path = os.path.join(EXP_DIR, f"predictions_t2h_muril_seed{seed}.jsonl")
    with open(pred_out_path, "w", encoding="utf-8") as f:
        for p in all_predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    runtime = time.time() - start_time
    print(f"T2-H Seed {seed} completed in {runtime:.1f}s. Saved {len(all_predictions)} predictions to {pred_out_path}")

    summary = {
        "seed": seed,
        "taxonomy": "T2-H",
        "architecture": "shared_encoder_multitask",
        "epochs_completed": len(history),
        "best_epoch": best_epoch,
        "stopping_epoch": stopping_epoch,
        "early_stop_triggered": early_stopped,
        "distance_from_ceiling": max_epochs - best_epoch,
        "best_val_op_f1": best_val_f1,
        "runtime_seconds": runtime,
        "checkpoint_path": ckpt_path,
        "predictions_path": pred_out_path,
        "history": history
    }

    sum_out_path = os.path.join(EXP_DIR, f"metrics_t2h_muril_seed{seed}.json")
    with open(sum_out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=3)
    args = parser.parse_args()

    train_t2h(seed=args.seed, max_epochs=args.max_epochs, patience=args.patience)
