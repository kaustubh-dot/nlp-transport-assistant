#!/usr/bin/env python3
"""Lexical Shortcut Audit for Gate B.1.

Audits unigrams, bigrams, and character n-grams across T2 and T3 taxonomies.
Identifies whether any intent is artificially dominated by single giveaway tokens
like 'frequency', 'fare', 'live', 'interchange', 'first', 'last', 'schedule'.
Produces:
- reports/nlp_v2/gate_b1/lexical_shortcut_audit.json
- reports/nlp_v2/gate_b1/lexical_shortcut_audit.md
"""

import os
import csv
import json
import math
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b1", "gate_b1_all.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "nlp_v2", "gate_b1")
os.makedirs(REPORTS_DIR, exist_ok=True)

KEY_TRANSIT_TERMS = [
    "frequency", "headway", "interval",
    "fare", "ticket", "tariff", "cost", "charge",
    "live", "gps", "delay", "tracker",
    "interchange", "change", "transfer", "switch",
    "sequence", "stops", "halts", "list",
    "membership", "halt", "stop", "touch",
    "first", "early", "earliest",
    "last", "night", "midnight",
    "schedule", "timetable", "scheduled"
]

def tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())

import re

def compute_n_grams(tokens: List[str]) -> List[str]:
    ngrams = list(tokens)
    for i in range(len(tokens) - 1):
        ngrams.append(f"{tokens[i]}_{tokens[i+1]}")
    return ngrams

def run_audit():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} records for Lexical Shortcut Audit.")

    audit_results = {
        "dataset_version": "gate_b1_hard_stress_v1.0",
        "sample_count": len(rows),
        "taxonomies": {}
    }

    markdown_lines = [
        "# Gate B.1 Pre-Training Lexical Shortcut Audit",
        "",
        f"**Dataset:** Gate B.1 Hard-Boundary Stress Corpus ({len(rows)} examples)  ",
        "**Target:** Evaluate token-to-label association, conditional purity $P(\\text{label} \\mid \\text{token})$, and potential single-word lexical giveaways across candidate taxonomies T2 and T3.  ",
        "",
        "---",
        ""
    ]

    for tax in ["T2", "T3"]:
        label_key = f"{tax}_label"
        labels = [r[label_key] for r in rows]
        label_counts = Counter(labels)
        total_samples = len(labels)

        # Count token-label co-occurrences
        token_label_counts = defaultdict(Counter)
        token_counts = Counter()

        for r in rows:
            lbl = r[label_key]
            tokens = compute_n_grams(tokenize(r["query"]))
            for tok in set(tokens):
                token_counts[tok] += 1
                token_label_counts[tok][lbl] += 1

        # Analyze key transit terms
        key_term_analysis = []
        for term in KEY_TRANSIT_TERMS:
            c = token_counts[term]
            if c > 0:
                dist = dict(token_label_counts[term])
                top_label, top_count = token_label_counts[term].most_common(1)[0]
                purity = top_count / c
                key_term_analysis.append({
                    "term": term,
                    "frequency": c,
                    "dominant_label": top_label,
                    "purity": round(purity, 4),
                    "distribution": dist
                })

        # Find tokens with extreme association (frequency >= 10, purity >= 0.95)
        extreme_tokens = []
        for tok, c in token_counts.items():
            if c >= 10:
                top_label, top_count = token_label_counts[tok].most_common(1)[0]
                purity = top_count / c
                if purity >= 0.95:
                    extreme_tokens.append({
                        "token": tok,
                        "frequency": c,
                        "dominant_label": top_label,
                        "purity": round(purity, 4)
                    })

        extreme_tokens.sort(key=lambda x: (x["purity"], x["frequency"]), reverse=True)

        audit_results["taxonomies"][tax] = {
            "key_transit_terms": key_term_analysis,
            "extreme_tokens_count": len(extreme_tokens),
            "extreme_tokens": extreme_tokens[:30]
        }

        markdown_lines.extend([
            f"## {tax} Taxonomy Lexical Audit",
            "",
            f"### Monitored Key Transit Terms in {tax}",
            "",
            "| Term | Frequency | Dominant Label | Purity $P(\\text{Label} \\mid \\text{Term})$ | Distributed Labels Count |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ])
        for kta in key_term_analysis:
            markdown_lines.append(
                f"| `{kta['term']}` | {kta['frequency']} | `{kta['dominant_label']}` | {kta['purity']:.2%} | {len(kta['distribution'])} |"
            )

        markdown_lines.extend([
            "",
            f"### Highly Predictive Tokens in {tax} (Min Frequency 10, Purity $\\ge$ 95%)",
            "",
            f"Found **{len(extreme_tokens)}** tokens meeting extreme single-label association criteria.",
            ""
        ])
        if extreme_tokens:
            markdown_lines.extend([
                "| Token | Frequency | Dominant Label | Purity |",
                "| :--- | :--- | :--- | :--- |"
            ])
            for et in extreme_tokens[:15]:
                markdown_lines.append(f"| `{et['token']}` | {et['frequency']} | `{et['dominant_label']}` | {et['purity']:.2%} |")
        markdown_lines.append("\n---\n")

    # Save JSON and MD
    json_path = os.path.join(REPORTS_DIR, "lexical_shortcut_audit.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)
        f.write("\n")

    md_path = os.path.join(REPORTS_DIR, "lexical_shortcut_audit.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))

    print(f"Wrote Lexical Shortcut Audit to {json_path} and {md_path}")

if __name__ == "__main__":
    run_audit()
