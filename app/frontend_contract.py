"""Pure frontend contract helpers for the local T3 API."""

from __future__ import annotations

import os

import requests


DEFAULT_API_URL = "http://127.0.0.1:8765"


def ask_api(query: str, *, base_url: str | None = None, session=None) -> dict:
    """Submit one complete question; return a safe error object on API failure."""
    client = session or requests
    base = (base_url or os.environ.get("NLP_V2_API_URL") or DEFAULT_API_URL).rstrip("/")
    try:
        response = client.post(base + "/api/v2/query", json={"query": query}, timeout=20)
        result = response.json()
    except (requests.RequestException, ValueError, TypeError):
        return {"status": "error", "response_text": "The local T3 API is unavailable. Start the API and try again."}
    if not isinstance(result, dict) or not isinstance(result.get("status"), str) or not isinstance(result.get("response_text"), str):
        return {"status": "error", "response_text": "The T3 API returned an invalid response."}
    if response.status_code >= 400 and result["status"] != "error":
        return {"status": "error", "response_text": "The T3 API could not complete this request."}
    return result


PANEL_KINDS = {
    "PLAN_ROUTE": ("routes", "routes"),
    "PLAN_MULTIMODAL_ROUTE": ("routes", "routes"),
    "LIST_ROUTE_STOPS": ("sequences", "stops"),
    "CHECK_STOP_ON_ROUTE": ("on_route", "membership"),
    "GET_FIRST_LAST_SERVICE": ("first_departure", "service_bounds"),
    "GET_SERVICE_FREQUENCY": ("median_headway_minutes", "frequency"),
    "GET_SCHEDULED_DEPARTURES": ("departures", "departures"),
    "CALCULATE_FARE": ("amount", "fare"),
    "GET_TICKETING_POLICY": ("policy", "ticketing"),
    "GET_STATION_FACILITY": ("facility", "facility"),
    "GET_ACCESSIBILITY_INFO": ("feature", "accessibility"),
    "GET_INTERCHANGE_DETAILS": ("transfers", "interchange"),
    "FIND_NEAREST_STATION": ("stops", "nearest"),
}


def result_panel(reply: dict) -> dict | None:
    """Select a display panel only when verified structured data is present."""
    if reply.get("status") != "ok" or not isinstance(reply.get("data"), dict):
        return None
    operation = reply.get("operation")
    spec = PANEL_KINDS.get(operation)
    if not spec:
        return None
    key, kind = spec
    data = reply["data"]
    if key not in data:
        return None
    return {"kind": kind, "data": data, "operation": operation}
