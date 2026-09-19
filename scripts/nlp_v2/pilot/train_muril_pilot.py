#!/usr/bin/env python3
"""Google MuRIL Fine-Tuning Harness for NLP v2 Gate B.

Trains and evaluates 18 configurations:
3 Taxonomies (T1, T2, T3) x 2 Regimes (Regime A, Regime B) x 3 Seeds (42, 101, 777).
Architecture: google/muril-base-cased with sequence classification head.
Features:
- BF16 mixed precision
- Early stopping (patience=3 epochs, min_delta=0.001 on validation Macro-F1)
- Evaluates best checkpoint on pilot_eval.csv
- Logs metrics.json, confusion_matrix.json, and predictions.jsonl for every run.
"""

import os
import csv
import copy
import json
import random
import argparse
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "pilot")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "taxonomy_pilot")
MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")
MODEL_NAME = "google/muril-base-cased"

with open(MAP_PATH, "r", encoding="utf-8") as f:
    TAX_SPEC = json.load(f)

ALLOWED_OPS = {"T1": defaultdict(set), "T2": defaultdict(set), "T3": defaultdict(set)}
for scen in TAX_SPEC["scenarios"]:
    op = scen["downstream_operation"]
    ALLOWED_OPS["T1"][scen["T1_label"]].add(op)
    ALLOWED_OPS["T2"][scen["T2_label"]].add(op)
    ALLOWED_OPS["T3"][scen["T3_label"]].add(op)


class IntentDataset(Dataset):
    def __init__(self, rows, label_to_idx, tokenizer, max_len=64):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.label_to_idx = label_to_idx

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        text = row["query"]
        label = self.label_to_idx[row["taxonomy_label"]]
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
            "utterance_id": row["utterance_id"]
        }


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_split(split_path: str):
    rows = []
    with open(split_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def evaluate_model(model, dataloader, device):
    model.eval()
    all_preds = []
    all_labels = []
    total_loss = 0.0

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss
                logits = outputs.logits

            total_loss += loss.item() * len(labels)
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(dataloader.dataset)
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    acc = accuracy_score(all_labels, all_preds)
    return avg_loss, macro_f1, acc, all_preds


def train_single_experiment(regime: str, taxonomy: str, seed: int, batch_size=32, lr=3e-5, max_epochs=15, patience=3):
    exp_id = f"{regime}_{taxonomy}_muril_seed{seed}"
    out_dir = os.path.join(EXP_DIR, exp_id)
    os.makedirs(out_dir, exist_ok=True)

    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    data_dir = os.path.join(DATA_DIR, regime, taxonomy)
    train_rows = load_split(os.path.join(data_dir, "pilot_train.csv"))
    val_rows = load_split(os.path.join(data_dir, "pilot_validation.csv"))
    eval_rows = load_split(os.path.join(data_dir, "pilot_eval.csv"))

    classes = sorted(list(TAX_SPEC["taxonomies"][taxonomy]["intents"]))
    label_to_idx = {l: i for i, l in enumerate(classes)}

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_ds = IntentDataset(train_rows, label_to_idx, tokenizer)
    val_ds = IntentDataset(val_rows, label_to_idx, tokenizer)
    eval_ds = IntentDataset(eval_rows, label_to_idx, tokenizer)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    eval_loader = DataLoader(eval_ds, batch_size=batch_size, shuffle=False)

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=len(classes))
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * max_epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    best_val_macro_f1 = -1.0
    best_weights = None
    epochs_no_improve = 0
    min_delta = 0.001
    best_epoch = 0

    print(f"\n[{exp_id}] Starting fine-tuning (max {max_epochs} epochs, patience {patience})...")

    for epoch in range(1, max_epochs + 1):
        model.train()
        train_loss = 0.0

        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            optimizer.zero_grad()
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            train_loss += loss.item() * len(labels)

        avg_train_loss = train_loss / len(train_ds)
        val_loss, val_macro_f1, val_acc, _ = evaluate_model(model, val_loader, device)

        print(f"[{exp_id}] Epoch {epoch}/{max_epochs} - Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}, Val Macro-F1: {val_macro_f1:.4f}")

        if val_macro_f1 - best_val_macro_f1 > min_delta:
            best_val_macro_f1 = val_macro_f1
            best_weights = copy.deepcopy(model.state_dict())
            epochs_no_improve = 0
            best_epoch = epoch
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"[{exp_id}] Early stopping triggered at epoch {epoch} (Best epoch {best_epoch} with Val Macro-F1: {best_val_macro_f1:.4f})")
                break

    # Load best weights and evaluate on pilot_eval
    model.load_state_dict(best_weights)
    eval_loss, eval_macro_f1, eval_acc, eval_preds = evaluate_model(model, eval_loader, device)

    y_eval_idx = [label_to_idx[r["taxonomy_label"]] for r in eval_rows]
    weighted_f1 = float(f1_score(y_eval_idx, eval_preds, average="weighted", zero_division=0))
    per_class_f1_vals = f1_score(y_eval_idx, eval_preds, average=None, labels=range(len(classes)), zero_division=0)
    per_class_f1 = {classes[i]: float(per_class_f1_vals[i]) for i in range(len(classes))}
    cm = confusion_matrix(y_eval_idx, eval_preds, labels=range(len(classes))).tolist()

    # Downstream semantic operation accuracy
    correct_op_count = 0
    predictions_records = []
    allowed = ALLOWED_OPS[taxonomy]

    for i, r in enumerate(eval_rows):
        pred_label = classes[eval_preds[i]]
        gold_label = r["taxonomy_label"]
        gold_op = r["semantic_operation"]

        allowed_for_pred = allowed.get(pred_label, set())
        op_correct = bool(gold_op in allowed_for_pred)
        if op_correct:
            correct_op_count += 1

        rec = {
            "utterance_id": r["utterance_id"],
            "query": r["query"],
            "language": r["language"],
            "script": r["script"],
            "gold_label": gold_label,
            "pred_label": pred_label,
            "gold_operation": gold_op,
            "op_correct": op_correct,
            "intent_correct": bool(gold_label == pred_label)
        }
        predictions_records.append(rec)

    semantic_op_accuracy = float(correct_op_count / len(eval_rows))

    metrics = {
        "experiment_id": exp_id,
        "model_family": "muril",
        "regime": regime,
        "taxonomy": taxonomy,
        "seed": seed,
        "best_epoch": best_epoch,
        "num_classes": len(classes),
        "train_samples": len(train_rows),
        "val_samples": len(val_rows),
        "eval_samples": len(eval_rows),
        "accuracy": float(eval_acc),
        "macro_f1": float(eval_macro_f1),
        "weighted_f1": weighted_f1,
        "semantic_op_accuracy": semantic_op_accuracy,
        "per_class_f1": per_class_f1
    }

    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(out_dir, "confusion_matrix.json"), "w", encoding="utf-8") as f:
        json.dump({"classes": classes, "matrix": cm}, f, indent=2)

    with open(os.path.join(out_dir, "predictions.jsonl"), "w", encoding="utf-8") as f:
        for rec in predictions_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[{exp_id} COMPLETED] Best Epoch: {best_epoch}, Acc: {eval_acc:.4f}, Macro-F1: {eval_macro_f1:.4f}, SemOp-Acc: {semantic_op_accuracy:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regime", type=str, choices=["regime_a", "regime_b", "all"], default="all")
    parser.add_argument("--taxonomy", type=str, choices=["T1", "T2", "T3", "all"], default="all")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 101, 777])
    args = parser.parse_args()

    regimes = ["regime_a", "regime_b"] if args.regime == "all" else [args.regime]
    taxonomies = ["T1", "T2", "T3"] if args.taxonomy == "all" else [args.taxonomy]

    total_runs = len(regimes) * len(taxonomies) * len(args.seeds)
    print(f"Starting MuRIL Pilot runs: {total_runs} total runs planned...")

    all_metrics = []
    for reg in regimes:
        for tax in taxonomies:
            for seed in args.seeds:
                m = train_single_experiment(reg, tax, seed)
                all_metrics.append(m)

    print(f"\nAll {len(all_metrics)} MuRIL pilot runs successfully completed!")


if __name__ == "__main__":
    main()
