"""Frontend API client and panel tests using synthetic replies."""

import pytest


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def post(self, url, json=None, timeout=None):
        self.calls.append((url, json, timeout))
        if self.error:
            raise self.error
        return self.response


def test_api_client_sends_query_and_accepts_structured_reply():
    from app.frontend_contract import ask_api

    session = FakeSession(FakeResponse(200, {"status": "clarification", "response_text": "Provide origin.", "missing_slots": ["origin"]}))
    reply = ask_api("How to Guindy?", base_url="http://127.0.0.1:8765", session=session)
    assert reply["status"] == "clarification"
    assert session.calls == [("http://127.0.0.1:8765/api/v2/query", {"query": "How to Guindy?"}, 20)]


def test_api_client_reports_offline_and_malformed_response():
    import requests
    from app.frontend_contract import ask_api

    offline = ask_api("bus", session=FakeSession(error=requests.ConnectionError("offline")))
    malformed = ask_api("bus", session=FakeSession(FakeResponse(200, {"unexpected": 1})))
    assert offline["status"] == "error"
    assert "API" in offline["response_text"]
    assert malformed["status"] == "error"


@pytest.mark.parametrize("body", [
    {"status": "unavailable", "response_text": "Unavailable", "data": []},
    {"status": "clarification", "response_text": "Choose", "candidate_entities": [None]},
    {"status": "ok", "response_text": "Fare", "operation": "CALCULATE_FARE", "data": {"amount": "bad"}},
    {"status": "ok", "response_text": "Stops", "operation": "LIST_ROUTE_STOPS", "data": {"sequences": [None]}},
])
def test_api_client_rejects_reply_shapes_that_would_crash_rendering(body):
    from app.frontend_contract import ask_api

    assert ask_api("question", session=FakeSession(FakeResponse(200, body)))["status"] == "error"


@pytest.mark.parametrize("health_body", [[], None, "unavailable"])
def test_streamlit_malformed_health_response_degrades_to_offline(monkeypatch, health_body):
    import requests
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(200, health_body))
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=10)
    assert not app.exception
    assert any("API is offline" in warning.value for warning in app.warning)


@pytest.mark.parametrize("operation,data,expected_kind", [
    ("PLAN_ROUTE", {"routes": [{"route_name": "102", "mode": "bus"}]}, "routes"),
    ("LIST_ROUTE_STOPS", {"sequences": [{"stops": []}]}, "stops"),
    ("GET_SCHEDULED_DEPARTURES", {"departures": [{"route_name": "102", "time": "08:00:00"}]}, "departures"),
    ("CALCULATE_FARE", {"amount": 40, "currency": "INR"}, "fare"),
    ("GET_ACCESSIBILITY_INFO", {"feature": "lift", "available": True}, "accessibility"),
    ("FIND_NEAREST_STATION", {"stops": [{"name": "Metro", "distance_m": 100}]}, "nearest"),
    ("GET_INTERCHANGE_DETAILS", {"transfers": [{"from_stop_id": "A", "to_stop_id": "B"}]}, "interchange"),
    ("CHECK_STOP_ON_ROUTE", {"on_route": False}, "membership"),
    ("GET_FIRST_LAST_SERVICE", {"first_departure": "05:00:00", "last_departure": "23:00:00"}, "service_bounds"),
    ("GET_SERVICE_FREQUENCY", {"median_headway_minutes": 10}, "frequency"),
    ("GET_STATION_FACILITY", {"facility": "parking"}, "facility"),
    ("GET_TICKETING_POLICY", {"policy": "published"}, "ticketing"),
])
def test_result_panel_selection(operation, data, expected_kind):
    from app.frontend_contract import result_panel

    assert result_panel({"status": "ok", "operation": operation, "data": data})["kind"] == expected_kind


def test_unavailable_and_error_do_not_render_success_panels():
    from app.frontend_contract import result_panel

    assert result_panel({"status": "unavailable", "operation": "PLAN_ROUTE", "data": {"routes": []}}) is None
    assert result_panel({"status": "error", "operation": "CALCULATE_FARE", "data": {"amount": 40}}) is None


def test_published_connectivity_has_candidate_source_panel():
    from app.frontend_contract import result_panel
    data = {'routes': [{'route_name': '88', 'mode': 'bus', 'source': 'synthetic'}],
            'scope': 'published_connectivity_not_current_operation', 'provisional': True}
    panel = result_panel({'status': 'ok', 'operation': 'CHECK_SERVICE_AVAILABILITY', 'data': data})
    assert panel is not None
    assert panel['kind'] == 'routes'
    assert panel['data']['routes'][0]['source'] == 'synthetic'


def test_streamlit_chat_shows_api_clarification_and_revision_form(monkeypatch):
    import requests
    from streamlit.testing.v1 import AppTest

    calls = []

    def get(url, timeout):
        return FakeResponse(200, {"status": "ok", "taxonomy": "T3"})

    def post(url, json, timeout):
        calls.append((url, json))
        return FakeResponse(200, {
            "status": "clarification", "response_text": "Please provide origin.",
            "intent": "point_to_point_route", "operation": "PLAN_ROUTE",
            "slots": {"destination": "HUB_GUINDY"}, "data": {},
            "missing_slots": ["origin"], "clarification_reason": "missing_slot",
            "candidate_entities": [], "candidate_intents": ["point_to_point_route"],
        })

    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(requests, "post", post)
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert not app.exception
    assert calls and calls[0][0].endswith("/api/v2/query")
    assert app.text_input[0].label == "Revise / संशोधित करें / Badlein"
    assert any(item.value == "Revise your full question" for item in app.caption)
    assert any("Please provide origin" in info.value for info in app.info)


def test_entity_clarification_explains_choice_without_internal_ids(monkeypatch):
    import requests
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(200, {"status": "ok", "taxonomy": "T3"}))
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(200, {
        "status": "clarification", "response_text": "Please clarify the location.",
        "intent": "point_to_point_route", "operation": None, "slots": {}, "data": {},
        "missing_slots": [], "clarification_reason": "entity_ambiguity",
        "candidate_entities": ["HUB_CENTRAL", "METRO_CENTRAL"],
        "candidate_intents": ["point_to_point_route"],
    }))
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert not app.exception
    captions = ' '.join(caption.value for caption in app.caption)
    assert 'More than one stop' in captions
    assert 'transport mode' in captions
    assert 'HUB_CENTRAL' not in captions and 'METRO_CENTRAL' not in captions


@pytest.mark.parametrize('status,label', [
    ('ok','Published information'), ('clarification','More information needed'),
    ('unavailable','Information unavailable'), ('out_of_scope','Outside transport scope'),
    ('error','Request could not be completed'),
])
def test_chat_labels_all_statuses_and_retains_snapshot_limit(monkeypatch, status, label):
    import requests
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(requests, 'get', lambda *a, **k: FakeResponse(200, {'status':'ok','taxonomy':'T3'}))
    monkeypatch.setattr(requests, 'post', lambda *a, **k: FakeResponse(200, {
        'status':status,'response_text':'Test message.', 'data':{}, 'slots':{},
    }))
    app = AppTest.from_file('app/streamlit_app.py').run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert not app.exception
    captions=' '.join(c.value for c in app.caption)
    assert label in captions
    assert 'No live updates' in captions
    assert not app.metric
    if status in {'unavailable','error'}:
        assert any(e.value=='Test message.' for e in (app.warning if status=='unavailable' else app.error))


def test_partial_route_panel_discloses_omissions_without_internal_ids(monkeypatch):
    import requests
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(requests, 'get', lambda *a, **k: FakeResponse(200, {'status':'ok','taxonomy':'T3'}))
    monkeypatch.setattr(requests, 'post', lambda *a, **k: FakeResponse(200, {
        'status':'ok','response_text':'Published sequence.', 'operation':'LIST_ROUTE_STOPS',
        'data':{'partial_topology':True,'excluded_unusable_rows':2,'uncovered_route_ids':['PRIVATE_VARIANT'],
                'provisional':True,'sequences':[{'route_name':'102','source':'SCHEDULE_SOURCE',
                'stops':[{'sequence':1,'name':'Example stop','stop_id':'PRIVATE_STOP'}]}]},
    }))
    app=AppTest.from_file('app/streamlit_app.py').run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert not app.exception
    captions=' '.join(c.value for c in app.caption)
    assert 'Partial published coverage' in captions
    assert '2 unusable links' in captions and '1 route variant' in captions
    assert 'PRIVATE_VARIANT' not in captions
    assert 'stop_id' not in list(app.dataframe[0].value.columns)


@pytest.mark.parametrize('operation,data', [
    ('CALCULATE_FARE', {'amount':17,'routes':None}),
    ('CALCULATE_FARE', {'amount':17,'routes':[None]}),
    ('LIST_ROUTE_STOPS', {'sequences':[{'stops':[]}], 'partial_topology':True,
                          'excluded_unusable_rows':2,'uncovered_route_ids':None}),
])
def test_optional_coverage_metadata_never_exposes_renderer_exception(monkeypatch, operation, data):
    import requests
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(requests, 'get', lambda *a, **k: FakeResponse(200, {'status':'ok','taxonomy':'T3'}))
    monkeypatch.setattr(requests, 'post', lambda *a, **k: FakeResponse(200, {
        'status':'ok','response_text':'Published information.', 'operation':operation,'data':data,
    }))
    app=AppTest.from_file('app/streamlit_app.py').run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert not app.exception


@pytest.mark.parametrize("operation,data,expected", [
    ("LIST_ROUTE_STOPS", {"sequences": [{"route_name": "102", "direction_id": 0, "source": "GTFS_SOURCE", "stops": [{"sequence": 1, "name": "A", "stop_id": "BUS_A"}]}], "truncated": True}, "GTFS_SOURCE"),
    ("GET_FIRST_LAST_SERVICE", {"first_departure": "05:00", "last_departure": "23:00", "source": ["TIMETABLE_SOURCE"]}, "TIMETABLE_SOURCE"),
    ("GET_SERVICE_FREQUENCY", {"median_headway_minutes": 10, "source": ["FREQUENCY_SOURCE"]}, "FREQUENCY_SOURCE"),
])
def test_structured_panels_show_source(monkeypatch, operation, data, expected):
    import requests
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(200, {"status": "ok", "taxonomy": "T3"}))
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(200, {
        "status": "ok", "response_text": "Published snapshot result.",
        "intent": "route_stop_sequence", "operation": operation,
        "slots": {}, "data": data, "missing_slots": [],
        "clarification_reason": None, "candidate_entities": [], "candidate_intents": [],
    }))
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert not app.exception
    assert any(expected in caption.value for caption in app.caption)
    if operation == "LIST_ROUTE_STOPS":
        assert any("additional" in caption.value.lower() for caption in app.caption)
