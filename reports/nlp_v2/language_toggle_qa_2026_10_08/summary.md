# Language selector and Hindi/Hinglish product QA — 2026-10-08

The website now has an exclusive **English / हिंदी / Hinglish** selector using the restored parchment/oxblood style. It changes main website text, known explanations, panel labels and saved replies. Questions reach the API exactly as typed; the selected display language does not change understanding or restrict input language. Unknown explanations remain verbatim behind a localized label. Canonical names, route codes, money, service-day times, dates and source IDs remain unchanged. Some built-in Streamlit controls remain English.

**Frontend checks pass; Hindi/Hinglish understanding remains incomplete.** This extension does not claim to fix the model or make every question answerable.

## Actual language testing

Two agents independently authored 48 Hindi and 48 Hinglish questions: two per16 intended intent families, followed by16 missing-input, name/time ambiguity, number, noise, multiple-goal, waypoint and unrelated-topic contrasts per language. The actual model/API was exercised sequentially at localhost8875. The primary then replayed all96 unique cases through the actual website at localhost8601 using native browser accessibility actions. Each final record contains the preserved question and rendered localized response. All96 displayed explanations match the recorded API response after AX whitespace normalization; clock text can be split by inline formatting. This means presentation agrees with the API, not that the answer fulfills the question.

|Manual product category|Hindi|Hinglish|
|---|---:|---:|
|Recognition/input/goal issue|22|10|
|Matched family but source unsupported|10|13|
|Legitimate ambiguity|7|11|
|Successful bounded goal|6|6|
|Conservative guard/refusal|3|8|

Hindi's22 issue judgments include wrong family, missed extraction, unexpected scope guards and dropped goals. Hinglish's10 mismatches identify wrong-family selections; the agents' category boundaries differ. These counts are manually scoped observations, **not accuracy estimates**, independent held-out metrics or32 proven classifier bugs. Hindi statuses:25clarification,14unavailable,8OK,1out of scope. Hinglish:23clarification,18unavailable,6OK,1error. Two Hindi OK replies still miss an explicitly asked goal.

Examples requiring follow-up:

- Hindi H05: `बस संख्या १०२ किन-किन स्टॉप पर जाती है, क्रम में नाम बताइए।` asks for route102 but receives a missing-route prompt.
- Hindi H13: a request for departures after09:00 selects first/last bounds and answers that different goal. Spelled ordinal stages and several Hindi proper-name forms also miss supplied inputs.
- Hinglish H12: `102 bus ki frequency Island ground Terminus par kitni hai?` selects fare calculation.
- Hinglish H30: `Aaj Central se Tambaram train kitni delay hai?` selects service bounds; H32's Java programming request selects ticket/pass policy.
- The user's `guindy se central kaise jau` selects the correct route family and recognizes Guindy, then clarifies Central's multiple distinct canonical candidates. The [earlier diagnosis](../hinglish_diagnosis_2026_10_08.md) explains why blindly merging those records is unjustified.

Source-unavailable facilities/transfers/passes and genuine entity/time ambiguity are reported separately from recognition failures. Intended waypoint wording does not establish every waypoint-guard path when the model chose another operation. No backend/model/alias/database repair was made from these fresh examples.

## UI and review checks

- All six Hindi/Hinglish starter buttons were actually activated in the browser; each sent its authored question and produced the intended bounded nearest/stops/fare response. Separate API starter requests are also recorded.
- Final native phone interactions verify genuinely unsubmitted revision/composer drafts across Hinglish→English→Hindi, unchanged chat-pair count during language switches, exact revised submission, retained composer draft, then a Hindi question with Hindi INR17/date/source/caveat display. Source and AppTest checks establish no API resubmission on language-only reruns.
- Real language-switch draft loss was reproduced and corrected using stable labels/placeholders and a revision key per clarification turn. New and identical repeated questions reset the revision default. Early stale field values during streamed rendering are not counted as a persistent bug; final readiness checks wait for current question and reply text.
- Independent review reproduced two accepted-payload localization crashes: literal braces and non-string route modes. Both are fixed with verbatim fallback and meaningful red/green regressions. Final independent source/presentation review passes112 targeted variants across26 groups with no additional actionable finding.
- Default desktop, requested390×844 and360×800 phone overrides, and768×1024 tablet were inspected. Buttons wrap to two rows on phones; Hindi/Hinglish text, focus styles, table headings, dated fare/source caveats and canonical Tamil names were visually checked. The compact stable hint fits one line at360px. Sidebar reopening works after resetting the viewport.
- Screenshots are native captures, scaled by the in-app browser: actual dimensions are recorded in [verification.json](verification.json). They prove the visible region, not full-page pixel geometry. `phone-390-english.jpg` is an initial incomplete resize frame; `phone-390-ready.jpg`, `phone-390-hindi.jpg`, `phone-360-final.jpg` and the tablet image are settled captures.

Native click and focused-key input worked after selector preparation failed; Playwright DOM inspection timed out, so no browser console inspection or new download verification is claimed. Agent browser inventories were unavailable, so both language agents owned real API QA while the primary owned browser coverage. Diagnostic repeats and early snapshots are preserved but excluded from the96 unique final-case denominator.

## Verification and provenance

Fresh final full suite: **1,147 passed in33.17s**; focused language/frontend suite:306 passed. Compilation, dependency check and diff check pass. Automated tests validate contracts and regressions, not representative language accuracy. [Independent review](hindi/independent_review.md) and [full test output](full_pytest.txt) are preserved.

Frontend behavior is committed at `57bb69b7f1f7b9cb4b1e99c8564842ddc5c8f457`. API QA baseline HEAD was `490ba62b65f7bd3b223f66eaa1ac3c6335800006`; backend freeze remains `1bf748c9e4cc35e75b1db004f5b74c9dad1eeb1b`. Eighteen original recorded source hashes, checkpoint, canonical DB, manifest, development suite and10 historical report/context hashes remain unchanged. Only the two original UI source files changed, plus the new presentation module/tests and documentation/QA exports. No standalone evaluator or production training campaign, or individual protected-item inspection, ran. The unit suite retains its synthetic evaluator/trainer guard and smoke tests. Both frozen descriptive evaluations retain their original sources and meaning; there is no matching new final-backend aggregate evaluation. The compact hint was shortened after the96-case replay; final source hashes, five native interaction checks and fresh tests cover that final adjustment.

## Exports and screenshots

- [Hindi cases and actual JSON](hindi/baseline.csv), [Hinglish cases and actual JSON](hinglish/api_baseline.csv).
- [96 browser exchanges CSV](primary/browser_cases.csv) and [JSON](primary/browser_cases.json); [six starter activations](primary/starter_browser.json); [five final interactions](primary/final_interactions.json).
- [Hindi desktop](primary/final-hindi-desktop.jpg), [Hindi fare/date/source](primary/hindi-fare.jpg), [Hindi expanded stop table](primary/hindi-stops-expanded.jpg), [Hinglish nearest/source limits](primary/hinglish-nearest.jpg), [390px Hindi](primary/phone-390-hindi.jpg), [final360px Hinglish](primary/phone-360-final.jpg), [768px Hinglish](primary/tablet-768-hinglish.jpg).

All exports are inside the repository. CSV line endings were normalized to LF without changing parsed UTF-8 cells. Temporary owned browser tabs are closed and the viewport override reset; API/UI remain available locally.
