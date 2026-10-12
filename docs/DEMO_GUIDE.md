# Five-minute academic demo

Use the **TF-IDF baseline** first. It has the stronger validation result. MuRIL remains available for the model comparison; it does not automatically improve every question.

## Start

From the repository root, with the existing environment and generated models:

```bash
.venv/bin/python -m streamlit run app/streamlit_app.py --server.address=127.0.0.1 --server.port=18505 --server.fileWatcherType=none --browser.gatherUsageStats=false
```

Open `http://127.0.0.1:18505`. If the demo is already running there, use that instance. Inference is local and needs no live transport API. The MuRIL option requires the neural dependencies and verified release assets; see [model setup](MODEL_SETUP.md).

Use a quick example or the example selector to fill a question, then submit it. Examples never run the model automatically or rewrite an existing draft when the display language changes. “New question” clears the current draft/result. Model selection and station context are in the side rail; open it with the arrow on smaller screens. The rail also keeps the five most recent submitted questions for this browser session. Selecting one restores its text for editing and waits for submission. The answer shows source information and a compact NLP slot panel; raw records remain in an expander. Expand the same-question comparison below a result and press its button to run both models. The comparison uses the submitted question, even if a new draft is waiting in the input.

## Presentation order

| Time | What to show | What to explain |
| --- | --- | --- |
| 0:00–0:30 | Title and selected locations | An academic Hindi/Hinglish NLP transport case study with a small catalog |
| 0:30–1:30 | `चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या?` | Actual predicted intent, origin/destination/mode, published Metro record and Hindi response |
| 1:30–2:00 | Switch to Hinglish | The raw query and model result stay the same; response presentation changes |
| 2:00–2:45 | `Tambaram se Guindy ke liye bus available hai kya?` | Availability intent, bus 51A stop-sequence snapshot, boarding/alighting stops and source limits |
| 2:45–3:15 | `Central metro mein lift hai?` | Accessibility feature extraction; the facility record is for Metro, not Railway |
| 3:15–3:45 | `Meri train bahut late hai.` | Live-status intent recognized; no live data is invented |
| 3:45–4:15 | `Train ka toilet ganda hai.` | Complaint intent and cleanliness type; guidance rather than complaint submission |
| 4:15–4:45 | `Chennai Central se Mambalam station kaise jau?` | Both names recognized; same-name/mode ambiguity is exposed. Qualify railway stations to show the missing rail-route records |
| 4:45–5:00 | Evaluation expander and model selector | Baseline versus partially fine-tuned MuRIL; generated-data results have limits |

If asked about timings, show `Subah sabse pehle train guindy se chennai central kab hai?`. It is a scheduled-time query, and the requested rail timetable is absent. The 2024 Metro terminal-window example is historical and cannot answer this question.

## Your four questions

- `Guindy se Central kaise jayein?` — route intent; published Blue Line Metro connection.
- `Velachery se Park station kaise jayein?` — route intent; both names recognized. Park/Park Town and bus/rail variants need clarification.
- `Chennai Central se Mambalam station kaise jau?` — route intent; both names recognized. `Chennai Central railway station se Mambalam railway station train se kaise jau?` resolves railway IDs; the snapshot has no rail-route sequence.
- `Subah sabse pehle train guindy se chennai central kab hai?` — timing intent; no current rail timetable for this pair.

Both final models classify these four intents correctly. These are development-exposed qualitative checks, not an unseen accuracy benchmark. Keep exact outputs and original failures in the [pipeline report](PIPELINE_EVALUATION.md).

## Explain the NLP work

The baseline uses character TF-IDF features and Logistic Regression. MuRIL reuses the existing checkpoint and fine-tunes its last two layers plus a nine-class head. Both train on the same 1,112 training rows; MuRIL epoch selection uses 216 validation rows. The test partition has 324 generated questions. Entity extraction uses a gazetteer and role/mode rules, not learned NER. Comparison scores are uncalibrated and must not be interpreted as directly comparable accuracy estimates.

## Additional natural questions

- `Chennai Central se velachery kaise jayein?` — a sourced rail option names Park Town MRTS as the separate boarding station. No mode prompt or direct Central-to-Velachery train is invented.
- `Velachery station ke paas bus stop kaunsa h?` — bus-stop options around the MRTS station, with straight-line distance and access caveats.
- `वेलाचेरी स्टेशन के पास बस स्टॉप कौन सा है?` — the equivalent Hindi lookup.
- `Central se Velachery bus se kaise jau?` — published bus options with the actual General Hospital/Central boarding-stop name and partial-topology notice.
- `Central se Velachery metro se kaise jayein?` — explicit missing Metro coverage; the chosen mode is not requested again or replaced with MRTS.
- `Guindy metro station ke paas bus stop kaunsa hai?` — official associated bus-stop names are returned; conflicting station coordinates prevent a reliable distance estimate. This is a source-data issue, not an intent or mode error.

The [project report](PROJECT_REPORT.md), [classification results](NLP_EVALUATION.md) and [pipeline diagnostic](PIPELINE_EVALUATION.md) contain the measured results. Do not describe generated-data scores as real-passenger reliability. Tamil phrases are optional, unreviewed drafts; leave the phrasebook collapsed unless specifically discussing future communication support.
