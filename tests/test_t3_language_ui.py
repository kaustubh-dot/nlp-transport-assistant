"""Language selection must localize presentation without changing query semantics."""

import pytest


class Response:
    status_code = 200

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


@pytest.fixture
def ui(monkeypatch):
    import requests
    from streamlit.testing.v1 import AppTest

    calls = []
    reply = {
        'status': 'ok', 'intent': 'fare_calculation', 'operation': 'CALCULATE_FARE',
        'response_text': 'Published fare (Deluxe Services): INR 17 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.',
        'slots': {'stage_number': 4, 'service_type': 'Deluxe Services'},
        'data': {'amount': 17, 'currency': 'INR', 'service_type': 'Deluxe Services',
                 'effective_date': '2018-01-29', 'source': 'MTC_OFFICIAL', 'provisional': True},
        'missing_slots': [], 'candidate_entities': [], 'candidate_intents': ['fare_calculation'],
        'clarification_reason': None, 'outcome_reason': 'answered',
    }
    monkeypatch.setattr(requests, 'get', lambda *a, **k: Response({'taxonomy': 'T3', 'status': 'ok'}))

    def post(url, json, timeout):
        calls.append(dict(json))
        return Response(reply.copy())

    monkeypatch.setattr(requests, 'post', post)
    return AppTest.from_file('app/streamlit_app.py').run(timeout=10), calls, reply


def test_language_switch_preserves_history_and_original_question(ui):
    app, calls, _ = ui
    query = 'बस stage ४ का deluxe किराया कितना है?'
    app.chat_input[0].set_value(query).run(timeout=10)
    for language in ('hi', 'hinglish', 'en'):
        app.radio[0].set_value(language).run(timeout=10)
        assert not app.exception
        assert app.session_state.messages[0]['text'] == query
        assert len(app.session_state.messages) == 2
        assert app.metric[0].value == 'INR 17'
    assert calls == [{'query': query}]


def test_mode_controls_send_default_without_rewriting_question(ui):
    app, calls, _ = ui
    question = 'guindy se central kaise jau'
    app.radio[1].set_value('metro').run(timeout=10)
    app.chat_input[0].set_value(question).run(timeout=10)
    assert not app.exception
    assert calls == [{'query': question, 'transport_mode': 'metro'}]
    assert app.session_state.messages[0]['text'] == question
    assert app.session_state.messages[0]['default_transport_mode'] == 'metro'
    for language in ('hi', 'hinglish', 'en'):
        app.radio[0].set_value(language).run(timeout=10)
        assert not app.exception
        assert app.radio[1].value == 'metro'
        assert len(app.session_state.messages) == 2
    assert len(calls) == 1
    app.radio[1].set_value('auto').run(timeout=10)
    app.chat_input[0].set_value('bus stage 4 deluxe fare').run(timeout=10)
    assert calls[-1] == {'query': 'bus stage 4 deluxe fare'}


def test_published_records_control_is_interactive_without_api_query(ui):
    app, calls, _ = ui
    button = next(item for item in app.button if item.key == 'published_records')
    button.click().run(timeout=10)
    assert not app.exception
    assert app.session_state.records_open is True
    assert any('Source coverage' in item.value for item in app.subheader)
    assert calls == []
    next(item for item in app.button if item.key == 'published_records').click().run(timeout=10)
    assert app.session_state.records_open is False
    assert calls == []


def test_language_switch_keeps_composer_widget_identity(ui):
    app, calls, _ = ui
    composer_id = app.chat_input[0].id
    for language in ('hi', 'hinglish', 'en'):
        app.radio[0].set_value(language).run(timeout=10)
        assert not app.exception
        assert app.chat_input[0].id == composer_id
    assert calls == []


@pytest.mark.parametrize('language,heading,source_label', [
    ('hi', 'प्रकाशित किराया', 'स्रोत'),
    ('hinglish', 'Prakashit kiraya', 'Source'),
])
def test_selected_language_localizes_fare_and_retains_source_date_caveat(ui, language, heading, source_label):
    app, _, _ = ui
    app.radio[0].set_value(language).run(timeout=10)
    app.chat_input[0].set_value('stage 4 deluxe fare?').run(timeout=10)
    assert not app.exception
    assert app.metric[0].label == heading
    assert app.metric[0].value == 'INR 17'
    captions = ' '.join(item.value for item in app.caption)
    assert '2018-01-29' in captions and 'MTC_OFFICIAL' in captions and source_label in captions
    assert ('पुष्टि' if language == 'hi' else 'confirm') in captions


@pytest.mark.parametrize('language,expected', [('hi', 'समय'), ('hinglish', 'samay')])
def test_clarification_and_revision_remain_usable_in_selected_language(ui, language, expected):
    app, calls, reply = ui
    reply.update(status='clarification', operation=None, data={}, intent='scheduled_departure',
                 response_text='Please clarify the time or day you mean.',
                 clarification_reason='temporal_ambiguity', outcome_reason='temporal_ambiguity')
    question = 'Poonamallee Bus Terminus se 8 baje bus kab hai?'
    app.chat_input[0].set_value(question).run(timeout=10)
    app.radio[0].set_value(language).run(timeout=10)
    assert not app.exception
    assert any(expected in item.value for item in app.info)
    assert app.text_input[0].value == question
    assert calls == [{'query': question}]
    assert not app.metric


def test_unmapped_response_is_preserved_rather_than_invented(ui):
    app, _, reply = ui
    reply.update(status='unavailable', operation=None, data={},
                 response_text='Unfamiliar source says service only on 2027-03-19.',
                 outcome_reason='unsupported_source')
    app.radio[0].set_value('hi').run(timeout=10)
    app.chat_input[0].set_value('bus?').run(timeout=10)
    assert not app.exception
    assert any('Unfamiliar source says service only on 2027-03-19.' in item.value for item in app.warning)
    assert not app.metric


def test_switching_language_keeps_unsubmitted_revision_draft(ui):
    app, calls, reply = ui
    reply.update(status='clarification', operation=None, data={},
                 response_text='Please clarify which stop or location you mean.',
                 clarification_reason='entity_ambiguity', outcome_reason='entity_ambiguity')
    app.chat_input[0].set_value('guindy se central kaise jau').run(timeout=10)
    revision_id = app.text_input[0].id
    draft = 'Guindy Metro se Central Metro kaise jau?'
    app.text_input[0].set_value(draft).run(timeout=10)
    app.radio[0].set_value('hi').run(timeout=10)
    assert not app.exception
    assert app.text_input[0].id == revision_id
    assert app.text_input[0].value == draft
    assert calls == [{'query': 'guindy se central kaise jau'}]
    next(item for item in app.button if (item.key or '').startswith('FormSubmitter:revise_question-')).click().run(timeout=10)
    assert not app.exception
    assert calls[-1] == {'query': draft}
    assert len(app.session_state.messages) == 4


@pytest.mark.parametrize('next_question', ['guindy se central kaise jau', 'Central se airport kaise jau?'])
def test_new_clarification_resets_the_old_draft(ui, next_question):
    app, calls, reply = ui
    reply.update(status='clarification', operation=None, data={},
                 response_text='Please clarify which stop or location you mean.',
                 clarification_reason='entity_ambiguity', outcome_reason='entity_ambiguity')
    app.chat_input[0].set_value('guindy se central kaise jau').run(timeout=10)
    previous_id = app.text_input[0].id
    app.text_input[0].set_value('An unsent revision of the previous question').run(timeout=10)
    app.chat_input[0].set_value(next_question).run(timeout=10)
    assert not app.exception
    # AppTest 1.44 retains the previous form node after the app's explicit rerun.
    # The last input belongs to the new turn, as confirmed by the live browser.
    assert app.text_input[-1].value == next_question
    assert app.text_input[-1].id != previous_id
    assert calls[-1] == {'query': next_question}
