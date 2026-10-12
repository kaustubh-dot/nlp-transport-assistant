"""Canonical query scopes and slot validation for the shared lookup layer."""
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
