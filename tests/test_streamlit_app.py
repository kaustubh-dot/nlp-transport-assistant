"""Automated tests for Streamlit application UI/UX.

Uses streamlit.testing.v1.AppTest to verify initial rendering, quick suggestions,
manual input processing, model switching, NLU breakdown diagnostics, Hallmark design tokens,
interchange route visualizer, and Gate 46/30/39 compliance.
"""

import os
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app",
    "streamlit_app.py"
)


def test_app_initial_render():
    """Verifies that the Streamlit app loads with zero exceptions and correct structure."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    assert not at.exception, f"App raised exceptions on load: {at.exception}"
    assert len(at.tabs) == 4, f"Expected 4 navigation tabs, got {len(at.tabs)}"

    # Check that masthead title is rendered in markdown
    all_markdown = " ".join([m.value for m in at.markdown])
    assert "चेन्नई बहुभाषी परिवहन सहायक" in all_markdown
    assert "Chennai Multimodal Public Transit Assistant" in all_markdown
    assert "ब्लू लाइन" in all_markdown
    assert "ग्रीन लाइन" in all_markdown


def test_app_quick_route_query():
    """Verifies route query execution from quick suggestions."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Click btn_q1 (चेन्नई सेंट्रल से एयरपोर्ट)
    at.button(key="btn_q1").click().run()

    assert not at.exception, f"Exceptions after btn_q1: {at.exception}"
    assert at.text_input(key="main_user_input").value == "चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?"

    all_markdown = " ".join([m.value for m in at.markdown])
    assert "आधिकारिक प्रतिक्रिया" in all_markdown
    assert "route_query" in all_markdown
    assert "Blue Line" in all_markdown or "ब्लू" in all_markdown


def test_app_quick_accessibility_query():
    """Verifies accessibility query execution."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Click btn_q3 (कोयम्बेडु पर व्हीलचेयर)
    at.button(key="btn_q3").click().run()

    assert not at.exception, f"Exceptions after btn_q3: {at.exception}"
    all_markdown = " ".join([m.value for m in at.markdown])
    assert "accessibility" in all_markdown
    assert "व्हीलचेयर" in all_markdown


def test_app_manual_hinglish_query():
    """Verifies manual Hinglish input execution."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    at.text_input(key="main_user_input").input("central se airport route").run()

    assert not at.exception, f"Exceptions after manual input: {at.exception}"
    all_markdown = " ".join([m.value for m in at.markdown])
    assert "आधिकारिक प्रतिक्रिया" in all_markdown
    assert "route_query" in all_markdown


def test_app_muril_model_selection():
    """Verifies model switching to MuRIL in sidebar."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Switch to MuRIL (index 1)
    at.sidebar.selectbox[0].select_index(1).run()
    assert "MuRIL" in at.sidebar.selectbox[0].value

    at.text_input(key="main_user_input").input("सेंट्रल से एयरपोर्ट").run()
    assert not at.exception, f"Exceptions with MuRIL model: {at.exception}"


def test_app_developer_inspector():
    """Verifies developer debug inspector displays normalized query and slots."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Enable developer debug checkbox
    at.sidebar.checkbox[0].check().run()
    at.button(key="btn_q1").click().run()

    assert not at.exception, f"Exceptions with debug enabled: {at.exception}"
    assert len(at.expander) > 0, "Expected developer inspector expander to be present"


def test_interchange_route_visualizer():
    """Verifies 3-stage interchange visualization for multi-line transit journeys."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Input an interchange journey: Koyambedu to Airport
    at.text_input(key="main_user_input").input("कोयम्बेडु से एयरपोर्ट कैसे जाएँ?").run()

    assert not at.exception, f"Exceptions on interchange query: {at.exception}"
    all_markdown = " ".join([m.value for m in at.markdown])
    assert "इंटरचेंज आवश्यक" in all_markdown
    assert "route-node-interchange" in all_markdown
    assert "आलंदूर" in all_markdown or "Alandur" in all_markdown


def test_gate_46_honest_out_of_scope_badge():
    """Verifies that out-of-scope queries display an honest badge, not claiming verified CMRL record."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    at.text_input(key="main_user_input").input("tell me a joke").run()

    assert not at.exception, f"Exceptions on out_of_scope query: {at.exception}"
    all_markdown = " ".join([m.value for m in at.markdown])
    assert "दायरा सीमा" in all_markdown or "Out of Scope" in all_markdown
    # Must NOT claim that an out of scope joke disclaimer is a verified CMRL record!
    assert "सत्यापित CMRL रिकॉर्ड" not in all_markdown


def test_form_action_and_clear_synchronization():
    """Verifies clear button and process button state synchronization."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    at.text_input(key="main_user_input").input("सेंट्रल से एयरपोर्ट").run()
    assert at.text_input(key="main_user_input").value == "सेंट्रल से एयरपोर्ट"

    # Click clear button
    at.button(key="btn_clear_input").click().run()
    assert at.text_input(key="main_user_input").value == ""

    # Click a suggestion button
    at.button(key="btn_q1").click().run()
    assert at.text_input(key="main_user_input").value == "चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?"


def test_gate_30_no_emoji_in_navigation_tabs_and_headings():
    """Verifies Gate 30 anti-slop compliance: no generic emojis as headers or tab icons."""
    with open(APP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Banned emoji tells from Gate 30 in tabs or main headers
    banned_emojis = ["💬", "🗺️", "♿", "⚙️", "⚡", "🎯", "🚩", "🏁", "🛠️", "📊", "🔍", "📜", "📝", "🏷️", "🗄️", "🚆", "⏰", "🔤"]
    for emoji in banned_emojis:
        assert f'"{emoji} ' not in content, f"Found banned emoji icon tell in string: {emoji}"
        assert f"#### {emoji}" not in content, f"Found banned emoji heading tell: {emoji}"


def test_hallmark_css_tokens_and_stamp():
    """Verifies presence of required Hallmark custom design tokens and stamp."""
    with open(APP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Stamp verification
    assert "Hallmark · macrostructure: Workbench" in content
    assert "theme: custom" in content
    assert "Quiet Exchange" in content or "MandiPulse" in content
    assert "oklch(" in content
    assert "display: Cormorant Garamond" in content or "display: Plus Jakarta Sans" in content
    assert "contrast: pass (40–41)" in content
    assert "mobile: pass (34, 49, 50–57)" in content

    # Token discipline verification (Gate 48)
    assert "--color-paper:" in content
    assert "--color-ink:" in content
    assert "--color-accent:" in content
    assert "--font-display:" in content
    assert "--font-body:" in content
    assert "--font-outlier:" in content

    # Gate 38a: No italic headers
    assert "font-style: normal !important;" in content

    # Gate 34: overflow-x: clip
    assert "overflow-x: clip !important;" in content

    # Gate 26 & Gate 39: 8-state button & input rules
    assert "min-height: 44px !important;" in content
    assert "outline: 2px solid transparent !important;" in content
    assert "cursor: not-allowed !important;" in content


def test_tamil_translation_card_rendered():
    """Verifies that processing a query renders the Tamil translation communication card."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Trigger route query
    at.button(key="btn_q1").click().run()

    assert not at.exception, f"Exceptions after processing query: {at.exception}"
    all_markdown = " ".join([m.value for m in at.markdown])

    # Check for Tamil Translation card presence
    assert "transit-tamil-card" in all_markdown
    assert "தமிழ் மொழிபெயர்ப்பு" in all_markdown
    assert "உள்ளூர் தொடர்பு அட்டை" in all_markdown
    # Verify Tamil Unicode characters (U+0B80 to U+0BFF)
    has_tamil = any("\u0b80" <= ch <= "\u0bff" for ch in all_markdown)
    assert has_tamil, "Expected Tamil Unicode characters in rendered output"


def test_voice_recorder_audio_input_rendered():
    """Verifies that the voice query expander and audio recorder are rendered."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    assert not at.exception, f"Exceptions on render: {at.exception}"
    # Verify the voice query expander is rendered
    expander_labels = [exp.label for exp in at.expander]
    assert any("आवाज इनपुट" in label for label in expander_labels), "Expected voice query expander"

    # Check that the audio recorder widget is present in the codebase
    with open(APP_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "st.audio_input" in content
    assert "voice_query_recorder" in content


def test_sidebar_full_model_roster():
    """Verifies that the sidebar contains the full multi-model roster with IndicBERT v2 champion first."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    options = at.sidebar.selectbox[0].options
    assert len(options) == 6, f"Expected 6 candidate models in roster, found {len(options)}"
    assert "IndicBERT v2" in options[0], f"Expected IndicBERT v2 at index 0, got: {options[0]}"
    assert "MuRIL" in options[1], f"Expected MuRIL at index 1, got: {options[1]}"
    assert any("XLM-RoBERTa" in opt for opt in options)
    assert any("MiniLM" in opt for opt in options)
    assert any("HingBERT" in opt for opt in options)
    assert any("Baseline" in opt for opt in options)


def test_ui_language_selector_present():
    """Verifies that the sidebar contains the UI language mode selector."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    assert not at.exception, f"Exceptions on load: {at.exception}"
    radios = [r for r in at.sidebar.radio]
    assert len(radios) >= 1, "Expected UI language radio selector in sidebar"
    lang_radio = radios[0]
    assert "हिन्दी (Pure Hindi)" in lang_radio.options
    assert "English" in lang_radio.options
    assert "हिंग्लिश (Hinglish)" in lang_radio.options


def test_ui_language_mode_english():
    """Verifies switching UI language mode to English."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Select English
    at.sidebar.radio[0].set_value("English").run()
    assert not at.exception, f"Exceptions after selecting English: {at.exception}"

    all_markdown = " ".join([m.value for m in at.markdown])
    assert "Chennai Multimodal Transit Assistant" in all_markdown
    assert "Verified CMRL Stations" in all_markdown
    assert "Quick Discovery Queries" in all_markdown


def test_ui_language_mode_hinglish():
    """Verifies switching UI language mode to Hinglish."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    # Select Hinglish
    at.sidebar.radio[0].set_value("हिंग्लिश (Hinglish)").run()
    assert not at.exception, f"Exceptions after selecting Hinglish: {at.exception}"

    all_markdown = " ".join([m.value for m in at.markdown])
    assert "Chennai Multimodal Transit Assistant" in all_markdown
    assert "Verified Stations" in all_markdown or "Verified CMRL" in all_markdown
