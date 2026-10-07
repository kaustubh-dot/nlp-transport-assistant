"""Frozen T3 prediction and canonical slot contracts."""

from dataclasses import dataclass
from datetime import date as calendar_date
import re
from typing import Mapping, Any


T3_INTENTS = frozenset({
    "point_to_point_route", "multimodal_route", "route_stop_sequence",
    "route_stop_membership", "first_and_last_service", "service_frequency",
    "scheduled_departure", "mode_availability", "fare_calculation",
    "ticketing_and_passes", "station_facilities", "station_accessibility",
    "interchange_transfer", "nearest_transport", "realtime_status_query",
    "out_of_scope",
})

CANONICAL_SLOTS = frozenset({
    "origin", "destination", "via", "station", "stop", "landmark", "locality",
    "route_number", "line_name", "transport_mode", "mode_from", "mode_to",
    "preference", "timing_type", "time", "temporal_relative", "date",
    "ticket_type", "fare_type", "stage_number", "service_type", "facility_type",
    "accessibility_feature",
})

TRANSPORT_MODES = frozenset({"metro", "bus", "suburban_rail", "mrts", "any"})
CLARIFICATION_REASONS = frozenset({"intent_ambiguity", "entity_ambiguity", "temporal_ambiguity", "multiple_goals"})
OUTCOME_REASONS = frozenset({
    'intent_ambiguity', 'entity_ambiguity', 'temporal_ambiguity', 'multiple_goals',
    'missing_execution_slot', 'unsupported_source', 'external_source_required',
    'malformed_request', 'temporary_service_unavailability', 'answered', 'out_of_scope',
})
ENUM_SLOTS = {
    "transport_mode": TRANSPORT_MODES,
    "mode_from": TRANSPORT_MODES,
    "mode_to": TRANSPORT_MODES,
    "preference": frozenset({"fastest", "cheapest", "least_transfers", "direct_only"}),
    "timing_type": frozenset({"first", "last", "frequency", "departure", "operating_hours"}),
    "ticket_type": frozenset({"token", "smart_card", "ncmc_card", "qr_ticket", "monthly_pass", "tourist_pass", "season_pass"}),
    "fare_type": frozenset({"stage_fare", "distance_fare", "concession", "pass_fare"}),
    "service_type": frozenset({"Ordinary Services", "Express Services", "Deluxe Services", "Night Services", "Air Conditioned Services"}),
    "facility_type": frozenset({"parking", "interchange", "restroom", "waiting_room", "cloak_room", "atm", "wifi", "drinking_water"}),
    "accessibility_feature": frozenset({"wheelchair", "lift", "escalator", "ramp", "accessible_toilet", "tactile_paths", "any"}),
    "line_name": frozenset({"Blue Line", "Green Line", "Corridor 1", "Corridor 2", "MRTS", "North Line", "South Line", "West Line"}),
}
ENTITY_SLOTS = frozenset({"origin", "destination", "via", "station", "stop", "landmark", "locality"})
TEXT_SLOTS = frozenset({"temporal_relative"})
ALLOWED_SLOTS = {
    "point_to_point_route": {"origin", "destination", "via", "landmark", "locality", "route_number", "line_name", "transport_mode", "preference", "timing_type", "time", "temporal_relative", "date"},
    "multimodal_route": {"origin", "destination", "via", "landmark", "locality", "route_number", "line_name", "transport_mode", "preference", "timing_type", "time", "temporal_relative", "date"},
    "route_stop_sequence": {"route_number", "line_name", "transport_mode"},
    "route_stop_membership": {"route_number", "line_name", "stop", "transport_mode"},
    "first_and_last_service": {"origin", "destination", "station", "route_number", "line_name", "transport_mode", "timing_type", "time", "temporal_relative", "date"},
    "service_frequency": {"origin", "destination", "station", "route_number", "line_name", "transport_mode", "timing_type", "time", "temporal_relative", "date"},
    "scheduled_departure": {"origin", "destination", "station", "stop", "route_number", "line_name", "transport_mode", "timing_type", "time", "temporal_relative", "date"},
    "mode_availability": {"origin", "destination", "via", "route_number", "line_name", "transport_mode", "time", "temporal_relative", "date"},
    "fare_calculation": {"origin", "destination", "route_number", "transport_mode", "ticket_type", "fare_type", "stage_number", "service_type"},
    "ticketing_and_passes": {"station", "transport_mode", "ticket_type"},
    "station_facilities": {"station", "transport_mode", "facility_type"},
    "station_accessibility": {"station", "transport_mode", "accessibility_feature"},
    "interchange_transfer": {"origin", "destination", "station", "route_number", "line_name", "transport_mode", "mode_from", "mode_to"},
    "nearest_transport": {"landmark", "locality", "transport_mode"},
    "realtime_status_query": {"origin", "destination", "station", "landmark", "locality", "route_number", "line_name", "transport_mode", "temporal_relative", "date"},
    "out_of_scope": CANONICAL_SLOTS,
}


class ContractError(ValueError):
    """Raised when a caller violates the production T3 input contract."""


@dataclass(frozen=True)
class IntentPrediction:
    primary_label: str | None
    acceptable_labels: tuple[str, ...]
    confidence: float
    clarification_reason: str | None = None


def validate_prediction(prediction: IntentPrediction) -> None:
    """Reject malformed or non-T3 classifier output."""
    if prediction.primary_label is not None and prediction.primary_label not in T3_INTENTS:
        raise ContractError(f"Unknown T3 intent: {prediction.primary_label}")
    if not prediction.acceptable_labels or any(label not in T3_INTENTS for label in prediction.acceptable_labels):
        raise ContractError("Acceptable labels must contain T3 intents")
    if len(set(prediction.acceptable_labels)) != len(prediction.acceptable_labels):
        raise ContractError("Acceptable labels must be unique")
    if prediction.primary_label is not None and prediction.primary_label not in prediction.acceptable_labels:
        raise ContractError("Primary intent must be in acceptable labels")
    if not isinstance(prediction.confidence, (int, float)) or not 0 <= prediction.confidence <= 1:
        raise ContractError("Confidence must be between 0 and 1")
    if prediction.primary_label is None and len(prediction.acceptable_labels) < 2:
        raise ContractError("Ambiguous prediction requires at least two candidate intents")
    if prediction.clarification_reason == "multiple_goals" and len(prediction.acceptable_labels) < 2:
        raise ContractError("Multiple goals require at least two intents")
    if prediction.clarification_reason is not None and prediction.clarification_reason not in CLARIFICATION_REASONS:
        raise ContractError("Unknown clarification reason")


def validate_slots(slots: Mapping[str, Any]) -> None:
    """Validate caller-supplied canonical slot names and bounded enums."""
    unknown = set(slots) - CANONICAL_SLOTS
    if unknown:
        raise ContractError(f"Unknown canonical slot(s): {', '.join(sorted(unknown))}")
    for name, value in slots.items():
        if value is None:
            continue
        if name in ENUM_SLOTS and (not isinstance(value, str) or value not in ENUM_SLOTS[name]):
            raise ContractError(f"Invalid {name}: {value}")
        if name in ENTITY_SLOTS and (not isinstance(value, str) or not re.fullmatch(r"[A-Z0-9_]+", value)):
            raise ContractError(f"{name} must be a canonical entity ID")
        if name in TEXT_SLOTS and (not isinstance(value, str) or not value.strip()):
            raise ContractError(f"{name} must be nonempty text")
        if name == "route_number" and (not isinstance(value, str) or not re.fullmatch(r"[A-Z0-9][A-Z0-9#-]*", value)):
            raise ContractError("route_number must be a canonical route code")
        if name == "time":
            candidates = value if isinstance(value, (list, tuple)) else [value]
            if not candidates or any(not isinstance(t, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d", t) for t in candidates):
                raise ContractError("time must be ISO HH:MM:SS or a candidate set")
        if name == "date":
            try:
                if not isinstance(value, str) or calendar_date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except ValueError as exc:
                raise ContractError("date must be ISO YYYY-MM-DD") from exc
    stage = slots.get("stage_number")
    if stage is not None and (type(stage) is not int or not 1 <= stage <= 30):
        raise ContractError("stage_number must be an integer from 1 to 30")


def validate_intent_slots(intent: str, slots: Mapping[str, Any]) -> None:
    """Prevent forbidden slots from crossing into an operation service."""
    forbidden = {name for name, value in slots.items() if value is not None and name not in ALLOWED_SLOTS[intent]}
    if forbidden:
        raise ContractError(f"Forbidden slot(s) for {intent}: {', '.join(sorted(forbidden))}")


def missing_slots(intent: str, slots: Mapping[str, Any]) -> tuple[str, ...]:
    """Return execution requirements missing for a T3 operation."""
    required = {
        "point_to_point_route": ("origin", "destination"),
        "multimodal_route": ("origin", "destination"),
        "route_stop_membership": ("stop",),
        "mode_availability": ("origin", "destination"),
        "station_facilities": ("station",),
        "station_accessibility": ("station",),
    }.get(intent, ())
    missing = [name for name in required if not slots.get(name)]
    if intent in {"route_stop_sequence", "route_stop_membership"} and not (slots.get("route_number") or slots.get("line_name")):
        missing.append("route_number_or_line_name")
    if intent in {"scheduled_departure", "first_and_last_service", "service_frequency"} and not (slots.get("station") or slots.get("stop") or slots.get("origin")):
        missing.append("station_or_stop")
    if intent == "service_frequency" and not (slots.get("route_number") or slots.get("line_name")):
        missing.append("route_number_or_line_name")
    if intent == "fare_calculation" and not slots.get("stage_number"):
        if not slots.get("origin"):
            missing.append("origin_or_stage_number")
        if not slots.get("destination"):
            missing.append("destination_or_stage_number")
    if intent == "interchange_transfer" and not (slots.get("station") or (slots.get("mode_from") and slots.get("mode_to"))):
        missing.append("station_or_mode_pair")
    if intent == "nearest_transport" and not (slots.get("landmark") or slots.get("locality")):
        missing.append("landmark_or_locality")
    return tuple(missing)
