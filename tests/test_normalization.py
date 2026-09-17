"""Unit tests for text normalization module."""

import pytest
from src.normalization import normalize_text, HindiNormalizer


def test_basic_normalization():
    normalizer = HindiNormalizer()
    raw = "चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?"
    cleaned = normalizer.normalize(raw)
    assert "चेन्नई" in cleaned
    assert "सेंट्रल" in cleaned
    assert "एयरपोर्ट" in cleaned
    assert "?" not in cleaned


def test_hinglish_normalization():
    raw = "Chennai Central Se Airport Kaise Jau?"
    cleaned = normalize_text(raw)
    assert cleaned == "chennai central se airport kaise jau"


def test_danda_removal():
    raw = "यह एक वाक्य है। दूसरा वाक्य॥"
    cleaned = normalize_text(raw)
    assert "।" not in cleaned
    assert "॥" not in cleaned
    assert "यह एक वाक्य है दूसरा वाक्य" == cleaned


def test_nuqta_normalization():
    raw = "फ़ोन और क़िला"
    cleaned = normalize_text(raw)
    assert cleaned == "फोन और किला"
