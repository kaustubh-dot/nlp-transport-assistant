# Functional and multilingual live browser QA — 2026-10-08

Tested real Streamlit http://127.0.0.1:8601/ in an isolated hidden in-app-browser tab against the task-owned API at port 8875. Git HEAD was independently read as bd9f148456778acb2a0562d8cfcb047783b5be57. Browser viewport was left unchanged (screenshots are 1280×720). Only this agent's tab was used. No application, model, production DB, evaluation, training or held-out data changes were made.

## Scope and method

Read app/streamlit_app.py, app/frontend_contract.py, src/nlp_v2/contracts.py, the T3 dispatch design, current production runbook, answerability matrix, and source registry. The older answerability matrix lists aspirational capabilities; the current runbook explicitly limits transfer, facilities, accessibility, ticketing and live status. The matrix's sample queries were not submitted. All below are fresh synthetic manual questions, with two extra contract-term phrasings supplied by the primary agent. No query grid or evaluator was run.

Each query was filled into the visible chat textbox and submitted with Enter. The assistant message count was checked, the new assistant message was awaited, then a fresh visible DOM snapshot and the message's rendered innerText were read. Case 8 instead used the visible full-question revision form and Ask revised question button. Browser responses are observations, not gold labels. Exact public operation IDs are not shown in this UI: operation alignment below is inferred from visible panel/message/required-input content, not hidden API state. This report does not attribute every mismatch exclusively to the classifier; extraction and dispatch can also affect visible outcomes.

**Counts:** 32 distinct query submissions and 32 primary query-result checks. Nine supplemental checks cover the initial controls, revision interaction, route expander, four screenshot inspections, final console inspection and a read-only source audit (nearest anchor plus Unicode). These 41 checks overlap and are not independent accuracy samples. Visible status totals: 12 Published information, 12 More information needed, 8 Information unavailable; zero Outside transport scope and zero Request could not be completed. No warn/error console entries were captured at the end. No crash was observed.

## Findings

- Genuine live successful panels were reached for route stops, stop membership, service bounds, departures, stage fare and nearest transport. Source, effective-date, partial-coverage and provisional warnings rendered where appropriate.
- Point-to-point route candidates and median scheduled interval panels were **not reached**. Repeated route entity ambiguity is a conservative limitation; the explicit route-candidate wording in case 24 also gave an unrelated stop-list requirement. Four frequency questions (12, 13, 14, 23) returned bounds, fare clarification or departures. Do not infer frequency coverage from their OK statuses.
- Membership case 2 returned a full stop list rather than Yes/No; Roman Hindi case 3 reached Yes. Natural interchange case 20 required one mode despite asking for a transfer between two modes. Hindi realtime case 26 returned an interchange-source reason, and delay case 25 requested a stop. Explicit live-tracking case 31 reached the correct source refusal.
- Both unrelated-domain questions (27 and 28) failed to reach outside-transport-scope status: one received a transfer-graph limitation and one a boarding-stop clarification. The app did not invent poem/weather facts, but these are material goal/response mismatches.
- Hindi numeral ७ and noisy mixed-case stage fare succeeded; spelled ordinal सातवें was not accepted as the stage number. Original Unicode and punctuation remained visible in the query transcript. Replies remained English, consistent with the runbook's documented limitation.
- Case 22 has a material location-scope limitation: generic “IIT Madras” produced a result exactly matching the Thaiyur Campus anchor without displaying that campus. The same table has a confirmed Tamil glyph-rendering issue. Read-only evidence is below.

Conservative unavailable replies for cross-mode journeys, ticket policy, facilities and accessibility were presented without success panels (9, 17–19). Entity clarification (4–8, 10) preserved the full-query revision flow, but the route-scope revision in case 8 still did not resolve it. This report does not declare all sixteen operations passing simply because all sixteen goals were attempted.

## Intended operation coverage

| Intended T3 family | Cases | Visible outcome |
|---|---|---|
| point_to_point_route / PLAN_ROUTE | 4–8, 24 | Entity ambiguity; route-candidate wording requests route/line. Live routes panel unreached. |
| multimodal_route / PLAN_MULTIMODAL_ROUTE | 9 | Correct conservative graph-source refusal. |
| route_stop_sequence / LIST_ROUTE_STOPS | 1 | Ordered sequence expander/source/partial notes. |
| route_stop_membership / CHECK_STOP_ON_ROUTE | 2, 3 | English mismatch; Roman Hindi Yes panel. |
| first_and_last_service / GET_FIRST_LAST_SERVICE | 11 | 06:15:00 and 21:30:00 metrics. |
| service_frequency / GET_SERVICE_FREQUENCY | 12–14, 23 | Bounds/fare/departure mismatches; headway panel unreached. |
| scheduled_departure / GET_SCHEDULED_DEPARTURES | 15 | Five published departures after 08:00; table/source screenshot. |
| mode_availability / CHECK_SERVICE_AVAILABILITY | 10 | Entity ambiguity, no connectivity claim. |
| fare_calculation / CALCULATE_FARE | 16, 29, 30, 32 | Sourced INR 11 fares; spelled Hindi ordinal limitation. |
| ticketing_and_passes / GET_TICKETING_POLICY | 17 | No authoritative policy table. |
| station_facilities / GET_STATION_FACILITY | 18 | Facility availability unverified. |
| station_accessibility / GET_ACCESSIBILITY_INFO | 19 | No verified accessibility values. |
| interchange_transfer / GET_INTERCHANGE_DETAILS | 20, 21 | Mode clarification/general facility refusal; intended interchange not established. |
| nearest_transport / FIND_NEAREST_STATION | 22 | Table and geometric caveat; silent Thaiyur scope and Tamil glyph issue. |
| realtime_status_query | 25, 26, 31 | Two goal/reason mismatches; explicit live tracking correctly refused. |
| out_of_scope | 27, 28 | Transfer-source refusal / boarding-stop clarification; scope rejection unreached. |

## Supplemental evidence

Route sequence expander in case 1 was opened. The screenshot shows columns sequence/name and rows 1 Island ground Terminus, 2 High Court, 3 Parrys Corner, 4 Secretariat, 5 War Memorial. Visible source was CHENNAI_COMMUNITY_GTFS; partial notes reported zero unusable links and one route variant omitted. Download/search/fullscreen table controls were visible but not activated, because this task concerns live response rendering.

Case 15 screenshot verifies route_name/time/source rows: 102 08:05:00, 102 08:10:00, 102 08:50:00, 102 08:55:00, 102 09:20:00; every source is CHENNAI_COMMUNITY_GTFS. Case 22 table screenshot verifies: Sholinganallur Metro / metro / 12801 / OSM_OVERPASS; Airport Metro / metro / 20875 / CHENNAI_COMMUNITY_GTFS; Tamil Chennai Airport row / metro / 20925 / OSM_OVERPASS; Chennai International Airport / metro / 20929 / CMRL_API; Chennai Airport Metro / metro / 21047 / CHENNAI_COMMUNITY_GTFS. The tables are canvas-rendered and their row cells are not in the DOM snapshot, so screenshot evidence was used instead of claiming DOM coverage.

Read-only SQLite connections used mode=ro, solely to interpret case 22. places has OSM_POI_11013406019 “IIT Madras, Thaiyur Campus” at 12.7936971,80.1850698 (inside_cma=1, OSM_OVERPASS), while OSM_POI_24730814 “Indian Institute of Technology - Madras” has NULL coordinates/inside_cma=0. domain._nearest uses the resolved anchor coordinates and Haversine distance over located inside-CMA stops for the chosen mode. An independent read-only geometry calculation from the Thaiyur row reproduced **all five displayed names/distances/sources exactly**. This is evidence of the resolved scope, not an external factual claim about the geographically nearest operational metro station. The service returns anchor_name, but the frontend nearest panel omits it. Metro snapshot coverage was 152 inside-CMA rows with coordinates, plus five outside/no-coordinate rows.

The third nearest row's canonical name is “சென்னை விமான நிலையம்”. The database has Tamil Unicode (including U+0BB5 U+0BBF U+0BAE U+0BBE U+0BA9 in விமான), with no literal square placeholders. The screenshot shows boxes in that word. This supports a rendering/font issue, not corrupted literal □ source text. No font or DB fix was made.

Final tab console inspection used levels error/warn, limit 100 and returned []. This only describes captured browser console entries, not backend logs.

## Screenshots

![Expanded source-backed route sequence](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/functional_sequence.jpg)

![Published departure rows and snapshot caveats](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/functional_departures.jpg)

![Nearest table, source columns, and Tamil glyph issue](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/functional_nearest.jpg)

![Hindi numeral fare query with source and effective date](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/functional_hindi_fare.jpg)

## Exact case log

The following blocks preserve exact rendered assistant message text; blank lines are from the rendered innerText, except case 1 additionally includes the source revealed by its expander. Table rows are separately preserved above/screenshotted. Repeated caveats are intentionally retained. Every case used fill → submit → await new message → fresh DOM snapshot → read visible reply, except case 8 used the revision form as stated.

### Case 1 — route_stop_sequence

Query: Please show the published stops served by bus 102 in order.

Assessment: PASS — stop-sequence panel, source, ordered rows and partial/provisional notes rendered; expander inspected.

Exact visible assistant reply:

```text
Published information
102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.
Route stops
102 · published sequence 1
Source: CHENNAI_COMMUNITY_GTFS
Partial published coverage: some links or route variants cannot be verified.
Omitted: 0 unusable links and 1 route variant(s).
Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 2 — route_stop_membership

Query: Does bus route 102 include the Marina Beach stop in its published sequence?

Assessment: CAPABILITY ISSUE — asked membership; rendered stop sequence rather than Yes/No. Message and panel agree with each other, but differ from user goal.

Exact visible assistant reply:

```text
Published information

102 stops: Island ground Terminus, High Court, Parrys Corner, Secretariat, War Memorial, Annasquare, Kannagi Statue Shelter 1, Marina Beach, …. Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.

Route stops

102 · published sequence 1

Partial published coverage: some links or route variants cannot be verified.

Omitted: 0 unusable links and 1 route variant(s).

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 3 — route_stop_membership / Roman Hindi

Query: Kya 102 bus Marina Beach par rukti hai?

Assessment: PASS — Roman Hindi membership returned Yes with source, partial coverage and current-service caveat.

Exact visible assistant reply:

```text
Published information

The stop appears on the published route sequence. Published route-stop sequence checked; current service is not confirmed.

On published route sequence

Yes

Source: CHENNAI_COMMUNITY_GTFS

Partial published coverage: some links or route variants cannot be verified.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 4 — point_to_point_route

Query: How can I travel by bus from High Court to Marina Beach?

Assessment: CONSERVATIVE LIMITATION — entity clarification; full-question revision control rendered. No live route panel reached.

Exact visible assistant reply:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### Case 5 — point_to_point_route / precise stop

Query: What bus route goes from Island ground Terminus to Marina Beach?

Assessment: CONSERVATIVE LIMITATION — even precise visible stop names produced entity clarification; no route candidate panel.

Exact visible assistant reply:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### Case 6 — point_to_point_route / exact stops

Query: How do I go from Secretariat to War Memorial by bus?

Assessment: CONSERVATIVE LIMITATION — two visible route-sequence stop names produced entity clarification.

Exact visible assistant reply:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### Case 7 — point_to_point_route / Hinglish

Query: Adyar se Broadway bus ka route bata sakte ho?

Assessment: CONSERVATIVE LIMITATION — Hinglish route question produced entity clarification.

Exact visible assistant reply:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### Case 8 — point_to_point_route / revised full question

Query: How can I go from Secretariat to War Memorial on bus route 102?

Assessment: CONSERVATIVE LIMITATION — revised full question including route 102 submitted successfully but entity clarification persisted. Revision interaction passed.

Exact visible assistant reply:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### Case 9 — multimodal_route

Query: Suggest a bus and metro journey from Guindy to the Chennai Airport.

Assessment: PASS SOURCE BOUNDARY — confirmed cross-mode graph absent; unavailable reply, no success panel.

Exact visible assistant reply:

```text
Information unavailable

No confirmed cross-mode transfer graph is available in this snapshot.
```

### Case 10 — mode_availability

Query: Is a bus service available between Guindy and Chennai Central?

Assessment: CONSERVATIVE LIMITATION — service-availability query blocked by entity ambiguity; no false connectivity claim.

Exact visible assistant reply:

```text
More information needed

Please clarify which stop or location you mean.

More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.
```

### Case 11 — first_and_last_service

Query: What are the first and last departures of bus 102 from Island ground Terminus?

Assessment: PASS — first/last metrics matched visible schedule text, source and service-day/provisional caveats.

Exact visible assistant reply:

```text
Published information

Published first departure: 06:15:00; last: 21:30:00 (service-day time). Published schedule bounds; verify current operation with the operator.

Published service times

First departure

06:15:00

Last departure

21:30:00

GTFS service-day times may continue past 24:00.

Source: CHENNAI_COMMUNITY_GTFS

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 12 — service_frequency

Query: How often is bus 102 scheduled to depart from Island ground Terminus?

Assessment: CAPABILITY ISSUE — frequency goal returned first/last bounds.

Exact visible assistant reply:

```text
Published information

Published first departure: 06:15:00; last: 21:30:00 (service-day time). Published schedule bounds; verify current operation with the operator.

Published service times

First departure

06:15:00

Last departure

21:30:00

GTFS service-day times may continue past 24:00.

Source: CHENNAI_COMMUNITY_GTFS

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 13 — service_frequency / Hinglish

Query: Bus 102 ki frequency Island ground Terminus par kitni hai?

Assessment: CAPABILITY ISSUE — Hinglish frequency goal asked for fare origin/stage; unrelated clarification.

Exact visible assistant reply:

```text
More information needed

Please provide the starting stop or fare stage number.

Needed: origin or stage number
```

### Case 14 — service_frequency / direct wording

Query: What is the frequency of bus route 102 at Island ground Terminus?

Assessment: CAPABILITY ISSUE — frequency goal returned departures table instead of headway.

Exact visible assistant reply:

```text
Published information

Published departures: 102 at 06:15:00, 102 at 06:35:00, 102 at 06:50:00, 102 at 07:15:00, 102 at 07:20:00 (service-day time). Published departures only; times are not live predictions.

Published departures

Times are schedule records, not live predictions.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 15 — scheduled_departure

Query: Show the scheduled departures of bus 102 from Island ground Terminus after 8 AM.

Assessment: PASS — after-08:00 departure table matched five visible times; screenshot verifies route/source columns and schedule caveat.

Exact visible assistant reply:

```text
Published information

Published departures: 102 at 08:05:00, 102 at 08:10:00, 102 at 08:50:00, 102 at 08:55:00, 102 at 09:20:00 (service-day time). Published departures only; times are not live predictions.

Published departures

Times are schedule records, not live predictions.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 16 — fare_calculation

Query: What is the ordinary MTC bus fare for stage 7?

Assessment: PASS — INR 11 ordinary stage fare, class, 2018-01-29 effective date and MTC_OFFICIAL source rendered.

Exact visible assistant reply:

```text
Published information

Published fare (Ordinary Services): INR 11 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.

Published fare

INR 11

Service class: Ordinary Services

Effective date: 2018-01-29 · Source: MTC_OFFICIAL

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 17 — ticketing_and_passes

Query: Can I recharge a metro smart card at Chennai Central station?

Assessment: PASS SOURCE BOUNDARY — authoritative ticket/pass policy absent, no success panel.

Exact visible assistant reply:

```text
Information unavailable

This snapshot contains no authoritative ticket or pass policy table.
```

### Case 18 — station_facilities

Query: Is drinking water available at Guindy metro station?

Assessment: PASS SOURCE BOUNDARY — unverified facility availability reported, no success panel.

Exact visible assistant reply:

```text
Information unavailable

Facility availability is not verified in this snapshot.
```

### Case 19 — station_accessibility

Query: Does Guindy metro station have a wheelchair accessible ramp?

Assessment: PASS SOURCE BOUNDARY — verified accessibility values absent, no success panel.

Exact visible assistant reply:

```text
Information unavailable

The snapshot contains no verified accessibility feature values.
```

### Case 20 — interchange_transfer

Query: How do I transfer from metro to suburban rail at Chennai Central?

Assessment: CAPABILITY ISSUE — natural two-mode transfer goal asked to choose one transport mode; intended interchange boundary not reached.

Exact visible assistant reply:

```text
More information needed

Please choose one transport mode for this question.

Needed: transport mode
```

### Case 21 — interchange_transfer / direct wording

Query: What interchange facilities are recorded at Chennai Central?

Assessment: LIMITED / AMBIGUOUS WORDING — interchange-facilities goal returned general facility unavailability; not evidence that interchange execution succeeded.

Exact visible assistant reply:

```text
Information unavailable

Facility availability is not verified in this snapshot.
```

### Case 22 — nearest_transport

Query: Which metro station is nearest to IIT Madras?

Assessment: MATERIAL SCOPE LIMITATION — nearest panel rendered, but generic IIT Madras result exactly matches Thaiyur Campus coordinates; UI does not disclose resolved campus. Tamil table row also has confirmed glyph loss. See source audit.

Exact visible assistant reply:

```text
Published information

Nearest by straight line: Sholinganallur Metro (12801 m). Nearest by straight-line distance only; walking access is not verified.

Nearest by straight line

Walking access and current operation are not verified.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 23 — service_frequency / contract wording

Query: What is the scheduled service frequency for bus route 102 at Island ground Terminus?

Assessment: CAPABILITY ISSUE — explicit scheduled-frequency goal still returned departures; median-headway panel unreached.

Exact visible assistant reply:

```text
Published information

Published departures: 102 at 06:15:00, 102 at 06:35:00, 102 at 06:50:00, 102 at 07:15:00, 102 at 07:20:00 (service-day time). Published departures only; times are not live predictions.

Published departures

Times are schedule records, not live predictions.

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 24 — point_to_point_route / contract wording

Query: Show published bus route candidates from Island ground Terminus to Annasquare.

Assessment: CAPABILITY ISSUE — published route-candidates goal asked for a route number/line name, consistent with stop-list requirement rather than point-to-point result.

Exact visible assistant reply:

```text
More information needed

Please provide the route number or line name.

Needed: route number or line name
```

### Case 25 — realtime_status_query

Query: Is bus 102 delayed at the moment?

Assessment: CAPABILITY ISSUE — current delay goal asked for boarding stop, rather than explaining missing realtime source.

Exact visible assistant reply:

```text
More information needed

Please provide the boarding stop or station.

Needed: station or stop
```

### Case 26 — realtime_status_query / Hindi Devanagari

Query: १०२ बस अभी कहाँ है?

Assessment: CAPABILITY ISSUE — Hindi current-location goal returned interchange-source limitation; unavailable is conservative but reason is unrelated.

Exact visible assistant reply:

```text
Information unavailable

The snapshot has no confirmed interchange records.
```

### Case 27 — out_of_scope

Query: Write a short poem about monsoon clouds.

Assessment: CAPABILITY ISSUE — unrelated poem goal returned cross-mode graph limitation instead of outside-transport-scope status.

Exact visible assistant reply:

```text
Information unavailable

No confirmed cross-mode transfer graph is available in this snapshot.
```

### Case 28 — out_of_scope / direct wording

Query: What is the weather forecast for Mumbai this weekend?

Assessment: CAPABILITY ISSUE — unrelated weather goal asked for boarding stop; outside-scope boundary not reached.

Exact visible assistant reply:

```text
More information needed

Please provide the boarding stop or station.

Needed: station or stop
```

### Case 29 — fare_calculation / Hindi Devanagari

Query: साधारण बस में सातवें स्टेज का किराया कितना है?

Assessment: EXTRACTION LIMITATION — spelled Hindi ordinal सातवें was not accepted as stage 7; asked for stage or OD. No unsupported fare guessed.

Exact visible assistant reply:

```text
More information needed

Please provide a fare stage number, or the starting and destination stops.

Needed: origin or stage number, destination or stage number
```

### Case 30 — fare_calculation / mixed case and noisy punctuation

Query: oRdInArY BUS... stage 7 fare pls???

Assessment: PASS — mixed case, ellipsis and repeated punctuation preserved; sourced INR 11 fare rendered.

Exact visible assistant reply:

```text
Published information

Published fare (Ordinary Services): INR 11 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.

Published fare

INR 11

Service class: Ordinary Services

Effective date: 2018-01-29 · Source: MTC_OFFICIAL

Snapshot-derived information. Verify current service and conditions with the operator.
```

### Case 31 — realtime_status_query / live tracking wording

Query: Can you show live tracking for bus 102 right now?

Assessment: PASS REALTIME BOUNDARY — explicit live tracking request refused with operator verification guidance and no result panel.

Exact visible assistant reply:

```text
Information unavailable

Live transport status is unavailable; please verify with the operator.
```

### Case 32 — fare_calculation / Devanagari numeral

Query: साधारण बस के स्टेज ७ का किराया बताओ।

Assessment: PASS — Hindi Devanagari numeral ७ recognized; source-backed INR 11 fare rendered with effective date.

Exact visible assistant reply:

```text
Published information

Published fare (Ordinary Services): INR 11 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.

Published fare

INR 11

Service class: Ordinary Services

Effective date: 2018-01-29 · Source: MTC_OFFICIAL

Snapshot-derived information. Verify current service and conditions with the operator.
```
