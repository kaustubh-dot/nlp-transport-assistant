# Independent language root-cause audit — 2026-10-08

Source inspected: `main` at `3336e0d4ed0f84ddc706bf14cbf1aaa1e5c33a4c`. This is a read-only engineering audit for the fresh 400-query product QA task, not a model evaluation, claim of representative accuracy, implementation, or permission to reopen historical research.

## Boundaries and evidence

Read the authoritative language specification, production source, current known limitations, published 96-query language QA summary, entity-resolution contract, and the original and Phase23 user instructions in the supplied attachments. No applicable `AGENTS.md` was found in the repository or its ancestry.

The original request preserves the 16 T3 classes, selected checkpoint, raw-query inference, benchmark integrity, and conservative source-backed answers. It permits independently created development cases and deterministic improvements without fuzzy entity guesses. The later Phase23 exception was strictly scoped historically and does not itself authorize general model/alias changes. This audit changes only this report. No individual frozen, development-v1, stress, validation, reference, or held-out examples were inspected; no training, research evaluator, API call, or model inference was run.

Evidence below comes from source tracing plus fresh, independently authored direct parser probes. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python` imported the production helper/extractor functions and opened the canonical DB through its read-only resolver. An explicitly supplied intent isolates extraction; this is **not evidence that the actual model selects that intent**. Prior real-model observations are attributed only to the published language QA summary. Root's 400-query real-API run is needed for current end-to-end attribution.

## 1. Confirmed Unicode boundary defect affects days, modes, enums and guards

**High correctness risk.** `src/nlp_v2/slots.py:84-85` implements phrase boundaries using Python `(?<!\w)` / `(?!\w)`. Python's `\w` includes letters and numbers but excludes combining marks. Devanagari vowel signs and virama are integral parts of words. For example, `ो` is Unicode category `Mc`, and `े` / `्` are `Mn`; all three fail a Python `\w` test.

Consequently a word-internal position adjacent to a vowel sign can be mistaken for a token boundary. This is not a Hindi-day ambiguity or missing timetable source:

| Fresh direct probe | Actual result | Required distinction |
|---|---|---|
| `_has('लोकल', 'कल')` | `True` | Local train does not mean yesterday/tomorrow |
| `_has('local', 'kal')` | `False` | Latin control does not create a day |
| `_has('कल', 'कल')` | `True` | A real whole day marker remains recognized |
| `_has('कलाकार', 'कल')` | `True` | Artist does not express a day |
| `_has('महाकाली', 'काल')` | `True` | A proper-name substring is not an independent token |
| `_has('पासिंग', 'पास')` | `True` | Passing is not a transit pass |

With fixed intent `first_and_last_service`, `Guindy se local train ki pehli service kab hai?` extracts `suburban_rail`, `first`, `RAIL_GUINDY`, and no temporal ambiguity. Its independently authored Hindi contrast, `Guindy से लोकल ट्रेन की पहली सेवा कब है?`, extracts those same values **plus** `temporal_relative='कल'` and `clarification_reason='temporal_ambiguity'`. The faulty match enters at `slots.py:441-444`; the resulting clarification is selected at `slots.py:516-517`, `assistant.py:260-270`, and independently protected at `dispatch.py:84-86`.

The same defect reaches mode extraction through `slots.py:13-18,362-375`: `बसंत नगर से Guindy कैसे जाएँ` spuriously requests `bus`, even though the Hindi proper-name text contains no independently requested bus mode. This changes entity filtering, not just wording.

Other affected lexical boundary sites include enum recognition (`slots.py:88-92`), timing type (`388-392`), line selection (`394-397`), multiple-scope detection (`67,290-334`), waypoint/endpoint markers (`455-509`), unsupported temporal operators (`518-521`), and assistant goal/conjunction matching (`assistant.py:21-60`). Fixing only the relative-day loop leaves the shared defect elsewhere.

**General repair design:** centralize lexical span boundaries, treating adjacent Unicode categories `L`, `N`, `M` and underscore as word continuation. This can be implemented by matching candidate spans and checking adjacent characters with `unicodedata.category`, without a new keyword intent router. Reuse it for enums, modes, relative days, goal cues, operators and role markers while keeping raw model input unchanged. Do not classify the entire Devanagari Unicode block as a word: danda punctuation must remain a separator. Regress punctuation, mixed script, NFC/decomposed marks, start/end positions, genuine `कल`, substring negatives and Latin controls.

A stricter boundary also stops currently accepted root matches inside inflected forms: `_has('टिकटों','टिकट')` currently returns `True`. Inflected language coverage must be handled deliberately by documented complete forms or grammatical extraction, not retained accidentally through broken Unicode boundaries. This tradeoff requires explicit regression coverage.

## 2. Confirmed route-label grammar gap; Unicode decimal conversion works

`slots.py:194-242` already converts Unicode decimal digits to ASCII (`198-199`) and preserves bounded operational suffixes. The prior Hindi route102 symptom is therefore not proof that Devanagari numerals are unsupported. The label-word grammar at `214-215` accepts `no`, `number`, `नंबर`; it does not accept `संख्या`. The explicit-constraint detector at `337-343` has the same omission.

| Fresh direct probe | `_route_number` |
|---|---|
| `बस १०२ के स्टॉप दिखाओ` | `102` |
| `बस नंबर १०२ के स्टॉप दिखाओ` | `102` |
| `बस संख्या १०२ के स्टॉप दिखाओ` | `None` |
| `route number 102 stops` | `102` |
| `102 number bus stops` | `None` |
| `बस १०२ ए के स्टॉप दिखाओ` | `102A` |
| `बस १०२ एफ के स्टॉप दिखाओ` | `None`, preserving the unsupported suffix boundary |

For route-stop intents this produces an unnecessary missing-route question (`contracts.py:149-150`). For journey/timetable intents, both a missed code and missed explicit-constraint marker can omit an explicitly supplied route rather than ask for it (`slots.py:379-386`), potentially allowing a broader route answer. This is the material invariant, beyond one spelling example.

**General repair design:** one shared, mark-safe route grammar for route introducers, optional number labels before/after the number, Unicode decimal normalization and complete suffix boundaries. Both successful extraction and the unsupported-explicit-constraint detector must recognize the same grammar. Cover Hindi/English/Roman forms, clocks and dates that must not become routes, suffix hashes/hyphens, unknown suffixes, and coordinated codes. Keep suffix refusal conservative; do not turn an unsupported route into its base integer. This is deterministic route-slot parsing and does not alter intent selection or canonical aliases.

## 3. Confirmed spelled-number gap can silently lose a time constraint

`_time` in `slots.py:245-284` parses numeric 12-hour/24-hour and numeric Hindi/Roman colloquial clocks. It does not parse number words. The invalid-time detector at `431-432` also recognizes only numeric-looking expressions. Thus an unsupported but clear word clock is omitted rather than preserved as an unresolved constraint.

| Fresh direct probe | `_time` |
|---|---|
| `सुबह ९ बजे` | `09:00:00` |
| `सुबह नौ बजे` | `None` |
| `०९:००` / `09:00` | `09:00:00` |
| `रात ८ बजे` | `20:00:00` |
| `रात आठ बजे` | `None` |
| `8 बजे` / `8 baje` | Both `08:00:00` and `20:00:00`; correct ambiguity |

There are two separate causes behind a departure request receiving service bounds: the retained classifier may select `first_and_last_service`, and extraction may lose its explicit clock. `domain.py:388-392` **already refuses** first/last with a parsed `time`. It would refuse a literal `09:00` clock that survives extraction. Therefore the QA summary's after09:00 observation cannot be fully attributed to a missing first/last guard from source alone; exact current query/response tracing is needed. Number-word omission is a confirmed route to answering unrestricted bounds when the model is wrong and the clock is dropped.

Fare stages have the analogous bounded grammar gap at `slots.py:420-422`: `साधारण बस स्टेज ५ का किराया` extracts stage5, whereas `साधारण बस पाँचवें स्टेज का किराया` does not. `ordinary bus stage 5 fare` works; `ordinary bus stage five fare` omits the stage. A correct missing-stage response is safer than invented fare arithmetic, but asking for an already supplied stage is incomplete recognition.

**General repair design:** introduce a bounded typed numeral/ordinal parser scoped to explicit time/stage expressions, separate from model preprocessing. Preserve zero-default time ambiguity. Even when number words cannot be normalized safely, retain unresolved explicit clock/stage evidence and clarify/refuse instead of running with the constraint absent. Do not globally replace number words in station names, code, recipes or unrelated prose. Parsing an after-time does not authorize changing the model's selected operation; first/last must continue refusing incompatible clock constraints.

The language spec also describes tense-supported resolution of `kal/कल`. Current extraction never uses tense; genuine `kal/कल` always clarifies without an explicit date (`slots.py:441-444,516-517`; `domain.py:362-364`). This is safe but less complete than the spec. Any later grammatical resolution must require unambiguous aspect/tense in the relevant clause; a bare future/past word somewhere in the query is insufficient.

## 4. Additional confirmed lexical-role and polarity limitations

`_endpoints` at `slots.py:113-120` recognizes `from|से|se` before a location without a leading word boundary. Fresh `Guindy to Koyambedu route` keeps Guindy as origin; `Guindy please Koyambedu route` moves Guindy to destination because the end of `please` is interpreted as `se`. Koyambedu remains independently ambiguous in these probes; the observed role switch is still directly attributable to the parser. `_endpoints` and the single-endpoint rule at `478` need the same whole-token role matching as the Unicode repair.

Mode extraction has no polarity representation. `Guindy to Koyambedu metro chahiye` and `Guindy to Koyambedu metro nahi chahiye` both extract `transport_mode='metro'` and filter Guindy to `METRO_GUINDY`. The Hindi `मेट्रो चाहिए` / `मेट्रो नहीं चाहिए` pair likewise produces the same positive mode. This can silently invert an explicit constraint if the remaining inputs become executable.

**General repair design:** lexical boundaries are appropriate for source markers. Negated execution constraints require separate span/polarity handling or a bounded clarification/unsupported guard; they cannot be solved by changing token boundaries. A generic “contains nahi/not” rule would also block legitimate negative questions and quoted text. Do not reinterpret a negated mode as a guessed alternate mode or override model intent.

## 5. Exact entity coverage is intentionally limited and contains target-name drift

`entities.py:64-90` indexes canonical stop/hub/place names and recorded aliases. `123-143` matches only longest exact normalized whitespace-token spans. There is no broad transliteration, typo correction or morphological name parser. Only a small Roman alias map and three explicit Hindi/mixed canonical-name mappings appear at `13-20`.

Legacy surface aliases are reused only if their English target appears exactly in the current index (`entities.py:106-113`). A read-only canonical-name probe found no exact `Chennai Airport` target, but did find `Chennai International Airport`, `Airport Metro` and `Chennai Airport Metro`. Consequently `airport`, `chennai airport`, and `एयरपोर्ट` each have zero indexed candidates, although the legacy gazetteer lists them under `Chennai Airport` (`src/entity_extractor.py:37-43`). `chennai international airport` has four candidates. Similarly, `सेंट्रल` / `चेन्नई सेंट्रल` have candidates, while `सेन्ट्रल` / `चेन्नई सेन्ट्रल` do not. The latter spelling even appears in the public language spec's example; it was not taken from a protected example.

This separates missing aliases from legitimate identity ambiguity. The resolver preserves duplicate physical nodes (`entities.py:145-174`); the current Central hubs have different mode/member records according to the published earlier diagnosis. Similar names do not justify merging them or selecting one.

**Needed larger data work:** vetted, versioned multilingual names/alias coverage tied to canonical identity and verified hub/mode metadata, plus useful candidate descriptions in clarification. Resolve legacy-to-current target mappings deliberately; report orphaned alias targets. Do not add a list of QA-specific spellings, fuzzy guesses, or unverified node merges. No alias changes are proposed for the current frozen baseline.

## 6. Wrong intent families originate in the frozen model path

The retained classifier receives the raw query (`assistant.py:189`; `model.py:44-45,91-94`) and emits exactly one argmax label with confidence (`model.py:95-100`). It does not emit semantic ambiguity, low-confidence abstention, or multiple acceptable labels. `assistant.py:203-216` extracts only for that predicted intent. `dispatch.py:9-25,63-64` maps each label directly to its frozen operation.

Thus the published Hinglish frequency→fare, delay→bounds, and Java→ticket-policy failures are not caused by slot extraction choosing a competing operation. A label change must originate in model inference. A source-unavailable response after a wrong label does not prove that the user's actual goal was understood or refused correctly. No current full query was replayed by this auditor.

There are additional architectural limits: model input truncates at64 tokenizer tokens (`model.py:73,91-94`), and the lexical multiple-goal guard has a bounded vocabulary and conjunction grammar (`assistant.py:21-60`). Fresh `Guindy se bus route aur fare batao` is guarded; `Guindy से मार्ग और किराया बताओ` and `Guindy से रूट और किराया बताओ` are not. The guard returns clarification and never selects a different operation. Expanding such a guard must not become a substitute classifier.

**Needed larger model work:** independently authored, family-disjoint language/noise/multiple-goal/out-of-scope training and validation coverage; a new reproducible proposal for T3 training or ambiguity calibration; selection only on allowed validation; separate new artifacts; and a source/manifest freeze before any authorized descriptive evaluation. This audit does not justify automatic retraining or threshold tuning. “Perfect on arbitrary Hindi/Hinglish” cannot be made credible while weights, raw preprocessing,64-token context and single-label policy remain immutable. A frequency keyword router or hand-coded recipes/programming rejection added to rescue QA items would violate the intended architecture.

## 7. Source-unavailable answers remain legitimate limitations

Current refusal paths are explicit: ticket/pass policy, station facilities and confirmed multimodal graph (`domain.py:114-125`); confirmed interchange/accessibility coverage checks (`126-142`); mode-consistent topology/schedule preflight (`87-112`); unsupported timed route/availability requests (`237-240,456-460`); live status (`dispatch.py:81-82`, `domain.py:603-604`). First/last bounds, directional frequency and at/after departures are separate bounded handlers (`domain.py:388-454`).

The documented snapshot lacks confirmed interchange/transfer evidence, verified facilities/accessibility values, authoritative pass policy and telemetry; mode-consistent metro topology/timetables are unusable. These cannot be repaired by parser correctness, a better language selector, a larger query set or a higher `ok` count. They require verified source ingestion and, where applicable, authorized external integrations. Retain source dates, provisional caveats and explicit unavailable states.

## Recommended disposition after the 400-query run

Keep classifier failures, lost execution constraints, missing exact names, real entity/time ambiguity, unsupported source and transient errors separate. Correlate each fresh failure with the actual model label, extracted slots and outcome rather than treating status alone as success. A direct parser probe with an injected intended intent diagnoses the downstream layer and must not be counted as real-model correctness.

The most concrete general correctness candidates are shared Unicode lexical boundaries, whole-token endpoint markers, consistent route-label grammar, and preservation of unparsed explicit time/stage constraints. Polarity and general semantic understanding need a separately reviewed scope. Model/alias/source coverage expansion is larger work, not a promise of perfect functionality from400 examples. Preserve the fresh QA as an observed development diagnostic; any later fixes must use independent contract regressions and disclose that the400 cases have been observed.

## Mode-selector design review requested during the audit

The user's additional mode-selector request can be implemented as an optional request context with a strict canonical enum, leaving `classifier.predict(query)` and raw query text untouched. Current API forwarding is `app/api.py:73-76`; frontend POST construction is `app/frontend_contract.py:21`. The default must enter extraction before entity resolution (`slots.py:362-377,446-451`), because applying it after resolution cannot safely recover the physical candidates lost to ambiguity or prior filtering.

Only absent explicitly requested target modes should inherit the context default. Do not add the default to explicit mode mentions and accidentally create an extra multiple-mode clarification, collapse explicit multimodal requests, or invent `mode_from`/`mode_to` from a default. Existing nearest-query logic deliberately excludes mode words inside the anchor name (`slots.py:367-369`); maintain that behavior. A mode written as part of a station name and an independently requested target mode are different roles.

The API's canonical values are `bus`, `metro`, `suburban_rail`, `mrts`, `any` (`contracts.py:26`); generic `rail` does not exist. A UI label “Rail” must disclose any intended suburban-only meaning or preserve the difference between suburban and MRTS, rather than silently promising a union the slot contract cannot express. Negation remains a separate language limitation: both positive and negated textual modes are currently detected as positive; default fallback must not conceal that limitation by choosing another mode.

Recommended independent contract regressions before implementation:

- Omitted mode retains existing assistant/API behavior and compatibility with injected test services; raw classifier input stays byte-for-byte identical for each default.
- Generic request inherits each valid mode; explicit metro overrides a bus default and explicit MRTS overrides a suburban default.
- Two explicit modes retain the existing multimodal/clarification/transfer behavior without introducing a third default.
- “Nearest bus stop near Guindy Metro” requests bus; “nearest stop near Guindy Metro” may use context default without treating the anchor name as a target-mode override.
- Default mode participates in canonical resolution and mode-consistent preflight; an explicit known incompatible entity remains an execution constraint and is never substituted.
- Invalid strings, lists, objects, numbers and booleans receive a clear client validation error; define the handling of explicit null/any consistently with optional omission.
- Mode switching itself sends no API request, preserves current drafts/history, and applies only to the next submission; saved replies retain the request's submitted mode context.
- A negative explicit mode, quoted mode word and code/recipe request do not acquire a fabricated positive transit answer merely because a default is set. These cases may continue exposing a classifier/semantic limitation; tests must not encode a keyword intent override as the solution.

No API/frontend/production files were changed by this auditor. This section is design feedback, separate from the400 baseline observations.
