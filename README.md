# Hindi and Hinglish transport assistant

An academic NLP project for transport questions in Chennai. A question is classified into one of nine intents, its locations and slots are extracted, and a Hindi or Hinglish answer is built from stored transport records. The interface shows the model output and sources so an evaluator can inspect how the answer was produced.

The project compares a character TF-IDF and Logistic Regression baseline with a partially fine-tuned MuRIL encoder. The baseline is the default because it performed better on the synthetic validation set.

## Run the demo

Use Python 3.12. The baseline, tokenizer, example data and transport database are included in the repository. You do not need to train a model or start an API server.

```bash
git clone https://github.com/kaustubh-dot/nlp-transport-assistant.git
cd nlp-transport-assistant
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app/streamlit_app.py --server.address=127.0.0.1
```

Open <http://127.0.0.1:8501>. On Windows, create the environment with `py -3.12 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1` in PowerShell. Run commands from the repository root.

Choose Hindi or Hinglish, type a question and submit it. Quick examples fill the input for editing. Recent questions are kept for the current session. Changing the display language preserves the question and saved model result. The side rail contains the model selector and optional station context, which applies to phrases such as `इस स्टेशन` or `is station`.

Try these questions:

- `चेन्नई सेंट्रल से एयरपोर्ट के लिए मेट्रो है क्या?`
- `Guindy se Central kaise jayein?`
- `Chennai Central se Velachery kaise jayein?`
- `Velachery station ke paas bus stop kaunsa h?`
- `सेंट्रल मेट्रो में लिफ्ट है?`
- `मेरी ट्रेन बहुत लेट है।`
- `ट्रेन का शौचालय बहुत गंदा है।`

The answer includes its data status, sources and extracted slots. Expand the evidence panel for raw records. The [demo guide](docs/DEMO_GUIDE.md) gives a five-minute presentation sequence.

## Enable MuRIL and model comparison

The two large neural weight files are distributed through a [versioned release](https://github.com/kaustubh-dot/nlp-transport-assistant/releases/tag/submission-models-v1). The download is about 1 GB. Setup verifies each file's size and SHA-256 before installing it. No Hugging Face account, API key or separately supplied private checkpoint is needed.

On Linux or Windows, install CPU PyTorch before the neural requirements:

```bash
python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-neural.txt
python -m scripts.prepare_models
```

On Apple Silicon, install `requirements-neural.txt` directly using a Python 3.12 environment with compatible PyTorch wheels. The verified setup is Linux with CPU inference. The baseline demo does not require PyTorch.

Restart Streamlit after installing the neural dependencies. Select `MuRIL (partial fine-tuning)` or use the comparison button below a submitted answer. Both models run on the same submitted text and station context. [Model setup](docs/MODEL_SETUP.md) explains the files, integrity checks and offline setup.

## Method and results

The nine intents are route queries, service availability, service timing, station information, accessibility, ticketing, train status, railway complaints and out-of-scope questions. Entity extraction uses a canonical gazetteer with Hindi/Hinglish role and mode rules. It is a rule-based extractor; no NER model was trained.

The teaching corpus contains 1,652 intent examples and 320 linked slot examples. Intent splits contain 1,112 training, 216 validation and 324 test rows. Related template families stay in one split. The generated text has not been reviewed by human annotators.

| Model | Synthetic test accuracy | Macro F1 |
| --- | ---: | ---: |
| TF-IDF + Logistic Regression | 0.975 | 0.975 |
| MuRIL, final two layers and nine-class head | 0.781 | 0.780 |

MuRIL starts from an existing transport-trained encoder. The experiment trains its final two layers and a new head for five epochs, selecting the epoch on validation macro F1. The saved tokenizer and encoder preserve the original runtime's outputs. This is a small transfer-learning comparison, and the synthetic scores do not establish accuracy on real passengers' questions.

The [NLP evaluation](docs/NLP_EVALUATION.md) includes per-class results, confusion matrices and errors. A separate [pipeline diagnostic](docs/PIPELINE_EVALUATION.md) checks 90 AI-authored questions and records four user-supplied examples. Those questions were visible during development, so the diagnostic is not a blind benchmark. The [project report](docs/PROJECT_REPORT.md) describes the experiment and limitations.

## Reproduce the experiment

Install the neural dependencies and prepare the models first. The saved models are sufficient for the demo; training is only needed to repeat the experiment. It overwrites the local baseline, head, adapted layers, manifest and evaluation outputs. Fresh training can produce different results because initialization and library behavior can differ from the earlier run.

```bash
python -m scripts.nlp_v2.build_project_dataset
python -m scripts.nlp_v2.train_project
python -m scripts.nlp_v2.evaluate_project
```

Run the software regressions with:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The baseline-only environment skips the PyTorch layer-integrity test. Install the neural requirements to run the complete suite. Tests cover the academic assistant, interface state, model-file integrity and shared canonical lookup rules.

## Data coverage and limits

Name recognition searches the stored railway, Metro, MRTS, bus-stop and landmark records. Route and timetable coverage is incomplete, and duplicate names can require clarification. Recognizing a station does not establish a service between two stations.

Published Metro links, bus stop sequences, selected accessibility facts and Central/Velachery MRTS guidance support the demo. Bus records are snapshot data. The terminal timing example is explicitly dated 16 October 2024. Nearby distances are straight-line distances; walking routes and accessible transfers have not been verified.

The app cannot fetch live train status, book tickets or file railway complaints. It classifies those questions and explains the available guidance. Speech input, general translation and route optimization are outside the implemented scope. The optional Hindi-Tamil phrasebook contains five fixed phrases that still need Tamil-speaker review.

See [data coverage](docs/DATA_COVERAGE.md), [sources](DATA_SOURCES.md), the [annotation guide](data/project/ANNOTATION_GUIDE.md) and [known limitations](docs/KNOWN_LIMITATIONS.md).

## Repository layout

```text
app/                    Streamlit interface and preserved theme
src/hindi_project/      Nine-intent models, extraction, lookup and answers
src/nlp_v2/             Shared canonical resolver, slots and transport service
scripts/                Model setup, dataset generation, training and evaluation
data/                   Canonical database, aliases and teaching datasets
models/                 Manifest, baseline, small head, tokenizer and results
docs/                   Report, evaluation, data notes and demo guide
tests/                  Regressions for the submitted components
```

Code is [MIT licensed](LICENSE). MuRIL's Apache 2.0 license and model attribution are in [model notices](models/NOTICE.md). Transport data has separate source terms recorded in [data sources](DATA_SOURCES.md).
