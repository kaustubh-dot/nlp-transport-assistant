"""Operation names and result type for read-only canonical lookups."""
from dataclasses import dataclass, field
from typing import Any

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
