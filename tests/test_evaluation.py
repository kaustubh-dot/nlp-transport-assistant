import pandas as pd
import pytest
from scripts.generate_intent_dataset import generate_dataset
from scripts.evaluate import validate_splits


def test_generated_families_never_cross_splits():
    df = generate_dataset(200)
    validate_splits(df)
    assert set(df.split) == {'train','val','test'}
    assert df.groupby('intent')['split'].nunique().eq(3).all()
    pairs = df.dropna(subset=['origin','destination'])
    assert (pairs.origin != pairs.destination).all()
    assert not df.slots_reviewed.any()
    pd.testing.assert_frame_equal(df, generate_dataset(200))


def test_rejects_family_leakage():
    df = pd.DataFrame({'query':['a','b','c'], 'intent':['route_query']*3,
                       'template_family':['same']*3, 'split':['train','val','test']})
    with pytest.raises(ValueError, match='family leakage'):
        validate_splits(df)


def test_rejects_absent_holdout():
    df = pd.DataFrame({'query':['a'], 'intent':['route_query'], 'template_family':['one'], 'split':['train']})
    with pytest.raises(ValueError, match='splits are required'):
        validate_splits(df)


def test_evaluator_refuses_untrained_fallback(monkeypatch, tmp_path):
    import scripts.evaluate as evaluation
    from src.intent_classifier import TfidfBaselineClassifier
    path = tmp_path / 'intents.csv'
    generate_dataset(200).to_csv(path, index=False)
    monkeypatch.setattr(evaluation, 'INTENTS_CSV', path)
    monkeypatch.setattr(evaluation, 'get_classifier', lambda _: TfidfBaselineClassifier(str(tmp_path / 'missing.pkl')))
    with pytest.raises(ValueError, match='refusing to benchmark'):
        evaluation.evaluate_system()
