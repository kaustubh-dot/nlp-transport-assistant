# Final source review

Primary-agent review of committed backend `3ed0c33` and final UI `597bf91`. This is not an independent whole-project signoff. Two independent agents authored/assessed the language cases; a third audited root causes and theme. Their usage allowance ended before a final independent source review, so the primary agent completed verification.

## Verified implementation behavior

- Original query reaches `classifier.predict(query)` unchanged. The optional API `transport_mode` field is a separate validated default, used before canonical resolution only when the question has no explicit mode. Omitted API fields preserve the legacy one-argument injected assistant/extractor calls. Invalid API values are rejected422 before inference.
- Explicit typed modes override selected defaults; multiple explicit modes clarify for single-mode intents. Multimodal and interchange operations do not manufacture a mode pair from one default. Source-preflight refusals retain existing behavior.
- Unicode letters/numbers/combining marks delimit complete words. `लोकल` cannot create `कल`; bus plural forms and explicit local/suburban rail phrases are recognized without generic train/rail mode guessing.
- Fare counts are bounded 1–30, consume compound number words whole, preserve original query, and never choose intent. Invalid, missing, negative or conflicting stage scopes cannot silently fall back to endpoint execution. Night class and explicitly unknown class do not silently become Ordinary.
- Possessive alphanumeric route codes require explicit bus/route context. Numbers for passengers, clocks and dates do not enter this branch. Existing numeric route cue grammar and complete suffix preservation remain covered.
- Explicit Hindi/Roman numeric day periods apply consistently to clock forms. Contradictory period/AM-PM and unqualified ambiguous clocks clarify. Spelled clock words remain unsupported.
- Negated selected-goal guard requests clarification; it does not select a replacement intent. Negative availability/membership propositions are not treated as excluded goal families. Stop-list/live independently requested goals clarify before partial execution.
- Generic nearest-target labels such as Bus Stop are removed from anchor spans. Known named station anchors are retained; remaining unqualified campus, locality and rail-mode source concerns are explicitly recorded, not silently credited as successful answers.
- Persistent mode choice is separate from translated widget identity. Language changes preserve choice/history; starters have stable keys. Published records uses a callback before rendering and opens/closes source coverage. The revision submit control uses the installed Streamlit 1.44 signature.
- Body/control/heading/numeric font roles share one palette/font configuration. Live review found a nested metric value overriding its parent's numeric font; the final CSS explicitly applies the numeric font to the rendered child. Radio targets remain native controls with keyboard/focus semantics; semantic alerts retain distinguishable colors and shared typography.

## Evidence and limits

All 1,344 tests pass on the closed source, including strict checkpoint inference, synthetic API/parser/integration/UI contracts and preservation checks. Actual 400-request final API replay has HTTP 200 for every case. Browser reply equality is a presentation test; it does not prove correct intent, scope, coordinates, current service, or current fare. Manual final semantic review remains authoritative for product quality and records 175 recognition failures and 3 cases needing source/anchor audit.

Concrete regressions discovered during replay were added before their fixes; RED logs remain alongside GREEN suite logs. Intermediate campaigns are preserved and clearly distinguished from final `verified` results. The selected model, six untouched NLP/domain/resolver modules, checkpoint, canonical DB, manifest, development data and historical report hashes remain unchanged. No training or research evaluator ran.

No claim of perfect multilingual understanding, comprehensive factual transit accuracy, independent final review, or updated historical research metrics is made.
