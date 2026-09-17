"""Text normalization module for Hindi and Hinglish queries.

Provides Unicode normalization, punctuation stripping, case folding,
and Hindi-specific character cleanup.
"""

import re
import unicodedata
from typing import List


class HindiNormalizer:
    """Normalizes Hindi (Devanagari) and Hinglish (Roman) input text."""

    def __init__(self):
        # Common Hindi punctuation including Danda and Double Danda
        self.punct_pattern = re.compile(r"[\।\॥\?\!\,\.\:\;\-\_\(\)\[\]\{\}\'\"\‘\’\“\”\/\\]+")
        # Redundant whitespace
        self.whitespace_pattern = re.compile(r"\s+")
        # Devanagari character ranges
        self.devanagari_range = (0x0900, 0x097F)

    def normalize(self, text: str) -> str:
        """Applies full normalization pipeline to input string.

        Args:
            text: Raw input string in Hindi, Hinglish, or English.

        Returns:
            Normalized clean string.
        """
        if not text:
            return ""

        # 1. Unicode NFC canonical decomposition followed by canonical composition
        text = unicodedata.normalize("NFC", text)

        # 2. Convert Roman characters to lowercase for consistent Hinglish processing
        text = text.lower()

        # 3. Replace punctuation with whitespace
        text = self.punct_pattern.sub(" ", text)

        # 4. Normalize common Devanagari character variations (e.g. Nuqta characters)
        text = self._normalize_nuqta(text)

        # 5. Compress multiple whitespace into a single space and strip boundaries
        text = self.whitespace_pattern.sub(" ", text).strip()

        return text

    def _normalize_nuqta(self, text: str) -> str:
        """Normalizes Devanagari characters with Nuqta to their base forms

        for robust lexical matching.
        """
        nuqta_map = {
            "क़": "क",
            "ख़": "ख",
            "ग़": "ग",
            "ज़": "ज",
            "ड़": "ड",
            "ढ़": "ढ",
            "फ़": "फ",
            "य़": "य",
        }
        for k, v in nuqta_map.items():
            text = text.replace(k, v)
        return text

    def is_devanagari(self, text: str) -> bool:
        """Checks if the text contains any Devanagari script characters."""
        for char in text:
            code = ord(char)
            if self.devanagari_range[0] <= code <= self.devanagari_range[1]:
                return True
        return False

    def tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenizer on normalized text."""
        normalized = self.normalize(text)
        return normalized.split() if normalized else []


_normalizer = HindiNormalizer()


def normalize_text(text: str) -> str:
    """Convenience functional wrapper for text normalization."""
    return _normalizer.normalize(text)
