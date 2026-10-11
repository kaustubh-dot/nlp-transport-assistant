"""Single production T3 utterance-to-response path."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from .text import normalize_extraction_text as normalize_text

from .contracts import IntentPrediction, validate_prediction
from .dispatch import DispatchResult, ServiceResult, OPERATIONS, dispatch
from .domain import CanonicalTransitService
from .entities import CanonicalResolver
from .model import T3IntentClassifier
from .slots import T3SlotExtractor, _route_number, _route_scope, _word_matches, _word_character, _timetable_reporting_modifier, _new_request_after_negative_predicate, _MEMBERSHIP_PREDICATE, _NATIVE_AVOIDANCE, _native_avoidance_has_operand

from .semantics import GOAL_CUES, _MEMBERSHIP_QUESTION_CUE, _cue_is_negated, _goal_clauses, _NEGATIVE_CONTRACTION

def selected_goal_negated(query: str, intent: str) -> bool:
    """Refuse an explicitly negated predicted goal; never select another one."""
    # A negative proposition ("doesn't this bus run?") still asks about
    # availability or membership. It does not exclude that question family.
    if intent in {'mode_availability', 'route_stop_membership'}:
        return False
    pattern = next((pattern for label, pattern in GOAL_CUES if label == intent), None)
    if pattern is None:
        return False
    polarity = [_cue_is_negated(clause, match) for clause in _goal_clauses(query)
                for match in _word_matches(pattern, clause)]
    return bool(polarity) and all(polarity)


def explicit_multiple_goals(query: str) -> tuple[str, ...]:
    clauses = _goal_clauses(query)
    if len(clauses) < 2:
        return ()
    goals = []
    found_clauses = []
    for clause in clauses:
        for intent, pattern in GOAL_CUES:
            matches = tuple(_word_matches(pattern, clause))
            if any(not _cue_is_negated(clause, match) for match in matches):
                found_clauses.append((intent, clause))
                if intent not in goals:
                    goals.append(intent)
                break
    # Departure-time nouns qualify a first/last-service request. They do not
    # independently request a second timetable operation without a new verb.
    if 'first_and_last_service' in goals and all(
            _timetable_reporting_modifier(clause)
            for intent, clause in found_clauses if intent == 'scheduled_departure'):
        goals = [goal for goal in goals if goal != 'scheduled_departure']
    positive_routes, excluded_routes, _ = _route_scope(query)
    incompatible_routes = len(positive_routes) > 1 or bool(positive_routes & excluded_routes)
    return tuple(goals) if len(goals) > 1 or incompatible_routes else ()


def explicit_membership_question(query: str) -> bool:
    """A stop-at question constrains the operation without reclassifying it."""
    auxiliary = r'does|do|is|are|was|were|can|could|will|would|has|have|kya|क्या|whether|if|' + _NEGATIVE_CONTRACTION
    for clause in _goal_clauses(query):
        for cue in _word_matches(_MEMBERSHIP_QUESTION_CUE, clause):
            if ('?' in query or '？' in query
                    or next(_word_matches(auxiliary, clause[:cue.start()]), None)
                    or next(_word_matches(r'kya|क्या', clause[cue.end():]), None)):
                return True
    return False


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
        'service_type': 'the bus service class (Ordinary, Express, Deluxe, Night or Air Conditioned)',
        'route_number': 'a supported route number including its complete suffix',
        'stage_number': 'a valid fare stage number',
        'via': 'a recognized waypoint after “via”',
    }
    return 'Please provide ' + ', '.join(descriptions.get(name, name.replace('_', ' ')) for name in names) + '.'


def _capability_check(method, *args) -> ServiceResult | None:
    if not callable(method):
        return None
    try:
        capability = method(*args)
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

    def process_query(self, query: str, *, default_transport_mode: str | None = None) -> AssistantReply:
        if not isinstance(query, str) or not any(char.isalnum() for char in query):
            return AssistantReply("error", "Please enter a transport question.", query if isinstance(query, str) else "", "", None, None, None,
                                  data={'reason': 'malformed_request'})
        normalized = normalize_text(query)
        try:
            prediction: IntentPrediction = self.classifier.predict(query)
            validate_prediction(prediction)
            if prediction.clarification_reason or prediction.primary_label is None:
                return self._reply(query, normalized, dispatch(prediction, {}, self.service))
            if selected_goal_negated(query, prediction.primary_label):
                return AssistantReply('clarification', 'Please clarify which transport question you mean.',
                                      query, normalized, None, None, prediction.confidence,
                                      data={'reason': 'negated_selected_goal'}, clarification_reason='intent_ambiguity',
                                      candidate_intents=prediction.acceptable_labels)
            goals = explicit_multiple_goals(query)
            if goals:
                if len(goals) == 1:
                    # Two separately asked scopes can share one T3 intent.
                    # This is a request guard, not an ambiguous model prediction.
                    return AssistantReply('clarification', 'Please ask one transport question at a time.',
                                          query, normalized, None, None, prediction.confidence,
                                          clarification_reason='multiple_goals', candidate_intents=goals)
                clarification = IntentPrediction(None, goals, prediction.confidence, "multiple_goals")
                return self._reply(query, normalized, dispatch(clarification, {}, self.service))
            intent = prediction.primary_label
            if intent != 'route_stop_membership' and explicit_membership_question(query):
                return AssistantReply('clarification', 'Please clarify which transport question you mean.',
                                      query, normalized, None, None, prediction.confidence,
                                      data={'reason': 'predicted_operation_conflict'}, clarification_reason='intent_ambiguity',
                                      candidate_intents=(intent, 'route_stop_membership'))
            if intent in {"out_of_scope", "realtime_status_query"}:
                result = dispatch(prediction, {}, self.service)
                return self._reply(query, normalized, result)

            # Keep legacy/injected extractors' one-question call unchanged when
            # no UI default was supplied. The raw classifier input is unchanged.
            extraction = (self.extractor.extract(query, intent) if default_transport_mode is None
                          else self.extractor.extract(query, intent, default_transport_mode=default_transport_mode))
            if extraction.multiple_execution_scopes:
                return AssistantReply('clarification', 'Please ask about one route, stop, fare stage or time at a time.',
                                      query, extraction.normalized_query, intent, None, prediction.confidence,
                                      clarification_reason='multiple_goals', candidate_intents=prediction.acceptable_labels)
            preflight = getattr(self.service, "preflight", None)
            capability = _capability_check(preflight, OPERATIONS[intent])
            if capability is not None:
                result = DispatchResult(intent, OPERATIONS[intent], capability.status, {},
                                        prediction.acceptable_labels, prediction.confidence,
                                        message=capability.message, data=capability.data)
                return self._reply(query, normalized, result)

            constraints = getattr(extraction, 'request_constraints', {})
            excluded = getattr(extraction, 'excluded_modes', ())
            if excluded and (not extraction.requested_modes or set(excluded) & set(extraction.requested_modes)):
                return AssistantReply('clarification', 'Please choose a transport mode that you want to use.',
                                      query, extraction.normalized_query, intent, None, prediction.confidence,
                                      dict(extraction.slots), {'excluded_modes': list(excluded)},
                                      missing_slots=('transport_mode',), clarification_reason='missing_slot',
                                      candidate_intents=prediction.acceptable_labels)
            if constraints.get('distance_metric') == 'walking_network':
                return AssistantReply('unavailable', 'Verified walking-distance routing is unavailable; straight-line distance cannot satisfy this request.',
                                      query, extraction.normalized_query, intent, OPERATIONS[intent], prediction.confidence,
                                      dict(extraction.slots), {'reason':'walking_network_unverified','request_constraints':constraints})
            if len(extraction.requested_modes) > 1 and intent not in {'multimodal_route', 'interchange_transfer'}:
                return AssistantReply(
                    'clarification', 'Please choose one transport mode for this question.',
                    query, extraction.normalized_query, intent, None, prediction.confidence,
                    dict(extraction.slots), {'requested_modes': list(extraction.requested_modes)},
                    missing_slots=('transport_mode',), clarification_reason='missing_slot',
                    candidate_intents=prediction.acceptable_labels,
                )
            if getattr(extraction, 'unsupported_timetable_waypoint', False):
                result = DispatchResult(intent, OPERATIONS[intent], 'unavailable', dict(extraction.slots),
                                        prediction.acceptable_labels, prediction.confidence,
                                        message='Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.',
                                        data={'reason': 'timetable_waypoint_scope_unsupported'})
                return self._reply(query, extraction.normalized_query, result)
            if extraction.unsupported_temporal_scope:
                result = DispatchResult(intent, OPERATIONS[intent], 'unavailable', dict(extraction.slots),
                                        prediction.acceptable_labels, prediction.confidence,
                                        message='Before-time, time-range and period-only requests are not supported by this operation.',
                                        data={'reason': 'unsupported temporal scope', 'request_constraints': constraints})
                return self._reply(query, extraction.normalized_query, result)
            capability = _capability_check(getattr(self.service, 'preflight_mode', None),
                                           OPERATIONS[intent], extraction.slots.get('transport_mode'))
            if capability is not None:
                result = DispatchResult(intent, OPERATIONS[intent], capability.status, dict(extraction.slots),
                                        prediction.acceptable_labels, prediction.confidence,
                                        message=capability.message, data=capability.data)
                return self._reply(query, extraction.normalized_query, result)
            if extraction.missing_execution_slots:
                refusal = (_capability_check(getattr(self.service, 'preflight_fare_class', None), extraction.slots)
                           if intent == 'fare_calculation' else None)
                if refusal is not None:
                    result = DispatchResult(intent, OPERATIONS[intent], refusal.status, dict(extraction.slots),
                                            prediction.acceptable_labels, prediction.confidence,
                                            message=refusal.message, data=refusal.data)
                else:
                    result = DispatchResult(intent, OPERATIONS[intent], 'clarification', dict(extraction.slots),
                                            prediction.acceptable_labels, prediction.confidence,
                                            missing_slots=extraction.missing_execution_slots, reason='missing_slot')
                return self._reply(query, extraction.normalized_query, result)
            if extraction.clarification_reason:
                candidates = tuple(sorted({candidate.entity_id for unresolved in extraction.unresolved
                                           for candidate in unresolved.candidates}))
                reason = extraction.clarification_reason
                text = "Please clarify which stop or location you mean." if reason == "entity_ambiguity" else "Please clarify the time or day you mean."
                details = (self.resolver.describe_candidates(candidates)
                           if reason == 'entity_ambiguity' and hasattr(self.resolver, 'describe_candidates') else [])
                if details:
                    text += ' Candidates: ' + '; '.join(
                        f"{row['canonical_name']} ({row['mode'] or row['kind']}, {row['entity_id']})"
                        for row in details) + '.'
                return AssistantReply(
                    "clarification", text, query, extraction.normalized_query, intent,
                    None, prediction.confidence, dict(extraction.slots),
                    data={'entity_candidates': details} if details else {},
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
