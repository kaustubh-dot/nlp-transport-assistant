# tests/test_benchmark_runner.py
"""Tests for benchmark runner and comparison report generator."""

import os
import json
import pytest

ACCEPTANCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "eval", "acceptance_test_suite.json")
BENCHMARK_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "benchmark_all_models.py")


def test_acceptance_suite_exists_and_valid():
    assert os.path.exists(ACCEPTANCE_PATH), f"Acceptance test suite missing at {ACCEPTANCE_PATH}"
    with open(ACCEPTANCE_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    assert len(items) == 149, f"Expected 149 gold items, got {len(items)}"
    for item in items:
        assert "query" in item
        assert "gold_intent" in item
        assert "expected_substrings" in item


def test_benchmark_runner_script_exists():
    assert os.path.exists(BENCHMARK_SCRIPT), f"Benchmark runner missing at {BENCHMARK_SCRIPT}"
