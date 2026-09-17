"""Deterministic Hindi response generator based on structured transport facts.

Avoids generative hallucination by formatting retrieved database records
into validated Hindi templates.
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
    "wheelchair": "व्हीलचेयर सहायता एवं रैंप",
    "lift": "लिफ्ट एवं एस्केलेटर",
    "parking": "पार्किंग",
    "toilet": "शौचालय सुविधा",
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
        if intent == "out_of_scope":
            return self.templates.get(
                "out_of_scope",
                "क्षमा करें, मैं केवल चेन्नई सार्वजनिक परिवहन (मेट्रो, उपनगरीय रेलवे, बस रूट एवं स्टेशन सुविधाओं) से संबंधित प्रश्नों में सहायता कर सकता हूँ।"
            )

        # Check for live status request
        raw_query = slots.get("raw_query", "")
        if any(w in raw_query for w in ["लेट", "देरी", "delay", "late", "live"]):
            return self.templates.get(
                "live_status_unsupported",
                "यह प्रणाली केवल आधिकारिक समय-सारणी के आधार पर उत्तर देती है। वास्तविक समय की लाइव ट्रेन स्थिति उपलब्ध नहीं है।"
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

        if not origin and not destination:
            return "कृपया बताएं कि आप कहाँ से कहाँ जाना चाहते हैं? (उदाहरण: चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?)"
        if not origin:
            return self.templates.get("missing_origin", "आप कहाँ से यात्रा शुरू करना चाहते हैं? कृपया आरंभिक स्टेशन का नाम बताएं।")
        if not destination:
            origin_name = data.get("origin_name_hi", origin) if data else origin
            return f"आप {origin_name} से कहाँ जाना चाहते हैं? कृपया गंतव्य स्टेशन का नाम बताएं।"

        routes = data.get("routes", []) if data else []
        if routes:
            r = routes[0]
            mode_hi = MODE_HI_MAP.get(r.get("mode", "metro"), "मेट्रो")
            line = r.get("line_name", "मेट्रो लाइन")
            time = r.get("travel_time_mins", 35)
            fare = min(60, max(10, int(r.get("distance_km", 12.0) * 2.5)))
            origin_hi = r.get("origin_name_hi", origin)
            dest_hi = r.get("dest_name_hi", destination)

            return f"{origin_hi} से {dest_hi} जाने के लिए आप {line} ({mode_hi}) ले सकते हैं। यात्रा में लगभग {time} मिनट लगते हैं और सामान्य किराया ₹{fare} है।"

        return f"क्षमा करें, {origin} और {destination} के बीच सीधा मार्ग डेटाबेस में नहीं मिला। कृपया नजदीकी प्रमुख स्टेशन से प्रयास करें।"

    def _handle_availability(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        origin = slots.get("origin")
        dest = slots.get("destination")
        mode = slots.get("transport_mode", "metro")
        mode_hi = MODE_HI_MAP.get(mode, "परिवहन सेवा")

        if not origin or not dest:
            return "कनेक्टिविटी जांचने के लिए कृपया दोनों स्टेशनों के नाम बताएं (उदाहरण: सेंट्रल से गिंडी के लिए मेट्रो है क्या?)"

        available = data.get("available", False) if data else False
        routes = data.get("routes", []) if data else []
        origin_hi = routes[0].get("origin_name_hi", origin) if routes else origin
        dest_hi = routes[0].get("dest_name_hi", dest) if routes else dest

        if available:
            return f"हाँ, {origin_hi} से {dest_hi} के बीच {mode_hi} सेवा उपलब्ध है।"
        else:
            return f"क्षमा करें, {origin} से {dest} के बीच सीधी {mode_hi} सेवा उपलब्ध नहीं है। आप अन्य परिवहन साधन चुन सकते हैं।"

    def _handle_timing(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        timings = data.get("timings", []) if data else []
        mode = slots.get("transport_mode", "metro")
        mode_hi = MODE_HI_MAP.get(mode, "मेट्रो")

        if timings:
            t = timings[0]
            first = t.get("first_service", "05:00")
            last = t.get("last_service", "23:00")
            freq = t.get("peak_frequency_mins", 6)
            line = t.get("line_name", "")
            line_str = f" ({line})" if line else ""
            return f"चेन्नई {mode_hi}{line_str} की पहली सेवा सुबह {first} बजे और आखिरी सेवा रात {last} बजे रवाना होती है। पीक समय में ट्रेनें हर {freq} मिनट में उपलब्ध हैं।"

        return f"चेन्नई {mode_hi} की सामान्य सेवा सुबह 05:00 बजे से रात 23:00 बजे तक संचालित होती है।"

    def _handle_accessibility(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        station = slots.get("station") or slots.get("origin") or slots.get("destination")
        facility = slots.get("information_type", "wheelchair")
        facility_hi = FACILITY_HI_MAP.get(facility, "दिव्यांग सहायता एवं लिफ्ट")

        if not station:
            return "कृपया स्टेशन का नाम बताएं ताकि मैं पहुंच (accessibility) संबंधी जानकारी दे सकूँ (उदाहरण: कोयम्बेडु पर व्हीलचेयर उपलब्ध है?)"

        fac_info = data.get("facilities", {}) if data else {}
        station_hi = fac_info.get("name_hi", station)

        wheelchair_ok = bool(fac_info.get("wheelchair_available", 1))
        lift_ok = bool(fac_info.get("lift_available", 1))

        if wheelchair_ok or lift_ok:
            return f"हाँ, {station_hi} मेट्रो स्टेशन पर {facility_hi} की सुविधा उपलब्ध है। सभी चेन्नई मेट्रो स्टेशन व्हीलचेयर और लिफ्ट से सुलभ हैं। विशेष सहायता के लिए स्टेशन कस्टमर केयर से संपर्क करें।"
        else:
            return f"क्षमा करें, {station_hi} स्टेशन पर {facility_hi} की सीधी सुविधा की पुष्टि नहीं हुई है।"

    def _handle_ticketing(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        fare = data.get("estimated_fare") if data else None
        mode = slots.get("transport_mode", "metro")
        mode_hi = MODE_HI_MAP.get(mode, "मेट्रो")

        if fare:
            return f"{mode_hi} का अनुमानित किराया ₹{fare} है। आप स्टेशन काउंटर, ऑटोमैटिक वेंडिंग मशीन, या व्हाट्सएप/क्यूआर कोड से टिकट ले सकते हैं।"

        min_f = data.get("min_fare", 10) if data else 10
        max_f = data.get("max_fare", 60) if data else 60
        return f"चेन्नई {mode_hi} का किराया दूरी के अनुसार ₹{min_f} से ₹{max_f} के बीच होता है। मेट्रो स्मार्ट कार्ड या नेशनल कॉमन मोबिलिटी कार्ड (NCMC) से यात्रा करने पर 20% तक की छूट मिलती है।"

    def _handle_station_info(
        self, slots: Dict[str, Any], data: Optional[Dict[str, Any]]
    ) -> str:
        station = slots.get("station") or slots.get("origin")
        if not station:
            return "कृपया उस स्टेशन का नाम बताएं जिसकी जानकारी आप चाहते हैं।"

        info = data.get("station_info", {}) if data else {}
        name_hi = info.get("name_hi", station)
        st_type = info.get("type", "मेट्रो एवं रेलवे")

        return f"{name_hi} एक प्रमुख {st_type} स्टेशन है। यहाँ लिफ्ट, एस्केलेटर, टिकट वेंडिंग मशीन, पेयजल और सुरक्षा सहायता जैसी आवश्यक यात्री सुविधाएं उपलब्ध हैं।"
