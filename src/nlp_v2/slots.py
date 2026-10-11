"""Explicit multilingual T3 slot extraction with separate uncertainty metadata."""

from dataclasses import dataclass, field
from datetime import date as calendar_date
from functools import lru_cache
import re
import unicodedata

from .text import normalize_extraction_text as normalize_text
from src.nlp_v2.contracts import ContractError, T3_INTENTS
from src.nlp_v2.entities import CanonicalResolver, EntitySpan, Resolution


MODE_PATTERNS = {
    "metro": r"(?<!\w)(?:metro|मेट्रो)(?!\w)",
    "bus": r"(?<!\w)(?:buses|bus|bs|बसें|बसों|बस)(?!\w)",
    "suburban_rail": r"(?<!\w)(?:suburban(?:\s+rail)?|local(?:\s+train)?|rail(?:\s+train)?|train|रेल|ट्रेन|लोकल(?:\s+(?:ट्रेन|रेल))?|उपनगरीय(?:\s+(?:रेल|ट्रेन))?)(?!\w)",
    "mrts": r"(?<!\w)(?:mrts|एमआरटीएस)(?!\w)",
}
FACILITIES = {
    "parking": ("parking", "पार्किंग", "gaadi khadi", "गाड़ी खड़ी"),
    "restroom": ("restroom", "toilet", "शौचालय", "shauchalay"),
    "waiting_room": ("waiting room", "प्रतीक्षालय"),
    "cloak_room": ("cloak room", "क्लोक रूम"),
    "atm": ("atm", "एटीएम"),
    "wifi": ("wifi", "wi fi", "वाईफाई"),
    "drinking_water": ("drinking water", "पीने का पानी", "peene ka paani"),
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
    "fastest": ("fastest", "सबसे तेज", "sabse tez"),
    "cheapest": ("cheapest", "सबसे सस्ता", "sabse sasta"),
    "least_transfers": ("least transfers", "fewest changes", "कम से कम बदलाव", "kam se kam badlav"),
    "direct_only": ("direct only", "सीधा", "सीधी", "seedha", "seedhi"),
}
LINE_NAMES = ("Blue Line", "Green Line", "Corridor 1", "Corridor 2", "MRTS", "North Line", "South Line", "West Line")
SERVICE_TYPES = {
    "Ordinary Services": ("ordinary", "साधारण"),
    "Express Services": ("express", "एक्सप्रेस"),
    "Deluxe Services": ("deluxe", 'deluxw', "डीलक्स"),
    "Night Services": ("night service", "night bus", "रात्रि बस", "रात्रि सेवा", "raat ki bus"),
    "Air Conditioned Services": ("air conditioned", "ac bus", "एसी बस", "वातानुकूलित", "vatanukoolit"),
}
FARE_TYPES = {
    "concession": ("concession", "concessional", "रियायती", "रियायत"),
    "pass_fare": ("pass fare", "पास किराया"),
    "stage_fare": ("stage fare", "स्टेज किराया"),
    "distance_fare": ("distance fare", "दूरी किराया"),
}


COORDINATION = r'(?<!\w)(?:and|also|aur|और|or|ya|या)(?!\w)'
CLOCK_TOKEN = r'(?<![\d:.])\d{1,2}(?:[:.]\d{2}(?::\d{2})?)?\s*(?:am|pm|baje|बजे|o[\x27’]?clock)(?!\w)|(?<![\d:.])\d{1,2}:\d{2}(?::\d{2})?(?![\d:])'
_SERVICE_MODIFIER = '(?:' + '|'.join(re.escape(alias) for alias in sorted(
    {normalize_text(alias) for aliases in SERVICE_TYPES.values() for alias in aliases}, key=len, reverse=True)) + ')'
_STAGE_LINK = r'\s*-?\s*(?:' + _SERVICE_MODIFIER + r'\s+)?(?:(?:bus(?:es)?|बस)\s+)?'
ROUTE_QUANTITY = (r'(?<!\w)\d+(?:[.,]\d+)?(?:' + _STAGE_LINK + r'(?:stages?|स्टेज|चरण)'
                  r'|\s*-?\s*(?:passengers?|people|persons?|tickets?|mins?|minutes?|km|kg|hours?|hrs?|rs|inr|यात्री|यात्रियों))(?!\w)')
_AVAILABILITY_PREDICATE = r'run|runs|running|operate|operates|operating|available|chalti|chalta|चलती|चलता|चलते'
from .semantics import (GOAL_CUES, _MEMBERSHIP_PREDICATE, _NATIVE_AVOIDANCE,
                        _native_avoidance_has_operand, _new_request_after_negative_predicate,
                        _word_character, _word_matches, positive_goal_attribute_text)
_LOCATION_POSTPOSITION = r'पर|में|से|तक|par|mein|se|tak'
# Words that begin ordinary request grammar after a complete numeric route.
# This is a lexical boundary contract, not a normalization/alias rule. Other
# Latin letter groups may be suffix operands of any length and cannot be
# discarded merely because they exceed the generic identifier's old limit.
_ROUTE_PROSE_WORDS = frozenset('''
    a i an as and not the for all its bus buses via to at on in by is are no
    ki ka ke se ko na mat am pm min km hr hrs rs or vs do aur ya nor but pls
    please kindly thanks thank show list tell give display quote calculate
    need want would can could will may should must we you they he she it
    from with without except excluding avoid skip omit instead however between
    also plus through along together compared versus well then next afterwards
    followed than available availability run runs running operate operates operating
    does did was were have has had don doesn didn isn aren wasn weren shouldn
    wouldn couldn mustn won cannot can
    stop stops sequence sequences route routes first last departure departures
    time times timing timings schedule schedules timetable frequency headway
    fare fares price prices cost costs ordinary express deluxe service services
    today tomorrow yesterday morning afternoon evening night after before
    nahi nahin nhi chahiye batao bataiye dikhao lekin subah shaam dopahar raat baje
'''.split()) | frozenset((_AVAILABILITY_PREDICATE + '|' + _MEMBERSHIP_PREDICATE + '|' + _LOCATION_POSTPOSITION + '|' + _NATIVE_AVOIDANCE).split('|')) | {'chhod', 'chod'}

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
    excluded_modes: tuple[str, ...] = ()
    request_constraints: dict[str, object] = field(default_factory=dict)


def _has(text: str, phrase: str) -> bool:
    return next(_word_matches(re.escape(normalize_text(phrase)), text), None) is not None


def _word_split(pattern: str, text: str, *, punctuation: str | None = None) -> list[str]:
    separators = [*_word_matches(pattern, text)]
    if punctuation:
        separators.extend(re.finditer(punctuation, text))
    pieces, cursor = [], 0
    for match in sorted(separators, key=lambda m: m.start()):
        if match.start() < cursor:
            continue
        pieces.append(text[cursor:match.start()])
        cursor = match.end()
    pieces.append(text[cursor:])
    return pieces


# Explicit tariff counts only. These words never choose an intent or alter the
# raw classifier input. Compound counts are consumed whole, not truncated.
_COUNT_WORDS = [
    ('one', 'एक', 'ek'), ('two', 'दो', 'do'), ('three', 'तीन', 'teen'),
    ('four', 'चार', 'chaar', 'char'), ('five', 'पाँच', 'पांच', 'paanch', 'panch'),
    ('six', 'छह', 'छः', 'chhe', 'chhah', 'cheh'), ('seven', 'सात', 'saat'),
    ('eight', 'आठ', 'aath'), ('nine', 'नौ', 'nau'), ('ten', 'दस', 'das'),
    ('eleven', 'ग्यारह', 'gyarah'), ('twelve', 'बारह', 'barah'),
    ('thirteen', 'तेरह', 'terah'), ('fourteen', 'चौदह', 'chaudah'),
    ('fifteen', 'पंद्रह', 'पन्द्रह', 'pandrah'), ('sixteen', 'सोलह', 'solah'),
    ('seventeen', 'सत्रह', 'satrah'), ('eighteen', 'अठारह', 'atharah'),
    ('nineteen', 'उन्नीस', 'unnis', 'unnees'), ('twenty', 'बीस', 'bees'),
    ('twenty one', 'इक्कीस', 'ikkis', 'ikkees'), ('twenty two', 'बाईस', 'baais', 'bais'),
    ('twenty three', 'तेईस', 'teis'), ('twenty four', 'चौबीस', 'chaubis', 'chaubees'),
    ('twenty five', 'पच्चीस', 'pachis', 'pachchis'), ('twenty six', 'छब्बीस', 'chabbis'),
    ('twenty seven', 'सत्ताईस', 'sattais'), ('twenty eight', 'अट्ठाईस', 'atthais'),
    ('twenty nine', 'उनतीस', 'untees'), ('thirty', 'तीस', 'tees'),
]
_COUNT_VALUES = {normalize_text(word): number for number, words in enumerate(_COUNT_WORDS, 1) for word in words}
for _number, _words in enumerate(_COUNT_WORDS, 1):
    for _word in _words:
        if any('\u0900' <= char <= '\u097f' for char in _word):
            for _ending in ('वाँ', 'वां', 'वें', 'वीं', 'वे'):
                _COUNT_VALUES[normalize_text(_word + _ending)] = _number
for _number, _root in enumerate(('पहल', 'दूसर', 'तीसर', 'चौथ', 'पाँचव', 'छठ', 'सातव', 'आठव', 'नौव', 'दसव'), 1):
    for _ending in ('ा', 'े', 'ी', 'ाँ', 'ां', 'ें', 'ीं'):
        _COUNT_VALUES[normalize_text(_root + _ending)] = _number
_COUNT_PATTERN = r'(?:\d+|' + '|'.join(re.escape(word) for word in sorted(_COUNT_VALUES, key=len, reverse=True)) + r')'
_COUNT_TOKENS = {token for word in _COUNT_VALUES for token in word.split()}
_STAGE_UNIT = r'(?:stages?|स्टेज|चरण)'


def _stage_counts(query: str) -> tuple[set[int], bool, bool]:
    # A new sentence/imperative cannot become the operand of a preceding
    # stage unit after punctuation folding (English "do" is also Hindi two).
    clauses, cursor = [], 0
    for separator in re.finditer(r'[;；!?।॥,，]|(?<!\d)\.(?!\d)', query):
        if (separator.group() in {',', '，'} and re.search(r'\d\s*$', query[:separator.start()])
                and re.match(r'\s*\d', query[separator.end():])):
            continue
        clauses.append(query[cursor:separator.start()])
        cursor = separator.end()
    clauses.append(query[cursor:])
    results = [_stage_counts_clause(clause) for clause in clauses]
    return set().union(*(values for values, _, _ in results)), any(invalid for _, invalid, _ in results), any(mentioned for _, _, mentioned in results)


def _stage_counts_clause(query: str) -> tuple[set[int], bool, bool]:
    text = normalize_text(query)
    mentioned = next(_word_matches(_STAGE_UNIT, text), None) is not None
    values: set[int] = set()
    # Check complete numeric expressions before extraction punctuation folding.
    # Otherwise 3.5 stages becomes "3 5 stages" and silently selects tariff 5.
    raw = _ascii_digits(query).lower()
    numeric = r'(?:[+\-−]\s*)?\d+(?:\s*[.,/\-–]\s*\d+)*(?:e[+\-]?\d+)?'
    numeric_patterns = (
        _STAGE_UNIT + r'\s*(?:(?:number|count|नंबर|संख्या)\s*)?(?P<count>' + numeric + ')',
        r'(?P<count>' + numeric + r')' + _STAGE_LINK + _STAGE_UNIT,
    )
    invalid = any(not re.fullmatch(r'\d+', match.group('count').strip())
                  for pattern in numeric_patterns for match in _word_matches(pattern, raw))
    signed_count = r'[+\-−]\s*' + _COUNT_PATTERN
    invalid |= next(_word_matches(signed_count + _STAGE_LINK + _STAGE_UNIT
                                  + r'|' + _STAGE_UNIT + r'\s*' + signed_count, raw), None) is not None
    modifiers = r'(?:minus|negative|माइनस|ऋणात्मक|half|quarter|aadhe|adhe|saadhe|sadhe|sawa|sava|paune|dhai|आधे|आधा|साढ़े|सवा|पौने|ढाई|डेढ़)'
    invalid |= next(_word_matches(modifiers + r'\s+' + _COUNT_PATTERN + _STAGE_LINK + _STAGE_UNIT
                                  + r'|' + _STAGE_UNIT + r'\s+' + modifiers + r'\s+' + _COUNT_PATTERN, text), None) is not None
    coordinated = _COUNT_PATTERN + r'(?:\s+' + COORDINATION + r'\s*' + _COUNT_PATTERN + r')*'
    patterns = (_STAGE_UNIT + r'\s*(?:(?:number|count|नंबर|संख्या)\s*)?(?P<count>' + coordinated + ')',
                r'(?P<count>' + coordinated + r')' + _STAGE_LINK + _STAGE_UNIT)
    unsupported_number_words = {
        'hundred', 'thousand', 'million', 'lakh', 'crore', 'point', 'decimal',
        'सौ', 'हजार', 'हज़ार', 'लाख', 'करोड़', 'दशमलव', 'sau', 'hazar',
        'hazaar', 'dasamlav', 'dashamlav',
        'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety',
    }
    for pattern in patterns:
        for match in _word_matches(pattern, text):
            before, after = text[:match.start()].strip(), text[match.end():].strip()
            count_start, count_end = match.span('count')
            neighboring_words = text[:count_start].split()[-3:] + text[count_end:].split()[:3]
            if any(word in unsupported_number_words for word in neighboring_words):
                invalid = True
                continue
            prior_number_word = text[:count_start].split()[-1:]
            next_number_word = text[count_end:].split()[:1]
            if (prior_number_word and prior_number_word[0] in _COUNT_TOKENS
                    or next_number_word and next_number_word[0] in _COUNT_TOKENS):
                invalid = True
                continue
            negated = (bool(re.search(r'(?<!\w)(?:not|no|nahi|नहीं)\s*$', before))
                       or bool(re.match(r'(?:nahi|nahin|nhi|नहीं|नही)(?!\w)', after)))
            invalid |= negated
            for count in _word_split(COORDINATION, match.group('count')):
                count = count.strip()
                if count == 'do' and after.startswith('calculation'):
                    continue
                value = int(count) if count.isdecimal() else _COUNT_VALUES.get(count)
                if value is not None:
                    values.add(value)
                    invalid |= not 1 <= value <= 30
    return values, invalid, mentioned


def _enum(text: str, vocabulary: dict[str, tuple[str, ...]]) -> str | None:
    for value, aliases in vocabulary.items():
        if any(_has(text, alias) for alias in (value, *aliases)):
            return value
    return None


def _uncertain_service_class(text: str) -> bool:
    if any(_has(text, phrase) for phrase in ('service class unknown', 'unknown service class',
                                            'सेवा का प्रकार नहीं मालूम', 'सेवा वर्ग नहीं मालूम')):
        return True
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
    first_source = bool(next(_word_matches(source_before, text[:first.start]), None) or re.match(source_after, text[first.end:last.start]))
    last_source = bool(next(_word_matches(source_before, text[first.end:last.start]), None) or re.match(source_after, text[last.end:]))
    return (last, first) if last_source and not first_source else (first, last)


def _timetable_reporting_modifier(text: str) -> bool:
    """A requested time attribute without a new operation or operand."""
    return bool(re.fullmatch(r'(?:(?:the|their|its)\s+)?(?:(?:published|scheduled)\s+)?'
                             r'(?:(?:departure|service|bus|train)\s+)?(?:times?|timings?)'
                             r'(?:\s+(?:please|thanks))?', text))


def _timetable_modifier_component(text: str) -> bool:
    """Recognize complete parameter/courtesy clauses, never name prefixes."""
    if _timetable_reporting_modifier(text):
        return True
    # A fronted boarding location may be followed by a comma and the same
    # timetable request. Only a complete operand-free request phrase qualifies;
    # an additional unknown name or endpoint role still triggers the guard.
    timetable_unit = r'(?:services?|departures?|bus(?:es)?|trains?|timings?|times?|सेवा|बस|ट्रेन|समय|samay)'
    pair = (r'(?:first|पहली|पहला|pehli|pehla)(?:\s+' + timetable_unit + r')*\s+'
            r'(?:last|आखिरी|aakhiri)(?:\s+' + timetable_unit + r')*'
            r'(?:\s+(?:ka|ki|ke|का|की|के)\s+' + timetable_unit + r'(?:\s+' + timetable_unit + r')*)?')
    courtesy = r'(?:please|kindly|कृपया)'
    prefix_request = r'(?:give|show|tell|list)(?:\s+(?:me|us))?(?:\s+the)?\s+'
    postfix_request = r'(?:बताओ|बताइए|बताइये|दिखाओ|दिखाइए|चाहिए|batao|bataiye|dikhao|dikhaiye|chahiye)'
    request = (r'(?:' + courtesy + r'\s+)?(?:' + prefix_request + pair + r'|'
               + pair + r'\s+' + postfix_request + r')(?:\s+(?:please|thanks))?')
    if re.fullmatch(request, text):
        return True
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
    marker = '__timetable_location_'
    identities = {}
    replacements = []
    for span in spans:
        identity = tuple(sorted(candidate.entity_id for candidate in span.candidates))
        index = identities.setdefault(identity, len(identities))
        replacements.append((span.start, span.end, f' {marker}{index}__ '))
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
    roles = r'(?<!\w)(?:from|at|to|से|se|पर|par|तक|tak)(?!\w)'
    operand = re.escape(marker) + r'\d+__'
    def temporal_at(mention: re.Match) -> bool:
        if mention.group() != 'at' or re.match(r'\s*' + operand, masked[mention.end():]):
            return False
        tail = masked[mention.end():]
        boundary = next(_word_matches(COORDINATION + r'|from|to|से|se|तक|tak', tail), None)
        fragment = tail[:boundary.start()] if boundary else tail
        fragment = re.sub(r'\s+(?:bus(?:es)?|trains?|services?)\s*$', '', fragment).strip()
        return (_timetable_modifier_component('at ' + fragment)
                or _timetable_modifier_component(fragment))
    role_mentions = tuple(m for m in _word_matches(roles, masked) if not temporal_at(m))
    # Endpoint aliases share a semantic role. Distinct boarding operands
    # cannot become a source/destination pair merely because one uses "at"
    # or a Hindi postposition and the other uses "from".
    for group in (r'from|at|से|se|पर|par', r'to|तक|tak'):
        mentions = tuple(m for m in role_mentions if re.fullmatch(group, m.group()))
        values = []
        for mention in mentions:
            value = (re.match(r'\s*(' + operand + ')', masked[mention.end():])
                     if mention.group() in {'from', 'at', 'to'} else
                     re.search('(' + operand + r')\s*$', masked[:mention.start()]))
            values.append(value.group(1) if value else None)
        if len(values) > 1 and (None in values or len(set(values)) > 1):
            return True
    coordination = list(_word_matches(COORDINATION, masked))
    for index, separator in enumerate(coordination):
        previous_roles = [m for m in role_mentions if m.end() <= separator.start()]
        left_start = max(previous_roles[-1].end() if previous_roles else 0,
                         coordination[index - 1].end() if index else 0)
        right_start = separator.end()
        direction = re.match(r'\s*(?:from|to)(?!\w)\s*', masked[right_start:])
        if direction:
            right_start += direction.end()
        following_role = next((m for m in role_mentions if m.start() >= right_start), None)
        right_end = min(following_role.start() if following_role else len(masked),
                        coordination[index + 1].start() if index + 1 < len(coordination) else len(masked))
        left, right = masked[left_start:separator.start()].strip(), masked[right_start:right_end].strip()
        context = marker in left + right or previous_roles or (
            len(spans) >= 2 and marker in masked[:separator.start()])
        if context and any(marker not in part and re.search(r'[^\W\d_]', part)
                           and not _timetable_modifier_component(part) for part in (left, right)):
            return True
    return False


def _timetable_unique_spans(text: str, spans: tuple[EntitySpan, ...]) -> tuple[EntitySpan, ...]:
    """Collapse repeated identical operands only when their endpoint role agrees."""
    selected, seen = [], set()
    for span in spans:
        before, after = text[:span.start], text[span.end:]
        role = ('source' if next(_word_matches(r'(?:from|at)\s*$', before), None)
                or re.match(r'\s*(?:से|se|पर|par)(?!\w)', after) else
                'destination' if next(_word_matches(r'to\s*$', before), None)
                or re.match(r'\s*(?:तक|tak)(?!\w)', after) else None)
        key = role, tuple(sorted(candidate.entity_id for candidate in span.candidates))
        if key not in seen:
            selected.append(span)
            seen.add(key)
    return tuple(selected)


def _negative_transport_proposition(text: str, intent: str | None, start: int, end: int) -> bool:
    """A negative run/stop question asks about its operand rather than avoiding it."""
    if intent not in {'mode_availability', 'route_stop_membership'}:
        return False
    if intent == 'mode_availability':
        # The question predicate follows the complete noun phrase, including
        # descriptive words owned by Metro/MRTS and their generic train head.
        for head in _word_matches(r'train|rail|ट्रेन|रेल', text):
            if head.start() < end:
                continue
            owner = _specific_train_owner(text, head)
            if owner and owner.span() == (start, end):
                end = head.end()
            break
    boundaries = tuple(re.finditer(r'[;；.!?।॥]', text))
    left = max((m.end() for m in boundaries if m.end() <= start), default=0)
    right = min((m.start() for m in boundaries if m.start() >= end), default=len(text))
    before, after = normalize_text(text[left:start]), normalize_text(text[end:right])
    if not next(_word_matches(r'does|do|is|are|can|will|kya|क्या|whether|doesn\s*t|don\s*t|isn\s*t|aren\s*t', before + ' ' + after), None):
        return False
    predicate = _AVAILABILITY_PREDICATE if intent == 'mode_availability' else _MEMBERSHIP_PREDICATE
    operand = r'(?:(?:train|rail|ट्रेन|रेल)\s+)?(?:(?:[a-z]{0,3})?\d{1,4}[a-z]{0,6}\s+)?'
    negative = r'(?:not|nahi|nahin|nhi|नहीं|नही|doesn\s*t|don\s*t|isn\s*t|aren\s*t)'
    return bool(next(_word_matches(operand + negative + r'\s+(?:' + predicate + ')', after), None)
                and re.match(operand + negative + r'\s+(?:' + predicate + r')(?!\w)', after)
                or next(_word_matches(negative + r'\s*$', before), None)
                and re.match(operand + r'(?:' + predicate + r')(?!\w)', after))


@lru_cache(maxsize=8)
def _published_route_pattern(known_routes: tuple[str, ...]) -> str:
    # Expand complete canonical identifiers, including their multiword letter
    # groups. The data determines valid codes; no query-specific aliases exist.
    patterns = []
    for code in known_routes:
        if re.fullmatch(r'[A-Z]{0,3}\d{1,4}[A-Z]{2,}', code):
            patterns.append(''.join((r'\s*' if index and char.isalpha() else '') + re.escape(char)
                                    for index, char in enumerate(code)))
    return '|'.join(sorted(patterns, key=len, reverse=True))


def _published_code_ranges(text: str, known_routes: tuple[str, ...]) -> tuple[tuple[int, int], ...]:
    pattern = _published_route_pattern(known_routes)
    if not pattern:
        return ()
    digits = ''.join(str(unicodedata.digit(char)) if char.isdecimal() else char for char in text)
    return tuple(match.span() for match in _word_matches(pattern, digits, re.IGNORECASE))


def _route_scope(query: str, intent: str | None = None, known_routes: tuple[str, ...] = (), known_entities: tuple[str, ...] = ()) -> tuple[set[str], set[str], bool]:
    """Collect explicit route identifiers and their polarity before selection.

    An exclusion is a constraint, never an alternate route candidate. The
    single-route contract cannot represent competing or contradictory codes.
    """
    # Canonical location phrases are independent operands, including when
    # mentioned directly after a route without a preposition. Their names
    # cannot become unknown letter suffixes. Preserve punctuation elsewhere.
    query = unicodedata.normalize('NFC', query)
    complete_codes = _published_code_ranges(query, known_routes)
    for surface in sorted(set(known_entities), key=len, reverse=True):
        pattern = r'[\W_]+'.join(re.escape(word) for word in surface.split())
        for mention in reversed(tuple(_word_matches(pattern, query, re.IGNORECASE))):
            if any(start < mention.end() and mention.start() < end for start, end in complete_codes):
                continue
            # A bare Latin name immediately after a numeric code can also be
            # its suffix. A declared postposition still makes it a stop role.
            postposition = (intent != 'route_stop_sequence' and re.match(
                r'\s+(?:' + _LOCATION_POSTPOSITION + r')(?!\w)', query[mention.end():], re.IGNORECASE))
            if (re.fullmatch(r'[A-Za-z]+', mention.group()) and not postposition
                    and next(_word_matches(r'(?:[a-z]{0,3})?\d{1,4}[a-z]{0,3}\s*$',
                                           query[:mention.start()], re.IGNORECASE), None)):
                continue
            query = query[:mention.start()] + ' ' * len(mention.group()) + query[mention.end():]
    # Unicode decimal digits include Hindi numerals; preserve operational suffixes.
    query = re.sub(CLOCK_TOKEN, '', query, flags=re.IGNORECASE)
    query = re.sub(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)', '', query)
    ascii_digits = "".join(str(unicodedata.digit(char)) if char.isdecimal() else char
                           for char in unicodedata.normalize('NFC', query))
    # Unit-bearing quantities are not operands of a route list, even when
    # coordinated with a route. Mask the complete decimal, never a prefix.
    ascii_digits = re.sub(ROUTE_QUANTITY, lambda m: ' ' * len(m.group()), ascii_digits, flags=re.IGNORECASE)
    suffixes = {'आर': 'R', 'जी': 'G', 'बी': 'B', 'सी': 'C', 'डी': 'D', 'ए': 'A', 'ई': 'E'}
    unsupported_names = {'एफ', 'एच', 'जे', 'एल', 'एम', 'एन', 'ओ', 'पी', 'क्यू',
                         'एस', 'टी', 'यू', 'वी', 'डब्ल्यू', 'एक्स', 'वाई', 'ज़ेड', 'जेड'}
    letter_names = set(suffixes) | unsupported_names | {'के'}
    def native_suffix_token(word: str) -> bool:
        decomposed = unicodedata.normalize('NFD', word)
        names = '(?:' + '|'.join(re.escape(unicodedata.normalize('NFD', name))
                                 for name in sorted(letter_names - {'के'}, key=len, reverse=True)) + ')+'
        suffix = re.match(names, decomposed)
        return bool(suffix and all(unicodedata.category(char)[0] == 'M' or char.isdecimal()
                                   or char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ#-'
                                   for char in decomposed[suffix.end():]))
    def translate_suffix(match: re.Match) -> str:
        # Marks belong to the suffix; punctuation such as danda ends it.
        if match.end() < len(ascii_digits) and _word_character(ascii_digits[match.end()]):
            return match.group(0)
        return suffixes[match.group(1)]
    ascii_digits = re.sub(r'(?<=\d)\s*-?\s*(' + '|'.join(suffixes) + r')',
                          translate_suffix, ascii_digits)
    ascii_digits = re.sub(r"(?<=\d)\s*-\s*(?=[A-Za-z](?![A-Za-z]))", "-", ascii_digits)
    code = r"(?:[A-Za-z]{1,3})?\d{1,4}(?:[A-Za-z]{1,3})?(?:-[A-Za-z]{1,3})?#?"
    published = _published_route_pattern(known_routes)
    if published:
        code = '(?:' + published + '|' + code + ')'
    terminal = r"(?![\w#-]|[.:]\d)"
    spaced_suffix = r'(?:\s+([A-Za-z]#?)' + terminal + r')?'

    marker = r"(?:bus(?:es)?|bs|routes?|बस|रूट|क्रमांक|संख्या)"
    prefix_pattern = marker + r"\s*(?:(?:route|रूट|no\.?|number|नंबर|संख्या|क्रमांक)\s*)?(" + code + r")" + terminal + spaced_suffix
    suffix_pattern = r"(" + code + r")" + terminal + spaced_suffix + r"\s*" + marker
    possessive_pattern = r"(" + code + r")" + terminal + spaced_suffix + r"\s+(?:ki|ka|ke|की|का|के)(?!\w)"
    bare_pattern = r"(?<![\w:.])(" + code + r")" + terminal + spaced_suffix

    def complete_value(match: re.Match, prefixed: bool) -> str | None:
        end = match.end(2) if match.group(2) else match.end(1)
        if end < len(ascii_digits) and _word_character(ascii_digits[end]):
            return None
        if prefixed:
            punctuated = re.match(r'\s*([–—−.:/]|->|→)\s*([^\s.,;!?]+)', ascii_digits[end:])
            if punctuated:
                separator, operand = punctuated.groups()
                # A token ends at any punctuation outside route symbols,
                # including Hindi danda; its marks remain part of the token.
                token = []
                for char in operand:
                    if not _word_character(char) and char not in '#-':
                        break
                    token.append(char)
                operand = ''.join(token)
                rest = ascii_digits[end + punctuated.start(2):].lower()
                sentence = re.match(r'(?:i|we|you|they|he|she|it)\s+(?:need|want|would|can|will|am|have|prefer|request|ask)(?!\w)'
                                    r'|(?:can|could|would|will|may|should|must|do|does|did)\s+(?:you|we|i|it|the|this|that)(?!\w)', rest)
                # Slash-separated numeric routes are a list; the scope collector
                # must retain every operand rather than discard its first route.
                if not sentence and (re.match(r'\d', operand) and separator != '/'
                        or native_suffix_token(operand)
                        or re.match(r'[a-zA-Z]+[\d\u0900-\u097f#-]', operand)
                        or re.fullmatch(r'[a-zA-Z]+[#-]?', operand)
                        and operand.lower() not in _ROUTE_PROSE_WORDS):
                    return None
            following = re.match(r'\s+(.+)', ascii_digits[end:])
            if following:
                # Consume letters/marks and route symbols, stopping at punctuation.
                token = []
                for char in following.group(1):
                    if not _word_character(char) and char not in '#-':
                        break
                    token.append(char)
                word = ''.join(token).rstrip('#-_')
                hindi_segment = unicodedata.normalize('NFD', re.split(r'[#_-]', word, maxsplit=1)[0])
                plausible_suffix = hindi_segment != 'के' and re.fullmatch(
                    '(?:' + '|'.join(sorted(letter_names, key=len, reverse=True)) + r')+[\u093a-\u094f\u0951-\u0957]*', hindi_segment)
                if (plausible_suffix or native_suffix_token(word)
                        or re.match(r'[A-Za-z]+[\d\u0900-\u097f#-]', ''.join(token))
                        or (re.fullmatch(r'[a-zA-Z]+', ''.join(token))
                            and word.lower() not in _ROUTE_PROSE_WORDS)
                        or re.match(r'(?:' + '|'.join(letter_names) + r')[\d#-]', hindi_segment)):
                    return None
        value = re.sub(r'\s+', '', match.group(1) + (match.group(2) or "")).upper()
        return re.sub(r"(?<=\d)-(?=[A-Z](?:#|$))", "", value)

    def is_excluded(start: int, end: int) -> bool:
        if _negative_transport_proposition(ascii_digits, intent, start, end):
            return False
        before, after = ascii_digits[:start].lower(), ascii_digits[end:].lower()
        negator = r"(?:not|never|no|except|excluding|exclude|avoid|skip|omit|without|other\s+than|rather\s+than|instead\s+of|don't|don’t|dont|won't|won’t|wont|shouldn't|shouldn’t|cannot|can't|can’t|neither|bina|बिना|मत|mat|refuse(?:\s+to)?|refrain\s+from|" + _NATIVE_AVOIDANCE + ')'
        operators = [m for m in _word_matches(negator, before)
                     if not (re.fullmatch(_NATIVE_AVOIDANCE, m.group())
                             and _native_avoidance_has_operand(before[:m.start()]))]
        tail = before[operators[-1].end():].strip() if operators else ''
        preceding = bool(operators and len(tail.split()) <= 8
                         and all(char.isspace() or _word_character(char) and not char.isdecimal() for char in tail)
                         and not next(_word_matches(COORDINATION + r'|but|however|लेकिन|lekin|plus', tail), None)
                         and not _new_request_after_negative_predicate(tail))
        following = re.match(r'\s*(?:(?:ki|ka|ke|की|का|के|ko|को|se|से)\s+)?(?:(?:ever|kabhi|bilkul|कभी|बिल्कुल)\s+)?(?:nahi|nahin|nhi|नहीं|नही|na|ना|न|mat|मत|not|avoid|skip|exclude|omit|bina|बिना|alawa|alava|अलावा|' + _NATIVE_AVOIDANCE + r')(?!\w)', after)
        # English 'not <route operand>' excludes that following operand;
        # it is not postfix negation of the preceding positive identifier.
        if re.match(r'\s+not\s+(?:(?:bus|routes?)\s+)?[a-z]{0,3}\d', after):
            following = None
        if re.match(r'\s+not\s+(?:(?:please|kindly)\s+)?(?:give|quote|show|list|calculate|tell|display)(?!\w)', after):
            following = None
        predicate = re.match(r'\s*(?:(?:stops?|stop\s+list)\s*)?(?:(?:[.;,]\s*)?(?:it|that|this)(?:\s+(?:route|bus))?\s+)?(?:(?:is|are|was|were|should|must)(?:\s+be)?\s+)?(?:excluded|unwanted|forbidden|(?:not|never)\s+(?:ever\s+)?(?:be\s+)?(?:ever\s+)?(?:wanted|allowed|included|used|taken|boarded|chosen|considered))(?!\w)', after)
        negative_head = re.match(r"\s*(?:(?:stops?|stop\s+list)\s*)?(?:(?:[.;,]\s*)?(?:it|that|this)(?:\s+(?:route|bus))?\s+)?(?:"
                                 r"(?:(?:is|are|was|were|should|must)(?:\s+be)?\s+)?(?:not|never)"
                                 r"|isn't|isn’t|aren't|aren’t|shouldn't|shouldn’t|mustn't|mustn’t|won't|won’t|can't|can’t)\s+", after)
        negative_predicate = False
        if negative_head:
            body = after[negative_head.end():]
            action = next(_word_matches(r'used|taken|boarded|chosen|wanted|allowed|included|considered', body), None)
            modifiers = body[:action.start()].strip() if action else ''
            negative_predicate = bool(action and len(modifiers.split()) <= 6
                                      and all(char.isspace() or _word_character(char) and not char.isdecimal() for char in modifiers)
                                      and not next(_word_matches(r'and|or|but|लेकिन|lekin|और|या', modifiers), None))
        use_predicate = re.match(r'\s*(?:(?:ka|ki|ke|का|की|के)\s+)?(?:istemal|istemaal|istamal|istamaal|upyog|upayog|इस्तेमाल|उपयोग)\s+(?:nahi|nahin|nhi|na|नहीं|नही|ना|न|mat|मत)(?!\w)', after)
        return bool(preceding or following or predicate or negative_predicate or use_predicate)

    candidates = {}
    naked_numbers = []
    invalid = False
    context = any(_has(normalize_text(ascii_digits), word) for word in ('bus', 'buses', 'bs', 'बस', 'route', 'routes', 'रूट'))
    for pattern, prefixed in ((prefix_pattern, True), (suffix_pattern, False), (possessive_pattern, False), (bare_pattern, False)):
        for match in _word_matches(pattern, ascii_digits, re.IGNORECASE):
            if pattern == possessive_pattern and not context:
                continue
            if pattern == bare_pattern:
                value = match.group(1).upper()
                letters = re.sub(r'[^A-Z]', '', value)
                if letters in {'MIN','MINS','AM','PM','KM','KG','HR','HRS','RS','INR'} or re.fullmatch(r'\d+(?:ST|ND|RD|TH)', value):
                    continue
                if not letters:
                    unit_after = ascii_digits[match.end():]
                    if re.match(r'\s*(?:passengers?|people|persons?|tickets?|stages?|mins?|minutes?|km|kg|hours?|hrs?|rs|inr|यात्री|यात्रियों|स्टेज|चरण)(?!\w)', unit_after, re.IGNORECASE):
                        continue
                    naked_numbers.append(match)
                    continue
            value = complete_value(match, prefixed)
            if value is None:
                invalid |= prefixed
                continue
            key = match.span(1)
            candidates.setdefault(key, (value, match.start(1), match.end(2) if match.group(2) else match.end(1)))
    # A bare numeric operand inherits route scope only through an explicit
    # exclusion or coordination with an already identified route. Arbitrary
    # passenger counts, distances and isolated digits remain outside it.
    sequence = r'(?:[,;]\s*)?(?:(?:and|और|aur)\s+)?(?:then|next|afterwards?|after\s+that|followed\s+by)'
    connector = r'\s*(?:[,/;，&+]|and|or|also|aur|ya|और|या|plus|through|to|से|तक|se|tak|along\s+with|together\s+with|compared\s+(?:with|to)|' + sequence + r'|versus|vs|nor|as\s+well\s+as)\s*'
    marked_connector = connector + r'(?:(?:bus(?:es)?|bs|routes?|बस|रूट)\s*)?'
    changed = True
    while candidates and changed:
        changed = False
        for match in naked_numbers:
            if match.span(1) in candidates:
                continue
            start, end = match.span()
            linked = any(re.fullmatch(marked_connector, ascii_digits[other_end:start], re.IGNORECASE) if other_end <= start
                         else re.fullmatch(marked_connector, ascii_digits[end:other_start], re.IGNORECASE) if end <= other_start
                         else False for _, other_start, other_end in candidates.values())
            specified = (re.match(r'\s+(?:ki|ka|ke|की|का|के)\s+(?:stops?|स्टॉप)(?!\w)', ascii_digits[end:], re.IGNORECASE)
                         or re.search(r'(?:stops?\s+for|stop\s+list\s+for)\s*$', ascii_digits[:start], re.IGNORECASE))
            if is_excluded(start, end) or linked or specified:
                value = complete_value(match, False)
                if value:
                    candidates[match.span(1)] = (value, start, end)
                    changed = True
    mentions = sorted(candidates.values(), key=lambda mention: mention[1])
    positive, excluded = set(), set()
    prior_end, prior_excluded = None, False
    for value, start, end in mentions:
        negated = is_excluded(start, end)
        # A list headed by an exclusion keeps that polarity through bare or
        # explicitly marked operands; a new clause or contrast resets it.
        if prior_end is not None and prior_excluded:
            link = ascii_digits[prior_end:start]
            inherited = re.fullmatch(connector + r'(?:(?:bus|bs|routes?|बस|रूट)\s*)?', link, re.IGNORECASE)
            if inherited and ';' in link:
                # A semicolon can continue an operand list or start a new
                # request whose imperative follows its route in Hindi. Keep
                # list polarity unless this clause contains an affirmative
                # request; an operand-only list still inherits exclusion.
                clause_tail = re.split(r'[;；।॥!?]', ascii_digits[end:], maxsplit=1)[0].lower()
                request = next(_word_matches(
                    r'show|list|tell|give|display|बताओ|बताइए|बताइये|दिखाओ|दिखाइए|'
                    r'batao|bataiye|dikhao|dikhaiye|chahiye|चाहिए', clause_tail), None)
                rejection = next(_word_matches(
                    r'not|never|no|nahi|nahin|nhi|नहीं|नही|ना|मत|mat|avoid|skip|exclude|omit|'
                    + _NATIVE_AVOIDANCE, clause_tail), None)
                if request and not rejection:
                    inherited = None
            negated |= bool(inherited)
        (excluded if negated else positive).add(value)
        prior_end, prior_excluded = end, negated
    return positive, excluded, invalid


def _route_number(query: str, intent: str | None = None, known_routes: tuple[str, ...] = (), known_entities: tuple[str, ...] = ()) -> str | None:
    positive, excluded, invalid = _route_scope(query, intent, known_routes, known_entities)
    return next(iter(positive)) if len(positive) == 1 and not positive & excluded and not invalid else None


def _ascii_digits(text: str) -> str:
    return ''.join(str(unicodedata.decimal(char)) if char.isdecimal() else char
                   for char in unicodedata.normalize('NFC', text))


def _clock_text(query: str) -> tuple[str, bool]:
    """Convert bounded cardinal clock words only beside an explicit clock unit."""
    text = _ascii_digits(query).lower()
    values = {normalize_text(word): number for number, words in enumerate(_COUNT_WORDS, 1) for word in words}
    values.update({'paanch': 5, 'chhe': 6})
    words = '|'.join(re.escape(word) for word in sorted(values, key=len, reverse=True))
    pattern = r'(?P<number>' + words + r')\s*(?P<unit>am|pm|baje|बजे|o[\x27’]?clock)'
    invalid = bool(re.search(r'(?:quarter|half|saadhe|sadhe|sava|sawa|paune|साढ़े|सवा|पौने)(?:\s+\S+){1,3}\s*(?:am|pm|baje|बजे|o[\x27’]?clock)', text))
    replacements=[]
    for match in _word_matches(pattern, text):
        before = normalize_text(text[:match.start()]).split()[-1:]
        if before and before[0] in {token for word in values for token in word.split()}:
            invalid=True
        replacements.append((match.start('number'), match.end('number'), str(values[match.group('number')])))
    for start,end,value in reversed(replacements):text=text[:start]+value+text[end:]
    # An explicit unsupported word clock cannot vanish from execution.
    for unit in _word_matches(r'am|pm|baje|बजे|o[\x27’]?clock', text):
        prefix=text[:unit.start()].rstrip()
        if unit.group() == 'am' and re.search(r'(?<!\w)i$', prefix):
            continue
        if not re.search(r'\d(?:[:.]\d{2})?(?:[:.]\d{2})?$', prefix):
            invalid=True
    return text,invalid


def _specific_train_owner(text: str, head: re.Match) -> re.Match | None:
    """Bind a generic train head to its adjacent specific mode phrase."""
    owners = tuple(_word_matches(r'metro|mrts|मेट्रो|एमआरटीएस', text[:head.start()]))
    if not owners:
        return None
    owner = owners[-1]
    modifiers = text[owner.end():head.start()].strip()
    words = modifiers.split()
    blockers = (r'and|or|also|aur|ya|और|या|but|however|lekin|लेकिन|from|to|via|से|तक|'
                r'not|no|nahi|nahin|नहीं|mat|मत|bus|buses|बस|local|suburban|rail|'
                r'station|stations|stop|stops|use|take|board|route|routes')
    if (len(words) > 4 or any(not all(_word_character(c) for c in word) for word in words)
            or next(_word_matches(blockers, modifiers), None)):
        return None
    return owner


def _mode_negated(text: str, match: re.Match) -> bool:
    end = match.end()
    if match.group() in {'metro', 'mrts', 'मेट्रो', 'एमआरटीएस'}:
        head = next(_word_matches(r'train|rail|ट्रेन|रेल', text[end:]), None)
        if head:
            absolute = next((m for m in _word_matches(r'train|rail|ट्रेन|रेल', text)
                             if m.start() == end + head.start()), None)
            owner = _specific_train_owner(text, absolute) if absolute else None
            if owner and owner.span() == match.span():
                end = absolute.end()
    following=text[end:]
    preceding=text[:match.start()]
    prefix = next(_word_matches(r'(?:no|not|without|avoid|skip|omit|बिना|मत|mat|' + _NATIVE_AVOIDANCE + r')\s+'
                                r'(?:(?:use|take|board|choose|by|using|a|the)\s+)*$', preceding), None)
    if prefix:
        operator = next(_word_matches(_NATIVE_AVOIDANCE, prefix.group()), None)
        if operator and _native_avoidance_has_operand(preceding[:prefix.start() + operator.start()]):
            prefix = None
    return bool(re.match(r'\s+(?:(?:train|rail|ट्रेन|रेल)\s+)?(?:(?:se|से|ko|को)\s+)?(?:nahi|nahin|nhi|नहीं|नही|mat|मत|not|' + _NATIVE_AVOIDANCE + r')(?!\w)',following)
                or prefix)


def _without_train_modifier_entities(text: str, spans: tuple[EntitySpan, ...]) -> tuple[EntitySpan, ...]:
    """An adjective inside a specific train noun phrase is not a place operand."""
    modifiers = {'new', 'old', 'fast', 'slow', 'electric', 'diesel', 'rapid', 'modern'}
    ranges = []
    for head in _word_matches(r'train|rail|ट्रेन|रेल', text):
        owner = _specific_train_owner(text, head)
        if owner:
            ranges.append((owner.end(), head.start()))
    return tuple(span for span in spans if not (
        set(span.surface.split()) <= modifiers
        and any(start <= span.start and span.end <= end for start, end in ranges)))


def _time(query: str) -> str | list[str] | None:
    text, invalid_word_clock = _clock_text(query)
    if invalid_word_clock:
        return None
    periods = {period for period, phrases in {
        'morning': ('subah', 'सुबह', 'morning'), 'afternoon': ('dopahar', 'दोपहर', 'afternoon'),
        'evening': ('shaam', 'शाम', 'evening'), 'night': ('raat', 'रात', 'night')}.items()
        if any(_has(normalize_text(text), phrase) for phrase in phrases)}
    if len(periods) > 1:
        return None
    period = next(iter(periods), None)

    def period_hour(hour: int):
        if hour > 12:
            return hour if period != 'morning' else None
        if period in {'afternoon', 'evening'}:
            return hour % 12 + 12
        if period == 'morning':
            return hour % 12
        if period == 'night':
            return (0 if hour == 12 else hour if hour <= 4 else
                    [hour, hour + 12] if hour <= 7 else hour + 12)
        return hour
    explicit = re.search(r"(?<![\d:.])(\d{1,2})(?:[:.](\d{2})(?::(\d{2}))?)?\s*(am|pm)(?!\w)", text)
    if explicit:
        hour, minute = int(explicit.group(1)), int(explicit.group(2) or 0)
        second = int(explicit.group(3) or 0)
        if 1 <= hour <= 12 and minute < 60 and second < 60:
            value = hour % 12 + (12 if explicit.group(4) == 'pm' else 0)
            inferred = period_hour(hour)
            if period and (value not in inferred if isinstance(inferred, list) else value != inferred):
                return None
            return f"{value:02d}:{minute:02d}:{second:02d}"
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
        if period or hour > 12:
            value = period_hour(hour)
            return ([stamp(item) for item in value] if isinstance(value, list)
                    else stamp(value) if value is not None else None)
        return [stamp(hour % 12), stamp(hour % 12 + 12)]
    twenty_four = re.search(r"(?<![\d:.])(\d{1,2}):(\d{2})(?::(\d{2}))?(?![\d:])", text)
    if twenty_four:
        hour, minute = int(twenty_four.group(1)), int(twenty_four.group(2))
        second = int(twenty_four.group(3) or 0)
        if hour < 24 and minute < 60 and second < 60:
            value = period_hour(hour)
            return ([f"{item:02d}:{minute:02d}:{second:02d}" for item in value] if isinstance(value, list)
                    else f"{value:02d}:{minute:02d}:{second:02d}" if value is not None else None)
    return None





def _multiple_scopes(text: str, intent: str, spans: tuple[EntitySpan, ...], known_routes: tuple[str, ...] = ()) -> bool:
    """Reject cardinality that a single-operation slot schema cannot represent."""
    # Keep punctuation for clocks, ISO dates and complete route suffixes.
    text = _clock_text(text)[0]
    clauses = _word_split(COORDINATION, text, punctuation=r'[,，&]')
    known_entities = tuple(span.surface for span in spans)
    lines = {line for line in LINE_NAMES if _has(positive_goal_attribute_text(text), line)}
    if len(lines) > 1 or (lines and _route_number(text, intent, known_routes, known_entities)):
        return True
    positive_routes, excluded_routes, invalid_route = _route_scope(text, intent, known_routes, known_entities)
    if len(positive_routes) > 1 or positive_routes & excluded_routes:
        return True
    if len(clauses) > 1:
        if sum(_explicit_route_marker(clause) for clause in clauses) > 1 and any(
                _explicit_route_marker(clause) and _route_number(clause, intent, known_routes, known_entities) is None and not _route_scope(clause, intent, known_routes, known_entities)[1] for clause in clauses):
            return True
    if intent == 'fare_calculation':
        stages, _, _ = _stage_counts(text)
        if len(stages) > 1:
            return True
    if intent in {'route_stop_membership', 'nearest_transport', 'station_accessibility', 'station_facilities', 'ticketing_and_passes'}:
        identities = {tuple(sorted(c.entity_id for c in span.candidates)) for span in spans}
        if len(identities) > 1:
            return True
    vocabulary = {'station_accessibility': ACCESSIBILITY, 'station_facilities': FACILITIES,
                  'ticketing_and_passes': TICKETS}.get(intent)
    if vocabulary and sum(any(_has(normalize_text(text), alias) for alias in (value, *aliases))
                          for value, aliases in vocabulary.items()) > 1:
        return True
    temporal_intents = {'first_and_last_service', 'service_frequency', 'scheduled_departure',
                        'point_to_point_route', 'multimodal_route', 'mode_availability'}
    if intent in temporal_intents:
        clocks = {match.group().strip() for match in re.finditer(CLOCK_TOKEN, text)}
        inherited_clock = re.search(r'\d{1,2}\s*' + COORDINATION + r'\s*\d{1,2}\s*(?:am|pm|baje|बजे)(?!\w)', text)
        dates = set(re.findall(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)', text))
        explicit_relative = {value for phrase,value in [('aane wale kal','tomorrow'),('आने वाले कल','tomorrow'),('beete kal','yesterday'),('बीते कल','yesterday')] if _has(normalize_text(text),phrase)}
        relative_text=text
        for phrase in ('aane wale kal','आने वाले कल','beete kal','बीते कल'):
            relative_text=relative_text.replace(phrase,' ')
        relative_days = explicit_relative | {value for value, words in {
            'today': ('today', 'aaj', 'आज'), 'tomorrow': ('tomorrow',),
            'yesterday': ('yesterday',), 'kal': ('kal', 'कल'), 'parso': ('parso', 'परसों')}.items()
            if any(_has(normalize_text(relative_text), word) for word in words)}
        if len(clocks) > 1 or inherited_clock or len(dates) + len(relative_days) > 1:
            return True
    return False


def _explicit_route_marker(text: str) -> bool:
    """Detect an explicit numeric route even when its suffix is unsupported."""
    text = re.sub(CLOCK_TOKEN, '', text)
    text = re.sub(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)', '', text)
    text = re.sub(ROUTE_QUANTITY, lambda m: ' ' * len(m.group()), text, flags=re.IGNORECASE)
    marker = r'(?:\bbus(?:es)?\b|\bbs\b|\broutes?\b|बस|रूट)'
    return bool(re.search(marker + r'\s*(?:(?:route|रूट|no\.?|number|नंबर|संख्या|क्रमांक)\s*)?(?:[a-z]{1,3})?\d', text)
                or re.search(r'(?<!\w)(?:[a-z]{1,3})?\d[^\s?.,!:;()]*(?:\s+[^\s?.,!:;()]+)?\s*' + marker, text))


class T3SlotExtractor:
    def __init__(self, resolver: CanonicalResolver):
        self.resolver = resolver
        self.known_routes = tuple(sorted(getattr(resolver, 'route_stops', {})))

    def extract(self, query: str, intent: str, *, default_transport_mode: str | None = None) -> ExtractionResult:
        """Extract explicit canonical slots for one T3 intent."""
        if intent not in T3_INTENTS:
            raise ContractError(f"Unknown T3 intent: {intent}")
        normalized = normalize_text(query)
        slots: dict[str, object] = {}
        spans = _without_train_modifier_entities(normalized, self.resolver.find_spans(query))
        code_ranges = _published_code_ranges(normalized, self.known_routes)
        # A suffix token belongs to its complete published route operand,
        # even if the gazetteer also contains a stop with that short name.
        spans = tuple(span for span in spans if not any(
            start <= span.start and span.end <= end for start, end in code_ranges))
        if intent == 'nearest_transport':
            # Gazetteers can contain generic names such as "Bus Stop". Those
            # words describe the requested target, not the search's anchor.
            generic_targets = {'bus stop', 'bus station', 'metro station', 'railway station',
                               'train station', 'बस स्टॉप', 'बस स्टेशन', 'मेट्रो स्टेशन', 'रेलवे स्टेशन'}
            spans = tuple(span for span in spans if span.surface not in generic_targets)
        unresolved: list[Resolution] = []
        invalid_temporal = False
        missing_execution = ()
        multiple_locations = False

        known_entities = tuple(span.surface for span in spans)
        positive_routes, excluded_routes, invalid_route = _route_scope(query, intent, self.known_routes, known_entities)
        attribute_text = positive_goal_attribute_text(query)
        attribute_spans = self.resolver.find_spans(attribute_text)
        if intent == 'nearest_transport':
            attribute_spans = tuple(span for span in attribute_spans
                                    if span.surface not in generic_targets)
        mode_hits = []
        excluded = []
        for mode, pattern in MODE_PATTERNS.items():
            # In nearest queries, mode words in the anchor name describe its
            # location, not the requested target mode. Other intents retain
            # mode-qualified station resolution (e.g. Guindy metro).
            matches = [m for m in _word_matches(pattern, normalized)
                       if (intent != 'nearest_transport'
                           or not any(span.start <= m.start() < span.end for span in spans))
                       and not (mode == 'suburban_rail' and m.group() in {'train','rail','ट्रेन','रेल'}
                                and _specific_train_owner(normalized, m) is not None)]
            def retain_route_modes(matches, mode_text):
                if mode != 'bus' or not excluded_routes:
                    return matches
                retained = []
                for match in matches:
                    operand = re.match(r'\s*(?:(?:routes?|no|number|रूट|नंबर)\s*)?((?:[a-z]{1,3})?\d{1,4}[a-z\u0900-\u097f]*(?:\s*[\-]\s*[a-z])?#?(?:\s+(?:[a-z](?![a-z])|आर|जी|बी|सी|डी|ए|ई)#?)?)', _ascii_digits(mode_text[match.end():]))
                    value = operand.group(1) if operand else ''
                    # Include the complete spaced suffix before asking the
                    # canonical route parser about polarity. A partial parent
                    # match must not erase a genuinely explicit bus mention.
                    tail = mode_text[match.end():]
                    remainder = tail[operand.end():] if operand else ''
                    while operand:
                        suffix = re.match(r'\s+([a-z]+)(?!\w)', remainder)
                        if not suffix or suffix.group(1) in _ROUTE_PROSE_WORDS:
                            break
                        value += ' ' + suffix.group(1)
                        remainder = remainder[suffix.end():]
                    mentioned = _route_number('bus ' + value, known_routes=self.known_routes) if operand else None
                    if mentioned not in excluded_routes or mentioned in positive_routes:
                        retained.append(match)
                return retained
            matches = retain_route_modes(matches, normalized)
            negated = [m for m in matches if _mode_negated(normalized, m)
                       and not _negative_transport_proposition(normalized, intent, m.start(), m.end())]
            positive = [m for m in _word_matches(pattern, attribute_text)
                        if (not _mode_negated(attribute_text, m)
                            or _negative_transport_proposition(attribute_text, intent, m.start(), m.end()))
                        and (intent != 'nearest_transport'
                             or not any(span.start <= m.start() < span.end for span in attribute_spans))
                        and not (mode == 'suburban_rail' and m.group() in {'train','rail','ट्रेन','रेल'}
                                 and _specific_train_owner(attribute_text, m) is not None)]
            positive = retain_route_modes(positive, attribute_text)
            if negated:
                excluded.append(mode)
            if positive:
                mode_hits.append((positive[0].start(), mode))
        requested_modes = tuple(mode for _, mode in sorted(mode_hits))
        excluded_modes = tuple(sorted(excluded))
        if not requested_modes and default_transport_mode not in excluded_modes and default_transport_mode is not None and intent not in {'out_of_scope', 'multimodal_route', 'interchange_transfer'}:
            if default_transport_mode not in MODE_PATTERNS:
                raise ContractError('Unknown default transport mode')
            requested_modes = (default_transport_mode,)
        mode = requested_modes[0] if len(requested_modes) == 1 else None
        if mode and intent not in {"out_of_scope"}:
            slots["transport_mode"] = mode
        if intent == "interchange_transfer" and len(requested_modes) == 2:
            slots["mode_from"], slots["mode_to"] = requested_modes

        code = _route_number(query, intent, self.known_routes, known_entities)
        if code and intent in {"route_stop_sequence", "route_stop_membership", "first_and_last_service", "service_frequency", "scheduled_departure", "fare_calculation", "realtime_status_query", "point_to_point_route", "multimodal_route", "mode_availability", "interchange_transfer"}:
            slots["route_number"] = code
        elif not code and intent in {'point_to_point_route', 'mode_availability', 'multimodal_route',
                                    'scheduled_departure', 'first_and_last_service', 'service_frequency',
                                    'route_stop_sequence', 'route_stop_membership', 'fare_calculation',
                                    'interchange_transfer'} and (positive_routes or excluded_routes or invalid_route or _explicit_route_marker(query.lower())):
            missing_execution = ('route_number',)

        if intent == "first_and_last_service":
            first = any(_has(normalized, word) for word in ("first", "पहली", "पहला", "pehli", "pehla"))
            last = any(_has(normalized, word) for word in ("last", "आखिरी", "aakhiri"))
            if first != last:
                slots["timing_type"] = "first" if first else "last"

        for line in LINE_NAMES:
            if _has(attribute_text, line) and intent in {"point_to_point_route", "multimodal_route", "route_stop_sequence", "route_stop_membership", "first_and_last_service", "service_frequency", "scheduled_departure", "mode_availability", "interchange_transfer", "realtime_status_query"}:
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
            stages, invalid_stage, stage_mentioned = _stage_counts(query)
            if len(stages) == 1 and not invalid_stage:
                slots['stage_number'] = next(iter(stages))
                # A published stage tariff needs no route operand. Retain an
                # avoided route as a constraint without making it an input to
                # this independent calculation. Invalid/positive route scopes
                # still keep their existing clarification requirements.
                if excluded_routes and not positive_routes and not invalid_route:
                    missing_execution = tuple(name for name in missing_execution if name != 'route_number')
            elif stage_mentioned and len(stages) < 2:
                missing_execution += ('stage_number',)
            if _uncertain_service_class(normalized):
                slots.pop('service_type', None)
                missing_execution += ('service_type',)

        if intent in {"first_and_last_service", "service_frequency", "scheduled_departure", "point_to_point_route", "multimodal_route", "mode_availability"}:
            clock_query=query
            for span in spans:
                for raw in re.finditer(re.escape(span.surface),query,re.I):
                    clock_query=clock_query[:raw.start()]+" "*(raw.end()-raw.start())+clock_query[raw.end():]
            clock = _time(clock_query)
            if clock:
                slots["time"] = clock
            elif re.search(r"\d{1,2}[:.]\d{2}|\d{1,2}\s*(?:am|pm|baje|बजे)", _clock_text(clock_query)[0], re.IGNORECASE) or _clock_text(clock_query)[1]:
                invalid_temporal = True
        if intent in {"first_and_last_service", "service_frequency", "scheduled_departure", "point_to_point_route", "multimodal_route", "mode_availability", "realtime_status_query"}:
            date_match = re.search(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)", _ascii_digits(query))
            if date_match:
                try:
                    calendar_date.fromisoformat(date_match.group())
                    slots["date"] = date_match.group()
                except ValueError:
                    invalid_temporal = True
            explicit_relative = next((value for phrase,value in (
                ('aane wale kal','tomorrow'),('आने वाले कल','tomorrow'),
                ('beete kal','yesterday'),('बीते कल','yesterday')) if _has(normalized,phrase)),None)
            if explicit_relative:
                slots['temporal_relative']=explicit_relative
            else:
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
                              if via_marker and (
                                  via_marker.group() == 'via' and span.start >= via_marker.end()
                                  and re.fullmatch(r'\s*', normalized[via_marker.end():span.start])
                                  or via_marker.group() != 'via' and span.end <= via_marker.start()
                                  and re.fullmatch(r'\s*', normalized[span.end:via_marker.start()])
                                  and not re.search(r'(?<!\w)(?:from|to)\s*$', normalized[:span.start]))), None)
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
            timetable_spans = _timetable_unique_spans(normalized, spans)
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
                multiple_locations = len(timetable_spans) > 2 or _unknown_timetable_coordination(query, spans)
                if len(timetable_spans) >= 2:
                    origin, destination = _endpoints(normalized, list(timetable_spans))
                    assign(origin, "station")
                    assign(destination, "destination")
                elif timetable_spans:
                    assign(timetable_spans[0], 'station')
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
        request_constraints = {}
        if excluded_routes:
            request_constraints['excluded_routes'] = sorted(excluded_routes)
        if positive_routes:
            request_constraints['required_routes'] = sorted(positive_routes)
        if excluded_modes:
            request_constraints['excluded_modes'] = list(excluded_modes)
        if requested_modes:
            request_constraints['required_modes'] = list(requested_modes)
        period = next((name for name,words in {
            'morning':('सुबह','subah','morning'), 'afternoon':('दोपहर','dopahar','afternoon'),
            'evening':('शाम','shaam','evening'), 'night':('रात','raat','night')}.items()
            if any(_has(normalized, word) for word in words)), None)
        if period and intent in {'scheduled_departure','service_frequency','first_and_last_service','point_to_point_route','mode_availability','multimodal_route'}:
            request_constraints['day_period']=period
            if not slots.get('time') and not invalid_temporal:
                unsupported_temporal=True
        if intent == 'nearest_transport' and any(_has(normalized,word) for word in ('walking','walk','पैदल','paidal','walking distance','walk distance','पैदल दूरी','paidal doori','walking network')):
            request_constraints['distance_metric']='walking_network'
        return ExtractionResult(slots, spans, tuple(unresolved), reason, requested_modes, normalized,
                                missing_execution, multiple_locations or _multiple_scopes(query, intent, spans, self.known_routes),
                                unsupported_temporal, unsupported_timetable_waypoint, excluded_modes, request_constraints)
