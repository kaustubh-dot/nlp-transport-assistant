"""Candidate separation and promotion rules, independent of model weights."""
import pytest

def test_reviewed_new_training_excludes_nonapplicable_compounds():
    from scripts.nlp_v2.train_multilingual import training_material
    train,oldval,newval=training_material()
    assert len(train)==1396+458 and len(oldval)==332 and len(newval)==108
    assert all(r['T3_label'] for r in train)
    assert {r['source'] for r in train}=={'original_train','multilingual_train'}
    assert not {r['query'] for r in newval}&{r['query'] for r in train}


def test_promotion_rejects_minority_class_regression_despite_aggregate_gain():
    from scripts.nlp_v2.train_multilingual import promotion_decision
    def group(count,accuracy,f1,support=3,recall=1):
        return {'count':count,'accuracy':accuracy,'macro_f1':f1,'per_class':{'service_frequency':{'support':support,'recall':recall}}}
    baseline={'new':group(108,.5,.4),'old':group(332,.9,.85),'old_languages':{'EN':group(45,.8,.7)},'new_languages':{'HI_DEVA':group(27,.4,.3)}}
    candidate={'new':group(108,.8,.7),'old':group(332,.92,.86,recall=2/3),'old_languages':{'EN':group(45,.82,.72)},'new_languages':{'HI_DEVA':group(27,.8,.7)}}
    result=promotion_decision(baseline,candidate)
    assert not result['eligible'] and any('service_frequency' in reason for reason in result['failures'])


def test_candidate_output_cannot_overwrite_baseline_checkpoint():
    from scripts.nlp_v2.train_multilingual import validate_candidate_output
    with pytest.raises(ValueError):validate_candidate_output('experiments/nlp_v2/gate_b2')


def test_promotion_blocks_minority_precision_collapse_with_same_recall():
    from copy import deepcopy
    from scripts.nlp_v2.train_multilingual import promotion_decision
    group={'count':100,'accuracy':.9,'macro_f1':.9,'macro_f1_supported_classes':.9,'per_class':{'mode_availability':{'support':4,'recall':1.,'f1':1.}}}
    baseline={'new':deepcopy(group),'old':deepcopy(group),'old_languages':{'EN':deepcopy(group)},'new_languages':{'HI_DEVA':deepcopy(group)}}
    baseline['new']['macro_f1']=.4
    candidate=deepcopy(baseline);candidate['new']['macro_f1']=.6;candidate['old']['macro_f1']=.895;candidate['old']['per_class']['mode_availability']['f1']=.36
    decision=promotion_decision(baseline,candidate)
    assert not decision['eligible'] and 'old:mode_availability per-class F1 regression' in decision['failures']
