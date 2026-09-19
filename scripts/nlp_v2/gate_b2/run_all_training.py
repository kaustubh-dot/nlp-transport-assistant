#!/usr/bin/env python3
"""Sequentially trains all remaining Gate B.2 confirmation runs.

Runs:
- T2-H Seed 101
- T2-H Seed 777
- T3 Seed 42
- T3 Seed 101
- T3 Seed 777
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_t2h_muril import train_t2h
from train_t3_muril import train_t3

def main():
    print("=" * 70)
    print("STARTING BATCH TRAINING FOR GATE B.2 CONFIRMATION")
    print("=" * 70)

    # Remaining T2-H seeds
    for seed in [101, 777]:
        print(f"\n>>> Running T2-H Seed {seed}...")
        train_t2h(seed=seed, max_epochs=30, patience=3)

    # All T3 seeds
    for seed in [42, 101, 777]:
        print(f"\n>>> Running T3 Seed {seed}...")
        train_t3(seed=seed, max_epochs=30, patience=3)

    print("\n" + "=" * 70)
    print("ALL 6 GATE B.2 TRANSFORMER RUNS SUCCESSFULLY COMPLETED!")
    print("=" * 70)

if __name__ == "__main__":
    main()
