"""Read-only raw-classifier/counterfactual development and validation diagnosis."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import subprocess

from scripts.nlp_v2.evaluate_development_coverage import (
    ROOT, SUITE, MANIFEST, fingerprint, heldout_fingerprints, load_suite, score_cases,
)
from scripts.nlp_v2.train_production_t3 import (
    TRAIN_PATH, TRAIN_SHA256, VALIDATION_PATH, VALIDATION_SHA256, load_training_splits,
)
from src.nlp_v2.assistant import T3Assistant
from src.nlp_v2.contracts import IntentPrediction, validate_prediction
from src.nlp_v2.domain import CanonicalTransitService
from src.nlp_v2.entities import DEFAULT_DB
from src.nlp_v2.model import (
    DEFAULT_MANIFEST, LABEL_ORDER, T3IntentClassifier, load_manifest, sha256_file,
)


def metric(success: int, count: int) -> dict:
    return {'success': success, 'count': count, 'rate': success / count if count else None}


def classification_metrics(gold: list[str], predicted: list[str]) -> dict:
    from sklearn.metrics import confusion_matrix, f1_score
    if not gold or len(gold) != len(predicted):
        raise ValueError('Empty or unaligned classifier records')
    if any(label not in LABEL_ORDER for label in gold + predicted):
        raise ValueError('Classifier records must use frozen T3 labels')
    return {
        'accuracy': metric(sum(a == b for a, b in zip(gold, predicted)), len(gold)),
        'macro_f1': float(f1_score(gold, predicted, labels=list(LABEL_ORDER), average='macro', zero_division=0)),
        'label_order': list(LABEL_ORDER),
        'confusion_matrix_gold_rows_predicted_columns': confusion_matrix(gold, predicted, labels=list(LABEL_ORDER)).tolist(),
        'per_intent': {label: metric(sum(a == label and a == b for a, b in zip(gold, predicted)), gold.count(label))
                       for label in LABEL_ORDER},
    }


def attribute_failures(cases: list[dict], predictions: list[IntentPrediction],
                       actual: list[dict], gold: list[dict]) -> dict:
    """Partition terminal failures; raw wrong classes can be recovered by guards."""
    if not cases or not len(cases) == len(predictions) == len(actual) == len(gold):
        raise ValueError('Empty or unaligned diagnosis records')
    partition = Counter({key: 0 for key in (
        'classifier_failure_correctable_by_intent', 'structured_ambiguity_or_guard_failure',
        'residual_downstream_failure', 'same_raw_intent_counterfactual_divergence',
    )})
    downstream = Counter({key: 0 for key in (
        'slot_extraction_failure', 'entity_resolution_failure',
        'clarification_policy_failure', 'domain_code_limitation',
    )})
    rows, correct, count, recovered = [], 0, 0, 0
    for c, p, a, g in zip(cases, predictions, actual, gold):
        if c['id'] != a['id'] or c['id'] != g['id']:
            raise ValueError('Misaligned diagnosis case IDs')
        validate_prediction(p)
        raw_correct = p.primary_label == c['intent'] if c['intent'] is not None else None
        if raw_correct is not None:
            correct += raw_correct
            count += 1
            recovered += not raw_correct and a['terminal_success']
        category = None
        if not a['terminal_success']:
            if not g['terminal_success']:
                category = 'residual_downstream_failure'
            elif raw_correct is False:
                category = 'classifier_failure_correctable_by_intent'
            elif raw_correct is None:
                category = 'structured_ambiguity_or_guard_failure'
            else:
                category = 'same_raw_intent_counterfactual_divergence'
            partition[category] += 1
        if not g['terminal_success']:
            case_flags = set()
            for flag in set(g['failures']):
                if flag in downstream:
                    case_flags.add(flag)
                elif flag in {'evidence_contract_failure', 'operation_selection_failure', 'domain_code_failure'}:
                    case_flags.add('domain_code_limitation')
            downstream.update(case_flags)
        rows.append({'id': c['id'], 'language': c['language'], 'noise': c['noise'],
                     'gold_intent': c['intent'], 'raw_intent': p.primary_label,
                     'raw_intent_correct': raw_correct, 'actual_terminal_success': a['terminal_success'],
                     'gold_intent_terminal_success': g['terminal_success'], 'failure_partition': category,
                     'downstream_failure_flags': g['failures'] if not g['terminal_success'] else []})
    return {'raw_single_label_accuracy': metric(correct, count),
            'null_intent_contract_count_excluded_from_raw_accuracy': len(cases) - count,
            'terminal_failure_partition': dict(partition),
            'downstream_failure_flags': dict(downstream),
            'wrong_raw_class_with_successful_terminal': recovered, 'cases': rows}


def diagnose(output_dir: Path, *, manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    output_dir = Path(output_dir).resolve()
    if output_dir.is_relative_to(ROOT) and not output_dir.is_relative_to(ROOT/'reports/nlp_v2/training_decision'):
        raise ValueError('Diagnosis output destination must be dedicated reports or outside repo')
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError('Diagnosis output exists')
    cases = load_suite()
    suite_manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if sha256_file(DEFAULT_DB) != suite_manifest['canonical_database_sha256']:
        raise ValueError('Canonical DB hash mismatch')
    if sha256_file(TRAIN_PATH) != TRAIN_SHA256 or sha256_file(VALIDATION_PATH) != VALIDATION_SHA256:
        raise ValueError('Train/validation hash mismatch')
    heldout = heldout_fingerprints(ROOT/'data/nlp_v2/gate_b2/gate_b2_stress_eval.csv',
                                   ROOT/'data/nlp_v2/gate_b2/human_annotation_key.json')
    if any(fingerprint(c['query']) in heldout for c in cases):
        raise ValueError('Development overlaps held-out normalized fingerprints')
    manifest_path = Path(manifest_path).resolve()
    classifier = T3IntentClassifier(manifest_path)
    class FixedPrediction:
        prediction = None
        def predict(self, query):
            return self.prediction
    replay = FixedPrediction()
    assistant = T3Assistant(classifier=replay, service=CanonicalTransitService(
        reference_date=date.fromisoformat(suite_manifest['reference_date'])))
    predictions, replies, counterfactual = [], [], []
    for c in cases:
        p = classifier.predict(c['query'])
        predictions.append(p)
        replay.prediction = p
        replies.append(assistant.process_query(c['query']))
        replay.prediction = (IntentPrediction(c['intent'], (c['intent'],), 1.) if c['intent'] is not None
                             else IntentPrediction(None, tuple(c['candidate_intents']), 1., c['clarification_reason']))
        counterfactual.append(assistant.process_query(c['query']))
    actual_scores, gold_scores = score_cases(cases, replies), score_cases(cases, counterfactual)
    attribution = attribute_failures(cases, predictions, actual_scores['cases'], gold_scores['cases'])
    single = [(c, p) for c, p in zip(cases, predictions) if c['intent'] is not None]
    train, validation = load_training_splits(TRAIN_PATH, VALIDATION_PATH, exclude_overlaps=True)
    validation_predicted = [classifier.predict(r['query']).primary_label for r in validation]
    import torch
    report = {
        'evaluation_type': 'development_and_allowed_validation_training_decision',
        'git_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        'suite_sha256': sha256_file(SUITE), 'canonical_database_sha256': sha256_file(DEFAULT_DB),
        'model_manifest_sha256': sha256_file(manifest_path), 'checkpoint_sha256': load_manifest(manifest_path)['checkpoint_sha256'],
        'train_sha256': TRAIN_SHA256, 'validation_sha256': VALIDATION_SHA256,
        'reference_date': suite_manifest['reference_date'], 'normalized_heldout_overlap': 0,
        'source_hashes': {str(p.relative_to(ROOT)): sha256_file(p) for p in sorted([
            *(ROOT/'src/nlp_v2').glob('*.py'), ROOT/'src/normalization.py', ROOT/'src/entity_extractor.py',
            ROOT/'scripts/nlp_v2/evaluate_development_coverage.py',
            ROOT/'scripts/nlp_v2/train_production_t3.py', Path(__file__).resolve()])},
        'development_raw_classifier': classification_metrics([c['intent'] for c,p in single], [p.primary_label for c,p in single]),
        'development_raw_by_language': {language: classification_metrics(
            [c['intent'] for c,p in single if c['language'] == language],
            [p.primary_label for c,p in single if c['language'] == language]) for language in sorted({c['language'] for c,p in single})},
        'development_raw_by_noise': {noise: classification_metrics(
            [c['intent'] for c,p in single if c['noise'] == noise],
            [p.primary_label for c,p in single if c['noise'] == noise]) for noise in sorted({c['noise'] for c,p in single})},
        'actual_assistant': actual_scores, 'gold_intent_counterfactual': gold_scores, 'attribution': attribution,
        'correct_expected_unavailable_by_intent': dict(sorted(Counter(c['intent'] for c,g in zip(cases, gold_scores['cases'])
            if c['status'] == 'unavailable' and g['terminal_success']).items())),
        'disjoint_validation': {**classification_metrics([r['T3_label'] for r in validation], validation_predicted),
            'train_rows': len(train), 'validation_rows_used': len(validation),
            'filter': 'exclude_train_family_semantic_family_and_exact_casefolded_query_overlap'},
        'hardware': {'torch_version': torch.__version__, 'cuda_runtime': torch.version.cuda,
                     'cuda_available': torch.cuda.is_available(), 'gpu_count': torch.cuda.device_count(),
                     'model_parameter_count': sum(p.numel() for p in classifier.model.parameters())},
        'limitations': [
            'Observed development/validation are not untouched test estimates; no held-out evaluation ran.',
            'Correct-intent counterfactual measures downstream reachability, not expected training gain.',
            'Null-intent contracts are excluded from single-label model accuracy and tested as guard contracts.',
            'Residual downstream flags overlap; policy/gold divergence is not automatically a production defect.',
            'Correct unavailable responses are data/scope/external limitations, not failures or current absence claims.',
            'Frozen original phase coverage classifier_accuracy_measured metadata and classifier_failure flags refer to reply intent; use this raw trace for model diagnosis.',
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/'diagnosis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'raw_accuracy': attribution['raw_single_label_accuracy'],
                      'failure_partition': attribution['terminal_failure_partition'],
                      'validation_macro_f1': report['disjoint_validation']['macro_f1'],
                      'hardware': report['hardware']}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST,
                        help='Strict T3 candidate manifest for assessment without production promotion')
    args = parser.parse_args()
    diagnose(args.output_dir, manifest_path=args.manifest)


if __name__ == '__main__':
    main()
