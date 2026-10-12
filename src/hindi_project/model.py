"""Nine project intents with a small partial MuRIL fine-tuning experiment."""
from __future__ import annotations

import json
from pathlib import Path

from .artifacts import sha256_file
from .encoder import MuRILEncoder

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'models/hindi_project_manifest.json'
LABELS = ('route_query', 'service_availability', 'service_timing',
          'station_information', 'accessibility', 'ticketing',
          'train_status', 'railway_complaint', 'out_of_scope')
LABELS_HI = {
    'route_query': 'मार्ग / अंतिम चरण का परिवहन',
    'service_availability': 'बस / मेट्रो की उपलब्धता',
    'service_timing': 'सेवा का समय',
    'station_information': 'स्टेशन की जानकारी',
    'accessibility': 'सुगम्यता सुविधाएँ',
    'ticketing': 'टिकट / किराया',
    'train_status': 'ट्रेन की देरी / स्थिति',
    'railway_complaint': 'रेलवे शिकायत',
    'out_of_scope': 'परिवहन से बाहर का प्रश्न',
}


def encode_queries(base: MuRILEncoder, queries: list[str], batch_size: int = 8, pooling: str = 'mean'):
    """Encode with the loaded project encoder at inference; do not invoke T3 labels."""
    import torch

    batches = []
    with torch.inference_mode():
        for start in range(0, len(queries), batch_size):
            encoded = base.tokenizer(queries[start:start + batch_size], padding=True,
                                     truncation=True, max_length=base.max_length,
                                     return_tensors='pt')
            output = base.model(**encoded)
            if pooling == 'mean':
                mask = encoded['attention_mask'].unsqueeze(-1)
                representation = (output.last_hidden_state * mask).sum(1) / mask.sum(1)
            elif pooling == 'pooler':
                representation = output.pooler_output
            else:
                raise ValueError('Unknown encoder pooling')
            batches.append(representation.cpu())
    return torch.cat(batches).clone()


class ProjectIntentClassifier:
    """Strict local loading. Probabilities are raw scores, not calibrated accuracy."""

    def __init__(self, manifest_path: Path = MANIFEST):
        import torch
        torch.set_num_threads(2)

        manifest_path = Path(manifest_path)
        if not manifest_path.is_file():
            raise FileNotFoundError('Project head missing. Run python -m scripts.nlp_v2.train_project')
        self.manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if self.manifest['labels'] != list(LABELS):
            raise ValueError('Project intent labels do not match the saved head')
        self.base = MuRILEncoder(manifest_path)
        if self.manifest['training_mode'] == 'last_two_encoder_layers_and_head':
            patch_path = ROOT / self.manifest['encoder_patch_path']
            if sha256_file(patch_path) != self.manifest['encoder_patch_sha256']:
                raise ValueError('Fine-tuned encoder SHA-256 mismatch')
            patch = torch.load(patch_path, map_location='cpu', weights_only=True)
            if set(patch) != {'10', '11'}:
                raise ValueError('Expected exactly the final two MuRIL encoder layers')
            for index, state in patch.items():
                self.base.model.encoder.layer[int(index)].load_state_dict(state, strict=True)
        elif self.manifest['training_mode'] != 'frozen_encoder_linear_head':
            raise ValueError('Unknown project training mode')
        head_path = ROOT / self.manifest['head_path']
        if sha256_file(head_path) != self.manifest['head_sha256']:
            raise ValueError('Project classifier head SHA-256 mismatch')
        self.head = torch.nn.Linear(self.base.model.config.hidden_size, len(LABELS))
        self.head.load_state_dict(torch.load(head_path, map_location='cpu', weights_only=True), strict=True)
        self.head.eval()

    def predict(self, query: str) -> tuple[str, float]:
        import torch

        if not isinstance(query, str) or not query.strip():
            raise ValueError('Please provide a nonempty Hindi question')
        with torch.inference_mode():
            probabilities = self.head(encode_queries(self.base, [query], pooling=self.manifest['pooling']))[0].softmax(-1)
            index = int(probabilities.argmax())
        return LABELS[index], float(probabilities[index])


class BaselineIntentClassifier:
    """Load only the locally trained baseline matching the project manifest."""

    def __init__(self, manifest_path: Path = MANIFEST):
        import pickle

        manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
        path = ROOT / manifest['baseline_path']
        if sha256_file(path) != manifest['baseline_sha256']:
            raise ValueError('Baseline SHA-256 mismatch')
        # Trusted local training output, never a pickle downloaded from a URL.
        with path.open('rb') as stream:
            self.model = pickle.load(stream)
        if set(self.model.classes_) != set(LABELS):
            raise ValueError('Baseline labels do not match the project taxonomy')

    def predict(self, query: str) -> tuple[str, float]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Please provide a nonempty Hindi question')
        scores = self.model.predict_proba([query])[0]
        index = int(scores.argmax())
        return str(self.model.classes_[index]), float(scores[index])
