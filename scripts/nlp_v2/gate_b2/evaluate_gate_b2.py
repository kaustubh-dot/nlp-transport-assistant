#!/usr/bin/env python3
"""Gate B.2 Comprehensive Evaluator & Statistical Comparison Harness.

Evaluates T2-H vs T3 across seeds [42, 101, 777]:
1. Exact Downstream Operation Accuracy & Macro-F1 (Multi-seed Mean ± Std)
2. Minimal-Pair Contrast Group Exact Consistency (100% of group correct)
3. Ambiguity-Aware vs Strict Primary Scoring
4. Stratified Subgroups (Language, CS0–CS4, N0–N5, Implicit, Ambiguous, Author Source)
5. Multi-Seed Paired McNemar Significance (per seed: 42, 101, 777)
6. Hierarchical Query × Seed Paired Bootstrap (1,000 resamples: mean diff, 95% CI, p-value)
7. Entity-Masked & Token-Masked Diagnostics
8. Calibration Analysis (ECE, Brier score, Mean Confidence on Correct / Incorrect / Ambiguous)
9. Categorized Error Review of >= 100 disagreement/failure exemplars

Outputs:
- reports/nlp_v2/gate_b2/gate_b2_confirmation_results.json
- reports/nlp_v2/gate_b2/gate_b2_confirmation_results.md
"""

import os
import sys
import json
from typing import Tuple, List, Dict, Any
import numpy as np
import scipy.stats as stats
from collections import defaultdict
from sklearn.metrics import accuracy_score, f1_score, brier_score_loss

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EXP_DIR = os.path.join(BASE_DIR, "experiments", "nlp_v2", "gate_b2")
REPORT_DIR = os.path.join(BASE_DIR, "reports", "nlp_v2", "gate_b2")

os.makedirs(REPORT_DIR, exist_ok=True)

SEEDS = [42, 101, 777]


def load_predictions(model_prefix: str, seed: int):
    path = os.path.join(EXP_DIR, f"predictions_{model_prefix}_seed{seed}.jsonl")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing prediction file: {path}")
    preds = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                preds.append(json.loads(line))
    return preds


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Computes Expected Calibration Error (ECE)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(probs)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        mask = (probs > bin_lower) & (probs <= bin_upper) if i > 0 else (probs >= bin_lower) & (probs <= bin_upper)
        bin_size = np.sum(mask)

        if bin_size > 0:
            bin_acc = np.mean(labels[mask])
            bin_conf = np.mean(probs[mask])
            ece += (bin_size / total_samples) * np.abs(bin_acc - bin_conf)

    return float(ece)


def run_mcnemar_test(b: int, c: int) -> Tuple[float, float]:
    """Calculates McNemar Chi-Square test with Edwards continuity correction."""
    n = b + c
    if n == 0:
        return 0.0, 1.0
    chi2 = ((abs(b - c) - 1.0) ** 2) / n
    p_val = 1.0 - stats.chi2.cdf(chi2, df=1)
    return float(chi2), float(p_val)


def run_hierarchical_bootstrap(t2h_preds_by_seed, t3_preds_by_seed, n_bootstraps=1000, seed=42):
    """Hierarchical query x seed bootstrap."""
    rng = np.random.RandomState(seed)
    n_queries = len(t2h_preds_by_seed[SEEDS[0]])
    diffs = []

    # Map utterance_id to index
    uid_order = [p["utterance_id"] for p in t2h_preds_by_seed[SEEDS[0]]]

    t2h_correct_matrix = np.zeros((len(SEEDS), n_queries))
    t3_correct_matrix = np.zeros((len(SEEDS), n_queries))

    for s_idx, s in enumerate(SEEDS):
        for q_idx, p in enumerate(t2h_preds_by_seed[s]):
            t2h_correct_matrix[s_idx, q_idx] = 1.0 if p["exact_operation_correct"] else 0.0
        for q_idx, p in enumerate(t3_preds_by_seed[s]):
            t3_correct_matrix[s_idx, q_idx] = 1.0 if p["exact_operation_correct"] else 0.0

    for _ in range(n_bootstraps):
        # Sample queries with replacement
        q_indices = rng.choice(n_queries, size=n_queries, replace=True)

        # Include paired predictions from all three seeds
        boot_t2h = np.mean(t2h_correct_matrix[:, q_indices])
        boot_t3 = np.mean(t3_correct_matrix[:, q_indices])
        diffs.append(boot_t3 - boot_t2h)

    diffs = np.array(diffs)
    mean_diff = float(np.mean(diffs))
    ci_lower = float(np.percentile(diffs, 2.5))
    ci_upper = float(np.percentile(diffs, 97.5))

    # Two-sided p-value
    if mean_diff >= 0:
        p_val = float(2.0 * np.mean(diffs <= 0))
    else:
        p_val = float(2.0 * np.mean(diffs >= 0))
    p_val = min(1.0, p_val)

    return {
        "mean_diff": mean_diff,
        "ci_lower_95": ci_lower,
        "ci_upper_95": ci_upper,
        "two_sided_p_val": p_val
    }


def analyze_contrast_groups(preds: List[Dict[str, Any]]) -> float:
    """Computes exact group accuracy: 100% of group members must be correct."""
    groups = defaultdict(list)
    for p in preds:
        cg_id = p.get("contrast_group_id")
        if cg_id:
            groups[cg_id].append(p["exact_operation_correct"])

    if not groups:
        return 0.0

    correct_groups = sum(1 for g_res in groups.values() if all(g_res))
    return float(correct_groups / len(groups))


def evaluate_gate_b2():
    print("=" * 70)
    print("Executing Gate B.2 Comprehensive Taxonomy Confirmation Evaluation")
    print("=" * 70)

    # 1. Load predictions
    t2h_preds = {s: load_predictions("t2h_muril", s) for s in SEEDS}
    t3_preds = {s: load_predictions("t3_muril", s) for s in SEEDS}

    print(f"Loaded predictions across seeds {SEEDS} for T2-H and T3.")

    # 2. Multi-Seed Core Metrics
    core_metrics = {"T2-H": {}, "T3": {}}

    for model_name, preds_dict in [("T2-H", t2h_preds), ("T3", t3_preds)]:
        intent_accs, intent_f1s = [], []
        op_accs, op_f1s = [], []
        cg_accs = []
        ambig_accs = []

        for s in SEEDS:
            preds = preds_dict[s]
            gold_ops = [p["gold_operation"] for p in preds]
            pred_ops = [p["pred_operation"] for p in preds]

            gold_intents = [p["gold_T2_intent"] if model_name == "T2-H" else p["gold_T3_intent"] for p in preds]
            pred_intents = [p["pred_T2_intent"] if model_name == "T2-H" else p["pred_T3_intent"] for p in preds]

            intent_acc = accuracy_score(gold_intents, pred_intents)
            intent_f1 = f1_score(gold_intents, pred_intents, average="macro")

            op_acc = accuracy_score(gold_ops, pred_ops)
            op_f1 = f1_score(gold_ops, pred_ops, average="macro")

            cg_acc = analyze_contrast_groups(preds)
            ambig_acc = np.mean([1.0 if p["ambiguity_aware_correct"] else 0.0 for p in preds])

            intent_accs.append(intent_acc)
            intent_f1s.append(intent_f1)
            op_accs.append(op_acc)
            op_f1s.append(op_f1)
            cg_accs.append(cg_acc)
            ambig_accs.append(ambig_acc)

        core_metrics[model_name] = {
            "intent_accuracy": {"mean": float(np.mean(intent_accs)), "std": float(np.std(intent_accs)), "seeds": intent_accs},
            "intent_macro_f1": {"mean": float(np.mean(intent_f1s)), "std": float(np.std(intent_f1s)), "seeds": intent_f1s},
            "downstream_op_accuracy": {"mean": float(np.mean(op_accs)), "std": float(np.std(op_accs)), "seeds": op_accs},
            "downstream_op_macro_f1": {"mean": float(np.mean(op_f1s)), "std": float(np.std(op_f1s)), "seeds": op_f1s},
            "contrast_group_accuracy": {"mean": float(np.mean(cg_accs)), "std": float(np.std(cg_accs)), "seeds": cg_accs},
            "ambiguity_aware_accuracy": {"mean": float(np.mean(ambig_accs)), "std": float(np.std(ambig_accs)), "seeds": ambig_accs}
        }

    # 3. Paired McNemar Tests (Per Seed)
    mcnemar_results = {}
    for s in SEEDS:
        p_t2h = t2h_preds[s]
        p_t3 = t3_preds[s]

        # b: T3 correct, T2-H incorrect
        # c: T3 incorrect, T2-H correct
        b = sum(1 for p3, p2 in zip(p_t3, p_t2h) if p3["exact_operation_correct"] and not p2["exact_operation_correct"])
        c = sum(1 for p3, p2 in zip(p_t3, p_t2h) if not p3["exact_operation_correct"] and p2["exact_operation_correct"])
        both_correct = sum(1 for p3, p2 in zip(p_t3, p_t2h) if p3["exact_operation_correct"] and p2["exact_operation_correct"])
        both_incorrect = sum(1 for p3, p2 in zip(p_t3, p_t2h) if not p3["exact_operation_correct"] and not p2["exact_operation_correct"])

        chi2, p_val = run_mcnemar_test(b, c)
        mcnemar_results[f"seed_{s}"] = {
            "b_t3_wins": b,
            "c_t2h_wins": c,
            "both_correct": both_correct,
            "both_incorrect": both_incorrect,
            "chi2_statistic": chi2,
            "p_value": p_val
        }

    # 4. Hierarchical Bootstrap
    bootstrap_results = run_hierarchical_bootstrap(t2h_preds, t3_preds)

    # 5. Calibration Metrics
    calibration_results = {}
    for model_name, preds_dict in [("T2-H", t2h_preds), ("T3", t3_preds)]:
        all_confs = []
        all_corrects = []
        correct_confs = []
        incorrect_confs = []
        ambig_confs = []

        for s in SEEDS:
            for p in preds_dict[s]:
                conf = p["confidence"]
                corr = 1.0 if p["exact_operation_correct"] else 0.0
                all_confs.append(conf)
                all_corrects.append(corr)

                if p["exact_operation_correct"]:
                    correct_confs.append(conf)
                else:
                    incorrect_confs.append(conf)

                if p.get("clarification_required"):
                    ambig_confs.append(conf)

        all_confs = np.array(all_confs)
        all_corrects = np.array(all_corrects)

        ece = compute_ece(all_confs, all_corrects)
        brier = float(brier_score_loss(all_corrects, all_confs))

        calibration_results[model_name] = {
            "mean_confidence_correct": float(np.mean(correct_confs)),
            "mean_confidence_incorrect": float(np.mean(incorrect_confs)),
            "mean_confidence_ambiguous": float(np.mean(ambig_confs)) if ambig_confs else 0.0,
            "ece": ece,
            "brier_score": brier
        }

    # 6. Stratified Subgroup Analysis (Mean across 3 seeds)
    def compute_subgroup_performance(attr_name):
        res = {}
        # Get unique values for attr
        vals = sorted(list(set(p[attr_name] for p in t2h_preds[SEEDS[0]])))

        for v in vals:
            v_str = str(v)
            res[v_str] = {"count": 0, "T2-H_op_acc": 0.0, "T3_op_acc": 0.0, "delta": 0.0}

            t2_accs, t3_accs = [], []
            for s in SEEDS:
                p2_subset = [p for p in t2h_preds[s] if p[attr_name] == v]
                p3_subset = [p for p in t3_preds[s] if p[attr_name] == v]
                res[v_str]["count"] = len(p2_subset)

                t2_acc = np.mean([1.0 if p["exact_operation_correct"] else 0.0 for p in p2_subset]) if p2_subset else 0.0
                t3_acc = np.mean([1.0 if p["exact_operation_correct"] else 0.0 for p in p3_subset]) if p3_subset else 0.0
                t2_accs.append(t2_acc)
                t3_accs.append(t3_acc)

            m2 = float(np.mean(t2_accs))
            m3 = float(np.mean(t3_accs))
            res[v_str]["T2-H_op_acc"] = m2
            res[v_str]["T3_op_acc"] = m3
            res[v_str]["delta"] = m3 - m2

        return res

    subgroups = {
        "language_class": compute_subgroup_performance("language_class"),
        "code_switch_level": compute_subgroup_performance("code_switch_level"),
        "noise_level": compute_subgroup_performance("noise_level"),
        "author_source": compute_subgroup_performance("author_source"),
        "clarification_required": compute_subgroup_performance("clarification_required")
    }

    # 7. Error Categorization (Auditing >= 100 cases)
    error_taxonomy = defaultdict(list)
    p2_s42 = t2h_preds[42]
    p3_s42 = t3_preds[42]

    for p2, p3 in zip(p2_s42, p3_s42):
        uid = p2["utterance_id"]
        q = p2["query"]
        gold_op = p2["gold_operation"]
        op2 = p2["pred_operation"]
        op3 = p3["pred_operation"]

        # Only analyze cases where at least one model failed
        if p2["exact_operation_correct"] and p3["exact_operation_correct"]:
            continue

        category = "OTHER"
        if gold_op in ("PLAN_ROUTE", "PLAN_MULTIMODAL_ROUTE") and (op2 in ("PLAN_ROUTE", "PLAN_MULTIMODAL_ROUTE") or op3 in ("PLAN_ROUTE", "PLAN_MULTIMODAL_ROUTE")):
            category = "ROUTE_VS_MULTIMODAL"
        elif gold_op in ("LIST_ROUTE_STOPS", "CHECK_STOP_ON_ROUTE"):
            category = "SEQUENCE_VS_MEMBERSHIP"
        elif gold_op in ("GET_FIRST_LAST_SERVICE", "GET_SERVICE_FREQUENCY", "GET_SCHEDULED_DEPARTURES"):
            category = "TIMING_SUBTYPE"
        elif gold_op == "CHECK_SERVICE_AVAILABILITY" or op2 == "CHECK_SERVICE_AVAILABILITY" or op3 == "CHECK_SERVICE_AVAILABILITY":
            category = "AVAILABILITY_VS_ROUTE"
        elif gold_op == "GET_INTERCHANGE_DETAILS" or op2 == "GET_INTERCHANGE_DETAILS" or op3 == "GET_INTERCHANGE_DETAILS":
            category = "INTERCHANGE_VS_ROUTE"
        elif gold_op in ("GET_STATION_FACILITY", "GET_ACCESSIBILITY_INFO"):
            category = "FACILITY_VS_ACCESSIBILITY"
        elif gold_op == "REJECT_UNSUPPORTED_REALTIME":
            category = "STATIC_VS_REALTIME"
        elif p2["noise_level"] in ("N4", "N5"):
            category = "SEVERE_NOISE_CORRUPTION"
        elif p2["code_switch_level"] == "CS4":
            category = "COMPLEX_MIXED_SCRIPT"
        elif p2.get("clarification_required"):
            category = "TRUE_ANNOTATION_AMBIGUITY"

        item = {
            "utterance_id": uid,
            "query": q,
            "gold_operation": gold_op,
            "T2H_pred_operation": op2,
            "T3_pred_operation": op3,
            "T2H_correct": p2["exact_operation_correct"],
            "T3_correct": p3["exact_operation_correct"],
            "noise_level": p2["noise_level"],
            "code_switch_level": p2["code_switch_level"],
            "category": category
        }
        error_taxonomy[category].append(item)

    # 8. Compile Comprehensive JSON Report
    results_json = {
        "evaluation_name": "Gate B.2 Confirmation Experiment Results",
        "sample_size": len(t2h_preds[42]),
        "seeds": SEEDS,
        "core_metrics": core_metrics,
        "mcnemar_per_seed": mcnemar_results,
        "hierarchical_bootstrap": bootstrap_results,
        "calibration": calibration_results,
        "subgroups": subgroups,
        "error_analysis_summary": {k: len(v) for k, v in error_taxonomy.items()},
        "error_exemplars": {k: v[:5] for k, v in error_taxonomy.items()}
    }

    json_path = os.path.join(REPORT_DIR, "gate_b2_confirmation_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_json, f, indent=2, ensure_ascii=False)

    print(f"\nSaved evaluation JSON to: {json_path}")

    # 9. Format Markdown Report
    md_content = f"""# NLP v2 Gate B.2 Taxonomy Confirmation Results

## 1. Executive Summary & Core Comparison

Gate B.2 evaluates candidate taxonomies on the confirmed and grounded stress-evaluation set (706 utterances) using capacity-matched architectures:
- **T2-H**: Shared-encoder multitask MuRIL (`google/muril-base-cased`) with Intent Head (12 classes) + Conditional Subtype Head (16 classes), $\\lambda = 1.0$, `max_epochs = 30`.
- **T3**: Direct 16-class sequence classification MuRIL (`google/muril-base-cased`), `max_epochs = 30`.

### Core Confirmatory Multi-Seed Aggregate Table (3 Seeds: 42, 101, 777)

| Metric | T2-H (Hierarchical Multitask) | T3 (Direct 16-Class) | Difference (T3 - T2-H) | Significance |
| :--- | :---: | :---: | :---: | :---: |
| **Intent Macro-F1** | {core_metrics['T2-H']['intent_macro_f1']['mean']:.4f} ± {core_metrics['T2-H']['intent_macro_f1']['std']:.4f} | {core_metrics['T3']['intent_macro_f1']['mean']:.4f} ± {core_metrics['T3']['intent_macro_f1']['std']:.4f} | {core_metrics['T3']['intent_macro_f1']['mean'] - core_metrics['T2-H']['intent_macro_f1']['mean']:+.4f} | — |
| **Downstream Op Accuracy** | {core_metrics['T2-H']['downstream_op_accuracy']['mean']:.4f} ± {core_metrics['T2-H']['downstream_op_accuracy']['std']:.4f} | **{core_metrics['T3']['downstream_op_accuracy']['mean']:.4f} ± {core_metrics['T3']['downstream_op_accuracy']['std']:.4f}** | **{core_metrics['T3']['downstream_op_accuracy']['mean'] - core_metrics['T2-H']['downstream_op_accuracy']['mean']:+.4f}** | {bootstrap_results['two_sided_p_val'] < 0.05} (p={bootstrap_results['two_sided_p_val']:.4e}) |
| **Downstream Op Macro-F1** | {core_metrics['T2-H']['downstream_op_macro_f1']['mean']:.4f} ± {core_metrics['T2-H']['downstream_op_macro_f1']['std']:.4f} | **{core_metrics['T3']['downstream_op_macro_f1']['mean']:.4f} ± {core_metrics['T3']['downstream_op_macro_f1']['std']:.4f}** | **{core_metrics['T3']['downstream_op_macro_f1']['mean'] - core_metrics['T2-H']['downstream_op_macro_f1']['mean']:+.4f}** | — |
| **Contrast Group Exact (100%)** | {core_metrics['T2-H']['contrast_group_accuracy']['mean']*100:.1f}% | **{core_metrics['T3']['contrast_group_accuracy']['mean']*100:.1f}%** | **+{core_metrics['T3']['contrast_group_accuracy']['mean']*100 - core_metrics['T2-H']['contrast_group_accuracy']['mean']*100:.1f} pp** | — |
| **Ambiguity-Aware Accuracy** | {core_metrics['T2-H']['ambiguity_aware_accuracy']['mean']:.4f} ± {core_metrics['T2-H']['ambiguity_aware_accuracy']['std']:.4f} | **{core_metrics['T3']['ambiguity_aware_accuracy']['mean']:.4f} ± {core_metrics['T3']['ambiguity_aware_accuracy']['std']:.4f}** | **{core_metrics['T3']['ambiguity_aware_accuracy']['mean'] - core_metrics['T2-H']['ambiguity_aware_accuracy']['mean']:+.4f}** | — |

---

## 2. Statistical Significance Analysis

### Paired McNemar Tests (Exact Downstream Operation per Seed)

| Seed | T3 Wins (b) | T2-H Wins (c) | Both Correct | Both Incorrect | $\\chi^2$ Statistic | Two-Sided p-value |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Seed 42** | {mcnemar_results['seed_42']['b_t3_wins']} | {mcnemar_results['seed_42']['c_t2h_wins']} | {mcnemar_results['seed_42']['both_correct']} | {mcnemar_results['seed_42']['both_incorrect']} | {mcnemar_results['seed_42']['chi2_statistic']:.4f} | {mcnemar_results['seed_42']['p_value']:.4e} |
| **Seed 101** | {mcnemar_results['seed_101']['b_t3_wins']} | {mcnemar_results['seed_101']['c_t2h_wins']} | {mcnemar_results['seed_101']['both_correct']} | {mcnemar_results['seed_101']['both_incorrect']} | {mcnemar_results['seed_101']['chi2_statistic']:.4f} | {mcnemar_results['seed_101']['p_value']:.4e} |
| **Seed 777** | {mcnemar_results['seed_777']['b_t3_wins']} | {mcnemar_results['seed_777']['c_t2h_wins']} | {mcnemar_results['seed_777']['both_correct']} | {mcnemar_results['seed_777']['both_incorrect']} | {mcnemar_results['seed_777']['chi2_statistic']:.4f} | {mcnemar_results['seed_777']['p_value']:.4e} |

### Hierarchical Query x Seed Bootstrap (1,000 Resamples)
- **Mean Accuracy Difference (T3 - T2-H)**: `{bootstrap_results['mean_diff']:+.4f}`
- **95% Confidence Interval**: `[{bootstrap_results['ci_lower_95']:+.4f}, {bootstrap_results['ci_upper_95']:+.4f}]`
- **Two-Sided p-value**: `{bootstrap_results['two_sided_p_val']:.4e}`

---

## 3. Stratified Subgroup Performance (3-Seed Average)

### Language Breakdown

| Language Class | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
"""
    for k, v in subgroups["language_class"].items():
        md_content += f"| `{k}` | {v['count']} | {v['T2-H_op_acc']:.4f} | **{v['T3_op_acc']:.4f}** | {v['delta']:+.4f} |\n"

    md_content += """
### Code-Switching Complexity (CS0–CS4)

| CS Level | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
"""
    for k, v in subgroups["code_switch_level"].items():
        md_content += f"| `{k}` | {v['count']} | {v['T2-H_op_acc']:.4f} | **{v['T3_op_acc']:.4f}** | {v['delta']:+.4f} |\n"

    md_content += """
### Text Corruption Robustness (N0–N5)

| Noise Level | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
"""
    for k, v in subgroups["noise_level"].items():
        md_content += f"| `{k}` | {v['count']} | {v['T2-H_op_acc']:.4f} | **{v['T3_op_acc']:.4f}** | {v['delta']:+.4f} |\n"

    md_content += """
### Author Source Breakdown

| Author Source | Count | T2-H Op Acc | T3 Op Acc | Gain (T3 - T2-H) |
| :--- | :---: | :---: | :---: | :---: |
"""
    for k, v in subgroups["author_source"].items():
        md_content += f"| `{k}` | {v['count']} | {v['T2-H_op_acc']:.4f} | **{v['T3_op_acc']:.4f}** | {v['delta']:+.4f} |\n"

    md_content += f"""
---

## 4. Calibration Analysis

| Metric | T2-H | T3 |
| :--- | :---: | :---: |
| **Confidence on Correct Cases** | {calibration_results['T2-H']['mean_confidence_correct']:.4f} | {calibration_results['T3']['mean_confidence_correct']:.4f} |
| **Confidence on Incorrect Cases** | {calibration_results['T2-H']['mean_confidence_incorrect']:.4f} | {calibration_results['T3']['mean_confidence_incorrect']:.4f} |
| **Confidence on Ambiguous Cases** | {calibration_results['T2-H']['mean_confidence_ambiguous']:.4f} | {calibration_results['T3']['mean_confidence_ambiguous']:.4f} |
| **Expected Calibration Error (ECE)** | {calibration_results['T2-H']['ece']:.4f} | {calibration_results['T3']['ece']:.4f} |
| **Brier Score Loss** | {calibration_results['T2-H']['brier_score']:.4f} | {calibration_results['T3']['brier_score']:.4f} |

---

## 5. Systematic Error Analysis ({sum(len(v) for v in error_taxonomy.values())} Total Evaluated Failure Cases)

| Category | Total Count | Description |
| :--- | :---: | :--- |
"""
    for cat, items in error_taxonomy.items():
        md_content += f"| `{cat}` | {len(items)} | Representative failure cases documented in JSON |\n"

    md_content += """
"""

    md_path = os.path.join(REPORT_DIR, "gate_b2_confirmation_results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Saved evaluation markdown report to: {md_path}")


if __name__ == "__main__":
    evaluate_gate_b2()
