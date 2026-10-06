"""Explicit multilingual T3 slot extraction with separate uncertainty metadata."""

from dataclasses import dataclass
from datetime import date as calendar_date
import re
import unicodedata

from src.normalization import normalize_text
from src.nlp_v2.contracts import ContractError, T3_INTENTS
from src.nlp_v2.entities import CanonicalResolver, EntitySpan, Resolution


MODE_PATTERNS = {
    "metro": r"(?<!\w)(?:metro|मेट्रो)(?!\w)",
    "bus": r"(?<!\w)(?:bus|बस)(?!\w)",
    "suburban_rail": r"(?<!\w)(?:suburban(?:\s+rail)?|local\s+train|लोकल\s+ट्रेन)(?!\w)",
    "mrts": r"(?<!\w)(?:mrts|एमआरटीएस)(?!\w)",
}
FACILITIES = {
    "parking": ("parking", "पार्किंग"),
    "restroom": ("restroom", "toilet", "शौचालय"),
    "waiting_room": ("waiting room", "प्रतीक्षालय"),
    "cloak_room": ("cloak room", "क्लोक रूम"),
    "atm": ("atm", "एटीएम"),
    "wifi": ("wifi", "wi fi", "वाईफाई"),
    "drinking_water": ("drinking water", "पीने का पानी"),
}
ACCESSIBILITY = {
    "wheelchair": ("wheelchair", "व्हीलचेयर", "व्हीलचेयर"),
    "lift": ("lift", "elevator", "लिफ्ट"),
    "escalator": ("escalator", "एस्केलेटर"),
    "ramp": ("ramp", "रैंप"),
    "accessible_toilet": ("accessible toilet", "दिव्यांग शौचालय"),
    "tactile_paths": ("tactile", "स्पर्श पथ"),
}
TICKETS = {
    "smart_card": ("smart card", "स्मार्ट कार्ड"),
    "ncmc_card": ("ncmc", "एनसीएमसी"),
    "qr_ticket": ("qr ticket", "क्यूआर टिकट"),
    "monthly_pass": ("monthly pass", "मासिक पास"),
    "tourist_pass": ("tourist pass", "पर्यटक पास"),
    "season_pass": ("season pass", "सीजन पास"),
    "token": ("token", "टोकन"),
}
PREFERENCES = {
    "fastest": ("fastest", "सबसे तेज"),
    "cheapest": ("cheapest", "सबसे सस्ता"),
    "least_transfers": ("least transfers", "fewest changes"),
    "direct_only": ("direct only", "सीधा"),
}
LINE_NAMES = ("Blue Line", "Green Line", "Corridor 1", "Corridor 2", "MRTS", "North Line", "South Line", "West Line")


@dataclass(frozen=True)
class ExtractionResult:
    slots: dict[str, object]
    spans: tuple[EntitySpan, ...]
    unresolved: tuple[Resolution, ...]
    clarification_reason: str | None
    requested_modes: tuple[str, ...]
    normalized_query: str


def _has(text: str, phrase: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(normalize_text(phrase)) + r"(?!\w)", text) is not None


def _enum(text: str, vocabulary: dict[str, tuple[str, ...]]) -> str | None:
    for value, aliases in vocabulary.items():
        if any(_has(text, alias) for alias in aliases):
            return value
    return None


def _route_number(query: str) -> str | None:
    # Unicode decimal digits include Hindi numerals; preserve operational suffixes.
    ascii_digits = "".join(str(unicodedata.digit(char)) if char.isdecimal() else char for char in query)
    ascii_digits = re.sub(r"(?<=\d)जी(?=\W|$)", "G", ascii_digits)
    ascii_digits = re.sub(r"(?<=\d)\s*-\s*(?=[A-Za-z](?![A-Za-z]))", "-", ascii_digits)
    code = r"(?:[A-Za-z]{1,3})?\d{1,4}(?:[A-Za-z]{1,3})?(?:-[A-Za-z]{1,3})?#?"
    terminal = r"(?![A-Za-z0-9#-])"
    prefix = re.search(r"(?i)(?:\bbus\b|\broute\b|बस|रूट)\s*(?:(?:no\.?|number|नंबर)\s*)?(" + code + r")" + terminal + r"(?:\s+([A-Za-z])(?![A-Za-z]))?", ascii_digits)
    suffix = re.search(r"(?i)(" + code + r")" + terminal + r"(?:\s+([A-Za-z])(?![A-Za-z]))?\s*(?:\bbus\b|\broute\b|बस|रूट)", ascii_digits)
    match = prefix or suffix
    if not match:
        return None
    value = (match.group(1) + (match.group(2) or "")).upper()
    return re.sub(r"(?<=\d)-(?=[A-Z](?:#|$))", "", value)


def _time(query: str) -> str | list[str] | None:
    text = unicodedata.normalize("NFKC", query).lower()
    explicit = re.search(r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(am|pm)(?!\w)", text)
    if explicit:
        hour, minute = int(explicit.group(1)), int(explicit.group(2) or 0)
        if 1 <= hour <= 12 and minute < 60:
            return f"{hour % 12 + (12 if explicit.group(3) == 'pm' else 0):02d}:{minute:02d}:00"
    twenty_four = re.search(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)", text)
    if twenty_four:
        hour, minute = int(twenty_four.group(1)), int(twenty_four.group(2))
        if hour < 24 and minute < 60:
            return f"{hour:02d}:{minute:02d}:00"
    colloquial = re.search(r"(?<!\d)(\d{1,2})\s*(?:baje|बजे|o['’]?clock)(?!\w)", text)
    if colloquial:
        hour = int(colloquial.group(1))
        if not 1 <= hour <= 12:
            return None
        if re.search(r"raat|रात", text):
            if hour == 12:
                return "00:00:00"
            if hour <= 4:
                return f"{hour:02d}:00:00"
            if hour <= 7:
                return [f"{hour:02d}:00:00", f"{hour + 12:02d}:00:00"]
            return f"{hour + 12:02d}:00:00"
        if re.search(r"shaam|शाम|dopahar|दोपहर", text):
            return f"{hour % 12 + 12:02d}:00:00"
        if re.search(r"subah|सुबह", text):
            return f"{hour % 12:02d}:00:00"
        return [f"{hour % 12:02d}:00:00", f"{hour % 12 + 12:02d}:00:00"]
    return None


class T3SlotExtractor:
    def __init__(self, resolver: CanonicalResolver):
        self.resolver = resolver

    def extract(self, query: str, intent: str) -> ExtractionResult:
        """Extract explicit canonical slots for one T3 intent."""
        if intent not in T3_INTENTS:
            raise ContractError(f"Unknown T3 intent: {intent}")
        normalized = normalize_text(query)
        slots: dict[str, object] = {}
        spans = self.resolver.find_spans(query)
        unresolved: list[Resolution] = []

        mode_hits = []
        for mode, pattern in MODE_PATTERNS.items():
            match = re.search(pattern, normalized)
            if match:
                mode_hits.append((match.start(), mode))
        requested_modes = tuple(mode for _, mode in sorted(mode_hits))
        mode = requested_modes[0] if len(requested_modes) == 1 else None
        if mode and intent not in {"out_of_scope"}:
            slots["transport_mode"] = mode
        if intent == "interchange_transfer" and len(requested_modes) == 2:
            slots["mode_from"], slots["mode_to"] = requested_modes

        code = _route_number(query)
        if code and intent in {"route_stop_sequence", "route_stop_membership", "first_and_last_service", "service_frequency", "scheduled_departure", "fare_calculation", "realtime_status_query", "point_to_point_route", "multimodal_route", "interchange_transfer"}:
            slots["route_number"] = code

        if intent == "first_and_last_service":
            first = any(_has(normalized, word) for word in ("first", "पहली", "पहला", "pehli", "pehla"))
            last = any(_has(normalized, word) for word in ("last", "आखिरी", "aakhiri"))
            if first != last:
                slots["timing_type"] = "first" if first else "last"

        for line in LINE_NAMES:
            if _has(normalized, line) and intent in {"point_to_point_route", "multimodal_route", "route_stop_sequence", "route_stop_membership", "first_and_last_service", "service_frequency", "scheduled_departure", "mode_availability", "interchange_transfer", "realtime_status_query"}:
                slots["line_name"] = line
                break

        if intent in {"point_to_point_route", "multimodal_route"}:
            preference = _enum(normalized, PREFERENCES)
            if preference:
                slots["preference"] = preference
        if intent == "station_facilities":
            facility = _enum(normalized, FACILITIES)
            if facility:
                slots["facility_type"] = facility
        if intent == "station_accessibility":
            feature = _enum(normalized, ACCESSIBILITY)
            if feature:
                slots["accessibility_feature"] = feature
        if intent in {"ticketing_and_passes", "fare_calculation"}:
            ticket = _enum(normalized, TICKETS)
            if ticket:
                slots["ticket_type"] = ticket
        if intent == "fare_calculation":
            stage = re.search(r"(?<!\w)(?:stage|स्टेज)\s*(\d{1,2})(?!\w)", normalized)
            if stage and 1 <= int(stage.group(1)) <= 30:
                slots["stage_number"] = int(stage.group(1))

        if intent in {"first_and_last_service", "service_frequency", "scheduled_departure", "point_to_point_route", "multimodal_route"}:
            clock = _time(query)
            if clock:
                slots["time"] = clock
        if intent in {"first_and_last_service", "service_frequency", "scheduled_departure", "point_to_point_route", "multimodal_route", "mode_availability", "realtime_status_query"}:
            date_match = re.search(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)", query)
            if date_match:
                try:
                    calendar_date.fromisoformat(date_match.group())
                    slots["date"] = date_match.group()
                except ValueError:
                    pass
            for marker in ("kal", "कल", "tomorrow", "today", "yesterday", "aaj", "आज"):
                if _has(normalized, marker):
                    slots["temporal_relative"] = marker
                    break

        def assign(span: EntitySpan, role: str) -> None:
            resolution = self.resolver.resolve(span, role, intent, mode=mode, route_number=code)
            if resolution.entity_id:
                slots[role] = resolution.entity_id
            elif resolution.ambiguous:
                unresolved.append(resolution)

        journey_intents = {"point_to_point_route", "multimodal_route", "mode_availability", "fare_calculation"}
        if intent in journey_intents:
            via_index = next((index for index in range(1, len(spans))
                              if re.search(r"(?:\bvia\b|होते हुए|hote hue)\s*$", normalized[spans[index - 1].end:spans[index].start])), None)
            if via_index is not None and intent in {"point_to_point_route", "multimodal_route"}:
                assign(spans[via_index], "via")
                endpoints = [span for index, span in enumerate(spans) if index != via_index]
            else:
                endpoints = list(spans)
            if len(endpoints) >= 2:
                before_first = normalized[:endpoints[0].start]
                between = normalized[endpoints[0].end:endpoints[-1].start]
                reverse = re.search(r"(?:to|तक|को)\s*$", before_first) and re.search(r"(?:from)\s*$", between)
                assign(endpoints[0], "destination" if reverse else "origin")
                assign(endpoints[-1], "origin" if reverse else "destination")
            elif len(endpoints) == 1:
                span = endpoints[0]
                before = normalized[:span.start]
                after = normalized[span.end:]
                role = "origin" if re.search(r"(?:from|से|se)\s*$", before) or re.match(r"\s*(?:से|se|from)(?!\w)", after) else "destination"
                assign(span, role)
        elif intent == "route_stop_membership" and spans:
            assign(spans[0], "stop")
        elif intent == "nearest_transport" and spans:
            assign(spans[0], "landmark")
        elif intent in {"station_facilities", "station_accessibility", "scheduled_departure", "first_and_last_service", "service_frequency", "ticketing_and_passes", "interchange_transfer"} and spans:
            assign(spans[0], "station")

        reason = None
        if unresolved:
            reason = "entity_ambiguity"
        elif isinstance(slots.get("time"), list) or (slots.get("temporal_relative") in {"kal", "कल"} and not slots.get("date")):
            reason = "temporal_ambiguity"
        return ExtractionResult(slots, spans, tuple(unresolved), reason, requested_modes, normalized)
