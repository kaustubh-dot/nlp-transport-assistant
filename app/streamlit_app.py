"""Streamlit Web Application for Hindi Multimodal Transport Assistant for Chennai.

Provides an interactive user interface for querying Chennai transit in Hindi
and Hinglish with detailed NLU inspector and deterministic response generation.
Adheres strictly to Hallmark custom design system.
"""

import os
import sys
import sqlite3
from typing import Dict, List, Any, Optional

# Ensure repository root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.pipeline import TransportAssistant

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="चेन्नई परिवहन सहायक · Chennai Transit NLU",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. Hallmark Custom Design Tokens & Typography
# -----------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
/* Hallmark · macrostructure: Workbench · workbench knobs: layout=split-transit, tabs=live-query+network-directory
 * theme: custom · vibe: "chennai transit precision, sapphire rail, bilingual clarity" · paper: oklch(98.5% 0.006 240) · accent: oklch(56% 0.16 245)
 * display: Plus Jakarta Sans · body: Plus Jakarta Sans · outlier: JetBrains Mono · axes: light / geometric-sans / cool
 * pre-emit critique: P5 H5 E5 S5 R5 V5 · contrast: pass (40–41) · mobile: pass (34, 49, 50–57) · honest: pass (46) · chrome: pass (47) · tokens: pass (48) · responsive: pass (49) · icons: pass (30)
 * studied: no · context: explicit · v0.8.0
 */

:root {
    --color-paper: oklch(98.5% 0.006 240);
    --color-paper-2: oklch(96.2% 0.010 240);
    --color-paper-3: oklch(93.5% 0.012 240);
    --color-paper-elevated: oklch(99.2% 0.004 240);
    --color-ink: oklch(20% 0.014 240);
    --color-ink-2: oklch(38% 0.012 240);
    --color-rule: oklch(86% 0.010 240);
    --color-rule-2: oklch(91% 0.008 240);
    --color-muted: oklch(50% 0.012 240);
    --color-accent: oklch(56% 0.16 245);
    --color-accent-ink: oklch(98% 0.005 240);
    --color-focus: oklch(58% 0.20 245);

    /* Transit Functional Line Tokens */
    --color-blue-line: oklch(52% 0.18 245);
    --color-blue-line-surface: oklch(95.5% 0.030 245);
    --color-green-line: oklch(52% 0.17 148);
    --color-green-line-surface: oklch(95.5% 0.030 148);
    --color-interchange: oklch(48% 0.15 295);
    --color-interchange-surface: oklch(95.5% 0.025 295);
    --color-verified: oklch(50% 0.14 155);
    --color-verified-surface: oklch(96% 0.025 155);
    --color-scope-notice: oklch(52% 0.14 45);
    --color-scope-surface: oklch(96% 0.025 45);

    /* Elevation Shadows */
    --shadow-subtle: 0 1px 3px oklch(20% 0.014 240 / 0.05);
    --shadow-card: 0 2px 8px oklch(20% 0.014 240 / 0.07);

    /* Typography */
    --font-display: 'Plus Jakarta Sans', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-body: 'Plus Jakarta Sans', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-outlier: 'JetBrains Mono', monospace;

    /* Spacing 4-pt Scale */
    --space-3xs: 4px;
    --space-2xs: 8px;
    --space-xs: 12px;
    --space-sm: 16px;
    --space-md: 20px;
    --space-lg: 24px;
    --space-xl: 32px;
    --space-2xl: 40px;
    --space-3xl: 48px;

    /* Geometry */
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --radius-full: 9999px;
}

/* Page Edge Clipping & Base Typography (Gate 34) */
html, body, [data-testid="stAppViewContainer"] {
    overflow-x: clip !important;
    font-family: var(--font-body) !important;
    color: var(--color-ink) !important;
    background-color: var(--color-paper) !important;
}

/* Headings Discipline: Roman Always (Gate 38a) */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-display) !important;
    font-style: normal !important;
    color: var(--color-ink) !important;
    font-weight: 700 !important;
    overflow-wrap: anywhere !important;
    min-width: 0 !important;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: var(--color-paper-2) !important;
    border-right: 1px solid var(--color-rule) !important;
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: var(--color-ink) !important;
}

/* Button 8-State Refinement (Gate 26, Gate 39) */
.stButton > button {
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    min-height: 44px !important;
    border: 1px solid var(--color-rule) !important;
    background-color: var(--color-paper-elevated) !important;
    color: var(--color-ink) !important;
    border-radius: var(--radius-sm) !important;
    padding: var(--space-2xs) var(--space-sm) !important;
    white-space: nowrap !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: var(--space-2xs) !important;
    outline: 2px solid transparent !important;
    outline-offset: 1px !important;
    box-shadow: var(--shadow-subtle) !important;
    transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.1s ease !important;
}

.stButton > button:hover {
    background-color: var(--color-paper-3) !important;
    border-color: var(--color-accent) !important;
    color: var(--color-accent) !important;
}

.stButton > button:active {
    transform: translateY(1px) !important;
    background-color: var(--color-paper-2) !important;
}

.stButton > button:focus-visible {
    outline: 2px solid var(--color-focus) !important;
    outline-offset: 1px !important;
}

.stButton > button:disabled, .stButton > button[disabled] {
    opacity: 0.55 !important;
    cursor: not-allowed !important;
    pointer-events: none !important;
}

/* Primary Button Styling */
.stButton > button[kind="primary"] {
    background-color: var(--color-accent) !important;
    border-color: var(--color-accent) !important;
    color: var(--color-accent-ink) !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: oklch(50% 0.17 245) !important;
    border-color: oklch(50% 0.17 245) !important;
    color: var(--color-accent-ink) !important;
}

/* Text Input Refinement (Gate 39) */
div[data-testid="stTextInput"] input {
    font-family: var(--font-body) !important;
    font-size: 1rem !important;
    min-height: 44px !important;
    border: 1px solid var(--color-rule) !important;
    border-radius: var(--radius-md) !important;
    background-color: var(--color-paper-elevated) !important;
    color: var(--color-ink) !important;
    padding: var(--space-2xs) var(--space-sm) !important;
    outline: 2px solid transparent !important;
    outline-offset: 1px !important;
    transition: border-color 0.15s ease !important;
}

div[data-testid="stTextInput"] input:hover {
    border-color: var(--color-ink-2) !important;
}

div[data-testid="stTextInput"] input:focus, div[data-testid="stTextInput"] input:focus-visible {
    border-color: var(--color-focus) !important;
    outline: 2px solid var(--color-focus) !important;
    outline-offset: 1px !important;
}

div[data-testid="stTextInput"] input:disabled {
    opacity: 0.55 !important;
    cursor: not-allowed !important;
}

/* Tabs Header */
div[data-baseweb="tab-list"] {
    gap: var(--space-xs) !important;
    border-bottom: 1px solid var(--color-rule) !important;
    margin-bottom: var(--space-lg) !important;
}

div[data-baseweb="tab"] {
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: var(--color-muted) !important;
    padding: var(--space-xs) var(--space-sm) !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
}

div[data-baseweb="tab"][aria-selected="true"] {
    color: var(--color-accent) !important;
    border-bottom: 2px solid var(--color-accent) !important;
}

/* Masthead Container */
.transit-masthead {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
    background-color: var(--color-paper-2);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-lg);
}

.transit-masthead-title {
    font-family: var(--font-display);
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--color-ink);
    line-height: 1.2;
    margin: 0;
}

.transit-masthead-subtitle {
    font-family: var(--font-body);
    font-size: 0.95rem;
    color: var(--color-ink-2);
    margin: 0;
    max-width: 70ch;
}

.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-xs);
    margin-top: var(--space-2xs);
    align-items: center;
}

.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: var(--space-3xs);
    font-family: var(--font-outlier);
    font-size: 0.775rem;
    font-weight: 600;
    padding: var(--space-3xs) var(--space-xs);
    border-radius: var(--radius-full);
    white-space: nowrap;
}

.badge-blue {
    background-color: var(--color-blue-line-surface);
    color: var(--color-blue-line);
    border: 1px solid var(--color-blue-line);
}

.badge-green {
    background-color: var(--color-green-line-surface);
    color: var(--color-green-line);
    border: 1px solid var(--color-green-line);
}

.badge-interchange {
    background-color: var(--color-interchange-surface);
    color: var(--color-interchange);
    border: 1px solid var(--color-interchange);
}

.badge-verified {
    background-color: var(--color-verified-surface);
    color: var(--color-verified);
    border: 1px solid var(--color-verified);
}

.badge-scope-notice {
    background-color: var(--color-scope-surface);
    color: var(--color-scope-notice);
    border: 1px solid var(--color-scope-notice);
}

/* Response Section Card (Hairline Border, Gate 5 Compliant) */
.transit-response-card {
    background-color: var(--color-paper-elevated);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-md);
    padding: var(--space-lg);
    margin-top: var(--space-md);
    margin-bottom: var(--space-md);
    box-shadow: var(--shadow-card);
}

.transit-response-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: var(--space-xs);
    border-bottom: 1px solid var(--color-rule-2);
    margin-bottom: var(--space-sm);
}

.transit-response-label {
    font-family: var(--font-display);
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-muted);
}

.transit-response-body {
    font-family: var(--font-body);
    font-size: 1.15rem;
    line-height: 1.6;
    color: var(--color-ink);
    font-weight: 500;
    max-width: 65ch;
}

/* Tamil Translation Communication Card */
.transit-tamil-card {
    background-color: var(--color-paper-2);
    border: 1px solid var(--color-rule);
    border-left: 4px solid var(--color-accent);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-top: var(--space-xs);
    margin-bottom: var(--space-md);
    box-shadow: var(--shadow-card);
}

.transit-tamil-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: var(--space-2xs);
    border-bottom: 1px solid var(--color-rule-2);
    margin-bottom: var(--space-xs);
}

.transit-tamil-label {
    font-family: var(--font-display);
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-accent);
}

.transit-tamil-body {
    font-family: var(--font-body);
    font-size: 1.05rem;
    line-height: 1.5;
    color: var(--color-ink);
    font-weight: 500;
    max-width: 65ch;
}

/* Route Stepper Diagram */
.route-visualizer {
    background-color: var(--color-paper-2);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-top: var(--space-sm);
    margin-bottom: var(--space-md);
}

.route-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
}

.route-steps {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
}

@media (min-width: 640px) {
    .route-steps {
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
    }
}

.route-node {
    display: flex;
    align-items: center;
    gap: var(--space-xs);
}

.route-node-circle {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-outlier);
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
}

.route-node-blue {
    background-color: var(--color-blue-line);
    color: var(--color-accent-ink);
}

.route-node-green {
    background-color: var(--color-green-line);
    color: var(--color-accent-ink);
}

.route-node-interchange {
    background-color: var(--color-interchange);
    color: var(--color-accent-ink);
}

.route-station-name {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--color-ink);
}

.route-station-sub {
    font-size: 0.8rem;
    color: var(--color-muted);
}

.route-connector {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3xs);
    padding: 0 var(--space-xs);
}

.route-connector-label {
    font-size: 0.75rem;
    font-family: var(--font-outlier);
    color: var(--color-muted);
    white-space: nowrap;
}

.route-track {
    height: 4px;
    width: 100%;
    border-radius: var(--radius-full);
}

.route-track-blue {
    background-color: var(--color-blue-line);
}

.route-track-green {
    background-color: var(--color-green-line);
}

/* Accessibility Grid */
.amenity-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--space-sm);
    margin-top: var(--space-sm);
}

.amenity-pill {
    display: flex;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-xs) var(--space-sm);
    background-color: var(--color-paper-elevated);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
}

.amenity-active {
    color: var(--color-verified);
    font-weight: 600;
}

.amenity-inactive {
    color: var(--color-muted);
}

/* Metric Display Cards */
.nlu-metric-card {
    background-color: var(--color-paper-elevated);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-sm);
    padding: var(--space-sm);
    height: 100%;
}

.nlu-metric-label {
    font-family: var(--font-display);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-muted);
    margin-bottom: var(--space-3xs);
}

.nlu-metric-value {
    font-family: var(--font-outlier);
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--color-ink);
}

.nlu-metric-delta {
    font-family: var(--font-outlier);
    font-size: 0.8rem;
    color: var(--color-accent);
    margin-top: var(--space-3xs);
}

/* Station Table & Card Styles */
.station-card {
    background-color: var(--color-paper-elevated);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-bottom: var(--space-sm);
    transition: border-color 0.15s ease;
}

.station-card:hover {
    border-color: var(--color-accent);
}

/* Reduced Motion Fallback (Gate 27) */
@media (prefers-reduced-motion: reduce) {
    *, ::before, ::after {
        animation-delay: -1ms !important;
        animation-duration: 1ms !important;
        animation-iteration-count: 1 !important;
        background-attachment: initial !important;
        scroll-behavior: auto !important;
        transition-delay: 0s !important;
        transition-duration: 0s !important;
    }
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 3. Database & Assistant Initializers
# -----------------------------------------------------------------------------
@st.cache_resource
def get_assistant(model_type: str = "indicbert_v2") -> TransportAssistant:
    """Initializes and caches the Transport Assistant pipeline."""
    return TransportAssistant(model_type=model_type)


@st.cache_resource
def get_translator():
    """Initializes and caches the Hindi-to-Tamil translator."""
    from src.translator import HindiToTamilTranslator
    return HindiToTamilTranslator()


@st.cache_resource
def get_speech_recognizer():
    """Initializes and caches the local Hindi speech recognizer."""
    from src.speech_recognizer import HindiSpeechRecognizer
    return HindiSpeechRecognizer()


@st.cache_data
def get_all_stations() -> List[Dict[str, Any]]:
    """Loads all verified CMRL stations from SQLite."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "processed", "transport.db")
    if not os.path.exists(db_path):
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM stations ORDER BY station_id")
        return [dict(r) for r in cur.fetchall()]


@st.cache_data
def get_all_facilities() -> List[Dict[str, Any]]:
    """Loads verified accessibility facilities from SQLite."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "processed", "transport.db")
    if not os.path.exists(db_path):
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT f.*, s.name_en, s.name_hi, s.name_ta, s.type
            FROM facilities f
            JOIN stations s ON f.station_id = s.station_id
            ORDER BY s.name_en
        """)
        return [dict(r) for r in cur.fetchall()]


# -----------------------------------------------------------------------------
# 4. State Management
# -----------------------------------------------------------------------------
if "active_query" not in st.session_state:
    st.session_state.active_query = ""

if "main_user_input" not in st.session_state:
    st.session_state.main_user_input = ""


def set_query(query_text: str):
    """Callback to set active query and synchronize text widget state."""
    st.session_state.active_query = query_text
    st.session_state.main_user_input = query_text


def clear_all_query():
    """Callback to clear active query and text input before widget instantiation."""
    st.session_state.active_query = ""
    st.session_state.main_user_input = ""


# -----------------------------------------------------------------------------
# 5. Sidebar: Engine Controls & Data Provenance
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### CMRL पारगमन नियंत्रण")
    st.markdown("**Bilingual Transit NLU System**")
    st.caption("चेन्नई मेट्रो रेल लिमिटेड (CMRL) के लिए बहुभाषी प्राकृतिक भाषा समझ")

    st.markdown("---")
    model_options = [
        "IndicBERT v2 (AI4Bharat Champion · 90.6% Acc)",
        "MuRIL (Google Multilingual)",
        "XLM-RoBERTa (Meta Cross-Lingual)",
        "MiniLM (Sentence-Transformers)",
        "HingBERT (L3Cube Hinglish)",
        "Baseline (TF-IDF + Logistic Regression)"
    ]
    model_choice = st.selectbox(
        "मॉडल चुनें (Active Model Backend):",
        model_options,
        index=0,
        help="चुनें कि किस NLU मॉडल बैकएंड का उपयोग करना है। डिफ़ॉल्ट मॉडल AI4Bharat IndicBERT v2 है।"
    )
    if "IndicBERT" in model_choice:
        selected_model_type = "indicbert_v2"
    elif "MuRIL" in model_choice:
        selected_model_type = "muril"
    elif "XLM-RoBERTa" in model_choice:
        selected_model_type = "xlm_roberta"
    elif "MiniLM" in model_choice:
        selected_model_type = "minilm"
    elif "HingBERT" in model_choice:
        selected_model_type = "hingbert"
    else:
        selected_model_type = "baseline"

    st.markdown("---")
    st.markdown("#### सत्यापित डेटा स्लाइस")
    st.markdown("""
    - **सत्यापित स्टेशन**: 13 आधिकारिक CMRL स्टेशन (ब्लू एवं ग्रीन लाइन)
    - **सुलभता रिकॉर्ड**: आधिकारिक CMRL सुलभता सुविधाएं (लिफ्ट, व्हीलचेयर, दृष्टिबाधित स्पर्श पथ)
    - **इंटरचेंज हब**: आलंदूर एवं चेन्नई सेंट्रल
    """)

    st.markdown("---")
    st.markdown("#### सिस्टम सीमाएं (Gate 46 Honest Copy)")
    st.markdown("""
    - **समय-सारणी**: गतिशील लाइव प्रस्थान/आगमन समय असमर्थित हैं।
    - **किराया गणना**: परिवर्तनशील किराया तालिका इस स्लाइस में दर्ज नहीं है।
    - **लाइव स्थिति**: ट्रेन रनिंग स्थिति रियल-टाइम में समर्थित नहीं है।
    """)

    st.markdown("---")
    show_developer_debug = st.checkbox("डेवलपर इंस्पेक्टर (NLU Deep Inspection)", value=False)

    st.button("नया संवाद (Clear Query)", key="btn_sidebar_clear", on_click=clear_all_query, use_container_width=True)

    st.caption("लागत: ₹0 | 100% स्थानीय प्रोटोटाइप | Hallmark Custom")


# Initialize assistant with cached resource
assistant = get_assistant(model_type=selected_model_type)

# -----------------------------------------------------------------------------
# 6. Masthead Banner (Gate 30 SVG Lead)
# -----------------------------------------------------------------------------
st.markdown("""
<header class="transit-masthead" role="banner">
    <div style="display: flex; align-items: center; gap: var(--space-xs);">
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect width="16" height="16" x="4" y="3" rx="2"></rect>
            <path d="M4 11h16"></path>
            <path d="M12 3v8"></path>
            <path d="m8 19-2 3"></path>
            <path d="m18 22-2-3"></path>
            <circle cx="8" cy="15" r="1"></circle>
            <circle cx="16" cy="15" r="1"></circle>
        </svg>
        <div>
            <h1 class="transit-masthead-title">चेन्नई बहुभाषी परिवहन सहायक</h1>
            <p class="transit-masthead-subtitle">Chennai Multimodal Public Transit Assistant · Bilingual NLU for CMRL Metro Network</p>
        </div>
    </div>
    <div class="badge-row">
        <span class="badge-pill badge-blue">ब्लू लाइन: विमको नगर ↔ एयरपोर्ट</span>
        <span class="badge-pill badge-green">ग्रीन लाइन: सेंट्रल ↔ सेंट थॉमस माउंट</span>
        <span class="badge-pill badge-interchange">इंटरचेंज: आलंदूर व सेंट्रल</span>
        <span class="badge-pill badge-verified">13 सत्यापित CMRL स्टेशन</span>
    </div>
</header>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. Navigation Tabs
# -----------------------------------------------------------------------------
tab_query, tab_stations, tab_accessibility, tab_architecture = st.tabs([
    "संवाद (Assistant)",
    "स्टेशन (Stations)",
    "सुलभता (Amenities)",
    "आर्किटेक्चर (System)"
])

# =============================================================================
# TAB 1: संवादात्मक सहायक (Interactive Query & Visual Route Stepper)
# =============================================================================
with tab_query:
    st.markdown("#### त्वरित प्रश्न सुझाव (Quick Discovery Queries)")
    st.caption("नीचे दिए गए किसी भी वर्ग के नमूना प्रश्न पर क्लिक करें या अपना प्रश्न नीचे लिखें:")

    q_col1, q_col2, q_col3, q_col4 = st.columns(4)

    with q_col1:
        st.markdown("**मार्ग (Route Queries)**")
        if st.button("चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?", key="btn_q1", use_container_width=True):
            set_query("चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?")
        if st.button("सेंट्रल से गिंडी के लिए मेट्रो है?", key="btn_q2", use_container_width=True):
            set_query("सेंट्रल से गिंडी के लिए मेट्रो है क्या?")

    with q_col2:
        st.markdown("**सुलभता (Accessibility)**")
        if st.button("कोयम्बेडु पर व्हीलचेयर उपलब्ध है?", key="btn_q3", use_container_width=True):
            set_query("कोयम्बेडु पर व्हीलचेयर उपलब्ध है?")
        if st.button("आलंदूर स्टेशन पर लिफ्ट है?", key="btn_q4", use_container_width=True):
            set_query("आलंदूर स्टेशन पर लिफ्ट उपलब्ध है क्या?")

    with q_col3:
        st.markdown("**समय व किराया (Timing & Fare)**")
        if st.button("आखिरी मेट्रो कितने बजे छूटती है?", key="btn_q5", use_container_width=True):
            set_query("आखिरी मेट्रो कितने बजे छूटती है?")
        if st.button("मेट्रो का किराया कितना है?", key="btn_q6", use_container_width=True):
            set_query("मेट्रो का किराया कितना है?")

    with q_col4:
        st.markdown("**हिंग्लिश (Hinglish Queries)**")
        if st.button("central se airport route", key="btn_q7", use_container_width=True):
            set_query("central se airport route")
        if st.button("airport ke liye metro hai kya", key="btn_q8", use_container_width=True):
            set_query("airport ke liye metro hai kya")

    st.markdown("<div style='margin-top: var(--space-md);'></div>", unsafe_allow_html=True)

    # Voice Input Recorder (Whisper Local ASR)
    with st.expander("आवाज इनपुट (Hindi / Hinglish Voice Query via Whisper)", expanded=False):
        st.caption("माइक्रोफ़ोन से बोलें — स्थानीय ओपन-सोर्स Whisper मॉडल स्वचालित रूप से इसे टेक्स्ट में बदलेगा:")
        audio_prompt = st.audio_input("माइक्रोफ़ोन रिकॉर्डर (Record Hindi Query):", key="voice_query_recorder")
        if audio_prompt is not None:
            audio_bytes = audio_prompt.read()
            if audio_bytes and len(audio_bytes) > 0:
                audio_cache_key = hash(audio_bytes)
                if st.session_state.get("last_processed_audio") != audio_cache_key:
                    with st.spinner("Whisper द्वारा ध्वनि पहचान जारी है (Transcribing audio)..."):
                        transcribed_text = get_speech_recognizer().transcribe(audio_bytes)
                        if transcribed_text:
                            st.session_state.last_processed_audio = audio_cache_key
                            set_query(transcribed_text)
                            st.rerun()

    # Input Box Form
    input_val = st.text_input(
        "अपना प्रश्न हिंदी या हिंग्लिश में लिखें (Ask your transit question):",
        value=st.session_state.active_query,
        placeholder="उदाहरण: चेन्नई सेंट्रल से एग्मोर कैसे जाएँ या airport ke liye metro hai kya?",
        key="main_user_input"
    )

    # Synchronize session state
    if input_val != st.session_state.active_query:
        st.session_state.active_query = input_val

    # Action Buttons Row
    action_col1, action_col2, _ = st.columns([2, 2, 6])
    with action_col1:
        search_clicked = st.button("विश्लेषण करें (Process)", type="primary", key="btn_process_query", use_container_width=True)
    with action_col2:
        st.button("साफ़ करें (Clear)", key="btn_clear_input", on_click=clear_all_query, use_container_width=True)

    current_query = st.session_state.active_query.strip()

    if current_query:
        with st.spinner("प्राकृतिक भाषा समझ (NLU) और ज्ञानकोष खोज जारी है..."):
            result = assistant.process_query(current_query)

        # ---------------------------------------------------------------------
        # Gate 46 Honest Copy Badge Determination
        # ---------------------------------------------------------------------
        intent = result.get("intent", "unknown")
        db_data = result.get("db_result", {})
        if not isinstance(db_data, dict):
            db_data = {}

        routes = db_data.get("routes", [])
        facilities = db_data.get("facilities")
        station_info = db_data.get("station_info")

        if intent == "out_of_scope":
            badge_label = "दायरा सीमा (Out of Scope)"
            badge_class = "badge-scope-notice"
        elif intent in ("service_timing", "ticketing"):
            badge_label = "प्रोटोटाइप सीमा (Static Notice)"
            badge_class = "badge-scope-notice"
        elif routes or facilities or station_info:
            badge_label = "सत्यापित CMRL रिकॉर्ड (Verified Record)"
            badge_class = "badge-verified"
        else:
            badge_label = "NLU परिणाम (Parsed Result)"
            badge_class = "badge-interchange"

        # ---------------------------------------------------------------------
        # Primary Response Presentation
        # ---------------------------------------------------------------------
        st.markdown(f"""
        <article class="transit-response-card" role="region" aria-label="परिवहन सहायक उत्तर">
            <div class="transit-response-header">
                <span class="transit-response-label">आधिकारिक प्रतिक्रिया (Assistant Response)</span>
                <span class="badge-pill {badge_class}">{badge_label}</span>
            </div>
            <div class="transit-response-body">
                {result["response_hi"]}
            </div>
        </article>
        """, unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # Tamil Translation Communication Card (For Conductors & Metro Staff)
        # ---------------------------------------------------------------------
        tamil_translation = get_translator().translate(result["response_hi"])
        if tamil_translation:
            st.markdown(f"""
            <aside class="transit-tamil-card" role="complementary" aria-label="தமிழ் மொழிபெயர்ப்பு">
                <div class="transit-tamil-header">
                    <span class="transit-tamil-label">தமிழ் மொழிபெயர்ப்பு (Tamil Translation for Conductors & Staff)</span>
                    <span class="badge-pill badge-verified">உள்ளூர் தொடர்பு அட்டை</span>
                </div>
                <div class="transit-tamil-body">
                    {tamil_translation}
                </div>
            </aside>
            """, unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # Dynamic Visualizer (Route Stepper / Accessibility / Station Metadata)
        # ---------------------------------------------------------------------
        # 1. Route Visualizer
        if routes:
            st.markdown("##### मार्ग एवं कॉरिडोर विवरण (Journey Route Corridor)")
            for idx, r in enumerate(routes):
                line_text = r.get("line_name", "CMRL Metro")
                is_direct = bool(r.get("direct", 1))

                if is_direct:
                    is_blue = "Blue" in line_text or "ब्लू" in line_text
                    track_class = "route-track-blue" if is_blue else "route-track-green"
                    node_class = "route-node-blue" if is_blue else "route-node-green"
                    line_badge = "badge-blue" if is_blue else "badge-green"
                    status_badge = "badge-verified"
                    status_text = "सीधी सेवा (Direct Service)"

                    st.markdown(f"""
                    <div class="route-visualizer">
                        <div class="route-header-bar">
                            <span class="badge-pill {status_badge}">{status_text}</span>
                            <span class="badge-pill {line_badge}">{line_text}</span>
                        </div>
                        <div class="route-steps">
                            <div class="route-node">
                                <div class="route-node-circle {node_class}">1</div>
                                <div>
                                    <div class="route-station-name">{r.get('origin_name_hi', 'प्रस्थान')}</div>
                                    <div class="route-station-sub">{r.get('origin_name_en', '')}</div>
                                </div>
                            </div>
                            <div class="route-connector">
                                <div class="{track_class} route-track"></div>
                                <span class="route-connector-label">{line_text}</span>
                            </div>
                            <div class="route-node">
                                <div class="route-node-circle {node_class}">2</div>
                                <div>
                                    <div class="route-station-name">{r.get('dest_name_hi', 'गंतव्य')}</div>
                                    <div class="route-station-sub">{r.get('dest_name_en', '')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Multi-stage Interchange Stepper (e.g. Green -> Blue via Alandur)
                    status_badge = "badge-interchange"
                    status_text = "इंटरचेंज आवश्यक (Interchange Required)"

                    interchange_hi = "आलंदूर मेट्रो"
                    interchange_en = "Alandur Interchange"
                    if "सेंट्रल" in line_text or "Central" in line_text:
                        interchange_hi = "चेन्नई सेंट्रल मेट्रो"
                        interchange_en = "Chennai Central Interchange"

                    st.markdown(f"""
                    <div class="route-visualizer">
                        <div class="route-header-bar">
                            <span class="badge-pill {status_badge}">{status_text}</span>
                            <span class="badge-pill badge-interchange">{line_text}</span>
                        </div>
                        <div class="route-steps">
                            <div class="route-node">
                                <div class="route-node-circle route-node-green">1</div>
                                <div>
                                    <div class="route-station-name">{r.get('origin_name_hi', 'प्रस्थान')}</div>
                                    <div class="route-station-sub">{r.get('origin_name_en', '')}</div>
                                </div>
                            </div>
                            <div class="route-connector">
                                <div class="route-track-green route-track"></div>
                                <span class="route-connector-label">ग्रीन लाइन (Green Line)</span>
                            </div>
                            <div class="route-node">
                                <div class="route-node-circle route-node-interchange">⇄</div>
                                <div>
                                    <div class="route-station-name">{interchange_hi}</div>
                                    <div class="route-station-sub">{interchange_en}</div>
                                </div>
                            </div>
                            <div class="route-connector">
                                <div class="route-track-blue route-track"></div>
                                <span class="route-connector-label">ब्लू लाइन (Blue Line)</span>
                            </div>
                            <div class="route-node">
                                <div class="route-node-circle route-node-blue">2</div>
                                <div>
                                    <div class="route-station-name">{r.get('dest_name_hi', 'गंतव्य')}</div>
                                    <div class="route-station-sub">{r.get('dest_name_en', '')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # 2. Accessibility Facility Visualizer
        elif facilities:
            st.markdown(f"##### {facilities.get('name_hi', 'स्टेशन')} सुलभता सुविधाएं (Station Amenities)")
            st.markdown(f"""
            <div class="amenity-grid">
                <div class="amenity-pill {'amenity-active' if facilities.get('wheelchair_available') else 'amenity-inactive'}">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <circle cx="12" cy="4" r="2"></circle>
                        <path d="m10.5 8.5 2.5 4.5h5"></path>
                        <path d="M5.5 12a6 6 0 1 0 6 6"></path>
                    </svg>
                    <span>व्हीलचेयर: <strong>{'उपलब्ध' if facilities.get('wheelchair_available') else 'दर्ज नहीं'}</strong></span>
                </div>
                <div class="amenity-pill {'amenity-active' if facilities.get('lift_available') else 'amenity-inactive'}">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <rect width="18" height="18" x="3" y="3" rx="2"></rect>
                        <path d="m9 10 3-3 3 3"></path>
                        <path d="m9 14 3 3 3-3"></path>
                    </svg>
                    <span>लिफ्ट (Elevator): <strong>{'उपलब्ध' if facilities.get('lift_available') else 'दर्ज नहीं'}</strong></span>
                </div>
                <div class="amenity-pill {'amenity-active' if facilities.get('tactile_paths') else 'amenity-inactive'}">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <path d="M2 12h20"></path>
                        <path d="M6 16v-8"></path>
                        <path d="M10 16v-8"></path>
                        <path d="M14 16v-8"></path>
                        <path d="M18 16v-8"></path>
                    </svg>
                    <span>स्पर्श पथ (Tactile): <strong>{'उपलब्ध' if facilities.get('tactile_paths') else 'दर्ज नहीं'}</strong></span>
                </div>
                <div class="amenity-pill {'amenity-active' if facilities.get('accessible_toilet') else 'amenity-inactive'}">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <path d="M7 21v-4a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v4"></path>
                        <circle cx="12" cy="7" r="3"></circle>
                    </svg>
                    <span>सुलभ शौचालय: <strong>{'उपलब्ध' if facilities.get('accessible_toilet') else 'दर्ज नहीं'}</strong></span>
                </div>
                <div class="amenity-pill {'amenity-active' if facilities.get('parking_available') else 'amenity-inactive'}">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <rect width="18" height="18" x="3" y="3" rx="2"></rect>
                        <path d="M9 17V7h4a3 3 0 0 1 0 6H9"></path>
                    </svg>
                    <span>पार्किंग सुविधा: <strong>{'उपलब्ध' if facilities.get('parking_available') else 'दर्ज नहीं'}</strong></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if facilities.get("notes_hi"):
                st.info(f"CMRL आधिकारिक सुलभता टिप्पणी: {facilities.get('notes_hi')}")

        # 3. Station Info Visualizer
        elif station_info:
            st.markdown("##### स्टेशन विवरण (Station Profile)")
            st_col1, st_col2, st_col3 = st.columns(3)
            with st_col1:
                st.markdown(f"**हिंदी नाम:** {station_info.get('name_hi')}")
                st.markdown(f"**English:** {station_info.get('name_en')}")
            with st_col2:
                st.markdown(f"**तमिल (தமிழ்):** {station_info.get('name_ta', '—')}")
                st.markdown(f"**प्रकार (Type):** `{station_info.get('type')}`")
            with st_col3:
                st.markdown(f"**अक्षांश (Lat):** `{station_info.get('latitude', '—')}`")
                st.markdown(f"**देशांतर (Lon):** `{station_info.get('longitude', '—')}`")

        # ---------------------------------------------------------------------
        # NLU Pipeline Breakdown Metrics
        # ---------------------------------------------------------------------
        st.markdown("<div style='margin-top: var(--space-sm);'></div>", unsafe_allow_html=True)
        st.markdown("##### NLU पाइपलाइन विश्लेषण (Natural Language Understanding Breakdown)")

        m_col1, m_col2, m_col3 = st.columns(3)

        with m_col1:
            conf_val = result.get("confidence", 0.0) * 100
            st.markdown(f"""
            <div class="nlu-metric-card">
                <div class="nlu-metric-label">पहचाना गया उद्देश्य (Intent)</div>
                <div class="nlu-metric-value">{result.get("intent", "unknown")}</div>
                <div class="nlu-metric-delta">{conf_val:.1f}% विश्‍वसनीयता (Confidence)</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col2:
            orig = result["slots"].get("origin") or "निर्दिष्ट नहीं (Not specified)"
            st.markdown(f"""
            <div class="nlu-metric-card">
                <div class="nlu-metric-label">प्रस्थान स्थान (Origin Slot)</div>
                <div class="nlu-metric-value">{orig}</div>
                <div class="nlu-metric-delta">मोड: {result['slots'].get('transport_mode') or 'ऑटो / metro'}</div>
            </div>
            """, unsafe_allow_html=True)

        with m_col3:
            dest = result["slots"].get("destination") or "निर्दिष्ट नहीं (Not specified)"
            st.markdown(f"""
            <div class="nlu-metric-card">
                <div class="nlu-metric-label">गंतव्य स्थान (Destination Slot)</div>
                <div class="nlu-metric-value">{dest}</div>
                <div class="nlu-metric-delta">प्रकार: {result['slots'].get('information_type') or 'सामान्य'}</div>
            </div>
            """, unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # Developer Inspector Drawer
        # ---------------------------------------------------------------------
        if show_developer_debug:
            st.markdown("<div style='margin-top: var(--space-sm);'></div>", unsafe_allow_html=True)
            with st.expander("NLU डीप इंस्पेक्शन (Developer Inspection Payload)", expanded=True):
                insp_tab1, insp_tab2, insp_tab3 = st.tabs(["सामान्यीकरण (Normalization)", "स्लॉट्स (Slots)", "डेटाबेस रिकॉर्ड (DB Result)"])
                with insp_tab1:
                    st.code(f"कच्चा प्रश्न (Raw): {result['raw_query']}\nसामान्यीकृत (Normalized): {result['normalized_query']}", language="text")
                with insp_tab2:
                    st.json(result["slots"])
                with insp_tab3:
                    st.json(result["db_result"])

    else:
        st.info("ऊपर दिए गए किसी त्वरित प्रश्न पर क्लिक करें या चेन्नई पारगमन संबंधी अपना प्रश्न टाइप करें।")


# =============================================================================
# TAB 2: CMRL स्टेशन नेटवर्क (Station Directory)
# =============================================================================
with tab_stations:
    st.markdown("#### चेन्नई मेट्रो रेल (CMRL) 13 सत्यापित स्टेशन नेटवर्क")
    st.caption("यह निर्देशिका आधिकारिक CMRL ब्लू एवं ग्रीन लाइन के 13 सत्यापित स्टेशनों की पूरी सूची दर्शाती है।")

    stations = get_all_stations()

    search_station = st.text_input("स्टेशन खोजें (Search station by name in English or Hindi):", "")

    filtered_stations = stations
    if search_station.strip():
        q_lower = search_station.lower()
        filtered_stations = [
            s for s in stations
            if q_lower in s["name_en"].lower() or q_lower in s["name_hi"] or q_lower in (s["name_ta"] or "") or q_lower in s["station_id"].lower()
        ]

    for stn in filtered_stations:
        stn_type_label = "इंटरचेंज जंक्शन (Interchange)" if "interchange" in stn["type"] else "मेट्रो स्टेशन (Station)"
        stn_type_badge = "badge-interchange" if "interchange" in stn["type"] else "badge-blue"

        st.markdown(f"""
        <div class="station-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: var(--color-ink);">{stn['name_hi']}</h3>
                    <div style="font-size: 0.9rem; color: var(--color-ink-2);">{stn['name_en']} · {stn.get('name_ta', '')}</div>
                </div>
                <span class="badge-pill {stn_type_badge}">{stn_type_label}</span>
            </div>
            <div style="display: flex; gap: var(--space-md); margin-top: var(--space-xs); font-size: 0.8rem; font-family: var(--font-outlier); color: var(--color-muted);">
                <span>ID: <strong>{stn['station_id']}</strong></span>
                <span>Lat: {stn.get('latitude', '—')}</span>
                <span>Lon: {stn.get('longitude', '—')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# TAB 3: सुलभता निर्देशिका (Accessibility Directory)
# =============================================================================
with tab_accessibility:
    st.markdown("#### CMRL स्टेशन सुलभता मैट्रिक्स (Accessibility Directory)")
    st.caption("CMRL के आधिकारिक रिकॉर्ड के अनुसार प्रत्येक स्टेशन की सुलभता सुविधाएं:")

    all_fac = get_all_facilities()

    fac_filter = st.selectbox(
        "सुविधा के अनुसार फ़िल्टर करें (Filter by facility):",
        ["सभी स्टेशन (All Stations)", "केवल व्हीलचेयर उपलब्ध (Wheelchair Available)", "केवल दृष्टिबाधित स्पर्श पथ उपलब्ध (Tactile Paths Available)"]
    )

    displayed_fac = all_fac
    if "व्हीलचेयर" in fac_filter:
        displayed_fac = [f for f in all_fac if f.get("wheelchair_available") == 1]
    elif "स्पर्श पथ" in fac_filter:
        displayed_fac = [f for f in all_fac if f.get("tactile_paths") == 1]

    for f in displayed_fac:
        st.markdown(f"""
        <div class="station-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2xs);">
                <h4 style="margin: 0; font-size: 1.05rem;">{f['name_hi']} ({f['name_en']})</h4>
                <span class="badge-pill badge-verified">ID: {f['station_id']}</span>
            </div>
            <div class="amenity-grid">
                <div class="amenity-pill {'amenity-active' if f.get('wheelchair_available') else 'amenity-inactive'}">
                    <span>व्हीलचेयर: {'✓ उपलब्ध' if f.get('wheelchair_available') else '✗ दर्ज नहीं'}</span>
                </div>
                <div class="amenity-pill {'amenity-active' if f.get('lift_available') else 'amenity-inactive'}">
                    <span>लिफ्ट: {'✓ उपलब्ध' if f.get('lift_available') else '✗ दर्ज नहीं'}</span>
                </div>
                <div class="amenity-pill {'amenity-active' if f.get('tactile_paths') else 'amenity-inactive'}">
                    <span>स्पर्श पथ: {'✓ उपलब्ध' if f.get('tactile_paths') else '✗ दर्ज नहीं'}</span>
                </div>
                <div class="amenity-pill {'amenity-active' if f.get('accessible_toilet') else 'amenity-inactive'}">
                    <span>सुलभ शौचालय: {'✓ उपलब्ध' if f.get('accessible_toilet') else '✗ दर्ज नहीं'}</span>
                </div>
                <div class="amenity-pill {'amenity-active' if f.get('parking_available') else 'amenity-inactive'}">
                    <span>पार्किंग: {'✓ उपलब्ध' if f.get('parking_available') else '✗ दर्ज नहीं'}</span>
                </div>
            </div>
            {f"<div style='margin-top: var(--space-2xs); font-size: 0.85rem; color: var(--color-ink-2);'><strong>टिप्पणी:</strong> {f.get('notes_hi')}</div>" if f.get('notes_hi') else ""}
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# TAB 4: NLU आर्किटेक्चर (System Architecture & Integrity)
# =============================================================================
with tab_architecture:
    st.markdown("#### सिस्टम वास्तुकला एवं NLU पाइपलाइन (End-to-End Architecture)")
    st.markdown("""
    चेन्नई बहुभाषी परिवहन सहायक एक 5-स्तरीय नियतात्मक (Deterministic) प्राकृतिक भाषा प्रसंस्करण प्रणाली है:
    """)

    st.markdown("""
    1. **पाठ्य सामान्यीकरण (Text Normalization)**:
       - देवनागरी यूनिकोड फॉर्म (NFKC) सामान्यीकरण
       - हिंग्लिश और बोलचाल की वर्तनी का लिप्यंतरण मानचित्रण
       - विराम चिह्न एवं अतिरिक्त रिक्त स्थान निष्कासन

    2. **उद्देश्य वर्गीकरण (Multi-Model Intent Classification)**:
       - **AI4Bharat IndicBERT v2 (Champion · 90.56% Acc, 0.8719 Macro-F1)**: शीर्ष रैंक वाला बहुभाषी मॉडल
       - **Meta XLM-RoBERTa (Runner-Up · 87.76% Acc, 0.8469 Macro-F1)**: क्रॉस-लिंगुअल एनकोडर
       - **Google MuRIL & L3Cube HingBERT & MiniLM**: विविध आर्किटेक्चर
       - **Baseline**: वर्ड + कैरेक्टर n-ग्राम TF-IDF + लॉजिस्टिक रिग्रेशन
       - 7 उद्देश्य: `route_query`, `service_availability`, `service_timing`, `accessibility`, `ticketing`, `station_information`, `out_of_scope`

    3. **इकाई एवं स्लॉट निष्कर्षण (Entity & Slot Extraction)**:
       - बहुभाषी उपनाम शब्दकोश (Hindi, English, Tamil, Hinglish)
       - प्रस्थान (`origin`) एवं गंतव्य (`destination`) संदर्भ मार्कर (`से`, `तक`, `के लिए`, `from`, `to`)
       - सुविधा स्लॉट (`wheelchair`, `lift`, `timing`, `fare`)

    4. **ज्ञानकोष पुनर्प्राप्ति (Knowledge Base Retrieval)**:
       - स्थानीय SQLite रिलेशनल डेटाबेस (`transport.db`)
       - 13 सत्यापित CMRL स्टेशन, 42 रेल संपर्क (डायरेक्ट एवं इंटरचेंज)
       - आधिकारिक सुलभता सुविधाएं

    5. **नियतात्मक प्रतिक्रिया एवं बहुभाषी तमिल संचार (Multimodal & Bilingual Translation)**:
       - **सुरक्षित हिंदी टेम्पलेट**: कोई अनुमानित या काल्पनिक किराया/समय नहीं (Zero Hallucination)
       - **तमिल अनुवाद कार्ड**: चेन्नई बस कंडक्टरों, ऑटो चालकों व स्टेशन कर्मियों से बातचीत हेतु तत्काल तमिल अनुवाद
       - **ध्वनि पहचान (Whisper ASR)**: शून्य-लागत स्थानीय ओपन-सोर्स वाक-से-पाठ इनपुट
    """)

    st.markdown("---")
    st.markdown("#### हॉलमार्क कस्टम डिज़ाइन प्रमाणन (Hallmark Compliance Stamp)")
    st.code("""
/* Hallmark · macrostructure: Workbench · workbench knobs: layout=split-transit, tabs=live-query+network-directory
 * theme: custom · vibe: "chennai transit precision, sapphire rail, bilingual clarity" · paper: oklch(98.5% 0.006 240) · accent: oklch(56% 0.16 245)
 * display: Plus Jakarta Sans · body: Plus Jakarta Sans · outlier: JetBrains Mono · axes: light / geometric-sans / cool
 * pre-emit critique: P5 H5 E5 S5 R5 V5 · contrast: pass (40–41) · mobile: pass (34, 49, 50–57) · honest: pass (46) · chrome: pass (47) · tokens: pass (48) · responsive: pass (49) · icons: pass (30)
 * studied: no · context: explicit · v0.8.0
 */
    """, language="css")

st.markdown("<div style='margin-top: var(--space-lg);'></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: var(--color-muted); font-size: 0.8rem; font-family: var(--font-body);'>चेन्नई बहुभाषी परिवहन सहायक · CMRL NLU Urban Mobility Prototype</div>", unsafe_allow_html=True)
