"""Independent correctness of evaluation aggregation."""
import pytest

def test_wrong_entity_and_dropped_constraint_do_not_score_as_correct():
    from scripts.nlp_v2.evaluate_multilingual import score_extraction
    from src.nlp_v2.slots import ExtractionResult
    row={'slots':{'origin':'RAIL_A','time':'09:00:00'},'entity_expectations':{'origin':{'canonical_ids':['RAIL_A']}},'request_constraints':{'excluded_modes':['bus']},'expected_clarification':None}
    result=ExtractionResult({'origin':'RAIL_B'},(),(),None,(),'q')
    metrics=score_extraction(row,result)
    assert metrics['slot_correct']==0 and metrics['slot_total']==2
    assert metrics['entity_correct']==0 and metrics['entity_total']==1
    assert metrics['constraint_correct']==0 and metrics['constraint_total']==1


def test_ambiguity_requires_exact_real_candidate_set():
    from scripts.nlp_v2.evaluate_multilingual import score_extraction
    from src.nlp_v2.entities import EntityCandidate,Resolution
    from src.nlp_v2.slots import ExtractionResult
    row={'slots':{},'entity_expectations':{'station':{'canonical_ids':['STOP_A','STOP_B']}},'request_constraints':{},'expected_clarification':'entity_ambiguity'}
    result=ExtractionResult({},(),(Resolution(None,(EntityCandidate('STOP_A','stop'),),True),),'entity_ambiguity',(),'q')
    assert score_extraction(row,result)['entity_correct']==0


def test_classifier_metrics_exclude_nonapplicable_compounds():
    from scripts.nlp_v2.evaluate_multilingual import classification_metrics
    rows=[{'intent':'fare_calculation','classifier_applicable':True},{'intent':None,'classifier_applicable':False}]
    metrics=classification_metrics(rows,['fare_calculation','out_of_scope'])
    assert metrics['count']==1 and metrics['accuracy']==1


def test_invented_extra_slot_prevents_exact_extraction_score():
    from scripts.nlp_v2.evaluate_multilingual import score_extraction
    from src.nlp_v2.slots import ExtractionResult
    row={'slots':{'destination':'STOP_B'},'entity_expectations':{},'request_constraints':{}}
    result=ExtractionResult({'origin':'STOP_A','destination':'STOP_B'},(),(),None,(),'q')
    score=score_extraction(row,result)
    assert score['slot_correct']==1 and score['slot_exact']==0 and score['unexpected_slot_values']==1


def test_expected_clarification_ok_is_failure_not_source_mask_and_null_is_counted():
    from scripts.nlp_v2.evaluate_multilingual import clarification_metrics
    records=[{'injected':{'status':'ok','clarification_reason':None,'data':{}},'actual':{},'expected_clarification':'multiple_goals'},
             {'injected':None,'actual':{'status':'clarification','clarification_reason':'intent_ambiguity','data':{}},'expected_clarification':'intent_ambiguity'}]
    result=clarification_metrics(records)
    assert result['assessed']==2 and result['matches_authored_state']==1 and result['source_preflight_masked']==0


def test_reversed_time_bounds_do_not_score_as_preserved_constraint():
    from scripts.nlp_v2.evaluate_multilingual import score_extraction
    from src.nlp_v2.slots import ExtractionResult
    row={'slots':{},'entity_expectations':{},'request_constraints':{'time_range':['08:00:00','10:00:00']}}
    result=ExtractionResult({},(),(),None,(),'q',request_constraints={'time_range':['10:00:00','08:00:00']})
    assert score_extraction(row,result)['constraint_correct']==0
