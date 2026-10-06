"""Synthetic aggregate scoring and freeze guards; no held-out examples."""

import pytest


def test_assistant_scoring_distinguishes_selected_operation_and_dispatch():
    from scripts.nlp_v2.evaluate_assistant import score_replies

    rows = [
        {"gold": "point_to_point_route", "intent": "point_to_point_route", "operation": "PLAN_ROUTE", "status": "clarification", "gold_clarification": True, "language_class": "English"},
        {"gold": "nearest_transport", "intent": "nearest_transport", "operation": "FIND_NEAREST_STATION", "status": "ok", "gold_clarification": False, "language_class": "English"},
        {"gold": "realtime_status_query", "intent": "realtime_status_query", "operation": "REJECT_UNSUPPORTED_REALTIME", "status": "unavailable", "gold_clarification": False, "language_class": "Hindi"},
        {"gold": "fare_calculation", "intent": None, "operation": None, "status": "error", "gold_clarification": True, "language_class": "Hindi"},
    ]
    result = score_replies(rows)
    assert result["count"] == 4
    assert result["strict_intent_accuracy"] == 0.75
    assert result["selected_operation_accuracy"] == 0.75
    assert result["terminal_dispatch_accuracy"] == 0.5
    assert result["status_counts"] == {"clarification": 1, "error": 1, "ok": 1, "unavailable": 1}
    assert result["clarification"]["true_positive"] == 1
    assert result["clarification"]["false_negative"] == 1
    assert result["clarification"]["recall"] == 0.5
    assert result["strata"]["language_class"]["English"]["count"] == 2


def test_assistant_scoring_rejects_empty_or_invalid_records():
    from scripts.nlp_v2.evaluate_assistant import score_replies

    with pytest.raises(ValueError, match="empty"):
        score_replies([])
    with pytest.raises(ValueError, match="status"):
        score_replies([{"gold": "nearest_transport", "intent": None, "operation": None, "status": "unexpected", "gold_clarification": False}])


def test_freeze_guard_rejects_source_drift(monkeypatch):
    from scripts.nlp_v2 import evaluate_assistant as evaluator

    calls = []
    def git(*args):
        calls.append(args)
        if args[0] == "rev-parse":
            return "a" * 40
        if args[0] == "status":
            return ""
        return "src/nlp_v2/assistant.py"
    monkeypatch.setattr(evaluator, "git_output", git)
    with pytest.raises(ValueError, match="freeze"):
        evaluator.verify_freeze("a" * 40)
    assert any(call[0] == "diff" for call in calls)


def test_evaluation_refuses_existing_output_before_loading_model(tmp_path):
    from scripts.nlp_v2.evaluate_assistant import evaluate

    (tmp_path / "existing.json").write_text("{}")
    with pytest.raises(ValueError, match="exists"):
        evaluate(tmp_path, freeze_commit="a" * 40)
