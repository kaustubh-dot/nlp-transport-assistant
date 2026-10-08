"""Local JSON API contract tests without binding restricted sandbox sockets."""

import json

import pytest

from src.nlp_v2.assistant import AssistantReply


class FakeAssistant:
    def process_query(self, query):
        return AssistantReply(
            status="clarification", response_text="Please provide origin.",
            raw_query=query, normalized_query="private normalized text",
            intent="point_to_point_route", operation="PLAN_ROUTE", confidence=0.91,
            slots={"destination": "HUB_GUINDY"}, missing_slots=("origin",),
            clarification_reason="missing_slot", candidate_intents=("point_to_point_route",),
        )


def request(path, payload=None, content_type="application/json", method=None, assistant=None):
    from app.api import handle_request

    body = b"" if payload is None else json.dumps(payload).encode()
    return handle_request(
        method or ("GET" if payload is None else "POST"), path,
        {"Content-Type": content_type, "Content-Length": str(len(body))},
        body, assistant or FakeAssistant(),
    )


def test_health_and_public_query_schema():
    status, health = request("/health")
    assert status == 200 and health == {"status": "ok", "taxonomy": "T3"}
    status, body = request("/api/v2/query", {"query": "How to Guindy?"})
    assert status == 200
    assert body["status"] == "clarification"
    assert body["missing_slots"] == ["origin"]
    assert body["slots"]["destination"] == "HUB_GUINDY"
    assert body["candidate_intents"] == ["point_to_point_route"]
    assert "raw_query" not in body and "normalized_query" not in body and "confidence" not in body


@pytest.mark.parametrize('mode', ['bus', 'metro', 'suburban_rail', 'mrts'])
def test_api_passes_selected_mode_separately_from_exact_question(mode):
    calls = []

    class ModeAssistant(FakeAssistant):
        def process_query(self, query, *, default_transport_mode=None):
            calls.append((query, default_transport_mode))
            return super().process_query(query)

    query = 'गिंडी से Central कैसे जाऊँ?'
    status, _ = request('/api/v2/query', {'query': query, 'transport_mode': mode}, assistant=ModeAssistant())
    assert status == 200
    assert calls == [(query, mode)]


@pytest.mark.parametrize('mode', ['rail', 'hovercraft', '', None, 4, True, [], {}])
def test_api_rejects_invalid_mode_before_assistant(mode):
    class Uncalled:
        def process_query(self, *args, **kwargs):
            raise AssertionError('Invalid mode reached the assistant')

    status, reply = request('/api/v2/query', {'query': 'route please', 'transport_mode': mode}, assistant=Uncalled())
    assert status == 422
    assert reply['status'] == 'error'
    assert reply['outcome_reason'] == 'malformed_request'


@pytest.mark.parametrize("payload,expected", [
    ({}, 422), ({"query": ""}, 422), ({"query": 42}, 422),
    ({"query": "x" * 9000}, 413),
])
def test_bad_query_rejected(payload, expected):
    status, body = request("/api/v2/query", payload)
    assert status == expected
    assert body["status"] == "error"


def test_unknown_path_media_type_and_malformed_json_rejected():
    from app.api import handle_request

    assert request("/missing")[0] == 404
    assert request("/api/v2/query", {"query": "x"}, "text/plain")[0] == 415
    assert handle_request("POST", "/api/v2/query", {
        "Content-Type": "application/json", "Content-Length": "1",
    }, b"{", FakeAssistant())[0] == 400


def test_assistant_error_has_no_internal_exception_text():
    class BrokenAssistant:
        def process_query(self, query):
            raise RuntimeError("sensitive local file path")

    status, body = request("/api/v2/query", {"query": "bus"}, assistant=BrokenAssistant())
    assert status == 503
    assert "sensitive" not in body["response_text"]


def test_lowercase_header_names_are_accepted():
    from app.api import handle_request

    body = b'{"query":"bus"}'
    status, response = handle_request(
        "POST", "/api/v2/query",
        {"content-type": "application/json", "content-length": str(len(body))},
        body, FakeAssistant(),
    )
    assert status == 200
    assert response["status"] == "clarification"


def test_body_read_timeout_is_typed_for_adapter():
    from app.api import RequestTimeout, read_body

    class StalledBody:
        def read(self, length):
            raise TimeoutError("client stalled")

    with pytest.raises(RequestTimeout):
        read_body(StalledBody(), 16)
