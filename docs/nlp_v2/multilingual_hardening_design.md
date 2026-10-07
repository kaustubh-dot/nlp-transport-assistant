# Phase 16 bounded multilingual extraction

Preserve raw classifier input, fixed MuRIL tokenization and all T3 labels. Extend
only deterministic extraction/resolution using canonical names, independently
created development v1 cases and allowed training shorthand. No held-out rows.

Register exact Hindi/mixed-script surfaces for Alwar Thirunagar, Poonamallee Bus
Terminus and Marina Beach. Resolve each surface through the exact current English
canonical name, retaining every duplicate node. Route context can disambiguate
only through existing mode-consistent operational links. These surfaces describe
names, not verified transport service facts. Unsupported names are never selected
by similarity.

Map bounded Hindi letter names after route digits (आर/जी/बी/सी/डी/ए/ई) to operational
Latin suffixes; unknown adjoining letters cannot silently truncate to a shorter
route. Support `bs` as bus shorthand, present in allowed training queries. Exact
`Deluxw` (development adjacent-key typo) means Deluxe, and `mnthly pass` is a bounded
vowel-omission ticket phrase. No global spelling correction, vowel restoration,
transliteration or semantic word replacement.

Near Latin service-class spellings are a refusal-to-guess guard: one edit from
ordinary/express/deluxe that is not an explicitly accepted alias requests
the service class. Multiple explicitly named classes likewise require a choice.
The guard never selects a fuzzy class or an entity. Separate extraction metadata
records actionable missing service input; canonical slot enums stay unchanged.
Night is excluded from similarity detection because right/light/eight are common
unrelated words; explicit night phrases keep their existing exact matching.

Existing case/punctuation normalization, Hindi clock parsing, mode separation,
unknown-name ambiguity and raw query inference receive synthetic regressions.
Frozen development v1 remains unchanged, including the documented v1-098 policy
divergence. Evaluate contracts by language/noise; no model tuning from this phase.

Spaced route suffixes use the same Unicode terminal as contiguous codes. Plausible
unsupported Hindi letter-name sequences/marks or mixed Latin-Hindi suffix tokens
must not fall back to a shorter numeric route; grammatical `के` and unrelated
words such as `आराम` retain the ordinary route code. This is bounded letter-name
recognition, not whole-query transliteration.

Common unrelated `deluge`, `delude` and `empress` words are excluded from the near-class
guard. The guard otherwise does not depend on immediate adjacency to bus/fare
words, so a misspelled modifier cannot silently become an Ordinary tariff.
Domain-owned `_fare_scope` is shared by execution and optional
`preflight_fare_class(slots)`: known ticket/mode/OD/stage-type refusals precede an
unknown-class question. Extended fare execution/handlers/maps bypass base scope
assumptions. Multiple requested modes still retain precedence.

Route extraction alone uses NFC to equate precomposed/decomposed Hindi letters.
Unicode letters/numbers/marks belong to a code token, while danda and other
punctuation end it. Spaced unsupported suffixes remain rejected through punctuation
and route symbols; supported hash suffixes remain intact. Model input stays raw.
