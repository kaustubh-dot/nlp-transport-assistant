"""Independent English counterparts across T3 operations and the public API."""
import json
from pathlib import Path
import pytest
from app.api import handle_request
from scripts.nlp_v2.evaluate_multilingual import FixedClassifier
from src.nlp_v2.assistant import T3Assistant
from src.nlp_v2.entities import CanonicalResolver
from src.nlp_v2.slots import T3SlotExtractor

CASES=json.loads((Path(__file__).resolve().parents[1]/'data/nlp_v2/remediation_v2/english.json').read_text())['cases']
@pytest.fixture(scope='module')
def extractor():
    return T3SlotExtractor(CanonicalResolver())

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id']+'-'+c['expected_intent'])
def test_english_semantic_contract_and_public_api(extractor,case):
    query=case['query'];intent=case['expected_intent']
    assistant=T3Assistant(classifier=FixedClassifier(intent),extractor=extractor,resolver=extractor.resolver)
    extraction=extractor.extract(query,intent,default_transport_mode=case['default_mode'])
    for name,value in case['expected_slots'].items():
        assert extraction.slots.get(name)==value
    reply=assistant.process_query(query,default_transport_mode=case['default_mode'])
    assert reply.raw_query==query and reply.status==case['expected_status']
    payload={'query':query}
    if case['default_mode'] is not None:payload['transport_mode']=case['default_mode']
    encoded=json.dumps(payload).encode()
    status,body=handle_request('POST','/api/v2/query',{'Content-Type':'application/json','Content-Length':str(len(encoded))},encoded,assistant)
    assert status==200 and body['status']==reply.status
    assert body['slots']==reply.slots and body['data']==reply.data
    assert 'raw_query' not in body and 'normalized_query' not in body

@pytest.mark.parametrize('predicted',['route_stop_sequence','fare_calculation','scheduled_departure','nearest_transport'])
def test_english_public_api_rejects_conflicting_membership_operation(extractor,predicted):
    query="Isn't bus 54 stopping at Poonamallee Bus Terminus please?"
    assistant=T3Assistant(classifier=FixedClassifier(predicted),extractor=extractor,resolver=extractor.resolver)
    encoded=json.dumps({'query':query}).encode()
    status,body=handle_request('POST','/api/v2/query',{'Content-Type':'application/json','Content-Length':str(len(encoded))},encoded,assistant)
    assert status==200 and body['status']=='clarification'
    assert body['operation'] is None and body['data']['reason']=='predicted_operation_conflict'
