"""Independent canonical-name and synthetic Unicode safety regressions."""
import unicodedata
import pytest
from src.nlp_v2.entities import CanonicalResolver

@pytest.fixture(scope='module')
def resolver():
    return CanonicalResolver()

@pytest.mark.parametrize('surface,name', [
 ('पट्टरवाक्कम','Pattaravakkam'), ('वालाजाबाद','Walajabad'),
 ('चेन्नई बीच','Chennai Beach'), ('नेहरू पार्क','Nehru Park'),
 ('नेहरूपार्क','Nehru Park'), ('pattaravakam','Pattaravakkam'),
 ('अडयार','Adyar'), ('नुंगम्बाक्कम','Nungambakkam'),
])
def test_reviewed_transliterations_preserve_exact_candidate_set(resolver,surface,name):
    assert {c.entity_id for c in resolver.find_spans(surface)[0].candidates} == {c.entity_id for c in resolver.find_spans(name)[0].candidates}


def test_mode_qualified_devanagari_excludes_other_modes(resolver):
    span=resolver.find_spans('नेहरू पार्क मेट्रो स्टेशन')[0]
    assert span.surface == 'नेहरू पार्क मेट्रो स्टेशन'
    assert {c.mode for c in span.candidates} == {'metro'}
    assert len(resolver.find_spans('नेहरू पार्क')[0].candidates) > 1


def test_spacing_variant_keeps_ambiguity(resolver):
    assert {c.entity_id for c in resolver.find_spans('Nehrupark')[0].candidates} == {c.entity_id for c in resolver.find_spans('Nehru Park')[0].candidates}


def test_unicode_normalization_keeps_nuqta_and_combining_marks():
    from src.nlp_v2.text import normalize_extraction_text
    assert normalize_extraction_text('फ़ज़ल, नहीं।') == unicodedata.normalize('NFC','फ़ज़ल नहीं')
    assert normalize_extraction_text('फजल') != normalize_extraction_text('फ़ज़ल')


def test_candidate_descriptions_are_real_canonical_rows(resolver):
    ids=[c.entity_id for c in resolver.find_spans('Nehru Park')[0].candidates]
    rows=resolver.describe_candidates(ids)
    assert {r['entity_id'] for r in rows} == set(ids)
    assert all(r['canonical_name']=='Nehru Park' and r['kind']=='stop' for r in rows)
    assert {r['mode'] for r in rows} >= {'metro','bus'}
    assert resolver.describe_candidates(['INVENTED']) == []

def test_ambiguous_reply_lists_canonical_names_modes_and_ids(resolver):
    from src.nlp_v2.assistant import T3Assistant
    from src.nlp_v2.contracts import IntentPrediction
    class Classifier:
        def predict(self,query):
            return IntentPrediction('route_stop_membership',('route_stop_membership',),0.9)
    reply=T3Assistant(classifier=Classifier(),resolver=resolver).process_query('Does bus route 9999 stop at Nehru Park?')
    assert reply.clarification_reason == 'entity_ambiguity'
    assert reply.data['entity_candidates']
    assert all(r['entity_id'] in reply.candidate_entities for r in reply.data['entity_candidates'])
    assert 'Nehru Park' in reply.response_text and 'bus' in reply.response_text


def test_qualified_spacing_variants_keep_full_final_collision_set(resolver):
    spaced=resolver.find_spans('Bharathi Nagar Bus Stop')[0]
    compact=resolver.find_spans('BharathiNagarBusStop')[0]
    assert {c.entity_id for c in spaced.candidates} == {c.entity_id for c in compact.candidates}
    assert len(compact.candidates)>1
