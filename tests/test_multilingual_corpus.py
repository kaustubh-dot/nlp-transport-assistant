"""Corpus isolation guards exercised using independently authored toy records."""

import pytest


def row(identifier, family, split, query, semantic=None):
    return dict(id=identifier, family_id=family, semantic_family_id=semantic or family,
                split=split, query=query, language_class='HI_LATN',
                intent='fare_calculation', slots={'stage_number': 12},
                entity_expectations={}, expected_clarification=None,
                constraints=[], request_constraints={'tags': []},
                classifier_applicable=True,
                provenance='canonical T3 contract, independent authoring',
                review_method='manual template and expanded-row review')


def test_corpus_rejects_translated_family_crossing_partitions():
    from scripts.nlp_v2.multilingual_corpus import audit_rows

    records = [row('a', 'frame-a', 'train', 'Sadharan bus ka barah stage bhada'),
               row('b', 'frame-b', 'validation', 'Ordinary bus stage twelve cost',
                   semantic='frame-a')]
    with pytest.raises(ValueError, match='semantic'):
        audit_rows(records)


def test_corpus_rejects_normalized_duplicates_and_frozen_fingerprints():
    from scripts.nlp_v2.multilingual_corpus import audit_rows, fingerprint

    records = [row('a', 'a', 'train', 'Bus BARAH stage!'),
               row('b', 'b', 'validation', 'bus barah stage')]
    with pytest.raises(ValueError, match='duplicate'):
        audit_rows(records)
    with pytest.raises(ValueError, match='excluded'):
        audit_rows(records[:1], excluded_hashes={fingerprint('bus barah stage')})


def test_corpus_rejects_near_template_leakage_even_with_new_ids():
    from scripts.nlp_v2.multilingual_corpus import audit_rows

    records = [row('a', 'a', 'train', 'Please tell me the ordinary bus fare for stage 12'),
               row('b', 'b', 'validation', 'Please tell me the ordinary bus fare for stage 18')]
    with pytest.raises(ValueError, match='template'):
        audit_rows(records)


def test_corpus_accepts_independent_constructions_and_preserves_annotations():
    from scripts.nlp_v2.multilingual_corpus import audit_rows

    records = [row('a', 'a', 'train', 'Sadharan bus ka barah stage bhada'),
               row('b', 'b', 'validation', 'AC service mein stage 18 ke paise kitne')]
    assert audit_rows(records)['rows'] == 2
    assert records[0]['slots'] == {'stage_number': 12}


@pytest.mark.parametrize('field,value', [
    ('slots', {'stage_number': 0}),
    ('slots', {'transport_mode': 'balloon'}),
    ('expected_clarification', 'invented_reason'),
    ('classifier_applicable', 'yes'),
    ('request_constraints', {'time_range': ['10:00:00']}),
    ('request_constraints', {'required_modes': ['balloon']}),
    ('request_constraints', {'clock': '29:00:00'}),
])
def test_corpus_rejects_invalid_annotations(field, value):
    from scripts.nlp_v2.multilingual_corpus import audit_rows

    record = row('a', 'a', 'train', 'Sadharan bus ka barah stage bhada')
    record[field] = value
    with pytest.raises(ValueError):
        audit_rows([record])


def test_corpus_rejects_unknown_canonical_entities():
    from scripts.nlp_v2.multilingual_corpus import audit_rows

    record = row('a', 'a', 'train', 'Unknown pier ka bhada')
    record['slots'] = {'origin': 'PLACE_INVENTED'}
    with pytest.raises(ValueError, match='entity'):
        audit_rows([record], known_entities={'PLACE_REAL'})


def test_reviewed_corpus_expansion_and_gold_are_reproducible():
    import json
    from scripts.nlp_v2.multilingual_corpus import CORPUS, expand_registry, load_corpus

    rebuilt = expand_registry(json.loads((CORPUS / 'families.json').read_text()))
    saved = [r for split in ('train', 'validation', 'development_test')
             for r in load_corpus(split)]
    assert {r['id']: r for r in rebuilt} == {r['id']: r for r in saved}
