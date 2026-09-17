"""Streamlit Web Application for Hindi Multimodal Transport Assistant for Chennai.

Provides an interactive user interface for querying Chennai transit in Hindi
and Hinglish with detailed NLU inspector and deterministic response generation.
"""

import os
import sys

# Ensure repository root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.pipeline import TransportAssistant

# Page Configuration
st.set_page_config(
    page_title="चेन्नई परिवहन सहायक (Chennai Transport Assistant)",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .response-card {
        background-color: #F0FDF4;
        border-left: 5px solid #22C55E;
        padding: 1.2rem;
        border-radius: 8px;
        font-size: 1.2rem;
        font-weight: 500;
        color: #14532D;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .slot-badge {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_assistant(model_type: str = "baseline") -> TransportAssistant:
    """Initializes and caches the Transport Assistant pipeline."""
    return TransportAssistant(model_type=model_type)


# Sidebar Configuration
with st.sidebar:
    st.title("⚙️ नियंत्रण पैनल")
    st.markdown("**Hindi Multimodal Transport Assistant**")
    st.markdown("चेन्नई सार्वजनिक परिवहन के लिए प्राकृतिक भाषा समझ (NLU)")

    model_option = st.selectbox(
        "🧠 NLU मॉडल चुनें (Model)",
        ["baseline (TF-IDF + LR)", "muril (Transformer)"],
        index=0
    )
    selected_model = "muril" if "muril" in model_option else "baseline"

    st.markdown("---")
    st.subheader("📚 डेमो उदाहरण (पूर्ण नेटवर्क नहीं)")
    st.markdown("""
    - 🚇 **चेन्नई मेट्रो (CMRL)**: ब्लू एवं ग्रीन लाइन
    - 🚆 **उपनगरीय रेलवे (SR)**: बीच - तांबरम - चेंगलपट्टू
    - 🚌 **एमटीसी बसें (MTC)**: प्रमुख शहर मार्ग
    - ♿ **सुलभता (Accessibility)**: दर्ज व्यक्तिगत सुविधाएं
    """)

    st.markdown("---")
    show_dev_info = st.checkbox("🔍 डेवलपर इंस्पेक्टर (Debug Mode)", value=False)
    st.caption("लागत: ₹0 | स्थानीय प्रोटोटाइप")


# Initialize assistant
assistant = get_assistant(model_type=selected_model)

# Header
st.markdown('<div class="main-title">🚇 चेन्नई बहुभाषी परिवहन सहायक</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hindi Multimodal Transport Assistant for Chennai Using NLP</div>', unsafe_allow_html=True)

st.warning("डेमो डेटा सत्यापित नहीं है। यात्रा से पहले संचालक से पुष्टि करें। समय-सारणी और किराया उपलब्ध नहीं हैं।")
st.caption("हर प्रश्न में पूरी जानकारी दें; पिछले प्रश्न की जानकारी याद नहीं रखी जाती।")

# Quick Query Suggestions
st.markdown("**त्वरित प्रश्न (Quick Sample Queries):**")
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

query_input = ""
with col1:
    if st.button("📍 चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?"):
        query_input = "चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?"
with col2:
    if st.button("🚇 सेंट्रल से गिंडी के लिए मेट्रो है क्या?"):
        query_input = "सेंट्रल से गिंडी के लिए मेट्रो है क्या?"
with col3:
    if st.button("♿ कोयम्बेडु पर व्हीलचेयर उपलब्ध है?"):
        query_input = "कोयम्बेडु पर व्हीलचेयर उपलब्ध है?"
with col4:
    if st.button("⏰ आखिरी मेट्रो कितने बजे छूटती है?"):
        query_input = "आखिरी मेट्रो कितने बजे छूटती है?"
with col5:
    if st.button("🎟️ मेट्रो का किराया कितना है?"):
        query_input = "मेट्रो का किराया कितना है?"
with col6:
    if st.button("🔤 central se airport route"):
        query_input = "central se airport route"

# Main Text Input
user_query = st.text_input(
    "अपना प्रश्न हिंदी या हिंग्लिश में लिखें (Ask your question in Hindi / Hinglish):",
    value=query_input,
    placeholder="उदाहरण: चेन्नई सेंट्रल से एग्मोर कैसे जाएँ या airport ke liye metro hai kya?"
)

if user_query:
    with st.spinner("प्रश्न का विश्लेषण और डेटाबेस खोज जारी है..."):
        result = assistant.process_query(user_query)

    if result["model_backend"] == "heuristic":
        st.caption("नियम-आधारित डेमो: प्रशिक्षित मॉडल उपलब्ध नहीं है; स्कोर अनुमान है।")

    # 1. Main Response Card
    st.markdown("### 💬 उत्तर (Response):")
    st.markdown(f'<div class="response-card">{result["response_hi"]}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 2. Structured Analysis Cards
    st.markdown("### 📋 प्राकृतिक भाषा विश्लेषण (NLU Pipeline Breakdown)")

    meta_col1, meta_col2, meta_col3 = st.columns(3)
    with meta_col1:
        st.metric(
            label="🎯 पहचाना गया उद्देश्य (Intent)",
            value=result["intent"],
            delta=f"{result['confidence'] * 100:.1f}% Confidence"
        )
    with meta_col2:
        orig = result["slots"].get("origin") or "निर्दिष्ट नहीं (Not specified)"
        st.metric(label="🚩 प्रस्थान (Origin)", value=orig)
    with meta_col3:
        dest = result["slots"].get("destination") or "निर्दिष्ट नहीं (Not specified)"
        st.metric(label="🏁 गंतव्य (Destination)", value=dest)

    # Secondary Slots
    sec_col1, sec_col2 = st.columns(2)
    with sec_col1:
        mode_val = result["slots"].get("transport_mode") or "ऑटो-डिटेक्ट / कोई भी (Any)"
        st.markdown(f"**परिवहन साधन (Mode):** `{mode_val}`")
    with sec_col2:
        info_val = result["slots"].get("information_type") or "सामान्य मार्ग (General)"
        st.markdown(f"**जानकारी प्रकार (Info Type):** `{info_val}`")

    # Developer / Debug Inspector Drawer
    if show_dev_info:
        with st.expander("🛠️ तकनीकी विवरण एवं डेटाबेस परिणाम (Developer Inspector)", expanded=False):
            st.json({
                "raw_query": result["raw_query"],
                "normalized_query": result["normalized_query"],
                "intent": result["intent"],
                "confidence": result["confidence"],
                "slots": result["slots"],
                "retrieved_database_records": result["db_result"]
            })

else:
    st.info("👆 ऊपर दिए गए उदाहरण प्रश्नों पर क्लिक करें या अपना प्रश्न टाइप करें।")
