"""Synthetic causal attribution controls; no historical evaluation inputs."""
import pytest
from src.nlp_v2.contracts import IntentPrediction


def row(case_id, success, failures=()):
    return {'id': case_id, 'terminal_success': success, 'failures': list(failures)}


def case(case_id, intent='fare_calculation', status='ok'):
    return {'id': case_id, 'intent': intent, 'status': status,
            'language': 'EN', 'noise': 'clean'}


def test_raw_mismatch_attribution_uses_counterfactual_and_excludes_null_intents():
    from scripts.nlp_v2.diagnose_training_need import attribute_failures
    cases = [case('a'), case('b'), case('c'), case('d', None, 'clarification')]
    raw = [IntentPrediction('route_stop_sequence', ('route_stop_sequence',), .9),
           IntentPrediction('fare_calculation', ('fare_calculation',), .9),
           IntentPrediction('route_stop_sequence', ('route_stop_sequence',), .9),
           IntentPrediction('fare_calculation', ('fare_calculation',), .9)]
    actual = [row('a', False), row('b', False), row('c', True), row('d', False)]
    gold = [row('a', True), row('b', False, ('entity_resolution_failure',)),
            row('c', True), row('d', True)]
    result = attribute_failures(cases, raw, actual, gold)
    assert result['raw_single_label_accuracy'] == {'success': 1, 'count': 3, 'rate': 1/3}
    assert result['terminal_failure_partition'] == {
        'classifier_failure_correctable_by_intent': 1,
        'structured_ambiguity_or_guard_failure': 1,
        'residual_downstream_failure': 1,
        'same_raw_intent_counterfactual_divergence': 0,
    }
    assert result['wrong_raw_class_with_successful_terminal'] == 1
    assert result['downstream_failure_flags']['entity_resolution_failure'] == 1
    assert result['cases'][-1]['raw_intent_correct'] is None


def test_same_intent_counterfactual_difference_is_not_claimed_as_model_failure():
    from scripts.nlp_v2.diagnose_training_need import attribute_failures
    result = attribute_failures([case('a')],
        [IntentPrediction('fare_calculation', ('fare_calculation',), .9)],
        [row('a', False)], [row('a', True)])
    assert result['terminal_failure_partition']['same_raw_intent_counterfactual_divergence'] == 1
    assert result['terminal_failure_partition']['classifier_failure_correctable_by_intent'] == 0


@pytest.mark.parametrize('actual,gold', [([], [row('a', True)]),
                                      ([row('b', True)], [row('a', True)])])
def test_attribution_rejects_missing_or_misaligned_records(actual, gold):
    from scripts.nlp_v2.diagnose_training_need import attribute_failures
    with pytest.raises(ValueError):
        attribute_failures([case('a')], [IntentPrediction('fare_calculation', ('fare_calculation',), .9)], actual, gold)


def test_training_decision_output_guard_precedes_model_loading(tmp_path):
    from scripts.nlp_v2.diagnose_training_need import diagnose, ROOT
    (tmp_path/'existing').write_text('synthetic')
    with pytest.raises(ValueError, match='exists'):
        diagnose(tmp_path)
    with pytest.raises(ValueError, match='destination'):
        diagnose(ROOT/'reports/nlp_v2/gate_b2/forbidden')


def test_full_training_refuses_cpu_before_cache_or_artifact_writes(tmp_path, monkeypatch):
    from scripts.nlp_v2 import train_production_t3 as trainer
    monkeypatch.setattr(trainer.torch.cuda, 'is_available', lambda: False)
    def cache_must_not_load(*args, **kwargs):
        raise AssertionError('GPU guard must precede model cache loading')
    monkeypatch.setattr(trainer.AutoTokenizer, 'from_pretrained', cache_must_not_load)
    with pytest.raises(RuntimeError, match='GPU'):
        trainer.train(trainer.TrainConfig(output_dir=tmp_path/'full'))
    assert not (tmp_path/'full').exists()


def test_full_training_propagates_cuda_allocation_failure_without_cpu_fallback(tmp_path, monkeypatch):
    from scripts.nlp_v2 import train_production_t3 as trainer
    monkeypatch.setattr(trainer.torch.cuda, 'is_available', lambda: True)
    def allocation_denied(*args, **kwargs):
        raise RuntimeError('synthetic CUDA allocation denied')
    monkeypatch.setattr(trainer.torch, 'empty', allocation_denied)
    with pytest.raises(RuntimeError, match='allocation denied'):
        trainer.train(trainer.TrainConfig(output_dir=tmp_path/'full'))
    assert not (tmp_path/'full').exists()


def test_overlapping_domain_flags_count_one_case_per_failure_category():
    from scripts.nlp_v2.diagnose_training_need import attribute_failures
    r = attribute_failures([case('a')],
        [IntentPrediction('fare_calculation', ('fare_calculation',), .9)],
        [row('a', False)], [row('a', False, ('evidence_contract_failure',
            'operation_selection_failure', 'domain_code_failure'))])
    assert r['downstream_failure_flags']['domain_code_limitation'] == 1


def test_candidate_diagnosis_uses_explicit_manifest_without_promoting_it(tmp_path, monkeypatch):
    from scripts.nlp_v2 import diagnose_training_need as diagnostic
    candidate = tmp_path/'candidate.json'
    seen = []
    def strict_loader(path):
        seen.append(path)
        raise ValueError('synthetic candidate loader reached')
    monkeypatch.setattr(diagnostic, 'T3IntentClassifier', strict_loader)
    monkeypatch.setattr(diagnostic, 'heldout_fingerprints', lambda *args: set())
    with pytest.raises(ValueError, match='candidate loader reached'):
        diagnostic.diagnose(tmp_path/'output', manifest_path=candidate)
    assert seen == [candidate.resolve()]
    assert not (tmp_path/'output').exists()
