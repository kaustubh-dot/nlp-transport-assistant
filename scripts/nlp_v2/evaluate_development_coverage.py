#!/usr/bin/env python3
"""Versioned development-only contracts; never an untouched test estimate."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date
import hashlib
import json
from math import isfinite
from pathlib import Path
import re
import subprocess

from src.normalization import normalize_text
from src.nlp_v2.assistant import AssistantReply, T3Assistant
from src.nlp_v2.contracts import IntentPrediction, validate_slots, validate_intent_slots, TRANSPORT_MODES
from src.nlp_v2.dispatch import OPERATIONS
from src.nlp_v2.domain import CanonicalTransitService, DEFAULT_DB
from src.nlp_v2.model import DEFAULT_MANIFEST, load_manifest, sha256_file

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / 'data/nlp_v2/development/assistant_coverage_v1.json'
MANIFEST = SUITE.with_name('assistant_coverage_v1_manifest.json')
STATUSES = {'ok', 'unavailable', 'clarification', 'out_of_scope', 'error'}
LANGUAGES = {'EN', 'HI_DEVA', 'HI_LATN', 'HINGLISH_LATN', 'MIXED_SCRIPT_CS'}
REASONS = {'missing_slot', 'entity_ambiguity', 'temporal_ambiguity', 'intent_ambiguity', 'multiple_goals'}
EVIDENCE = {'fare', 'sequences', 'membership', 'routes', 'connectivity', 'bounds', 'frequency', 'departures', 'nearest'}
INTENT_EVIDENCE = {
    'fare_calculation':'fare', 'route_stop_sequence':'sequences',
    'route_stop_membership':'membership', 'point_to_point_route':'routes',
    'mode_availability':'connectivity', 'first_and_last_service':'bounds',
    'service_frequency':'frequency', 'scheduled_departure':'departures',
    'nearest_transport':'nearest',
}


def fingerprint(query: str) -> str:
    return hashlib.sha256(normalize_text(query).encode('utf-8')).hexdigest()


def heldout_fingerprints(stress: Path, reference: Path) -> set[str]:
    """Opaque overlap check only. Never return text, labels or held-out row IDs."""
    with stress.open(newline='', encoding='utf-8') as stream:
        fingerprints = {fingerprint(row['query']) for row in csv.DictReader(stream)}
    entries = json.loads(reference.read_text(encoding='utf-8'))
    values = entries.values() if isinstance(entries, dict) else entries
    fingerprints.update(fingerprint(row['query']) for row in values if row.get('query'))
    return fingerprints


def validate_cases(cases: list[dict]) -> None:
    if not isinstance(cases, list) or not cases:
        raise ValueError('Development cases must be a nonempty list')
    ids, queries = set(), set()
    for c in cases:
        if not isinstance(c, dict) or any(not isinstance(c.get(k), str) or not c[k].strip()
                                         for k in ('id', 'query', 'status', 'language', 'noise', 'scenario', 'provenance')):
            raise ValueError('Malformed development case')
        if c['id'] in ids or fingerprint(c['query']) in queries:
            raise ValueError('Duplicate development id or normalized query')
        ids.add(c['id']); queries.add(fingerprint(c['query']))
        ambiguous = (c.get('intent') is None and c.get('operation') is None
                     and c.get('status') == 'clarification'
                     and c.get('clarification_reason') in {'multiple_goals', 'intent_ambiguity'})
        candidate_intents = c.get('candidate_intents', [])
        if not isinstance(candidate_intents, list) or any(v not in OPERATIONS for v in candidate_intents):
            raise ValueError('Invalid candidate intents')
        if len(candidate_intents) != len(set(candidate_intents)):
            raise ValueError('Duplicate candidate intents')
        if ambiguous and len(set(candidate_intents)) < 2:
            raise ValueError('Ambiguous intent requires candidates')
        if not ambiguous and (c.get('intent') not in OPERATIONS or c.get('operation') != OPERATIONS[c['intent']]):
            raise ValueError('Invalid T3 intent/operation contract')
        if c['status'] not in STATUSES or c['language'] not in LANGUAGES:
            raise ValueError('Invalid status or language')
        if not isinstance(c.get('slots'), dict):
            raise ValueError('Gold slots must be a dictionary')
        validate_slots(c['slots'])
        if c.get('intent') is not None:
            validate_intent_slots(c['intent'], c['slots'])
        if not isinstance(c.get('expected_data', {}), dict):
            raise ValueError('Invalid expected data')
        if c.get('evidence') is not None and c['evidence'] not in EVIDENCE:
            raise ValueError('Unknown evidence kind')
        if c.get('evidence') is not None and c['evidence'] != INTENT_EVIDENCE.get(c.get('intent')):
            raise ValueError('Evidence kind does not match the expected operation')
        if c['status'] == 'ok' and c.get('evidence') not in EVIDENCE:
            raise ValueError('An OK case requires evidence')
        reason = c.get('clarification_reason')
        if reason is not None and (reason not in REASONS or c['status'] != 'clarification'):
            raise ValueError('Invalid clarification reason')
        if c['status'] == 'clarification' and reason is None:
            raise ValueError('Clarification requires a reason')
        if not isinstance(c.get('missing_slots', []), list) or any(not isinstance(v, str) for v in c.get('missing_slots', [])):
            raise ValueError('Invalid missing slot expectations')
        if not isinstance(c.get('require_candidates', False), bool):
            raise ValueError('Invalid candidate expectation')


def load_suite(path: Path = SUITE, manifest_path: Path = MANIFEST) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    def checksum(value):
        return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)
    if (not isinstance(manifest, dict) or type(manifest.get('version')) is not int
            or manifest['version'] != 1 or not checksum(manifest.get('suite_sha256'))
            or sha256_file(path) != manifest['suite_sha256']):
        raise ValueError('Development suite version/hash mismatch')
    if not checksum(manifest.get('canonical_database_sha256')):
        raise ValueError('Invalid canonical database hash')
    try:
        value = manifest.get('reference_date')
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError as exc:
        raise ValueError('Invalid reference date') from exc
    cases = json.loads(path.read_text(encoding='utf-8'))
    validate_cases(cases)
    if type(manifest.get('count')) is not int or manifest['count'] != len(cases):
        raise ValueError('Development manifest count mismatch')
    return cases


def _metric(success: int, count: int) -> dict:
    return {'success': success, 'count': count, 'rate': success/count if count else None}


def _evidence(kind: str | None, data: dict, slots: dict) -> bool:
    if kind is None:
        return True
    if data.get('provisional') is not True:
        return False
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def source(value):
        return text(value) or (isinstance(value, list) and bool(value) and all(text(v) for v in value))
    def number(value):
        return type(value) in (int, float) and isfinite(value)
    def clock(value):
        return isinstance(value, str) and re.fullmatch(r'\d{2,}:[0-5]\d:[0-5]\d', value) is not None
    def sourced(rows):
        return isinstance(rows, list) and bool(rows) and all(isinstance(v, dict) and source(v.get('source')) for v in rows)
    if kind == 'fare':
        return (source(data.get('source')) and text(data.get('effective_date'))
                and text(data.get('currency')) and number(data.get('amount')) and data['amount'] >= 0)
    if kind == 'bounds':
        return source(data.get('source')) and clock(data.get('first_departure')) and clock(data.get('last_departure'))
    if kind == 'frequency':
        return (source(data.get('source')) and number(data.get('median_headway_minutes'))
                and data['median_headway_minutes'] > 0 and type(data.get('sample_intervals')) is int and data['sample_intervals'] > 0)
    if kind == 'membership':
        return (isinstance(data.get('on_route'), bool) and isinstance(data.get('route_ids'), list)
                and bool(data['route_ids']) and all(text(v) for v in data['route_ids']) and source(data.get('source')))
    if kind == 'nearest':
        mode = slots.get('transport_mode')
        return (data.get('distance_type') == 'straight_line' and sourced(data.get('stops'))
                and data.get('anchor') == (slots.get('landmark') or slots.get('locality'))
                and all(text(v.get('name')) and text(v.get('stop_id'))
                        and v.get('mode') in TRANSPORT_MODES - {'any'}
                        and (mode in (None, 'any') or v['mode'] == mode)
                        and number(v.get('distance_m')) and v['distance_m'] >= 0 for v in data['stops']))
    if kind == 'connectivity':
        kind = 'routes'
        if data.get('scope') != 'published_connectivity_not_current_operation':
            return False
    key = {'routes': 'routes', 'sequences': 'sequences', 'departures': 'departures'}[kind]
    rows = data.get(key)
    if not sourced(rows):
        return False
    if kind == 'sequences':
        for row in rows:
            if (not text(row.get('route_id')) or not text(row.get('route_name'))
                    or row.get('mode') not in TRANSPORT_MODES - {'any'}
                    or (slots.get('transport_mode') not in (None,'any') and row['mode'] != slots['transport_mode'])):
                return False
            stops = row.get('stops')
            if not isinstance(stops, list) or len(stops) < 2:
                return False
            if not all(isinstance(v, dict) and text(v.get('stop_id')) and text(v.get('name')) and type(v.get('sequence')) is int for v in stops):
                return False
            if any(a['sequence'] >= b['sequence'] for a,b in zip(stops,stops[1:])):
                return False
        return True
    if kind == 'departures':
        return all(clock(v.get('time')) and text(v.get('route_name')) and text(v.get('route_id')) for v in rows)
    return all(text(v.get('route_id')) and text(v.get('route_name')) and text(v.get('origin_stop_id'))
               and text(v.get('destination_stop_id')) and v.get('mode') in TRANSPORT_MODES - {'any'}
               and (slots.get('transport_mode') in (None,'any') or v['mode'] == slots['transport_mode']) for v in rows)


def score_cases(cases: list[dict], replies: list[AssistantReply]) -> dict:
    if not cases or len(cases) != len(replies):
        raise ValueError('Empty or unaligned development replies')
    validate_cases(cases)
    rows = []
    for c, r in zip(cases, replies):
        if r.status not in STATUSES:
            raise ValueError('Unknown assistant status')
        intent = r.intent == c['intent']
        operation = r.operation == c['operation']
        slot_checks = [r.slots.get(k) == v for k, v in c['slots'].items()]
        slots = all(slot_checks)
        reason = c.get('clarification_reason') is None or r.clarification_reason == c['clarification_reason']
        missing = set(c.get('missing_slots', [])) <= set(r.missing_slots)
        candidates = not c.get('require_candidates') or len(r.candidate_entities) > 1
        candidate_intents = not c.get('candidate_intents') or set(c['candidate_intents']) == set(r.candidate_intents)
        evidence = _evidence(c.get('evidence'), r.data, c['slots'])
        expected_data = all(type(r.data.get(k)) is type(v) and r.data.get(k) == v
                            for k,v in c.get('expected_data', {}).items())
        terminal = (intent and r.status == c['status'] and slots and reason and missing and candidates and candidate_intents
                    and evidence and expected_data and (operation or (c['status'] == 'clarification' and r.operation is None)))
        failures = []
        if not intent:
            failures.append('classifier_failure')
        else:
            if not slots:
                failures.append('entity_resolution_failure' if any(k in {'origin','destination','station','stop','landmark','locality','via'} and r.slots.get(k) != v for k,v in c['slots'].items()) else 'slot_extraction_failure')
            if r.status != c['status'] or not reason or not missing or not candidates or not candidate_intents:
                failures.append('clarification_policy_failure' if 'clarification' in {r.status,c['status']} else 'domain_code_failure')
            if not evidence or not expected_data:
                failures.append('evidence_contract_failure')
            if not operation and (c['status'] != 'clarification' or r.operation is not None):
                failures.append('operation_selection_failure')
        rows.append({'id': c['id'], 'gold_intent': c['intent'] or 'ambiguous', 'language': c['language'], 'noise': c['noise'],
                     'scenario': c['scenario'], 'gold_status': c['status'], 'status': r.status,
                     'intent_success': intent, 'operation_success': operation, 'slot_success': slots,
                     'slot_checks': len(slot_checks), 'correct_slots': sum(slot_checks),
                     'evidence_success': evidence, 'terminal_success': terminal,
                     'failures': failures})
    def aggregate(items):
        n = len(items)
        nonclar = [v for v in items if v['gold_status'] != 'clarification']
        answerable = [v for v in items if v['gold_status'] == 'ok']
        counts = Counter(v['status'] for v in items)
        return {
            'count': n, 'intent_contract': _metric(sum(v['intent_success'] for v in items),n),
            'operation_selection': _metric(sum(v['operation_success'] for v in items),n),
            'slot_resolution': _metric(sum(v['correct_slots'] for v in items),sum(v['slot_checks'] for v in items)),
            'slot_case_success': _metric(sum(v['slot_success'] for v in items if v['slot_checks']),sum(bool(v['slot_checks']) for v in items)),
            'terminal_behavior': _metric(sum(v['terminal_success'] for v in items),n),
            'answerable_coverage': _metric(sum(v['terminal_success'] for v in answerable),len(answerable)),
            'false_positive_clarification': _metric(sum(v['status']=='clarification' for v in nonclar),len(nonclar)),
            'clarification_rate': counts['clarification']/n,
            'unavailable_rate': counts['unavailable']/n, 'ok_rate': counts['ok']/n,
            'status_counts': {s: counts[s] for s in sorted(STATUSES)},
            'failure_counts': dict(sorted(Counter(f for v in items for f in v['failures']).items())),
        }
    scores = aggregate(rows)
    scores['per_intent'] = {intent: aggregate([v for v in rows if v['gold_intent']==intent]) for intent in sorted({v['gold_intent'] for v in rows})}
    scores['by_language'] = {language: aggregate([v for v in rows if v['language']==language]) for language in sorted({v['language'] for v in rows})}
    scores['by_noise'] = {noise: aggregate([v for v in rows if v['noise']==noise]) for noise in sorted({v['noise'] for v in rows})}
    scores['cases'] = rows
    return scores


def evaluate(output_dir: Path, *, gold_intent: bool = False) -> dict:
    output_dir = Path(output_dir).resolve()
    allowed = ROOT / 'reports/nlp_v2/development_coverage'
    if output_dir.is_relative_to(ROOT) and not output_dir.is_relative_to(allowed):
        raise ValueError('Development output destination must be dedicated reports or outside the repo')
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError('Development output exists')
    cases = load_suite()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if sha256_file(DEFAULT_DB) != manifest['canonical_database_sha256']:
        raise ValueError('Development canonical DB hash mismatch')
    heldout = heldout_fingerprints(ROOT/'data/nlp_v2/gate_b2/gate_b2_stress_eval.csv', ROOT/'data/nlp_v2/gate_b2/human_annotation_key.json')
    if any(fingerprint(c['query']) in heldout for c in cases):
        raise ValueError('Development suite overlaps held-out normalized query fingerprints')
    class GoldIntentDiagnostic:
        case = None
        def predict(self, query):
            c = self.case
            if c['intent'] is None:
                return IntentPrediction(None, tuple(c['candidate_intents']), 1., c['clarification_reason'])
            return IntentPrediction(c['intent'], (c['intent'],), 1.)
    classifier = GoldIntentDiagnostic() if gold_intent else None
    assistant = T3Assistant(classifier=classifier, service=CanonicalTransitService(reference_date=date.fromisoformat(manifest['reference_date'])))
    replies = []
    for c in cases:
        if gold_intent:
            classifier.case = c
        replies.append(assistant.process_query(c['query']))
    production_files = [p for p in (ROOT/'src/nlp_v2').glob('*.py')]+[ROOT/'src/normalization.py',ROOT/'src/entity_extractor.py',Path(__file__).resolve()]
    report = {
        'evaluation_type': 'development_only_contracts',
        'mode': 'gold_intent_downstream_diagnostic' if gold_intent else 'production_model',
        'classifier_accuracy_measured': not gold_intent,
        'git_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        'suite_version': 1, 'suite_sha256': sha256_file(SUITE),
        'canonical_database_sha256': manifest['canonical_database_sha256'],
        'reference_date': manifest['reference_date'], 'model_manifest_sha256': sha256_file(DEFAULT_MANIFEST),
        'checkpoint_sha256': load_manifest()['checkpoint_sha256'],
        'source_hashes': {str(p.relative_to(ROOT)): sha256_file(p) for p in sorted(production_files)},
        'normalized_heldout_overlap': 0,
        'limitations': ['Development contracts are an observed optimization suite, not generalization evidence.',
                        'Exact normalized overlap guard does not prove semantic independence.',
                        'Gold-intent diagnostics bypass classifier inference; their intent score is not model accuracy.',
                        'Evidence checks validate shape/source presence, not independent transport fact correctness.'],
        'scores': score_cases(cases,replies),
    }
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'coverage.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report['scores'][k] for k in ('count','intent_contract','terminal_behavior','answerable_coverage','false_positive_clarification','status_counts')}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--gold-intent',action='store_true',help='Diagnostic bypass of classifier; never model accuracy')
    args=parser.parse_args()
    evaluate(args.output_dir,gold_intent=args.gold_intent)

if __name__ == '__main__':
    main()
