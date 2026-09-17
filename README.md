# Hindi Transport Assistant for Chennai

A local Hindi/Hinglish text prototype using intent classification, gazetteer slot extraction, SQLite lookups and deterministic Hindi responses.

**Current status: unverified demonstration data.** The bundled transport records are hardcoded fixtures, not an imported official feed. Do not use them as current travel guidance. Deterministic templates do not guarantee factual accuracy.

See [PRD.md](PRD.md) for MVP boundaries and measurable release gates, [ARCHITECTURE.md](ARCHITECTURE.md) for the implemented contract, [ROADMAP.md](ROADMAP.md) for sequencing, and [DATA_SOURCES.md](DATA_SOURCES.md) for outstanding source verification.

## Scope
The first verified release targets selected Metro routes and individual facilities. Current demo fixtures also include bus/suburban examples. Lookup covers only stored pairs, not arbitrary routing. Timetables, fares, ticket rules and live status return an explicit limitation. Speech and translation are deferred. Each question must be self-contained.

## Local setup (Python 3.12)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.build_transport_db
python -m scripts.generate_intent_dataset
python -c "from src.intent_classifier import train_baseline; train_baseline()"
python -m scripts.evaluate --model baseline
python -m pytest -q
streamlit run app/streamlit_app.py
```

Database generation replaces `data/processed/transport.db` with demo fixtures. Training replaces `models/baseline/model.pkl`. Synthetic rows carry template-family splits; slot columns are unreviewed hints, not gold labels. The evaluator reports intent metrics only and refuses heuristic fallback. The UI can still run without weights using explicitly identified heuristic predictions.

## Examples
- `चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?`: returns a stored demo route, without estimating fare.
- `कोयम्बेडु पर व्हीलचेयर उपलब्ध है?`: reads the wheelchair field only, with a demo warning.
- `आखिरी मेट्रो कब छूटती है?`: explains that verified timetables are unavailable.
- `central se airport kaise jaye`: accepts Roman Hindi.

## Dependencies and license
Core dependencies are pinned in requirements.txt; the lightweight baseline does not require PyTorch. Transformer training and its environment remain a later milestone. Code is MIT licensed. External data/model licensing must be verified per artifact before distribution; no blanket license claim applies to the demonstration records.
