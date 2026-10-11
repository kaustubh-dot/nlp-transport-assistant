import re
import unicodedata
from .text import normalize_extraction_text as normalize_text

"""Shared explicit goal cues for guards and operand polarity ownership."""

_MEMBERSHIP_PREDICATE = r'stop|stops|stopping|halt|halts|halting|rukti|rukta|रुकती|रुकता'

_MEMBERSHIP_QUESTION_CUE = (r'(?:' + _MEMBERSHIP_PREDICATE + r')\s+at|'
                            r'(?:पर|में|par|mein)\s+(?:(?:नहीं|नही|nahi|nahin|not)\s+)?'
                            r'(?:' + _MEMBERSHIP_PREDICATE + r')')

# This guard only requests clarification for independently expressed conjoined
# goals. It never chooses an operation or substitutes a rule-based classifier.
GOAL_CUES = (
    ("first_and_last_service", r"(?:first|last|पहली|पहला|आखिरी|pehli|pehla|aakhiri)\s+(?:buses|bus|trains?|metro|service|departure|timing|time|बस|ट्रेन|मेट्रो|सेवा)(?!\w)(?!\s+(?:stops?|station|स्टॉप|स्टेशन))(?:\s+(?:(?:ka|ki|ke|का|की|के)\s+)?(?:departures?|schedules?|timetables?|timings?|times?|समय|samay)(?!\w))?"),
    ("service_frequency", r"frequenc(?:y|ies)|headways?|how often|kitni der|कितनी देर"),
    ("scheduled_departure", r"departures?|schedules?|timetables?|छूटे|chhut"),
    ("fare_calculation", r"fares?|costs?|prices?|किरा(?:या|ये|ए)|kiray[ae]"),
    ("station_accessibility", r"wheelchair|ramp|lift|escalator|व्हीलचेयर|लिफ्ट|रैंप"),
    ("station_facilities", r"parking|toilet|restroom|wifi|atm|पार्किंग|शौचालय"),
    ("ticketing_and_passes", r"pass|ticket rules|smart card|टिकट|पास"),
    ("route_stop_sequence", r"all stops|(?:list|show)\s+stops|route stops|stops? lists?|stop sequences?|सभी स्टॉप"),
    ("route_stop_membership", _MEMBERSHIP_QUESTION_CUE + r'|रुकती|rukti'),
    ("nearest_transport", r"nearest|closest|nazdik|नजदीक"),
    ("interchange_transfer", r"transfer|interchange|बदलना|badalna"),
    ("realtime_status_query", r"(?:live|realtime)(?:\s+status)?|delay|अभी(?:\s+(?:बस|ट्रेन|मेट्रो))?\s+कहाँ"),
    ("point_to_point_route", r"routes?(?!\s+(?:(?:no|number)\s+)?[a-z]{0,3}\d)|how to get|kaise|कैसे"),
    ("mode_availability", r"available|availability|चलती|chalti"),
)



def _word_character(char: str) -> bool:
    # Python's \w excludes combining marks: a Hindi vowel or virama must not
    # become a word boundary (e.g. लोकल must not contain the relative day कल).
    return unicodedata.category(char)[0] in 'LNM' or char == '_'


def _word_matches(pattern: str, text: str, flags: int = 0):
    # Keep the boundary inside the regex so alternatives can backtrack from
    # "nahi" to "nahin", or from "न" to "ना". Filtering afterward discards
    # the shorter match without ever trying the complete alternative. Include
    # every combining mark present in this text alongside Python's word class.
    marks = ''.join(sorted({char for char in text if unicodedata.category(char)[0] == 'M'}))
    boundary = r'[\w' + re.escape(marks) + ']'
    return re.finditer(r'(?<!' + boundary + ')(?:' + pattern + ')(?!' + boundary + ')', text, flags)


_NATIVE_AVOIDANCE = (r'छोड़कर|छोडकर|छोड़ो|छोडो|छोड़िए|छोड़िये|छोडिए|छोडिये|'
                     r'chhodo|chodo|chhodkar|chodkar|chhod\s+do|chod\s+do')
_AVOIDANCE_GOAL_HEAD = (r'stops?|list|sequence|स्टॉप|सूची|times?|timings?|समय|samay|'
                        r'frequency|headway|आवृत्ति|ticket|tickets|pass|passes|पास|टिकट')


def _native_avoidance_has_operand(prefix: str) -> bool:
    """A postfix avoidance verb already owns a preceding operand or goal."""
    owner = re.sub(r'\s+(?:ko|को)\s*$', '', prefix.strip())
    explicit_goal_owner = any(
        any(cue.end() == len(owner) for cue in _word_matches(pattern, owner))
        for _, pattern in GOAL_CUES)
    return explicit_goal_owner or next(_word_matches(
        r'(?:bus|metro|mrts|rail|train|बस|मेट्रो|एमआरटीएस|रेल|ट्रेन|'
        r'(?:[a-z]{0,3})?\d{1,4}(?:[a-z\u0900-\u097f#-]+|\s+(?:[a-z]+|आर|जी|बी|सी|डी|ए|ई)){0,4}|' + _AVOIDANCE_GOAL_HEAD + r')\s*$', owner), None) is not None
def _new_request_after_negative_predicate(text: str) -> bool:
    return next(_word_matches(r'(?:wanted|needed|required|requested|chahiye|चाहिए)\s+'
                              r'(?:(?:please|kindly)\s+)?(?:show|list|tell|give|display|calculate|quote|दिखाओ|बताओ|batao|dikhao)', text), None) is not None


_NEGATIVE_CONTRACTION = r'(?:isn|aren|wasn|weren|doesn|don|didn|shouldn|wouldn|couldn|mustn|needn|hasn|haven|hadn|can|won)\s*t'


def _cue_is_negated(text: str, match: re.Match) -> bool:
    following = text[match.end():]
    preceding = text[:match.start()]
    current_pattern = next((pattern for _, pattern in GOAL_CUES if re.fullmatch(pattern, match.group())), match.re.pattern)
    other_goal_patterns = [pattern for _, pattern in GOAL_CUES if pattern != current_pattern]
    def has_other_goal(fragment: str) -> bool:
        same_goals = tuple(_word_matches(current_pattern, fragment))
        return any(not any(same.start() <= cue.start() and cue.end() <= same.end() for same in same_goals)
                   for pattern in other_goal_patterns for cue in _word_matches(pattern, fragment))
    # An immediately following route exclusion belongs to the identifier, not
    # the operation noun (e.g. a stop list followed by an excluded route).
    if re.match(r'\s+(?:not|no|nahi|nahin|नहीं)\s+(?:(?:routes?|bus|रूट|बस)\s+)?[a-z]{0,3}\d', following):
        return False
    postfix = next(_word_matches(r'नहीं|नही|न|ना|nahi|nahin|nhi|na|not|never|neither|nor|मत|mat|' + _NEGATIVE_CONTRACTION + '|' + _NATIVE_AVOIDANCE, following), None)
    if postfix:
        operand = following[:postfix.start()].strip()
        # Postposition predicates can follow an operand and arbitrary modifiers.
        # Bind them to the closest goal in this punctuation-preserved clause.
        if (not all(char.isspace() or _word_character(char) for char in operand)
                or has_other_goal(operand)):
            postfix = None
        else:
            remainder = following[postfix.end():].strip()
            if (re.fullmatch(_NATIVE_AVOIDANCE, postfix.group())
                    and next(_word_matches(r'(?:[a-z]{0,3})?\d{1,4}[a-z]{0,3}\s*(?:ko|को)?\s*$', operand), None)):
                # A postfix avoidance instruction owns its preceding route,
                # rather than the positive operation requested before it.
                postfix = None
            auxiliary = next(_word_matches(r'is|are|was|were|should|must', operand), None)
            if postfix and postfix.group() in {'not', 'never'} and auxiliary is None:
                # A bare English operator can introduce the next goal instead:
                # "stop list, not the fare" or "do not show the fare".
                complement = r'(?:(?:a|an|the|any|give|quote|show|list|calculate|tell|me|us|about|please|request|ordinary|express|deluxe|bus|buses)\s+)*'
                if (re.match(r'(?:(?:routes?|bus|buses)\s+)?[a-z]{0,3}\d', remainder)
                        or any((cue := next(_word_matches(pattern, remainder), None)) is not None
                               and re.fullmatch(complement, remainder[:cue.start()])
                               for pattern in other_goal_patterns)):
                    postfix = None
    if postfix:
        return True
    # Negation is an operator over the adjacent requested goal. Its bounded
    # intervening words may include arbitrary request verbs/qualifiers. A
    # prior goal cue or a numeric/entity operand ends that operator's scope.
    operators = list(_word_matches(r'(?:not|never|no|neither|nor|dont|nahi|nahin|nhi|na|नहीं|नही|न|ना|मत|mat|without|except|excluding|exclude|avoid|skip|omit|refuse(?:\s+to)?|refrain\s+from|' + _NEGATIVE_CONTRACTION + '|' + _NATIVE_AVOIDANCE + ')', preceding))
    if not operators:
        return False
    if re.fullmatch(_NATIVE_AVOIDANCE, operators[-1].group()):
        owner = re.sub(r'\s+(?:ko|को)\s*$', '', preceding[:operators[-1].start()].strip())
        if (_native_avoidance_has_operand(owner)
                or any(any(cue.end() == len(owner) for cue in _word_matches(pattern, owner))
                       for _, pattern in GOAL_CUES)):
            return False
    tail = preceding[operators[-1].end():].strip()
    # A completed negative predicate followed by a new request verb ends the
    # prior goal's operator scope, even without a written conjunction.
    if _new_request_after_negative_predicate(tail):
        return False
    # A quantity explicitly modifying the requested goal does not end the
    # negation scope; unrelated numeric/entity operands still do.
    tail = re.sub(r'\d+\s+(?:stages?|स्टेज|चरण)(?!\w)', ' ', tail)
    tail = re.sub(r'(?:stages?|स्टेज|चरण)\s+(?:(?:number|count|नंबर|संख्या)\s+)?\d+', ' ', tail)
    words = tail.split()
    if any(not all(_word_character(char) and not char.isdecimal() for char in word) for word in words):
        return False
    if words and words[0] in {'bus','buses','metro','mrts','rail','train','suburban','local','बस','मेट्रो','ट्रेन','रेल','एमआरटीएस'}:
        return False
    if has_other_goal(tail):
        return False
    return True



def _goal_clauses(query: str) -> list[str]:
    # Preserve clause punctuation until scopes are separated. Each clause
    # uses the same extraction-only normalization as the existing goal cues.
    text = query.lower()
    text = re.sub(r"(?<!\w)(first|पहली|पहला|pehli|pehla)(?:\s+(?:services?|departures?|bus(?:es)?|trains?|timings?|times?|सेवा|बस|ट्रेन))*\s+(?:and|aur|और)\s+(last|आखिरी|aakhiri)(?!\w)", r"\1 \2", text)
    separators = sorted([*_word_matches(r'(?:and|also|aur|और|साथ ही|plus|along\s+with|together\s+with|but|however|lekin|लेकिन)', text),
                         *re.finditer(r'[;；,，!?।॥]|[—–]|(?<!\d)\.(?!\d)|(?<=\d)\.(?![\da-z])', text)], key=lambda m: m.start())
    clauses, cursor = [], 0
    for separator in separators:
        left, right = text[:separator.start()].rstrip(), text[separator.end():].lstrip()
        # Coordinated synonymous goal nouns share their following operand
        # and predicate. An operand or new request between nouns separates scopes.
        if any((cues := tuple(_word_matches(pattern, left))) and cues[-1].end() == len(left)
               and (cue := next(_word_matches(pattern, right), None)) is not None and cue.start() == 0
               for _, pattern in GOAL_CUES):
            continue
        clauses.append(normalize_text(text[cursor:separator.start()]))
        cursor = separator.end()
    clauses.append(normalize_text(text[cursor:]))
    return clauses


def positive_goal_attribute_text(query: str) -> str:
    """Only an affirmative goal contributes required mode/line attributes.

    Keep clauses with no explicit goal (including independent exclusions), and
    clauses whose goal polarity is not wholly negative. This is extraction
    metadata; the raw request still reaches the classifier unchanged.
    """
    clauses = [clause for clause in _goal_clauses(query) if clause.strip()]
    active = []
    for clause in clauses:
        cues = [(intent, cue) for intent, pattern in GOAL_CUES
                for cue in _word_matches(pattern, clause)]
        positive = any(intent in {'mode_availability', 'route_stop_membership'}
                       or not _cue_is_negated(clause, cue) for intent, cue in cues)
        if not cues or positive:
            active.append(clause)
    # The selected-goal guard refuses wholly negative requests. Preserve their
    # extraction metadata, and avoid changing ordinary positive query grammar.
    if not active or len(active) == len(clauses):
        return normalize_text(query)
    return normalize_text(' ; '.join(active))
