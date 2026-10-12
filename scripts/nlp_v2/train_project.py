"""One bounded experiment: TF-IDF versus MuRIL with its last two layers fine-tuned."""
from __future__ import annotations

import argparse
import csv
import json
import pickle
import random
from pathlib import Path

from src.hindi_project.model import LABELS, ROOT
from src.hindi_project.artifacts import sha256_file
from src.hindi_project.encoder import MuRILEncoder


def load_rows(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open()))
    if not rows or any(not row['text'].strip() or not row['family_id'].strip()
                       or row['intent'] not in LABELS or row['split'] not in {'train', 'validation', 'test'} for row in rows):
        raise ValueError('Invalid project dataset')
    seen, families = set(), {}
    for row in rows:
        if row['text'] in seen:
            raise ValueError('Duplicate question')
        seen.add(row['text'])
        if families.setdefault(row['family_id'], row['split']) != row['split']:
            raise ValueError('A template family crosses dataset splits')
    if any({row['intent'] for row in rows if row['split'] == split} != set(LABELS)
           for split in ('train', 'validation', 'test')):
        raise ValueError('Every split must cover every intent')
    return rows


def scores(expected, predicted) -> dict:
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    if not expected or len(expected) != len(predicted) or any(label not in LABELS for label in [*expected, *predicted]):
        raise ValueError('Metrics require equal nonempty sequences of project labels')
    report = classification_report(expected, predicted, labels=LABELS, output_dict=True, zero_division=0)
    return {'count': len(expected), 'accuracy': accuracy_score(expected, predicted),
            'macro_f1': report['macro avg']['f1-score'], 'per_class': {label: report[label] for label in LABELS},
            'confusion_matrix': confusion_matrix(expected, predicted, labels=LABELS).tolist()}


def main():
    import numpy as np
    import torch
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/project/hindi_intents.csv')
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--pooling', choices=['mean', 'pooler'], default='mean')
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error('--epochs must be positive')
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(4)
    rows = load_rows(args.dataset)
    partitions = {split: [row for row in rows if row['split'] == split]
                  for split in ('train', 'validation', 'test')}
    output = ROOT / 'models/project'
    output.mkdir(parents=True, exist_ok=True)
    baseline = Pipeline([('tfidf', TfidfVectorizer(analyzer='char', ngram_range=(2, 5), sublinear_tf=True)),
                         ('classifier', LogisticRegression(C=4, max_iter=1000, random_state=42))])
    train = partitions['train']
    baseline.fit([row['text'] for row in train], [row['intent'] for row in train])
    print('TF-IDF trained. Fine-tuning the final two MuRIL layers and nine-class head…', flush=True)
    base = MuRILEncoder()
    for parameter in base.model.parameters():
        parameter.requires_grad_(False)
    layers = base.model.encoder.layer
    for layer in layers[-2:]:
        for parameter in layer.parameters():
            parameter.requires_grad_(True)
    tokens = {split: base.tokenizer([row['text'] for row in part], padding='max_length',
                                   truncation=True, max_length=base.max_length, return_tensors='pt')
              for split, part in partitions.items()}
    targets = {split: torch.tensor([LABELS.index(row['intent']) for row in part])
               for split, part in partitions.items()}
    head = torch.nn.Linear(base.model.config.hidden_size, len(LABELS))
    optimizer = torch.optim.AdamW([
        {'params': [p for layer in layers[-2:] for p in layer.parameters()], 'lr': 5e-5},
        {'params': list(head.parameters()), 'lr': 1e-3}], weight_decay=0.01)
    best_f1, best_epoch, best_state, best_encoder = -1.0, 0, None, None
    def forward(encoded):
        result = base.model(**encoded)
        mask = encoded['attention_mask'].unsqueeze(-1)
        representation = ((result.last_hidden_state * mask).sum(1) / mask.sum(1)
                          if args.pooling == 'mean' else result.pooler_output)
        return head(representation)

    def predict(split):
        base.model.eval()
        head.eval()
        result = []
        with torch.no_grad():
            for start in range(0, len(partitions[split]), 16):
                encoded = {key: value[start:start + 16] for key, value in tokens[split].items()}
                result.extend(forward(encoded).argmax(-1).tolist())
        return [LABELS[index] for index in result]

    for epoch in range(1, args.epochs + 1):
        # Frozen layers retain deterministic features; dropout trains only in the adapted layers.
        base.model.eval()
        for layer in layers[-2:]:
            layer.train()
        head.train()
        order = torch.randperm(len(train))
        total_loss = 0.0
        for start in range(0, len(train), 16):
            indices = order[start:start + 16]
            encoded = {key: value[indices] for key, value in tokens['train'].items()}
            optimizer.zero_grad()
            loss = torch.nn.functional.cross_entropy(forward(encoded), targets['train'][indices])
            loss.backward()
            torch.nn.utils.clip_grad_norm_([p for group in optimizer.param_groups for p in group['params']], 1.0)
            optimizer.step()
            total_loss += float(loss.detach()) * len(indices)
        prediction = predict('validation')
        value = scores([row['intent'] for row in partitions['validation']], prediction)['macro_f1']
        print(f'Epoch {epoch}/{args.epochs}: loss={total_loss / len(train):.4f}, validation macro F1={value:.4f}', flush=True)
        if value > best_f1:
            best_f1, best_epoch = value, epoch
            best_state = {name: tensor.detach().clone() for name, tensor in head.state_dict().items()}
            best_encoder = {str(index): {name: value.detach().clone() for name, value in layers[index].state_dict().items()}
                            for index in (10, 11)}
    head.load_state_dict(best_state)
    head.eval()
    for index, state in best_encoder.items():
        layers[int(index)].load_state_dict(state)
    base.model.eval()
    head_path = output / 'intent_head.pt'
    torch.save(head.state_dict(), head_path)
    encoder_path = ROOT / 'models/assets/encoder_last_two.pt'
    torch.save(best_encoder, encoder_path)
    with (output / 'tfidf.pkl').open('wb') as stream:
        pickle.dump(baseline, stream)
    original = json.loads((ROOT / 'models/hindi_project_manifest.json').read_text())
    manifest = {**original, 'labels': list(LABELS), 'model': 'MuRIL last two encoder layers + nine-class head',
                'training_mode': 'last_two_encoder_layers_and_head',
                'encoder_patch_path': str(encoder_path.relative_to(ROOT)), 'encoder_patch_sha256': sha256_file(encoder_path),
                'head_path': str(head_path.relative_to(ROOT)), 'head_sha256': sha256_file(head_path),
                'dataset_path': str(args.dataset.resolve().relative_to(ROOT)), 'dataset_sha256': sha256_file(args.dataset),
                'preprocessing': 'raw_query', 'max_length': base.max_length, 'seed': 42,
                'pooling': args.pooling,
                'epochs': args.epochs, 'selected_epoch': best_epoch, 'selection': 'validation_macro_f1_only',
                'baseline_path': str((output / 'tfidf.pkl').relative_to(ROOT)),
                'baseline_sha256': sha256_file(output / 'tfidf.pkl')}
    manifest['languages'] = ['hi', 'hinglish']
    manifest['encoder_learning_rate'] = 5e-5
    manifest['head_learning_rate'] = 1e-3
    manifest['batch_size'] = 16
    manifest['trainable_encoder_layers'] = [10, 11]
    (ROOT / 'models/hindi_project_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    metrics = {'labels': list(LABELS), 'data_origin': 'synthetic templates and AI-authored development examples; not human reviewed',
               'split_policy': 'template family disjoint', 'training_mode': manifest['training_mode'],
               'limitations': ['Small synthetic academic comparison, not passenger accuracy.',
                               'The reused encoder was previously fine-tuned on transport data; this is not a new base-model benchmark.',
                               'Only the final two encoder layers and nine-class head are trained; this is partial fine-tuning.',
                               'Classification scores do not measure factual retrieval or entity accuracy.'],
               'counts': {split: len(part) for split, part in partitions.items()},
               'dataset_sha256': manifest['dataset_sha256'], 'selected_epoch': best_epoch, 'epochs': args.epochs, 'pooling': args.pooling,
               'models': {}}
    for name in ('tfidf', 'muril_finetuned'):
        metrics['models'][name] = {}
        for split in ('validation', 'test'):
            part = partitions[split]
            if name == 'tfidf':
                prediction = baseline.predict([row['text'] for row in part]).tolist()
            else:
                prediction = predict(split)
            metrics['models'][name][split] = scores([row['intent'] for row in part], prediction)
            metrics['models'][name].setdefault('by_language', {}).setdefault(split, {})
            for language in ('hi', 'hinglish'):
                subset = [(row, pred) for row, pred in zip(part, prediction) if row['language'] == language]
                metrics['models'][name]['by_language'][split][language] = scores(
                    [row['intent'] for row, _ in subset], [pred for _, pred in subset])
            if split == 'test':
                metrics['models'][name]['errors'] = [{'text': row['text'], 'expected': row['intent'], 'predicted': pred}
                                                   for row, pred in zip(part, prediction) if row['intent'] != pred][:10]
    from src.hindi_project.assistant import CATALOG, extract_entities
    catalog = json.loads(CATALOG.read_text())
    entity_rows = [row for row in csv.DictReader((ROOT / 'data/project/entity_slots.csv').open()) if row['split'] == 'test']
    tp = fp = fn = exact = 0
    for row in entity_rows:
        expected = {(name, row[name]) for name in ('origin', 'destination', 'transport_mode') if row[name]}
        slots = extract_entities(row['text'], catalog)
        predicted = {(name, str(slots[name])) for name in ('origin', 'destination', 'transport_mode') if name in slots}
        tp += len(expected & predicted)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
        exact += expected == predicted
    precision, recall = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
    metrics['entities'] = {'method': 'canonical gazetteer + Hindi/Hinglish role rules; no learned NER model',
                           'test_rows': len(entity_rows), 'precision': precision, 'recall': recall,
                           'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0,
                           'exact_match': exact / len(entity_rows) if entity_rows else 0,
                           'tp': tp, 'fp': fp, 'fn': fn, 'fields': ['origin', 'destination', 'transport_mode'],
                           'scope': 'Linked synthetic slot dataset; independent of intent prediction, not end-to-end accuracy'}
    (ROOT / 'models/hindi_project_metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
    write_report(metrics, ROOT / 'docs/NLP_EVALUATION.md')
    print(json.dumps({name: result['test']['macro_f1'] for name, result in metrics['models'].items()}), flush=True)


def write_report(metrics: dict, path: Path):
    lines = ['# Hindi / Hinglish intent-classification experiment', '',
             'Synthetic teaching data; template families are disjoint across train/validation/test. '
             'These results are not real-passenger accuracy. The frozen 400-query challenge is not used.', '',
             f"Rows: {metrics['counts']}. Seed: 42. Pooling: {metrics['pooling']}. Selected epoch: {metrics['selected_epoch']} (validation only).", '',
             'The existing transport-fine-tuned MuRIL checkpoint is reused. Its final two encoder layers and a new '
             f"nine-class head are trained for {metrics.get('epochs', 5)} epochs; the remaining encoder and embeddings are frozen. "
             'This is partial fine-tuning, not a fresh pretrained-model comparison. No hyperparameter search was run.', '',
             '| Model | Split | Accuracy | Macro precision | Macro recall | Macro F1 |',
             '| --- | --- | --- | --- | --- | --- |']
    for name, results in metrics['models'].items():
        for split in ('validation', 'test'):
            result = results[split]
            precision = sum(row['precision'] for row in result['per_class'].values()) / len(LABELS)
            recall = sum(row['recall'] for row in result['per_class'].values()) / len(LABELS)
            lines.append(f"| {name} | {split} | {result['accuracy']:.3f} | {precision:.3f} | {recall:.3f} | {result['macro_f1']:.3f} |")
    lines += ['', '## Hindi and Hinglish separately', '', '| Model | Language | Test rows | Accuracy | Macro F1 |',
              '| --- | --- | --- | --- | --- |']
    for name, results in metrics['models'].items():
        for language, result in results['by_language']['test'].items():
            lines.append(f"| {name} | {language} | {result['count']} | {result['accuracy']:.3f} | {result['macro_f1']:.3f} |")
    for name, results in metrics['models'].items():
        lines += ['', f'## {name}: test confusion matrix', '', 'Rows are true labels; columns are predicted labels.',
                  '', '| True / predicted | ' + ' | '.join(LABELS) + ' |', '| --- | ' + ' | '.join(['---'] * len(LABELS)) + ' |']
        for label, row in zip(LABELS, results['test']['confusion_matrix']):
            lines.append('| ' + label + ' | ' + ' | '.join(map(str, row)) + ' |')
        lines += ['', 'Example classification errors:', '']
        lines += [f"- {row['text']} → {row['predicted']} (label: {row['expected']})" for row in results['errors'][:5]] or ['No test errors observed in this synthetic sample.']
    entity = metrics['entities']
    lines += ['', '## Entity / slot extraction', '',
              f"Rule-based gazetteer, {entity['test_rows']} linked synthetic test queries: precision {entity['precision']:.3f}, recall {entity['recall']:.3f}, F1 {entity['f1']:.3f}, exact match {entity['exact_match']:.3f}.", '',
              'Fields evaluated: origin, destination and transport mode. Intent prediction is held out of this component measurement; '
              'these are related synthetic questions, not independent passenger data or end-to-end accuracy.', '',
              'Per-class precision, recall, F1 and support are saved in `models/hindi_project_metrics.json`. '
              'Human-authored Hindi examples and broader entity evaluation remain academic follow-up work.', '']
    path.write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
