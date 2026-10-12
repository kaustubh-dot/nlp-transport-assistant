"""Single-process Hindi/Hinglish academic NLP demonstration."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

import streamlit as st
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.hindi_project.assistant import HindiProjectAssistant  # noqa: E402
from src.hindi_project.model import BaselineIntentClassifier, ProjectIntentClassifier, LABELS_HI  # noqa: E402
from app.project_ui import e, masthead, sidebar_brand, entity_ledger, record_overview, source_links  # noqa: E402

st.set_page_config(page_title='Chennai Transit · Hindi / Hinglish NLP', page_icon='🚆', layout='wide', initial_sidebar_state='auto')
st.markdown('<style>' + (ROOT / 'app/project_theme.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)
language = st.session_state.get('project_language', 'hi')


def text(hi, hinglish):
    return hi if language == 'hi' else hinglish


with st.container(key='project_header'):
    title_col, language_col = st.columns([3, 1])
    with title_col:
        st.markdown(masthead(language == 'hi'), unsafe_allow_html=True)
    with language_col:
        language = st.radio('भाषा / Bhasha', ['hi', 'hinglish'],
                            format_func=lambda code: 'हिंदी' if code == 'hi' else 'Hinglish',
                            horizontal=True, key='project_language')
        st.caption(text('उत्तर की भाषा चुनें।', 'Jawab ki bhasha chunein.'))

EXAMPLES = {
    'metro': ('मेट्रो की उपलब्धता', 'Metro availability', 'चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या?', 'Chennai Central se Airport ke liye metro hai kya?'),
    'bus': ('बस का कनेक्शन', 'Bus connection', 'तांबरम से गिंडी के लिए बस उपलब्ध है क्या?', 'Tambaram se Guindy ke liye bus available hai kya?'),
    'route': ('मार्ग की जानकारी', 'Route information', 'गिंडी से सेंट्रल कैसे जाएँ?', 'Guindy se Central kaise jayein?'),
    'lift': ('मेट्रो में लिफ्ट', 'Metro lift', 'सेंट्रल मेट्रो में लिफ्ट है?', 'Central metro mein lift hai?'),
    'delay': ('ट्रेन की देरी', 'Train delay', 'मेरी ट्रेन बहुत लेट है।', 'Meri train bahut late hai.'),
    'complaint': ('रेलवे शिकायत', 'Railway complaint', 'ट्रेन का शौचालय बहुत गंदा है।', 'Train ka toilet ganda hai.'),
    'station': ('पास का बस स्टॉप', 'Nearby bus stop', 'एग्मोर रेलवे स्टेशन के पास बस स्टॉप कौन सा है?', 'Egmore railway station ke paas bus stop kaunsa h?'),
    'ticket': ('टिकट की जानकारी', 'Ticket information', 'सेंट्रल से एयरपोर्ट का मेट्रो टिकट कहाँ खरीदूँ?', 'Central se Airport ka metro ticket kahan kharidu?'),
    'other': ('परिवहन से बाहर का प्रश्न', 'Non-transport question', 'आज क्रिकेट का स्कोर क्या है?', 'Aaj cricket ka score kya h?'),
    'timing': ('पहली ट्रेन का समय', 'First train timing', 'सुबह सबसे पहली ट्रेन गिंडी से सेंट्रल कब है?', 'Subah sabse pehle train guindy se chennai central kab hai?'),
    'unknown': ('अन्य रेलवे स्टेशन', 'Another railway station', 'चेन्नई सेंट्रल से माम्बलम स्टेशन कैसे जाऊँ?', 'Chennai Central se Mambalam station kaise jau?'),
}


def clear_result():
    for key in ('project_result', 'project_result_model', 'project_result_context', 'project_comparison'):
        st.session_state.pop(key, None)


def new_question():
    clear_result()
    st.session_state['project_query'] = ''
    st.session_state['project_example'] = None


def use_example():
    selected = st.session_state.get('project_example')
    if selected:
        st.session_state['project_query'] = EXAMPLES[selected][2 if st.session_state['project_language'] == 'hi' else 3]


def use_quick_example(key):
    st.session_state['project_example'] = key
    use_example()


def recall_question(question):
    st.session_state['project_query'] = question
    st.session_state['project_example'] = None


@st.cache_resource
def load_assistant(model_name):
    if model_name == 'TF-IDF baseline':
        classifier = BaselineIntentClassifier()
    else:
        classifier = ProjectIntentClassifier()
    return HindiProjectAssistant(classifier=classifier)


@st.cache_data
def stop_names():
    path = ROOT / 'data/canonical/transit/canonical_transport.db'
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as connection:
        return dict(connection.execute('SELECT stop_id, canonical_name FROM transport_stops'))


catalog = json.loads((ROOT / 'data/project/chennai_case_study.json').read_text(encoding='utf-8'))
origins = [row for row in catalog['locations'] if row.get('origin')]
with st.sidebar:
    st.markdown(sidebar_brand(), unsafe_allow_html=True)
    st.subheader(text('डेमो सेटिंग', 'Demo settings'))
    model_name = st.selectbox('Intent model', ['TF-IDF baseline', 'MuRIL (partial fine-tuning)'], key='project_model')
    context = st.selectbox('Station context / स्टेशन संदर्भ', [''] + [row['id'] for row in origins],
                           format_func=lambda key: '—' if not key else next(row['name_en'] for row in origins if row['id'] == key),
                           key='project_station')
    st.caption(text('केवल “इस स्टेशन” या “यहाँ” जैसे प्रश्नों के लिए।', 'Sirf “is station” ya “yahan” jaise sawaalon ke liye.'))
    with st.expander(text('डेटा में क्या है?', 'Data mein kya hai?')):
        st.write(text('मूल डेटाबेस में रेलवे, मेट्रो, MRTS, बस स्टॉप और landmarks के नाम खोजे जाते हैं।',
                      'Original database mein railway, metro, MRTS, bus stop aur landmark names search hote hain.'))
        st.caption(text('नाम पहचान और रूट/समय की कवरेज अलग हैं। स्रोत अधूरे हो सकते हैं। लाइव स्थिति और बुकिंग उपलब्ध नहीं।',
                        'Name recognition aur route/timetable coverage alag hain. Sources adhure ho sakte hain. Live status aur booking available nahi.'))

with st.form('project_query_form'):
    query = st.text_area('प्रश्न / Sawal', height=104,
                         placeholder='चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या? / Central se Airport ke liye metro hai kya?', key='project_query')
    submit_col, reset_col = st.columns([2, 1])
    with submit_col:
        submitted = st.form_submit_button(text('प्रश्न समझें', 'Sawal samjhein'), type='primary', use_container_width=True)
    with reset_col:
        st.form_submit_button(text('नया प्रश्न', 'Naya sawal'), on_click=new_question, use_container_width=True)

with st.container(key='project_quick_examples'):
    quick_cols = st.columns(3)
    for column, key in zip(quick_cols, ('route', 'station', 'lift')):
        with column:
            st.button(text(EXAMPLES[key][0], EXAMPLES[key][1]) + ' ↗', key='project_quick_' + key,
                      on_click=use_quick_example, args=(key,), use_container_width=True)
st.selectbox(text('और डेमो उदाहरण', 'Aur demo examples'), list(EXAMPLES), index=None,
             format_func=lambda key: EXAMPLES[key][0 if language == 'hi' else 1], key='project_example',
             placeholder=text('उदाहरण चुनें — फिर प्रश्न भेजें', 'Example chunein — phir sawal bhejein'), on_change=use_example)

if submitted:
    if not query.strip():
        clear_result()
        st.warning(text('कृपया प्रश्न लिखें।', 'Please sawal likhein.'))
    else:
        try:
            with st.spinner(text('NLP मॉडल प्रश्न समझ रहा है…', 'NLP model sawal samajh raha hai…')):
                result = load_assistant(model_name).process_query(query, context or None)
            st.session_state['project_result'] = result
            st.session_state['project_result_model'] = model_name
            st.session_state['project_result_context'] = context or None
            st.session_state.pop('project_comparison', None)
            recent = st.session_state.get('project_recent_queries', [])
            st.session_state['project_recent_queries'] = [query] + [item for item in recent if item != query][:4]
        except (OSError, ValueError, RuntimeError, ImportError) as error:
            clear_result()
            st.error(text('प्रोजेक्ट मॉडल तैयार नहीं है: ', 'Project model taiyar nahi hai: ') + str(error))
            st.code('python -m pip install -r requirements-neural.txt\npython -m scripts.prepare_models', language='bash')

if 'project_result' in st.session_state:
    result = st.session_state['project_result']
    if query != result['query'] or model_name != st.session_state['project_result_model'] or (context or None) != st.session_state.get('project_result_context'):
        st.info(text('यह पिछला भेजा हुआ प्रश्न है। नए प्रश्न या बदली हुई सेटिंग के लिए “प्रश्न समझें” दबाएँ।',
                     'Yeh pehle bheja hua sawal hai. Naye sawal ya badli settings ke liye “Sawal samjhein” dabayein.'))
    statuses = {
        'information': ('कैटलॉग जानकारी / मार्गदर्शन', 'Catalog information / guidance'),
        'unavailable': ('माँगी गई जानकारी उपलब्ध नहीं', 'Maangi gayi information available nahi'),
        'clarification': ('स्थान या प्रश्न स्पष्ट करें', 'Location ya sawal clear karein'),
        'out_of_scope': ('परिवहन से बाहर का प्रश्न', 'Transport se bahar ka sawal'),
    }
    names = stop_names()
    names.update(result.get('entity_labels', {}))
    names.update({row['id']: row['name_hi'] if language == 'hi' else row['name_en'] for row in catalog['locations']})
    slots = {key: names.get(value, value) if isinstance(value, str) else
             [names.get(item, item) for item in value] if isinstance(value, list) else value
             for key, value in result['entities'].items()}

    with st.container(key='project_result_columns'):
        answer_col, nlp_col = st.columns([2, 1], gap='large')
        with answer_col, st.container(key='project_answer'):
            st.caption(text(*statuses[result['status']]))
            st.subheader(text('हिंदी उत्तर', 'Hinglish jawab'))
            st.caption(text('प्रश्न: ', 'Sawal: ') + result['query'])
            overview = record_overview(result, names, language == 'hi')
            if overview:
                st.markdown(overview, unsafe_allow_html=True)
            st.write(result['response_hi'] if language == 'hi' else result['response_hinglish'])
            if result.get('location_ambiguities') and result['status'] == 'clarification':
                st.caption(text('मिलते-जुलते नाम / स्टेशन प्रकार:', 'Matching names / station types:'))
                rows = [{'Name / नाम': row['canonical_name'], 'Mode / माध्यम': row['mode'] or row['kind']}
                        for ambiguity in result['location_ambiguities'] for row in ambiguity['candidates']]
                st.table(pd.DataFrame(rows).drop_duplicates().set_index('Name / नाम'))
            st.markdown(source_links(result['sources']), unsafe_allow_html=True)
        with nlp_col, st.container(key='project_understanding'):
            st.subheader(text('क्या समझा गया', 'Kya samjha gaya'))
            intent_label = LABELS_HI[result['intent']] if language == 'hi' else result['intent'].replace('_', ' ')
            st.markdown(f'<div class="transit-intent">{e(intent_label)}<br>{e(result["intent"])}</div>', unsafe_allow_html=True)
            st.caption('Extracted entities / slots')
            if slots:
                st.markdown(entity_ledger(slots, language == 'hi'), unsafe_allow_html=True)
            else:
                st.caption(text('स्थान या स्लॉट पहचाने नहीं गए। पूरा स्थान नाम लिखें।',
                                'Locations ya slots pehchane nahi gaye. Poora place name likhein.'))
            st.caption(st.session_state['project_result_model'])
            st.caption(f"Model score: {result['model_score']:.3f} — " + text('यह calibrated accuracy नहीं है।', 'Yeh calibrated accuracy nahi hai.'))

    with st.expander(text('स्लॉट और कैटलॉग प्रमाण', 'Slots aur catalog evidence')):
        st.caption('Source records / स्रोत रिकॉर्ड')
        st.write(result['sources'])
        st.caption('Raw NLP slots')
        st.json(result['entities'])
        if result.get('location_matches'):
            st.caption('Canonical name matches / डेटाबेस में नाम')
            st.json(result['location_matches'])
            st.caption('Resolved canonical IDs')
            st.json(result['canonical_slots'])
        if result['records']:
            st.caption('Catalog lookup / कैटलॉग')
            st.json(result['records'])

    with st.expander(text('इस प्रश्न पर दोनों मॉडल की तुलना', 'Is sawal par dono models compare karein'),
                     expanded=bool(st.session_state.get('project_comparison') or st.session_state.get('project_compare'))):
        st.caption(text('तुलना ऊपर दिखाए गए भेजे हुए प्रश्न और उसी स्टेशन संदर्भ पर होती है।',
                        'Comparison upar dikhaye gaye submitted sawal aur usi station context par hota hai.'))
        if st.button(text('दोनों मॉडल चलाएँ', 'Dono models chalayein'), key='project_compare'):
            try:
                with st.spinner(text('दोनों मॉडल तुलना के लिए चल रहे हैं…', 'Dono models comparison ke liye chal rahe hain…')):
                    compared = []
                    for name in ('TF-IDF baseline', 'MuRIL (partial fine-tuning)'):
                        other = load_assistant(name).process_query(result['query'], st.session_state.get('project_result_context'))
                        compared.append({'Model': name, 'Intent': other['intent'], 'Score': round(other['model_score'], 3), 'Status': other['status']})
                    st.session_state['project_comparison'] = compared
            except (OSError, ValueError, RuntimeError, ImportError) as error:
                st.session_state.pop('project_comparison', None)
                st.warning(text('मॉडल तुलना अभी उपलब्ध नहीं: ', 'Model comparison abhi available nahi: ') + str(error))
        if 'project_comparison' in st.session_state:
            st.table(pd.DataFrame(st.session_state['project_comparison']).set_index('Model'))
            st.caption(text('दोनों scores कच्चे model outputs हैं; इन्हें accuracy या सीधे तुलनीय confidence न मानें।',
                            'Dono scores raw model outputs hain; inhe accuracy ya seedha comparable confidence na maanein.'))

else:
    heading = text('एक सवाल से शुरू करें।', 'Ek sawal se shuru karein.')
    note = text('ऊपर का उदाहरण चुनें या अपना प्रश्न लिखें। नाम, intent और स्रोत से मिला उत्तर साथ दिखेंगे।',
                'Upar ka example chunein ya apna sawal likhein. Names, intent aur sources se mila jawab saath dikhega.')
    st.markdown(f'<section class="transit-empty"><h2>{heading}</h2><p>{note}</p>'
                '<div class="transit-process"><span>QUESTION</span><span>→ INTENT</span><span>→ ENTITIES</span>'
                '<span>→ LOOKUP</span><span>→ ANSWER</span></div></section>', unsafe_allow_html=True)

with st.sidebar:
    st.divider()
    st.subheader(text('हाल के प्रश्न', 'Haal ke sawal'))
    recent = st.session_state.get('project_recent_queries', [])
    if recent:
        for index, question in enumerate(recent):
            st.button(question, key=f'project_recent_{index}', on_click=recall_question,
                      args=(question,), use_container_width=True)
        st.caption(text('चुनने पर प्रश्न भरता है; भेजने के बाद मॉडल चलता है। इस सत्र तक सीमित।',
                        'Chunne par sawal bharta hai; bhejne ke baad model chalta hai. Sirf is session mein.'))
    else:
        st.caption(text('भेजे गए प्रश्न यहाँ मिलेंगे।', 'Bheje gaye sawal yahan milenge.'))

with st.expander(text('वैकल्पिक: हिंदी–तमिल संचार वाक्य', 'Optional: Hindi–Tamil communication phrases')):
    phrases = json.loads((ROOT / 'data/project/communication_phrases.json').read_text(encoding='utf-8'))
    selected = st.selectbox('Communication phrase / संचार वाक्य', range(len(phrases)),
                            format_func=lambda index: phrases[index]['hindi'] if language == 'hi' else phrases[index]['hinglish'],
                            key='communication_phrase')
    st.write('தமிழ்:', phrases[selected]['tamil'])
    st.caption(text('पाँच तय वाक्यों की phrasebook; सामान्य translation model नहीं। तमिल भाषी से समीक्षा आवश्यक है।',
                    'Paanch fixed phrases ki phrasebook; general translation model nahi. Tamil speaker se review zaroori hai.'))

with st.expander(text('NLP मूल्यांकन', 'NLP evaluation')):
    metrics_path = ROOT / 'models/hindi_project_metrics.json'
    if metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
        st.table([{'Model': name, 'Language': code, 'Test rows': values['count'],
                   'Accuracy': round(values['accuracy'], 3), 'Macro F1': round(values['macro_f1'], 3)}
                  for name, values_by_split in metrics['models'].items()
                  for code, values in values_by_split['by_language']['test'].items()])
        st.caption(text('Synthetic template-family test set; वास्तविक यात्रियों की accuracy का दावा नहीं।',
                        'Synthetic template-family test set; real passengers ki accuracy ka daava nahi.'))
    else:
        st.info(text('पहले training/evaluation script चलाएँ।', 'Pehle training/evaluation script chalayein.'))

st.markdown('<footer class="transit-footer">CHENNAI CASE STUDY · 9 INTENTS · STATIC SOURCE DATA<br>'
            + text('NLP परियोजना · लाइव स्थिति या टिकट बुकिंग उपलब्ध नहीं।',
                   'NLP project · live status aur ticket booking available nahi.') + '</footer>', unsafe_allow_html=True)
