"""Synthetic artifact transfer checks, never real weights in Git fixtures."""
import json
import pytest
from src.nlp_v2.model import DEFAULT_MANIFEST, load_manifest, sha256_file


def manifest(tmp_path, *, content=b'synthetic authorized bytes'):
    m=load_manifest(); p=tmp_path/'weights.pt';p.write_bytes(content)
    m['checkpoint_path']='weights.pt';m['checkpoint_sha256']=sha256_file(p)
    target=tmp_path/'manifest.json';target.write_text(json.dumps(m))
    return target,p


def test_valid_transfer_hashes_relative_checkpoint_without_model_runtime(tmp_path):
    from scripts.nlp_v2.validate_model_artifact import validate_artifact
    path,weights=manifest(tmp_path)
    result=validate_artifact(path)
    assert result['checkpoint_sha256']==sha256_file(weights)
    assert result['checkpoint_bytes']==weights.stat().st_size
    assert result['sha256_verified'] is True
    assert result['strict_model_loaded'] is False
    assert result['taxonomy']=='T3' and result['label_count']==16


@pytest.mark.parametrize('change',['missing','corrupt','taxonomy'])
def test_bad_or_missing_transfer_fails_clearly(tmp_path,change):
    from scripts.nlp_v2.validate_model_artifact import validate_artifact
    path,weights=manifest(tmp_path)
    if change=='missing': weights.unlink()
    elif change=='corrupt': weights.write_bytes(b'corrupted transfer')
    else:
        m=json.loads(path.read_text());m['taxonomy']='T2';path.write_text(json.dumps(m))
    with pytest.raises((FileNotFoundError,ValueError),match='checkpoint|SHA-256|T3'):
        validate_artifact(path)


def test_optional_strict_check_forwards_selected_manifest_to_existing_loader(tmp_path,monkeypatch):
    from scripts.nlp_v2 import validate_model_artifact as validator
    path,weights=manifest(tmp_path);seen=[]
    monkeypatch.setattr(validator,'T3IntentClassifier',lambda p: seen.append(p))
    result=validator.validate_artifact(path,load_model=True)
    assert seen==[path.resolve()] and result['strict_model_loaded'] is True


def test_cli_missing_artifact_is_nonzero_actionable_without_traceback(tmp_path,capsys):
    from scripts.nlp_v2.validate_model_artifact import main
    path,weights=manifest(tmp_path);weights.unlink()
    assert main(['--manifest',str(path)])==1
    error=capsys.readouterr().err
    assert 'Supply the selected checkpoint' in error
    assert 'Traceback' not in error


def test_cli_malformed_manifest_shape_is_clear_nonzero(tmp_path,capsys):
    from scripts.nlp_v2.validate_model_artifact import main
    path=tmp_path/'manifest.json';path.write_text('[]')
    assert main(['--manifest',str(path)])==1
    error=capsys.readouterr().err
    assert 'T3 manifest' in error and 'Traceback' not in error
