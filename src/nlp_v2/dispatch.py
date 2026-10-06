"""Direct T3 intent dispatch with explicit clarification and answerability states."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from src.nlp_v2.contracts import IntentPrediction, missing_slots, validate_intent_slots, validate_prediction, validate_slots


OPERATIONS = {
    "point_to_point_route": "PLAN_ROUTE",
    "multimodal_route": "PLAN_MULTIMODAL_ROUTE",
    "route_stop_sequence": "LIST_ROUTE_STOPS",
    "route_stop_membership": "CHECK_STOP_ON_ROUTE",
    "first_and_last_service": "GET_FIRST_LAST_SERVICE",
    "service_frequency": "GET_SERVICE_FREQUENCY",
    "scheduled_departure": "GET_SCHEDULED_DEPARTURES",
    "mode_availability": "CHECK_SERVICE_AVAILABILITY",
    "fare_calculation": "CALCULATE_FARE",
    "ticketing_and_passes": "GET_TICKETING_POLICY",
    "station_facilities": "GET_STATION_FACILITY",
    "station_accessibility": "GET_ACCESSIBILITY_INFO",
    "interchange_transfer": "GET_INTERCHANGE_DETAILS",
    "nearest_transport": "FIND_NEAREST_STATION",
    "realtime_status_query": "REJECT_UNSUPPORTED_REALTIME",
    "out_of_scope": "REJECT_OUT_OF_SCOPE",
}


@dataclass(frozen=True)
class ServiceResult:
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""


class DomainService(Protocol):
    def execute(self, operation: str, slots: Mapping[str, Any]) -> ServiceResult: ...


class UnavailableService:
    def execute(self, operation: str, slots: Mapping[str, Any]) -> ServiceResult:
        return ServiceResult("unavailable", {}, "Verified transport data is unavailable for this operation.")


@dataclass(frozen=True)
class DispatchResult:
    intent: str | None
    operation: str | None
    status: str
    slots: dict[str, Any]
    acceptable_labels: tuple[str, ...]
    confidence: float
    missing_slots: tuple[str, ...] = ()
    reason: str | None = None
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def dispatch(prediction: IntentPrediction, slots: Mapping[str, Any], service: DomainService | None = None) -> DispatchResult:
    """Validate, clarify, and invoke exactly one T3 operation when executable."""
    validate_prediction(prediction)
    validate_slots(slots)
    intent = prediction.primary_label
    operation = OPERATIONS[intent] if intent else None
    base = {
        "intent": intent,
        "operation": operation,
        "slots": dict(slots),
        "acceptable_labels": prediction.acceptable_labels,
        "confidence": prediction.confidence,
    }

    if intent is None or prediction.clarification_reason:
        reason = prediction.clarification_reason or "intent_ambiguity"
        return DispatchResult(status="clarification", reason=reason, message="Please clarify which transport question you mean.", **base)

    validate_intent_slots(intent, slots)

    if intent == "out_of_scope":
        return DispatchResult(status="out_of_scope", message="I can help with Chennai public transport questions.", **base)
    if intent == "realtime_status_query":
        return DispatchResult(status="unavailable", message="Live transport status is unavailable; please verify with the operator.", **base)

    time_value = slots.get("time")
    if (isinstance(time_value, (list, tuple)) and len(time_value) != 1) or (slots.get("temporal_relative") in {"kal", "कल"} and not slots.get("date")):
        return DispatchResult(status="clarification", reason="temporal_ambiguity", message="Please clarify the intended time or day.", **base)

    missing = missing_slots(intent, slots)
    if missing:
        return DispatchResult(status="clarification", reason="missing_slot", missing_slots=missing,
                              message="Please provide the missing journey information.", **base)

    try:
        result = (service or UnavailableService()).execute(operation, dict(slots))
    except Exception:
        return DispatchResult(status="error", message="The transport service could not complete this request.", **base)
    if not isinstance(result, ServiceResult) or result.status not in {"ok", "unavailable", "error"} or not isinstance(result.data, dict):
        return DispatchResult(status="error", message="The transport service returned an invalid state.", **base)
    return DispatchResult(status=result.status, message=result.message, data=result.data, **base)
