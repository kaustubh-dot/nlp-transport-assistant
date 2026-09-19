# Multimodal Multilingual Evaluation Protocol (Phase N7)

Document: `docs/nlp_v2/evaluation_protocol.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Evaluation Protocol

---

## 1. Six-Layer Evaluation Framework

To prevent opaque aggregation, the evaluation protocol assesses performance across six distinct architectural layers:

```
+-------------------------------------------------------------------------+
| LAYER 1: INTENT CLASSIFICATION                                          |
| Macro-F1, Accuracy, Per-Class F1, Confusion Matrix, OOS Calibration     |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| LAYER 2: SLOT SPAN EXTRACTION                                           |
| Span Strict F1 (BIO boundary), Exact Slot-Set Match, Per-Slot F1        |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| LAYER 3: CANONICAL ENTITY RESOLUTION                                    |
| Top-1 Canonical Accuracy, Top-3 Accuracy, Ambiguity Rate, Unresolved Rate|
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| LAYER 4: TRANSPORT KB RETRIEVAL & ROUTING                               |
| Table Hit Rate, Correct Routing Graph Path, Fare Stage Consistency      |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| LAYER 5: END-TO-END TASK SUCCESS                                        |
| Factual Task Success Rate, Unsupported Rejection Rate, Zero Hallucination|
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| LAYER 6: RESPONSE GENERATION                                            |
| Response Language Match (EN, HI, Hinglish), Grounded Fact Fidelity     |
+-------------------------------------------------------------------------+
```

An error at Layer 4 (e.g. database path not found) is never counted as an intent classification failure (Layer 1). A fuzzy matching failure in entity resolution (Layer 3) is never counted as a span extraction error (Layer 2).

---

## 2. Layer-Specific Quantitative Metrics

### Layer 1: Intent Classification Metrics
- **Primary Metric**: **Test Macro-F1** across all $K$ intent classes.
  $$\text{Macro-F1} = \frac{1}{K} \sum_{k=1}^K F_1^{(k)}$$
- **Secondary Intent Metrics**:
  - Test Accuracy (Micro-F1)
  - Per-class Precision, Recall, and F1
  - Out-of-Scope (OOS) Precision, Recall, and False Alarm Rate
  - Subgroup Macro-F1 broken down across:
    - Language: `EN`, `HI_DEVA`, `HI_LATN`, `HINGLISH_LATN`, `MIXED_SCRIPT_CS`
    - Code-Switch Level: `CS0`, `CS1`, `CS2`, `CS3`, `CS4`
    - Noise Level: `N0`, `N1`, `N2`, `N3`, `N4`, `N5`
    - Transport Mode: `metro`, `bus`, `suburban_rail`, `mrts`, `multimodal`

### Layer 2: Slot Extraction Metrics
- **Span-Level Strict F1**: Strict character offset and entity type match.
- **Slot Exact Match Rate (EM)**: Proportion of queries where all extracted slots match ground truth spans perfectly.
- **Required-Slot Exact Match**: Proportion of queries where all mandatory (`REQ`) slots are correctly extracted.

### Layer 3: Canonical Entity Resolution Metrics
- **Top-1 Canonical Accuracy**: Extracted surface resolves to exact canonical ID in `canonical_transport.db`.
- **Top-3 Canonical Accuracy**: Canonical ID is present in top-3 resolver candidates.
- **Ambiguity Rate**: Proportion of queries triggering disambiguation across multi-mode nodes.
- **Entity Corruption Rate**: Percentage of entities mistranslated or deleted by translation preprocessing.

### Layer 4 & 5: Task Success & Factual Safety Metrics
- **End-to-End Task Success Rate**:
  $$\text{TaskSuccess} = \mathbb{I}(\text{IntentCorrect} \land \text{RequiredSlotsCorrect} \land \text{EntitiesResolved} \land \text{KBQueriedCorrectly})$$
- **Unsupported Request Rejection Accuracy**: Accuracy on refusing `REQUIRES_REALTIME_DATA` queries (e.g. live bus tracking) without hallucinating facts.
- **Hallucination Rate**: Any response containing fabricated fares, nonexistent route stops, or false live telemetry. Must be strictly **0.0%**.

---

## 3. Calibration and Confidence Diagnostics

Commuter assistants must be well-calibrated; a model should not output 0.99 confidence on an out-of-domain or malformed request.

1. **Expected Calibration Error (ECE)**:
   Partition predictions into $M=10$ confidence bins:
   $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
2. **Brier Score**:
   Mean squared difference between predicted class probabilities and one-hot true labels.
3. **Reliability Diagrams**:
   Plotted for all finalist models, specifically analyzing confidence on ambiguous and noisy inputs.

---

## 4. Latency and Resource Measurement Protocol

To ensure latency numbers are physical, reproducible, and comparable:
1. **Isolated Execution**: Batch size = 1, single query inference on dedicated GPU.
2. **CUDA Synchronization**:
   Every timing interval must be bracketed by `torch.cuda.synchronize()` before and after inference:
   ```python
   torch.cuda.synchronize()
   t0 = time.perf_counter()
   output = model(**inputs)
   torch.cuda.synchronize()
   latency_ms = (time.perf_counter() - t0) * 1000.0
   ```
3. **Reported Statistics**:
   - Warm-up: 50 discarded iterations.
   - Evaluation: Mean, P50, P95, and P99 latency across test queries.
   - Peak GPU VRAM footprint (`torch.cuda.max_memory_allocated()`).
   - Model serialized disk size (MB).

---

## 5. Storage of Per-Example Prediction Records

Aggregated summary statistics discard critical diagnostic evidence. Every benchmark run must serialize a machine-readable JSON Lines file (`predictions.jsonl`) recording per-example inferences:

```json
{
  "experiment_id": "V2_T2_B_MURIL_NORM0_SIZE40K_SEED42",
  "model_name": "google/muril-base-cased",
  "seed": 42,
  "utterance_id": "V2_UTT_001234",
  "query": "guindy se central metro ka last train kab hai",
  "language": "HINGLISH_LATN",
  "code_switch_level": "CS2",
  "noise_level": "N2",
  "gold_intent": "service_timing",
  "pred_intent": "service_timing",
  "confidence": 0.942,
  "intent_correct": true,
  "gold_slots": {"origin": "HUB_GUINDY", "destination": "HUB_CENTRAL", "transport_mode": "metro", "timing_type": "last"},
  "pred_slots": {"origin": "HUB_GUINDY", "destination": "HUB_CENTRAL", "transport_mode": "metro", "timing_type": "last"},
  "slots_exact_match": true,
  "latency_ms": 3.12
}
```

---

## 6. Formal Error Taxonomy for Failure Analysis

Finalist error analyses will classify failures into 17 standardized categories:
1. `intent_boundary_error`: Misclassification between adjacent valid intents (e.g. `service_timing` vs `service_availability`).
2. `missing_required_slot`: Extractor failed to detect a mandatory slot.
3. `wrong_slot_type`: Slot detected but assigned incorrect type (e.g. `destination` labeled as `origin`).
4. `entity_span_error`: Extracted boundary missed leading/trailing letters (`uindy` instead of `guindy`).
5. `entity_resolution_error`: Extracted span mapped to incorrect canonical ID.
6. `hub_node_ambiguity`: Failure to resolve generic hub vs specific modal station platform.
7. `transliteration_failure`: Failure caused by non-standard Romanization.
8. `hinglish_normalization_failure`: Parser tripped by colloquial Hinglish grammatical frames.
9. `code_switch_failure`: Classifier failed specifically on CS3/CS4 mixed-script queries.
10. `translation_corruption`: Pipeline A translation altered or erased a transit entity.
11. `route_number_corruption`: Route number suffix stripped or mistranslated (`102A` -> `102`).
12. `temporal_normalization_failure`: Failure to parse time expressions (`raat 8 baje`).
13. `oos_false_positive`: In-domain transit question incorrectly rejected as out-of-scope.
14. `oos_false_negative`: Out-of-scope or live-tracking query falsely fulfilled as a static transit answer.
15. `kb_missing_data`: System failed due to unlinked stage or uncataloged bus stop.
16. `routing_graph_error`: Pathfinding algorithm failed to compute valid transfer edge.
17. `response_generation_error`: Response text contradicted retrieval payload.
