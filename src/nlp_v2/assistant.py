"""Single production T3 utterance-to-response path."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.normalization import normalize_text

from .contracts import IntentPrediction, validate_prediction
from .dispatch import DispatchResult, dispatch
from .domain import CanonicalTransitService
from .entities import CanonicalResolver
from .model import T3IntentClassifier
from .slots import T3SlotExtractor


@dataclass(frozen=True)
class AssistantReply:
    status: str
    response_text: str
    raw_query: str
    normalized_query: str
    intent: str | None
    operation: str | None
    confidence: float | None
    slots: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    missing_slots: tuple[str, ...] = ()
    clarification_reason: str | None = None
    candidate_entities: tuple[str, ...] = ()
    candidate_intents: tuple[str, ...] = ()


def _answer(result: DispatchResult) -> str:
    """Render only facts supplied by the canonical service."""
    if result.status == "clarification":
        if result.reason == "missing_slot":
            names = ", ".join(result.missing_slots).replace("_", " ")
            return f"Please provide {names} so I can check the transport information."
        return {
            "entity_ambiguity": "Please clarify which stop or location you mean.",
            "temporal_ambiguity": "Please clarify the time or day you mean.",
            "multiple_goals": "Please choose which transport question to answer first.",
            "intent_ambiguity": "Please clarify which transport question you mean.",
        }.get(result.reason, result.message)
    if result.status != "ok":
        return result.message or "The transport information is unavailable."

    data = result.data
    operation = result.operation
    detail = ""
    if operation == "PLAN_ROUTE" and data.get("routes"):
        route = data["routes"][0]
        detail = f"Published route candidate: {route['route_name']} ({route['mode']}). "
    elif operation == "LIST_ROUTE_STOPS" and data.get("sequences"):
        sequence = data["sequences"][0]
        names = ", ".join(stop["name"] for stop in sequence["stops"][:8])
        suffix = ", …" if len(sequence["stops"]) > 8 else ""
        detail = f"{sequence['route_name']} stops: {names}{suffix}. "
    elif operation == "CHECK_STOP_ON_ROUTE" and "on_route" in data:
        detail = "The stop appears on the published route sequence. " if data["on_route"] else "The stop does not appear on the published route sequence. "
    elif operation == "GET_FIRST_LAST_SERVICE":
        detail = f"Published first departure: {data['first_departure']}; last: {data['last_departure']} (service-day time). "
    elif operation == "GET_SERVICE_FREQUENCY":
        detail = f"Published median interval: {data['median_headway_minutes']:g} minutes. "
    elif operation == "GET_SCHEDULED_DEPARTURES":
        departures = ", ".join(
            f"{row['route_name']} at {row['time']}" for row in data.get("departures", [])
        )
        detail = f"Published departures: {departures} (service-day time). "
    elif operation == "CALCULATE_FARE":
        detail = f"Published fare: {data['currency']} {data['amount']:g} (record effective {data['effective_date']}). "
    elif operation == "GET_ACCESSIBILITY_INFO":
        value = "recorded as available" if data.get("available") else "recorded as unavailable"
        detail = f"{data.get('feature', 'Feature')} is {value}. "
    elif operation == "FIND_NEAREST_STATION" and data.get("stops"):
        stop = data["stops"][0]
        detail = f"Nearest by straight line: {stop['name']} ({stop['distance_m']} m). "
    return detail + result.message


class T3Assistant:
    """Run frozen T3 inference, extraction, clarification, dispatch, and rendering."""

    def __init__(self, *, classifier=None, resolver=None, extractor=None, service=None):
        self.classifier = classifier if classifier is not None else T3IntentClassifier()
        self.resolver = resolver if resolver is not None else CanonicalResolver()
        self.extractor = extractor if extractor is not None else T3SlotExtractor(self.resolver)
        self.service = service if service is not None else CanonicalTransitService()

    def process_query(self, query: str) -> AssistantReply:
        if not isinstance(query, str) or not query.strip():
            return AssistantReply("error", "Please enter a transport question.", query if isinstance(query, str) else "", "", None, None, None)
        normalized = normalize_text(query)
        try:
            prediction: IntentPrediction = self.classifier.predict(query)
            validate_prediction(prediction)
            if prediction.clarification_reason or prediction.primary_label is None:
                return self._reply(query, normalized, dispatch(prediction, {}, self.service))
            intent = prediction.primary_label
            if intent in {"out_of_scope", "realtime_status_query"}:
                result = dispatch(prediction, {}, self.service)
                return self._reply(query, normalized, result)

            extraction = self.extractor.extract(query, intent)
            if extraction.clarification_reason:
                candidates = tuple(sorted({candidate.entity_id for unresolved in extraction.unresolved
                                           for candidate in unresolved.candidates}))
                reason = extraction.clarification_reason
                text = "Please clarify which stop or location you mean." if reason == "entity_ambiguity" else "Please clarify the time or day you mean."
                return AssistantReply(
                    "clarification", text, query, extraction.normalized_query, intent,
                    None, prediction.confidence, dict(extraction.slots),
                    clarification_reason=reason, candidate_entities=candidates,
                    candidate_intents=prediction.acceptable_labels,
                )
            result = dispatch(prediction, extraction.slots, self.service)
            return self._reply(query, extraction.normalized_query, result)
        except Exception:
            return AssistantReply(
                "error", "The assistant could not process this question. Please try again.",
                query, normalized, None, None, None,
            )

    @staticmethod
    def _reply(query: str, normalized: str, result: DispatchResult) -> AssistantReply:
        return AssistantReply(
            result.status, _answer(result), query, normalized, result.intent,
            result.operation, result.confidence, result.slots, result.data,
            result.missing_slots, result.reason, candidate_intents=result.acceptable_labels,
        )
