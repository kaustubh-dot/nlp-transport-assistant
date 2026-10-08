"""Pure frontend contract helpers for the local T3 API."""

from __future__ import annotations

import os
from math import isfinite

import requests

from src.nlp_v2.contracts import OUTCOME_REASONS


DEFAULT_API_URL = "http://127.0.0.1:8765"


def ask_api(query: str, *, base_url: str | None = None, session=None, transport_mode: str | None = None) -> dict:
    """Submit one complete question; return a safe error object on API failure."""
    client = session or requests
    base = (base_url or os.environ.get("NLP_V2_API_URL") or DEFAULT_API_URL).rstrip("/")
    try:
        payload = {"query": query}
        if transport_mode is not None:
            payload['transport_mode'] = transport_mode
        response = client.post(base + "/api/v2/query", json=payload, timeout=20)
        result = response.json()
    except (requests.RequestException, ValueError, TypeError):
        return {"status": "error", "response_text": "The local T3 API is unavailable. Start the API and try again."}
    if not valid_reply(result):
        return {"status": "error", "response_text": "The T3 API returned an invalid response."}
    if response.status_code >= 400 and result["status"] != "error":
        return {"status": "error", "response_text": "The T3 API could not complete this request."}
    return result


PANEL_KINDS = {
    "PLAN_ROUTE": ("routes", "routes"),
    "PLAN_MULTIMODAL_ROUTE": ("routes", "routes"),
    "CHECK_SERVICE_AVAILABILITY": ("routes", "routes"),
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


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def _rows(value) -> bool:
    return isinstance(value, list) and all(isinstance(row, dict) for row in value)


def _valid_panel_data(operation, data: dict) -> bool:
    spec = PANEL_KINDS.get(operation)
    if not spec or spec[0] not in data:
        return True
    key, kind = spec
    value = data[key]
    if kind in {"routes", "departures", "nearest", "interchange"}:
        return _rows(value)
    if kind == "stops":
        return _rows(value) and all(_rows(row.get("stops", [])) for row in value)
    if kind in {"fare", "frequency"}:
        return _number(value)
    if kind == "membership":
        return isinstance(value, bool)
    if kind == "service_bounds":
        return isinstance(value, str) and isinstance(data.get("last_departure"), str)
    if kind == "accessibility":
        return isinstance(value, str) and isinstance(data.get("available"), bool)
    return True


def valid_reply(reply) -> bool:
    """Validate renderer-facing shapes at the API boundary before saving history."""
    if not isinstance(reply, dict) or not isinstance(reply.get("status"), str) or reply["status"] not in {"ok", "unavailable", "clarification", "out_of_scope", "error"} or not isinstance(reply.get("response_text"), str):
        return False
    for field in ("slots", "data"):
        if not isinstance(reply.get(field, {}), dict):
            return False
    if 'outcome_reason' in reply and (
            not isinstance(reply['outcome_reason'], str) or reply['outcome_reason'] not in OUTCOME_REASONS):
        return False
    for field in ("missing_slots", "candidate_entities", "candidate_intents"):
        values = reply.get(field, [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            return False
    for field in ("intent", "operation", "clarification_reason"):
        if reply.get(field) is not None and not isinstance(reply[field], str):
            return False
    if reply.get("data", {}).get("service_type") is not None and not isinstance(reply["data"]["service_type"], str):
        return False
    return reply["status"] != "ok" or _valid_panel_data(reply.get("operation"), reply.get("data", {}))


def result_panel(reply: dict) -> dict | None:
    """Select a display panel only when verified structured data is present."""
    if reply.get("status") != "ok" or not isinstance(reply.get("data"), dict) or not isinstance(reply.get("operation"), str):
        return None
    operation = reply.get("operation")
    if not _valid_panel_data(operation, reply["data"]):
        return None
    spec = PANEL_KINDS.get(operation)
    if not spec:
        return None
    key, kind = spec
    data = reply["data"]
    if key not in data:
        return None
    return {"kind": kind, "data": data, "operation": operation}
