# Architecture

The application has one NLP entry point: `src.nlp_v2.assistant.T3Assistant`.

```text
Streamlit UI → local HTTP API → T3Assistant
                                ├─ selected MuRIL intent classifier
                                ├─ deterministic text/slot extraction
                                ├─ canonical entity resolver
                                ├─ semantic validation and dispatch
                                └─ read-only canonical transit service
```

The model reads the original multilingual question. Extraction normalizes a separate copy, resolves canonical names and reviewed aliases, and preserves explicit mode, time, route and exclusion constraints. Ambiguous entities, missing execution slots, unsupported constraints and multiple goals produce bounded clarification or unavailable responses.

The 16 intent labels cover point-to-point and multimodal routes; first/last service, frequency and scheduled departures; route sequences and stop membership; mode availability; fares and ticketing; facilities, accessibility and interchanges; nearest transport; realtime requests; and out-of-scope questions. A label's existence does not guarantee source coverage. The [manifest](models/nlp_v2_t3_manifest.json) defines the fixed label order and model-loading contract.

`src/nlp_v2/domain.py` queries [canonical_transport.db](data/canonical/transit/canonical_transport.db) through read-only SQLite connections. Responses include source evidence, dates and coverage limits where applicable. Routing uses published directional stop sequences; nearest-stop distances are geometric. The reviewed alias catalog is [reviewed_name_aliases_v1.json](data/nlp_v2/reviewed_name_aliases_v1.json). `src/entity_extractor.py` supplies a shared gazetteer and `src/normalization.py` supplies text normalization.

## API contract

`python -m app.api` starts the single-threaded local server on `127.0.0.1:8765`. It loads the exact selected checkpoint and pinned tokenizer/config before serving; a missing or invalid asset fails startup.

- `GET /health` reports T3 readiness.
- `POST /api/v2/query` accepts a nonempty `query` and optional `transport_mode` in a JSON body of at most 8,192 bytes.
- Assistant statuses are `ok`, `clarification`, `unavailable`, `out_of_scope` and `error`.
- Public replies carry `outcome_reason`, `response_text`, `intent`, `operation`, `slots`, `data`, `missing_slots`, `clarification_reason`, `candidate_entities` and `candidate_intents`, alongside `status`. Validation/availability errors have a smaller safe envelope.
- Raw/normalized questions, model confidence and exception details are omitted from the response.

## Frontend

`app/streamlit_app.py` calls the API through `app/frontend_contract.py`. `app/frontend_language.py` provides English, Hindi and Hinglish presentation, and `app/transit_theme.html` supplies the visual theme. History, drafts, the selected mode and accepted request state survive UI reruns and language changes. Questions are sent unchanged; display language does not select a different model. An explicit question mode takes priority over the selected default.

See [model setup](docs/MODEL_SETUP.md), [data sources](DATA_SOURCES.md) and [known limitations](docs/KNOWN_LIMITATIONS.md).
