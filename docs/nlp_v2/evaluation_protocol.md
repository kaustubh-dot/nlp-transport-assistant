# Multimodal Multilingual Evaluation Protocol (Phase N7)

Document: `docs/nlp_v2/evaluation_protocol.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Evaluation Protocol (Corrected Methodology Patch)

---

## 1. Six-Layer Evaluation Framework

To prevent opaque aggregation, the evaluation protocol assesses performance across six distinct architectural layers:

```
+-------------------------------------------------------------------------+
| LAYER 1: INTENT CLASSIFICATION                                          |
| Macro-F1, Accuracy, Per-Class F1, Confusion Matrix, OOS Calibration     |
+-------------------------------------------------------------------------+
                                    │
+-------------------------------------------------------------------------+
| LAYER 2: SLOT SPAN EXTRACTION                                           |
| Span Strict F1 (BIO boundary), Exact Slot-Set Match, Per-Slot F1        |
+-------------------------------------------------------------------------+
                                    │
+-------------------------------------------------------------------------+
| LAYER 3: CANONICAL ENTITY RESOLUTION                                    |
| Top-1 Canonical Accuracy, Top-3 Accuracy, Ambiguity Rate, Unresolved Rate|
+-------------------------------------------------------------------------+
                                    │
+-------------------------------------------------------------------------+
| LAYER 4: TRANSPORT KB RETRIEVAL & ROUTING                               |
| Table Hit Rate, Correct Routing Graph Path, Fare Stage Consistency      |
+-------------------------------------------------------------------------+
                                    │
+-------------------------------------------------------------------------+
| LAYER 5: END-TO-END TASK SUCCESS                                        |
| Factual Task Success Rate, Unsupported Rejection Rate, Zero Hallucination|
+-------------------------------------------------------------------------+
                                    │
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
- **Real-Time Request Rejection Accuracy**: Accuracy on refusing `realtime_status_query` (`REQUIRES_REALTIME_DATA`) queries (e.g. live bus tracking) without hallucinating live facts.
- **Hallucination Rate**: Any response containing fabricated fares, nonexistent route stops, or false live telemetry. Must be strictly **0.0%**.

---

## 3. Strict Experimental Lifecycle & Test Discipline

To guarantee benchmark integrity and prevent test contamination, development proceeds through four strictly partitioned phases:

```
1. DEVELOPMENT PHASE:
   Train models strictly on 'train' partition.
   Tune hyperparameters and monitor convergence strictly on 'validation'.
   Diagnose error modes and zero-shot entity behavior on dev challenge sets
   (challenge_unseen_pairs, challenge_unseen_aliases).

2. FINALIST FREEZE GATE:
   Lock candidate architectures, preprocessing pipelines, hyperparameter configs,
   taxonomy version, and confidence thresholds. No code or configuration changes permitted after this point.

3. FINAL TEST BENCHMARK:
   Execute frozen finalists on untouched 'test' partition.
   Log per-example predictions across seeds.
   Do NOT use test set errors for post-hoc hyperparameter tuning or feature engineering.

4. INDEPENDENT GOLD ACCEPTANCE SUITE:
   Evaluate selected champion on the independently authored, external Gold Suite.
```

---

## 4. Coverage-Based Independent Gold Suite Specification

The v2 Gold Suite replaces arbitrary sample size targets with a formal coverage-based requirement:

$$\text{Base Gold Size} \ge 10 \text{ independently authored cases} \times K_{\text{intents}} \times 5 \text{ language classes}$$

- **Scale under Taxonomy T1 (9 intents)**: $\ge 450$ curated queries.
- **Scale under Taxonomy T2 (12 intents)**: $\ge 600$ curated queries.
- **Scale under Taxonomy T3 (16 intents)**: $\ge 800$ curated queries.
- **Additional Robustness Cases**:
  - Typographical noise and chat abbreviations ($\ge 50$ cases).
  - Rare/tail bus stop and suburban rail entities ($\ge 50$ cases).
  - Alphanumeric bus route variants (`102A`, `21G`, `102K#`) ($\ge 30$ cases).
  - Boundary out-of-scope and real-time status queries ($\ge 50$ cases).
- **Authoring Independence**: Gold queries must be independently authored by native Hindi and Tamil/English bilingual speakers without access to training template banks.

---

## 5. Statistical Testing Across Seeds and Per-Example Predictions

1. **Per-Example Paired Testing Mandate**:
   Statistical significance tests (McNemar's test and paired bootstrap) **must operate on paired per-example predictions**, never on aggregated or averaged metrics across seeds. Applying McNemar to aggregate numbers is mathematically invalid.
2. **Multi-Seed Protocol for Finalists**:
   - For serious finalists, serialize `predictions.jsonl` for every evaluation seed (`[42, 101, 777, 1337, 2026]`).
   - Perform matched-seed paired comparisons ($S_i^{\text{ModelA}}$ vs $S_i^{\text{ModelB}}$) across all queries.
   - Report mean, standard deviation, and 95% bootstrap confidence intervals ($B = 1,000$ iterations).
   - Use hierarchical / seed-aware bootstrap for final robustness comparisons.

---

## 6. Physical Latency & Calibration Protocol

1. **CUDA Synchronization**:
   Timing intervals must use `torch.cuda.synchronize()` at `batch_size = 1`:
   ```python
   torch.cuda.synchronize()
   t0 = time.perf_counter()
   output = model(**inputs)
   torch.cuda.synchronize()
   latency_ms = (time.perf_counter() - t0) * 1000.0
   ```
2. **Calibration Diagnostics**:
   - Compute Expected Calibration Error (ECE, 10 bins) and Brier score.
   - Specifically evaluate confidence calibration on ambiguous entities, noisy queries, and `out_of_scope`.
