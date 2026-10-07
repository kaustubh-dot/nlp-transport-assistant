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
    "bus": r"(?<!\w)(?:bus|bs|बस)(?!\w)",
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
    "monthly_pass": ("monthly pass", 'mnthly pass', "मासिक पास"),
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
SERVICE_TYPES = {
    "Ordinary Services": ("ordinary", "साधारण"),
    "Express Services": ("express", "एक्सप्रेस"),
    "Deluxe Services": ("deluxe", 'deluxw', "डीलक्स"),
    "Night Services": ("night service", "night bus", "रात्रि बस"),
    "Air Conditioned Services": ("air conditioned", "ac bus", "एसी बस", "वातानुकूलित"),
}
FARE_TYPES = {
    "concession": ("concession", "concessional", "रियायती", "रियायत"),
    "pass_fare": ("pass fare", "पास किराया"),
    "stage_fare": ("stage fare", "स्टेज किराया"),
    "distance_fare": ("distance fare", "दूरी किराया"),
}


COORDINATION = r'(?<!\w)(?:and|also|aur|और|or|ya|या)(?!\w)'
CLOCK_TOKEN = r'(?<![\d:.])\d{1,2}(?:[:.]\d{2}(?::\d{2})?)?\s*(?:am|pm|baje|बजे|o[\x27’]?clock)(?!\w)|(?<![\d:.])\d{1,2}:\d{2}(?::\d{2})?(?![\d:])'

@dataclass(frozen=True)
class ExtractionResult:
    slots: dict[str, object]
    spans: tuple[EntitySpan, ...]
    unresolved: tuple[Resolution, ...]
    clarification_reason: str | None
    requested_modes: tuple[str, ...]
    normalized_query: str
    missing_execution_slots: tuple[str, ...] = ()
    multiple_execution_scopes: bool = False
    unsupported_temporal_scope: bool = False
    unsupported_timetable_waypoint: bool = False


def _has(text: str, phrase: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(normalize_text(phrase)) + r"(?!\w)", text) is not None


def _enum(text: str, vocabulary: dict[str, tuple[str, ...]]) -> str | None:
    for value, aliases in vocabulary.items():
        if any(_has(text, alias) for alias in (value, *aliases)):
            return value
    return None


def _uncertain_service_class(text: str) -> bool:
    hits = [value for value, aliases in SERVICE_TYPES.items()
            if any(_has(text, alias) for alias in (value, *aliases))]
    if len(hits) > 1:
        return True
    known = {normalize_text(alias) for aliases in SERVICE_TYPES.values() for alias in aliases if ' ' not in alias}
    def one_edit(a: str, b: str) -> bool:
        if len(a) == len(b):
            return sum(x != y for x, y in zip(a, b)) == 1
        short, long = sorted((a, b), key=len)
        return len(long) == len(short) + 1 and any(long[:i] + long[i+1:] == short for i in range(len(long)))
    # Similarity only stops execution; it never chooses a service class.
    unrelated_words = {'deluge', 'delude', 'empress'}
    return any(word not in known | unrelated_words
               and any(one_edit(word, root) for root in ('ordinary', 'express', 'deluxe'))
               for word in re.findall(r'(?<!\w)[a-z]{4,}(?!\w)', text))


def _endpoints(text: str, spans: list[EntitySpan]) -> tuple[EntitySpan, EntitySpan]:
    """Use explicit source prepositions/postpositions before mention order."""
    first, last = spans[0], spans[-1]
    source_before = r"(?:from|से|se)\s*$"
    source_after = r"\s*(?:से|se)(?!\w)"
    first_source = bool(re.search(source_before, text[:first.start]) or re.match(source_after, text[first.end:last.start]))
    last_source = bool(re.search(source_before, text[first.end:last.start]) or re.match(source_after, text[last.end:]))
    return (last, first) if last_source and not first_source else (first, last)


def _timetable_modifier_component(text: str) -> bool:
    """Recognize complete parameter/courtesy clauses, never name prefixes."""
    clock = r'\d{1,2}(?:\s+\d{2}){0,2}(?:\s*(?:am|pm|baje|बजे|o\s*clock))?'
    period = r'(?:subah|सुबह|shaam|शाम|dopahar|दोपहर|raat|रात)'
    day = r'(?:\d{4}\s+\d{2}\s+\d{2}|today|tomorrow|yesterday|aaj|आज|kal|कल|parso|परसों)'
    code = r'(?:[a-z]{0,3}\d{1,4}(?:[a-z]{0,3}|\s+[a-z]|\s*(?:आर|जी|बी|सी|डी|ए|ई))#?)'
    unit = r'(?:services?|departures?|bus(?:es)?|trains?|timings?|times?|सेवा|बस|ट्रेन)'
    atom = (r'(?:please|thanks|thank you|प्लीज|'
            r'(?:(?:departing|leaving|arriving)\s*)?(?:(?:at|after|before)\s*)?'
            r'(?:' + period + r'\s*)?' + clock + r'(?:\s*' + period + r')?|'
            r'(?:(?:on|for)\s+)?' + day + r'|'
            r'(?:(?:for|on)\s+)?(?:(?:bus|bs|बस)\s+)?'
            r'(?:route|रूट|bus|bs|बस)\s*(?:(?:no|number|नंबर)\s+)?' + code + r'|'
            r'(?:by|using)\s+(?:bus|metro|mrts|suburban rail)|'
            r'(?:first|पहली|पहला|pehli|pehla)(?:\s+' + unit + r')*\s+'
            r'(?:last|आखिरी|aakhiri)(?:\s+' + unit + r')*)')
    # Commit only complete atoms: numeric runs must not be repartitioned
    # exponentially on a later unknown word. The boundary stays inside the
    # atomic choice so a date can still win over its shorter clock prefix.
    component = r'(?>' + atom + r'(?=\s|$))'
    return bool(re.fullmatch(component + r'(?:\s+' + component + r')*', text))


def _unknown_timetable_coordination(query: str, spans: tuple[EntitySpan, ...]) -> bool:
    """Do not reduce a location list merely because one name is unknown."""
    text = normalize_text(query)
    marker = '__timetable_location__'
    replacements = [(span.start, span.end, f' {marker} ') for span in spans]
    # Preserve list punctuation outside names, including removed ASCII commas.
    for separator in re.finditer(r'[,，&]', query):
        position = len(normalize_text(query[:separator.start()]))
        if not any(span.start <= position < span.end for span in spans):
            replacements.append((position, position + len(normalize_text(separator.group())), ' and '))
    pieces, cursor = [], 0
    for start, end, replacement in sorted(replacements):
        pieces.extend((text[cursor:start], replacement))
        cursor = end
    pieces.append(text[cursor:])
    masked = ''.join(pieces)
    # This supported modifier is one request, including Hindi/postfix grammar.
    masked = re.sub(
        r'(?<!\w)((?:first|पहली|पहला|pehli|pehla)'
        r'(?:\s+(?:services?|departures?|bus(?:es)?|trains?|timings?|times?|सेवा|बस|ट्रेन))*)'
        r'\s+(?:and|aur|और)\s+'
        r'(last|आखिरी|aakhiri)(?!\w)', r'\1 \2', masked)
    # Count explicit roles independently of whether their names were resolved.
    roles = r'(?<!\w)(?:from|to|से|se|तक|tak)(?!\w)'
    if any(len(re.findall(r'(?<!\w)' + role + r'(?!\w)', masked)) > 1
           for role in ('from', 'to', 'से', 'se', 'तक', 'tak')):
        return True
    coordination = list(re.finditer(COORDINATION, masked))
    for index, separator in enumerate(coordination):
        previous_roles = list(re.finditer(roles, masked[:separator.start()]))
        left_start = max(previous_roles[-1].end() if previous_roles else 0,
                         coordination[index - 1].end() if index else 0)
        right_start = separator.end()
        direction = re.match(r'\s*(?:from|to)(?!\w)\s*', masked[right_start:])
        if direction:
            right_start += direction.end()
        following_role = re.search(roles, masked[right_start:])
        right_end = min(right_start + following_role.start() if following_role else len(masked),
                        coordination[index + 1].start() if index + 1 < len(coordination) else len(masked))
        left, right = masked[left_start:separator.start()].strip(), masked[right_start:right_end].strip()
        context = marker in left + right or previous_roles or (
            len(spans) >= 2 and marker in masked[:separator.start()])
        if context and any(marker not in part and re.search(r'[^\W\d_]', part)
                           and not _timetable_modifier_component(part) for part in (left, right)):
            return True
    return False


def _route_number(query: str) -> str | None:
    # Unicode decimal digits include Hindi numerals; preserve operational suffixes.
    query = re.sub(CLOCK_TOKEN, '', query, flags=re.IGNORECASE)
    query = re.sub(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)', '', query)
    ascii_digits = "".join(str(unicodedata.digit(char)) if char.isdecimal() else char
                           for char in unicodedata.normalize('NFC', query))
    suffixes = {'आर': 'R', 'जी': 'G', 'बी': 'B', 'सी': 'C', 'डी': 'D', 'ए': 'A', 'ई': 'E'}
    def word_character(char: str) -> bool:
        return unicodedata.category(char)[0] in 'LNM' or char == '_'
    def translate_suffix(match: re.Match) -> str:
        # Marks belong to the suffix; punctuation such as danda ends it.
        if match.end() < len(ascii_digits) and word_character(ascii_digits[match.end()]):
            return match.group(0)
        return suffixes[match.group(1)]
    ascii_digits = re.sub(r'(?<=\d)\s*(' + '|'.join(suffixes) + r')',
                          translate_suffix, ascii_digits)
    ascii_digits = re.sub(r"(?<=\d)\s*-\s*(?=[A-Za-z](?![A-Za-z]))", "-", ascii_digits)
    code = r"(?:[A-Za-z]{1,3})?\d{1,4}(?:[A-Za-z]{1,3})?(?:-[A-Za-z]{1,3})?#?"
    terminal = r"(?![\w#-])"
    spaced_suffix = r'(?:\s+([A-Za-z]#?)' + terminal + r')?'
    prefix = re.search(r"(?i)(?:\bbus\b|\bbs\b|\broute\b|बस|रूट)\s*(?:(?:no\.?|number|नंबर)\s*)?(" + code + r")" + terminal + spaced_suffix, ascii_digits)
    suffix = re.search(r"(?i)(" + code + r")" + terminal + spaced_suffix + r"\s*(?:\bbus\b|\bbs\b|\broute\b|बस|रूट)", ascii_digits)
    match = prefix or suffix
    if not match:
        return None
    end = match.end(2) if match.group(2) else match.end(1)
    if end < len(ascii_digits) and word_character(ascii_digits[end]):
        return None
    if prefix and not match.group(2):
        following = re.match(r'\s+(.+)', ascii_digits[match.end(1):])
        if following:
            # Consume letters/marks and route symbols, stopping at punctuation.
            token = []
            for char in following.group(1):
                if not word_character(char) and char not in '#-':
                    break
                token.append(char)
            word = ''.join(token).rstrip('#-_')
            hindi_segment = re.split(r'[#_-]', word, maxsplit=1)[0]
            unsupported_names = {'एफ', 'एच', 'जे', 'एल', 'एम', 'एन', 'ओ', 'पी', 'क्यू',
                                 'एस', 'टी', 'यू', 'वी', 'डब्ल्यू', 'एक्स', 'वाई', 'ज़ेड', 'जेड'}
            letter_names = set(suffixes) | unsupported_names | {'के'}
            plausible_suffix = hindi_segment != 'के' and re.fullmatch(
                '(?:' + '|'.join(sorted(letter_names, key=len, reverse=True)) + r')+[\u093a-\u094f\u0951-\u0957]*', hindi_segment)
            if (plausible_suffix
                    or re.match(r'[A-Za-z][\d\u0900-\u097f#-]', word)):
                return None
    value = (match.group(1) + (match.group(2) or "")).upper()
    return re.sub(r"(?<=\d)-(?=[A-Z](?:#|$))", "", value)


def _time(query: str) -> str | list[str] | None:
    text = unicodedata.normalize("NFKC", query).lower()
    explicit = re.search(r"(?<![\d:.])(\d{1,2})(?:[:.](\d{2})(?::(\d{2}))?)?\s*(am|pm)(?!\w)", text)
    if explicit:
        hour, minute = int(explicit.group(1)), int(explicit.group(2) or 0)
        second = int(explicit.group(3) or 0)
        if 1 <= hour <= 12 and minute < 60 and second < 60:
            return f"{hour % 12 + (12 if explicit.group(4) == 'pm' else 0):02d}:{minute:02d}:{second:02d}"
        return None
    colloquial = re.search(r"(?<![\d:.])(\d{1,2})(?:[:.](\d{2})(?::(\d{2}))?)?\s*(?:baje|बजे|o['’]?clock)(?!\w)", text)
    if colloquial:
        hour = int(colloquial.group(1))
        minute = int(colloquial.group(2) or 0)
        second = int(colloquial.group(3) or 0)
        if minute >= 60 or second >= 60 or not 1 <= hour <= 23:
            return None
        def stamp(value: int) -> str:
            return f"{value:02d}:{minute:02d}:{second:02d}"
        if hour > 12:
            return stamp(hour)
        if re.search(r"raat|रात", text):
            if hour == 12:
                return stamp(0)
            if hour <= 4:
                return stamp(hour)
            if hour <= 7:
                return [stamp(hour), stamp(hour + 12)]
            return stamp(hour + 12)
        if re.search(r"shaam|शाम|dopahar|दोपहर", text):
            return stamp(hour % 12 + 12)
        if re.search(r"subah|सुबह", text):
            return stamp(hour % 12)
        return [stamp(hour % 12), stamp(hour % 12 + 12)]
    twenty_four = re.search(r"(?<![\d:.])(\d{1,2}):(\d{2})(?::(\d{2}))?(?![\d:])", text)
    if twenty_four:
        hour, minute = int(twenty_four.group(1)), int(twenty_four.group(2))
        second = int(twenty_four.group(3) or 0)
        if hour < 24 and minute < 60 and second < 60:
            return f"{hour:02d}:{minute:02d}:{second:02d}"
    return None





def _multiple_scopes(text: str, intent: str, spans: tuple[EntitySpan, ...]) -> bool:
    """Reject cardinality that a single-operation slot schema cannot represent."""
    # Keep punctuation for clocks, ISO dates and complete route suffixes.
    text = unicodedata.normalize('NFC', text).lower()
    clauses = re.split(COORDINATION, text)
    lines = {line for line in LINE_NAMES if _has(normalize_text(text), line)}
    if len(lines) > 1 or (lines and _route_number(text)):
        return True
    if len(clauses) > 1:
        route_codes = {_route_number(clause) for clause in clauses}
        route_codes.discard(None)
        # A coordinated bare code inherits the first clause's explicit route cue.
        if route_codes:
            for clause in clauses[1:]:
                bare = re.fullmatch(r'\s*([a-z]{0,3}\d{1,4}(?:[a-z]{0,3}|आर|जी|बी|सी|डी|ए|ई)?)\s*[?.!]?\s*', clause)
                if bare:
                    route_codes.add(_route_number('bus ' + bare.group(1)))
        if len(route_codes - {None}) > 1:
            return True
        if sum(_explicit_route_marker(clause) for clause in clauses) > 1 and any(
                _explicit_route_marker(clause) and _route_number(clause) is None for clause in clauses):
            return True
    if intent == 'fare_calculation':
        stages = {int(m.group(1)) for m in re.finditer(r'(?<!\w)(?:stage|स्टेज)\s*(\d{1,2})(?!\w)', text)}
        for match in re.finditer(r'(?:stage|स्टेज)\s*\d{1,2}\s*' + COORDINATION + r'\s*(\d{1,2})(?!\w)', text):
            stages.add(int(match.group(1)))
        if len(stages) > 1:
            return True
    if intent in {'route_stop_membership', 'nearest_transport'}:
        identities = {tuple(sorted(c.entity_id for c in span.candidates)) for span in spans}
        if len(identities) > 1:
            return True
    temporal_intents = {'first_and_last_service', 'service_frequency', 'scheduled_departure',
                        'point_to_point_route', 'multimodal_route', 'mode_availability'}
    if intent in temporal_intents:
        clocks = {match.group().strip() for match in re.finditer(CLOCK_TOKEN, text)}
        inherited_clock = re.search(r'\d{1,2}\s*' + COORDINATION + r'\s*\d{1,2}\s*(?:am|pm|baje|बजे)(?!\w)', text)
        dates = set(re.findall(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)', text))
        relative_days = {value for value, words in {
            'today': ('today', 'aaj', 'आज'), 'tomorrow': ('tomorrow',),
            'yesterday': ('yesterday',), 'kal': ('kal', 'कल'), 'parso': ('parso', 'परसों')}.items()
            if any(_has(normalize_text(text), word) for word in words)}
        if len(clocks) > 1 or inherited_clock or len(dates) + len(relative_days) > 1:
            return True
    return False


def _explicit_route_marker(text: str) -> bool:
    """Detect an explicit numeric route even when its suffix is unsupported."""
    text = re.sub(CLOCK_TOKEN, '', text)
    text = re.sub(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)', '', text)
    marker = r'(?:\bbus\b|\bbs\b|\broute\b|बस|रूट)'
    return bool(re.search(marker + r'\s*(?:(?:route|रूट|no\.?|number|नंबर)\s*)?(?:[a-z]{1,3})?\d', text)
                or re.search(r'(?<!\w)(?:[a-z]{1,3})?\d[^\s?.,!:;()]*(?:\s+[^\s?.,!:;()]+)?\s*' + marker, text))


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
        invalid_temporal = False
        missing_execution = ()
        multiple_locations = False

        mode_hits = []
        for mode, pattern in MODE_PATTERNS.items():
            # In nearest queries, mode words in the anchor name describe its
            # location, not the requested target mode. Other intents retain
            # mode-qualified station resolution (e.g. Guindy metro).
            match = next((m for m in re.finditer(pattern, normalized)
                          if intent != 'nearest_transport'
                          or not any(span.start <= m.start() < span.end for span in spans)), None)
            if match:
                mode_hits.append((match.start(), mode))
        requested_modes = tuple(mode for _, mode in sorted(mode_hits))
        mode = requested_modes[0] if len(requested_modes) == 1 else None
        if mode and intent not in {"out_of_scope"}:
            slots["transport_mode"] = mode
        if intent == "interchange_transfer" and len(requested_modes) == 2:
            slots["mode_from"], slots["mode_to"] = requested_modes

        code = _route_number(query)
        if code and intent in {"route_stop_sequence", "route_stop_membership", "first_and_last_service", "service_frequency", "scheduled_departure", "fare_calculation", "realtime_status_query", "point_to_point_route", "multimodal_route", "mode_availability", "interchange_transfer"}:
            slots["route_number"] = code
        elif not code and intent in {'point_to_point_route', 'mode_availability', 'multimodal_route',
                                    'scheduled_departure', 'first_and_last_service', 'service_frequency',
                                    'route_stop_sequence', 'route_stop_membership', 'fare_calculation',
                                    'interchange_transfer'} and _explicit_route_marker(query.lower()):
            missing_execution = ('route_number',)

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
            for name, vocabulary in (("service_type", SERVICE_TYPES), ("fare_type", FARE_TYPES)):
                value = _enum(normalized, vocabulary)
                if value:
                    slots[name] = value
            stage = re.search(r"(?<!\w)(?:stage|स्टेज)\s*(\d{1,2})(?!\w)", normalized)
            if stage and 1 <= int(stage.group(1)) <= 30:
                slots["stage_number"] = int(stage.group(1))
            if _uncertain_service_class(normalized):
                slots.pop('service_type', None)
                missing_execution += ('service_type',)

        if intent in {"first_and_last_service", "service_frequency", "scheduled_departure", "point_to_point_route", "multimodal_route", "mode_availability"}:
            clock = _time(query)
            if clock:
                slots["time"] = clock
            elif re.search(r"\d{1,2}[:.]\d{2}|\d{1,2}\s*(?:am|pm|baje|बजे)", query, re.IGNORECASE):
                invalid_temporal = True
        if intent in {"first_and_last_service", "service_frequency", "scheduled_departure", "point_to_point_route", "multimodal_route", "mode_availability", "realtime_status_query"}:
            date_match = re.search(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)", query)
            if date_match:
                try:
                    calendar_date.fromisoformat(date_match.group())
                    slots["date"] = date_match.group()
                except ValueError:
                    invalid_temporal = True
            for marker in ("kal", "कल", "parso", "परसों", "tomorrow", "today", "yesterday", "aaj", "आज"):
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
        unsupported_timetable_waypoint = False
        if intent in journey_intents:
            via_marker = re.search(r'(?<!\w)(?:via|होते हुए|hote hue)(?!\w)', normalized)
            via_index = next((index for index, span in enumerate(spans)
                              if via_marker and re.fullmatch(r'\s*', normalized[via_marker.end():span.start])
                              and span.start >= via_marker.end()), None)
            if via_index is not None and intent in {"point_to_point_route", "multimodal_route", "mode_availability"}:
                assign(spans[via_index], "via")
                endpoints = [span for index, span in enumerate(spans) if index != via_index]
            else:
                endpoints = list(spans)
                if via_marker and intent != 'fare_calculation':
                    missing_execution += ('via',)
                    # A later known name cannot substitute for an unknown waypoint.
                    endpoints = [span for span in endpoints if span.end <= via_marker.start()]
            multiple_locations = len(endpoints) > 2
            if len(endpoints) >= 2:
                origin, destination = _endpoints(normalized, endpoints)
                assign(origin, "origin")
                assign(destination, "destination")
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
        elif intent in {"scheduled_departure", "first_and_last_service", "service_frequency"}:
            unsupported_timetable_waypoint = bool(re.search(
                r'(?<!\w)(?:via|होते हुए|hote hue)(?!\w)', normalized))
            if unsupported_timetable_waypoint:
                # Timetable contracts cannot execute a waypoint filter. Retain
                # explicit endpoint roles only; mention order must not turn a
                # waypoint into a destination. All mentions remain in spans.
                sources = [span for span in spans if
                           re.search(r'(?<!\w)from\s*$', normalized[:span.start])
                           or re.match(r'\s*(?:से|se)(?!\w)', normalized[span.end:])]
                destinations = [span for span in spans if
                                re.search(r'(?<!\w)to\s*$', normalized[:span.start])
                                or re.match(r'\s*(?:तक|tak)(?!\w)', normalized[span.end:])]
                multiple_locations = len(sources) > 1 or len(destinations) > 1
                if len(sources) == 1:
                    assign(sources[0], 'station')
                if len(destinations) == 1:
                    assign(destinations[0], 'destination')
            else:
                multiple_locations = len(spans) > 2 or _unknown_timetable_coordination(query, spans)
                if len(spans) >= 2:
                    origin, destination = _endpoints(normalized, list(spans))
                    assign(origin, "station")
                    assign(destination, "destination")
                elif spans:
                    assign(spans[0], 'station')
        elif intent in {"station_facilities", "station_accessibility", "ticketing_and_passes", "interchange_transfer"} and spans:
            assign(spans[0], "station")

        reason = None
        if unresolved:
            reason = "entity_ambiguity"
        elif invalid_temporal or isinstance(slots.get("time"), list) or (slots.get("temporal_relative") in {"kal", "कल", "parso", "परसों"} and not slots.get("date")):
            reason = "temporal_ambiguity"
        unsupported_temporal = intent in {'scheduled_departure', 'service_frequency', 'first_and_last_service',
                                           'point_to_point_route', 'multimodal_route', 'mode_availability'} and bool(
            slots.get('time') or invalid_temporal) and bool(re.search(
                r'(?<!\w)(?:before|between|pehle|pahle|पहले|बीच)(?!\w)', normalized))
        return ExtractionResult(slots, spans, tuple(unresolved), reason, requested_modes, normalized,
                                missing_execution, multiple_locations or _multiple_scopes(query, intent, spans),
                                unsupported_temporal, unsupported_timetable_waypoint)
