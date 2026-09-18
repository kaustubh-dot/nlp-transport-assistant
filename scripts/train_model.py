#!/usr/bin/env python3
"""Convenience alias for train_and_compare_models.py."""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.train_and_compare_models import main

if __name__ == "__main__":
    main()
