"""Hindi to Tamil Machine Translation module for Chennai Transport Assistant.

Translates assistant guidance and passenger queries from Hindi to Tamil
so Hindi-speaking commuters can communicate effectively with local MTC conductors,
auto drivers, and station staff in Chennai.

Supports:
  - Neural Translation: Meta NLLB-200 (facebook/nllb-200-distilled-600M)
  - High-precision dictionary fallback for key Chennai transit entities and vocabulary.
"""

import os
import re
from typing import Dict, Optional

# Curated high-precision transit dictionary for instant translation
TRANSIT_LEXICON_HI_TA: Dict[str, str] = {
    # Stations
    "चेन्नई सेंट्रल": "சென்னை சென்ட்ரல் (Chennai Central)",
    "सेंट्रल": "சென்ட்ரல் (Central)",
    "चेन्नई एग्मोर": "சென்னை எழும்பூர் (Chennai Egmore)",
    "एग्मोर": "எழும்பூர் (Egmore)",
    "चेन्नई एयरपोर्ट": "சென்னை விமான நிலையம் (Chennai Airport)",
    "एयरपोर्ट": "விமான நிலையம் (Airport)",
    "कोयम्बेडु": "கோயம்பேடு (Koyambedu)",
    "सीएमबीटी": "சி.எம்.பி.டி (CMBT)",
    "गिंडी": "கிண்டி (Guindy)",
    "ताम्बरम": "தாம்பரம் (Tambaram)",
    "आलंदूर": "ஆலந்தூர் (Alandur)",
    "विमको नगर": "விம்கோ நகர் (Wimco Nagar)",
    "सेंट थॉमस माउंट": "பரங்கிமலை (St. Thomas Mount)",
    "चेन्नई फोर्ट": "சென்னை கோட்டை (Chennai Fort)",
    "चेन्नई पार्क": "சென்னை பூங்கா (Chennai Park)",
    "मांबलम": "மாம்பலம் (Mambalam)",
    "सैदापेट": "சைதாப்பேட்டை (Saidapet)",
    "मीनांबक्कम": "மீனம்பாக்கம் (Meenambakkam)",
    "चेन्नई बीच": "சென்னை கடற்கரை (Chennai Beach)",
    "वेलाचेरी": "வேளச்சேரி (Velachery)",
    "किल्पॉक": "கீழ்ப்பாக்கம் (Kilpauk)",
    "नेहरू पार्क": "நேரு பூங்கா (Nehru Park)",
    "तिरुमंगलम": "திருமங்கலம் (Thirumangalam)",
    "वडापलानी": "வடபழனி (Vadapalani)",
    "अशोक नगर": "அசோக் நகர் (Ashok Nagar)",
    "अन्ना नगर": "அண்ணா நகர் (Anna Nagar)",
    "नंदनम": "நந்தனம் (Nandanam)",
    "टी नगर": "தி. நகர் (T. Nagar)",

    # Corridors & Lines
    "ब्लू लाइन": "நீல வழித்தடம் (Blue Line)",
    "ग्रीन लाइन": "பச்சை வழித்தடம் (Green Line)",
    "विमको नगर - एयरपोर्ट": "விம்கோ நகர் - விமான நிலையம்",
    "सेंट्रल - सेंट थॉमस माउंट": "சென்ட்ரல் - பரங்கிமலை",

    # Modes
    "मेट्रो": "மெட்ரோ (Metro)",
    "बस": "பேருந்து (Bus)",
    "लोकल ट्रेन": "புறநகர் ரயில் (Suburban Train)",
    "उपनगरीय ट्रेन": "புறநகர் ரயில் (Suburban Train)",
    "ट्रेन": "ரயில் (Train)",

    # Facilities & Terms
    "मेट्रो स्टेशन": "மெட்ரோ நிலையம்",
    "स्टेशन": "நிலையம்",
    "लिफ्ट": "மின்தூக்கி (Lift)",
    "व्हीलचेयर सहायता": "சக்கர நாற்காலி உதவி (Wheelchair)",
    "व्हीलचेयर": "சக்கர நாற்காலி (Wheelchair)",
    "रैंप": "சாய்தளம் (Ramp)",
    "एस्केलेटर": "நகரும் படிக்கட்டு (Escalator)",
    "सुलभ शौचालय": "மாற்றுத்திறனாளி கழிப்பறை (Accessible Toilet)",
    "शौचालय": "கழிப்பறை (Restroom)",
    "पार्किंग सुविधा": "வாகனம் நிறுத்துமிடம் (Parking)",
    "पार्किंग": "வாகனம் நிறுத்துமிடம் (Parking)",
    "स्पर्श पथ": "தொடு உணர்வு பாதை (Tactile Path)",
    "दृष्टिबाधित यात्रियों के लिए स्पर्श पथ": "பார்வையற்ற பயணிகளுக்கான தொடு உணர்வு பாதை",
    "किराया": "கட்டணம் (Fare)",
    "समय": "நேரம் (Timing)",
    "समय-सारणी": "கால அட்டவணை (Timetable)",
    "उपलब्ध है": "கிடைக்கிறது",
    "उपलब्ध नहीं है": "கிடைக்கவில்லை",
    "रास्ता": "வழி (Route)",
    "हाँ": "ஆம்",
    "नहीं": "இல்லை",

    # Transit Guidance Phrases
    "डेटाबेस में": "தரவுத்தளத்தில்",
    "के लिए": "க்கான",
    "मार्ग दर्ज है": "பாதை பதிவு செய்யப்பட்டுள்ளது",
    " से ": " இருந்து ",
    "सीधी सेवा": "நேரடி சேவை",
    "इंटरचेंज आवश्यक": "மாற்று நிலையம் தேவை",
    "सुविधाएं उपलब्ध हैं": "வசதிகள் கிடைக்கின்றன",
    "सुलभता सुविधाएं": "அணுகல்தன்மை வசதிகள்",
    "आधिकारिक CMRL स्मार्ट कार्ड पर 20% छूट उपलब्ध है": "அதிகாரப்பூர்வ CMRL ஸ்மார்ட் கார்டுக்கு 20% தள்ளுபடி உள்ளது",
    "कृपया स्टेशन काउंटर या CMRL मोबाइल ऐप से सत्यापित करें": "தயவுசெய்து நிலைய கவுண்டர் அல்லது CMRL செயலியில் சரிபார்க்கவும்",
    "वास्तविक समय की लाइव ट्रेन या बस स्थिति इस प्रोटोटाइप में उपलब्ध नहीं है": "நிகழ்நேர ரயில் அல்லது பேருந்து நேரலை நிலை இந்த மாதிரியில் கிடைக்கவில்லை",
    "सत्यापित समय-सारणी इस डेटासेट में उपलब्ध नहीं है": "சரிபார்க்கப்பட்ட கால அட்டவணை இந்த தரவுத்தொகுப்பில் கிடைக்கவில்லை",
    "परिवर्तनशील किराया तालिका इस डेटासेट में उपलब्ध नहीं है": "கட்டண விபரம் இந்த தரவுத்தொகுப்பில் கிடைக்கவில்லை"
}


class HindiToTamilTranslator:
    """Translates Hindi text to Tamil for local Chennai communication."""

    def __init__(self, model_name: str = "facebook/nllb-200-distilled-600M", lazy_load: bool = True):
        self.model_name = model_name
        self.pipeline = None
        self._lazy_load = lazy_load
        if not self._lazy_load:
            self._load_model()

    def _load_model(self):
        """Loads the NLLB pipeline if not already loaded."""
        if self.pipeline is None:
            try:
                import torch
                from transformers import pipeline

                device = 0 if torch.cuda.is_available() else -1
                self.pipeline = pipeline(
                    "translation",
                    model=self.model_name,
                    src_lang="hin_Deva",
                    tgt_lang="tam_Taml",
                    device=device,
                    max_length=128
                )
            except Exception as e:
                print(f"Warning: Could not load NLLB model ({e}). Using dictionary fallback.")
                self.pipeline = None

    def translate(self, text_hi: str) -> str:
        """Translates Hindi text to Tamil."""
        if not text_hi or not text_hi.strip():
            return ""

        # First check full phrase in transit lexicon
        stripped = text_hi.strip()
        if stripped in TRANSIT_LEXICON_HI_TA:
            return TRANSIT_LEXICON_HI_TA[stripped]

        # Check if neural model can be loaded
        if not self._lazy_load:
            self._load_model()
            if self.pipeline:
                try:
                    res = self.pipeline(text_hi)
                    return res[0]["translation_text"]
                except Exception:
                    pass

        # High-quality dictionary & token replacement fallback
        translated = text_hi
        for hi_term, ta_term in sorted(TRANSIT_LEXICON_HI_TA.items(), key=lambda x: len(x[0]), reverse=True):
            if hi_term in translated:
                translated = translated.replace(hi_term, ta_term)

        # If any Tamil was introduced, return it
        has_tamil = any("\u0b80" <= ch <= "\u0bff" for ch in translated)
        if has_tamil:
            return translated

        # Standard Tamil communication card template
        return f"சென்னை போக்குவரத்து தகவல்: {text_hi}"
