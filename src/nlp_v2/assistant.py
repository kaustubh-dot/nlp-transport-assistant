"""Single production T3 utterance-to-response path."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.normalization import normalize_text

from .contracts import IntentPrediction, validate_prediction
from .dispatch import DispatchResult, ServiceResult, OPERATIONS, dispatch
from .domain import CanonicalTransitService
from .entities import CanonicalResolver
from .model import T3IntentClassifier
from .slots import T3SlotExtractor


# This guard only requests clarification for independently expressed conjoined
# goals. It never chooses an operation or substitutes a rule-based classifier.
GOAL_CUES = (
    ("first_and_last_service", r"(?:first|last|पहली|पहला|आखिरी|pehli|pehla|aakhiri)\s+(?:buses|bus|trains?|metro|service|departure|timing|time|बस|ट्रेन|मेट्रो|सेवा)(?!\w)(?!\s+(?:stops?|station|स्टॉप|स्टेशन))"),
    ("service_frequency", r"frequency|headway|how often|kitni der|कितनी देर"),
    ("scheduled_departure", r"departures?|schedule|timetable|छूटे|chhut|schedule"),
    ("fare_calculation", r"fare|cost|price|किराया|kiraya"),
    ("station_accessibility", r"wheelchair|ramp|lift|escalator|व्हीलचेयर|लिफ्ट|रैंप"),
    ("station_facilities", r"parking|toilet|restroom|wifi|atm|पार्किंग|शौचालय"),
    ("ticketing_and_passes", r"pass|ticket rules|smart card|टिकट|पास"),
    ("route_stop_sequence", r"all stops|list stops|stop sequence|सभी स्टॉप"),
    ("route_stop_membership", r"stop at|stops at|रुकती|rukti"),
    ("nearest_transport", r"nearest|closest|nazdik|नजदीक"),
    ("interchange_transfer", r"transfer|interchange|बदलना|badalna"),
    ("realtime_status_query", r"live|realtime|delay|अभी कहाँ"),
    ("point_to_point_route", r"route|how to get|kaise|कैसे"),
    ("mode_availability", r"available|availability|चलती|chalti"),
)


def explicit_multiple_goals(query: str) -> tuple[str, ...]:
    text = normalize_text(query)
    # Coordinated endpoint/time modifiers describe one request, not two clauses.
    text = re.sub(r"(?<!\w)(first|पहली|पहला|pehli|pehla)\s+(?:and|aur|और)\s+(last|आखिरी|aakhiri)(?!\w)", r"\1 \2", text)
    clauses = re.split(r"(?<!\w)(?:and|also|aur|और|साथ ही)(?!\w)", text)
    if len(clauses) < 2:
        return ()
    goals = []
    for clause in clauses:
        for intent, pattern in GOAL_CUES:
            if re.search(r"(?<!\w)(?:" + pattern + r")(?!\w)", clause):
                if intent not in goals:
                    goals.append(intent)
                break
    return tuple(goals) if len(goals) > 1 else ()


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

    @property
    def outcome_reason(self) -> str:
        if self.status == 'clarification':
            return 'missing_execution_slot' if self.clarification_reason == 'missing_slot' else (self.clarification_reason or 'intent_ambiguity')
        if self.status == 'unavailable':
            return 'external_source_required' if self.intent == 'realtime_status_query' else 'unsupported_source'
        if self.status == 'error':
            return 'malformed_request' if self.data.get('reason') == 'malformed_request' else 'temporary_service_unavailability'
        return 'answered' if self.status == 'ok' else 'out_of_scope'


def _missing_prompt(names: tuple[str, ...]) -> str:
    if {'origin_or_stage_number', 'destination_or_stage_number'} <= set(names):
        return 'Please provide a fare stage number, or the starting and destination stops.'
    descriptions = {
        'origin': 'the starting stop', 'destination': 'the destination stop',
        'stop': 'the stop to check', 'station': 'the station',
        'station_or_stop': 'the boarding stop or station',
        'route_number_or_line_name': 'the route number or line name',
        'origin_or_stage_number': 'the starting stop or fare stage number',
        'destination_or_stage_number': 'the destination stop or fare stage number',
        'landmark_or_locality': 'a nearby landmark or locality',
        'station_or_mode_pair': 'the transfer station or the two transport modes',
        'transport_mode': 'one transport mode',
    }
    return 'Please provide ' + ', '.join(descriptions.get(name, name.replace('_', ' ')) for name in names) + '.'


def _capability_check(method, operation: str, *args) -> ServiceResult | None:
    if not callable(method):
        return None
    try:
        capability = method(operation, *args)
        if capability is not None and (
                not isinstance(capability, ServiceResult)
                or capability.status not in {'unavailable', 'error'}
                or not isinstance(capability.data, dict)
                or not isinstance(capability.message, str)):
            raise ValueError('Invalid capability preflight state')
        return capability
    except Exception:
        return ServiceResult('error', {}, 'The transport service could not complete the request.')


def _answer(result: DispatchResult) -> str:
    """Render only facts supplied by the canonical service."""
    if result.status == "clarification":
        if result.reason == "missing_slot":
            return _missing_prompt(result.missing_slots)
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
        service = f" ({data['service_type']})" if data.get("service_type") else ""
        detail = f"Published fare{service}: {data['currency']} {data['amount']:g} (record effective {data['effective_date']}). "
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
        if not isinstance(query, str) or not any(char.isalnum() for char in query):
            return AssistantReply("error", "Please enter a transport question.", query if isinstance(query, str) else "", "", None, None, None,
                                  data={'reason': 'malformed_request'})
        normalized = normalize_text(query)
        try:
            prediction: IntentPrediction = self.classifier.predict(query)
            validate_prediction(prediction)
            if prediction.clarification_reason or prediction.primary_label is None:
                return self._reply(query, normalized, dispatch(prediction, {}, self.service))
            goals = explicit_multiple_goals(query)
            if goals:
                clarification = IntentPrediction(None, goals, prediction.confidence, "multiple_goals")
                return self._reply(query, normalized, dispatch(clarification, {}, self.service))
            intent = prediction.primary_label
            if intent in {"out_of_scope", "realtime_status_query"}:
                result = dispatch(prediction, {}, self.service)
                return self._reply(query, normalized, result)

            preflight = getattr(self.service, "preflight", None)
            capability = _capability_check(preflight, OPERATIONS[intent])
            if capability is not None:
                result = DispatchResult(intent, OPERATIONS[intent], capability.status, {},
                                        prediction.acceptable_labels, prediction.confidence,
                                        message=capability.message, data=capability.data)
                return self._reply(query, normalized, result)

            extraction = self.extractor.extract(query, intent)
            if len(extraction.requested_modes) > 1 and intent not in {'multimodal_route', 'interchange_transfer'}:
                return AssistantReply(
                    'clarification', 'Please choose one transport mode for this question.',
                    query, extraction.normalized_query, intent, None, prediction.confidence,
                    dict(extraction.slots), {'requested_modes': list(extraction.requested_modes)},
                    missing_slots=('transport_mode',), clarification_reason='missing_slot',
                    candidate_intents=prediction.acceptable_labels,
                )
            capability = _capability_check(getattr(self.service, 'preflight_mode', None),
                                           OPERATIONS[intent], extraction.slots.get('transport_mode'))
            if capability is not None:
                result = DispatchResult(intent, OPERATIONS[intent], capability.status, dict(extraction.slots),
                                        prediction.acceptable_labels, prediction.confidence,
                                        message=capability.message, data=capability.data)
                return self._reply(query, extraction.normalized_query, result)
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
