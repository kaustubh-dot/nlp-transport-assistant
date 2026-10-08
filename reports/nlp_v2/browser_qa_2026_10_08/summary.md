# Browser QA report — 2026-10-08

Extensive manual browser testing found no application crash in the exercised paths, and the input, response validation and failure recovery checks passed. **The product is not issue-free:** independently authored questions exposed answer-selection mismatches, an undisclosed campus anchor, Tamil glyph loss and accessibility gaps. Remaining phone checks and native CSV-download verification are incomplete because browser automation became unavailable. This report is observational QA, not a new model evaluation or a declaration that all sixteen operations pass.

## Scope and evidence

Tested source: `main @ bd9f148456778acb2a0562d8cfcb047783b5be57`. Final behavioral freeze remains `1bf748c9e4cc35e75b1db004f5b74c9dad1eeb1b`. Real UI/API were http://127.0.0.1:8601/ and http://127.0.0.1:8875/. Three independently tasked **GPT-6.1 Sol xhigh** subagents tested functional/multilingual behavior, input/scope preservation, and failure recovery in separate temporary hidden browser tabs. Primary tested keyboard, table controls, exports and layout. All browser interaction used `mcp__cua_repl`.

| Workstream | Query submissions | Other checks | Evidence |
|---|---:|---|---|
| Functional/multilingual, real backend | 32 | Nine overlapping UI/source checks | [functional.md](functional.md) |
| Input, clarification and timetable scope, real backend | 33 | Two empty-input no-ops and one reload | [input_scope.md](input_scope.md) |
| Primary keyboard, tables and layout, real backend | 6 | Table controls, exports, responsive observations | [layout_interaction.md](layout_interaction.md) |
| Isolated failure/recovery | 25 | Two lifecycle assertions | [failure_recovery.md](failure_recovery.md) |

**96 total query scenarios: 71 real-backend submissions and 25 isolated scenarios** (24 synthetic stub POSTs plus one disconnected-API submission). Counts describe manual coverage, not independent accuracy samples or a representative benchmark. Additional interaction checks overlap these submissions; they are not inflated into a total accuracy denominator. All sixteen intended T3 families were attempted by the functional agent. Live routes and median-frequency success panels were not reached; those panels were verified only with synthetic fixtures. Some other intended operations returned clarification or unavailable outcomes instead of executing, as detailed in the family coverage table.

## Findings requiring future work

1. **Answer-selection mismatches (material).** Several ordinary first/last, frequency, membership and unrelated-domain questions produced panels, clarifications or refusal reasons for another goal. Examples: “What is the first bus from Island ground Terminus on route 102?” rendered a nearest-stop panel; frequency variants produced departure/bounds panels or fare/stop clarification; an English membership query returned a stop list. Two unrelated questions did not reach outside-scope status, while primary's dessert question did. Browser evidence establishes the mismatch, but does not isolate every cause to model classification versus extraction/dispatch. Repeated route ambiguity also prevented successful live route-candidate coverage. See exact query/reply logs, not aggregate accuracy claims.
2. **Undisclosed location scope (material).** Generic “IIT Madras” returned distances computed from “IIT Madras, Thaiyur Campus” without displaying the campus. Two browser sessions reproduced this. Read-only canonical audit reproduced all five displayed distances from that campus; the main “Indian Institute of Technology - Madras” row has no coordinates. `entities.py` derives comma-prefix place aliases, `domain._nearest` returns the qualified `anchor_name`, and the frontend nearest panel omits it. This can silently answer for a different campus than the user intended. It does not establish external current transit facts.
3. **Tamil table glyphs (UI).** The canonical name “சென்னை விமான நிலையம்” and CSV contain valid Tamil Unicode, but the canvas table displays boxes in விமான. The source text is not literally corrupted into squares.
4. **Unnamed controls (low accessibility).** Chat send lacks an accessible name; table search becomes unnamed after typing. Keyboard send works and has visible container focus, so a missing focus ring is not a finding. A full screen-reader audit was not performed.

These findings are documented separately under the user's bounded Phase23 governance: no aliases, classifier, model, data, frontend or domain behavior were changed. No new development phase was started. Historical independent-review results remain historical; they do not erase issues observed by this broader manual QA.

## Verified behavior

- Real sourced stop sequence, membership, first/last bounds, departures, fares and nearest panels rendered. Sources, fare effective dates, GTFS service-day, partial coverage, geometric distance and provisional warnings were retained where applicable.
- Enter, starter activation, keyboard send, full-question revision and history ordering worked. Duplicate Enter produced a single pair; empty/whitespace input produced no request. Table search, column hide/restore and fullscreen worked.
- English, Devanagari, Roman Hindi, Hinglish, mixed-script, punctuation, multiline and RTL inputs were exercised. Numeric Hindi fares worked; spelled ordinals remained a documented limitation. Replies remained English.
- HTML/script input stayed literal, with no injected script/image DOM or dialog. Browser-serialized request bodies accepted the tested 8192-byte boundary and rejected 8193 bytes; non-ASCII escaped JSON limits were tested separately. This is not a raw-unescaped API byte test.
- Known/unknown third stops clarified, and trailing waypoint timetable requests explicitly refused unsupported filtering, including Hindi/Hinglish. No successful panel silently dropping those constraints was observed. Guarded UI replies do not expose an operation ID, so all three timetable operations are not inferred solely from the intended wording.
- Isolated unchanged frontend safely handled offline API, HTTP 503, invalid JSON, malformed containers/amount/status, null optional values, absent panel data and malformed optional coverage. All five visible statuses and synthetic policy/facility/accessibility/interchange/frequency/routes panels were checked. Fixture sources are explicitly synthetic, not evidence of real transport capability.
- One 22-second fixture exceeded the configured 20-second client timeout and produced a safe error; the next valid request recovered. Exact elapsed timeout latency was not independently measured. Loading spinner was observed in that isolated slow case, not in fast live requests.
- No warning/error console entries were captured during the agents' completed cases; the isolated server shutdown later produced an expected WebSocket disconnect warning. No traceback was observed. No load/stress, screen-reader, external operator-data or real-device test was performed.

## Export location

All exports and evidence are inside this repository directory. The three UTF-8 CSVs each contain five data rows from the actual browser-rendered accessible table:

- [nearest_marina_beach.csv](exports/nearest_marina_beach.csv)
- [published_departures.csv](exports/published_departures.csv)
- [nearest_iit_madras.csv](exports/nearest_iit_madras.csv)

[Export manifest](exports/manifest.json) records queries, columns, row counts and extraction method. Native browser download remains unverified after a tool timeout; these CSVs are saved DOM-table exports, not asserted native download artifacts. They retain snapshot values, including the observed Thaiyur anchor issue, and are not current travel advice.

## Incomplete checks and cleanup

Responsive overrides at desktop/tablet sizes were observed. At 768×1024 CSS size, body/document widths were 768, but the open sidebar was an overlay. Native screenshots were partial/scaled and cannot certify full-height tablet layout. Before closing the drawer or starting phone-width checks, the browser connection disappeared: inventory was empty and both rebind and fresh-tab creation failed. Phone layout, mobile queries, virtual keyboard, drawer controls and primary's final viewport/tab cleanup are **unverified**. Last requested viewport was 768×1024; reset after disconnection is not asserted. The agents closed their tabs; user tabs were not deliberately closed. Real-service health and repository integrity are recorded in verification.json.

No evaluator, development evaluator, model-only evaluation, training or held-out item inspection was invoked. Production source, checkpoint, canonical DB, frozen development suite, research boundaries and both historical evaluation directories remain unchanged. No aggregate measurement matches the final behavioral freeze; this QA does not replace historical measurements. This addition contains reports, screenshots and exports only. The earlier 878-test result belongs to the historical source verification; this evidence-only addition does not claim a fresh full-suite run.

![Nearest table: hidden campus scope and Tamil glyph loss](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/functional_nearest.jpg)
