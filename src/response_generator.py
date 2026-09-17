"""Deterministic Hindi response generator based on structured transport facts.

Formats database records without inferring missing facts. The pipeline marks
bundled records as unverified demo data.
"""

import json
import os
from typing import Dict, Any, Optional

# Standard Hindi names for canonical transport modes
MODE_HI_MAP = {
    "metro": "मेट्रो",
    "bus": "बस",
    "suburban_rail": "उपनगरीय ट्रेन (लोकल)",
    "railway": "ट्रेन"
}

# Facility names in Hindi
FACILITY_HI_MAP = {
    "wheelchair": "व्हीलचेयर सहायता",
    "lift": "लिफ्ट",
    "parking": "पार्किंग",
    "toilet": "शौचालय सुविधा",
    "accessible_toilet": "दिव्यांग शौचालय सुविधा",
    "ramp": "रैंप एवं लिफ्ट",
    "tactile_paths": "दृष्टिबाधित यात्रियों के लिए स्पर्श पथ (tactile path)"
}


class ResponseGenerator:
    """Constructs deterministic Hindi text responses from NLU slots and database results."""

    def __init__(self, templates_path: Optional[str] = None):
        if templates_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            templates_path = os.path.join(base_dir, "data", "templates", "hindi_templates.json")

        self.templates: Dict[str, str] = {}
        if os.path.exists(templates_path):
            with open(templates_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.templates = data.get("response_templates_hi", {})

    def generate(
        self,
        intent: str,
        slots: Dict[str, Any],
        retrieval_data: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0
    ) -> str:
        """Generates a clear Hindi response string."""
        # Check for live status request first with token and phrase checks
        raw_query = (slots.get("raw_query") or "").lower()
        raw_tokens = set(raw_query.split())
        live_tokens = {"लेट", "देरी", "delay", "late", "live", "track"}
        live_phrases = ["कहाँ पहुँची", "kahan pahuchi", "लाइव स्थिति", "live status", "कहाँ पहुंची"]
        if (raw_tokens & live_tokens) or any(p in raw_query for p in live_phrases):
            return self.templates.get(
                "live_status_unsupported",
                "वास्तविक समय की लाइव ट्रेन या बस स्थिति इस प्रोटोटाइप में उपलब्ध नहीं है।"
            )

        if intent == "out_of_scope":
            return self.templates.get(
                "out_of_scope",
                "क्षमा करें, मैं केवल चेन्नई सार्वजनिक परिवहन (मेट्रो, उपनगरीय रेलवे, बस रूट एवं स्टेशन सुविधाओं) से संबंधित प्रश्नों में सहायता कर सकता हूँ।"
            )

        # Handle Route Query
        if intent == "route_query":
            return self._handle_route_query(slots, retrieval_data)

        # Handle Service Availability
        elif intent == "service_availability":
            return self._handle_availability(slots, retrieval_data)

        # Handle Service Timing
        elif intent == "service_timing":
            return self._handle_timing(slots, retrieval_data)

        # Handle Accessibility
        elif intent == "accessibility":
            return self._handle_accessibility(slots, retrieval_data)

        # Handle Ticketing
        elif intent == "ticketing":
            return self._handle_ticketing(slots, retrieval_data)

        # Handle Station Information
        elif intent == "station_information":
            return self._handle_station_info(slots, retrieval_data)

        # Generic fallback
        return "मुझे आपका प्रश्न समझ नहीं आया। कृपया अपना प्रश्न चेन्नई परिवहन से संबंधित स्पष्ट शब्दों में पूछें।"

    def _handle_route_query(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        origin = slots.get("origin")
        destination = slots.get("destination")
        origin_hi = (data or {}).get("origin_name_hi") or origin
        dest_hi = (data or {}).get("dest_name_hi") or destination

        if not origin and not destination:
            return "कृपया बताएं कि आप कहाँ से कहाँ जाना चाहते हैं? (उदाहरण: चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?)"
        if not origin:
            return f"आप कहाँ से {dest_hi} जाना चाहते हैं? कृपया अपने आरंभिक स्टेशन का नाम बताएं।"
        if not destination:
            return f"आप {origin_hi} से कहाँ जाना चाहते हैं? कृपया अपने गंतव्य स्टेशन का नाम बताएं।"

        routes = data.get("routes", []) if data else []
        if routes:
            r = routes[0]
            mode_hi = MODE_HI_MAP.get(r.get("mode", "metro"), "मेट्रो")
            line = r.get("line_name", "मेट्रो लाइन")
            is_direct = r.get("direct", 1) == 1
            origin_hi = r.get("origin_name_hi") or origin_hi
            dest_hi = r.get("dest_name_hi") or dest_hi
            transfer_note = " (यात्रा में लाइन बदलना / इंटरचेंज आवश्यक है)" if not is_direct else ""
            return f"डेटाबेस में {origin_hi} से {dest_hi} के लिए {line} ({mode_hi}) मार्ग दर्ज है।{transfer_note}"

        return f"क्षमा करें, {origin_hi} और {dest_hi} के बीच सीधा मार्ग डेटाबेस में नहीं मिला। कृपया नजदीकी प्रमुख स्टेशन से प्रयास करें।"

    def _handle_availability(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        origin = slots.get("origin")
        dest = slots.get("destination")
        mode = slots.get("transport_mode", "metro")
        mode_hi = MODE_HI_MAP.get(mode, "परिवहन सेवा")
        origin_hi = (data or {}).get("origin_name_hi") or origin
        dest_hi = (data or {}).get("dest_name_hi") or dest

        if not origin or not dest:
            if dest and not origin:
                return f"आप कहाँ से {dest_hi} जाना चाहते हैं? कनेक्टिविटी जांचने के लिए कृपया आरंभिक स्टेशन का नाम बताएं।"
            if origin and not dest:
                return f"आप {origin_hi} से कहाँ जाना चाहते हैं? कनेक्टिविटी जांचने के लिए कृपया गंतव्य स्टेशन का नाम बताएं।"
            return "कनेक्टिविटी जांचने के लिए कृपया दोनों स्टेशनों के नाम बताएं (उदाहरण: सेंट्रल से गिंडी के लिए मेट्रो है क्या?)"

        available = data.get("available", False) if data else False
        routes = data.get("routes", []) if data else []
        if routes:
            origin_hi = routes[0].get("origin_name_hi") or origin_hi
            dest_hi = routes[0].get("dest_name_hi") or dest_hi

        if available:
            direct = any(r.get("direct") == 1 for r in routes)
            detail = "सीधी सेवा" if direct else "बदलाव (इंटरचेंज) वाला मार्ग"
            return f"हाँ, डेटाबेस में {origin_hi} से {dest_hi} के बीच {mode_hi} का {detail} दर्ज है।"
        else:
            return f"क्षमा करें, {origin_hi} से {dest_hi} के बीच {mode_hi} सेवा की जानकारी डेटाबेस में नहीं मिली। इससे सेवा बंद होने की पुष्टि नहीं होती।"

    def _handle_timing(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        # The MVP has no station/direction/calendar-aware timetable.
        return "इस प्रोटोटाइप में सत्यापित समय-सारणी उपलब्ध नहीं है। पहली या आखिरी सेवा का समय संबंधित परिवहन संचालक से जांचें।"

    def _handle_accessibility(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        station = slots.get("station") or slots.get("origin") or slots.get("destination")
        facility = slots.get("information_type", "wheelchair")
        facility_hi = FACILITY_HI_MAP.get(facility, "दिव्यांग सहायता एवं लिफ्ट")

        if not station:
            return "कृपया स्टेशन का नाम बताएं ताकि मैं पहुंच (accessibility) संबंधी जानकारी दे सकूँ (उदाहरण: कोयम्बेडु पर व्हीलचेयर उपलब्ध है?)"

        fac_info = (data or {}).get("facilities") or {}
        station_hi = fac_info.get("name_hi", station)
        columns = {
            "wheelchair": "wheelchair_available", "lift": "lift_available",
            "parking": "parking_available", "toilet": "accessible_toilet",
            "accessible_toilet": "accessible_toilet", "ramp": "lift_available",
            "tactile_paths": "tactile_paths",
        }
        value = fac_info.get(columns.get(facility, "wheelchair_available"))
        if value == 1:
            return f"हाँ, डेटाबेस के अनुसार {station_hi} स्टेशन पर {facility_hi} उपलब्ध है। यह वर्तमान कार्यशील स्थिति की पुष्टि नहीं है।"
        if value == 0:
            return f"डेटाबेस के अनुसार {station_hi} स्टेशन पर {facility_hi} उपलब्ध नहीं है।"
        return f"{station_hi} स्टेशन पर इस सुविधा की जानकारी उपलब्ध नहीं है।"

    def _handle_ticketing(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        return "इस प्रोटोटाइप में सत्यापित किराया और टिकट नियम उपलब्ध नहीं हैं। कृपया संबंधित परिवहन संचालक से जांचें।"

    def _handle_station_info(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        station = slots.get("station") or slots.get("origin")
        if not station:
            return "कृपया उस स्टेशन का नाम बताएं जिसकी जानकारी आप चाहते हैं।"

        info = (data or {}).get("station_info") or {}
        if not info:
            return "इस स्टेशन की जानकारी डेटाबेस में उपलब्ध नहीं है।"
        name_hi = info.get("name_hi", station)
        return f"{name_hi} स्टेशन डेटाबेस में दर्ज है। सुविधाओं के लिए किसी विशेष सुविधा का नाम देकर पूछें।"
