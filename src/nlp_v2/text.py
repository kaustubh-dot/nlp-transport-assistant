"""Extraction-only Unicode normalization; frozen classifier receives raw text."""
import re
import unicodedata

_PUNCTUATION = re.compile(r"[।॥?!,.:;\-_()\[\]{}'\"‘’“”/\\]+")

def normalize_extraction_text(text: str) -> str:
    """Canonicalize case/punctuation while preserving all linguistic marks."""
    return re.sub(r'\s+', ' ', _PUNCTUATION.sub(' ', unicodedata.normalize('NFC', text).lower())).strip()
