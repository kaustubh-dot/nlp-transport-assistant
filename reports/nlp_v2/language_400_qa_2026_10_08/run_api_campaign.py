"""Fresh development-only language QA; no research evaluators or training.

This runner preserves exact authored questions and actual public API responses.
Semantic outcome judgments belong to the separate manual assessment files.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def campaign(label: str, api: str) -> None:
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    cases_by_language = {}
    all_queries = set()
    prior = set()
    for previous in ('hindi/baseline.json', 'hinglish/api_baseline.json'):
        data = json.loads((HERE.parent / 'language_toggle_qa_2026_10_08' / previous).read_text())
        rows = data if isinstance(data, list) else data.get('cases', data.get('results', []))
        prior.update(row['query'] for row in rows)
    for language in ('hindi', 'hinglish'):
        cases = json.loads((HERE / language / 'cases.json').read_text(encoding='utf-8'))
        assert len(cases) == 200, (language, len(cases))
        assert len({c['id'] for c in cases}) == 200
        for case in cases:
            assert isinstance(case['query'], str) and case['query'].strip()
            assert case['query'] not in all_queries, ('duplicate', case['id'])
            assert case['query'] not in prior, ('prior duplicate', case['id'])
            all_queries.add(case['query'])
        cases_by_language[language] = cases
    manifest_path = HERE / f'{label}_manifest.json'
    assert not manifest_path.exists(), 'Use a new campaign label; never overwrite evidence.'
    manifest = {
        'kind': 'fresh_custom_development_product_qa', 'label': label,
        'started_utc': datetime.now(timezone.utc).isoformat(), 'git_head': source,
        'api': api, 'count': 400,
        'case_sha256': {lang: digest(HERE / lang / 'cases.json') for lang in cases_by_language},
        'source_sha256': {str(p.relative_to(ROOT)): digest(p) for folder in ('src/nlp_v2', 'app')
                          for p in sorted((ROOT / folder).glob('*.py'))},
        'model_manifest_sha256': digest(ROOT / 'models/nlp_v2_t3_manifest.json'),
        'semantic_scoring': 'Independent manual assessments; status and intent equality alone are not goal success.'
    }
    with urllib.request.urlopen(api + '/health', timeout=10) as response:
        manifest['health'] = {'http': response.status, 'body': json.loads(response.read())}
    write_json(manifest_path, manifest)
    for language, cases in cases_by_language.items():
        records = []
        with (HERE / language / f'{label}.jsonl').open('x', encoding='utf-8') as log:
            for index, case in enumerate(cases, 1):
                request_body = json.dumps({'query': case['query']}, ensure_ascii=False).encode('utf-8')
                req = urllib.request.Request(api + '/api/v2/query', data=request_body,
                                             headers={'Content-Type': 'application/json'}, method='POST')
                started = time.monotonic()
                record = dict(case)
                record['timestamp_utc'] = datetime.now(timezone.utc).isoformat()
                try:
                    try:
                        response = urllib.request.urlopen(req, timeout=30)
                    except urllib.error.HTTPError as error:
                        response = error
                    with response:
                        record.update(http_status=response.status, actual=json.loads(response.read()))
                except Exception as exc:
                    record.update(http_status=None, actual=None,
                                  transport_error=f'{type(exc).__name__}: {exc}')
                record['round_trip_ms'] = round((time.monotonic() - started) * 1000, 2)
                record['intent_equal_diagnostic'] = (
                    record['actual'].get('intent') == case.get('expected_intent')
                    if record['actual'] and case.get('expected_intent') is not None else None)
                records.append(record)
                log.write(json.dumps(record, ensure_ascii=False) + '\n')
                log.flush()
                if index % 25 == 0:
                    print(f'{label}: {language} {index}/200', flush=True)
        write_json(HERE / language / f'{label}.json', records)
        with (HERE / language / f'{label}.csv').open('x', encoding='utf-8', newline='') as stream:
            columns = ['id', 'query', 'expected_intent', 'expected_operation', 'test_type',
                       'expected_behavior', 'http_status', 'actual_intent', 'actual_operation',
                       'actual_status', 'outcome_reason', 'response_text', 'round_trip_ms', 'actual_json']
            writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
            writer.writeheader()
            for row in records:
                actual = row['actual'] or {}
                export = {key: row.get(key) for key in columns if key in row}
                export.update(actual_intent=actual.get('intent'), actual_operation=actual.get('operation'),
                              actual_status=actual.get('status'), outcome_reason=actual.get('outcome_reason'),
                              response_text=actual.get('response_text'),
                              actual_json=json.dumps(actual, ensure_ascii=False, sort_keys=True))
                writer.writerow(export)
    manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
    manifest['response_sha256'] = {lang: digest(HERE / lang / f'{label}.json') for lang in cases_by_language}
    write_json(manifest_path, manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--api', default='http://127.0.0.1:8875')
    options = parser.parse_args()
    if not options.label.replace('_', '').isalnum():
        parser.error('label must contain only letters, numbers and underscores')
    campaign(options.label, options.api.rstrip('/'))
