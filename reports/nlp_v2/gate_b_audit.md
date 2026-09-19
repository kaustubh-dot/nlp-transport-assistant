# Gate B Controlled Synthetic Taxonomy Pilot Audit

## Overview
**Status:** Audit Completed & Acknowledged  
**Historical Experiment:** Gate B — Controlled Synthetic Taxonomy Smoke Test  
**Active Knowledge Base Baseline:** `chennai_multimodal_v1.2.2` (Enriched with 1,681 CMRL Fare Matrix records)  

The Gate B taxonomy pilot successfully validated pipeline machinery:
- End-to-end multi-regime dataset generation executed cleanly;
- Strict family-based partition machinery worked at a basic level;
- Both TF-IDF baseline and Google MuRIL fine-tuning harnesses ran without failure;
- Experiment logging, evaluation scripts, and aggregate comparison reports produced all 36 planned logical runs;
- The intent taxonomies (T1 Broad, T2 Medium, T3 Fine) proved technically learnable.

However, the empirical results exhibited an artificial performance ceiling:
- **Google MuRIL:** 1.0000 Macro-F1 across all 18 runs, both regimes, all taxonomies, and all 3 seeds.
- **TF-IDF + Logistic Regression:** ~0.997–1.000 Macro-F1 across all runs.

This audit establishes that the near-perfect performance was heavily influenced by synthetic generator artifacts, lexical giveaways, and template shortcuts. Consequently, **Gate B must be characterized as a controlled synthetic smoke test, not as definitive evidence for freezing T2 or T3**.

---

## Audit Findings

### 1. Visible Synthetic Marker Leakage
The pilot generator inserted synthetic markers directly into commuter query strings, including:
- Family and scenario annotations: `[seq F15]`, `[chk F20]`, `[freq F10]`, `[sched F7]`, `[fare F18]`, `[live F4]`, `[a11y F12]`, `[xfer F1]`, `[bahar F4]`, `(F13)`
- Variation/generator counters: `#2`, `#3`, `[v2]`, `[v3]`

These markers appeared over 44,000 times across pilot CSV queries (e.g. `13,162` occurrences of `[.*F\d+.*]`, `8,220` occurrences of `(F\d+)`, `23,326` occurrences of `#\d+`). These tokens acted as direct, synthetic shortcuts encoding scenario and family identity, making intent discrimination trivially easy for subword and n-gram classifiers.

*Requirement for Gate B.1:* Zero generator-only marker tokens in user-facing query text.

---

### 2. Overstated Family Diversity
The Gate B generator claimed 20 distinct linguistic families per semantic scenario. In practice, each scenario relied on a small fixed set of sentence frames where entity slots were substituted, numerical family tags (`F1`...`F20`) were swapped, and cosmetic affixes were added. This produced surface variation rather than 20 genuinely independent syntactic structures.

*Requirement for Gate B.1:* Use linguistically distinct syntactic structures across families, with family disjointness evaluated on genuine grammatical patterns.

---

### 3. Repetition Through Cosmetic Affixes
Utterances were diversified by prepending or appending formulaic discourse markers such as:
- `Please tell:`
- `Quick check:`
- `Could you specify:`
- `Transit query:`
- `Hello assistant:`
- Numerical tags: `#2`, `#3`

These affixes do not represent independent paraphrase families.

*Requirement for Gate B.1:* Paraphrase diversity must reside in the communicative core and syntactic argument structure of the utterance, not peripheral prefixes/suffixes.

---

### 4. `semantic_scenario_id` Dictionary Key Mismatch
In `scripts/nlp_v2/pilot/generate_pilot_bank.py`, the generator constructed item dictionaries with the key `scenario_id`, but the CSV partition writer expected `semantic_scenario_id`. As a result, all committed pilot CSVs contain empty string values (`""`) in the `semantic_scenario_id` column.

*Resolution:* Documented historically. In Gate B.1, `semantic_scenario_id` is properly populated and strictly verified by automated schema QA.

---

### 5. Incomplete Code-Switching Coverage
While the NLP v2 language specification specifies five discrete code-switching levels (`CS0` to `CS4`), the Gate B pilot generator only emitted queries under `CS0` (monolingual), `CS3` (intra-sentential lexical insertion), and `CS4` (mixed-script Hindi/English). `CS1` (phonetic transliteration with English keywords) and `CS2` (matrix language frame switching) were entirely absent from the committed pilot splits.

*Requirement for Gate B.1:* Meaningfully cover all five levels (`CS0`, `CS1`, `CS2`, `CS3`, `CS4`) with surface text strictly adhering to their sociolinguistic definitions.

---

### 6. Noise Metadata Disconnected from Text Corruption
The pilot generator assigned noise annotations (`N1`, `N2`) based on row index modular arithmetic (`u_counter % 7 == 0`, `u_counter % 11 == 0`) without applying any text corruption to the query string. Consequently:
- Queries labeled `noise_level = N1` or `N2` were completely pristine text.
- No keyboard transposition, phonetic misspelling, or truncation was evaluated.

*Requirement for Gate B.1:* Ensure `noise_level` strictly reflects actual, visible character/token transformations (`N0` to `N5`), while storing the pristine `clean_query` separately.

---

### 7. Narrow Entity Scope
Despite loading the full multimodal database, the pilot generator restricted its sampling to a hand-curated subset of 20 metro stations and 16 bus stops (heavily overindexing on Central, Airport, Guindy, Tambaram, and CMBT). This did not stress-test the model across Chennai's wide entity distribution.

*Requirement for Gate B.1:* Sample entities broadly across Metro, MTC bus, Suburban rail, MRTS, multimodal hubs, localities, and POIs (head, mid, and tail distributions).

---

### 8. Unvalidated Entity/Mode Relationships
Because route and stop IDs were sampled without topological cross-validation, the generator occasionally produced factually contradictory combinations (e.g., describing a metro line as a bus service or asserting that a bus route served a non-topological station).

*Requirement for Gate B.1:* Validate route mode, stop mode, and route-stop membership against canonical topology when making factual assertions.

---

### 9. Semantic Operation Metric Was Compatibility Accuracy
In the Gate B pilot evaluation harness, the metric reported as `semantic_op_accuracy` was computed by:
$$\text{predicted\_intent} \to \text{Allowed Operations for Intent} \implies \text{gold\_operation} \in \text{Allowed Operations}$$

Under this formulation:
- Predicting T2 `route_query` received credit for both `PLAN_ROUTE` and `PLAN_MULTIMODAL_ROUTE`.
- Predicting T2 `service_timing` received credit for `GET_FIRST_LAST_SERVICE`, `GET_SERVICE_FREQUENCY`, and `GET_SCHEDULED_DEPARTURES`.
- Predicting T2 `route_stops` received credit for both `LIST_ROUTE_STOPS` and `CHECK_STOP_ON_ROUTE`.

Therefore, the historical metric measured **operation compatibility accuracy**, not exact downstream operational dispatch.

*Clarification:* The historical Gate B metric is officially re-designated as `operation_compatibility_accuracy`. Gate B.1 must calculate both `exact_downstream_operation_accuracy` and `operation_compatibility_accuracy`.

---

### 10. Reported TF-IDF Error Count Mismatch
The committed aggregate pilot report (`reports/nlp_v2/taxonomy_pilot_results.json`) records 24 total `route_query` $\to$ `service_timing` misclassifications across repeated TF-IDF runs. The initial executive handoff summary claimed 16. The correct historical total across all 18 TF-IDF runs is **24**.

---

### 11. TF-IDF Architecture Clarification
The Gate B baseline classifier was implemented using:
```python
TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)
```
This is a word unigram and bigram model. It did not contain character n-grams. Descriptions of the Gate B baseline as incorporating character n-grams are incorrect.

---

### 12. MuRIL Best Epoch Distribution
Historical MuRIL training runs logged best validation Macro-F1 epochs ranging from **1 to 3** (specifically, `regime_a_T2_muril_seed42` reached its best checkpoint at epoch 3, while several Regime B runs reached best checkpoints at epoch 1). Handoff documentation claiming best epochs were universally 1–2 is hereby corrected.

---

## Conclusion & Gate B.1 Directives

Gate B fulfilled its intended purpose as a pipeline verification smoke test. However, due to synthetic marker leakage, formulaic phrasing, and compatibility-based operational evaluation, it does not provide sufficient discriminatory evidence to freeze T2 Medium or T3 Fine.

All taxonomy selection decisions are deferred to **Gate B.1**, which implements:
1. Zero generator-only marker tokens;
2. >=25% independently authored hard cases;
3. Dedicated minimal-pair contrast groups (>=400 queries);
4. Explicit implicit-intent (>=300) and ambiguous-intent (>=200) subsets;
5. Meaningful CS0–CS4 code-switching and genuine N0–N5 text corruptions;
6. Paired evaluation on identical queries across T2 and T3;
7. Exact downstream operation dispatch scoring (T2-A and T2-B vs T3);
8. Blind two-reviewer human annotation agreement study (raw agreement and Cohen's $\kappa$).
