"""Distribution integrity and atomic model installation without network access."""
import json

import pytest

from scripts.prepare_models import install_asset
from src.hindi_project.artifacts import sha256_file, verify_file
from src.hindi_project.model import ROOT, BaselineIntentClassifier


def test_clone_contains_baseline_head_and_complete_tokenizer():
    manifest = json.loads((ROOT / 'models/hindi_project_manifest.json').read_text())
    for key in ('baseline', 'head'):
        verify_file(ROOT / manifest[key + '_path'], manifest[key + '_sha256'])
    for name, checksum in manifest['tokenizer_files'].items():
        verify_file(ROOT / manifest['tokenizer_path'] / name, checksum)
    assert BaselineIntentClassifier().predict('Meri train bahut late hai.')[0] == 'train_status'


def test_verified_asset_does_not_download(tmp_path, monkeypatch):
    target = tmp_path / 'model.pt'
    target.write_bytes(b'valid')
    monkeypatch.setattr('scripts.prepare_models.urlopen', lambda *args, **kwargs: pytest.fail('Unexpected network request'))
    install_asset(target, sha256_file(target), 5, 'https://example.invalid/model.pt')
    assert target.read_bytes() == b'valid'


def test_offline_asset_is_verified_before_replacing_existing_file(tmp_path):
    source = tmp_path / 'offline'
    source.mkdir()
    (source / 'model.pt').write_bytes(b'valid')
    target = tmp_path / 'installed' / 'model.pt'
    target.parent.mkdir()
    target.write_bytes(b'old')
    install_asset(target, sha256_file(source / 'model.pt'), 5, 'unused', source)
    assert target.read_bytes() == b'valid'
    assert not list(target.parent.glob('*.part'))


@pytest.mark.parametrize('size,checksum', [(6, '0' * 64), (5, '0' * 64)])
def test_corrupt_asset_preserves_existing_file_and_cleans_staging(tmp_path, size, checksum):
    source = tmp_path / 'offline'
    source.mkdir()
    (source / 'model.pt').write_bytes(b'wrong')
    target = tmp_path / 'model.pt'
    target.write_bytes(b'old')
    with pytest.raises(ValueError, match='Integrity check failed'):
        install_asset(target, checksum, size, 'unused', source)
    assert target.read_bytes() == b'old'
    assert not list(tmp_path.glob('*.part'))
