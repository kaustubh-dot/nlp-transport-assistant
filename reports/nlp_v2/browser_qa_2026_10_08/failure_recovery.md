# Isolated browser failure and recovery QA — 2026-10-08

Result: **25 distinct query scenarios passed**, plus two lifecycle assertions (offline startup and fresh reload), for **27 browser assertions**. The stub received exactly 24 query POSTs, one per synthetic scenario. The disconnected API submission is the twenty-fifth query scenario. There was exactly one delayed request. No production code was changed and no material failure/recovery defect was found in this scope.

## Scope and isolation

The unchanged `app/streamlit_app.py` at Git HEAD `bd9f148456778acb2a0562d8cfcb047783b5be57` ran on localhost:8613 with `NLP_V2_API_URL=http://127.0.0.1:8879`. The synthetic fixture server and its request log lived only under `/tmp`. All browser interaction used `mcp__cua_repl` in a dedicated hidden in-app-browser tab (`qaFailureTab`, ID 1). No browser viewport override, shared test runner, evaluator, held-out set, model, alias, research document, or production service was changed.

This is renderer and transport-error contract coverage. Ticketing, facility, accessibility, interchange, frequency, route and GTFS examples below are **synthetic** and do not establish real canonical database support or real transport facts. `QA_SYNTHETIC_*` source strings explicitly identify fixtures. The source’s normal `unavailable` response remains a supported outcome, not a defect.

Initial free-port inspection through sandbox `/proc/net` showed no listeners for the chosen ports; the restricted sandbox could not bind sockets. Approved isolated localhost launches then bound 8613 and 8879 successfully. The final host-level read-only check confirmed real UI 8601 and API 8875 listeners remained active, while isolated ports 8613/8879 and the owned stub/UI processes were absent.

## Browser cases

Each query used the visible chat textbox, Enter, then inspected the newly appended assistant message. Non-success cases were also checked for absent result headings/panels. Dataframes were checked after their transient loading skeleton settled, using visible screenshots, AX rows, and DOM-backed canvas fallback text.

| Case | Browser result |
| --- | --- |
| `offline-initial` | PASS — Offline warning is visible; chat input remains available (lifecycle assertion). |
| `offline-submit` | PASS — Red safe error: Request could not be completed / local T3 API unavailable; no result panel. |
| `online` | PASS — Same session recovers when stub starts; offline warning disappears; Published information text. |
| `invalid-json` | PASS — Invalid JSON yields safe API-unavailable error, no traceback/panel. |
| `http503-ok` | PASS — HTTP 503 carrying an otherwise valid ok fare is rewritten to safe request failure; INR 123 never appears. |
| `malformed-root` | PASS — JSON list root rejected as invalid response. |
| `malformed-data` | PASS — Fare amount="ninety" rejected before numeric formatting. |
| `unknown-status` | PASS — Unrecognized optimistic status rejected. |
| `null-containers` | PASS — slots=null and data=null rejected. |
| `null-optional` | PASS — intent/operation/clarification_reason=null plus null optional source/provisional accepted as safe text; no panel. |
| `unavailable` | PASS — Amber Information unavailable; synthetic route data does not become a success panel; candidate-count/unconfirmed caption retained. |
| `clarification` | PASS — Blue More information needed; missing origin/destination, candidate intent and entity advice visible; full-question revision form appears; no route panel. |
| `out-of-scope` | PASS — Blue Outside transport scope; no route panel; preceding revision form removed. |
| `error` | PASS — Red Request could not be completed; supplied fare data does not become a success panel. |
| `ticketing` | PASS — Synthetic policy, source caption and provisional warning render. |
| `facility` | PASS — Synthetic restroom record, source caption and provisional warning render. |
| `accessibility` | PASS — Synthetic lift metric says Recorded unavailable when available=false; provisional warning render. |
| `interchange` | PASS — Settled station/from/to/source table displays synthetic station, metro, bus, synthetic source; hub and snapshot provisional captions retained. |
| `fare` | PASS — Published fare INR 29; Deluxe Services; effective 2026-01-01; exact synthetic source; provisional warning. |
| `gtfs24` | PASS — First 05:30:00 and last 25:10:00 preserved; GTFS past 24:00 explanation, source and provisional warning visible. |
| `frequency` | PASS — Median scheduled interval 7.5 min; 120-minute window after 09:00:00; synthetic source and provisional warning visible. |
| `partial` | PASS — Synthetic route table plus connectivity disclaimer, partial-coverage warning, omitted 2 links / 1 variant, hub warning and provisional warning. |
| `malformed-optional` | PASS — excluded_unusable_rows={bad:3}, uncovered_route_ids=7 safely ignored for counts; valid route panel and partial/hub/provisional cautions remain; no traceback. |
| `missing-panel` | PASS — ok fare operation missing amount renders safe response text and no metric/panel. |
| `timeout` | PASS — One 22-second delayed fixture exceeds configured 20-second requests timeout and ends in safe API-unavailable error; no late success response. |
| `after-error` | PASS — Next valid request succeeds with INR 19 and effective 2026-02-02/source after timeout; history remains usable. |
| `fresh-reload` | PASS — Settled reload shows empty history, three example buttons, enabled input and no offline banner (lifecycle assertion). |

## Labels, colors and robustness

Computed alert styles in this actual browser: error text `rgb(125, 53, 59)` over `rgba(255, 43, 43, 0.09)`; unavailable text `rgb(146, 108, 5)` over `rgba(255, 227, 18, 0.1)`; clarification/out_of_scope text `rgb(0, 66, 128)` over `rgba(28, 131, 225, 0.1)`. `ok` uses ordinary published-information text and a structured panel only when its required data key is present; it does not use a green success alert.

No browser console warning/error was captured during the 25 query scenarios and the settled reload, and no traceback appeared. After the isolated services exited, the tab showed Connecting and logged one expected `WebSocket onclose` warning. This disconnected-server warning is excluded from application response failures.

The delayed case used the unchanged frontend `timeout=20` with one stub `sleep(22)`. The browser locator wait itself has an approximately 3-second tooling deadline, so it first observed Running/Checking the transit snapshot, then the later DOM observation confirmed the safe error. This verifies bounded failure and recovery; it does not claim an independently measured exact 20-second latency. The stub log proves exactly one delayed request. No stress/load test was attempted.

Some screenshots captured a previous scroll position immediately after a render. Those images were renamed according to the content they actually show. Timeout and the first after-error result are supported by recorded DOM observations, not a mislabeled screenshot. The fresh-reload screenshot was retaken after starter controls fully settled. A supplementary screenshot resubmission attempt met a disabled Connecting input after the servers exited and sent no additional query.

## Proof screenshots

![Offline submission safe error](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/failure_offline_submit.jpg)

![Synthetic fare metadata](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/failure_metadata_fare.jpg)

![Synthetic interchange table](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/failure_panel_interchange.jpg)

![Synthetic frequency](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/failure_panel_frequency.jpg)

![Route coverage and flags](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/failure_partial_coverage_full.jpg)

![Malformed optional coverage handled safely](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/failure_malformed_optional_full.jpg)

![Fresh reload](/home/kaustubh/projects/NLP/reports/nlp_v2/browser_qa_2026_10_08/failure_fresh_reload.jpg)

Additional snapshots in this directory use the `failure_` prefix. `failure_status_clarification.jpg` is a partial viewport showing the label; the complete clarification content and revision controls were verified by DOM/AX.

## Exact synthetic inputs and boundary checks

For reproduction, start unchanged Streamlit with NLP_V2_API_URL=http://127.0.0.1:8879 and send `QA case <key>` in the visible chat. The offline submission was `QA offline complete question` before the stub was started. GET `/health` returned HTTP 200 `{"taxonomy":"T3"}`. POST `/api/v2/query` returned HTTP 200 for all fixtures except `http503-ok` (HTTP 503). Below are exact JSON payloads; `invalid-json` is the literal invalid body `{this is not JSON`.

Boundary checks called the unchanged `valid_reply` before `result_panel`, matching the application’s request boundary. This was a read-only fixture cross-check, not an additional browser scenario or shared pytest run.

```json
{
  "online": {
    "valid_reply": true,
    "panel": null
  },
  "http503-ok": {
    "valid_reply": true,
    "panel": "fare"
  },
  "malformed-root": {
    "valid_reply": false,
    "panel": null
  },
  "malformed-data": {
    "valid_reply": false,
    "panel": null
  },
  "unknown-status": {
    "valid_reply": false,
    "panel": null
  },
  "null-containers": {
    "valid_reply": false,
    "panel": null
  },
  "null-optional": {
    "valid_reply": true,
    "panel": null
  },
  "unavailable": {
    "valid_reply": true,
    "panel": null
  },
  "clarification": {
    "valid_reply": true,
    "panel": null
  },
  "out-of-scope": {
    "valid_reply": true,
    "panel": null
  },
  "error": {
    "valid_reply": true,
    "panel": null
  },
  "ticketing": {
    "valid_reply": true,
    "panel": "ticketing"
  },
  "facility": {
    "valid_reply": true,
    "panel": "facility"
  },
  "accessibility": {
    "valid_reply": true,
    "panel": "accessibility"
  },
  "interchange": {
    "valid_reply": true,
    "panel": "interchange"
  },
  "fare": {
    "valid_reply": true,
    "panel": "fare"
  },
  "frequency": {
    "valid_reply": true,
    "panel": "frequency"
  },
  "gtfs24": {
    "valid_reply": true,
    "panel": "service_bounds"
  },
  "partial": {
    "valid_reply": true,
    "panel": "routes"
  },
  "malformed-optional": {
    "valid_reply": true,
    "panel": "routes"
  },
  "missing-panel": {
    "valid_reply": true,
    "panel": null
  },
  "timeout": {
    "valid_reply": true,
    "panel": null
  },
  "after-error": {
    "valid_reply": true,
    "panel": "fare"
  }
}
```

### `online`

```json
{
  "status": "ok",
  "response_text": "QA online recovery verified.",
  "operation": null,
  "slots": {},
  "data": {}
}
```

### `invalid-json`

```json
{this is not JSON
```

### `http503-ok`

```json
{
  "status": "ok",
  "response_text": "QA invalid HTTP success must not display.",
  "operation": "CALCULATE_FARE",
  "slots": {},
  "data": {
    "amount": 123
  }
}
```

### `malformed-root`

```json
[
  "invalid root"
]
```

### `malformed-data`

```json
{
  "status": "ok",
  "response_text": "Synthetic browser contract fixture.",
  "operation": "CALCULATE_FARE",
  "slots": {},
  "data": {
    "amount": "ninety"
  }
}
```

### `unknown-status`

```json
{
  "status": "optimistic",
  "response_text": "QA unknown status must not display."
}
```

### `null-containers`

```json
{
  "status": "ok",
  "response_text": "QA null containers must not display.",
  "slots": null,
  "data": null
}
```

### `null-optional`

```json
{
  "status": "ok",
  "response_text": "QA null optional metadata rendered safely.",
  "operation": null,
  "slots": {},
  "data": {
    "source": null,
    "provisional": null
  },
  "intent": null,
  "clarification_reason": null
}
```

### `unavailable`

```json
{
  "status": "unavailable",
  "response_text": "QA unavailable synthetic fixture.",
  "operation": "PLAN_ROUTE",
  "slots": {},
  "data": {
    "routes": [
      {
        "route_name": "SHOULD NOT PANEL"
      }
    ],
    "published_directional_route_candidates": 3
  },
  "outcome_reason": "unsupported_source"
}
```

### `clarification`

```json
{
  "status": "clarification",
  "response_text": "QA clarification synthetic fixture.",
  "operation": "PLAN_ROUTE",
  "slots": {},
  "data": {
    "routes": [
      {
        "route_name": "SHOULD NOT PANEL"
      }
    ]
  },
  "missing_slots": [
    "origin",
    "destination"
  ],
  "candidate_intents": [
    "point_to_point_route",
    "multimodal_route"
  ],
  "candidate_entities": [
    "QA_STATION_A",
    "QA_STATION_B"
  ],
  "outcome_reason": "entity_ambiguity"
}
```

### `out-of-scope`

```json
{
  "status": "out_of_scope",
  "response_text": "QA outside transport synthetic fixture.",
  "operation": "PLAN_ROUTE",
  "slots": {},
  "data": {
    "routes": [
      {
        "route_name": "SHOULD NOT PANEL"
      }
    ]
  },
  "outcome_reason": "out_of_scope"
}
```

### `error`

```json
{
  "status": "error",
  "response_text": "QA error synthetic fixture.",
  "operation": "CALCULATE_FARE",
  "slots": {},
  "data": {
    "amount": 123
  },
  "outcome_reason": "temporary_service_unavailability"
}
```

### `ticketing`

```json
{
  "status": "ok",
  "response_text": "QA ticketing panel fixture.",
  "operation": "GET_TICKETING_POLICY",
  "slots": {},
  "data": {
    "policy": "QA synthetic ticketing: demonstration pass policy only.",
    "source": "QA_SYNTHETIC_TICKETING_SOURCE",
    "provisional": true
  }
}
```

### `facility`

```json
{
  "status": "ok",
  "response_text": "QA facility panel fixture.",
  "operation": "GET_STATION_FACILITY",
  "slots": {},
  "data": {
    "facility": "QA synthetic restroom record.",
    "source": "QA_SYNTHETIC_FACILITY_SOURCE",
    "provisional": true
  }
}
```

### `accessibility`

```json
{
  "status": "ok",
  "response_text": "QA accessibility panel fixture.",
  "operation": "GET_ACCESSIBILITY_INFO",
  "slots": {},
  "data": {
    "feature": "QA synthetic lift",
    "available": false,
    "provisional": true
  }
}
```

### `interchange`

```json
{
  "status": "ok",
  "response_text": "QA interchange panel fixture.",
  "operation": "GET_INTERCHANGE_DETAILS",
  "slots": {},
  "data": {
    "transfers": [
      {
        "station": "QA synthetic station",
        "from": "metro",
        "to": "bus",
        "source": "QA_SYNTHETIC_TRANSFER_SOURCE"
      }
    ],
    "hub_membership_unverified": true,
    "provisional": true
  }
}
```

### `fare`

```json
{
  "status": "ok",
  "response_text": "QA fare metadata fixture.",
  "operation": "CALCULATE_FARE",
  "slots": {},
  "data": {
    "amount": 29,
    "currency": "INR",
    "service_type": "Deluxe Services",
    "effective_date": "2026-01-01",
    "source": "QA_SYNTHETIC_FARE_SOURCE",
    "provisional": true
  }
}
```

### `frequency`

```json
{
  "status": "ok",
  "response_text": "QA synthetic frequency fixture.",
  "operation": "GET_SERVICE_FREQUENCY",
  "slots": {},
  "data": {
    "median_headway_minutes": 7.5,
    "window_start": "09:00:00",
    "window_minutes": 120,
    "source": "QA_SYNTHETIC_FREQUENCY_SOURCE",
    "provisional": true
  }
}
```

### `gtfs24`

```json
{
  "status": "ok",
  "response_text": "QA extended service day fixture.",
  "operation": "GET_FIRST_LAST_SERVICE",
  "slots": {},
  "data": {
    "first_departure": "05:30:00",
    "last_departure": "25:10:00",
    "source": [
      "QA_SYNTHETIC_GTFS_SOURCE"
    ],
    "provisional": true
  }
}
```

### `partial`

```json
{
  "status": "ok",
  "response_text": "QA partial coverage fixture.",
  "operation": "PLAN_ROUTE",
  "slots": {},
  "data": {
    "routes": [
      {
        "route_name": "QA synthetic route",
        "mode": "bus",
        "source": "QA_SYNTHETIC_ROUTE_SOURCE",
        "partial_topology": true
      }
    ],
    "partial_topology": true,
    "excluded_unusable_rows": 2,
    "uncovered_route_ids": [
      "QA_VARIANT"
    ],
    "hub_membership_unverified": true,
    "provisional": true
  }
}
```

### `malformed-optional`

```json
{
  "status": "ok",
  "response_text": "QA malformed optional coverage fixture.",
  "operation": "PLAN_ROUTE",
  "slots": {},
  "data": {
    "routes": [
      {
        "route_name": "QA synthetic optional metadata route",
        "mode": "bus",
        "source": "QA_SYNTHETIC_ROUTE_SOURCE"
      }
    ],
    "partial_topology": true,
    "excluded_unusable_rows": {
      "bad": 3
    },
    "uncovered_route_ids": 7,
    "hub_membership_unverified": true,
    "provisional": true
  }
}
```

### `missing-panel`

```json
{
  "status": "ok",
  "response_text": "QA missing panel key safe text fixture.",
  "operation": "CALCULATE_FARE",
  "slots": {},
  "data": {
    "source": "QA_SYNTHETIC_SOURCE"
  }
}
```

### `timeout`

```json
{
  "status": "ok",
  "response_text": "QA too late response must not display.",
  "operation": null,
  "slots": {},
  "data": {}
}
```

### `after-error`

```json
{
  "status": "ok",
  "response_text": "QA valid after error recovery fixture.",
  "operation": "CALCULATE_FARE",
  "slots": {},
  "data": {
    "amount": 19,
    "currency": "INR",
    "source": "QA_SYNTHETIC_RECOVERY_SOURCE",
    "effective_date": "2026-02-02"
  }
}
```

## Cleanup and file integrity

Own Streamlit session 15641 reported `Stopping...` and exit 0; own stub session 44826 reported exit 143. The earlier stub session 61118 was deliberately stopped once to add the frequency fixture, before further queries, then restarted. No production process was stopped. Final elevated read-only `/proc/net` inspection found UI 8601/API 8875 in LISTEN state and no 8613/8879 sockets; the only matched Streamlit process was real UI 8601 (PID 385017). Own tab ID1 was closed; user tabs remained untouched.

Source SHA256 at report generation:

```text
app/streamlit_app.py 311d83bfbfb5eb2edd1841f68d11fb38da16e50ced240a97293272cb3a83466b
app/frontend_contract.py 7cc09a5e2a900f942c942a3cd3fefca2edc22222a4703fc51eeb6d3539630f0a
src/nlp_v2/contracts.py 06e226d21430c93acfe7a1dc91a6672ab48b08a5f0460a530823f6355b73282c
```

Repository evidence added only under this report directory; disposable harness files remain under `/tmp`.
