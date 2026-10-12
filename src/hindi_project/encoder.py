"""Local MuRIL encoder, independent of the retired classifier and HF cache."""
import json
from pathlib import Path

from .artifacts import verify_file

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'models/hindi_project_manifest.json'


class MuRILEncoder:
    def __init__(self, manifest_path: Path = MANIFEST):
        from safetensors.torch import load_file
        from transformers import AutoTokenizer, BertConfig, BertModel

        manifest = json.loads(Path(manifest_path).read_text())
        encoder = ROOT / manifest['encoder_path']
        verify_file(encoder, manifest['encoder_sha256'])
        tokenizer = ROOT / manifest['tokenizer_path']
        for name, checksum in manifest['tokenizer_files'].items():
            verify_file(tokenizer / name, checksum)
        self.max_length = manifest['max_length']
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer, local_files_only=True, fix_mistral_regex=False)
        self.model = BertModel(BertConfig.from_pretrained(tokenizer, local_files_only=True))
        self.model.load_state_dict(load_file(str(encoder), device='cpu'), strict=True)
        self.model.eval()
