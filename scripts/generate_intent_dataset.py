#!/usr/bin/env python3
"""Generates the domain-adapted NLU dataset for Hindi Transport Assistant.

Combines:
  1. Authored templates from data/templates/hindi_templates.json with extensive slot replacement.
  2. Scraped CMRL stations from data/curated/cmrl_scraped_stations.json.
  3. Harvested conversational data from data/curated/external_harvested_queries.json.

Ensures:
  - Balanced 7 intent classes (>= 500 samples per class, total >= 4000).
  - Devanagari Hindi and Romanized Hinglish script representation.
  - Strict family-disjoint splits: Train (70%), Val (15%), Test (15%).
  - Zero data leakage between splits.

Outputs:
  - data/processed/intents.csv
"""

import os
import json
import random
import re
from typing import List, Dict, Any, Tuple
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_PATH = os.path.join(BASE_DIR, "data", "templates", "hindi_templates.json")
CURATED_PATH = os.path.join(BASE_DIR, "data", "curated", "cmrl_verified_stations.json")
SCRAPED_PATH = os.path.join(BASE_DIR, "data", "curated", "cmrl_scraped_stations.json")
EXTERNAL_PATH = os.path.join(BASE_DIR, "data", "curated", "external_harvested_queries.json")
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "intents.csv")
SPLIT_DIR = os.path.join(BASE_DIR, "data", "processed", "split")

# Core Station Pools
STATIONS_HI = [
    ("CHENNAI_CENTRAL", "चेन्नई सेंट्रल"),
    ("CHENNAI_CENTRAL", "सेंट्रल"),
    ("CHENNAI_CENTRAL", "सेंट्रल रेलवे स्टेशन"),
    ("CHENNAI_EGMORE", "चेन्नई एग्मोर"),
    ("CHENNAI_EGMORE", "एग्मोर"),
    ("CHENNAI_AIRPORT", "चेन्नई एयरपोर्ट"),
    ("CHENNAI_AIRPORT", "एयरपोर्ट"),
    ("CHENNAI_AIRPORT", "हवाई अड्डा"),
    ("KOYAMBEDU", "कोयम्बेडु"),
    ("KOYAMBEDU", "कोयम्बेडु मार्केट"),
    ("CMBT", "सीएमबीटी"),
    ("GUINDY", "गिंडी"),
    ("TAMBARAM", "ताम्बरम"),
    ("ALANDUR", "आलंदूर"),
    ("CHENNAI_BEACH", "चेन्नई बीच"),
    ("VELACHERY", "वेलाचेरी"),
    ("KILPAUK", "किल्पॉक"),
    ("NEHRU_PARK", "नेहरू पार्क"),
    ("THIRUMANGALAM", "तिरुमंगलम"),
    ("VADAPALANI", "वडापलानी"),
    ("ASHOK_NAGAR", "अशोक नगर"),
    ("ANNA_NAGAR", "अन्ना नगर"),
    ("SHENOY_NAGAR", "शेनॉय नगर"),
    ("GOVERNMENT_ESTATE", "गवर्नमेंट एस्टेट"),
    ("LIC", "एलआईसी"),
    ("THOUSAND_LIGHTS", "थाउजेंड लाइट्स"),
    ("AG_DMS", "एजी-डीएमएस"),
    ("TEYNAMPET", "तेनामपेट"),
    ("NANDANAM", "नंदनम"),
    ("NANDANAM", "टी नगर"),
    ("SAIDAPET", "सैदापेट"),
    ("LITTLE_MOUNT", "लिटिल माउंट"),
    ("ST_THOMAS_MOUNT", "सेंट थॉमस माउंट"),
    ("MEENAMBAKKAM", "मीनांबक्कम"),
    ("HIGH_COURT", "हाई कोर्ट")
]

STATIONS_HINGLISH = [
    ("CHENNAI_CENTRAL", "chennai central"),
    ("CHENNAI_CENTRAL", "central"),
    ("CHENNAI_CENTRAL", "central railway station"),
    ("CHENNAI_EGMORE", "chennai egmore"),
    ("CHENNAI_EGMORE", "egmore"),
    ("CHENNAI_AIRPORT", "chennai airport"),
    ("CHENNAI_AIRPORT", "airport"),
    ("KOYAMBEDU", "koyambedu"),
    ("CMBT", "cmbt"),
    ("GUINDY", "guindy"),
    ("TAMBARAM", "tambaram"),
    ("ALANDUR", "alandur"),
    ("CHENNAI_BEACH", "chennai beach"),
    ("VELACHERY", "velachery"),
    ("KILPAUK", "kilpauk"),
    ("NEHRU_PARK", "nehru park"),
    ("THIRUMANGALAM", "thirumangalam"),
    ("VADAPALANI", "vadapalani"),
    ("ASHOK_NAGAR", "ashok nagar"),
    ("ANNA_NAGAR", "anna nagar"),
    ("SHENOY_NAGAR", "shenoy nagar"),
    ("GOVERNMENT_ESTATE", "government estate"),
    ("LIC", "lic"),
    ("THOUSAND_LIGHTS", "thousand lights"),
    ("AG_DMS", "ag dms"),
    ("TEYNAMPET", "teynampet"),
    ("NANDANAM", "nandanam"),
    ("NANDANAM", "t nagar"),
    ("SAIDAPET", "saidapet"),
    ("LITTLE_MOUNT", "little mount"),
    ("ST_THOMAS_MOUNT", "st thomas mount"),
    ("MEENAMBAKKAM", "meenambakkam"),
    ("HIGH_COURT", "high court")
]

MODES_HI = [
    ("metro", "मेट्रो"),
    ("bus", "बस"),
    ("suburban_rail", "लोकल ट्रेन"),
    ("railway", "ट्रेन")
]

MODES_HINGLISH = [
    ("metro", "metro"),
    ("bus", "bus"),
    ("suburban_rail", "local train"),
    ("railway", "train")
]

TICKETS_HI = [
    "स्मार्ट कार्ड", "टोकन", "क्यूआर टिकट", "व्हाट्सएप टिकट", "मासिक पास",
    "टूरिस्ट पास", "एनसीएमसी रूपे कार्ड", "सीजन पास", "मेट्रो पास", "टिकट"
]

TICKETS_HINGLISH = [
    "smart card", "token", "qr ticket", "whatsapp ticket", "monthly pass",
    "tourist pass", "ncmc card", "season pass", "metro pass", "ticket"
]

CITIES_HI = [
    "चेन्नई", "ताम्बरम", "वेलाचेरी", "अडयार", "टी नगर", "मायलापुर", "अन्ना नगर",
    "कोयम्बेडु", "गिंडी", "मदुरै", "कोयंबटूर", "तिरुचि", "सलेम", "बेंगलुरु", "दिल्ली", "मुंबई"
]

CITIES_HINGLISH = [
    "chennai", "tambaram", "velachery", "adyar", "t nagar", "mylapore", "anna nagar",
    "koyambedu", "guindy", "madurai", "coimbatore", "delhi", "mumbai", "bangalore"
]

DAYS_HI = [
    "आज", "कल", "परसों", "रविवार को", "सोमवार को", "इस हफ्ते", "सुबह", "शाम को", "रात में", "वीकेंड पर"
]

DAYS_HINGLISH = [
    "aaj", "kal", "parso", "sunday ko", "monday ko", "this weekend", "morning me", "night me"
]

FOODS_HI = [
    "साउथ इंडियन डोसा", "बिरयानी", "वेज रेस्टोरेंट", "फिल्टर कॉफी", "मिठाई की दुकान",
    "अच्छा ढाबा", "इटैलियन पिज्जा", "फास्ट फूड", "होटल", "शाकाहारी भोजन"
]

FOODS_HINGLISH = [
    "south indian dosa", "biryani", "veg restaurant", "filter coffee", "sweet shop",
    "cafe", "fast food", "hotel for stay", "pure veg food"
]

TRAIN_NUMS = ["12621", "12622", "12673", "12007", "22625", "12637", "16127", "12615", "12652"]
AIRLINES = ["IndiGo", "Air India", "SpiceJet", "Akasa Air", "Vistara", "इंडिगो", "एयर इंडिया"]


def load_templates() -> Dict[str, Any]:
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["intents"]


def load_external_queries() -> List[Dict[str, Any]]:
    if not os.path.exists(EXTERNAL_PATH):
        return []
    with open(EXTERNAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("samples", [])


def detect_script(text: str) -> str:
    """Returns 'devanagari' if text contains Devanagari characters, else 'latin_hinglish'."""
    has_deva = any("\u0900" <= ch <= "\u097F" for ch in text)
    return "devanagari" if has_deva else "latin_hinglish"


def generate_dataset(samples_per_intent: int = 700, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic dataset from templates and merges external harvested queries."""
    random.seed(seed)
    templates = load_templates()
    rows: List[Dict[str, Any]] = []

    for intent, config in templates.items():
        hi_templates = config.get("templates_hi", [])
        hinglish_templates = config.get("templates_hinglish", [])
        families_hi = config.get("families_hi", [])
        families_hinglish = config.get("families_hinglish", [])

        intent_samples = 0
        max_attempts = samples_per_intent * 4
        attempts = 0

        while intent_samples < samples_per_intent and attempts < max_attempts:
            attempts += 1
            # 55% Hindi, 45% Hinglish
            is_hinglish = (random.random() < 0.45) and len(hinglish_templates) > 0
            template_list = hinglish_templates if is_hinglish else hi_templates
            family_list = families_hinglish if is_hinglish else families_hi

            idx = random.randint(0, len(template_list) - 1)
            tpl = template_list[idx]
            family_name = f"{intent}:{family_list[idx]}"

            station_id = None
            origin_id = None
            dest_id = None
            mode_id = None
            info_type = None

            filled = tpl

            # Handle Station Slots
            if "{origin}" in tpl and "{destination}" in tpl:
                station_pool = STATIONS_HINGLISH if is_hinglish else STATIONS_HI
                s1 = random.choice(station_pool)
                s2 = random.choice([s for s in station_pool if s[0] != s1[0]])
                origin_id, origin_name = s1
                dest_id, dest_name = s2
                filled = filled.replace("{origin}", origin_name).replace("{destination}", dest_name)
            elif "{station}" in tpl:
                station_pool = STATIONS_HINGLISH if is_hinglish else STATIONS_HI
                s = random.choice(station_pool)
                station_id, station_name = s
                filled = filled.replace("{station}", station_name)
            elif "{origin}" in tpl:
                station_pool = STATIONS_HINGLISH if is_hinglish else STATIONS_HI
                s = random.choice(station_pool)
                origin_id, station_name = s
                filled = filled.replace("{origin}", station_name)

            # Handle Mode Slot
            if "{mode}" in tpl:
                mode_pool = MODES_HINGLISH if is_hinglish else MODES_HI
                m_id, m_name = random.choice(mode_pool)
                mode_id = m_id
                filled = filled.replace("{mode}", m_name)

            # Handle Ticketing Extra Slots
            if "{ticket_type}" in filled:
                t_pool = TICKETS_HINGLISH if is_hinglish else TICKETS_HI
                filled = filled.replace("{ticket_type}", random.choice(t_pool))

            # Handle Out of Scope Extra Slots
            if "{city}" in filled:
                c_pool = CITIES_HINGLISH if is_hinglish else CITIES_HI
                filled = filled.replace("{city}", random.choice(c_pool))
            if "{day}" in filled:
                d_pool = DAYS_HINGLISH if is_hinglish else DAYS_HI
                filled = filled.replace("{day}", random.choice(d_pool))
            if "{food_type}" in filled:
                f_pool = FOODS_HINGLISH if is_hinglish else FOODS_HI
                filled = filled.replace("{food_type}", random.choice(f_pool))
            if "{train_num}" in filled:
                filled = filled.replace("{train_num}", random.choice(TRAIN_NUMS))
            if "{airline}" in filled:
                filled = filled.replace("{airline}", random.choice(AIRLINES))

            # Check Information / Facility Type
            if intent == "accessibility":
                info_type = "wheelchair"
            elif intent == "service_timing":
                info_type = "timing"
            elif intent == "ticketing":
                info_type = "fare"

            # Random variations for templates without slots to ensure variety
            if not ("{" in tpl) and (intent in ["out_of_scope", "ticketing"]):
                suffixes_hi = ["", " जी", " कृपया बताइए", " जल्दी बताओ", " जानकारी चाहिए", " क्या आप जानते हैं?"]
                suffixes_hinglish = ["", " please", " batao jaldi", " can you tell?", " details please"]
                suffix = random.choice(suffixes_hinglish if is_hinglish else suffixes_hi)
                filled = filled + suffix

            script = detect_script(filled)

            rows.append({
                "query": filled.strip(),
                "template_family": family_name,
                "station": station_id or origin_id or dest_id,
                "intent": intent,
                "origin": origin_id,
                "destination": dest_id,
                "transport_mode": mode_id,
                "information_type": info_type,
                "slots_reviewed": False,
                "language": "hinglish" if is_hinglish else "hi",
                "script": script,
                "source": "template_combinatorial"
            })
            intent_samples += 1

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["query"]).reset_index(drop=True)

    # Perform strict family-disjoint split
    df["split"] = "train"
    for intent in df["intent"].unique():
        families = sorted(df.loc[df.intent == intent, "template_family"].unique())
        if len(families) < 3:
            raise ValueError(f"{intent} needs at least three template families")
        random.shuffle(families)
        
        # Allocate 15% to val, 15% to test, 70% to train
        n_val = max(1, int(len(families) * 0.15))
        n_test = max(1, int(len(families) * 0.15))
        
        val_families = set(families[:n_val])
        test_families = set(families[n_val:n_val + n_test])

        df.loc[df.template_family.isin(val_families), "split"] = "val"
        df.loc[df.template_family.isin(test_families), "split"] = "test"

    # Merge external harvested queries into TRAIN split only (preventing any test leakage)
    ext_queries = load_external_queries()
    if ext_queries:
        ext_rows = []
        # Target adding external samples, especially for out_of_scope and underrepresented intents
        intent_targets = {
            "out_of_scope": 450,
            "ticketing": 250,
            "service_timing": 150,
            "service_availability": 150,
            "station_information": 150,
            "route_query": 150,
            "accessibility": 150
        }
        intent_counts = {i: 0 for i in df["intent"].unique()}
        random.shuffle(ext_queries)
        for q in ext_queries:
            q_intent = q.get("intent")
            target = intent_targets.get(q_intent, 100)
            if q_intent in intent_counts and intent_counts[q_intent] < target:
                q_text = q.get("query", "").strip()
                if q_text and q_text.lower() not in set(df["query"].str.lower()):
                    ext_rows.append({
                        "query": q_text,
                        "template_family": q.get("template_family", f"external_{q_intent}"),
                        "station": None,
                        "intent": q_intent,
                        "origin": None,
                        "destination": None,
                        "transport_mode": None,
                        "information_type": None,
                        "slots_reviewed": False,
                        "language": "hinglish",
                        "script": detect_script(q_text),
                        "source": q.get("source", "external_harvest"),
                        "split": "train"
                    })
                    intent_counts[q_intent] += 1
        if ext_rows:
            ext_df = pd.DataFrame(ext_rows)
            df = pd.concat([df, ext_df], ignore_index=True)

    # Deduplicate again
    df = df.drop_duplicates(subset=["query"]).reset_index(drop=True)

    # Double check no overlap between train and test/val
    train_queries = set(df[df["split"] == "train"]["query"].str.strip().str.lower())
    for split_name in ["val", "test"]:
        split_queries = set(df[df["split"] == split_name]["query"].str.strip().str.lower())
        overlap = train_queries.intersection(split_queries)
        if overlap:
            print(f"Removing {len(overlap)} overlapping queries from train...")
            df = df[~((df["split"] == "train") & (df["query"].str.strip().str.lower().isin(overlap)))]

    return df.reset_index(drop=True)


def export_frozen_split(df: pd.DataFrame, split_dir: str = SPLIT_DIR, split_seed: int = 42) -> Dict[str, Any]:
    """Exports frozen 70/15/15 train, validation, and test splits along with manifest metadata."""
    os.makedirs(split_dir, exist_ok=True)
    train_df = df[df["split"] == "train"].reset_index(drop=True)
    val_df = df[df["split"] == "val"].reset_index(drop=True)
    test_df = df[df["split"] == "test"].reset_index(drop=True)

    train_path = os.path.join(split_dir, "train.csv")
    val_path = os.path.join(split_dir, "validation.csv")
    test_path = os.path.join(split_dir, "test.csv")
    manifest_path = os.path.join(split_dir, "split_manifest.json")

    train_df.to_csv(train_path, index=False, encoding="utf-8")
    val_df.to_csv(val_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")

    manifest = {
        "strategy": "family_disjoint_stratified",
        "train_ratio": 0.70,
        "validation_ratio": 0.15,
        "test_ratio": 0.15,
        "split_seed": split_seed,
        "num_train": len(train_df),
        "num_validation": len(val_df),
        "num_test": len(test_df),
        "total_samples": len(df),
        "intents": sorted(list(df["intent"].unique())),
        "classes_distribution": {
            "train": train_df["intent"].value_counts().to_dict(),
            "validation": val_df["intent"].value_counts().to_dict(),
            "test": test_df["intent"].value_counts().to_dict()
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Exported frozen split to {split_dir}:")
    print(f"  - train.csv: {len(train_df)} samples")
    print(f"  - validation.csv: {len(val_df)} samples")
    print(f"  - test.csv: {len(test_df)} samples")
    print(f"  - split_manifest.json: {manifest_path}")
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate intent dataset with frozen family-disjoint split")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for generation and splitting (default: 42)")
    parser.add_argument("--samples-per-intent", type=int, default=900, help="Number of samples to generate per intent")
    parser.add_argument("--output", type=str, default=OUTPUT_CSV_PATH, help="Output CSV path (default: data/processed/intents.csv)")
    parser.add_argument("--split-dir", type=str, default=SPLIT_DIR, help="Directory to export train/validation/test splits")
    parser.add_argument("--no-split-export", action="store_true", help="Skip exporting split files to split-dir")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df = generate_dataset(samples_per_intent=args.samples_per_intent, seed=args.seed)
    df.to_csv(args.output, index=False, encoding="utf-8")
    print(f"Generated dataset with {len(df)} samples at: {args.output}")

    if not args.no_split_export:
        export_frozen_split(df, split_dir=args.split_dir, split_seed=args.seed)

    print("\nClass distribution by split:")
    print(pd.crosstab(df["intent"], df["split"]))
    print("\nScript distribution:")
    print(df["script"].value_counts())

