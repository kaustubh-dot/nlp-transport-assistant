"""Small academic scope, semantic lookups and truthful evaluation tests."""
import csv
import json
import sqlite3
from pathlib import Path

import pytest

from src.hindi_project.assistant import CATALOG, HindiProjectAssistant, extract_entities
from src.hindi_project.model import LABELS, ROOT


class Classifier:
    def __init__(self, intent):
        self.intent = intent

    def predict(self, query):
        return self.intent, 0.75


@pytest.mark.parametrize('query', [
    'चेन्नई सेंट्रल से एयरपोर्ट जाने के लिए मेट्रो उपलब्ध है क्या?',
    'एयरपोर्ट के लिए चेन्नई सेंट्रल से मेट्रो है क्या?',
    'चेन्नई सेन्ट्रल से हवाई अड्डा मेट्रो द्वारा जाना है।',
])
def test_origin_destination_roles_survive_reordered_hindi(query):
    catalog = json.loads(CATALOG.read_text())
    result = extract_entities(query, catalog)
    assert result['origin'] == 'central'
    assert result['destination'] == 'airport'
    assert result['transport_mode'] == 'metro'


def test_explicit_context_is_used_only_for_deictic_reference():
    catalog = json.loads(CATALOG.read_text())
    assert extract_entities('इस स्टेशन से बस मिलती है?', catalog, 'tambaram')['origin'] == 'tambaram'
    assert 'origin' not in extract_entities('बस मिलती है?', catalog, 'tambaram')
    assert extract_entities('एग्मोर से बस मिलती है?', catalog, 'tambaram')['origin'] == 'egmore'


def test_published_connectivity_has_source_and_does_not_claim_live_status():
    assistant = HindiProjectAssistant(Classifier('service_availability'))
    result = assistant.process_query('चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या?')
    assert result['status'] == 'information'
    assert result['records'][0]['mode'] == 'metro'
    assert result['sources'][0].startswith('https://chennaimetrorail.org/')
    assert 'प्रकाशित' in result['response_hi'] and 'लाइव' in result['response_hi']


@pytest.mark.parametrize('question', ['अवडी से एयरपोर्ट के लिए बस है क्या?',
                                     'चेन्नई सेंट्रल से एयरपोर्ट के लिए पैदल रास्ता है क्या?'])
def test_missing_connection_cannot_invent_route_or_walking_access(question):
    result = HindiProjectAssistant(Classifier('service_availability')).process_query(question)
    assert result['status'] == 'unavailable'
    assert result['records'] == []
    assert 'अर्थ यह नहीं' in result['response_hi']


def test_negative_route_goal_does_not_return_positive_connectivity():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('चेन्नई सेंट्रल से एयरपोर्ट मेट्रो से मत जाएँ।')
    assert result['status'] == 'clarification'
    assert not result['records']


def test_more_than_two_locations_cannot_silently_drop_a_destination():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('चेन्नई सेंट्रल से एयरपोर्ट और कोयंबेडु जाना है।')
    assert result['status'] == 'clarification'
    assert not result['records']


def test_accessibility_records_are_metro_specific():
    assistant = HindiProjectAssistant(Classifier('accessibility'))
    metro = assistant.process_query('सेंट्रल मेट्रो में लिफ्ट है?')
    railway = assistant.process_query('सेंट्रल रेलवे स्टेशन में लिफ्ट है?')
    assert metro['status'] == 'information'
    assert metro['records'][0]['mode'] == 'metro'
    assert 'वर्तमान चालू स्थिति' in metro['response_hi']
    assert railway['status'] == 'clarification'
    assert not railway['records']


def test_delay_and_complaint_are_classification_without_live_actions():
    delay = HindiProjectAssistant(Classifier('train_status')).process_query('मेरी ट्रेन बहुत लेट है।')
    complaint = HindiProjectAssistant(Classifier('railway_complaint')).process_query('ट्रेन का शौचालय बहुत गंदा है।')
    assert delay['intent'] == 'train_status' and delay['status'] == 'unavailable'
    assert 'लाइव ट्रेन डेटा नहीं' in delay['response_hi']
    assert complaint['intent'] == 'railway_complaint'
    assert complaint['entities']['complaint_type'] == 'cleanliness'
    assert 'शिकायत दर्ज नहीं' in complaint['response_hi']


def test_catalog_canonical_references_exist_without_database_mutation():
    catalog = json.loads(CATALOG.read_text())
    db = ROOT / catalog['sources']['canonical']
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as conn:
        for row in catalog['locations']:
            for key, mode in [('rail_id', 'suburban_rail'), ('metro_id', 'metro'), ('nearby_bus_id', 'bus')]:
                if key in row:
                    assert conn.execute('SELECT mode FROM transport_stops WHERE stop_id=?', (row[key],)).fetchone() == (mode,)


def test_new_teaching_data_is_small_disjoint_and_explicitly_synthetic():
    from scripts.nlp_v2.train_project import load_rows
    rows = load_rows(ROOT / 'data/project/hindi_intents.csv')
    assert len(rows) == 1652
    assert {row['intent'] for row in rows} == set(LABELS)
    assert {row['language'] for row in rows} == {'hi', 'hinglish'}
    assert all(row['human_reviewed'] == 'false' and (row['source'].startswith('synthetic') or row['source'] == 'ai_authored_development') for row in rows)
    assert all(row['split'] == 'train' for row in rows if row['source'] == 'ai_authored_development')
    for label in LABELS:
        assert 100 <= sum(row['intent'] == label for row in rows) <= 200


def test_family_leakage_is_rejected(tmp_path):
    from scripts.nlp_v2.train_project import load_rows
    rows = list(csv.DictReader((ROOT / 'data/project/hindi_intents.csv').open()))
    rows[1]['split'] = 'test'
    path = tmp_path / 'bad.csv'
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match='family crosses'):
        load_rows(path)


def test_metrics_keep_misses_and_confusion_counts():
    from scripts.nlp_v2.train_project import scores
    result = scores(['route_query', 'route_query', 'train_status', 'railway_complaint'],
                    ['route_query', 'train_status', 'train_status', 'train_status'])
    assert result['accuracy'] == 0.5
    assert sum(map(sum, result['confusion_matrix'])) == 4
    assert result['per_class']['railway_complaint']['recall'] == 0
    assert result['confusion_matrix'][LABELS.index('route_query')][LABELS.index('train_status')] == 1
    with pytest.raises(ValueError):
        scores(['route_query'], [])


def test_report_does_not_mix_entity_and_classifier_metrics(tmp_path):
    from scripts.nlp_v2.train_project import write_report
    metrics = json.loads((ROOT / 'models/hindi_project_metrics.json').read_text())
    metrics['entities'].update(precision=0.25, recall=0.5, f1=1 / 3)
    path = tmp_path / 'report.md'
    write_report(metrics, path)
    report = path.read_text()
    assert 'precision 0.250, recall 0.500, F1 0.333' in report
    summary, _ = report.split('## tfidf: test confusion matrix', 1)
    assert '| tfidf | test |' in summary and '| muril_finetuned | test |' in summary


def test_trained_baseline_handles_the_three_original_demo_categories():
    from src.hindi_project.model import BaselineIntentClassifier
    assistant = HindiProjectAssistant(BaselineIntentClassifier())
    for question, intent in [('मेरी ट्रेन बहुत लेट है।', 'train_status'),
                             ('चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या?', 'service_availability'),
                             ('ट्रेन का शौचालय बहुत गंदा है।', 'railway_complaint'),
                             ('सेंट्रल मेट्रो में लिफ्ट है?', 'accessibility')]:
        result = assistant.process_query(question)
        assert result['intent'] == intent


@pytest.mark.parametrize('question', [
    'Chennai Central se Airport ke liye metro available hai kya?',
    'Airport ke liye Chennai Central se metro hai kya?',
])
def test_hinglish_entity_roles_and_response_keep_same_source(question):
    result = HindiProjectAssistant(Classifier('service_availability')).process_query(question)
    assert result['entities']['origin'] == 'central'
    assert result['entities']['destination'] == 'airport'
    assert result['entities']['transport_mode'] == 'metro'
    assert result['status'] == 'information'
    assert 'published connectivity' in result['response_hinglish']
    assert 'live service' in result['response_hinglish']
    assert not any('\u0900' <= char <= '\u097f' for char in result['response_hinglish'])


def test_hinglish_relative_station_and_complaint_slots():
    catalog = json.loads(CATALOG.read_text())
    assert extract_entities('Is station se bus milti hai?', catalog, 'tambaram')['origin'] == 'tambaram'
    assert extract_entities('Train ka toilet ganda hai.', catalog)['complaint_type'] == 'cleanliness'


@pytest.mark.parametrize('question', [
    'चेन्नई सेंट्रल रेलवे स्टेशन से एयरपोर्ट के लिए मेट्रो है क्या?',
    'Chennai Central railway station se Airport ke liye metro hai kya?',
])
def test_railway_origin_qualifier_does_not_turn_metro_request_into_two_modes(question):
    result = HindiProjectAssistant(Classifier('service_availability')).process_query(question)
    assert result['entities']['origin'] == 'central'
    assert result['entities']['transport_mode'] == 'metro'
    assert result['status'] == 'information'


def test_bus_records_match_ordered_stops_in_the_original_snapshot():
    catalog = json.loads(CATALOG.read_text())
    with sqlite3.connect((ROOT / catalog['sources']['canonical']).resolve().as_uri() + '?mode=ro', uri=True) as conn:
        for row in catalog['connections']:
            if row['mode'] != 'bus':
                continue
            stops = conn.execute('SELECT canonical_stop_id FROM route_stops WHERE route_id=? AND direction_id=? ORDER BY stop_sequence',
                                 (row['route_id'], row['direction_id'])).fetchall()
            ids = [stop[0] for stop in stops]
            assert ids.index(row['boarding_stop_id']) < ids.index(row['alighting_stop_id'])
    result = HindiProjectAssistant(Classifier('service_availability')).process_query('Tambaram se Guindy ke liye bus hai?')
    assert result['records'][0]['route_name'] == '51A'
    assert 'snapshot' in result['response_hinglish'] and 'current service' in result['response_hinglish']


def test_dated_terminal_window_cannot_answer_route_specific_or_current_departures():
    assistant = HindiProjectAssistant(Classifier('service_timing'))
    historical = assistant.process_query('Central metro ki first service ka time kya hai?')
    assert historical['status'] == 'information'
    assert '2024' in historical['response_hinglish'] and 'purana example' in historical['response_hinglish']
    for question in ['Central se Guindy ki first metro kab hai?', 'Central se next metro kab hai?',
                     'Central metro ki frequency kya hai?', 'Guindy se Central ki first train kab hai?']:
        result = assistant.process_query(question)
        assert result['status'] == 'unavailable' and not result['records']


def test_unknown_station_details_are_not_replaced_with_generic_station_information():
    result = HindiProjectAssistant(Classifier('station_information')).process_query('Egmore ka address batao.')
    assert result['status'] == 'unavailable' and not result['records']


def test_metro_train_is_one_mode_but_explicit_alternatives_are_preserved():
    catalog = json.loads(CATALOG.read_text())
    assert extract_entities('Egmore metro ki last train kab hai?', catalog)['transport_mode'] == 'metro'
    assert extract_entities('Central se metro ya train leni hai?', catalog)['transport_mode'] == ['metro', 'rail']


def test_diagnostic_evaluation_cannot_hide_incorrect_intent_or_records():
    from scripts.nlp_v2.evaluate_project import evaluate
    dataset = json.loads((ROOT / 'data/project/academic_checks.json').read_text())
    rows = [dict(dataset['cases'][0], record_ids=['nonexistent_record'])]
    result = evaluate(Classifier('service_availability'), rows, dataset['fields'], json.loads(CATALOG.read_text()))
    assert result['classification']['accuracy'] == 0
    assert result['pipeline_success'] == 0
    assert not result['cases'][0]['records_ok']


def test_fine_tuned_layer_patch_loads_strictly_and_rejects_changed_weights(tmp_path, monkeypatch):
    torch = pytest.importorskip('torch')
    import src.hindi_project.model as project
    from types import SimpleNamespace
    from src.hindi_project.artifacts import sha256_file
    layers = torch.nn.ModuleList([torch.nn.Linear(3, 3) for _ in range(12)])
    monkeypatch.setattr(project, 'MuRILEncoder', lambda *args: SimpleNamespace(
        model=SimpleNamespace(config=SimpleNamespace(hidden_size=3), encoder=SimpleNamespace(layer=layers))))
    head = tmp_path / 'head.pt'
    torch.save(torch.nn.Linear(3, len(LABELS)).state_dict(), head)
    patch = tmp_path / 'patch.pt'
    state = {str(index): {key: torch.ones_like(value) for key, value in layers[index].state_dict().items()} for index in (10, 11)}
    torch.save(state, patch)
    manifest = dict(labels=list(LABELS), training_mode='last_two_encoder_layers_and_head',
                    encoder_patch_path=str(patch),
                    encoder_patch_sha256=sha256_file(patch), head_path=str(head), head_sha256=sha256_file(head))
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest))
    before = layers[0].weight.detach().clone()
    project.ProjectIntentClassifier(path)
    assert torch.equal(layers[10].weight, torch.ones_like(layers[10].weight))
    assert torch.equal(layers[0].weight, before)
    patch.write_bytes(b'changed')
    with pytest.raises(ValueError, match='encoder SHA-256 mismatch'):
        project.ProjectIntentClassifier(path)


@pytest.mark.parametrize('question,expected_ids', [
    ('Velachery se Park station kaise jayein?', {'MRTS_VELACHERY', 'RAIL_CHENNAI_PARK', 'RAIL_CHENNAI_PARK_TOWN'}),
    ('Chennai Central se Mambalam station kaise jau?', {'RAIL_MAMBALAM'}),
    ('वेलाचेरी से पार्क स्टेशन कैसे जाएं?', {'MRTS_VELACHERY', 'RAIL_CHENNAI_PARK', 'RAIL_CHENNAI_PARK_TOWN'}),
    ('चेन्नई सेंट्रल से माम्बलम स्टेशन कैसे जाऊँ?', {'RAIL_MAMBALAM'}),
    ('Marina Beach se Chennai Airport bus hai kya?', {'OSM_POI_12137617372'}),
])
def test_names_outside_demo_catalog_are_recognized_from_original_database(question, expected_ids):
    result = HindiProjectAssistant(Classifier('route_query')).process_query(question)
    actual = {candidate['entity_id'] for row in result['location_matches'] for candidate in row['candidates']}
    assert expected_ids <= actual
    assert 'origin' in result['entities'] and 'destination' in result['entities']
    assert 'pehchane gaye' in result['response_hinglish']


def test_park_station_preserves_park_and_park_town_ambiguity():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('Velachery MRTS station se Park station train se kaise jayein?')
    assert result['status'] == 'clarification' and not result['records']
    destinations = [row for row in result['location_ambiguities'] if row['role'] == 'destination']
    assert {'RAIL_CHENNAI_PARK', 'RAIL_CHENNAI_PARK_TOWN'} <= {row['entity_id'] for row in destinations[0]['candidates']}


def test_known_railway_names_do_not_invent_missing_rail_topology():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('Chennai Park railway station se Mambalam railway station train se kaise jayein?')
    assert result['canonical_slots'] == {'origin': 'RAIL_CHENNAI_PARK', 'destination': 'RAIL_MAMBALAM'}
    assert result['status'] == 'unavailable' and not result['records']
    assert 'real service' in result['response_hinglish']


def test_full_database_bus_lookup_retains_published_direction_and_source():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('Foreshore Estate Bus Terminus se M.G.R.Koyambedu Bus Terminus bus se kaise jayein?')
    assert result['status'] == 'information'
    record = result['records'][0]
    assert record['origin_stop_id'] == 'BUS_247677936'
    assert record['destination_stop_id'] == 'BUS_5822'
    assert record['origin_sequence'] < record['destination_sequence']
    assert record['source'] == 'CHENNAI_COMMUNITY_GTFS'
    assert result['sources'] and 'current service' in result['response_hinglish']


def test_metro_name_outside_demo_is_not_an_unknown_station():
    result = HindiProjectAssistant(Classifier('station_information')).process_query('Alandur metro station kahan hai?')
    assert result['entities']['station'] == 'METRO_ARIGNAR_ANNA_ALANDUR'
    assert result['status'] == 'information'
    assert 'Arignar Anna Alandur Metro' in result['response_hinglish']


def test_broader_lookup_does_not_discard_temporal_route_constraints():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('Foreshore Estate Bus Terminus se M.G.R.Koyambedu Bus Terminus bus se subah kaise jayein?')
    assert result['status'] != 'information' and not result['records']


def test_generic_bus_stand_target_is_not_mistaken_for_a_second_location():
    result = HindiProjectAssistant(Classifier('station_information')).process_query('Tambaram station ke nazdeek bus stand ka naam kya hai?')
    assert result['entities']['station'] == 'tambaram'
    assert 'origin' not in result['entities'] and 'destination' not in result['entities']
    assert result['status'] == 'information'


def test_additional_bus_timetable_uses_existing_schedule_with_snapshot_caveat():
    result = HindiProjectAssistant(Classifier('service_timing')).process_query('Foreshore Estate Bus Terminus ki first bus kab hai?')
    assert result['status'] == 'information'
    assert result['records'][0]['type'] == 'canonical_timetable'
    assert result['records'][0]['source'] == ['CHENNAI_COMMUNITY_GTFS']
    assert result['sources'] and 'current service' in result['response_hinglish']


@pytest.mark.parametrize('question', [
    'Chennai Central se velachery kaise jayein?',
    'चेन्नई सेंट्रल से वेलाचेरी कैसे जाएं?',
    'Chennai Central railway station se Velachery train se kaise jau?',
])
def test_open_route_question_can_offer_sourced_mrts_guidance_without_asking_for_mode(question):
    result = HindiProjectAssistant(Classifier('route_query')).process_query(question)
    assert result['status'] == 'information'
    assert result['records'][0]['id'] == 'central_velachery_mrts_guidance'
    assert 'Chennai Park Town MRTS' in result['response_hinglish']
    assert 'alag stations' in result['response_hinglish'] and 'current departure' in result['response_hinglish']
    assert result['sources'][0].startswith('https://sr.indianrailways.gov.in/')


def test_reverse_mrts_guidance_does_not_invent_a_direct_central_train():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('Velachery se Central kaise jayein?')
    assert result['records'][0]['id'] == 'velachery_central_mrts_guidance'
    assert 'Chennai Beach ki direction' in result['response_hinglish']
    assert 'Park Town aur Central alag' in result['response_hinglish']


@pytest.mark.parametrize('question', [
    'Velachery station ke paas bus stop kaunsa h?',
    'वेलाचेरी स्टेशन के पास बस स्टॉप कौन सा है?',
    'Mambalam station ke paas bus stand kaunsa hai?',
    'Marina Beach ke paas bus stop kaunsa h?',
])
def test_nearby_bus_target_is_separate_from_named_station_or_landmark(question):
    result = HindiProjectAssistant(Classifier('station_information')).process_query(question)
    assert result['status'] == 'information'
    assert result['canonical_slots']['station'] != result['records'][0]['stop_id']
    assert all(row['mode'] == 'bus' for row in result['records'])
    assert 'walking distance nahi' in result['response_hinglish']
    assert result['sources']


@pytest.mark.parametrize('question', [
    'Velachery station ke paas metro station kaunsa hai?',
    'Guindy railway station ke paas metro station kaunsa hai?',
])
def test_nearby_metro_target_does_not_reclassify_railway_anchor(question):
    result = HindiProjectAssistant(Classifier('station_information')).process_query(question)
    assert result['status'] == 'information'
    assert result['canonical_slots']['station'] in {'MRTS_VELACHERY', 'RAIL_GUINDY'}
    assert all(row['mode'] == 'metro' and row['source'] == 'CMRL_API' for row in result['records'])


@pytest.mark.parametrize('question', [
    'Guindy metro station ke paas bus stop kaunsa hai?',
    'गिंडी मेट्रो स्टेशन के पास बस स्टॉप कौन सा है?',
])
def test_official_nearby_stop_names_can_answer_without_guessing_conflicting_coordinates(question):
    result = HindiProjectAssistant(Classifier('station_information')).process_query(question)
    assert result['entities']['transport_mode'] == 'bus'
    assert result['status'] == 'information'
    assert result['records'][0]['id'] == 'guindy_metro_published_bus_stops'
    assert 'walking distance available nahi' in result['response_hinglish']
    assert not any('distance_m' in row for row in result['records'])
    assert any(row['reason'] == 'coordinate_conflict' for row in result['location_ambiguities'])


def test_coordinate_conflict_without_published_facts_is_a_data_gap(tmp_path):
    catalog = json.loads(CATALOG.read_text())
    catalog['nearby_transport_facts'] = []
    path = tmp_path / 'catalog.json'
    path.write_text(json.dumps(catalog))
    result = HindiProjectAssistant(Classifier('station_information'), path).process_query('Guindy metro station ke paas bus stop kaunsa hai?')
    assert result['status'] == 'unavailable' and not result['records']
    assert 'mode clear' in result['response_hinglish']


def test_explicit_bus_request_uses_bus_options_and_keeps_boarding_stop_names():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('Central se Velachery bus se kaise jau?')
    assert result['status'] == 'information'
    assert all(row['mode'] == 'bus' and row['source'] == 'CHENNAI_COMMUNITY_GTFS' for row in result['records'])
    assert all(row['origin_stop_id'] == 'BUS_83' for row in result['records'])
    assert 'Government General Hospital' in result['response_hinglish']
    assert 'coverage incomplete' in result['response_hinglish']


def test_uncovered_explicit_metro_mode_is_not_replaced_with_mrts_or_requested_again():
    result = HindiProjectAssistant(Classifier('route_query')).process_query('Central se Velachery metro se kaise jayein?')
    assert result['status'] == 'unavailable' and not result['records']
    assert 'mode samajh liya' in result['response_hinglish']


@pytest.mark.parametrize('question', [
    'Central se Velachery aaj train se kaise jayein?',
    'Central se Airport aaj metro hai kya?',
    'Central se Airport sabse sasta route kya hai?',
    'Central se Airport via Mars metro se kaise jayein?',
])
def test_curated_examples_cannot_discard_date_optimization_or_unknown_waypoint(question):
    result = HindiProjectAssistant(Classifier('route_query')).process_query(question)
    assert result['status'] != 'information' and not result['records']


def test_real_two_station_ambiguity_and_multiple_targets_still_need_clarification():
    assistant = HindiProjectAssistant(Classifier('station_information'))
    for question in ['Guindy station ke paas bus stop kaunsa hai?', 'Marina Beach ke paas bus ya metro station kaunsa hai?']:
        result = assistant.process_query(question)
        assert result['status'] == 'clarification' and not result['records']


def test_added_boarding_and_guidance_references_exist_in_the_original_database():
    catalog = json.loads(CATALOG.read_text())
    with sqlite3.connect((ROOT / catalog['sources']['canonical']).resolve().as_uri() + '?mode=ro', uri=True) as conn:
        for location in catalog['locations']:
            for candidate in location.get('boarding_candidates', []):
                assert conn.execute('SELECT canonical_name,mode FROM transport_stops WHERE stop_id=?', (candidate['entity_id'],)).fetchone() == (candidate['canonical_name'], candidate['mode'])
        for row in catalog['journey_guidance']:
            for key in ('origin_stop_id', 'destination_stop_id', 'boarding_stop_id', 'alighting_stop_id'):
                if key in row:
                    assert conn.execute('SELECT 1 FROM transport_stops WHERE stop_id=?', (row[key],)).fetchone()
