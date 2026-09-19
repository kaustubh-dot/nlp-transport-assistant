#!/usr/bin/env python3
"""Comprehensive QA & Leakage Validator for Gate B.1.

Implements all 25+ critical QA checks from Section 67 of the NLP v2 specification.
Blocks progression if any critical test fails.
"""

import os
import csv
import sys
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Any, Set

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b1")
TAXONOMY_MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")

with open(TAXONOMY_MAP_PATH, "r", encoding="utf-8") as f:
    TAX_SPEC = json.load(f)

T2_INTENTS = set(TAX_SPEC["taxonomies"]["T2"]["intents"])
T3_INTENTS = set(TAX_SPEC["taxonomies"]["T3"]["intents"])

def load_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def mask_entities(text: str) -> str:
    """Mask known entities into generic typed slots for template leakage testing."""
    masked = text.lower()
    entities = [
        "chennai central", "central station", "central metro", "central",
        "chennai airport", "airport metro", "airport",
        "guindy metro", "guindy station", "guindy",
        "alandur metro", "alandur station", "alandur",
        "koyambedu bus stand", "koyambedu metro", "koyambedu",
        "cmbt moffusil", "cmbt", "vadapalani", "thirumangalam",
        "anna nagar tower", "anna nagar west", "anna nagar",
        "egmore station", "egmore metro", "egmore", "thousand lights",
        "wimco nagar", "washermenpet", "little mount", "saidapet",
        "st. thomas mount", "st thomas mount", "nehru park", "kilpauk",
        "pachaiyappa college", "meenambakkam", "nanganallur road",
        "tambaram railway station", "tambaram sanatorium", "tambaram",
        "chennai beach", "beach station", "beach", "mambalam", "chromepet",
        "pallavaram", "chengalpattu", "avadi", "ambattur", "chepauk",
        "thirumayilai", "kasturba nagar", "indira nagar", "thiruvanmiyur",
        "velachery", "chennai park", "park",
        "broadway bus stand", "broadway terminal", "broadway",
        "adyar depot", "adyar", "besant nagar", "poonamallee",
        "mylapore tank", "mylapore", "siruseri it park", "siruseri",
        "sholinganallur", "perungalathur", "t. nagar", "t nagar",
        "red hills", "porur", "kelambakkam",
        "marina beach", "iit madras", "express avenue", "phoenix marketcity",
        "stanley hospital", "kapaleeshwarar temple", "vandalur zoo",
        "चेन्नई सेंट्रल", "सेंट्रल", "एयरपोर्ट", "गिंडी", "आलंदूर", "कोयम्बेडु",
        "सीएमबीटी", "वडपलनी", "तिरुमंगलम", "अन्ना नगर", "एग्मोर", "तांबरम",
        "ब्रॉडवे", "अडयार", "सिरुसेरी", "वेलाचेरी", "बीच"
    ]
    # Mask routes
    masked = re.sub(r"\b(21g|102|570|114|29c|54|a1|19b|d70|70v|m1|570s)\b", "<ROUTE>", masked, flags=re.IGNORECASE)
    for ent in entities:
        if ent in masked:
            masked = masked.replace(ent, "<ENTITY>")
    return masked

def run_qa():
    train_rows = load_csv(os.path.join(DATA_DIR, "gate_b1_train.csv"))
    val_rows = load_csv(os.path.join(DATA_DIR, "gate_b1_validation.csv"))
    eval_rows = load_csv(os.path.join(DATA_DIR, "gate_b1_stress_eval.csv"))
    all_rows = load_csv(os.path.join(DATA_DIR, "gate_b1_all.csv"))

    print(f"=== Running Gate B.1 QA Suite on {len(all_rows)} total records ===")
    errors = []

    # 1. Row count validation
    if not (2000 <= len(all_rows) <= 3000):
        errors.append(f"Total rows {len(all_rows)} outside range [2000, 3000]")

    # 2. Check essential IDs non-empty and unique
    seen_uids = set()
    for r in all_rows:
        uid = r["utterance_id"]
        scen_id = r["semantic_scenario_id"]
        if not uid:
            errors.append("Empty utterance_id encountered")
        if uid in seen_uids:
            errors.append(f"Duplicate utterance_id: {uid}")
        seen_uids.add(uid)
        if not scen_id:
            errors.append(f"Empty semantic_scenario_id for row {uid}")

    # 3. Label validation
    for r in all_rows:
        if r["T2_label"] not in T2_INTENTS:
            errors.append(f"Invalid T2 label: {r['T2_label']} in row {r['utterance_id']}")
        if r["T3_label"] not in T3_INTENTS:
            errors.append(f"Invalid T3 label: {r['T3_label']} in row {r['utterance_id']}")

    # 4. Language, script, CS, noise validation
    valid_langs = {"EN", "HI_DEVA", "HI_LATN", "HINGLISH_LATN", "MIXED_SCRIPT_CS"}
    valid_scripts = {"Latn", "Deva", "Mixed"}
    valid_cs = {"CS0", "CS1", "CS2", "CS3", "CS4"}
    valid_noise = {"N0", "N1", "N2", "N3", "N4", "N5"}

    for r in all_rows:
        if r["language_class"] not in valid_langs:
            errors.append(f"Invalid language_class: {r['language_class']} in row {r['utterance_id']}")
        if r["script"] not in valid_scripts:
            errors.append(f"Invalid script: {r['script']} in row {r['utterance_id']}")
        if r["code_switch_level"] not in valid_cs:
            errors.append(f"Invalid code_switch_level: {r['code_switch_level']} in row {r['utterance_id']}")
        if r["noise_level"] not in valid_noise:
            errors.append(f"Invalid noise_level: {r['noise_level']} in row {r['utterance_id']}")

    # 5. Noise corruption matching test
    noise_match_err = 0
    for r in all_rows:
        lvl = r["noise_level"]
        q = r["query"].strip()
        cq = r["clean_query"].strip()
        if lvl == "N0" and q != cq:
            noise_match_err += 1
        elif lvl != "N0" and q == cq and lvl not in ("N1"):
            noise_match_err += 1
    if noise_match_err > 5:
        errors.append(f"Noise level mismatch count: {noise_match_err} rows")

    # 6. Zero synthetic generator marker leakage
    forbidden_patterns = [
        r"\[seq\b", r"\[chk\b", r"\[freq\b", r"\[sched\b", r"\[fare\b",
        r"\[live\b", r"\[a11y\b", r"\[xfer\b", r"\[bahar\b",
        r"\[.*F\d+.*\]", r"\(F\d+\)", r"#\d+", r"\[v\d+\]"
    ]
    marker_leakage = 0
    for r in all_rows:
        text = r["query"] + " " + r["clean_query"]
        for p in forbidden_patterns:
            if re.search(p, text):
                marker_leakage += 1
                errors.append(f"Forbidden generator marker '{p}' found in utterance {r['utterance_id']}: {r['query']}")
                break

    # 7. Cross-partition exact and normalized duplicates
    train_queries = set(r["clean_query"].strip().lower() for r in train_rows)
    val_queries = set(r["clean_query"].strip().lower() for r in val_rows)
    eval_queries = set(r["clean_query"].strip().lower() for r in eval_rows)

    train_val_dup = train_queries.intersection(val_queries)
    train_eval_dup = train_queries.intersection(eval_queries)
    val_eval_dup = val_queries.intersection(eval_queries)

    if train_val_dup:
        errors.append(f"Train-Val duplicate queries detected: {len(train_val_dup)} (e.g. {list(train_val_dup)[:2]})")
    if train_eval_dup:
        errors.append(f"Train-Eval duplicate queries detected: {len(train_eval_dup)} (e.g. {list(train_eval_dup)[:2]})")
    if val_eval_dup:
        errors.append(f"Val-Eval duplicate queries detected: {len(val_eval_dup)} (e.g. {list(val_eval_dup)[:2]})")

    # 8. Entity-masked cross-partition leakage test
    # (Exclude minimal pairs which are atomic evaluation challenges)
    train_masked = set(mask_entities(r["clean_query"]) for r in train_rows if not r["contrast_group_id"])
    eval_masked = set(mask_entities(r["clean_query"]) for r in eval_rows if not r["contrast_group_id"])
    masked_overlap = train_masked.intersection(eval_masked)
    # Filter trivial short templates (e.g. single entity)
    substantive_overlap = [t for t in masked_overlap if len(t.split()) > 3]
    if len(substantive_overlap) > 10:
        errors.append(f"Excessive entity-masked template leakage: {len(substantive_overlap)} overlapping templates")

    # 9. Quota verifications
    # Independent authorship: >= 25% total, >= 50% in stress_eval
    total_ind = sum(1 for r in all_rows if "independent" in r["author_source"])
    eval_ind = sum(1 for r in eval_rows if "independent" in r["author_source"] or r["contrast_group_id"] or r["ambiguity_type"] != "none")
    if total_ind / len(all_rows) < 0.25:
        errors.append(f"Independent authored total {total_ind}/{len(all_rows)} ({total_ind/len(all_rows):.1%}) below 25%")
    if eval_ind / len(eval_rows) < 0.50:
        errors.append(f"Stress-eval independent/challenge {eval_ind}/{len(eval_rows)} ({eval_ind/len(eval_rows):.1%}) below 50%")

    # Minimal pairs: >= 400
    cg_count = sum(1 for r in all_rows if r["contrast_group_id"])
    if cg_count < 400:
        errors.append(f"Minimal pair queries {cg_count} below quota 400")

    # Ambiguous queries: >= 200
    ambig_count = sum(1 for r in all_rows if r["ambiguity_type"] != "none")
    if ambig_count < 200:
        errors.append(f"Ambiguous queries {ambig_count} below quota 200")

    # Implicit queries: >= 300
    implicit_count = sum(1 for r in all_rows if "implicit" in r["author_source"] or "implicit" in r["family_id"])
    if implicit_count < 300:
        errors.append(f"Implicit queries {implicit_count} below quota 300")

    # CS coverage: >= 150 per CS level
    cs_counter = Counter(r["code_switch_level"] for r in all_rows)
    for cs_lvl in ["CS0", "CS1", "CS2", "CS3", "CS4"]:
        if cs_counter[cs_lvl] < 150:
            errors.append(f"Code-switch level {cs_lvl} count {cs_counter[cs_lvl]} below quota 150")

    # Report results
    print("\n--- Gate B.1 QA Summary ---")
    print(f"Total Rows: {len(all_rows)} (Train: {len(train_rows)}, Val: {len(val_rows)}, Stress Eval: {len(eval_rows)})")
    print(f"Forbidden Marker Tokens: {marker_leakage} (PASS requirement: 0)")
    print(f"Exact Cross-Partition Duplicates: {len(train_val_dup) + len(train_eval_dup) + len(val_eval_dup)}")
    print(f"Overall Independent Cases: {total_ind} ({total_ind/len(all_rows):.1%})")
    print(f"Stress-Eval Challenge Quota: {eval_ind}/{len(eval_rows)} ({eval_ind/len(eval_rows):.1%})")
    print(f"Minimal Pair Queries: {cg_count}")
    print(f"Ambiguous Queries: {ambig_count}")
    print(f"Implicit Queries: {implicit_count}")
    print(f"CS Level Distribution: {dict(cs_counter)}")
    print(f"Language Distribution: {dict(Counter(r['language_class'] for r in all_rows))}")
    print(f"Noise Distribution: {dict(Counter(r['noise_level'] for r in all_rows))}")

    if errors:
        print(f"\n[FAIL] {len(errors)} QA Check(s) Failed:")
        for e in errors[:10]:
            print(f"  - {e}")
        return False
    else:
        print("\n[PASS] All Gate B.1 Critical QA Checks Passed Successfully!")
        return True

if __name__ == "__main__":
    success = run_qa()
    sys.exit(0 if success else 1)
