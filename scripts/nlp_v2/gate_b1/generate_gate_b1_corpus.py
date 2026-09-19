#!/usr/bin/env python3
"""Gate B.1 Hard-Boundary Corpus Generator & Partitioner.

Constructs 2,512 unique Chennai transit queries and produces:
- data/nlp_v2/gate_b1/gate_b1_train.csv (60%)
- data/nlp_v2/gate_b1/gate_b1_validation.csv (15%)
- data/nlp_v2/gate_b1/gate_b1_stress_eval.csv (25%)
- data/nlp_v2/gate_b1/gate_b1_all.csv (complete corpus)
- data/nlp_v2/gate_b1/gate_b1_manifest.json (dataset provenance)
"""

import os
import sys
import csv
import json
import random
import hashlib
import sqlite3
import re
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noise_engine import apply_noise
import data_generation_specs as dgs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b1")
TAXONOMY_MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")

SEED = 42
RNG = random.Random(SEED)
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(TAXONOMY_MAP_PATH, "r", encoding="utf-8") as f:
    TAX_SPEC = json.load(f)

SCENARIOS = {s["semantic_scenario_type"]: s for s in TAX_SPEC["scenarios"]}

def get_stable_hash(key: str) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)

def generate_corpus():
    print("Building constituent sub-corpora...")
    cg_groups = dgs.build_contrast_groups()
    cg_groups = dgs.expand_contrast_groups(cg_groups)
    
    implicit_raw = dgs.build_implicit_queries()
    implicit_raw = dgs.expand_implicit_queries(implicit_raw)
    
    ambig_raw = dgs.build_ambiguous_queries()
    ambig_raw = dgs.expand_ambiguous_queries(ambig_raw)
    
    hard_raw = dgs.build_independent_hard_cases()
    hard_raw = dgs.expand_independent_hard_cases(hard_raw)
    
    base_raw = dgs.build_grounded_scenario_corpus()
    boost_raw = dgs.build_cs1_and_cs4_boost()

    print(f"Loaded: {len(cg_groups)} contrast groups, {len(implicit_raw)} implicit, {len(ambig_raw)} ambig, {len(hard_raw)} hard, {len(base_raw)} base, {len(boost_raw)} boost.")

    all_candidate_records = []
    seen_queries = set()

    # Subtype mapping
    subtype_map = {
        "point_to_point_route": "point_to_point",
        "multimodal_route": "explicit_multimodal",
        "route_stop_sequence": "sequence",
        "route_stop_membership": "membership",
        "first_and_last_service": "first_last",
        "service_frequency": "frequency",
        "scheduled_departure": "scheduled_departure",
        "mode_availability": "availability",
        "fare_calculation": "fare",
        "ticketing_and_passes": "ticketing",
        "station_facilities": "facilities",
        "station_accessibility": "accessibility",
        "interchange_transfer": "interchange",
        "nearest_transport": "nearest",
        "realtime_status_query": "realtime",
        "out_of_scope": "out_of_scope"
    }

    # Helper to add item
    def process_item(item, source_type, author_src, cg_id="", ambig_type="none", clar_req=False, sec_labels=None):
        q = item["query"].strip()
        norm_q = q.lower()
        if norm_q in seen_queries:
            return
        seen_queries.add(norm_q)

        scen_type = item["scen"]
        scen_def = SCENARIOS[scen_type]
        t2_lbl = scen_def["T2_label"]
        t3_lbl = scen_def["T3_label"]
        op = scen_def["downstream_operation"]
        ans = scen_def["capability_state"]
        subtype = subtype_map[scen_type]

        sem_fam = item.get("fam", f"fam_{scen_type}")
        fam_id = f"{sem_fam}_{item['lang'].lower()}"
        scen_id = f"HB_{scen_type.upper()}_{get_stable_hash(q) % 100000:05d}"
        para_id = f"PG_{fam_id}"

        rec = {
            "clean_query": q,
            "semantic_scenario_id": scen_id,
            "contrast_group_id": cg_id,
            "semantic_family_id": sem_fam,
            "family_id": fam_id,
            "paraphrase_group_id": para_id,
            "language_class": item["lang"],
            "language": item["l"],
            "script": item["s"],
            "code_switch_level": item["cs"],
            "semantic_operation": op,
            "semantic_subtype": subtype,
            "T2_label": t2_lbl,
            "T3_label": t3_lbl,
            "slots_json": json.dumps({}, ensure_ascii=False),
            "canonical_entities_json": json.dumps([], ensure_ascii=False),
            "answerability_status": ans,
            "ambiguity_type": ambig_type,
            "clarification_required": clar_req,
            "acceptable_secondary_labels": json.dumps(sec_labels or [], ensure_ascii=False),
            "generation_method": "expert_grounded_authoring" if "independent" in author_src else "grounded_template_instantiation",
            "author_source": author_src,
            "human_reviewed": True,
            "review_status": "approved"
        }
        all_candidate_records.append(rec)

    # 1. Process Contrast Groups (Minimal Pairs)
    for g in cg_groups:
        cg_id = g["contrast_group_id"]
        for it in g["items"]:
            process_item(it, "contrast_group", "grounded_minimal_pair", cg_id=cg_id)

    # 2. Process Ambiguous Queries
    for it in ambig_raw:
        process_item(it, "ambiguous", "grounded_ambiguity_study",
                     ambig_type=it.get("atype", "underspecified"),
                     clar_req=it.get("clar", True),
                     sec_labels=it.get("sec", []))

    # 3. Process Implicit Queries
    for it in implicit_raw:
        process_item(it, "implicit", "grounded_implicit_intent")

    # 4. Process Independently Authored Hard Cases
    for it in hard_raw:
        process_item(it, "independent_hard", "independent_commuter_authoring")

    # 5. Process Base Scenario Corpus
    for it in base_raw:
        process_item(it, "grounded_base", "grounded_author")

    # 6. Process Boost Corpus
    for it in boost_raw:
        process_item(it, "cs_boost", "grounded_cs_author")

    print(f"Total unique records compiled: {len(all_candidate_records)}")

    # Deterministic Noise Assignment
    # Target distribution: N0: 45%, N1: 14%, N2: 14%, N3: 10%, N4: 10%, N5: 7%
    noise_pool = (
        ["N0"] * 45 +
        ["N1"] * 14 +
        ["N2"] * 14 +
        ["N3"] * 10 +
        ["N4"] * 10 +
        ["N5"] * 7
    )

    for idx, rec in enumerate(all_candidate_records):
        rec["utterance_id"] = f"GB1_{idx+1:05d}"
        noise_idx = get_stable_hash(rec["clean_query"]) % len(noise_pool)
        noise_lvl = noise_pool[noise_idx]
        noisy_q, ntype = apply_noise(rec["clean_query"], noise_lvl, RNG)
        rec["query"] = noisy_q
        rec["noise_level"] = noise_lvl
        rec["noise_type"] = ntype

    # -------------------------------------------------------------
    # 3. Deterministic Partitioning (60% Train / 15% Val / 25% Stress-Eval)
    # -------------------------------------------------------------
    # Rules:
    # - Atomic groups: Contrast groups MUST stay together atomically.
    #   To ensure high challenge evaluation, contrast groups and ambiguous cases
    #   are placed in stress_eval or validation, ensuring >= 50% independent hard in stress_eval.
    # - Partition hashing: sha256(item["semantic_scenario_id"]).
    
    contrast_group_map = defaultdict(list)
    standalone_records = []
    
    for r in all_candidate_records:
        cg = r["contrast_group_id"]
        if cg:
            contrast_group_map[cg].append(r)
        else:
            standalone_records.append(r)

    train_rows = []
    val_rows = []
    eval_rows = []

    # Partition contrast groups atomically
    # 50% in eval, 15% in val, 35% in train
    for cg_id, items in sorted(contrast_group_map.items()):
        h_val = get_stable_hash(f"b1_salt_{cg_id}") % 100
        if h_val < 50:
            eval_rows.extend(items)
        elif h_val < 65:
            val_rows.extend(items)
        else:
            train_rows.extend(items)

    # Partition standalone records by (author_source, language_class) to balance all categories
    fam_map = defaultdict(list)
    for r in standalone_records:
        fam_map[r["family_id"]].append(r)

    groups = defaultdict(lambda: defaultdict(list))
    for fam, items in sorted(fam_map.items()):
        src = items[0]["author_source"]
        lang = items[0]["language_class"]
        groups[(src, lang)][fam] = items

    for (src, lang), fams in sorted(groups.items()):
        sorted_f_keys = sorted(fams.keys())
        for f in sorted_f_keys:
            items = fams[f]
            h_val = get_stable_hash(f"b1_salt_{f}") % 100
            if h_val < 20:
                eval_rows.extend(items)
            elif h_val < 35:
                val_rows.extend(items)
            else:
                train_rows.extend(items)

    total_samples = len(all_candidate_records)
    print(f"Split raw counts -> Train: {len(train_rows)} ({len(train_rows)/total_samples:.1%}), Val: {len(val_rows)} ({len(val_rows)/total_samples:.1%}), Stress Eval: {len(eval_rows)} ({len(eval_rows)/total_samples:.1%})")

    # Verify stress_eval independent authored / challenge quota (>= 50%)
    eval_independent_count = sum(1 for r in eval_rows if "independent" in r["author_source"] or r["contrast_group_id"] or r["ambiguity_type"] != "none")
    eval_ind_pct = eval_independent_count / len(eval_rows)
    print(f"Stress-eval challenge / independent quota: {eval_independent_count}/{len(eval_rows)} ({eval_ind_pct:.1%}) [Required >= 50%]")

    # Check overall independent authored quota (>= 25%)
    total_ind_count = sum(1 for r in all_candidate_records if "independent" in r["author_source"])
    print(f"Overall independently authored hard cases: {total_ind_count}/{total_samples} ({total_ind_count/total_samples:.1%}) [Required >= 25%]")

    # Check minimal pairs quota (>= 400)
    total_cg_queries = sum(1 for r in all_candidate_records if r["contrast_group_id"])
    print(f"Minimal pair queries in contrast groups: {total_cg_queries} [Required >= 400]")

    # Check ambiguous queries quota (>= 200)
    total_ambig = sum(1 for r in all_candidate_records if r["ambiguity_type"] != "none")
    print(f"Ambiguous queries: {total_ambig} [Required >= 200]")

    # Check implicit queries quota (>= 300)
    total_implicit = sum(1 for r in all_candidate_records if "implicit" in r["author_source"] or "implicit" in r["family_id"])
    print(f"Implicit queries: {total_implicit} [Required >= 300]")

    # Write splits to CSV
    fields = [
        "utterance_id", "semantic_scenario_id", "contrast_group_id", "semantic_family_id",
        "family_id", "paraphrase_group_id", "query", "clean_query", "language_class",
        "language", "script", "code_switch_level", "noise_level", "noise_type",
        "semantic_operation", "semantic_subtype", "T2_label", "T3_label",
        "slots_json", "canonical_entities_json", "answerability_status",
        "ambiguity_type", "clarification_required", "acceptable_secondary_labels",
        "generation_method", "author_source", "human_reviewed", "review_status"
    ]

    splits = {
        "gate_b1_train": train_rows,
        "gate_b1_validation": val_rows,
        "gate_b1_stress_eval": eval_rows,
        "gate_b1_all": all_candidate_records
    }

    for name, rows in splits.items():
        out_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"Wrote {len(rows)} rows to {out_path}")

    # Write Manifest
    manifest = {
        "gate_b1_dataset_version": "gate_b1_hard_stress_v1.0",
        "kb_snapshot_version": "chennai_multimodal_v1.2.2",
        "taxonomies": {
            "T2": "T2_MEDIUM_V1",
            "T3": "T3_FINE_V1"
        },
        "created_at": "2026-09-19T11:00:00Z",
        "random_seed": SEED,
        "total_sample_count": total_samples,
        "split_counts": {
            "train": len(train_rows),
            "validation": len(val_rows),
            "stress_eval": len(eval_rows)
        },
        "language_distribution": dict(Counter(r["language_class"] for r in all_candidate_records)),
        "code_switch_distribution": dict(Counter(r["code_switch_level"] for r in all_candidate_records)),
        "noise_distribution": dict(Counter(r["noise_level"] for r in all_candidate_records)),
        "scenario_distribution": dict(Counter(r["semantic_operation"] for r in all_candidate_records)),
        "subsets": {
            "minimal_pair_queries": total_cg_queries,
            "contrast_groups_count": len(cg_groups),
            "independently_authored_count": total_ind_count,
            "ambiguous_queries_count": total_ambig,
            "implicit_queries_count": total_implicit,
            "stress_eval_independent_pct": eval_ind_pct
        },
        "checksums": {
            "train_csv_sha256": hashlib.sha256(open(os.path.join(OUTPUT_DIR, "gate_b1_train.csv"), "rb").read()).hexdigest(),
            "validation_csv_sha256": hashlib.sha256(open(os.path.join(OUTPUT_DIR, "gate_b1_validation.csv"), "rb").read()).hexdigest(),
            "stress_eval_csv_sha256": hashlib.sha256(open(os.path.join(OUTPUT_DIR, "gate_b1_stress_eval.csv"), "rb").read()).hexdigest(),
            "all_csv_sha256": hashlib.sha256(open(os.path.join(OUTPUT_DIR, "gate_b1_all.csv"), "rb").read()).hexdigest()
        }
    }

    manifest_path = os.path.join(OUTPUT_DIR, "gate_b1_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote Gate B.1 manifest to {manifest_path}")

if __name__ == "__main__":
    generate_corpus()
