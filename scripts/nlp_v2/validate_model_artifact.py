"""Verify supplied selected T3 weights before local startup; never download them."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from src.nlp_v2.model import DEFAULT_MANIFEST, T3IntentClassifier, load_manifest, sha256_file


def validate_artifact(manifest_path: Path = DEFAULT_MANIFEST, *, load_model: bool = False) -> dict:
    manifest_path = Path(manifest_path).resolve()
    manifest = load_manifest(manifest_path)
    checkpoint = Path(manifest['checkpoint_path'])
    if not checkpoint.is_absolute():
        checkpoint = manifest_path.parent / checkpoint
    checkpoint = checkpoint.resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(f'Missing selected checkpoint: {checkpoint}. Supply the selected checkpoint '
                                'from the project/run owner; see docs/nlp_v2/model_artifact_workflow.md.')
    actual = sha256_file(checkpoint)
    if actual != manifest['checkpoint_sha256']:
        raise ValueError('Checkpoint SHA-256 mismatch: obtain an intact copy matching the trusted T3 manifest.')
    if load_model:
        T3IntentClassifier(manifest_path)
    return {'taxonomy': manifest['taxonomy'], 'label_count': len(manifest['label_order']),
            'model_name': manifest['model_name'], 'model_revision': manifest['model_revision'],
            'preprocessing': manifest['preprocessing'], 'max_length': manifest['max_length'],
            'manifest_sha256': sha256_file(manifest_path), 'checkpoint_path': str(checkpoint),
            'checkpoint_sha256': actual, 'checkpoint_bytes': checkpoint.stat().st_size,
            'sha256_verified': True, 'strict_model_loaded': load_model}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--load-model', action='store_true',
                        help='Also verify strict tensor loading using the prepared offline tokenizer/config cache')
    args = parser.parse_args(argv)
    try:
        result = validate_artifact(args.manifest, load_model=args.load_model)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'Model artifact validation failed: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
