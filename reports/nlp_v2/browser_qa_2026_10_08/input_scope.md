# Browser QA: input boundaries, clarification and scope preservation

Date: 2026-10-08. Repository HEAD verified as bd9f148. UI: http://127.0.0.1:8601/; backend address supplied by coordinator: http://127.0.0.1:8875/. Independent hidden in-app browser tab, default 1280 × 720 viewport.

36 recorded cases: 33 actual query submissions, two empty/whitespace no-op checks, and one reload/session check. First session produced 50 chat messages (25 pairs), then reload cleared them; second session produced 16 messages (eight pairs). Two Enter presses in S21 produced only one submitted question. Extra ordinary controls and two Hindi/Hinglish waypoint cases were added at the coordinator's request.

All inputs are independently written synthetic examples. No evaluator, training, held-out/development rows, production model, aliases, canonical data, research or evaluation directories were used or changed. Browser interaction used cua_repl only. Source inspection was limited to app/api.py, app/streamlit_app.py, app/frontend_contract.py and assistant/slot/contracts implementation. This is a browser behavior assessment, not gold-intent accuracy evidence.

## Findings

No material UI contract defect was found in the exercised paths. Error, clarification, and unavailable replies showed their appropriate visible status captions without a success heading, metric, dataframe or route-stop expander within that reply. Existing successful panels remained in earlier history as expected. Each accepted nonempty submission added one user message followed by one assistant message, preserving order. Both revised-full-question submission paths worked, removed the form after a successful answer, and preserved earlier exchanges. The chat input stayed usable after errors/refusals.

S29, S30, S32 and S33 are classifier-capability mismatches for the independently authored ordinary controls. S32 asked for a first bus but showed the specific “Nearest by straight line” panel (FIND_NEAREST_STATION, confirmed from the frontend operation-to-panel mapping). S33 asked for frequency but showed “Published departures” (GET_SCHEDULED_DEPARTURES). S29 mentioned interchange records and S30 asked for a stop to check; those indicate a likely different classifier selection, but the browser does not expose the operation ID in these non-success replies. Do not count them as successful first/last or frequency operation coverage. No successful service-bounds or median-interval panel was observed. S34 provided positive scheduled-departure panel coverage after 09:00. These mismatches do not establish any aggregate model accuracy measure.

Known/unknown coordinated third-location requests S22–S24 all produced one-scope clarification. Known/unknown trailing waypoint requests S25–S27, Hindi postfix S35 and Hinglish postfix S36 all produced “Waypoint-filtered timetable requests are unsupported…” with no successful panel. Those queries were intended to exercise first/last, frequency and scheduled-departure wording; the machine operation is unexposed for these guarded replies, so specific operation selection is not claimed from intent wording alone.

S13 combined an invalid date/time with ambiguous Guindy, and the visible result asked to resolve the location first. S14 removed that ambiguous name and produced the temporal clarification. This distinction is preserved in the case record.

HTML/script text S07 stayed literal: the user message contained zero script and zero img DOM elements, and no JavaScript dialog appeared. Unicode Hindi numerals, a multiline question, and RTL/mixed-script text all rendered safely and returned route-stop panels. Long inputs caused no horizontal document overflow (body/document scroll width 1280 at viewport 1280).

## Boundary and timing evidence

The API source sets MAX_REQUEST_BYTES=8192, measured on the UTF-8 encoded JSON body. The frontend uses requests.post(json={query: query}), whose standard serialization adds 13 bytes around the query and escapes non-ASCII characters. Local json serialization verified these lengths; all four requests were still submitted through the real browser. S17 at 8192 bytes reached normal clarification; S18 at 8193 bytes returned “Query body is too large.” S19's Unicode input serialized to 8191 bytes and reached normal clarification; S20 serialized to 8197 bytes and returned the same safe body-limit error. These are Unicode UI serialization boundaries, not a direct raw-unescaped UTF-8 API transport test.

Measured browser action-to-result observations ranged from 161 to 532 ms; they include automation overhead and are not backend latency measurements. S03 completed but its initial snapshot arrived before the reply, so no reliable timing is claimed. The “Checking the transit snapshot…” spinner did not appear in the immediate captured snapshots, and no lingering spinner was observed after completion. S21's two consecutive Enter presses settled at exactly one pair, also verified in a subsequent observation. The short responses did not provide evidence for mid-request disabled-control behavior or spinner appearance; those details remain unverified rather than being scored as failures.

Console check at the end returned zero warning/error log entries.

## Case index

| ID | Type | Visible status | Success panel in that reply | Observed ms |
| --- | --- | --- | --- | ---: |
| S01 | no-op | no-op | none | — |
| S02 | no-op | no-op | none | — |
| S03 | submission | Request could not be completed | none | — |
| S04 | submission | Published information | Route stops | 259 |
| S05 | submission | Published information | Route stops | 251 |
| S06 | submission | Published information | Route stops | 282 |
| S07 | submission | Published information | Route stops | 252 |
| S08 | submission | More information needed | none | 279 |
| S09 | submission | Published information | Published fare metric | 338 |
| S10 | submission | More information needed | none | 280 |
| S11 | submission | Published information | Nearest by straight line | 324 |
| S12 | submission | More information needed | none | 294 |
| S13 | submission | More information needed | none | 201 |
| S14 | submission | More information needed | none | 284 |
| S15 | submission | More information needed | none | 277 |
| S16 | submission | More information needed | none | 289 |
| S17 | submission | More information needed | none | 294 |
| S18 | submission | Request could not be completed | none | 341 |
| S19 | submission | More information needed | none | 294 |
| S20 | submission | Request could not be completed | none | 206 |
| S21 | submission | Published information | Published fare metric | 362 |
| S22 | submission | More information needed | none | 359 |
| S23 | submission | More information needed | none | 468 |
| S24 | submission | More information needed | none | 532 |
| S25 | submission | Information unavailable | none | 310 |
| S26 | submission | Information unavailable | none | 296 |
| S27 | submission | Information unavailable | none | 328 |
| S28 | session check | session check | none | — |
| S29 | submission | Information unavailable | none | 257 |
| S30 | submission | More information needed | none | 161 |
| S31 | submission | More information needed | none | 255 |
| S32 | submission | Published information | Nearest by straight line | 170 |
| S33 | submission | Published information | Published departures | 267 |
| S34 | submission | Published information | Published departures | 282 |
| S35 | submission | Information unavailable | none | 282 |
| S36 | submission | Information unavailable | none | 267 |

## Screenshots

![Unicode body-limit safe error](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/scope_unicode_body_limit.jpg)

![English timetable waypoint refusal](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/scope_timetable_waypoint.jpg)

![Hinglish waypoint refusal](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/scope_hinglish_waypoint.jpg)

![First-bus wording selected nearest panel](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/scope_classifier_panel.jpg)

## Exact case records

Successful table cell canvases are not duplicated in these DOM text records; panel headings and available text, metrics, captions, warnings and visible responses are captured. The classifier-panel screenshot includes nearest-table cells.

### S01

Input: ""

Action: no-op.

Visible result:

```text
No message or request panel; initial screen unchanged
```

### S02

Input: " \t \n "

Action: no-op.

Visible result:

```text
No chat messages; initial screen unchanged
```

### S03

Input: "?!...{}[]<> 😶"

Action: submission. One user/reply pair; chat messages 0 → 2.

Visible result:

```text
Request could not be completed

Please enter a transport question.
```

### S04

Input: "List stops on bus route 102\nplease."

Action: Enter. One user/reply pair; chat messages 2 → 4.

Visible result:

```text
Published information

102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.

Route stops

102 · published sequence 1

Partial published coverage: some links or route variants cannot be verified.

Omitted: 0 unusable links and 1 route variant(s).

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S05

Input: "बस रूट १०२ के सभी स्टॉप बताओ।"

Action: Enter. One user/reply pair; chat messages 4 → 6.

Visible result:

```text
Published information

102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.

Route stops

102 · published sequence 1

Partial published coverage: some links or route variants cannot be verified.

Omitted: 0 unusable links and 1 route variant(s).

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S06

Input: "‏bus route 102 ke stops batao — சென்னை؟"

Action: Enter. One user/reply pair; chat messages 6 → 8.

Visible result:

```text
Published information

102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.

Route stops

102 · published sequence 1

Partial published coverage: some links or route variants cannot be verified.

Omitted: 0 unusable links and 1 route variant(s).

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S07

Input: "<script>alert(\"scopeqa\")</script> <img src=x onerror=alert(\"scopeqa\")> List stops on bus route 102"

Action: Enter. One user/reply pair; chat messages 8 → 10.

Visible result:

```text
Published information

102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.

Route stops

102 · published sequence 1

Partial published coverage: some links or route variants cannot be verified.

Omitted: 0 unusable links and 1 route variant(s).

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S08

Input: "What is the deluxe bus fare?"

Action: Enter. One user/reply pair; chat messages 10 → 12.

Visible result:

```text
More information needed

Please provide a fare stage number, or the starting and destination stops.

Needed: origin or stage number, destination or stage number
```

### S09

Input: "What is the deluxe bus fare for stage 4?"

Action: revised Enter. One user/reply pair; chat messages 12 → 14.

Visible result:

```text
Published information

Published fare (Deluxe Services): INR 17 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.

Published fare

INR 17

Service class: Deluxe Services

Effective date: 2018-01-29 · Source: MTC_OFFICIAL

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S10

Input: "Where is the nearest metro station to Zorvix Junction?"

Action: Enter. One user/reply pair; chat messages 14 → 16.

Visible result:

```text
More information needed

Please provide a nearby landmark or locality.

Needed: landmark or locality
```

### S11

Input: "Where is the nearest metro station to Marina Beach?"

Action: revised button. One user/reply pair; chat messages 16 → 18.

Visible result:

```text
Published information

Nearest by straight line: Lighthouse Metro (1121 m). Nearest by straight-line distance only; walking access is not verified.

Nearest by straight line

Walking access and current operation are not verified.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S12

Input: "Where is the nearest metro station to Central?"

Action: Enter. One user/reply pair; chat messages 18 → 20.

Visible result:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### S13

Input: "Show scheduled departures from Guindy at 25:70 on 2026-02-30."

Action: Enter. One user/reply pair; chat messages 20 → 22.

Visible result:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### S14

Input: "Show scheduled departures on bus route 102 at 25:70 on 2026-02-30."

Action: Enter. One user/reply pair; chat messages 22 → 24.

Visible result:

```text
More information needed

Please clarify the time or day you mean.
```

### S15

Input: "What is the deluxe bus fare for stage 4 and stage 5?"

Action: Enter. One user/reply pair; chat messages 24 → 26.

Visible result:

```text
More information needed

Please ask about one route, stop, fare stage or time at a time.
```

### S16

Input: "List stops on bus route 102 and bus route 27D."

Action: Enter. One user/reply pair; chat messages 26 → 28.

Visible result:

```text
More information needed

Please choose which transport question to answer first.

Question types: route stop sequence, point to point route
```

### S17

Input: "a" repeated 8179 times (8192-byte JSON body)

Action: Enter. One user/reply pair; chat messages 28 → 30.

Visible result:

```text
More information needed

Please provide the stop to check, the route number or line name.

Needed: stop, route number or line name
```

### S18

Input: "a" repeated 8180 times (8193-byte JSON body)

Action: Enter. One user/reply pair; chat messages 30 → 32.

Visible result:

```text
Request could not be completed

Query body is too large.
```

### S19

Input: "अ" repeated 1363 times (4089 query UTF-8 bytes; 8191-byte escaped JSON body)

Action: Enter. One user/reply pair; chat messages 32 → 34.

Visible result:

```text
More information needed

Please provide the stop to check, the route number or line name.

Needed: stop, route number or line name
```

### S20

Input: "अ" repeated 1364 times (4092 query UTF-8 bytes; 8197-byte escaped JSON body)

Action: Enter. One user/reply pair; chat messages 34 → 36.

Visible result:

```text
Request could not be completed

Query body is too large.
```

### S21

Input: "What is the deluxe bus fare for stage 4?"

Action: two consecutive Enter presses. One user/reply pair; chat messages 36 → 38.

Visible result:

```text
Published information

Published fare (Deluxe Services): INR 17 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.

Published fare

INR 17

Service class: Deluxe Services

Effective date: 2018-01-29 · Source: MTC_OFFICIAL

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S22

Input: "Show scheduled departures from Chennai Central to Tambaram and Guindy."

Action: Enter. One user/reply pair; chat messages 38 → 40.

Visible result:

```text
More information needed

Please ask about one route, stop, fare stage or time at a time.
```

### S23

Input: "What are the first and last trains from Chennai Central to Tambaram and Zorvix Junction?"

Action: Enter. One user/reply pair; chat messages 40 → 42.

Visible result:

```text
More information needed

Please ask about one route, stop, fare stage or time at a time.
```

### S24

Input: "How often do trains run from Chennai Central to Tambaram and Guindy?"

Action: Enter. One user/reply pair; chat messages 42 → 44.

Visible result:

```text
More information needed

Please ask about one route, stop, fare stage or time at a time.
```

### S25

Input: "What are the first and last trains from Chennai Central to Tambaram via Guindy?"

Action: Enter. One user/reply pair; chat messages 44 → 46.

Visible result:

```text
Information unavailable

Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.
```

### S26

Input: "How often do trains run from Chennai Central to Tambaram via Zorvix Junction?"

Action: Enter. One user/reply pair; chat messages 46 → 48.

Visible result:

```text
Information unavailable

Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.
```

### S27

Input: "Show scheduled departures from Chennai Central to Tambaram via Guindy."

Action: Enter. One user/reply pair; chat messages 48 → 50.

Visible result:

```text
Information unavailable

Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.
```

### S28

Input: "Reload agent-owned tab"

Action: session check.

Visible result:

```text
Reload returned the initial page, example buttons, and no revised form. Chat message count changed from 50 to 0.
```

### S29

Input: "What are the first and last buses on route 102?"

Action: Enter. One user/reply pair; chat messages 0 → 2.

Visible result:

```text
Information unavailable

The snapshot has no confirmed interchange records.
```

### S30

Input: "How often does bus route 102 run?"

Action: Enter. One user/reply pair; chat messages 2 → 4.

Visible result:

```text
More information needed

Please provide the stop to check.

Needed: stop
```

### S31

Input: "Show scheduled departures for bus route 102 after 09:00."

Action: Enter. One user/reply pair; chat messages 4 → 6.

Visible result:

```text
More information needed

Please provide the boarding stop or station.

Needed: station or stop
```

### S32

Input: "What is the first bus from Island ground Terminus on route 102?"

Action: Enter. One user/reply pair; chat messages 6 → 8.

Visible result:

```text
Published information

Nearest by straight line: Island ground Terminus (0 m). Nearest by straight-line distance only; walking access is not verified.

Nearest by straight line

Walking access and current operation are not verified.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S33

Input: "What is the frequency of bus route 102 from Island ground Terminus?"

Action: Enter. One user/reply pair; chat messages 8 → 10.

Visible result:

```text
Published information

Published departures: 102 at 06:15:00, 102 at 06:35:00, 102 at 06:50:00, 102 at 07:15:00, 102 at 07:20:00 (service-day time). Published departures only; times are not live predictions.

Published departures

Times are schedule records, not live predictions.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S34

Input: "Show scheduled departures from Island ground Terminus for bus route 102 after 09:00."

Action: Enter. One user/reply pair; chat messages 10 → 12.

Visible result:

```text
Published information

Published departures: 102 at 09:20:00, 102 at 09:45:00, 102 at 10:05:00, 102 at 13:10:00, 102 at 13:55:00 (service-day time). Published departures only; times are not live predictions.

Published departures

Times are schedule records, not live predictions.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### S35

Input: "Chennai Central से Tambaram तक Guindy होते हुए पहली और आखिरी ट्रेन कब है?"

Action: Enter. One user/reply pair; chat messages 12 → 14.

Visible result:

```text
Information unavailable

Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.
```

### S36

Input: "Chennai Central se Tambaram tak Zorvix Junction hote hue train ki frequency kya hai?"

Action: Enter. One user/reply pair; chat messages 14 → 16.

Visible result:

```text
Information unavailable

Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.
```
