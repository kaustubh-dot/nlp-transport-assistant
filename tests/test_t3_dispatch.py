"""Contract tests for frozen T3 production dispatch."""

import pytest


@pytest.mark.parametrize("intent,slots", [
    ("route_stop_sequence", {"line_name": "Blue Line"}),
    ("route_stop_membership", {"line_name": "Blue Line", "stop": "METRO_1"}),
])
def test_line_name_satisfies_route_identifier_requirement(intent, slots):
    from src.nlp_v2.contracts import missing_slots
    assert missing_slots(intent, slots) == ()


CASES = [
    ("point_to_point_route", "PLAN_ROUTE", {"origin": "HUB_A", "destination": "HUB_B"}),
    ("multimodal_route", "PLAN_MULTIMODAL_ROUTE", {"origin": "HUB_A", "destination": "HUB_B"}),
    ("route_stop_sequence", "LIST_ROUTE_STOPS", {"route_number": "29C"}),
    ("route_stop_membership", "CHECK_STOP_ON_ROUTE", {"route_number": "29C", "stop": "BUS_1"}),
    ("first_and_last_service", "GET_FIRST_LAST_SERVICE", {"station": "BUS_1"}),
    ("service_frequency", "GET_SERVICE_FREQUENCY", {"station": "BUS_1", "route_number": "29C"}),
    ("scheduled_departure", "GET_SCHEDULED_DEPARTURES", {"station": "METRO_1"}),
    ("mode_availability", "CHECK_SERVICE_AVAILABILITY", {"origin": "HUB_A", "destination": "HUB_B"}),
    ("fare_calculation", "CALCULATE_FARE", {"origin": "METRO_1", "destination": "METRO_2"}),
    ("ticketing_and_passes", "GET_TICKETING_POLICY", {}),
    ("station_facilities", "GET_STATION_FACILITY", {"station": "METRO_1"}),
    ("station_accessibility", "GET_ACCESSIBILITY_INFO", {"station": "METRO_1"}),
    ("interchange_transfer", "GET_INTERCHANGE_DETAILS", {"station": "HUB_A"}),
    ("nearest_transport", "FIND_NEAREST_STATION", {"landmark": "PLACE_1"}),
    ("realtime_status_query", "REJECT_UNSUPPORTED_REALTIME", {}),
    ("out_of_scope", "REJECT_OUT_OF_SCOPE", {}),
]


class RecordingService:
    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def execute(self, operation, slots):
        from src.nlp_v2.dispatch import ServiceResult

        self.calls.append((operation, dict(slots)))
        return self.result or ServiceResult("ok", {"source": "fixture"}, "Found data")


@pytest.mark.parametrize("intent,operation,slots", CASES)
def test_each_t3_intent_has_one_explicit_operation(intent, operation, slots):
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService()
    result = dispatch(IntentPrediction(intent, (intent,), 0.92), slots, service)
    assert result.intent == intent
    assert result.operation == operation
    if intent == "realtime_status_query":
        assert result.status == "unavailable"
        assert service.calls == []
    elif intent == "out_of_scope":
        assert result.status == "out_of_scope"
        assert service.calls == []
    else:
        assert result.status == "ok"
        assert service.calls == [(operation, slots)]
        assert result.data == {"source": "fixture"}


@pytest.mark.parametrize("intent,slots,missing", [
    ("point_to_point_route", {"destination": "HUB_B"}, ("origin",)),
    ("multimodal_route", {"origin": "HUB_A"}, ("destination",)),
    ("route_stop_membership", {"route_number": "29C"}, ("stop",)),
    ("scheduled_departure", {}, ("station_or_stop",)),
    ("fare_calculation", {"origin": "METRO_1"}, ("destination_or_stage_number",)),
    ("interchange_transfer", {"mode_from": "metro"}, ("station_or_mode_pair",)),
    ("nearest_transport", {}, ("landmark_or_locality",)),
])
def test_missing_execution_slots_clarify_without_service(intent, slots, missing):
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService()
    result = dispatch(IntentPrediction(intent, (intent,), 0.9), slots, service)
    assert result.status == "clarification"
    assert result.reason == "missing_slot"
    assert result.missing_slots == missing
    assert service.calls == []


def test_conditional_slots_can_satisfy_fare_interchange_and_nearest():
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService()
    for intent, slots in [
        ("fare_calculation", {"stage_number": 4}),
        ("interchange_transfer", {"mode_from": "metro", "mode_to": "bus"}),
        ("nearest_transport", {"locality": "PLACE_1"}),
        ("scheduled_departure", {"stop": "BUS_1"}),
    ]:
        result = dispatch(IntentPrediction(intent, (intent,), 0.9), slots, service)
        assert result.status == "ok"
    assert len(service.calls) == 4


def test_semantic_ambiguity_and_multiple_goals_preserve_candidates():
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService()
    ambiguous = dispatch(IntentPrediction(None, ("scheduled_departure", "mode_availability"), 0.5, "intent_ambiguity"), {}, service)
    assert ambiguous.status == "clarification"
    assert ambiguous.reason == "intent_ambiguity"
    assert ambiguous.acceptable_labels == ("scheduled_departure", "mode_availability")
    multiple = dispatch(IntentPrediction("fare_calculation", ("fare_calculation", "first_and_last_service"), 0.8, "multiple_goals"), {}, service)
    assert multiple.status == "clarification"
    assert multiple.reason == "multiple_goals"
    assert service.calls == []


def test_multiple_goal_slots_do_not_fail_primary_intent_restrictions():
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService()
    result = dispatch(IntentPrediction("fare_calculation", ("fare_calculation", "first_and_last_service"),
                                       0.8, "multiple_goals"),
                      {"origin": "METRO_1", "destination": "METRO_2", "station": "METRO_1"}, service)
    assert result.status == "clarification"
    assert result.reason == "multiple_goals"
    assert service.calls == []


@pytest.mark.parametrize("prediction,slots", [
    (("route_query", ("route_query",), 0.9), {}),
    (("point_to_point_route", ("point_to_point_route",), 1.1), {}),
    (("point_to_point_route", ("point_to_point_route",), 0.9), {"invented_slot": "x"}),
    (("point_to_point_route", ("point_to_point_route",), 0.9), {"transport_mode": "teleport"}),
    (("fare_calculation", ("fare_calculation",), 0.9), {"stage_number": 31}),
])
def test_invalid_predictions_or_slots_raise_contract_error(prediction, slots):
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import ContractError, IntentPrediction

    with pytest.raises(ContractError):
        dispatch(IntentPrediction(*prediction), slots, RecordingService())


def test_default_service_and_service_failure_are_explicit():
    from src.nlp_v2.dispatch import ServiceResult, dispatch
    from src.nlp_v2.contracts import IntentPrediction

    prediction = IntentPrediction("station_facilities", ("station_facilities",), 0.9)
    unavailable = dispatch(prediction, {"station": "METRO_1"})
    assert unavailable.status == "unavailable"
    assert unavailable.data == {}

    service = RecordingService(ServiceResult("unavailable", {}, "No verified record"))
    result = dispatch(prediction, {"station": "METRO_1"}, service)
    assert result.status == "unavailable"
    assert result.message == "No verified record"

    class BrokenService:
        def execute(self, operation, slots):
            raise RuntimeError("database offline")

    failed = dispatch(prediction, {"station": "METRO_1"}, BrokenService())
    assert failed.status == "error"
    assert failed.data == {}
    assert "database offline" not in failed.message


@pytest.mark.parametrize("slots,reason", [
    ({"station": "METRO_1", "time": ["08:00:00", "20:00:00"]}, None),
    ({"station": "METRO_1", "temporal_relative": "kal"}, None),
    ({"station": "METRO_1", "time": "08:00:00"}, "temporal_ambiguity"),
])
def test_unresolved_temporal_inputs_clarify_without_execution(slots, reason):
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService()
    result = dispatch(IntentPrediction("scheduled_departure", ("scheduled_departure",), 0.9, reason), slots, service)
    assert result.status == "clarification"
    assert result.reason == "temporal_ambiguity"
    assert service.calls == []


@pytest.mark.parametrize("slot,value", [
    ("station", 123),
    ("origin", "Guindy"),
    ("route_number", 29),
    ("facility_type", "helipad"),
    ("ticket_type", "cash"),
    ("accessibility_feature", "skybridge"),
    ("preference", "scenic"),
    ("ticket_type", ["token"]),
    ("line_name", "Purple Line"),
    ("time", "8pm"),
    ("date", "2026-19-40"),
])
def test_malformed_canonical_slot_values_are_rejected(slot, value):
    from src.nlp_v2.contracts import ContractError, validate_slots

    with pytest.raises(ContractError):
        validate_slots({slot: value})


@pytest.mark.parametrize("intent,slots", [
    ("station_facilities", {"station": "METRO_1", "origin": "HUB_A"}),
    ("station_accessibility", {"station": "METRO_1", "route_number": "29C"}),
    ("route_stop_membership", {"route_number": "29C", "stop": "BUS_1", "fare_type": "stage_fare"}),
    ("point_to_point_route", {"origin": "HUB_A", "destination": "HUB_B", "station": "METRO_1"}),
])
def test_forbidden_intent_slot_combinations_do_not_execute(intent, slots):
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import ContractError, IntentPrediction

    service = RecordingService()
    with pytest.raises(ContractError):
        dispatch(IntentPrediction(intent, (intent,), 0.9), slots, service)
    assert service.calls == []


def test_unknown_clarification_reason_is_rejected():
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import ContractError, IntentPrediction

    with pytest.raises(ContractError):
        dispatch(IntentPrediction("scheduled_departure", ("scheduled_departure",), 0.9, "guess"),
                 {"station": "METRO_1"}, RecordingService())


def test_malformed_service_response_becomes_error_state():
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService(result={"status": "ok", "data": {"made_up": True}})
    result = dispatch(IntentPrediction("station_facilities", ("station_facilities",), 0.9),
                      {"station": "METRO_1"}, service)
    assert result.status == "error"
    assert result.data == {}


@pytest.mark.parametrize("intent,want", [
    ("realtime_status_query", "unavailable"),
    ("out_of_scope", "out_of_scope"),
])
def test_terminal_intents_do_not_ask_for_temporal_clarification(intent, want):
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    result = dispatch(IntentPrediction(intent, (intent,), 0.9), {"temporal_relative": "kal"}, RecordingService())
    assert result.status == want


@pytest.mark.parametrize("intent", ["point_to_point_route", "multimodal_route"])
def test_route_intents_accept_canonical_locality(intent):
    from src.nlp_v2.dispatch import dispatch
    from src.nlp_v2.contracts import IntentPrediction

    service = RecordingService()
    result = dispatch(IntentPrediction(intent, (intent,), 0.9),
                      {"origin": "HUB_A", "destination": "HUB_B", "locality": "PLACE_1"}, service)
    assert result.status == "ok"
    assert service.calls[0][1]["locality"] == "PLACE_1"


@pytest.mark.parametrize('intent,slots,want',[
    ('first_and_last_service',{'route_number':'25R'},('station_or_stop',)),
    ('service_frequency',{'route_number':'25R'},('station_or_stop',)),
    ('service_frequency',{'station':'BUS_A'},('route_number_or_line_name',)),
    ('scheduled_departure',{'origin':'BUS_A'},()),
])
def test_schedule_requirements_match_the_information_consumed(intent,slots,want):
    from src.nlp_v2.contracts import missing_slots
    assert missing_slots(intent,slots) == want
