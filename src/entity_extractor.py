"""Entity and Slot Extraction module for Chennai transport domain.

Uses a gazetteer of stations and aliases, directional postposition heuristics,
and RapidFuzz fallback matching to extract:
  - origin (canonical station id)
  - destination (canonical station id)
  - transport_mode (metro, bus, suburban_rail, railway)
  - information_type (wheelchair, lift, parking, fare, timing, etc.)
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Any
from rapidfuzz import fuzz, process

from src.normalization import normalize_text


# Default gazetteer of major Chennai transit hubs and aliases
DEFAULT_GAZETTEER: Dict[str, Dict[str, Any]] = {
    "CHENNAI_CENTRAL": {
        "canonical_name_en": "Chennai Central",
        "canonical_name_hi": "चेन्नई सेंट्रल",
        "aliases": [
            "चेन्नई सेंट्रल", "सेंट्रल", "एमजीआर सेंट्रल", "मद्रास सेंट्रल",
            "puratchi thalaivar dr mgr central", "chennai central", "central", "mgr central"
        ]
    },
    "CHENNAI_EGMORE": {
        "canonical_name_en": "Chennai Egmore",
        "canonical_name_hi": "चेन्नई एग्मोर",
        "aliases": [
            "चेन्नई एग्मोर", "एग्मोर", "एगमोर",
            "chennai egmore", "egmore"
        ]
    },
    "CHENNAI_AIRPORT": {
        "canonical_name_en": "Chennai Airport",
        "canonical_name_hi": "चेन्नई एयरपोर्ट",
        "aliases": [
            "चेन्नई एयरपोर्ट", "एयरपोर्ट", "हवाई अड्डा", "मीनम्बाक्कम एयरपोर्ट",
            "chennai airport", "airport", "meenambakkam airport"
        ]
    },
    "KOYAMBEDU": {
        "canonical_name_en": "Koyambedu",
        "canonical_name_hi": "कोयम्बेडु",
        "aliases": [
            "कोयम्बेडु", "कोयम्बेडू", "कोयम्बेडु मेट्रो",
            "koyambedu", "koyambedu metro", "koyambedu market"
        ]
    },
    "CMBT": {
        "canonical_name_en": "CMBT",
        "canonical_name_hi": "सीएमबीटी",
        "aliases": [
            "सीएमबीटी", "सीएमबीटी मेट्रो",
            "cmbt", "cmbt metro", "puratchi thalaivi dr j jayalalithaa cmbt"
        ]
    },
    "GUINDY": {
        "canonical_name_en": "Guindy",
        "canonical_name_hi": "गिंडी",
        "aliases": [
            "गिंडी", "गुइंडी", "गिंडी स्टेशन", "गिंडी मेट्रो",
            "guindy", "guindy station", "guindy metro"
        ]
    },
    "ALANDUR": {
        "canonical_name_en": "Alandur",
        "canonical_name_hi": "आलंदूर",
        "aliases": [
            "आलंदूर", "अलनदूर", "आलंदुर", "आलंदूर मेट्रो",
            "alandur", "alandur metro"
        ]
    },
    "VADAPALANI": {
        "canonical_name_en": "Vadapalani",
        "canonical_name_hi": "वडापलानी",
        "aliases": [
            "वडापलानी", "वडापलानी मेट्रो",
            "vadapalani", "vadapalani metro"
        ]
    },
    "SHENOY_NAGAR": {
        "canonical_name_en": "Shenoy Nagar",
        "canonical_name_hi": "शेनॉय नगर",
        "aliases": [
            "शेनॉय नगर", "शेनॉय नगर मेट्रो",
            "shenoy nagar", "shenoy nagar metro"
        ]
    },
    "NANDANAM": {
        "canonical_name_en": "Nandanam",
        "canonical_name_hi": "नंदनम",
        "aliases": [
            "नंदनम", "नंदनम मेट्रो", "टी नगर मेट्रो",
            "nandanam", "nandanam metro", "t nagar metro"
        ]
    },
    "WASHERMANPET": {
        "canonical_name_en": "Washermanpet",
        "canonical_name_hi": "वाशरमैनपेट",
        "aliases": [
            "वाशरमैनपेट", "वाशरमैनपेट मेट्रो",
            "washermanpet", "washermanpet metro"
        ]
    },
    "WIMCO_NAGAR": {
        "canonical_name_en": "Wimco Nagar",
        "canonical_name_hi": "विमको नगर",
        "aliases": [
            "विमको नगर", "विमको नगर डिपो", "विमको नगर मेट्रो",
            "wimco nagar", "wimco nagar depot", "wimco nagar metro"
        ]
    },
    "ST_THOMAS_MOUNT": {
        "canonical_name_en": "St. Thomas Mount",
        "canonical_name_hi": "सेंट थॉमस माउंट",
        "aliases": [
            "सेंट थॉमस माउंट", "थॉमस माउंट", "सेंट थॉमस माउंट मेट्रो",
            "st thomas mount", "st. thomas mount", "thomas mount", "st thomas mount metro"
        ]
    }
}

# Mode keywords
TRANSPORT_MODES: Dict[str, str] = {
    "मेट्रो": "metro",
    "metro": "metro",
    "बस": "bus",
    "bus": "bus",
    "एमटीसी": "bus",
    "mtc": "bus",
    "लोकल": "suburban_rail",
    "लोकल ट्रेन": "suburban_rail",
    "suburban": "suburban_rail",
    "suburban train": "suburban_rail",
    "ट्रेन": "railway",
    "रेल": "railway",
    "train": "railway",
    "rail": "railway",
    "एमआरटीएस": "suburban_rail",
    "mrts": "suburban_rail"
}

# Facility keywords
FACILITY_TYPES: Dict[str, str] = {
    "wheelchair": "wheelchair",
    "व्हीलचेयर": "wheelchair",
    "व्हील चेयर": "wheelchair",
    "दिव्यांग": "wheelchair",
    "दिव्यांगों": "wheelchair",
    "विकलांग": "wheelchair",
    "विकलांगों": "wheelchair",
    "lift": "lift",
    "लिफ्ट": "lift",
    "एलिवेटर": "lift",
    "elevator": "lift",
    "escalator": "lift",
    "एस्केलेटर": "lift",
    "parking": "parking",
    "पार्किंग": "parking",
    "दिव्यांग शौचालय": "accessible_toilet",
    "accessible toilet": "accessible_toilet",
    "toilet": "accessible_toilet",
    "टॉयलेट": "accessible_toilet",
    "शौचालय": "accessible_toilet",
    "washroom": "accessible_toilet",
    "tactile": "tactile_paths",
    "tactile path": "tactile_paths",
    "स्पर्श पथ": "tactile_paths",
    "दृष्टिहीन": "tactile_paths",
    "दृष्टिबाधित": "tactile_paths",
    "fare": "fare",
    "किराया": "fare",
    "टिकट": "fare",
    "ticket": "fare",
    "price": "fare",
    "card": "fare",
    "कार्ड": "fare",
    "smart card": "fare",
    "स्मार्ट कार्ड": "fare",
    "पास": "fare",
    "pass": "fare",
    "टोकन": "fare",
    "token": "fare",
    "एनसीएमसी": "fare",
    "ncmc": "fare",
    "डिस्काउंट": "fare",
    "discount": "fare",
    "timing": "timing",
    "समय": "timing",
    "टाइम": "timing",
    "time": "timing",
    "first": "timing",
    "last": "timing",
    "pehli": "timing",
    "पहली": "timing",
    "aakhiri": "timing",
    "आखिरी": "timing",
    "लास्ट": "timing",
    "frequency": "timing",
    "फ्रिक्वेंसी": "timing",
    "hours": "timing",
    "operating": "timing",
    "कितने बजे": "timing",
    "baje": "timing",
    "बजे": "timing",
    "subah": "timing",
    "सुबह": "timing",
    "देर": "timing",
    "der": "timing",
    "कब": "timing",
    "kab": "timing",
    "ramp": "ramp",
    "रैंप": "ramp"
}


class EntityExtractor:
    """Extracts transport domain entities using gazetteer and fuzzy matching."""

    def __init__(self, gazetteer: Optional[Dict[str, Dict[str, Any]]] = None):
        self.gazetteer = gazetteer or DEFAULT_GAZETTEER
        # Build inverted alias lookup: alias_normalized -> station_id
        self.alias_to_id: Dict[str, str] = {}
        self.sorted_aliases: List[Tuple[str, str]] = []

        for station_id, data in self.gazetteer.items():
            for alias in data.get("aliases", []):
                norm_alias = normalize_text(alias)
                if norm_alias:
                    self.alias_to_id[norm_alias] = station_id
                    self.sorted_aliases.append((norm_alias, station_id))

        # Sort aliases by length descending so longer aliases match first
        self.sorted_aliases.sort(key=lambda x: len(x[0]), reverse=True)

    def extract(self, query: str) -> Dict[str, Any]:
        """Extracts slots from query text.

        Returns:
            Dictionary containing:
                origin: Optional[str] canonical station id
                destination: Optional[str] canonical station id
                transport_mode: Optional[str] (metro, bus, suburban_rail, railway)
                information_type: Optional[str]
                station: Optional[str] (when only one station is specified)
        """
        norm_query = normalize_text(query)

        # 1. Extract Transport Mode
        mode = self._extract_mode(norm_query)

        # 2. Extract Information / Facility Type
        info_type = self._extract_info_type(norm_query)

        # 3. Extract Stations with directional cues
        origin, destination, single_station = self._extract_stations(norm_query, has_facility=bool(info_type))

        return {
            "origin": origin,
            "destination": destination,
            "station": single_station,
            "transport_mode": mode,
            "facility": info_type,
            "information_type": info_type,
            "raw_query": query,
            "normalized_query": norm_query
        }

    def _extract_mode(self, text: str) -> Optional[str]:
        """Identifies transport mode keyword."""
        # Longest keys first
        for keyword in sorted(TRANSPORT_MODES.keys(), key=len, reverse=True):
            pattern = r"(?<!\S)" + re.escape(keyword) + r"(?!\S)"
            if re.search(pattern, text):
                return TRANSPORT_MODES[keyword]
        return None

    def _extract_info_type(self, text: str) -> Optional[str]:
        """Identifies facility or info query keyword."""
        for keyword in sorted(FACILITY_TYPES.keys(), key=len, reverse=True):
            pattern = r"(?<!\S)" + re.escape(keyword) + r"(?!\S)"
            if re.search(pattern, text):
                return FACILITY_TYPES[keyword]
        return None

    def _extract_stations(
        self, text: str, has_facility: bool = False
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Identifies stations in the text and assigns origin/destination

        based on postpositions ('से' = from, 'तक' / 'को' / 'के लिए' / 'to' = to).
        """
        matched_spans: List[Dict[str, Any]] = []

        # Find exact alias matches
        for alias, station_id in self.sorted_aliases:
            pattern = r"(?<!\S)" + re.escape(alias) + r"(?!\S)"
            for match in re.finditer(pattern, text):
                start, end = match.span()
                # Check for overlapping span with already matched longer alias
                overlap = any(
                    (start >= s["start"] and start < s["end"]) or
                    (end > s["start"] and end <= s["end"])
                    for s in matched_spans
                )
                if not overlap:
                    matched_spans.append({
                        "station_id": station_id,
                        "alias": alias,
                        "start": start,
                        "end": end
                    })

        # If fewer than 2 matches, attempt fuzzy fallback on candidate tokens
        if len(matched_spans) < 2:
            matched_spans = self._fuzzy_station_fallback(text, matched_spans)

        # Sort matches by appearance in text
        matched_spans.sort(key=lambda x: x["start"])

        if not matched_spans:
            return None, None, None

        if len(matched_spans) == 1:
            station_id = matched_spans[0]["station_id"]
            subsequent_text = text[matched_spans[0]["end"]:]
            prior_text = text[:matched_spans[0]["start"]]
            is_timing = any(w in text for w in [
                "timing", "पहली", "pehli", "पहला", "first", "आखिरी", "aakhiri",
                "last", "सुबह", "subah", "छूटती", "nikalti", "kitne baje", "baje"
            ])

            if is_timing:
                return station_id, None, station_id
            elif re.search(r"^\s*(?:से|se|from)(?!\S)", subsequent_text) or re.search(r"(?<!\S)(?:from)\s*$", prior_text):
                return station_id, None, None
            elif re.search(r"^\s*(?:पर|में|par|mein)(?!\S)", subsequent_text) or has_facility:
                return None, None, station_id
            elif re.search(r"^\s*(?:तक|को|के लिए|ke liye|to)(?!\S)", subsequent_text) or re.search(r"(?<!\S)(?:to)\s*$", prior_text) or re.search(r"(?:जाना|जाऊँ|जाएं|पहुंच|kaise jau|kaise jaye|route|available|उपलब्ध)", text):
                return None, station_id, None
            else:
                return None, None, station_id

        # Two or more stations matched: determine origin vs destination
        origin = None
        destination = None

        first = matched_spans[0]
        second = matched_spans[1]

        # Look at intermediate text between first and second station
        between = text[first["end"]:second["start"]]
        after_second = text[second["end"]:]

        if re.search(r"(?<!\S)(?:से|se|from)(?!\S)", between):
            origin = first["station_id"]
            destination = second["station_id"]
        elif re.search(r"(?<!\S)(?:से|se|from)(?!\S)", after_second):
            origin = second["station_id"]
            destination = first["station_id"]
        elif re.search(r"(?<!\S)to(?!\S)", between):
            origin = first["station_id"]
            destination = second["station_id"]
        else:
            # By standard convention: First mentioned is origin, second is destination
            origin = first["station_id"]
            destination = second["station_id"]

        return origin, destination, None

    def _fuzzy_station_fallback(
        self, text: str, matched_spans: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Uses RapidFuzz to match candidate n-grams against station aliases."""
        tokens = text.split()
        existing_ids = {s["station_id"] for s in matched_spans}
        all_alias_strings = list(self.alias_to_id.keys())

        # Check unigrams and bigrams
        for n in [2, 1]:
            for i in range(len(tokens) - n + 1):
                candidate = " ".join(tokens[i:i + n])
                if len(candidate) < 3:
                    continue

                best = process.extractOne(
                    candidate,
                    all_alias_strings,
                    scorer=fuzz.ratio,
                    score_cutoff=85
                )
                if best:
                    matched_alias, score, _ = best
                    station_id = self.alias_to_id[matched_alias]
                    if station_id not in existing_ids:
                        # Find approximate start/end in text
                        match_idx = text.find(candidate)
                        if match_idx != -1:
                            matched_spans.append({
                                "station_id": station_id,
                                "alias": candidate,
                                "start": match_idx,
                                "end": match_idx + len(candidate),
                                "fuzzy_score": score
                            })
                            existing_ids.add(station_id)
        return matched_spans
