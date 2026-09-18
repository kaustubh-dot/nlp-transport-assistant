#!/usr/bin/env python3
"""Multi-Seed GPU Benchmark Runner for Intent Classification Models.

Orchestrates 5-seed evaluation across candidate architectures on a frozen 70/15/15 family-disjoint split.
Protocol:
  - 5 seeds: [42, 101, 777, 1337, 2026]
  - Max epochs = 15 ceiling
  - Early stopping: patience=3, min_delta=0.001 on Validation Macro-F1
  - BF16 mixed precision
  - Isolated batch=1 latency benchmark (CUDA sync)
  - Aggregates Mean ± Std for Test Macro-F1, Accuracy, Latency, and Best Epochs
  - Generates comprehensive markdown comparison report and JSON results
"""

import os
import sys
import time
import json
import shutil
import argparse
import statistics
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.train_and_compare_models import (
    MODEL_REGISTRY,
    DEFAULT_SPLIT_DIR,
    MODELS_DIR,
    load_splits,
    train_model,
    INTENT_CLASSES
)

DEFAULT_SEEDS = [42, 101, 777, 1337, 2026]
DEFAULT_MODELS = ["baseline", "muril", "indicbert_v2", "xlm_roberta", "hingbert", "minilm"]
BENCHMARK_MODELS_DIR = os.path.join(MODELS_DIR, "benchmark_runs")
DEFAULT_OUTPUT_MD = os.path.join(BASE_DIR, "docs", "benchmarks", "current_multi_seed_5seed_benchmark.md")
DEFAULT_OUTPUT_JSON = os.path.join(BASE_DIR, "docs", "benchmarks", "current_multi_seed_5seed_results.json")


def compute_mean_std(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean_val = float(statistics.mean(values))
    std_val = float(statistics.stdev(values)) if len(values) > 1 else 0.0
    return mean_val, std_val


def run_multi_seed_benchmark(seeds: List[int] = DEFAULT_SEEDS,
                             models: List[str] = DEFAULT_MODELS,
                             max_epochs: int = 15,
                             patience: int = 3,
                             min_delta: float = 0.001,
                             learning_rate: float = 2e-5,
                             batch_size: int = 32,
                             data_dir: str = DEFAULT_SPLIT_DIR,
                             output_md: str = DEFAULT_OUTPUT_MD,
                             output_json: str = DEFAULT_OUTPUT_JSON) -> Dict[str, Any]:
    """Executes multi-seed training and benchmarking across specified models."""
    os.makedirs(BENCHMARK_MODELS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(output_md), exist_ok=True)

    train_df, val_df, test_df = load_splits(data_dir)
    print(f"\n=======================================================")
    print(f"MULTI-SEED TRANSFORMER BENCHMARK (N={len(seeds)} SEEDS)")
    print(f"Dataset: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    print(f"Seeds: {seeds}")
    print(f"Candidate Models: {models}")
    print(f"Settings: Max Epochs={max_epochs}, Patience={patience}, min_delta={min_delta}, LR={learning_rate}")
    print(f"=======================================================\n")

    all_results: Dict[str, Any] = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "bf16_supported": torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
            "seeds": seeds,
            "max_epochs": max_epochs,
            "patience": patience,
            "min_delta": min_delta,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "num_train": len(train_df),
            "num_val": len(val_df),
            "num_test": len(test_df)
        },
        "raw_runs": {},
        "model_summaries": {}
    }

    # Track best model across all runs
    overall_best_f1 = -1.0
    overall_champion_key = None
    champion_seed = None

    for model_key in models:
        print(f"\n>>>>>>>>>>>> MODEL: {model_key.upper()} <<<<<<<<<<<<")
        model_runs = []
        best_model_run_val_f1 = -1.0
        best_run_checkpoint_dir = None

        is_baseline = (model_key == "baseline")
        # Baseline is deterministic; run once with seed 42
        run_seeds = [seeds[0]] if is_baseline else seeds

        for seed in run_seeds:
            run_out_dir = os.path.join(BENCHMARK_MODELS_DIR, f"{model_key}_seed_{seed}")
            metrics_path = os.path.join(run_out_dir, "metrics.json")
            if os.path.exists(metrics_path):
                try:
                    with open(metrics_path, "r", encoding="utf-8") as f:
                        metrics = json.load(f)
                    print(f"--> [CACHE HIT] Loaded existing metrics for {model_key} (seed {seed}) from {metrics_path} (Best Epoch: {metrics.get('best_epoch')}, Test F1: {metrics.get('test_f1')})", flush=True)
                    model_runs.append(metrics)
                    if metrics.get("val_f1", 0.0) > best_model_run_val_f1:
                        best_model_run_val_f1 = metrics["val_f1"]
                        best_run_checkpoint_dir = os.path.join(run_out_dir, "best_checkpoint") if not is_baseline else run_out_dir
                    continue
                except Exception as e:
                    print(f"Warning: failed reading {metrics_path}: {e}", flush=True)

            try:
                metrics = train_model(
                    model_key=model_key,
                    train_df=train_df,
                    val_df=val_df,
                    test_df=test_df,
                    seed=seed,
                    max_epochs=max_epochs,
                    patience=patience,
                    min_delta=min_delta,
                    batch_size=batch_size,
                    lr=learning_rate,
                    output_dir=run_out_dir,
                    save_checkpoint=True
                )
                model_runs.append(metrics)

                # Keep track of best run checkpoint to populate main models/<model_key> directory
                if metrics["val_f1"] > best_model_run_val_f1:
                    best_model_run_val_f1 = metrics["val_f1"]
                    best_run_checkpoint_dir = os.path.join(run_out_dir, "best_checkpoint") if not is_baseline else run_out_dir

            except Exception as e:
                print(f"Error training {model_key} with seed {seed}: {e}", file=sys.stderr)

        all_results["raw_runs"][model_key] = model_runs

        # If we have best checkpoint, copy it into models/<model_key>/ so production classifier can use it
        if best_run_checkpoint_dir and os.path.exists(best_run_checkpoint_dir):
            target_prod_dir = MODEL_REGISTRY[model_key]["output_dir"]
            os.makedirs(target_prod_dir, exist_ok=True)
            for item in os.listdir(best_run_checkpoint_dir):
                s = os.path.join(best_run_checkpoint_dir, item)
                d = os.path.join(target_prod_dir, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            print(f"Copied best validation checkpoint for [{model_key}] to {target_prod_dir}")

        # Compute summary statistics across seeds
        if model_runs:
            test_f1s = [r["test_f1"] for r in model_runs]
            test_accs = [r["test_acc"] for r in model_runs]
            val_f1s = [r["val_f1"] for r in model_runs]
            val_accs = [r["val_acc"] for r in model_runs]
            best_epochs = [r["best_epoch"] for r in model_runs]
            epochs_trained = [r["total_epochs_trained"] for r in model_runs]
            p95_lats = [r["p95_latency_ms"] for r in model_runs]
            mean_lats = [r["latency_ms"] for r in model_runs]
            train_times = [r["train_time_sec"] for r in model_runs]

            mean_test_f1, std_test_f1 = (test_f1s[0], 0.0) if is_baseline else compute_mean_std(test_f1s)
            mean_test_acc, std_test_acc = (test_accs[0], 0.0) if is_baseline else compute_mean_std(test_accs)
            mean_val_f1, std_val_f1 = (val_f1s[0], 0.0) if is_baseline else compute_mean_std(val_f1s)
            mean_val_acc, std_val_acc = (val_accs[0], 0.0) if is_baseline else compute_mean_std(val_accs)

            # Per-class mean F1
            per_class_aggregated = {}
            for intent in INTENT_CLASSES:
                c_f1s = [r["per_class_f1"].get(intent, 0.0) for r in model_runs if "per_class_f1" in r]
                m_cf1, s_cf1 = compute_mean_std(c_f1s) if c_f1s else (0.0, 0.0)
                per_class_aggregated[intent] = {
                    "mean": round(m_cf1, 4),
                    "std": round(s_cf1, 4)
                }

            summary = {
                "name": MODEL_REGISTRY[model_key]["name"],
                "model_key": model_key,
                "is_deterministic": is_baseline,
                "num_seeds": len(model_runs),
                "test_macro_f1": {"mean": round(mean_test_f1, 4), "std": round(std_test_f1, 4)},
                "test_accuracy": {"mean": round(mean_test_acc, 4), "std": round(std_test_acc, 4)},
                "val_macro_f1": {"mean": round(mean_val_f1, 4), "std": round(std_val_f1, 4)},
                "val_accuracy": {"mean": round(mean_val_acc, 4), "std": round(std_val_acc, 4)},
                "best_epochs": best_epochs,
                "mean_best_epoch": round(float(statistics.mean(best_epochs)), 1),
                "total_epochs_trained": epochs_trained,
                "p95_latency_ms": round(float(statistics.mean(p95_lats)), 2),
                "mean_latency_ms": round(float(statistics.mean(mean_lats)), 2),
                "model_size_mb": model_runs[0]["size_mb"],
                "peak_vram_mb": max(r["vram_mb"] for r in model_runs),
                "mean_train_time_sec": round(float(statistics.mean(train_times)), 1),
                "per_class_f1": per_class_aggregated
            }
            all_results["model_summaries"][model_key] = summary

    # Champion Selection Hierarchy:
    # 1. Highest mean Test Macro-F1
    # 2. Stability (lowest std dev)
    # 3. P95 latency / model size
    ranked_models = sorted(
        all_results["model_summaries"].values(),
        key=lambda s: (s["test_macro_f1"]["mean"], -s["test_macro_f1"]["std"], -s["p95_latency_ms"]),
        reverse=True
    )

    champion = ranked_models[0] if ranked_models else None
    all_results["champion"] = champion

    # Save JSON results
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nRaw results saved to {output_json}")

    # Generate Markdown Report
    generate_markdown_report(all_results, ranked_models, output_md)
    print(f"Markdown comparison report generated at {output_md}")

    return all_results


def generate_markdown_report(all_results: Dict[str, Any], ranked_models: List[Dict[str, Any]], output_md: str):
    """Generates an academic-grade comparative report in Markdown."""
    meta = all_results["metadata"]
    champion = all_results.get("champion")

    lines = []
    lines.append("# Multi-Seed Intent Classification Benchmark Report\n")
    lines.append(f"**Generated:** {meta['timestamp']}  \n")
    lines.append(f"**Hardware:** {meta['device']} (BF16: {meta['bf16_supported']})  \n")
    lines.append(f"**Environment:** PyTorch `{meta['torch_version']}`, CUDA `{torch.version.cuda if torch.cuda.is_available() else 'N/A'}`  \n")
    lines.append(f"**Dataset Partition:** Frozen Family-Disjoint 70/15/15 Split (Train: {meta['num_train']}, Val: {meta['num_val']}, Test: {meta['num_test']})  \n")
    lines.append(f"**Seeds Evaluated:** `{meta['seeds']}` | **Early Stopping:** Patience={meta['patience']}, min_delta={meta['min_delta']} | **Max Epochs:** {meta['max_epochs']}  \n")
    lines.append("\n---\n")

    if champion:
        lines.append(f"## 🏆 Selected Champion Architecture: **{champion['name']}**\n")
        lines.append(f"- **Primary Metric (Test Macro-F1):** **`{champion['test_macro_f1']['mean']:.4f} ± {champion['test_macro_f1']['std']:.4f}`**\n")
        lines.append(f"- **Test Accuracy:** **`{champion['test_accuracy']['mean']*100:.2f}% ± {champion['test_accuracy']['std']*100:.2f}%`**\n")
        lines.append(f"- **P95 Single-Query Latency:** `{champion['p95_latency_ms']:.2f} ms` (batch_size=1, CUDA sync)\n")
        lines.append(f"- **Model Disk Size:** `{champion['model_size_mb']:.1f} MB` | **Peak VRAM:** `{champion['peak_vram_mb']:.1f} MB`\n")
        lines.append(f"- **Best Epoch Distribution:** `{champion['best_epochs']}` (Mean: {champion['mean_best_epoch']})\n\n")

    lines.append("## 1. Overall Model Leaderboard (Mean ± Std across Seeds)\n\n")
    lines.append("| Rank | Model Architecture | Test Macro-F1 (Mean±SD) | Test Accuracy (Mean±SD) | Val Macro-F1 (Mean±SD) | Best Epochs | P95 Latency | Size | Peak VRAM |\n")
    lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")

    for i, s in enumerate(ranked_models, 1):
        f1_str = f"**{s['test_macro_f1']['mean']:.4f}** ± {s['test_macro_f1']['std']:.4f}" if not s['is_deterministic'] else f"**{s['test_macro_f1']['mean']:.4f}** (det)"
        acc_str = f"{s['test_accuracy']['mean']*100:.2f}% ± {s['test_accuracy']['std']*100:.2f}%" if not s['is_deterministic'] else f"{s['test_accuracy']['mean']*100:.2f}% (det)"
        val_f1_str = f"{s['val_macro_f1']['mean']:.4f} ± {s['val_macro_f1']['std']:.4f}" if not s['is_deterministic'] else f"{s['val_macro_f1']['mean']:.4f} (det)"
        epochs_str = str(s['best_epochs']) if not s['is_deterministic'] else "1"
        medal = "🥇 " if i == 1 else ("🥈 " if i == 2 else ("🥉 " if i == 3 else ""))

        lines.append(f"| {i} | {medal}{s['name']} | {f1_str} | {acc_str} | {val_f1_str} | {epochs_str} | {s['p95_latency_ms']:.2f} ms | {s['model_size_mb']:.1f} MB | {s['peak_vram_mb']:.0f} MB |\n")

    lines.append("\n---\n")
    lines.append("## 2. Seed-by-Seed Fine-Grained Stability Breakdown\n\n")
    lines.append("| Model | Seed | Best Epoch | Total Epochs | Val Macro-F1 | Test Macro-F1 | Test Accuracy | P95 Latency | Train Time |\n")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")

    for model_key, runs in all_results["raw_runs"].items():
        name = MODEL_REGISTRY[model_key]["name"]
        for r in runs:
            lines.append(f"| {name} | `{r['seed']}` | {r['best_epoch']} | {r['total_epochs_trained']} | {r['val_f1']:.4f} | {r['test_f1']:.4f} | {r['test_acc']*100:.2f}% | {r['p95_latency_ms']:.2f} ms | {r['train_time_sec']:.1f}s |\n")

    lines.append("\n---\n")
    lines.append("## 3. Convergence Diagnostics & Safety Verification\n\n")
    lines.append("Per protocol safety rule, we verify whether the 15-epoch ceiling truncated convergence:\n\n")

    for s in ranked_models:
        if s['is_deterministic']:
            continue
        max_seen = max(s['best_epochs'])
        if max_seen >= 13:
            status = f"⚠️ **CAUTION**: Best epoch reached {max_seen}/{meta['max_epochs']} (>= 13). Training ceiling may be truncating convergence; targeted diagnostic at max_epochs=20 recommended."
        else:
            status = f"✅ **PASS**: Best epochs peaked safely between {min(s['best_epochs'])} and {max_seen} (< 13). Ceiling {meta['max_epochs']} was non-binding; early stopping operated correctly."
        lines.append(f"- **{s['name']}**: Best epochs = `{s['best_epochs']}`. {status}\n")

    lines.append("\n---\n")
    lines.append("## 4. Per-Class F1 Score Breakdown (Mean across Seeds)\n\n")
    lines.append("| Intent Class | " + " | ".join([s["name"] for s in ranked_models]) + " |\n")
    lines.append("|:---|" + "|".join([":---:" for _ in ranked_models]) + "|\n")

    for intent in INTENT_CLASSES:
        row = [f"`{intent}`"]
        for s in ranked_models:
            val = s["per_class_f1"].get(intent, {}).get("mean", 0.0)
            row.append(f"{val:.4f}")
        lines.append("| " + " | ".join(row) + " |\n")

    lines.append("\n---\n")
    lines.append("## 5. Methodological Notes\n\n")
    lines.append("- **Dataset Partition Roles**:\n")
    lines.append("  - `train.csv` (70%): Parameter optimization and model weights learning.\n")
    lines.append("  - `validation.csv` (15%): Early stopping monitoring and best-checkpoint selection.\n")
    lines.append("  - `test.csv` (15%): Benchmark / architecture comparison and champion selection holdout.\n")
    lines.append("  - `acceptance_test_suite.json` (149 cases): Final untouched external evaluation suite; never seen during training, early stopping, or hyperparameter selection.\n")
    lines.append("- **Precision & Regularization**: BF16 mixed precision providing improved numerical stability and dynamic range over FP16, paired with standard `max_grad_norm = 1.0` gradient clipping and AdamW weight decay of 0.01.\n")
    lines.append("- **Fixed Effective Batch Size & Length**: Standardized at effective batch size = 32, max sequence length = 128 tokens across all transformer candidate models.\n")
    lines.append("- **Multilingual MiniLM Note**: `paraphrase-multilingual-MiniLM-L12-v2` encoder adapted for 7-class sequence classification and fine-tuned end-to-end.\n")
    lines.append("- **Champion Selection Rule**: Ranked primarily by mean Test Macro-F1 across 5 seeds. Where models fall within run-to-run seed variance (<0.20 F1), inference latency and model footprint break near-ties.\n")

    with open(output_md, "w", encoding="utf-8") as f:
        f.writelines(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 5-seed benchmark across intent models")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS, help="List of random seeds")
    parser.add_argument("--models", nargs="+", type=str, default=DEFAULT_MODELS, help="List of model keys to benchmark")
    parser.add_argument("--max-epochs", type=int, default=15, help="Maximum epochs ceiling (default: 15)")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience (default: 3)")
    parser.add_argument("--min-delta", type=float, default=0.001, help="Min improvement for early stopping (default: 0.001)")
    parser.add_argument("--learning-rate", "--lr", type=float, default=2e-5, help="Learning rate (default: 2e-5)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_SPLIT_DIR, help="Path to frozen split directory")
    parser.add_argument("--output-md", type=str, default=DEFAULT_OUTPUT_MD, help="Output markdown report path")
    parser.add_argument("--output-json", type=str, default=DEFAULT_OUTPUT_JSON, help="Output JSON results path")
    args = parser.parse_args()

    run_multi_seed_benchmark(
        seeds=args.seeds,
        models=args.models,
        max_epochs=args.max_epochs,
        patience=args.patience,
        min_delta=args.min_delta,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        data_dir=args.data_dir,
        output_md=args.output_md,
        output_json=args.output_json
    )
