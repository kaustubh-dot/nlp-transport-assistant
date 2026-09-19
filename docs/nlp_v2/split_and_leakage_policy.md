# Split and Leakage Policy Specification (Phase N6)

Document: `docs/nlp_v2/split_and_leakage_policy.md`  
Snapshot Version: `chennai_multimodal_v1.2.2`  
Date: 2026-09-19  
Status: Authoritative Split & Leakage Policy (Corrected Methodology Patch)

---

## 1. Zero-Leakage Splitting Principles

In synthetic and semi-synthetic NLP benchmarks, random train/val/test splitting produces severe data leakage. When surface paraphrases or cross-lingual translations of the same template appear in both training and test sets, models achieve artificially inflated accuracy by memorizing syntax templates rather than learning generalizable transit semantics.

To prevent leakage, the primary v2 benchmark enforces **Hierarchical Family-Disjoint and Semantic-Group-Disjoint Splitting**.

```
PRIMARY BENCHMARK SPLIT ISOLATION HIERARCHY:

         SEMANTIC FAMILY (semantic_family_id)
      "how_to_travel_direct_route_between_two_points"
                     │
     ┌───────────────┴───────────────┐
     ▼                               ▼
FAMILY A (family_id)             FAMILY B (family_id)
"How do I get from {O} to {D}?"  "{O} se {D} kaise jau?"
(English syntactic frame)       (Hindi/Hinglish syntactic frame)
     │                               │
  PRIMARY SPLIT: ASSIGNED EXCLUSIVELY TO ONE PARTITION (TRAIN ONLY)
```

**Cardinal Invariant for Primary Benchmark**:
If a `semantic_family_id` is assigned to `train`, no utterance belonging to that semantic family, regardless of language, script, or phrasing, may appear in the primary `validation` or `test` sets.

---

## 2. Benchmark Partitions & Challenge Set Isolation

### 2.1 Primary Frozen Split (70 / 15 / 15)
- **Train (70%)**: Parameter optimization and model weights learning.
- **Validation (15%)**: Early stopping monitoring, learning rate scheduling, and hyperparameter tuning.
- **Test (15%)**: Final benchmark evaluation holdout. Frozen once created. Never inspected during development.
- **Stratification Constraints**:
  - Intent-stratified across all active intent classes.
  - Language-aware across `EN`, `HI_DEVA`, `HI_LATN`, `HINGLISH_LATN`, and `MIXED_SCRIPT_CS`.
  - Script-aware across Devanagari, Latin, and mixed scripts.
- **Partition Seed**: Official Seed `42`.

---

### 2.2 Controlled Challenge Sets (Isolating Single Experimental Variables)

To prevent confounding variables, diagnostic challenge sets must isolate exactly the mechanism they are designed to evaluate. When an evaluation set simultaneously introduces unseen entities and unseen syntactic structures, error analysis cannot determine whether failure stemmed from lexical grounding or grammatical generalization.

We define two controlled diagnostic sets plus two separate hard challenge sets:

```
CHALLENGE SET DESIGN MATRIX:

Challenge Partition              Syntactic Family Status          Entity / Alias Status
----------------------------------------------------------------------------------------------------
challenge_unseen_pairs (Controlled)   KNOWN (present in train)         UNSEEN origin-destination pair
challenge_unseen_aliases (Controlled) KNOWN (present in train)         UNSEEN surface alias / typo form
challenge_hard_unseen_pairs (Hard)    UNSEEN (disjoint from train)     UNSEEN origin-destination pair
challenge_hard_unseen_aliases (Hard)  UNSEEN (disjoint from train)     UNSEEN surface alias / typo form
```

#### 1. `challenge_unseen_pairs` (Controlled Entity-Combination Isolation)
- **Design**: Uses linguistic and semantic families already represented in the training set, but populates them with **unseen origin-destination combinations**.
- **Example**:
  - Training contains family `route_query:how_basic` with pairs `(Guindy, Airport)` and `(Tambaram, Central)`.
  - Challenge set uses the **same** family `route_query:how_basic` but populates it with `(Guindy, Central)` and `(Tambaram, Airport)`.
- **Diagnostic Purpose**: Purely isolates whether the model memorized origin-destination co-occurrence rather than understanding the linguistic intent.

#### 2. `challenge_unseen_aliases` (Controlled Transliteration / Alias Isolation)
- **Design**: Uses syntactic families represented in training, but introduces **unseen surface aliases, phonetic Romanizations, or spelling corruptions** for canonical entities that were present in training under canonical names.
- **Example**:
  - Training saw: `Guindy`, `गिंडी`, `Chennai Central`.
  - Challenge contains: `Gindi`, `Guindi`, `Gindy stn`, `Cntral`.
- **Diagnostic Purpose**: Purely isolates zero-shot alias generalization and entity resolver robustness without confounding from syntactic novelty.

#### 3. Hard Challenge Variants (`challenge_hard_unseen_pairs`, `challenge_hard_unseen_aliases`)
- **Design**: Both the linguistic/semantic family **and** the entity condition (unseen pair or unseen alias) are simultaneously held out from training.
- **Diagnostic Purpose**: Measures compounding failure modes under maximum domain shift.

---

## 3. Seven Automated Leakage Audit Detectors

The validation auditor (`scripts/nlp_v2/audit_split_leakage.py`) runs seven automated checks on candidate partitions. Detection of any violation causes an immediate build failure.

1. **Exact Duplicate Query Detector**:
   Verifies that no raw query in `test` or `validation` exists in `train`.
   $$\text{ExactLeakage} = \{q \mid q \in Q_{\text{test}} \cap Q_{\text{train}}\} = \emptyset$$

2. **Normalized Query Deduplication**:
   Applies lowercase folding, whitespace collapsing, and punctuation stripping, then verifies zero cross-split overlap between `train` and `test`/`validation`.
   $$\text{NormLeakage} = \{\text{norm}(q) \mid \text{norm}(q) \in \text{Norm}(Q_{\text{test}}) \cap \text{Norm}(Q_{\text{train}})\} = \emptyset$$

3. **Family ID Disjointness (Primary Split)**:
   Confirms that every `family_id` in `test` and `validation` is strictly absent from `train`.
   $$\text{Families}(Q_{\text{train}}) \cap \text{Families}(Q_{\text{test}}) = \emptyset$$

4. **Semantic Family Group Disjointness (Primary Split)**:
   Confirms that cross-lingual equivalents sharing a `semantic_family_id` do not leak across primary splits.
   $$\text{SemanticFamilies}(Q_{\text{train}}) \cap \text{SemanticFamilies}(Q_{\text{test}}) = \emptyset$$

5. **Cross-Script Transliteration Overlap**:
   Transliterates Devanagari queries to Latin characters (via standard IAST / ISO 15919) and verifies that no Latin-script query in the test set is a phonetic duplicate of a Devanagari training query.

6. **Entity Pair Isolation in Controlled Challenge Set**:
   Verifies that 100% of origin-destination entity tuples in `challenge_unseen_pairs` and `challenge_hard_unseen_pairs` are strictly absent from the training set.

7. **Near-Duplicate Lexical Similarity Audit**:
   Computes word 3-gram Jaccard similarity across test and train queries. Queries with Jaccard similarity $> 0.85$ are flagged for inspection to ensure superficial word substitutions do not bypass family disjointness.

---

## 4. Secondary Split-Sensitivity Protocol

Because adequate compute is available, finalist architectures will undergo secondary sensitivity evaluation across three additional family-disjoint splits.

### Protocol Rules:
1. **Primary Benchmark Priority**:
   The primary leaderboard, model comparison rankings, and official macro-F1 metrics are evaluated exclusively on the primary frozen split (Seed 42).
2. **Secondary Sensitivity Verification**:
   The top finalist models are evaluated on three alternate random seeds (`Seeds [101, 777, 1337]`), with independent family-disjoint partitions generated using the same stratification algorithm.
3. **Diagnostic Reporting**:
   Secondary split results are reported as a diagnostic sensitivity table:
   $$\text{Split Stability Ratio} = \frac{\sigma_{\text{splits}}}{\mu_{\text{splits}}}$$
   A model whose performance collapses on alternate splits is penalized for overfitting to specific template families.
