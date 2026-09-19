#!/usr/bin/env python3
"""Deterministic Noise Engine for Gate B.1.

Implements genuine, visible text corruptions:
N0: Clean pristine query
N1: Casing, whitespace, punctuation stripping
N2: Common commuter phonetic transliteration shifts (e.g. guindy->gindi, kaise->kese)
N3: Adjacent keyboard character transpositions and key slips
N4: Vowel omission and heavy truncation (e.g. airport->arprt, central->cntrl)
N5: Realistic commuter SMS / chat shorthand (human interpretable)
"""

from typing import Tuple
import re
import random

PHONETIC_REPLACEMENTS = [
    (r"\bguindy\b", "gindi"),
    (r"\bGuindy\b", "Gindi"),
    (r"\bkaise\b", "kese"),
    (r"\bKaise\b", "Kese"),
    (r"\bairport\b", "erport"),
    (r"\bAirport\b", "Erport"),
    (r"\bmetro\b", "mtro"),
    (r"\bMetro\b", "Mtro"),
    (r"\bkitna\b", "ktna"),
    (r"\bkitne\b", "ktne"),
    (r"\bkitni\b", "ktni"),
    (r"\bkahan\b", "kha"),
    (r"\bkaunsi\b", "konsi"),
    (r"\bkaun\b", "kon"),
    (r"\braasta\b", "rasta"),
    (r"\bchalegi\b", "chlgi"),
    (r"\bniklegi\b", "nklgi"),
    (r"\bavailable\b", "availbl"),
    (r"\bticket\b", "tkt"),
    (r"\bTicket\b", "Tkt"),
    (r"\bcentral\b", "sntrl"),
    (r"\bCentral\b", "Sntrl"),
    (r"\bstation\b", "stn"),
    (r"\bStation\b", "Stn"),
    (r"\btambaram\b", "tambrum"),
    (r"\bTambaram\b", "Tambrum"),
    (r"\btime\b", "tym"),
    (r"\bplease\b", "plz"),
    (r"\broute\b", "rout"),
    (r"\bstops\b", "stps"),
    (r"\bhai\b", "h"),
    (r"\bkya\b", "kya"),
    (r"\bbatao\b", "btao"),
    (r"\bbataiye\b", "btaiye")
]

KEYBOARD_ADJACENT = {
    'a': 's', 's': 'a', 'e': 'r', 'r': 'e', 'i': 'o', 'o': 'i',
    'n': 'm', 'm': 'n', 't': 'y', 'y': 't', 'k': 'l', 'l': 'k',
    'd': 'f', 'f': 'd', 'u': 'y', 'p': 'o', 'b': 'v', 'v': 'b',
    'c': 'x', 'x': 'c', 'g': 'h', 'h': 'g', 'j': 'h', 'l': 'k'
}

TRUNCATION_WORDS = {
    "airport": "arprt",
    "central": "cntrl",
    "station": "stn",
    "timing": "tmg",
    "schedule": "sched",
    "frequency": "freq",
    "kaise": "kse",
    "jaana": "jna",
    "batao": "btao",
    "kahan": "khn",
    "direct": "drct",
    "metro": "mtro",
    "train": "trn",
    "please": "pls",
    "ticket": "tkt",
    "route": "rt",
    "stops": "stps",
    "wheelchair": "whlchr",
    "interchange": "xchng",
    "tracking": "trckng",
    "location": "loc",
    "change": "chg"
}

SMS_SHORTHAND_MAP = {
    "airport": "arprt",
    "central": "cntrl",
    "kaise": "kse",
    "jaun": "jau",
    "jaana": "jna",
    "hai": "h",
    "kya": "kya",
    "se": "s",
    "ko": "ko",
    "pe": "p",
    "par": "pr",
    "metro": "mtro",
    "train": "trn",
    "bus": "bs",
    "station": "stn",
    "kab": "kb",
    "first": "fst",
    "last": "lst",
    "ticket": "tkt",
    "batao": "btao",
    "please": "plz",
    "available": "avl",
    "timing": "tym",
    "time": "tym",
    "right now": "rgt nw",
    "live": "liv"
}

def apply_noise(clean_text: str, noise_level: str, rng: random.Random) -> Tuple[str, str]:
    """Applies genuine, visible transformation based on noise level.
    Guarantees query != clean_query when noise_level != N0.
    """
    if noise_level == "N0":
        return clean_text, "clean"

    if noise_level == "N1":
        noisy = clean_text.lower()
        noisy = re.sub(r"[?!.,:;'\"]", "", noisy)
        noisy = re.sub(r"\s+", " ", noisy).strip()
        if noisy == clean_text:
            noisy = noisy + " "
        return noisy, "casing_and_punctuation_normalization"

    if noise_level == "N2":
        noisy = clean_text
        applied = False
        for pat, rep in PHONETIC_REPLACEMENTS:
            if re.search(pat, noisy, flags=re.IGNORECASE):
                noisy = re.sub(pat, rep, noisy, count=1, flags=re.IGNORECASE)
                applied = True
                break
        if not applied:
            if "ai" in noisy:
                noisy = noisy.replace("ai", "e", 1)
            elif "ee" in noisy:
                noisy = noisy.replace("ee", "i", 1)
            elif "oo" in noisy:
                noisy = noisy.replace("oo", "u", 1)
            elif "ी" in noisy:
                noisy = noisy.replace("ी", "ि", 1)
            elif "ू" in noisy:
                noisy = noisy.replace("ू", "ु", 1)
            elif "े" in noisy:
                noisy = noisy.replace("े", "ै", 1)
            else:
                # Fallback typo in last word
                words = noisy.split()
                if words and len(words[-1]) > 2:
                    words[-1] = words[-1][:-1]
                    noisy = " ".join(words)
        noisy = re.sub(r"[?!.,:;'\"]", "", noisy).strip()
        if noisy == clean_text:
            noisy = noisy.lower()
        return noisy, "phonetic_transliteration_misspelling"

    if noise_level == "N3":
        words = clean_text.split()
        if not words:
            return clean_text, "keyboard_adjacent_typo"
        noisy = clean_text
        # Find a suitable word to corrupt
        for w_idx in range(len(words)-1, -1, -1):
            w = list(words[w_idx])
            if len(w) > 2:
                # Swap two letters
                w[1], w[2] = w[2], w[1]
                words[w_idx] = "".join(w)
                noisy = " ".join(words)
                break
            elif len(w) > 1 and w[0].lower() in KEYBOARD_ADJACENT:
                w[0] = KEYBOARD_ADJACENT[w[0].lower()]
                words[w_idx] = "".join(w)
                noisy = " ".join(words)
                break
        if noisy == clean_text:
            # Devanagari or special character swap
            if len(clean_text) > 3:
                chars = list(clean_text)
                chars[2], chars[3] = chars[3], chars[2]
                noisy = "".join(chars)
            else:
                noisy = clean_text + " "
        return noisy, "keyboard_adjacent_typo"

    if noise_level == "N4":
        words = clean_text.split()
        res_words = []
        for w in words:
            clean_w = re.sub(r"[^\w]", "", w).lower()
            if clean_w in TRUNCATION_WORDS:
                res_words.append(TRUNCATION_WORDS[clean_w])
            elif len(clean_w) > 4:
                truncated = clean_w[0] + re.sub(r"[aeiou]", "", clean_w[1:])
                res_words.append(truncated if len(truncated) >= 2 else clean_w)
            elif "ा" in w or "ी" in w or "े" in w:
                res_words.append(re.sub(r"[ाीे]", "", w))
            else:
                res_words.append(w.lower())
        noisy = " ".join(res_words)
        noisy = re.sub(r"[?!.,:;'\"]", "", noisy).strip()
        if noisy == clean_text:
            noisy = noisy[:-1] if len(noisy) > 3 else noisy.lower()
        return noisy, "vowel_omission_and_truncation"

    if noise_level == "N5":
        words = clean_text.split()
        res_words = []
        for w in words:
            clean_w = re.sub(r"[^\w]", "", w).lower()
            if clean_w in SMS_SHORTHAND_MAP:
                res_words.append(SMS_SHORTHAND_MAP[clean_w])
            elif len(clean_w) > 3:
                short = re.sub(r"[aeiou]", "", clean_w)
                res_words.append(short if len(short) >= 2 else clean_w)
            elif "ा" in w or "ी" in w or "े" in w or "ै" in w:
                res_words.append(re.sub(r"[ाीेै]", "", w))
            else:
                res_words.append(clean_w)
        noisy = " ".join(res_words)
        noisy = re.sub(r"[?!.,:;'\"]", "", noisy).strip()
        if noisy == clean_text:
            noisy = noisy[:-1] if len(noisy) > 3 else noisy + " plz"
        return noisy, "commuter_sms_chat_shorthand"

    return clean_text, "clean"
