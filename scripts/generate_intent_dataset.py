#!/usr/bin/env python3
"""Generates the domain-adapted NLU dataset for Hindi Transport Assistant.

Uses templates from data/templates/hindi_templates.json, canonical stations,
transport modes, and seeds to produce a balanced, stratified dataset:
  - Train: 70%
  - Validation: 15%
  - Test: 15%

Outputs: data/processed/intents.csv
"""

import os
import json
import random
import pandas as pd
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_PATH = os.path.join(BASE_DIR, "data", "templates", "hindi_templates.json")
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "intents.csv")

# Representative station aliases for template filling
STATIONS_HI = [
    ("CHENNAI_CENTRAL", "चेन्नई सेंट्रल"),
    ("CHENNAI_CENTRAL", "सेंट्रल"),
    ("CHENNAI_EGMORE", "चेन्नई एग्मोर"),
    ("CHENNAI_EGMORE", "एग्मोर"),
    ("CHENNAI_AIRPORT", "चेन्नई एयरपोर्ट"),
    ("CHENNAI_AIRPORT", "एयरपोर्ट"),
    ("KOYAMBEDU", "कोयम्बेडु"),
    ("GUINDY", "गिंडी"),
    ("TAMBARAM", "ताम्बरम"),
    ("ALANDUR", "आलंदूर"),
    ("CHENNAI_BEACH", "चेन्नई बीच"),
    ("VELACHERY", "वेलाचेरी")
]

STATIONS_HINGLISH = [
    ("CHENNAI_CENTRAL", "chennai central"),
    ("CHENNAI_CENTRAL", "central"),
    ("CHENNAI_EGMORE", "chennai egmore"),
    ("CHENNAI_EGMORE", "egmore"),
    ("CHENNAI_AIRPORT", "chennai airport"),
    ("CHENNAI_AIRPORT", "airport"),
    ("KOYAMBEDU", "koyambedu"),
    ("GUINDY", "guindy"),
    ("TAMBARAM", "tambaram"),
    ("ALANDUR", "alandur")
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


def load_templates() -> Dict[str, Any]:
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["intents"]


def generate_dataset(samples_per_intent: int = 150) -> pd.DataFrame:
    """Generates synthetic dataset from templates with slot replacements."""
    random.seed(42)
    templates = load_templates()
    rows: List[Dict[str, Any]] = []

    for intent, config in templates.items():
        hi_templates = config.get("templates_hi", [])
        hinglish_templates = config.get("templates_hinglish", [])

        intent_samples = 0
        while intent_samples < samples_per_intent:
            # 70% Hindi, 30% Hinglish
            is_hinglish = (random.random() < 0.3) and len(hinglish_templates) > 0
            template_list = hinglish_templates if is_hinglish else hi_templates
            tpl = random.choice(template_list)

            origin_id = None
            dest_id = None
            mode_id = None
            info_type = None

            filled = tpl

            # Handle Station Slots
            if "{origin}" in tpl and "{destination}" in tpl:
                station_pool = STATIONS_HINGLISH if is_hinglish else STATIONS_HI
                s1, s2 = random.sample(station_pool, 2)
                origin_id, origin_name = s1
                dest_id, dest_name = s2
                filled = filled.replace("{origin}", origin_name).replace("{destination}", dest_name)
            elif "{station}" in tpl:
                station_pool = STATIONS_HINGLISH if is_hinglish else STATIONS_HI
                s = random.choice(station_pool)
                origin_id, station_name = s
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

            # Check Information / Facility Type
            if intent == "accessibility":
                info_type = "wheelchair"
            elif intent == "service_timing":
                info_type = "timing"
            elif intent == "ticketing":
                info_type = "fare"

            rows.append({
                "query": filled.strip(),
                "intent": intent,
                "origin": origin_id,
                "destination": dest_id,
                "transport_mode": mode_id,
                "information_type": info_type,
                "language": "hinglish" if is_hinglish else "hi"
            })
            intent_samples += 1

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["query"]).reset_index(drop=True)

    # Stratified Train (70%), Val (15%), Test (15%)
    df["split"] = "train"
    for intent in df["intent"].unique():
        idx = df[df["intent"] == intent].index.tolist()
        random.shuffle(idx)
        n = len(idx)
        val_end = int(0.15 * n)
        test_end = int(0.30 * n)

        val_idx = idx[:val_end]
        test_idx = idx[val_end:test_end]

        df.loc[val_idx, "split"] = "val"
        df.loc[test_idx, "split"] = "test"

    return df


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    df = generate_dataset(samples_per_intent=200)
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8")
    print(f"✅ Generated dataset with {len(df)} samples at: {OUTPUT_CSV_PATH}")
    print("\nClass distribution by split:")
    print(pd.crosstab(df["intent"], df["split"]))
