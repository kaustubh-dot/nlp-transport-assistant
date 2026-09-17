#!/usr/bin/env python3
"""Generates the domain-adapted NLU dataset for Hindi Transport Assistant.

Uses templates from data/templates/hindi_templates.json, canonical stations,
and transport modes to produce an intent development dataset. Entire authored
template families are assigned to train/validation/test; counts are approximate
and may be imbalanced after deduplication. No external seed corpus is loaded.
Slot columns are unreviewed hints, not evaluation gold.

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

            # Check Information / Facility Type
            if intent == "accessibility":
                info_type = "wheelchair"
            elif intent == "service_timing":
                info_type = "timing"
            elif intent == "ticketing":
                info_type = "fare"

            rows.append({
                "query": filled.strip(),
                "template_family": intent + ":" + config["families_hinglish" if is_hinglish else "families_hi"][template_list.index(tpl)],
                "station": station_id or origin_id or dest_id,
                "intent": intent,
                "origin": origin_id,
                "destination": dest_id,
                "transport_mode": mode_id,
                "information_type": info_type,
                "slots_reviewed": False,
                "language": "hinglish" if is_hinglish else "hi"
            })
            intent_samples += 1

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["query"]).reset_index(drop=True)

    # Split entire authored template families; substitutions never cross splits.
    # With small template inventories, proportions are approximate, not 70/15/15.
    df["split"] = "train"
    for intent in df["intent"].unique():
        families = sorted(df.loc[df.intent == intent, "template_family"].unique())
        if len(families) < 3:
            raise ValueError(f"{intent} needs at least three template families")
        random.shuffle(families)
        n_holdout = max(1, int(len(families) * 0.15))
        df.loc[df.template_family.isin(families[:n_holdout]), "split"] = "val"
        df.loc[df.template_family.isin(families[n_holdout:2*n_holdout]), "split"] = "test"

    return df


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    df = generate_dataset(samples_per_intent=200)
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8")
    print(f"✅ Generated dataset with {len(df)} samples at: {OUTPUT_CSV_PATH}")
    print("\nClass distribution by split:")
    print(pd.crosstab(df["intent"], df["split"]))
