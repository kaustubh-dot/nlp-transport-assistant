"""Download the two pinned MuRIL assets, verifying bytes before installation."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from urllib.request import Request, urlopen

from src.hindi_project.artifacts import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def install_asset(destination, checksum, size, url, local_dir=None):
    if destination.is_file() and destination.stat().st_size == size and sha256_file(destination) == checksum:
        print(f'Already verified: {destination.name}', flush=True)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.part', delete=False) as temporary:
        staging = Path(temporary.name)
    try:
        if local_dir:
            with (local_dir / destination.name).open('rb') as source, staging.open('wb') as target:
                shutil.copyfileobj(source, target)
        else:
            print(f'Downloading {destination.name} ({size / 1024**2:.1f} MiB)...', flush=True)
            request = Request(url, headers={'User-Agent': 'Chennai-Transport-NLP-Setup'})
            with urlopen(request, timeout=60) as source, staging.open('wb') as target:
                last_report = 0
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
                    if target.tell() - last_report >= 100 * 1024**2:
                        last_report = target.tell()
                        print(f'  {last_report / 1024**2:.0f} MiB downloaded', flush=True)
        if staging.stat().st_size != size or sha256_file(staging) != checksum:
            raise ValueError(f'Integrity check failed: {destination.name}; existing asset was preserved')
        staging.replace(destination)
        print(f'Installed and verified: {destination.name}', flush=True)
    finally:
        staging.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-dir', type=Path, help='Use an offline directory containing the two release files')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'models/hindi_project_manifest.json').read_text(encoding='utf-8'))
    for path_key, checksum_key in (('encoder_path', 'encoder_sha256'), ('encoder_patch_path', 'encoder_patch_sha256')):
        destination = ROOT / manifest[path_key]
        install_asset(destination, manifest[checksum_key], manifest['asset_bytes'][destination.name],
                      manifest['asset_release'] + '/' + destination.name, args.local_dir)
    print('MuRIL assets are ready. Install requirements-neural.txt before selecting MuRIL.', flush=True)


if __name__ == '__main__':
    main()
