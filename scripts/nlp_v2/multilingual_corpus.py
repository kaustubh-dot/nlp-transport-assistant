"""Versioned independent multilingual corpus construction and isolation checks.

Frozen queries enter only an opaque exclusion audit; they are never emitted,
used to author forms, or made available to a training/evaluation consumer.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import unicodedata

from src.nlp_v2.model import LABEL_ORDER, sha256_file
from src.nlp_v2.contracts import validate_slots, validate_intent_slots, ENTITY_SLOTS

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / 'data/nlp_v2/multilingual_v1'
PARTITIONS = ('train', 'validation', 'development_test')
LANGUAGES = ('HI_DEVA', 'HI_LATN', 'HINGLISH_LATN', 'EN')


def normalized(value: str) -> str:
    value = unicodedata.normalize('NFC', value).casefold()
    return ' '.join(''.join(c if unicodedata.category(c)[0] in 'LNM' else ' '
                            for c in value).split())


def fingerprint(value: str) -> str:
    return hashlib.sha256(normalized(value).encode()).hexdigest()


def template(value: str, entities: dict) -> str:
    for entity in sorted(entities.values(), key=lambda e: len(e['surface']), reverse=True):
        value = value.replace(entity['surface'], 'ENTITY')
    return re.sub(r'\d+', 'NUMBER', normalized(value))


def audit_rows(rows: list[dict], *, excluded_hashes: set[str] | None = None,
               known_entities: set[str] | None = None) -> dict:
    if not rows:
        raise ValueError('Empty corpus')
    ids, queries, families, semantics, templates = set(), set(), {}, {}, {}
    required = {'id', 'family_id', 'semantic_family_id', 'split', 'query',
                'language_class', 'intent', 'slots', 'entity_expectations',
                'expected_clarification', 'provenance', 'review_method', 'constraints',
                'request_constraints', 'classifier_applicable'}
    for row in rows:
        if not required <= row.keys() or row['split'] not in PARTITIONS:
            raise ValueError('Invalid corpus schema/partition')
        if any(not isinstance(row[k], str) or not row[k].strip()
               for k in ('id', 'family_id', 'semantic_family_id', 'query', 'provenance', 'review_method')):
            raise ValueError('Empty corpus identity/text/provenance')
        if row['language_class'] not in LANGUAGES or row['intent'] not in (*LABEL_ORDER, None):
            raise ValueError('Invalid corpus language/intent')
        if not isinstance(row['slots'], dict):
            raise ValueError('Invalid slots')
        validate_slots(row['slots'])
        if row['intent'] is not None:
            validate_intent_slots(row['intent'], row['slots'])
        if row['expected_clarification'] not in {None, 'missing_slot', 'entity_ambiguity',
                                               'temporal_ambiguity', 'multiple_goals', 'intent_ambiguity'}:
            raise ValueError('Invalid clarification annotation')
        if type(row['classifier_applicable']) is not bool:
            raise ValueError('Invalid classifier applicability')
        if row['intent'] is None and row['classifier_applicable']:
            raise ValueError('Ambiguous gold cannot select a single-label classifier')
        if (not isinstance(row['constraints'], list)
                or not all(isinstance(v, str) for v in row['constraints'])
                or not isinstance(row['request_constraints'], dict)):
            raise ValueError('Invalid constraint gold')
        constraints = row['request_constraints']
        for mode_key in ('required_modes', 'excluded_modes'):
            if mode_key in constraints:
                if not isinstance(constraints[mode_key], list):
                    raise ValueError('Invalid mode constraints')
                for mode in constraints[mode_key]:
                    validate_slots({'transport_mode': mode})
        for key, slot in (('clock', 'time'), ('date', 'date')):
            if key in constraints:
                validate_slots({slot: constraints[key]})
        if 'time_range' in constraints:
            values = constraints['time_range']
            if not isinstance(values, list) or len(values) != 2:
                raise ValueError('A time range requires two bounds')
            for value in values:
                validate_slots({'time': value})
        for goal in constraints.get('goals', []):
            if goal['intent'] not in LABEL_ORDER:
                raise ValueError('Invalid compound goal')
            validate_slots(goal['slots'])
            validate_intent_slots(goal['intent'], goal['slots'])
            if known_entities is not None and {v for k, v in goal['slots'].items()
                                                if k in ENTITY_SLOTS} - known_entities:
                raise ValueError('Unknown canonical entity in compound gold')
        mentioned = {v for k, v in row['slots'].items() if k in ENTITY_SLOTS}
        if not isinstance(row['entity_expectations'], dict):
            raise ValueError('Invalid entity annotations')
        for role, annotation in row['entity_expectations'].items():
            if (role not in ENTITY_SLOTS or not isinstance(annotation, dict)
                    or not isinstance(annotation.get('surface'), str)
                    or not isinstance(annotation.get('canonical_name'), str)
                    or not isinstance(annotation.get('canonical_ids'), list)
                    or not annotation['canonical_ids']):
                raise ValueError('Invalid entity annotation')
            for entity_id in annotation['canonical_ids']:
                validate_slots({role: entity_id})
                mentioned.add(entity_id)
        if known_entities is not None and mentioned - known_entities:
            raise ValueError('Unknown canonical entity in gold')
        if row['id'] in ids:
            raise ValueError('Duplicate id')
        ids.add(row['id'])
        for key, registry in (('family_id', families), ('semantic_family_id', semantics)):
            if registry.setdefault(row[key], row['split']) != row['split']:
                raise ValueError(f'Cross-partition {key} leakage')
        hashed = fingerprint(row['query'])
        if hashed in queries:
            raise ValueError('Normalized duplicate query')
        queries.add(hashed)
        if hashed in (excluded_hashes or set()):
            raise ValueError('Query overlaps excluded observed/historical material')
        skeleton = template(row['query'], row['entity_expectations'])
        if templates.setdefault(skeleton, row['split']) != row['split']:
            raise ValueError('Cross-partition near-template leakage')
    return {'rows': len(rows), 'families': len(families),
            'semantic_families': len(semantics),
            'by_partition': dict(Counter(r['split'] for r in rows)),
            'by_language': dict(Counter(r['language_class'] for r in rows)),
            'by_intent': dict(Counter(r['intent'] or 'ambiguous' for r in rows))}


def expand_registry(registry: dict) -> list[dict]:
    """Expand authored forms/annotations without using production NLP output."""
    rows, seen = [], set()
    def substitute(obj, args):
        if isinstance(obj, str):
            if obj.startswith('{') and obj.endswith('}'):
                return args[obj[1:-1]]
            return obj.format(**args)
        if isinstance(obj, list):
            return [substitute(v, args) for v in obj]
        if isinstance(obj, dict):
            return {k: substitute(v, args) for k, v in obj.items()}
        return obj
    for family in registry['families']:
        for language, form in family['forms'].items():
            for index, values in enumerate(registry['values']):
                catalog = values['canonical_entities']
                args = dict(values['parameters'])
                args.update({symbol: e['hindi_transliteration'] if language == 'HI_DEVA'
                             else e['english_surface'] for symbol, e in catalog.items()})
                gold_args = dict(args)
                # These independently reviewed orthographic variants are stored
                # in the authoring registry, never discovered from failures.
                for symbol in ('O', 'OA', 'P', 'PM'):
                    for canonical, variant in registry['surface_variants'].get(language, {}).items():
                        args[symbol] = args[symbol].replace(canonical, variant)
                if language in registry['native_route_digits_languages']:
                    for symbol in ('R', 'R2'):
                        args[symbol] = ''.join(chr(0x966 + int(c)) if c.isdigit() else c
                                               for c in args[symbol])
                args['ND'] = ''.join(chr(0x966 + int(c)) for c in str(args['N']))
                query = form.format(**args)
                hashed = fingerprint(query)
                if hashed in seen:
                    continue
                seen.add(hashed)
                slots = substitute(family['slot_spec'], gold_args)
                slots.update(family['slot_overrides_by_language'].get(language, {}))
                entities = {}
                overrides = family['entity_candidate_overrides'].get(str(index), {})
                for role, symbol in family['entity_roles'].items():
                    entity = catalog[symbol]
                    ids = overrides.get(role, entity['canonical_ids'])
                    entities[role] = {'surface': args[symbol], 'canonical_name': entity['canonical_name'],
                                      'canonical_ids': ids}
                    if len(ids) == 1:
                        slots[role] = ids[0]
                constraints = substitute(family['constraint_spec'], gold_args)
                for goal in constraints.get('goals', []):
                    for role, symbol in goal.pop('entities', {}).items():
                        goal['slots'][role] = catalog[symbol]['canonical_id']
                ambiguous = any(len(e['canonical_ids']) > 1 for e in entities.values())
                rows.append(dict(
                    id=family['family_id']+'.'+language+'.'+str(index),
                    family_id=family['family_id'], semantic_family_id=family['semantic_family_id'],
                    split=family['split'], language_class=language, query=query, intent=family['intent'],
                    slots=slots, entity_expectations=entities,
                    expected_clarification='entity_ambiguity' if ambiguous else family['expected_clarification'],
                    constraints=family['constraints'], classifier_applicable=family['classifier_applicable'],
                    request_constraints=constraints, variant=index,
                    provenance=family['provenance'], review_method=family['review_method']))
    return rows


def opaque_exclusion_hashes() -> set[str]:
    """Return hashes only, without exposing observed or historical wording."""
    from scripts.nlp_v2.evaluate_development_coverage import heldout_fingerprints
    values = heldout_fingerprints(ROOT/'data/nlp_v2/gate_b2/gate_b2_stress_eval.csv',
                                 ROOT/'data/nlp_v2/gate_b2/human_annotation_key.json')
    observed = ROOT/'reports/nlp_v2/language_400_qa_2026_10_08'
    for language in ('hindi', 'hinglish'):
        values.update(fingerprint(r['query']) for r in
                      json.loads((observed/language/'cases.json').read_text()))
    # The imported historical helper uses legacy punctuation normalization;
    # retain those hashes as an additional guard and independently hash queries.
    import csv
    with (ROOT/'data/nlp_v2/gate_b2/gate_b2_stress_eval.csv').open() as stream:
        values.update(fingerprint(r['query']) for r in csv.DictReader(stream))
    reference = json.loads((ROOT/'data/nlp_v2/gate_b2/human_annotation_key.json').read_text())
    values.update(fingerprint(r['query']) for r in reference.values())
    return values


def load_corpus(partition: str) -> list[dict]:
    if partition not in PARTITIONS:
        raise ValueError('Unknown corpus partition')
    manifest = json.loads((CORPUS/'manifest.json').read_text())
    for name, digest in manifest['sha256'].items():
        if sha256_file(CORPUS/name) != digest:
            raise ValueError('Corpus hash mismatch')
    rows = json.loads((CORPUS/f'{partition}.json').read_text())
    audit_rows(rows)
    if any(r['split'] != partition for r in rows):
        raise ValueError('Corpus partition mismatch')
    return rows


def audit_corpus() -> dict:
    rows = [r for partition in PARTITIONS for r in load_corpus(partition)]
    database = ROOT/'data/canonical/transit/canonical_transport.db'
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True) as conn:
        known = set()
        canonical_names = {}
        for table, identifier, name in (('transport_stops', 'stop_id', 'canonical_name'),
                                       ('transport_hubs', 'hub_id', 'hub_name'),
                                       ('places', 'place_id', 'canonical_name')):
            for entity_id, entity_name in conn.execute(f'SELECT {identifier}, {name} FROM {table}'):
                known.add(entity_id)
                canonical_names[entity_id] = entity_name
    summary = audit_rows(rows, excluded_hashes=opaque_exclusion_hashes(), known_entities=known)
    registry = json.loads((CORPUS/'families.json').read_text())
    families = {f['family_id']: f for f in registry['families']}
    for row in rows:
        family = families[row['family_id']]
        if any(row[k] != family[k] for k in ('split', 'intent', 'semantic_family_id')):
            raise ValueError('Family registry differs from expansion')
        for expectation in row['entity_expectations'].values():
            if any(normalized(canonical_names[entity_id]) != normalized(expectation['canonical_name'])
                   for entity_id in expectation['canonical_ids']):
                raise ValueError('Gold entity name differs from canonical record')
    rebuilt = {r['id']: r for r in expand_registry(registry)}
    if rebuilt != {r['id']: r for r in rows}:
        raise ValueError('Gold/query expansion differs from authored registry')
    for partition in PARTITIONS:
        if {r['intent'] for r in rows if r['split'] == partition} - {None} != set(LABEL_ORDER):
            raise ValueError('Incomplete 16-intent coverage')
    return summary


if __name__ == '__main__':
    print(json.dumps(audit_corpus(), indent=2))
