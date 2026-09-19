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
  - Defends the final taxonomy choice with concrete empirical evidence rather than theoretical preference.
  - Satisfies Gate B requirement in Section 71 of the master specification.
- **Risks**:
  - Requires generating three small pilot datasets (~2,000 samples each) and training reference models before freezing the full corpus.

### Option B: Formally Approve Taxonomy T2 (Medium, 12 Intents) Directly
- **Benefits**:
  - Eliminates pilot overhead; advances directly to full-scale dataset generation on the 12-intent schema.
  - T2 already incorporates key operational requirements: separating tariff calculation from policy questions, adding explicit interchange queries, and isolating live-tracking refusals.
- **Risks**:
  - Bypasses empirical verification of class boundary separability on transformer embeddings.

### Option C: Formally Approve Taxonomy T1 (Broad, 9 Intents) Directly
- **Benefits**:
  - Maximum sample efficiency and highest anticipated Macro-F1 score.
  - Simpler classifier with fewer failure boundaries.
- **Risks**:
  - Requires heavier slot extraction complexity to resolve downstream operations (e.g. distinguishing fare lookup from card recharge rules within `fare_and_ticketing`).

### Agent Recommendation:
**Option A**. Conduct the controlled empirical pilot across T1, T2, and T3 on small datasets (~2,000 samples each) using TF-IDF and MuRIL.
### Evidence:
Historical benchmark data demonstrated that fine-grained intent boundaries in Hinglish (e.g. distinguishing timing from availability) produced confusion in XLM-RoBERTa and HingBERT. An empirical pilot provides ground-truth confusion matrices before investing compute in generating 40,000+ samples.

### What changes depending on decision:
- If Option A is approved: The next phase (Gate B) implements `scripts/nlp_v2/pilot/` to generate pilot data and compare T1/T2/T3 models.
- If Option B or C is approved: The pilot phase is bypassed, and we proceed directly to generating the full candidate corpus for the chosen taxonomy.

### Resume Point:
Phase P1 (Gate B: Taxonomy Pilot Implementation).

---

## Decision 2: Handling of Unsupported Real-Time Queries

### Topic:
Classification and response strategy for commuter queries requesting live vehicle locations, real-time delays, or dynamic tracking.

### Why a decision is required:
Commuters frequently ask "Where is bus 102 right now?" or "Is metro running late?". The canonical knowledge base (`chennai_multimodal_v1.2.1`) has static timetables and topologies, but zero live GPS telemetry. The system must never hallucinate live positions.

### Option A (Recommended): Dedicated Intent `unsupported_live_status`
- **Benefits**:
  - Explicitly separates transit questions that fail due to missing telemetry from non-transit questions (weather, food, cabs).
  - Enables informative, helpful refusals: "Live GPS tracking for MTC buses is not currently available; scheduled departure from this stop is 17:15."
  - Explicitly measures rejection accuracy as an independent metric.
- **Risks**:
  - Adds one additional intent class to the model taxonomy.

### Option B: Fold into Generic `out_of_scope` Class
- **Benefits**:
  - Keeps intent taxonomy smaller and aligns with historical CMRL benchmark structure.
- **Risks**:
  - Produces generic, unhelpful responses to legitimate transit questions.
  - Makes it difficult to diagnose whether the model failed on domain boundary or live-status boundary.

### Option C: Deterministic Pre-Classification Keyword / Regex Filter
- **Benefits**:
  - Zero model training required for live-status refusal; intercepts known live keywords (`kahan pahuchi`, `live status`, `late hai kya`) before the neural model.
- **Risks**:
  - Brittle under novel Hinglish phrasing or spelling variations; cannot leverage transformer contextual semantics.

### Agent Recommendation:
**Option A**. Use a dedicated intent `unsupported_live_status` in Taxonomy T2.
### Evidence:
The answerability audit confirmed that live vehicle tracking is the single most common cause of hallucination in transit assistants. Explicitly modeling this intent enables targeted safety evaluation.

### What changes depending on decision:
Affects intent count in Taxonomy T2 (12 vs 11 intents) and utterance generation templates for negative sampling.

### Resume Point:
Phase P1 (Gate B: Pilot Generation).

---

## Decision 3: Initial Pilot Dataset Scale for Gate B

### Topic:
Target sample count per candidate taxonomy for the empirical pilot study.

### Why a decision is required:
A pilot must balance sufficient sample diversity across languages and classes with minimal compute expenditure.

### Option A (Recommended): 2,000 Samples per Candidate Taxonomy (6,000 Total)
- **Benefits**:
  - Provides ~150-200 samples per intent class across 5 languages.
  - Fast generation and training (<5 minutes per run on RTX 4000 Ada GPU).
  - Sufficient statistical power to detect class confusion pairs.
- **Risks**:
  - Tail entities will not be extensively covered in the pilot (focused on Head/Mid entities).

### Option B: 5,000 Samples per Candidate Taxonomy (15,000 Total)
- **Benefits**:
  - Greater entity diversity and deeper code-switch coverage.
- **Risks**:
  - Slower iteration cycle for pilot phase.

### Option C: 1,000 Samples per Candidate Taxonomy (3,000 Total)
- **Benefits**:
  - Near-instant training.
- **Risks**:
  - Too few samples per intent class (~60-80) to produce stable confusion matrices across 5 languages.

### Agent Recommendation:
**Option A** (~2,000 samples per candidate taxonomy).

### What changes depending on decision:
Parameter `pilot_samples_per_intent` in the pilot generator configuration.

### Resume Point:
Phase P1 (Gate B: Pilot Generation).
