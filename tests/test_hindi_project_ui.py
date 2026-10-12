"""Academic UI behavior without model execution inside Streamlit tests."""
import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def model_calls():
    return []


@pytest.fixture
def ui(monkeypatch, model_calls):
    import src.hindi_project.model as model

    class Baseline:
        def predict(self, query):
            model_calls.append(('baseline', query))
            return ('train_status' if 'लेट' in query else 'service_availability'), 0.8

    class Neural:
        def predict(self, query):
            model_calls.append(('muril', query))
            return 'route_query', 0.65

    monkeypatch.setattr(model, 'BaselineIntentClassifier', Baseline)
    monkeypatch.setattr(model, 'ProjectIntentClassifier', Neural)
    import streamlit as st
    st.cache_resource.clear()
    app = AppTest.from_file('app/streamlit_app.py').run(timeout=10)
    yield app
    st.cache_resource.clear()


def test_project_demo_shows_intent_entities_and_hindi_answer(ui):
    ui.text_area[0].set_value('चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या?')
    ui.button[0].click().run(timeout=10)
    assert not ui.exception
    assert ui.session_state['project_result']['intent'] == 'service_availability'
    assert ui.session_state['project_result']['entities']['origin'] == 'central'
    content = ' '.join(item.value for item in ui.markdown)
    assert 'service_availability' in content and 'प्रकाशित कनेक्टिविटी' in content
    assert any('Extracted entities' in item.value for item in ui.caption)
    assert any('चेन्नई सेंट्रल' in item.value for item in ui.markdown)


def test_empty_question_does_not_load_or_run_a_model(ui):
    ui.button[0].click().run(timeout=10)
    assert not ui.exception
    assert 'project_result' not in ui.session_state
    assert any('प्रश्न लिखें' in item.value for item in ui.warning)


def test_delay_demo_stays_clear_about_live_data(ui):
    ui.text_area[0].set_value('मेरी ट्रेन बहुत लेट है।')
    ui.button[0].click().run(timeout=10)
    assert not ui.exception
    assert ui.session_state['project_result']['intent'] == 'train_status'
    assert any('लाइव ट्रेन डेटा नहीं' in item.value for item in ui.markdown)


def test_phrasebook_selects_actual_tamil_pair_without_changing_query(ui):
    ui.text_area[0].set_value('मेरी ट्रेन बहुत लेट है।')
    ui.button[0].click().run(timeout=10)
    original = ui.session_state['project_result']
    ui.selectbox(key='communication_phrase').set_value(1).run(timeout=10)
    assert not ui.exception
    assert ui.session_state['project_result'] == original
    assert any('ரயில் நிலையம்' in item.value for item in ui.markdown)


def test_switching_to_hinglish_renders_saved_response_without_rewriting_query(ui):
    question = 'Chennai Central se Airport ke liye metro hai kya?'
    ui.text_area[0].set_value(question)
    ui.button[0].click().run(timeout=10)
    original = dict(ui.session_state['project_result'])
    ui.radio(key='project_language').set_value('hinglish').run(timeout=10)
    assert not ui.exception
    assert ui.session_state['project_result'] == original
    assert ui.session_state['project_result']['query'] == question
    assert any('published connectivity' in item.value for item in ui.markdown)
    assert any('Hinglish jawab' in item.value for item in ui.subheader)


def test_language_change_preserves_unsubmitted_input(ui):
    question = 'Central se Airport kaise jaun?'
    ui.text_area[0].set_value(question).run(timeout=10)
    ui.radio(key='project_language').set_value('hinglish').run(timeout=10)
    assert not ui.exception
    assert ui.text_area[0].value == question
    assert 'project_result' not in ui.session_state


def test_example_selection_prefills_without_inference_and_language_switch_preserves_it(ui, model_calls):
    ui.selectbox(key='project_example').set_value('metro').run(timeout=10)
    question = ui.text_area[0].value
    assert question == 'चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या?'
    assert not model_calls and 'project_result' not in ui.session_state
    ui.radio(key='project_language').set_value('hinglish').run(timeout=10)
    assert ui.text_area[0].value == question
    ui.selectbox(key='project_example').set_value('bus').run(timeout=10)
    assert ui.text_area[0].value == 'Tambaram se Guindy ke liye bus available hai kya?'
    assert not model_calls


def test_new_question_clears_result_and_draft_but_preserves_language_and_model(ui):
    ui.radio(key='project_language').set_value('hinglish').run(timeout=10)
    ui.selectbox(key='project_example').set_value('metro').run(timeout=10)
    ui.button[0].click().run(timeout=10)
    assert 'project_result' in ui.session_state
    ui.button[1].click().run(timeout=10)
    assert not ui.exception
    assert ui.text_area[0].value == '' and ui.selectbox(key='project_example').value is None
    assert 'project_result' not in ui.session_state and 'project_comparison' not in ui.session_state
    assert ui.radio(key='project_language').value == 'hinglish'
    assert ui.selectbox(key='project_model').value == 'TF-IDF baseline'


def test_changed_model_or_draft_marks_old_result_without_running_it_again(ui, model_calls):
    ui.selectbox(key='project_example').set_value('metro').run(timeout=10)
    ui.button[0].click().run(timeout=10)
    original = dict(ui.session_state['project_result'])
    ui.selectbox(key='project_model').set_value('MuRIL (partial fine-tuning)').run(timeout=10)
    ui.selectbox(key='project_example').set_value('bus').run(timeout=10)
    assert ui.session_state['project_result'] == original
    assert ui.session_state['project_result_model'] == 'TF-IDF baseline'
    assert len(model_calls) == 1
    assert any('पिछला भेजा हुआ प्रश्न' in item.value for item in ui.info)


def test_comparison_uses_submitted_question_and_does_not_replace_result_or_draft(ui, model_calls):
    ui.selectbox(key='project_example').set_value('metro').run(timeout=10)
    ui.button[0].click().run(timeout=10)
    original = dict(ui.session_state['project_result'])
    ui.selectbox(key='project_example').set_value('bus').run(timeout=10)
    draft = ui.text_area[0].value
    ui.button(key='project_compare').click().run(timeout=10)
    assert not ui.exception
    assert model_calls[-2:] == [('baseline', original['query']), ('muril', original['query'])]
    assert ui.session_state['project_result'] == original and ui.text_area[0].value == draft
    rows = ui.session_state['project_comparison']
    assert [row['Intent'] for row in rows] == ['service_availability', 'route_query']
    assert rows[0]['Score'] != rows[1]['Score']


def test_missing_neural_asset_during_comparison_keeps_baseline_result(ui, monkeypatch):
    import src.hindi_project.model as model
    class Missing:
        def __init__(self):
            raise FileNotFoundError('Demo neural asset missing')
    ui.selectbox(key='project_example').set_value('metro').run(timeout=10)
    ui.button[0].click().run(timeout=10)
    original = dict(ui.session_state['project_result'])
    monkeypatch.setattr(model, 'ProjectIntentClassifier', Missing)
    ui.button(key='project_compare').click().run(timeout=10)
    assert not ui.exception and ui.session_state['project_result'] == original
    assert 'project_comparison' not in ui.session_state
    assert any('Demo neural asset missing' in item.value for item in ui.warning)


def test_empty_submission_clears_previous_result_instead_of_showing_stale_answer(ui):
    ui.selectbox(key='project_example').set_value('metro').run(timeout=10)
    ui.button[0].click().run(timeout=10)
    ui.text_area[0].set_value('')
    ui.button[0].click().run(timeout=10)
    assert not ui.exception and 'project_result' not in ui.session_state
    assert any('प्रश्न लिखें' in item.value for item in ui.warning)


def test_quick_action_prefills_only_and_keeps_language_and_model(ui, model_calls):
    ui.radio(key='project_language').set_value('hinglish').run(timeout=10)
    ui.button(key='project_quick_station').click().run(timeout=10)
    assert not ui.exception
    assert ui.text_area[0].value == 'Egmore railway station ke paas bus stop kaunsa h?'
    assert ui.selectbox(key='project_example').value == 'station'
    assert not model_calls and 'project_result' not in ui.session_state
    assert ui.radio(key='project_language').value == 'hinglish'
    assert ui.selectbox(key='project_model').value == 'TF-IDF baseline'


def test_recent_question_recall_keeps_saved_answer_and_waits_for_submission(ui, model_calls):
    ui.selectbox(key='project_example').set_value('metro').run(timeout=10)
    ui.button[0].click().run(timeout=10)
    original = dict(ui.session_state['project_result'])
    ui.selectbox(key='project_example').set_value('bus').run(timeout=10)
    ui.button(key='project_recent_0').click().run(timeout=10)
    assert not ui.exception
    assert ui.text_area[0].value == original['query']
    assert ui.session_state['project_result'] == original
    assert len(model_calls) == 1
    ui.button[0].click().run(timeout=10)
    assert ui.session_state['project_recent_queries'] == [original['query']]
    ui.button[1].click().run(timeout=10)
    assert ui.session_state['project_recent_queries'] == [original['query']]


def test_presentation_helpers_escape_input_and_do_not_invent_service_results():
    from app.project_ui import entity_ledger, record_overview, source_links
    html = entity_ledger({'station': '<script>alert(1)</script>'}, False)
    assert '<script>' not in html and '&lt;script&gt;' in html
    result = {'status': 'unavailable', 'entities': {'origin': 'a', 'destination': 'b'},
              'records': [{'route_name': 'unused'}]}
    assert record_overview(result, {'a': 'A', 'b': 'B'}, False) == ''
    html = source_links(['data/canonical/transit/canonical_transport.db'])
    assert 'local data snapshot' in html and '<a ' not in html


def test_nearby_stop_display_deduplicates_by_name_and_mode_and_labels_distance():
    from app.project_ui import record_overview
    result = {'status': 'information', 'records': [
        {'type': 'canonical_nearby_bus', 'name': 'Stop A', 'mode': 'bus', 'distance_m': 210},
        {'type': 'canonical_nearby_bus', 'name': 'Stop A', 'mode': 'bus', 'distance_m': 110},
        {'type': 'canonical_nearby_bus', 'name': 'Stop B', 'mode': 'bus', 'distance_m': 150},
    ]}
    html = record_overview(result, {}, False)
    assert html.count('Stop A') == 1 and '110 m' in html and '210 m' not in html
    assert html.index('Stop A') < html.index('Stop B')
    assert 'walking route nahi' in html
