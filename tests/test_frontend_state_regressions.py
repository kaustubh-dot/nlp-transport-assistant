"""Real Streamlit ScriptRunner control interrupts, independent of challenge data."""
import pytest
import requests
from streamlit.testing.v1 import AppTest
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.runtime.scriptrunner_utils.script_requests import RerunData

class Response:
    status_code=200
    def __init__(self,body):self.body=body
    def json(self):return self.body

REPLY={'status':'clarification','response_text':'Please provide the boarding stop.',
       'intent':'route_stop_sequence','operation':'LIST_ROUTE_STOPS',
       'slots':{'route_number':'281'},'data':{},'missing_slots':['station'],
       'clarification_reason':'missing_slot','candidate_entities':[],
       'candidate_intents':['route_stop_sequence']}

@pytest.mark.parametrize('query', ['List the bus 281 stop sequence.', 'बस २८१ के स्टॉप क्रम बताओ।',
    'bus 281 ke stop kram bataiye.', 'bus 281 stop sequence chahiye.'])
def test_completed_request_survives_source_panel_rerun(monkeypatch,query):
    calls=[]
    monkeypatch.setattr(requests,'get',lambda *a,**k:Response({'taxonomy':'T3'}))
    app=AppTest.from_file('app/streamlit_app.py').run()
    app.radio(key='transport_mode').set_value('bus').run()
    controls=app._tree.get_widget_states()
    for widget in controls.widgets:
        if widget.id==app.button(key='published_records').id:
            widget.trigger_value=True
    def post(url,json,timeout):
        calls.append(json)
        # Queue a real runtime rerun while the synchronous request is in flight.
        # Spinner teardown then reaches ScriptRunner's execution-control yield.
        runner=get_script_run_ctx()._enqueue.__self__
        runner.request_rerun(RerunData(widget_states=controls))
        return Response(REPLY)
    monkeypatch.setattr(requests,'post',post)
    app.chat_input[0].set_value(query).run(timeout=10)
    assert not app.exception
    assert [m['role'] for m in app.session_state['messages']]==['user','assistant']
    assert app.session_state['messages'][0]['text']==query
    assert app.session_state['messages'][1]['reply']==REPLY
    assert app.session_state['pending_query']==query
    assert app.session_state['selected_transport_mode']=='bus'
    assert calls==[{'query':query,'transport_mode':'bus'}]
    app.text_input[0].set_value(query+' revised').run()
    app.radio(key='ui_language').set_value('hi').run()
    assert app.text_input[0].value==query+' revised'
    assert len(app.session_state['messages'])==2 and len(calls)==1


def test_accepted_query_interrupted_before_post_resumes_once(monkeypatch):
    from contextlib import contextmanager
    import streamlit as st
    monkeypatch.setattr(requests,'get',lambda *a,**k:Response({'taxonomy':'T3'}))
    calls=[]
    monkeypatch.setattr(requests,'post',lambda url,json,timeout:(calls.append(json) or Response(REPLY)))
    app=AppTest.from_file('app/streamlit_app.py').run()
    app.radio(key='transport_mode').set_value('bus').run()
    controls=app._tree.get_widget_states()
    for widget in controls.widgets:
        if widget.id==app.button(key='published_records').id:
            widget.trigger_value=True
    original_spinner=st.spinner
    interrupted=False
    @contextmanager
    def spinner(*args,**kwargs):
        nonlocal interrupted
        if not interrupted:
            interrupted=True
            get_script_run_ctx()._enqueue.__self__.request_rerun(RerunData(widget_states=controls))
        with original_spinner(*args,**kwargs):
            yield
    monkeypatch.setattr(st,'spinner',spinner)
    query='List all bus 281 stops in order.'
    app.chat_input[0].set_value(query).run(timeout=10)
    assert not app.exception
    assert [m['role'] for m in app.session_state['messages']]==['user','assistant']
    assert calls==[{'query':query,'transport_mode':'bus'}]
    assert app.session_state['pending_query']==query


def test_inflight_mode_and_language_change_keeps_submission_snapshot(monkeypatch):
    monkeypatch.setattr(requests,'get',lambda *a,**k:Response({'taxonomy':'T3'}))
    app=AppTest.from_file('app/streamlit_app.py').run()
    app.radio(key='transport_mode').set_value('bus').run()
    app.radio(key='transport_mode').set_value('metro')
    app.radio(key='ui_language').set_value('hi')
    controls=app._tree.get_widget_states()
    app.radio(key='transport_mode').set_value('bus')
    app.radio(key='ui_language').set_value('en')
    calls=[]
    def post(url,json,timeout):
        calls.append(json)
        if len(calls)==1:
            get_script_run_ctx()._enqueue.__self__.request_rerun(RerunData(widget_states=controls))
        return Response(REPLY)
    monkeypatch.setattr(requests,'post',post)
    query='List the bus 281 stop sequence.'
    app.chat_input[0].set_value(query).run(timeout=10)
    assert not app.exception
    assert calls==[{'query':query,'transport_mode':'bus'}]
    assert len(app.session_state['messages'])==2
    assert app.session_state['messages'][0]['default_transport_mode']=='bus'
    assert app.session_state['selected_transport_mode']=='metro'
    assert app.radio(key='ui_language').value=='hi'
    # A deliberately repeated submission is a new turn, even with identical text.
    app.chat_input[0].set_value(query).run(timeout=10)
    assert len(calls)==2 and calls[1]=={'query':query,'transport_mode':'metro'}
    assert len(app.session_state['messages'])==4

@pytest.mark.parametrize('query',[
 'पूनमल्ली बस टर्मिनस पर, पहली और आखिरी बस का समय चाहिए।',
 'Poonamallee Bus Terminus par, pehli aur aakhiri bus ka time batao.',
])
def test_native_timetable_answer_survives_real_source_control_interrupt(monkeypatch,query):
    from dataclasses import asdict
    import json as wire_json
    from tests.helpers import FixedClassifier
    from src.nlp_v2.assistant import T3Assistant
    calls=[]
    monkeypatch.setattr(requests,'get',lambda *a,**k:Response({'taxonomy':'T3'}))
    app=AppTest.from_file('app/streamlit_app.py').run()
    app.radio(key='transport_mode').set_value('bus').run()
    controls=app._tree.get_widget_states()
    for widget in controls.widgets:
        if widget.id==app.button(key='published_records').id:widget.trigger_value=True
    def post(url,json,timeout):
        calls.append(json)
        # SQLite connections belong to the real ScriptRunner request thread.
        assistant=T3Assistant(classifier=FixedClassifier('first_and_last_service'))
        reply=assistant.process_query(json['query'],default_transport_mode=json['transport_mode'])
        get_script_run_ctx()._enqueue.__self__.request_rerun(RerunData(widget_states=controls))
        return Response(wire_json.loads(wire_json.dumps(asdict(reply))))
    monkeypatch.setattr(requests,'post',post)
    app.chat_input[0].set_value(query).run(timeout=10)
    assert not app.exception and len(calls)==1
    assert calls==[{'query':query,'transport_mode':'bus'}]
    messages=app.session_state['messages']
    assert [m['role'] for m in messages]==['user','assistant']
    reply=messages[1]['reply']
    assert reply['status']=='ok' and reply['slots']['station']=='BUS_5821', reply
    assert reply['data']['first_departure']=='00:18:00' and reply['data']['last_departure']=='25:16:00'
    app.radio(key='ui_language').set_value('hi').run()
    assert app.session_state['messages'][1]['reply']==reply and len(calls)==1
