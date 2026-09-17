# Hindi Multimodal Transport Assistant for Chennai Using NLP

An open-source, zero-cost Natural Language Understanding (NLU) transport assistant designed to help Hindi-speaking passengers navigate Chennai's public transportation network (Chennai Metro, Suburban Railway, and MTC buses).

The system accepts natural-language questions in Unicode Hindi or Romanized Hindi (Hinglish), determines user intent, extracts transport entities (origin, destination, transport mode), queries a local transit SQLite database, and returns clear, factual Hindi responses without relying on paid APIs, commercial mapping platforms, or external generative LLMs.

---

## Key Features

- **Hindi & Hinglish NLU**: Handles formal Hindi (`चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ?`), colloquial queries, and Roman script transliterations (`central se airport metro hai kya`).
- **Constrained Intent Taxonomy**: 7 well-defined user intents:
  - `route_query` (route navigation between stations)
  - `service_availability` (checks whether direct connectivity exists)
  - `service_timing` (first/last service and operating hours)
  - `station_information` (station facilities and interchange options)
  - `accessibility` (lifts, wheelchair ramps, accessible gates, tactile paths)
  - `ticketing` (fare info, smart cards, token rules)
  - `out_of_scope` (graceful rejection of non-transport questions)
- **Gazetteer-Driven Slot Extraction**: Fast, deterministic extraction using alias lookup tables and RapidFuzz fuzzy matching for Chennai transit hubs.
- **Local Structured Transport DB**: Lightweight SQLite database compiled from official CUMTA/CMRL static GTFS, OpenStreetMap (OSM), and official station facility records.
- **Zero Hallucination & ₹0 Cost**: Rule- and template-based Hindi response generation ensuring deterministic, factual outputs.
- **Hardware Optimized**: Fully runnable on local CPU or GPU (supports NVIDIA Ada / Ampere GPUs for fast MuRIL fine-tuning and inference).
- **Extensible Multimodal Architecture**: Optional plug-and-play stubs for IndicTrans2 (Hindi to Tamil translation) and IndicConformer / Indic-TTS.

---

## Architecture Overview

```text
       User Query (Hindi / Hinglish)
                     │
                     ▼
        [1. Text Normalization]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 [2. Intent Classifier]  [3. Slot Extractor]
 (TF-IDF Baseline /       (Gazetteer + RapidFuzz
  Fine-tuned MuRIL)        Alias Matching)
         │                       │
         └───────────┬───────────┘
                     ▼
          [4. Query Interpreter]
                     │
                     ▼
          [5. Local SQLite DB]
         (Metro, Rail, MTC, Accessibility)
                     │
                     ▼
     [6. Hindi Response Generator]
        (Deterministic Templates)
                     │
                     ▼
          User (Streamlit Web UI)
```

---

## Repository Structure

```text
nlp-transport-assistant/
├── README.md                      # Project overview, setup, and quickstart
├── ROADMAP.md                     # 6-Phase implementation roadmap
├── TODO.md                        # Granular task checklist & development status
├── DATA_SOURCES.md                # Open licenses, attribution, and dataset register
├── ARCHITECTURE.md                # Detailed technical and schema design document
├── requirements.txt               # Python package dependencies
├── .gitignore                     # Git exclusion rules
│
├── app/
│   └── streamlit_app.py           # Streamlit web UI application
│
├── data/
│   ├── raw/                       # Original downloaded datasets
│   │   ├── gtfs/                  # Static GTFS feeds (CUMTA / ChennaiGTFS)
│   │   ├── massive/               # Amazon MASSIVE Hindi seed corpus
│   │   └── osm/                   # OpenStreetMap extracts
│   ├── processed/                 # Generated artifacts
│   │   ├── transport.db           # SQLite transit database
│   │   ├── aliases.csv            # Station gazetteer & multilingual alias table
│   │   └── intents.csv            # Processed NLU training dataset
│   └── templates/
│       └── hindi_templates.json   # Intent generation patterns & response templates
│
├── src/
│   ├── __init__.py
│   ├── normalization.py           # Unicode & text preprocessing
│   ├── entity_extractor.py        # Gazetteer & fuzzy matching engine
│   ├── intent_classifier.py       # TF-IDF & MuRIL classifier wrappers
│   ├── retrieval.py               # SQLite transit querying module
│   └── response_generator.py      # Deterministic response constructor
│
├── scripts/
│   ├── download_data.py           # Fetch open-source datasets & GTFS feeds
│   ├── build_transport_db.py      # Compile SQLite database from raw feeds
│   ├── generate_intent_dataset.py # Synthesize NLU dataset from templates & seeds
│   └── evaluate.py                # Model evaluation (Accuracy, F1, Success Rate)
│
├── models/
│   ├── baseline/                  # Saved TF-IDF + Logistic Regression artifacts
│   └── muril/                     # Fine-tuned MuRIL transformer weights
│
├── notebooks/
│   ├── data_analysis.ipynb        # Exploratory analysis of transit & intent data
│   └── model_training.ipynb       # Transformer fine-tuning workflow
│
└── tests/
    ├── __init__.py
    ├── test_normalization.py
    ├── test_entity_extractor.py
    ├── test_retrieval.py
    └── test_pipeline.py
```

---

## Quickstart Guide

### 1. Environment Setup
Clone the repository and create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Build Transport Database & Gazetteer
Generate the SQLite database from curated Chennai transit records:
```bash
python3 scripts/build_transport_db.py
```

### 3. Synthesize the NLU Intent Dataset
Generate training, validation, and test datasets with domain-specific templates and MASSIVE seeds:
```bash
python3 scripts/generate_intent_dataset.py
```

### 4. Train the Baseline and MuRIL Classifiers
```bash
# Baseline TF-IDF + Logistic Regression
python3 -c "from src.intent_classifier import train_baseline; train_baseline()"

# Evaluate Models
python3 scripts/evaluate.py --model baseline
```

### 5. Launch the Streamlit Web Application
```bash
streamlit run app/streamlit_app.py
```

---

## Example Queries & Expected Outputs

| Input Query | Predicted Intent | Extracted Entities | Generated Hindi Response |
| :--- | :--- | :--- | :--- |
| चेन्नई सेंट्रल से एयरपोर्ट कैसे जाऊँ? | `route_query` | origin: Chennai Central, destination: Airport | चेन्नई सेंट्रल से चेन्नई एयरपोर्ट जाने के लिए आप ब्लू लाइन मेट्रो ले सकते हैं। यात्रा में लगभग 40 मिनट लगते हैं। |
| सेंट्रल से गिंडी के लिए मेट्रो है क्या? | `service_availability` | origin: Central, destination: Guindy, mode: metro | हाँ, चेन्नई सेंट्रल से गिंडी के बीच सीधी मेट्रो सेवा उपलब्ध है। |
| कोयम्बेडु स्टेशन पर व्हीलचेयर मिलेगी? | `accessibility` | station: Koyambedu, info: wheelchair | हाँ, कोयम्बेडु मेट्रो स्टेशन पर व्हीलचेयर और रैंप सुविधा उपलब्ध है। सहायता के लिए स्टेशन कंट्रोलर से संपर्क करें। |
| आखिरी मेट्रो कब छूटती है? | `service_timing` | mode: metro, info: last_service | चेन्नई मेट्रो की आखिरी सेवा रात 11:00 बजे टर्मिनल स्टेशनों से प्रस्थान करती है। |
| आज चेन्नई का तापमान क्या है? | `out_of_scope` | - | क्षमा करें, मैं केवल चेन्नई सार्वजनिक परिवहन (मेट्रो, उपनगरीय ट्रेन, बस) से संबंधित प्रश्नों में सहायता कर सकता हूँ। |

---

## License & Attribution

- **Source Code**: Released under the [MIT License](LICENSE).
- **Data & Models**: Amazon MASSIVE (CC-BY-4.0), OpenStreetMap (ODbL), CUMTA/ChennaiGTFS (ODbL), MuRIL (Apache-2.0). See [DATA_SOURCES.md](DATA_SOURCES.md) for detailed citations and license terms.
