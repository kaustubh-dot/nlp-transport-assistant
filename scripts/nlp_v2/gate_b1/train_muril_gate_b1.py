#!/usr/bin/env python3
"""Google MuRIL Fine-Tuning Harness for NLP v2 Gate B.1 Hard-Boundary Taxonomy Stress Test.

Trains and evaluates:
- 2 Taxonomies: T2 (12 intents) vs T3 (16 intents)
- 3 Seeds: 42, 101, 777
Total = 6 MuRIL experiments.

Architecture: google/muril-base-cased with sequence classification head.
Features:
- BF16 mixed precision
- Early stopping (patience=3 epochs, min_delta=0.001 on validation Macro-F1)
- Evaluates best checkpoint on gate_b1_stress_eval.csv
- Token-masked and entity-masked diagnostic evaluations
- Logs metrics.json, confusion_matrix.json, and predictions.jsonl for every run
- Saves best model state_dict for downstream evaluation
"""

import os
import re
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
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b1")
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "gate_b1")
MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")
MODEL_NAME = "google/muril-base-cased"

with open(MAP_PATH, "r", encoding="utf-8") as f:
    TAX_SPEC = json.load(f)

ALLOWED_OPS = {"T2": defaultdict(set), "T3": defaultdict(set)}
for scen in TAX_SPEC["scenarios"]:
    op = scen["downstream_operation"]
    ALLOWED_OPS["T2"][scen["T2_label"]].add(op)
    ALLOWED_OPS["T3"][scen["T3_label"]].add(op)


class IntentDataset(Dataset):
    def __init__(self, rows, label_col, label_to_idx, tokenizer, max_len=64, text_transform=None):
        self.rows = rows
        self.label_col = label_col
        self.label_to_idx = label_to_idx
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

        label = self.label_to_idx[row[self.label_col]]
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


def load_split(split_name: str):
    path = os.path.join(DATA_DIR, f"gate_b1_{split_name}.csv")
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


# Common domain shortcut keywords to mask for token-masked diagnostic
DOMAIN_KEYWORDS = [
    r"\bfare\b", r"\bfares\b", r"\bticket\b", r"\btickets\b", r"\bkiraya\b", r"\bpass\b",
    r"\bfirst\b", r"\blast\b", r"\bfrequency\b", r"\binterval\b", r"\bheadway\b",
    r"\broute\b", r"\bstops?\b", r"\bsequence\b", r"\binterchange\b", r"\btransfer\b",
    r"\blift\b", r"\belevator\b", r"\bwheelchair\b", r"\brange\b", r"\bparking\b",
    r"\bpehle\b", r"\baakhri\b", r"\bkitne baje\b", r"\bgadi\b", r"\btrain\b", r"\bbus\b"
]
DOMAIN_KEYWORD_RE = re.compile("|".join(DOMAIN_KEYWORDS), re.IGNORECASE)


def token_mask_transform(row):
    """Replaces domain keywords with [MASK] to test shortcut resilience."""
    query = row["query"]
    return DOMAIN_KEYWORD_RE.sub("[MASK]", query)


def entity_mask_transform(row):
    """Replaces canonical entities and station/location names with [MASK]."""
    query = row["query"]
    entities_json = row.get("canonical_entities_json", "[]")
    try:
        entities = json.loads(entities_json)
    except Exception:
        entities = []

    masked_query = query
    for ent in entities:
        name = ent.get("name") or ent.get("matched_text")
        if name and len(name) > 2:
            masked_query = re.sub(re.escape(name), "[MASK]", masked_query, flags=re.IGNORECASE)

    return masked_query


def evaluate_model(model, dataloader, device):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
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
            probs = torch.softmax(logits, dim=-1).cpu().to(torch.float32).numpy()
            preds = np.argmax(probs, axis=-1)
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs)

    avg_loss = total_loss / len(dataloader.dataset)
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    acc = accuracy_score(all_labels, all_preds)
    return avg_loss, macro_f1, acc, all_preds, all_probs


def train_single_experiment(taxonomy: str, seed: int, batch_size=32, lr=3e-5, max_epochs=15, patience=3):
    exp_id = f"muril_{taxonomy}_seed{seed}"
    out_dir = os.path.join(EXP_DIR, exp_id)
    os.makedirs(out_dir, exist_ok=True)

    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_rows = load_split("train")
    val_rows = load_split("validation")
    eval_rows = load_split("stress_eval")

    label_col = "T2_label" if taxonomy == "T2" else "T3_label"
    classes = sorted(list(TAX_SPEC["taxonomies"][taxonomy]["intents"]))
    label_to_idx = {l: i for i, l in enumerate(classes)}

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_ds = IntentDataset(train_rows, label_col, label_to_idx, tokenizer)
    val_ds = IntentDataset(val_rows, label_col, label_to_idx, tokenizer)
    eval_ds = IntentDataset(eval_rows, label_col, label_to_idx, tokenizer)

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

    print(f"\n[{exp_id}] Starting MuRIL fine-tuning on {taxonomy} (max {max_epochs} epochs, patience {patience})...")

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
        val_loss, val_macro_f1, val_acc, _, _ = evaluate_model(model, val_loader, device)

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

    # Load best weights
    model.load_state_dict(best_weights)

    # Save best checkpoint
    torch.save(best_weights, os.path.join(out_dir, "best_model.pt"))

    # Standard evaluation on stress_eval
    eval_loss, eval_macro_f1, eval_acc, eval_preds, eval_probs = evaluate_model(model, eval_loader, device)

    y_eval_idx = [label_to_idx[r[label_col]] for r in eval_rows]
    weighted_f1 = float(f1_score(y_eval_idx, eval_preds, average="weighted", zero_division=0))
    per_class_f1_vals = f1_score(y_eval_idx, eval_preds, average=None, labels=range(len(classes)), zero_division=0)
    per_class_f1 = {classes[i]: float(per_class_f1_vals[i]) for i in range(len(classes))}
    cm = confusion_matrix(y_eval_idx, eval_preds, labels=range(len(classes))).tolist()

    # Predictions and operation compatibility
    predictions_records = []
    allowed = ALLOWED_OPS[taxonomy]
    compatible_op_count = 0

    for i, r in enumerate(eval_rows):
        pred_label = classes[eval_preds[i]]
        gold_label = r[label_col]
        gold_op = r["semantic_operation"]

        allowed_for_pred = allowed.get(pred_label, set())
        op_compatible = bool(gold_op in allowed_for_pred)
        if op_compatible:
            compatible_op_count += 1

        top_prob = float(eval_probs[i][eval_preds[i]])
        rec = {
            "utterance_id": r["utterance_id"],
            "query": r["query"],
            "clean_query": r.get("clean_query", r["query"]),
            "language": r.get("language", ""),
            "language_class": r.get("language_class", ""),
            "script": r.get("script", ""),
            "author_source": r.get("author_source", ""),
            "generation_method": r.get("generation_method", ""),
            "contrast_group_id": r.get("contrast_group_id", ""),
            "is_implicit": "implicit" in r.get("generation_method", "") or "implicit" in r.get("author_source", "") or "implicit" in r.get("family_id", ""),
            "is_ambiguous": r.get("ambiguity_type", "none") != "none" or r.get("clarification_required", "False") == "True",
            "clarification_required": r.get("clarification_required", "False") == "True",
            "ambiguity_type": r.get("ambiguity_type", "none"),
            "noise_level": r.get("noise_level", "N0"),
            "code_switch_level": r.get("code_switch_level", "CS0"),
            "gold_label": gold_label,
            "pred_label": pred_label,
            "gold_operation": gold_op,
            "intent_correct": bool(gold_label == pred_label),
            "op_compatible": op_compatible,
            "confidence": top_prob,
            "probs": {classes[j]: float(eval_probs[i][j]) for j in range(len(classes))}
        }
        predictions_records.append(rec)

    op_compat_acc = float(compatible_op_count / len(eval_rows))

    # Diagnostic 1: Token-masked evaluation
    print(f"[{exp_id}] Running token-masked diagnostic evaluation...")
    ds_token_masked = IntentDataset(eval_rows, label_col, label_to_idx, tokenizer, text_transform=token_mask_transform)
    loader_token_masked = DataLoader(ds_token_masked, batch_size=batch_size, shuffle=False)
    _, masked_macro_f1, masked_acc, _, _ = evaluate_model(model, loader_token_masked, device)

    # Diagnostic 2: Entity-masked evaluation
    print(f"[{exp_id}] Running entity-masked diagnostic evaluation...")
    ds_entity_masked = IntentDataset(eval_rows, label_col, label_to_idx, tokenizer, text_transform=entity_mask_transform)
    loader_entity_masked = DataLoader(ds_entity_masked, batch_size=batch_size, shuffle=False)
    _, entity_masked_macro_f1, entity_masked_acc, _, _ = evaluate_model(model, loader_entity_masked, device)

    metrics = {
        "experiment_id": exp_id,
        "model_family": "muril",
        "taxonomy": taxonomy,
        "seed": seed,
        "num_classes": len(classes),
        "train_samples": len(train_rows),
        "val_samples": len(val_rows),
        "eval_samples": len(eval_rows),
        "best_epoch": best_epoch,
        "best_val_macro_f1": float(best_val_macro_f1),
        "eval_loss": float(eval_loss),
        "accuracy": float(eval_acc),
        "macro_f1": float(eval_macro_f1),
        "weighted_f1": float(weighted_f1),
        "op_compatible_accuracy": float(op_compat_acc),
        "per_class_f1": per_class_f1,
        "diagnostics": {
            "token_masked": {
                "accuracy": float(masked_acc),
                "macro_f1": float(masked_macro_f1),
                "accuracy_drop": float(eval_acc - masked_acc),
                "macro_f1_drop": float(eval_macro_f1 - masked_macro_f1)
            },
            "entity_masked": {
                "accuracy": float(entity_masked_acc),
                "macro_f1": float(entity_masked_macro_f1),
                "accuracy_drop": float(eval_acc - entity_masked_acc),
                "macro_f1_drop": float(eval_macro_f1 - entity_masked_macro_f1)
            }
        }
    }

    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(out_dir, "confusion_matrix.json"), "w", encoding="utf-8") as f:
        json.dump({"classes": classes, "matrix": cm}, f, indent=2)

    with open(os.path.join(out_dir, "predictions.jsonl"), "w", encoding="utf-8") as f:
        for rec in predictions_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[{exp_id}] Finished! Acc: {eval_acc:.4f}, Macro-F1: {eval_macro_f1:.4f}, OpCompat: {op_compat_acc:.4f} (Best epoch {best_epoch})")
    print(f"[{exp_id}] Token-masked drop: {eval_macro_f1 - masked_macro_f1:.4f}, Entity-masked drop: {eval_macro_f1 - entity_masked_macro_f1:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--taxonomy", type=str, choices=["T2", "T3", "all"], default="all")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 101, 777])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--max-epochs", type=int, default=15)
    parser.add_argument("--patience", type=int, default=3)
    args = parser.parse_args()

    taxonomies = ["T2", "T3"] if args.taxonomy == "all" else [args.taxonomy]
    total_runs = len(taxonomies) * len(args.seeds)
    print(f"Starting MuRIL Gate B.1 fine-tuning: {total_runs} total runs planned...")

    all_metrics = []
    for tax in taxonomies:
        for seed in args.seeds:
            m = train_single_experiment(
                tax, seed,
                batch_size=args.batch_size,
                lr=args.lr,
                max_epochs=args.max_epochs,
                patience=args.patience
            )
            all_metrics.append(m)

    print(f"\nAll {len(all_metrics)} MuRIL runs completed successfully!")


if __name__ == "__main__":
    main()
