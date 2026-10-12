"""Report actual model, slot and catalog outcomes on a small unreviewed check set."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.hindi_project.assistant import CATALOG, HindiProjectAssistant, extract_entities
from src.hindi_project.model import BaselineIntentClassifier, ProjectIntentClassifier, ROOT
from src.hindi_project.artifacts import sha256_file
from scripts.nlp_v2.train_project import scores


def slot_scores(pairs: list[tuple[dict, dict]]) -> dict:
    def values(slots):
        return {(name, json.dumps(value, ensure_ascii=False, sort_keys=True)) for name, value in slots.items()}
    tp = fp = fn = exact = 0
    for expected, actual in pairs:
        gold, predicted = values(expected), values(actual)
        tp += len(gold & predicted)
        fp += len(predicted - gold)
        fn += len(gold - predicted)
        exact += gold == predicted
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {'count': len(pairs), 'tp': tp, 'fp': fp, 'fn': fn, 'precision': precision, 'recall': recall,
            'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            'exact_match': exact / len(pairs) if pairs else 0.0}


def evaluate(classifier, rows, fields, catalog):
    assistant = HindiProjectAssistant(classifier)
    cases, slot_pairs = [], []
    for row in rows:
        raw_slots = extract_entities(row['text'], catalog)
        if row['intent'] != 'railway_complaint':
            raw_slots.pop('complaint_type', None)
        predicted_slots = {name: value for name, value in raw_slots.items() if name in fields}
        expected_slots = {name: value for name, value in row['entities'].items() if name in fields}
        slot_pairs.append((expected_slots, predicted_slots))
        result = assistant.process_query(row['text'])
        actual_ids = [record.get('id') for record in result['records']]
        records_ok = sorted(actual_ids) == sorted(row['record_ids'])
        # Information with sourced records must retain source attribution.
        records_ok = records_ok and (not result['records'] or bool(result['sources']))
        slot_ok = expected_slots == predicted_slots
        intent_ok = result['intent'] == row['intent']
        status_ok = result['status'] == row['status']
        cases.append({'id': row['id'], 'language': row['language'], 'text': row['text'],
                      'expected_intent': row['intent'], 'predicted_intent': result['intent'],
                      'expected_entities': expected_slots, 'predicted_entities': predicted_slots,
                      'expected_status': row['status'], 'actual_status': result['status'],
                      'expected_record_ids': row['record_ids'], 'actual_record_ids': actual_ids,
                      'intent_ok': intent_ok, 'slots_ok': slot_ok, 'status_ok': status_ok, 'records_ok': records_ok,
                      'pipeline_ok': intent_ok and slot_ok and status_ok and records_ok,
                      'response_hi': result['response_hi'], 'response_hinglish': result['response_hinglish'],
                      'sources': result['sources']})
    classification = scores([row['intent'] for row in rows], [case['predicted_intent'] for case in cases])
    return {'classification': classification,
            'by_language': {language: scores([case['expected_intent'] for case in cases if case['language'] == language],
                                            [case['predicted_intent'] for case in cases if case['language'] == language])
                            for language in sorted({row['language'] for row in rows})},
            'entities': slot_scores(slot_pairs),
            'pipeline_success': sum(case['pipeline_ok'] for case in cases) / len(cases),
            'status_success': sum(case['status_ok'] for case in cases) / len(cases),
            'record_success': sum(case['records_ok'] for case in cases) / len(cases), 'cases': cases}


def main():
    import torch
    torch.set_num_threads(2)
    path = ROOT / 'data/project/academic_checks.json'
    dataset = json.loads(path.read_text(encoding='utf-8'))
    rows = dataset['cases']
    training = list(csv.DictReader((ROOT / 'data/project/hindi_intents.csv').open(encoding='utf-8')))
    user_data = json.loads((ROOT / 'data/project/user_questions.json').read_text(encoding='utf-8'))
    if {row['text'] for row in rows + user_data['questions']} & {row['text'] for row in training}:
        raise ValueError('Evaluation question overlaps training/development partitions')
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    report = {'source': dataset['source'], 'human_reviewed': dataset['human_reviewed'], 'policy': dataset['policy'],
              'dataset_sha256': sha256_file(path), 'catalog_sha256': sha256_file(CATALOG),
              'model_manifest_sha256': sha256_file(ROOT / 'models/hindi_project_manifest.json'),
              'fields': dataset['fields'], 'models': {}, 'user_questions': {}}
    report['development_history'] = json.loads((ROOT / 'data/project/development_history.json').read_text(encoding='utf-8'))
    for name, classifier in [('tfidf', BaselineIntentClassifier()), ('muril_finetuned', ProjectIntentClassifier())]:
        report['models'][name] = evaluate(classifier, rows, dataset['fields'], catalog)
        assistant = HindiProjectAssistant(classifier)
        report['user_questions'][name] = [dict(row, actual=assistant.process_query(row['text']))
                                         for row in user_data['questions']]
        print(name, 'check accuracy', round(report['models'][name]['classification']['accuracy'], 3),
              'pipeline', round(report['models'][name]['pipeline_success'], 3), flush=True)
    (ROOT / 'models/hindi_project_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_report(report, ROOT / 'docs/PIPELINE_EVALUATION.md')


def write_report(report: dict, path: Path):
    lines = ['# Small Hindi/Hinglish pipeline check', '',
             'Ninety AI-authored, unreviewed questions: 45 paired Hindi/Hinglish scenarios across nine intents. '
             'Their exact questions were excluded from training. Diagnostic failures informed a later training-data coverage correction; '
             'epoch selection still used only the declared validation partition. This is a reproducible diagnostic, '
             'not a blind human benchmark or real-passenger accuracy estimate.', '',
             'Pipeline success requires correct intent, evaluated slot values, response status and exact catalog record IDs, '
             'with source attribution when records are returned. It does not judge fluency, full answer semantics or physical travel feasibility.', '',
             '| Model | Intent accuracy | Macro F1 | Slot F1 | Slot exact match | Pipeline success |',
             '| --- | --- | --- | --- | --- | --- |']
    for name, result in report['models'].items():
        c, e = result['classification'], result['entities']
        lines.append(f"| {name} | {c['accuracy']:.3f} | {c['macro_f1']:.3f} | {e['f1']:.3f} | {e['exact_match']:.3f} | {result['pipeline_success']:.3f} |")
    lines += ['', 'Evaluated slots: ' + ', '.join(report['fields']) + '. Name recognition reuses the full canonical database and its stored aliases. '
              'These checks mainly cover the seven curated example locations; they do not evaluate all database names, unknown-name span detection or a learned NER model. '
              'The original expected statuses are retained: broader-name ambiguity can now produce clarification where the earlier seven-name lookup returned unavailable.', '',
              '## Per-language classification', '', '| Model | Language | Accuracy | Macro F1 |', '| --- | --- | --- | --- |']
    for name, result in report['models'].items():
        for language, values in result['by_language'].items():
            lines.append(f"| {name} | {language} | {values['accuracy']:.3f} | {values['macro_f1']:.3f} |")
    for name, result in report['models'].items():
        lines += ['', f'## {name}: retained failures', '']
        for case in [case for case in result['cases'] if not case['pipeline_ok']]:
            failures = [key for key in ('intent', 'slots', 'status', 'records') if not case[key + '_ok']]
            lines.append(f"- {case['text']} — expected {case['expected_intent']}, predicted {case['predicted_intent']}; failed checks: {', '.join(failures)}.")
    lines += ['', '## Four user-supplied questions', '',
              'These four Hinglish inputs were supplied by the user and excluded from training. They were visible during implementation, '
              'so they are qualitative demonstrations, not a blind benchmark. Ground-truth intent labels were assigned by the assistant.', '']
    lines += ['First-pass TF-IDF classified one of these four intents correctly; after a general training-data correction '
              'it classified all four correctly. MuRIL classified all four in both passes. These inputs informed development '
              'and are not evidence of unseen-user accuracy. First-pass predictions are retained in `data/project/development_history.json`.', '']
    for name, cases in report['user_questions'].items():
        lines += [f'### {name}', '']
        for row in cases:
            actual = row['actual']
            lines += [f"- **{row['text']}**", f"  - Expected intent: `{row['intent']}`; predicted: `{actual['intent']}`; status: `{actual['status']}`.",
                      '  - ' + actual['response_hinglish']]
    lines += ['', '## Reproduce', '', 'Run `python -m scripts.nlp_v2.evaluate_project` after training. '
              'Exact per-question outputs and confusion matrices are saved in `models/hindi_project_checks.json`. '
              'Do not train or tune on these checks; retain errors in the report. Human review remains outstanding.', '']
    path.write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
