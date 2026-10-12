"""File integrity checks shared by setup and model loading."""
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected: str):
    if not path.is_file():
        raise FileNotFoundError(f'Model asset missing: {path.name}. Run python -m scripts.prepare_models')
    if sha256_file(path) != expected:
        raise ValueError(f'Model asset SHA-256 mismatch: {path.name}')
