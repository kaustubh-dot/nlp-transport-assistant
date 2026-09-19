# DECISION REQUIRED: Chennai Multimodal Multilingual NLP v2 (Gate A Sign-Off)

Date: 2026-09-19  
Project: Chennai Multimodal Public Transport Assistant (`nlp-transport-assistant`)  
Knowledge Base Snapshot: `chennai_multimodal_v1.2.1`  
Deliverables Produced: Phases N0 through N8 (`docs/nlp_v2/*` and `reports/nlp_v2/*`)

---

## Decision 1: Intent Taxonomy Selection Strategy for Gate B

### Topic:
Whether to execute an empirical pilot experiment comparing Taxonomies T1 (Broad, 9 classes), T2 (Medium, 12 classes), and T3 (Fine, 16 classes), or approve T2 directly.

### Why a decision is required:
The intent taxonomy defines the boundary of all downstream dataset synthesis, slot contracts, model training, and task fulfillment. Selecting an intent taxonomy without empirical verification carries the risk of choosing an over-fragmented or ambiguous intent space. However, running a three-way pilot requires creating small pilot template sets and running comparative model training.

### Option A (Recommended): Conduct Controlled Three-Taxonomy Empirical Pilot
- **Benefits**:
  - Quantifies real model learnability and boundary confusion matrices across T1, T2, and T3 on identical underlying transit scenarios.
  - Compares taxonomies under two controlled experimental regimes:
    - **Regime A (Equal Total Budget)**: Fixed ~5,000 samples per taxonomy (~555/intent for T1, ~417/intent for T2, ~312/intent for T3) to evaluate information packing and efficiency under a fixed budget.
    - **Regime B (Equal Class Density)**: Fixed ~500 samples per intent class (4,500 for T1, 6,000 for T2, 8,000 for T3) to evaluate intrinsic class boundary separability without sample starvation.
  - Defends the final taxonomy choice with concrete empirical evidence rather than theoretical preference.
  - Satisfies Gate B requirement in Section 71 of the master specification.
- **Risks**:
  - Requires generating pilot datasets and training reference models (TF-IDF and MuRIL across seeds `[42, 101, 777]`) before freezing the full corpus.

### Option B: Formally Approve Taxonomy T2 (Medium, 12 Intents) Directly
- **Benefits**:
  - Eliminates pilot overhead; advances directly to full-scale dataset generation on the 12-intent schema.
  - T2 already incorporates key operational requirements: separating tariff calculation from policy questions, adding explicit interchange queries, and isolating live-tracking queries.
- **Risks**:
  - Bypasses empirical verification of class boundary separability on transformer embeddings.

### Option C: Formally Approve Taxonomy T1 (Broad, 9 Intents) Directly
- **Benefits**:
  - Maximum sample efficiency and highest anticipated Macro-F1 score.
  - Simpler classifier with fewer failure boundaries.
- **Risks**:
  - Requires heavier slot extraction complexity to resolve downstream operations (for example, distinguishing fare lookup from card recharge rules within `fare_and_ticketing`).

### Agent Recommendation:
**Option A**. Conduct the controlled empirical pilot across T1, T2, and T3 across both Regime A and Regime B using TF-IDF and MuRIL with seeds `[42, 101, 777]`.

### Evidence:
Historical benchmark data demonstrated that fine-grained intent boundaries in Hinglish (such as distinguishing timing from availability) produced confusion in XLM-RoBERTa and HingBERT. An empirical pilot provides ground-truth confusion matrices before investing compute in generating 40,000+ samples.

### What changes depending on decision:
- If Option A is approved: The next phase (Gate B) implements `scripts/nlp_v2/pilot/` to generate pilot data for both regimes and evaluate T1/T2/T3 models.
- If Option B or C is approved: The pilot phase is bypassed, and we proceed directly to generating the full candidate corpus for the chosen taxonomy.

### Resume Point:
Phase P1 (Gate B: Taxonomy Pilot Implementation).

---

## Decision 2: Handling of Real-Time Transit Queries (`realtime_status_query`)

### Topic:
Classification and response strategy for commuter queries requesting live vehicle locations, real-time delays, or dynamic tracking.

### Why a decision is required:
Commuters frequently ask "Where is bus 102 right now?" or "Is metro running late?". The canonical knowledge base (`chennai_multimodal_v1.2.1`) has static timetables and topologies, but zero live GPS telemetry. The system must never hallucinate live positions. User intent must describe communicative goal, while capability state describes system execution.

### Option A (Recommended): Dedicated Intent `realtime_status_query` with Capability `REQUIRES_REALTIME_DATA`
- **Benefits**:
  - Separates transit queries asking for live tracking from general non-transit queries (food, cabs, weather).
  - Preserves legitimate transit entity annotations (`route_code`, `stop`, `mode`) rather than wiping them.
  - Enables informative, helpful refusals: "Live GPS tracking for MTC buses is not currently available; scheduled departure from this stop is 17:15."
  - Explicitly measures real-time status query detection and refusal accuracy as an independent metric.
- **Risks**:
  - Adds one intent class to the model taxonomy in T2 and T3.

### Option B: Fold into Generic `out_of_scope` Class
- **Benefits**:
  - Keeps intent taxonomy smaller (11 intents for T2) and matches historical CMRL benchmark structure.
- **Risks**:
  - Produces generic, unhelpful responses to legitimate transit questions.
  - Makes it difficult to diagnose whether the model failed on domain boundary or live-status boundary.

### Option C: Deterministic Pre-Classification Keyword / Regex Filter
- **Benefits**:
  - Intercepts known live keywords (`kahan pahuchi`, `live status`, `late hai kya`) before the neural model without dedicated training.
- **Risks**:
  - Brittle under novel Hinglish phrasing or spelling variations; cannot leverage transformer contextual semantics.

### Agent Recommendation:
**Option A**. Use the dedicated semantic intent `realtime_status_query` with capability state `REQUIRES_REALTIME_DATA` (or `REJECT_UNSUPPORTED`).

### Evidence:
The answerability audit confirmed that live vehicle tracking is the single most common cause of hallucination in transit assistants. Explicitly modeling this intent enables targeted safety evaluation.

### What changes depending on decision:
Affects intent count in Taxonomy T2 (12 vs 11 intents) and utterance generation templates for real-time status queries.

### Resume Point:
Phase P1 (Gate B: Pilot Generation).

---

## Decision 3: Gate B Pilot Evaluation Regimes and Scale

### Topic:
Experimental regimes and target sample counts for candidate taxonomies (T1, T2, T3) in the empirical pilot study.

### Why a decision is required:
Comparing taxonomies of different sizes (9, 12, 16 classes) on a single arbitrary data size can confound sample density per class with intrinsic semantic separability.

### Option A (Recommended): Dual Controlled Regimes (Regime A Equal Total Budget + Regime B Equal Class Density)
- **Benefits**:
  - **Regime A (Equal Total Budget ~5,000 samples)**: T1 = 5,000 (~555/intent), T2 = 5,000 (~417/intent), T3 = 5,000 (~312/intent). Answers: Which taxonomy performs best under a fixed annotation and training budget?
  - **Regime B (Equal Class Density ~500/intent)**: T1 = 4,500, T2 = 6,000, T3 = 8,000. Answers: How do the taxonomies compare when each class has equal representation and statistical power?
  - Evaluated across seeds `[42, 101, 777]` with paired McNemar and bootstrap tests on matched predictions.
  - Disentangles sample starvation from class boundary geometry.
- **Risks**:
  - Requires training 12 experimental runs per model type (3 taxonomies x 2 regimes x 2 model families x 3 seeds) using fast training protocols (<15 minutes total on RTX 4000 Ada GPU).

### Option B: Single Regime A Only (Equal Total Budget ~5,000 Samples)
- **Benefits**:
  - Half the number of pilot runs.
- **Risks**:
  - Disadvantages T3 because 16 classes receive only ~312 samples each, confounding class granularity with class starvation.

### Option C: Single Regime B Only (Equal Class Density ~500 Samples/Intent)
- **Benefits**:
  - Ensures each intent has sufficient statistical representation.
- **Risks**:
  - T3 receives 8,000 samples while T1 receives 4,500, introducing total data volume as a confounding variable.

### Agent Recommendation:
**Option A** (Dual Controlled Regimes A and B).

### What changes depending on decision:
Pilot generator generates both fixed-budget and fixed-density splits for Gate B evaluation scripts.

### Resume Point:
Phase P1 (Gate B: Pilot Generation).
