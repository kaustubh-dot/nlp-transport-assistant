#!/usr/bin/env python3
"""Harvests external conversational & transit NLP datasets from Hugging Face.

Harvests:
  - WillHeld/hinglish_top: Navigation queries for routing/availability/timing,
    and out-of-domain domains (weather, reminder, messaging, music, alarm) for out_of_scope.
  - Generates balanced real-world conversational data for train/val splits.

Outputs:
  - data/curated/external_harvested_queries.json
"""

import os
import json
from typing import List, Dict, Any
from datasets import load_dataset

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "curated", "external_harvested_queries.json")


def harvest_hinglish_top() -> List[Dict[str, Any]]:
    print("Loading WillHeld/hinglish_top from Hugging Face...")
    harvested = []
    
    # Load splits
    for split_name in ["train", "validation", "test"]:
        try:
            ds = load_dataset("WillHeld/hinglish_top", split=split_name)
        except Exception as e:
            print(f"Warning: Could not load split {split_name}: {e}")
            continue

        for item in ds:
            domain = item.get("domain", "")
            cs_query = item.get("cs_query", "").strip()
            if not cs_query or len(cs_query) < 5:
                continue

            # Map navigation queries
            if domain == "navigation":
                q_lower = cs_query.lower()
                if any(w in q_lower for w in ["kitna samay", "kitne baje", "time", "samay", "der"]):
                    intent = "service_timing"
                elif any(w in q_lower for w in ["traffic", "bheed", "chal sakti", "available", "milegi"]):
                    intent = "service_availability"
                else:
                    intent = "route_query"

                harvested.append({
                    "query": cs_query,
                    "intent": intent,
                    "script": "latin_hinglish",
                    "source": f"hinglish_top_{split_name}",
                    "template_family": f"external_nav_{domain}"
                })

            # Map non-transit domains to out_of_scope
            elif domain in ["weather", "alarm", "music", "reminder", "messaging"]:
                harvested.append({
                    "query": cs_query,
                    "intent": "out_of_scope",
                    "script": "latin_hinglish",
                    "source": f"hinglish_top_{split_name}",
                    "template_family": f"external_oos_{domain}"
                })

    print(f"Harvested {len(harvested)} items from WillHeld/hinglish_top.")
    return harvested


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    items = harvest_hinglish_top()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"total": len(items), "samples": items}, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(items)} external harvested queries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
