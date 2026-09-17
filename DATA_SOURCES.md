# Data and License Register (DATA_SOURCES.md)

This document formally records every external dataset, open transit feed, pretrained model, and lexical resource utilized in the **Hindi Multimodal Transport Assistant for Chennai Using NLP**.

All components comply with the project's zero-cost, open-source requirement.

---

## Data & Model Registry

| Resource Name | Source URL | Purpose in Project | License / Terms | Attribution Required | Processing & Transformation Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Amazon MASSIVE (Hindi split)** | [Hugging Face `AmazonScience/massive`](https://huggingface.co/datasets/AmazonScience/massive) | Seed natural Hindi utterances for transport and out-of-scope intent training | CC-BY-4.0 | Yes (Cite Amazon Science) | Filtered for Hindi (`hi-IN`) split. Selected transport domain queries (`transport_query`, `transport_ticket`, `transport_taxi`) and general domain queries for `out_of_scope`. |
| **CUMTA Transit Portal** | [cumta.tn.gov.in](https://cumta.tn.gov.in/) | Official static GTFS repository for Chennai public transport (Metro, MTC, Suburban Rail) | Open Public Transit Data (ODbL / Government Open Data) | Yes (Chennai Unified Metropolitan Transport Authority) | Extracted static routes, stops, coordinates, and trip frequencies for Metro and Suburban Rail networks. |
| **ChennaiGTFS (Fallback)** | [GitHub `ChennaiGTFS`](https://github.com/ChennaiGTFS) | Fallback community GTFS representation of MTC buses and Chennai Metro | Open Database License (ODbL) | Yes (ChennaiGTFS Contributors) | Utilized as cross-reference for bus stop naming conventions and route aliases. |
| **OpenStreetMap (OSM)** | [openstreetmap.org](https://www.openstreetmap.org/) | Station geographic coordinates, physical entrances, platforms, and interchange landmarks | Open Database License (ODbL) | Yes (© OpenStreetMap contributors) | Overpass API / OSM extracts filtered for `railway=station`, `railway=subway_entrance`, and `public_transport=stop_position` in Chennai metropolitan region. |
| **Chennai Metro Rail Limited (CMRL) Station Pages** | [chennaimetrorail.org](https://chennaimetrorail.org/) | Official station accessibility features, lifts, escalators, and wheelchair availability | Public Informational Domain | Yes (Reference source URL) | Only factual structured attributes (lift availability, wheelchair access, parking, first/last train timings) extracted. No proprietary copyrighted text copied. |
| **MuRIL (Multilingual Representations for Indian Languages)** | [Hugging Face `google/muril-base-cased`](https://huggingface.co/google/muril-base-cased) | Primary pretrained transformer for Hindi and Hinglish intent classification | Apache License 2.0 | Yes (Google Research) | Fine-tuned locally on `data/processed/intents.csv` for sequence classification into 7 transport intents. |
| **IndicBERTv2 (Alternative)** | [Hugging Face `ai4bharat/IndicBERTv2-MLM-only`](https://huggingface.co/ai4bharat/IndicBERTv2-MLM-only) | Comparative pretrained Indic language model | MIT License | Yes (AI4Bharat) | Evaluated as an alternative baseline for Indic language tokenization and intent detection. |
| **IndicTrans2 (Optional Extension)** | [GitHub `AI4Bharat/IndicTrans2`](https://github.com/AI4Bharat/IndicTrans2) | Hindi-to-Tamil translation module for generated transport responses | MIT License / CC-BY-4.0 | Yes (AI4Bharat) | Modular translation inference checkpoint for cross-state linguistic accessibility. |
| **IndicConformer (Optional Extension)** | [Hugging Face `ai4bharat/indicconformer`](https://huggingface.co/ai4bharat/indicconformer) | Open Hindi Automatic Speech Recognition (ASR) | MIT License | Yes (AI4Bharat) | Offline ASR inference pipeline converting passenger audio queries into Hindi text. |
| **Indic-TTS (Optional Extension)** | [GitHub `AI4Bharat/indic-tts`](https://github.com/AI4Bharat/indic-tts) | Open Indic Text-to-Speech synthesis | MIT License | Yes (AI4Bharat) | Audio synthesis module converting generated Hindi/Tamil responses into spoken audio. |

---

## Verification & Compliance Checklist

- [x] **No Commercial APIs**: Zero dependencies on OpenAI, Anthropic, Google Gemini API, Azure Cognitive Services, or paid Google Maps APIs.
- [x] **No Paid Cloud Infrastructure**: All training and inference runs locally on consumer or workstation hardware (tested on local NVIDIA RTX 4000 Ada Generation GPU).
- [x] **Permissive Model Checkpoints**: All model checkpoints (MuRIL, IndicTrans2, IndicConformer) carry Apache-2.0 or MIT licenses permitting research and educational use.
- [x] **Data Privacy**: No user PII (Personally Identifiable Information) collected or stored.
- [x] **Attribution**: Proper attribution statements are integrated into the documentation and user-facing interface.
