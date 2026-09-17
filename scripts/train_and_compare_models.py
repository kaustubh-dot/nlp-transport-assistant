#!/usr/bin/env python3
"""Multi-Model GPU Training and Benchmarking Harness for Chennai Transport Assistant.

Trains, evaluates, and compares 8 open-source candidate architectures:
  1. Baseline: TF-IDF + LogisticRegression
  2. Google MuRIL (google/muril-base-cased)
  3. AI4Bharat IndicBERT v2 (ai4bharat/IndicBERTv2-MLM-only)
  4. AI4Bharat IndicBERT v1 (ai4bharat/indic-bert)
  5. L3Cube HingBERT (l3cube-pune/hing-bert)
  6. Meta XLM-RoBERTa (xlm-roberta-base)
  7. Microsoft mDeBERTa-v3 (microsoft/mdeberta-v3-base)
  8. Sentence-Transformers MiniLM (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)

Features:
  - Mixed precision (fp16) on NVIDIA RTX 4000 Ada GPU
  - Validation-guided checkpointing (saves best model weights)
  - Measures Accuracy, Macro-F1, training time, GPU VRAM peak, and inference latency
"""

import os
import sys
import time
import pickle
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple

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
        "name": "Multilingual MiniLM",
        "description": "Distilled lightweight multilingual sentence encoder",
        "output_dir": os.path.join(MODELS_DIR, "minilm")
    }
}


class IntentTextDataset(Dataset):
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_len: int = 64):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt"
        )
        item = {key: val.squeeze(0) for key, val in encoding.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def load_splits() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}. Run scripts/generate_intent_dataset.py first.")
    df = pd.read_csv(DATASET_PATH)
    train_df = df[df["split"] == "train"].copy().reset_index(drop=True)
    val_df = df[df["split"] == "val"].copy().reset_index(drop=True)
    test_df = df[df["split"] == "test"].copy().reset_index(drop=True)
    return train_df, val_df, test_df


def train_baseline(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict[str, Any]:
    print("\n--- Training Baseline (TF-IDF + Logistic Regression) ---")
    start_time = time.time()
    
    from sklearn.pipeline import FeatureUnion

    word_vec = TfidfVectorizer(ngram_range=(1, 3), max_features=10000, lowercase=True)
    char_vec = TfidfVectorizer(ngram_range=(2, 5), analyzer="char", max_features=15000, lowercase=True)
    union = FeatureUnion([("word", word_vec), ("char", char_vec)])

    X_train = union.fit_transform(train_df["query"])
    y_train = train_df["intent"]

    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    clf.fit(X_train, y_train)

    train_time = time.time() - start_time

    # Evaluate on val
    X_val = union.transform(val_df["query"])
    y_val_pred = clf.predict(X_val)
    val_acc = accuracy_score(val_df["intent"], y_val_pred)
    _, _, val_f1, _ = precision_recall_fscore_support(val_df["intent"], y_val_pred, average="macro", zero_division=0)

    # Evaluate on test
    X_test = union.transform(test_df["query"])
    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        clf.predict(X_test[:10])
        latencies.append((time.perf_counter() - t0) * 100) # ms per query
    mean_lat = float(np.mean(latencies))

    y_test_pred = clf.predict(X_test)
    test_acc = accuracy_score(test_df["intent"], y_test_pred)
    _, _, test_f1, _ = precision_recall_fscore_support(test_df["intent"], y_test_pred, average="macro", zero_division=0)

    # Save artifact
    out_dir = MODEL_REGISTRY["baseline"]["output_dir"]
    os.makedirs(out_dir, exist_ok=True)
    model_path = os.path.join(out_dir, "model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"vectorizer": union, "classifier": clf, "classes": INTENT_CLASSES}, f)

    file_size_mb = os.path.getsize(model_path) / (1024 * 1024)

    metrics = {
        "model_key": "baseline",
        "name": MODEL_REGISTRY["baseline"]["name"],
        "train_time_sec": round(train_time, 2),
        "val_acc": round(val_acc, 4),
        "val_f1": round(val_f1, 4),
        "test_acc": round(test_acc, 4),
        "test_f1": round(test_f1, 4),
        "latency_ms": round(mean_lat, 2),
        "size_mb": round(file_size_mb, 2),
        "vram_mb": 0.0
    }
    print(f"Baseline Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f} | Test Acc: {test_acc:.4f}, Test F1: {test_f1:.4f}")
    return metrics


def train_transformer(model_key: str, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame,
                      epochs: int = 3, batch_size: int = 32, lr: float = 3e-5) -> Dict[str, Any]:
    info = MODEL_REGISTRY[model_key]
    hf_id = info["hf_id"]
    output_dir = info["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n--- Training Transformer [{model_key.upper()}]: {hf_id} ---")
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

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    if "deberta" in model_key:
        lr = 1e-5

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)

    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    amp_dtype = torch.bfloat16 if use_bf16 else torch.float16
    scaler = torch.amp.GradScaler('cuda') if (torch.cuda.is_available() and not use_bf16) else None

    best_val_f1 = 0.0
    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
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

        # Validation loop
        model.eval()
        val_preds, val_targets = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                if torch.cuda.is_available():
                    with torch.amp.autocast('cuda', dtype=amp_dtype):
                        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                else:
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(batch["labels"].numpy())

        epoch_val_acc = accuracy_score(val_targets, val_preds)
        _, _, epoch_val_f1, _ = precision_recall_fscore_support(val_targets, val_preds, average="macro", zero_division=0)
        print(f"Epoch {epoch}/{epochs} | Loss: {train_loss/len(train_loader):.4f} | Val Acc: {epoch_val_acc:.4f} | Val F1: {epoch_val_f1:.4f}")

        if epoch_val_f1 > best_val_f1:
            best_val_f1 = epoch_val_f1
            best_val_acc = epoch_val_acc
            # Save checkpoint
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)

    train_time = time.time() - start_time
    peak_vram = torch.cuda.max_memory_allocated() / (1024 * 1024) if torch.cuda.is_available() else 0.0

    # Test evaluation on holdout test set using saved best checkpoint
    best_model = AutoModelForSequenceClassification.from_pretrained(output_dir).to(device)
    best_model.eval()

    test_preds, test_targets = [], []
    latencies = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            
            t0 = time.perf_counter()
            if torch.cuda.is_available():
                with torch.amp.autocast('cuda', dtype=amp_dtype):
                    outputs = best_model(input_ids=input_ids, attention_mask=attention_mask)
            else:
                outputs = best_model(input_ids=input_ids, attention_mask=attention_mask)
            latencies.append((time.perf_counter() - t0) * 1000 / len(input_ids))

            preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
            test_preds.extend(preds)
            test_targets.extend(batch["labels"].numpy())

    test_acc = accuracy_score(test_targets, test_preds)
    _, _, test_f1, _ = precision_recall_fscore_support(test_targets, test_preds, average="macro", zero_division=0)
    mean_lat = float(np.mean(latencies))

    # Calculate model disk size
    total_size_mb = sum(
        os.path.getsize(os.path.join(output_dir, f))
        for f in os.listdir(output_dir)
        if os.path.isfile(os.path.join(output_dir, f))
    ) / (1024 * 1024)

    metrics = {
        "model_key": model_key,
        "name": info["name"],
        "train_time_sec": round(train_time, 2),
        "val_acc": round(best_val_acc, 4),
        "val_f1": round(best_val_f1, 4),
        "test_acc": round(test_acc, 4),
        "test_f1": round(test_f1, 4),
        "latency_ms": round(mean_lat, 2),
        "size_mb": round(total_size_mb, 2),
        "vram_mb": round(peak_vram, 2)
    }
    print(f"Done {model_key}! Test Acc: {test_acc:.4f}, Test F1: {test_f1:.4f}, Latency: {mean_lat:.2f}ms")
    return metrics


def train_model(model_key: str, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame,
                epochs: int = 3, batch_size: int = 32) -> Dict[str, Any]:
    if model_key == "baseline":
        return train_baseline(train_df, val_df, test_df)
    else:
        return train_transformer(model_key, train_df, val_df, test_df, epochs=epochs, batch_size=batch_size)


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate intent models on GPU")
    parser.add_argument("--model", type=str, default="baseline", choices=list(MODEL_REGISTRY.keys()) + ["all"])
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    train_df, val_df, test_df = load_splits()
    print(f"Loaded dataset: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    targets = list(MODEL_REGISTRY.keys()) if args.model == "all" else [args.model]
    results = []

    for key in targets:
        try:
            m = train_model(key, train_df, val_df, test_df, epochs=args.epochs, batch_size=args.batch_size)
            results.append(m)
        except Exception as e:
            print(f"Error training {key}: {e}", file=sys.stderr)

    # Save summary json
    summary_path = os.path.join(MODELS_DIR, "training_summary.json")
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        import json
        json.dump(results, f, indent=2)

    print(f"\nAll training completed. Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
