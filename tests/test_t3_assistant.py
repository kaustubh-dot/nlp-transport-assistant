"""T3 assistant contract tests using synthetic commuter questions."""

import pytest

from src.nlp_v2.contracts import IntentPrediction


class FixedClassifier:
    def __init__(self, intent):
        self.intent = intent
        self.queries = []

    def predict(self, query):
        self.queries.append(query)
        return IntentPrediction(self.intent, (self.intent,), 0.9)


@pytest.fixture(scope="module")
def resolver():
    from src.nlp_v2.entities import CanonicalResolver

    return CanonicalResolver()


@pytest.mark.parametrize("query", [
    "Which bus route 102 stops at Guindy?",
    "बस 102 गिंडी पर रुकती है क्या?",
    "102 bus gindi pe rukti hai kya?",
    "बस 102 Guindy पर रुकती है?",
    "bus 102 gindi stop pls",
])
def test_multilingual_queries_follow_one_t3_path(resolver, query):
    from src.nlp_v2.assistant import T3Assistant

    classifier = FixedClassifier("route_stop_membership")
    assistant = T3Assistant(classifier=classifier, resolver=resolver)
    reply = assistant.process_query(query)
    assert classifier.queries == [query]
    assert reply.intent == "route_stop_membership"
    assert reply.operation == "CHECK_STOP_ON_ROUTE"
    assert reply.status in {"ok", "clarification", "unavailable"}
    assert reply.response_text


def test_missing_origin_prompts_for_exact_slot(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("point_to_point_route"), resolver=resolver).process_query(
        "How do I travel to Guindy?"
    )
    assert reply.status == "clarification"
    assert "origin" in reply.missing_slots


def test_entity_ambiguity_precedes_missing_slot(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("point_to_point_route"), resolver=resolver).process_query(
        "How to go from Guindy to Central?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "entity_ambiguity"
    assert reply.candidate_entities


def test_out_of_scope_and_realtime_are_terminal(resolver):
    from src.nlp_v2.assistant import T3Assistant

    oos = T3Assistant(classifier=FixedClassifier("out_of_scope"), resolver=resolver).process_query("Tell me a joke")
    live = T3Assistant(classifier=FixedClassifier("realtime_status_query"), resolver=resolver).process_query("Live bus status?")
    assert oos.status == "out_of_scope"
    assert live.status == "unavailable"
    assert "live" in live.response_text.lower()


def test_empty_query_is_structured_error(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("out_of_scope"), resolver=resolver).process_query("  ")
    assert reply.status == "error"
    assert reply.intent is None


def test_relative_day_ambiguity_is_kept_separate_from_missing_slots(resolver):
    from src.nlp_v2.assistant import T3Assistant

    reply = T3Assistant(classifier=FixedClassifier("first_and_last_service"), resolver=resolver).process_query(
        "Last bus kal?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "temporal_ambiguity"


def test_classifier_multi_goal_clarification_is_preserved(resolver):
    from src.nlp_v2.assistant import T3Assistant

    class MultipleGoals:
        def predict(self, query):
            return IntentPrediction(None, ("fare_calculation", "scheduled_departure"), 0.5, "multiple_goals")

    reply = T3Assistant(classifier=MultipleGoals(), resolver=resolver).process_query(
        "What is the fare and when does the bus leave?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "multiple_goals"
    assert reply.candidate_intents == ("fare_calculation", "scheduled_departure")


def test_primary_label_with_multiple_goals_precedes_entity_extraction(resolver):
    from src.nlp_v2.assistant import T3Assistant

    class PrimaryWithMultipleGoals:
        def predict(self, query):
            return IntentPrediction(
                "point_to_point_route", ("point_to_point_route", "fare_calculation"),
                0.72, "multiple_goals",
            )

    reply = T3Assistant(classifier=PrimaryWithMultipleGoals(), resolver=resolver).process_query(
        "How to go from Guindy to Central and what is the fare?"
    )
    assert reply.status == "clarification"
    assert reply.clarification_reason == "multiple_goals"


def test_service_failure_becomes_safe_error(resolver):
    from src.nlp_v2.assistant import T3Assistant

    class BrokenService:
        def execute(self, operation, slots):
            raise OSError("internal secret path")

    reply = T3Assistant(
        classifier=FixedClassifier("nearest_transport"), resolver=resolver, service=BrokenService(),
    ).process_query("Where is the nearest metro station to Marina Beach?")
    assert reply.status == "error"
    assert "secret" not in reply.response_text


def test_departure_text_preserves_route_time_associations():
    from src.nlp_v2.assistant import _answer
    from src.nlp_v2.dispatch import DispatchResult

    result = DispatchResult(
        intent="scheduled_departure", operation="GET_SCHEDULED_DEPARTURES", status="ok",
        slots={}, acceptable_labels=("scheduled_departure",), confidence=0.9,
        message="Published only; verify with operator.",
        data={"departures": [
            {"route_name": "70G", "time": "02:47:00"},
            {"route_name": "11G R", "time": "04:35:00"},
        ]},
    )
    text = _answer(result)
    assert "70G at 02:47:00" in text
    assert "11G R at 04:35:00" in text
    assert "verify with operator" in text
