#!/usr/bin/env python3
"""Multi-Model GPU Training and Benchmarking Harness for Chennai Transport Assistant.

Trains, evaluates, and compares candidate architectures on intent classification:
  1. Baseline: TF-IDF + LogisticRegression
  2. Google MuRIL (google/muril-base-cased)
  3. AI4Bharat IndicBERT v2 (ai4bharat/IndicBERTv2-MLM-only)
  4. Meta XLM-RoBERTa (xlm-roberta-base)
  5. Sentence-Transformers MiniLM (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
  6. L3Cube HingBERT (l3cube-pune/hing-bert)
  7. Microsoft mDeBERTa-v3 (microsoft/mdeberta-v3-base)
  8. AI4Bharat IndicBERT v1 (ai4bharat/indic-bert)

Protocol:
  - Frozen 70/15/15 family-disjoint dataset split
  - Early stopping on Validation Macro-F1 (patience=3, min_delta=0.001)
  - Max epochs = 15 ceiling (restoring best validation checkpoint)
  - Native BF16 mixed precision on NVIDIA RTX 4000 Ada GPU
  - Standardized latency measurement (30 warmup + 100 timed queries, batch_size=1, CUDA sync)
"""

import os
import sys
import time
import json
import random
import pickle
import argparse
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd

import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.intent_classifier import INTENT_CLASSES
from src.normalization import normalize_text

DEFAULT_SPLIT_DIR = os.path.join(BASE_DIR, "data", "processed", "split")
DATASET_PATH = os.path.join(BASE_DIR, "data", "processed", "intents.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

LABEL2ID = {label: i for i, label in enumerate(INTENT_CLASSES)}
ID2LABEL = {i: label for i, label in enumerate(INTENT_CLASSES)}

MODEL_REGISTRY = {
    "baseline": {
        "type": "sklearn",
        "name": "TF-IDF + Logistic Regression",
        "description": "Word (1-3) & Char (2-5) n-grams with L2 regularized Logistic Regression",
        "output_dir": os.path.join(MODELS_DIR, "baseline")
    },
    "muril": {
        "type": "transformer",
        "hf_id": "google/muril-base-cased",
        "name": "Google MuRIL",
        "description": "Pretrained on 17 Indian languages and transliterated Hinglish (Google)",
        "output_dir": os.path.join(MODELS_DIR, "muril")
    },
    "indicbert_v2": {
        "type": "transformer",
        "hf_id": "ai4bharat/IndicBERTv2-MLM-only",
        "name": "AI4Bharat IndicBERT v2",
        "description": "Trained on IndicCorp v2 (20.9B tokens, 24 languages, AI4Bharat)",
        "output_dir": os.path.join(MODELS_DIR, "indicbert_v2")
    },
    "indicbert": {
        "type": "transformer",
        "hf_id": "ai4bharat/indic-bert",
        "name": "AI4Bharat IndicBERT v1",
        "description": "Parameter-efficient ALBERT model for Indian languages (AI4Bharat)",
        "output_dir": os.path.join(MODELS_DIR, "indicbert")
    },
    "hingbert": {
        "type": "transformer",
        "hf_id": "l3cube-pune/hing-bert",
        "name": "L3Cube HingBERT",
        "description": "Trained on Romanized Hindi-English conversational corpus (L3Cube)",
        "output_dir": os.path.join(MODELS_DIR, "hingbert")
    },
    "xlm_roberta": {
        "type": "transformer",
        "hf_id": "xlm-roberta-base",
        "name": "Meta XLM-RoBERTa",
        "description": "Cross-lingual multilingual model covering 100 languages (Meta)",
        "output_dir": os.path.join(MODELS_DIR, "xlm_roberta")
    },
    "mdeberta": {
        "type": "transformer",
        "hf_id": "microsoft/mdeberta-v3-base",
        "name": "Microsoft mDeBERTa-v3",
        "description": "Disentangled attention multilingual encoder (Microsoft)",
        "output_dir": os.path.join(MODELS_DIR, "mdeberta")
    },
    "minilm": {
        "type": "transformer",
        "hf_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "name": "Multilingual MiniLM (Full FT)",
        "description": "paraphrase-multilingual-MiniLM-L12-v2 encoder adapted for 7-class sequence classification and fine-tuned end-to-end",
        "output_dir": os.path.join(MODELS_DIR, "minilm")
    }
}


def set_seed(seed: int):
    """Sets random seeds across Python, NumPy, PyTorch, and CUDA for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class IntentTextDataset(Dataset):
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_len: int = 128):
        encodings = tokenizer(
            [str(t) for t in texts],
            truncation=True,
            padding="max_length",
            max_length=max_len,
            return_tensors="pt"
        )
        self.input_ids = encodings["input_ids"]
        self.attention_mask = encodings["attention_mask"]
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            "input_ids": self.input_ids[idx],
            "attention_mask": self.attention_mask[idx],
            "labels": self.labels[idx]
        }


def load_splits(split_dir: str = DEFAULT_SPLIT_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads train, validation, and test splits from the frozen split directory or fallbacks to intents.csv."""
    train_path = os.path.join(split_dir, "train.csv")
    val_path = os.path.join(split_dir, "validation.csv")
    test_path = os.path.join(split_dir, "test.csv")

    if os.path.exists(train_path) and os.path.exists(val_path) and os.path.exists(test_path):
        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)
        return train_df, val_df, test_df

    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH)
        train_df = df[df["split"] == "train"].copy().reset_index(drop=True)
        val_df = df[df["split"] == "val"].copy().reset_index(drop=True)
        test_df = df[df["split"] == "test"].copy().reset_index(drop=True)
        return train_df, val_df, test_df

    raise FileNotFoundError(f"Neither frozen split at {split_dir} nor dataset at {DATASET_PATH} found.")


def benchmark_baseline_latency(model, vectorizer, queries: List[str]) -> Dict[str, float]:
    """Measures single-query (batch=1) inference latency for baseline model."""
    sample_queries = queries[:150] if len(queries) >= 150 else queries * (150 // max(1, len(queries)) + 1)
    
    # Warmup
    for q in sample_queries[:30]:
        _ = model.predict(vectorizer.transform([q]))

    # Measured runs (100 queries, batch_size=1)
    latencies = []
    for q in sample_queries[30:130]:
        t0 = time.perf_counter()
        _ = model.predict(vectorizer.transform([q]))
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    return {
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "median_latency_ms": round(float(np.median(latencies)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2)
    }


def benchmark_transformer_latency(model, tokenizer, queries: List[str], device: torch.device, use_bf16: bool) -> Dict[str, float]:
    """Measures single-query (batch=1) inference latency for transformer model with CUDA sync."""
    amp_dtype = torch.bfloat16 if use_bf16 else torch.float16
    sample_queries = queries[:150] if len(queries) >= 150 else queries * (150 // max(1, len(queries)) + 1)

    model.eval()

    # GPU warmup (30 queries)
    with torch.inference_mode():
        for q in sample_queries[:30]:
            inputs = tokenizer(q, return_tensors="pt", truncation=True, max_length=128, padding=True).to(device)
            if device.type == "cuda":
                with torch.amp.autocast('cuda', dtype=amp_dtype):
                    _ = model(**inputs)
            else:
                _ = model(**inputs)
        if device.type == "cuda":
            torch.cuda.synchronize()

    # Measured runs (100 queries, batch_size=1)
    latencies = []
    with torch.inference_mode():
        for q in sample_queries[30:130]:
            inputs = tokenizer(q, return_tensors="pt", truncation=True, max_length=128, padding=True).to(device)
            if device.type == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            if device.type == "cuda":
                with torch.amp.autocast('cuda', dtype=amp_dtype):
                    _ = model(**inputs)
                torch.cuda.synchronize()
            else:
                _ = model(**inputs)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

    return {
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "median_latency_ms": round(float(np.median(latencies)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2)
    }


def train_baseline(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame,
                   output_dir: Optional[str] = None, seed: int = 42) -> Dict[str, Any]:
    """Trains TF-IDF + Logistic Regression baseline model (deterministic)."""
    set_seed(seed)
    out_dir = output_dir or MODEL_REGISTRY["baseline"]["output_dir"]
    os.makedirs(out_dir, exist_ok=True)

    print("\n--- Training Baseline (TF-IDF + Logistic Regression) ---")
    start_time = time.time()
    
    from sklearn.pipeline import FeatureUnion

    word_vec = TfidfVectorizer(ngram_range=(1, 3), max_features=10000, lowercase=True)
    char_vec = TfidfVectorizer(ngram_range=(2, 5), analyzer="char", max_features=15000, lowercase=True)
    union = FeatureUnion([("word", word_vec), ("char", char_vec)])

    X_train = union.fit_transform(train_df["query"])
    y_train = train_df["intent"]

    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=seed, solver="lbfgs")
    clf.fit(X_train, y_train)

    train_time = time.time() - start_time

    # Evaluate on val
    X_val = union.transform(val_df["query"])
    y_val_pred = clf.predict(X_val)
    val_acc = accuracy_score(val_df["intent"], y_val_pred)
    _, _, val_f1, _ = precision_recall_fscore_support(val_df["intent"], y_val_pred, average="macro", zero_division=0)

    # Evaluate on test
    X_test = union.transform(test_df["query"])
    y_test_pred = clf.predict(X_test)
    test_acc = accuracy_score(test_df["intent"], y_test_pred)
    _, _, test_f1, _ = precision_recall_fscore_support(test_df["intent"], y_test_pred, average="macro", zero_division=0)

    # Per-class F1
    _, _, per_class_f1, _ = precision_recall_fscore_support(test_df["intent"], y_test_pred, average=None, labels=INTENT_CLASSES, zero_division=0)
    per_class_f1_dict = {INTENT_CLASSES[i]: round(float(f), 4) for i, f in enumerate(per_class_f1)}

    # Latency benchmark
    lat_dict = benchmark_baseline_latency(clf, union, test_df["query"].tolist())

    # Save artifact
    model_path = os.path.join(out_dir, "model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"vectorizer": union, "classifier": clf, "classes": INTENT_CLASSES}, f)

    file_size_mb = os.path.getsize(model_path) / (1024 * 1024)

    metrics = {
        "model_key": "baseline",
        "name": MODEL_REGISTRY["baseline"]["name"],
        "seed": seed,
        "train_time_sec": round(train_time, 2),
        "total_epochs_trained": 1,
        "best_epoch": 1,
        "val_acc": round(float(val_acc), 4),
        "val_f1": round(float(val_f1), 4),
        "test_acc": round(float(test_acc), 4),
        "test_f1": round(float(test_f1), 4),
        "per_class_f1": per_class_f1_dict,
        "latency_ms": lat_dict["mean_latency_ms"],
        "median_latency_ms": lat_dict["median_latency_ms"],
        "p95_latency_ms": lat_dict["p95_latency_ms"],
        "size_mb": round(file_size_mb, 2),
        "vram_mb": 0.0
    }

    metrics_path = os.path.join(out_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Baseline Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f} | Test Acc: {test_acc:.4f}, Test F1: {test_f1:.4f} | P95 Latency: {lat_dict['p95_latency_ms']}ms", flush=True)
    return metrics


def train_transformer(model_key: str, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame,
                      seed: int = 42, max_epochs: int = 15, patience: int = 3, min_delta: float = 0.001,
                      batch_size: int = 32, lr: float = 2e-5, weight_decay: float = 0.01,
                      warmup_ratio: float = 0.10, output_dir: Optional[str] = None,
                      save_checkpoint: bool = True) -> Dict[str, Any]:
    """Fine-tunes a transformer sequence classifier with early stopping and restores the best validation checkpoint."""
    set_seed(seed)
    info = MODEL_REGISTRY[model_key]
    hf_id = info["hf_id"]
    out_dir = output_dir or info["output_dir"]
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n--- Training [{model_key.upper()}] (seed={seed}) | Max Epochs={max_epochs}, Patience={patience}, min_delta={min_delta} ---")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    start_time = time.time()
    tokenizer = AutoTokenizer.from_pretrained(hf_id)
    model = AutoModelForSequenceClassification.from_pretrained(
        hf_id,
        num_labels=len(INTENT_CLASSES),
        id2label=ID2LABEL,
        label2id=LABEL2ID
    ).to(device)

    train_labels = [LABEL2ID[i] for i in train_df["intent"]]
    val_labels = [LABEL2ID[i] for i in val_df["intent"]]
    test_labels = [LABEL2ID[i] for i in test_df["intent"]]

    train_ds = IntentTextDataset(train_df["query"].tolist(), train_labels, tokenizer)
    val_ds = IntentTextDataset(val_df["query"].tolist(), val_labels, tokenizer)
    test_ds = IntentTextDataset(test_df["query"].tolist(), test_labels, tokenizer)

    g = torch.Generator()
    g.manual_seed(seed)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, generator=g)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    if "deberta" in model_key:
        lr = min(lr, 1e-5)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    total_steps = len(train_loader) * max_epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * warmup_ratio), num_training_steps=total_steps)

    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    amp_dtype = torch.bfloat16 if use_bf16 else torch.float16
    scaler = torch.amp.GradScaler('cuda') if (torch.cuda.is_available() and not use_bf16) else None

    best_val_f1 = 0.0
    best_val_acc = 0.0
    best_epoch = 0
    patience_counter = 0

    checkpoint_dir = os.path.join(out_dir, "best_checkpoint") if save_checkpoint else out_dir
    os.makedirs(checkpoint_dir, exist_ok=True)

    actual_epochs_trained = 0
    epoch_history = []

    for epoch in range(1, max_epochs + 1):
        actual_epochs_trained = epoch
        model.train()
        train_loss = 0.0
        train_preds, train_targets = [], []
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            if torch.cuda.is_available():
                with torch.amp.autocast('cuda', dtype=amp_dtype):
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                    loss = outputs.loss
                if scaler is not None:
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
            else:
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

            scheduler.step()
            train_loss += loss.item()
            preds = torch.argmax(outputs.logits.detach(), dim=1).cpu().numpy()
            train_preds.extend(preds)
            train_targets.extend(labels.cpu().numpy())

        _, _, epoch_train_f1, _ = precision_recall_fscore_support(train_targets, train_preds, average="macro", zero_division=0)
        epoch_train_f1 = float(epoch_train_f1)
        mean_train_loss = train_loss / len(train_loader)

        # Validation loop
        model.eval()
        val_loss = 0.0
        val_preds, val_targets = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)
                if torch.cuda.is_available():
                    with torch.amp.autocast('cuda', dtype=amp_dtype):
                        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                else:
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                val_loss += outputs.loss.item()
                preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(labels.cpu().numpy())

        mean_val_loss = val_loss / len(val_loader)
        epoch_val_acc = float(accuracy_score(val_targets, val_preds))
        _, _, epoch_val_f1, _ = precision_recall_fscore_support(val_targets, val_preds, average="macro", zero_division=0)
        epoch_val_f1 = float(epoch_val_f1)

        epoch_history.append({
            "epoch": epoch,
            "train_loss": round(mean_train_loss, 4),
            "train_f1": round(epoch_train_f1, 4),
            "val_loss": round(mean_val_loss, 4),
            "val_acc": round(epoch_val_acc, 4),
            "val_f1": round(epoch_val_f1, 4)
        })

        print(f"Epoch {epoch:02d}/{max_epochs:02d} | Train Loss: {mean_train_loss:.4f} | Train F1: {epoch_train_f1:.4f} | Val Loss: {mean_val_loss:.4f} | Val Acc: {epoch_val_acc:.4f} | Val Macro-F1: {epoch_val_f1:.4f}")

        # Early stopping logic with min_delta
        if epoch_val_f1 > best_val_f1 + min_delta:
            best_val_f1 = epoch_val_f1
            best_val_acc = epoch_val_acc
            best_epoch = epoch
            patience_counter = 0
            if save_checkpoint:
                model.save_pretrained(checkpoint_dir)
                tokenizer.save_pretrained(checkpoint_dir)
            print(f"  --> Saved new best checkpoint at epoch {epoch} (Val F1: {best_val_f1:.4f})")
        else:
            patience_counter += 1
            print(f"  --> No improvement >= {min_delta:.4f} (patience: {patience_counter}/{patience})")
            if patience_counter >= patience:
                print(f"\n[Early Stopping] Triggered at epoch {epoch}. Restoring best checkpoint from epoch {best_epoch} (Val F1: {best_val_f1:.4f}).")
                break

    train_time = time.time() - start_time
    peak_vram = torch.cuda.max_memory_allocated() / (1024 * 1024) if torch.cuda.is_available() else 0.0

    # Restore best checkpoint for final test split evaluation
    if save_checkpoint and os.path.exists(os.path.join(checkpoint_dir, "config.json")):
        best_model = AutoModelForSequenceClassification.from_pretrained(checkpoint_dir).to(device)
    else:
        best_model = model
    best_model.eval()

    test_preds, test_targets = [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            if torch.cuda.is_available():
                with torch.amp.autocast('cuda', dtype=amp_dtype):
                    outputs = best_model(input_ids=input_ids, attention_mask=attention_mask)
            else:
                outputs = best_model(input_ids=input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
            test_preds.extend(preds)
            test_targets.extend(batch["labels"].numpy())

    test_acc = float(accuracy_score(test_targets, test_preds))
    _, _, test_f1, _ = precision_recall_fscore_support(test_targets, test_preds, average="macro", zero_division=0)
    test_f1 = float(test_f1)

    # Per-class metrics
    _, _, per_class_f1, _ = precision_recall_fscore_support(test_targets, test_preds, average=None, labels=list(range(len(INTENT_CLASSES))), zero_division=0)
    per_class_f1_dict = {INTENT_CLASSES[i]: round(float(f), 4) for i, f in enumerate(per_class_f1)}

    # Standardized isolated single-query latency benchmark
    lat_dict = benchmark_transformer_latency(best_model, tokenizer, test_df["query"].tolist(), device, use_bf16)

    # Calculate model disk footprint
    eval_dir = checkpoint_dir if os.path.exists(checkpoint_dir) else out_dir
    total_size_mb = sum(
        os.path.getsize(os.path.join(eval_dir, f))
        for f in os.listdir(eval_dir)
        if os.path.isfile(os.path.join(eval_dir, f))
    ) / (1024 * 1024)

    metrics = {
        "model_key": model_key,
        "name": info["name"],
        "seed": seed,
        "train_time_sec": round(train_time, 2),
        "total_epochs_trained": actual_epochs_trained,
        "best_epoch": best_epoch,
        "val_acc": round(best_val_acc, 4),
        "val_f1": round(best_val_f1, 4),
        "test_acc": round(test_acc, 4),
        "test_f1": round(test_f1, 4),
        "per_class_f1": per_class_f1_dict,
        "latency_ms": lat_dict["mean_latency_ms"],
        "median_latency_ms": lat_dict["median_latency_ms"],
        "p95_latency_ms": lat_dict["p95_latency_ms"],
        "size_mb": round(total_size_mb, 2),
        "vram_mb": round(peak_vram, 2),
        "epoch_history": epoch_history
    }

    metrics_path = os.path.join(out_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Done {model_key} (seed {seed})! Best Epoch: {best_epoch} | Test Acc: {test_acc:.4f}, Test Macro-F1: {test_f1:.4f} | P95 Lat: {lat_dict['p95_latency_ms']}ms", flush=True)
    return metrics


def train_model(model_key: str, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame,
                seed: int = 42, max_epochs: int = 15, patience: int = 3, min_delta: float = 0.001,
                batch_size: int = 32, lr: float = 2e-5, output_dir: Optional[str] = None,
                save_checkpoint: bool = True) -> Dict[str, Any]:
    """Unified dispatcher for baseline and transformer model training."""
    if model_key == "baseline":
        return train_baseline(train_df, val_df, test_df, output_dir=output_dir, seed=seed)
    else:
        return train_transformer(
            model_key=model_key,
            train_df=train_df,
            val_df=val_df,
            test_df=test_df,
            seed=seed,
            max_epochs=max_epochs,
            patience=patience,
            min_delta=min_delta,
            batch_size=batch_size,
            lr=lr,
            output_dir=output_dir,
            save_checkpoint=save_checkpoint
        )


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate intent models on GPU with early stopping")
    parser.add_argument("--model", type=str, default="baseline", choices=list(MODEL_REGISTRY.keys()) + ["all"])
    parser.add_argument("--seed", type=int, default=42, help="Random seed for model initialization and data loading")
    parser.add_argument("--max-epochs", "--epochs", type=int, default=15, help="Maximum epochs ceiling (default: 15)")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience (default: 3)")
    parser.add_argument("--min-delta", type=float, default=0.001, help="Minimum Macro-F1 improvement for early stopping (default: 0.001)")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate (default: 2e-5)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_SPLIT_DIR, help="Path to frozen split directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory for model artifacts")
    args = parser.parse_args()

    train_df, val_df, test_df = load_splits(args.data_dir)
    print(f"Loaded dataset from {args.data_dir}: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    targets = list(MODEL_REGISTRY.keys()) if args.model == "all" else [args.model]
    results = []

    for key in targets:
        try:
            m = train_model(
                model_key=key,
                train_df=train_df,
                val_df=val_df,
                test_df=test_df,
                seed=args.seed,
                max_epochs=args.max_epochs,
                patience=args.patience,
                min_delta=args.min_delta,
                batch_size=args.batch_size,
                lr=args.lr,
                output_dir=args.output_dir
            )
            results.append(m)
        except Exception as e:
            print(f"Error training {key}: {e}", file=sys.stderr)

    # Save summary json
    summary_path = os.path.join(MODELS_DIR, "training_summary.json")
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nTraining completed. Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
