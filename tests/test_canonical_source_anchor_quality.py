"""Source/anchor safety based on independent structural fixtures."""
import sqlite3
import pytest
from src.nlp_v2.entities import CanonicalResolver
from src.nlp_v2.slots import T3SlotExtractor

@pytest.fixture(scope='module')
def resolver():return CanonicalResolver()


@pytest.fixture
def synthetic_resolver(tmp_path):
    path=tmp_path/'canonical.db'
    with sqlite3.connect(path) as c:
        c.executescript("""
        CREATE TABLE transport_hubs(hub_id TEXT,hub_name TEXT);
        CREATE TABLE transport_stops(stop_id TEXT,canonical_name TEXT,mode TEXT);
        CREATE TABLE places(place_id TEXT,canonical_name TEXT);
        CREATE TABLE place_names(place_id TEXT,name TEXT);
        CREATE TABLE stop_names(stop_id TEXT,name TEXT);
        CREATE TABLE transport_routes(route_id TEXT,route_short_name TEXT,mode TEXT,status TEXT);
        CREATE TABLE route_stops(route_id TEXT,canonical_stop_id TEXT);
        INSERT INTO places VALUES('PLACE_MAPLE','Maple Research Institute, Estuary Campus');
        INSERT INTO transport_stops VALUES('BUS_MAPLE','Maple Quay','bus');
        """)
    return CanonicalResolver(path)


def test_campus_suffix_cannot_be_dropped_to_claim_general_institution(synthetic_resolver):
    span=synthetic_resolver.find_spans('Maple Research Institute')[0]
    resolution=synthetic_resolver.resolve(span,'landmark','nearest_transport')
    assert resolution.entity_id is None and resolution.ambiguous
    assert {c.entity_id for c in resolution.candidates}=={'PLACE_MAPLE'}
    assert synthetic_resolver.find_spans('Maple Research Institute Estuary Campus')[0].candidates


def test_unqualified_unique_stop_cannot_be_assumed_to_mean_geographic_locality(synthetic_resolver):
    result=T3SlotExtractor(synthetic_resolver).extract('closest metro station near Maple Quay','nearest_transport')
    assert result.clarification_reason=='entity_ambiguity'
    assert 'landmark' not in result.slots and result.unresolved


def test_source_inferred_rail_mode_is_not_presented_as_verified():
    from src.nlp_v2.domain import CanonicalTransitService
    result=CanonicalTransitService().execute('FIND_NEAREST_STATION',{'landmark':'RAIL_WALAJABAD','transport_mode':'suburban_rail'})
    assert result.status=='unavailable'
    assert result.data['reason']=='requested_mode_classification_unverified'


def test_qualified_stop_still_provides_an_exact_reference(resolver):
    result=T3SlotExtractor(resolver).extract('closest bus stop near Pattaravakkam suburban railway station','nearest_transport')
    assert result.slots['landmark']=='RAIL_PATTARAVAKKAM' and not result.clarification_reason


def test_incomplete_branch_candidates_survive_plain_name_alias_collision(synthetic_resolver):
    with sqlite3.connect(synthetic_resolver.db_path) as c:
        c.execute("INSERT INTO transport_stops VALUES('BUS_INSTITUTE','Maple Research Institute','bus')")
    resolver=CanonicalResolver(synthetic_resolver.db_path)
    span=resolver.find_spans('Maple Research Institute')[0]
    assert span.requires_qualification
    resolution=resolver.resolve(span,'landmark','nearest_transport')
    assert resolution.entity_id is None and resolution.ambiguous
    assert {c.entity_id for c in resolution.candidates}=={'PLACE_MAPLE','BUS_INSTITUTE'}


def test_compact_partial_name_keeps_qualification_and_all_candidates(synthetic_resolver):
    with sqlite3.connect(synthetic_resolver.db_path) as c:
        c.execute("INSERT INTO transport_stops VALUES('BUS_INSTITUTE','Maple Research Institute','bus')")
    resolver=CanonicalResolver(synthetic_resolver.db_path)
    span=resolver.find_spans('MapleResearchInstitute')[0]
    assert span.requires_qualification
    assert {c.entity_id for c in span.candidates}=={'PLACE_MAPLE','BUS_INSTITUTE'}


def test_trailing_comma_is_punctuation_not_an_incomplete_branch(synthetic_resolver):
    with sqlite3.connect(synthetic_resolver.db_path) as c:
        c.execute("INSERT INTO places VALUES('PLACE_CLINIC','Quayside Clinic,')")
    resolver=CanonicalResolver(synthetic_resolver.db_path)
    span=resolver.find_spans('Quayside Clinic')[0]
    assert not span.requires_qualification
    assert resolver.resolve(span,'landmark','nearest_transport').entity_id=='PLACE_CLINIC'
