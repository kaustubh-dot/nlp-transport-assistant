# NLP Transport Assistant

A local Chennai public transport assistant with a 16-intent MuRIL classifier, deterministic request handling, a canonical SQLite transit snapshot, a JSON API, and a Streamlit chat interface. Answers identify published records and ask for clarification when the request is ambiguous or incomplete.

## Capabilities

- Published route candidates, stop sequences and route membership.
- First/last service, scheduled departures and frequency where records support them.
- Dated metro fares, bus stage fares, and straight-line nearest-stop searches.
- Explicit clarification, unavailable, out-of-scope and error responses.
- Language and transport-mode selection with preserved chat history and drafts.

Questions may use English, Hindi, Roman Hindi, Hinglish or mixed script. The interface offers English, हिंदी and Hinglish; recognition and translated presentation have limitations. Modes are Bus, Metro, suburban Rail and MRTS, with source coverage varying by mode.

## Architecture

The UI calls the local API, which uses `T3Assistant` in `src/nlp_v2`. The selected model classifies the original question; deterministic extraction resolves slots and canonical entities, then dispatches to read-only transit operations. Responses expose uncertainty and source limits. See [architecture](ARCHITECTURE.md) and [data sources](DATA_SOURCES.md).

## Setup

Use Python 3.12 and run commands from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
export HF_HOME="$PWD/.cache/huggingface"
```

The required selected checkpoint is **950,358,409 bytes** and is supplied separately by the project owner. Put the exact file at `experiments/nlp_v2/gate_b2/t3_muril_seed42_best.pt`; this local asset is excluded from Git. The tracked canonical database is ready to use. Follow [model setup](docs/MODEL_SETUP.md) to prepare the pinned tokenizer/config cache and validate the checkpoint:

```bash
python -m scripts.nlp_v2.validate_model_artifact --load-model
```

## Run

Start the API:

```bash
python -m app.api
```

In a second terminal, activate the same environment, set the same `HF_HOME`, and start the UI:

```bash
streamlit run app/streamlit_app.py --server.address=127.0.0.1
```

Open `http://127.0.0.1:8501`. The API uses `http://127.0.0.1:8765`; `NLP_V2_API_URL` can configure the UI's API address. Keep both services local. The API exposes `GET /health` and `POST /api/v2/query`; each clarification requires a revised complete question.

## Tests

Install the test dependency and run the suite with the required checkpoint and tokenizer cache available:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Verified local result: **2,247 passed, 0 failed, 0 skipped, 0 xfailed in 51.75 seconds** (Python 3.12; required model assets present).

The suite covers production contracts, transit operations, multilingual safety regressions, API/UI behavior and strict real-checkpoint inference. Regression results do not establish broad population-level accuracy.

## Limitations and license

Transit data is a published/static snapshot, with variable coverage and dated fares and schedules. It must not be presented as live operational information. Hindi/Hinglish recognition remains limited; live delays, verified cross-mode transfers, and many facility/accessibility/policy facts are unavailable. Verify travel information with the operator. See [known limitations](docs/KNOWN_LIMITATIONS.md).

Code is [MIT licensed](LICENSE). External data and model terms are separate; public availability does not imply unrestricted redistribution.
