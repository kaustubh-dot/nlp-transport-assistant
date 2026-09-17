# tests/test_multimodal.py
"""Tests for multimodal extensions: NLLB Hindi-Tamil translation and Whisper speech recognition."""

import os
import pytest


def test_translator_module_exists():
    from src.translator import HindiToTamilTranslator
    translator = HindiToTamilTranslator()
    assert hasattr(translator, "translate")


def test_hindi_to_tamil_translation_simple():
    from src.translator import HindiToTamilTranslator
    translator = HindiToTamilTranslator()
    
    hi_text = "चेन्नई सेंट्रल मेट्रो स्टेशन"
    ta_text = translator.translate(hi_text)
    
    assert isinstance(ta_text, str)
    assert len(ta_text) > 0
    # Check that output contains Tamil Unicode range (\u0B80 - \u0BFF)
    has_tamil = any("\u0b80" <= ch <= "\u0bff" for ch in ta_text)
    assert has_tamil, f"Expected Tamil script in translation output, got: {ta_text}"


def test_speech_recognizer_module_exists():
    from src.speech_recognizer import HindiSpeechRecognizer
    asr = HindiSpeechRecognizer()
    assert hasattr(asr, "transcribe")


def test_hindi_to_tamil_route_translation():
    from src.translator import HindiToTamilTranslator
    translator = HindiToTamilTranslator()

    hi_route = "चेन्नई सेंट्रल से चेन्नई एयरपोर्ट तक मेट्रो मार्ग दर्ज है।"
    ta_text = translator.translate(hi_route)

    assert isinstance(ta_text, str)
    # Verify key Tamil transit terms are translated
    assert "சென்னை சென்ட்ரல்" in ta_text
    assert "சென்னை விமான நிலையம்" in ta_text
    assert "மெட்ரோ" in ta_text


def test_hindi_to_tamil_accessibility_translation():
    from src.translator import HindiToTamilTranslator
    translator = HindiToTamilTranslator()

    hi_access = "कोयम्बेडु स्टेशन पर व्हीलचेयर और लिफ्ट उपलब्ध है"
    ta_text = translator.translate(hi_access)

    assert "கோயம்பேடு" in ta_text
    assert "சக்கர நாற்காலி" in ta_text
    assert "மின்தூக்கி" in ta_text
    assert "கிடைக்கிறது" in ta_text


def test_speech_recognizer_empty_and_error_handling():
    from src.speech_recognizer import HindiSpeechRecognizer
    asr = HindiSpeechRecognizer()

    # Empty string or empty bytes should return empty string without error
    assert asr.transcribe("") == ""
    assert asr.transcribe(b"") == ""
