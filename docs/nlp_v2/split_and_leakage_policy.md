# Split and Leakage Policy Specification (Phase N6)

Document: `docs/nlp_v2/split_and_leakage_policy.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Split & Leakage Policy

---

## 1. Zero-Leakage Splitting Principles

In synthetic and semi-synthetic NLP benchmarks, random train/val/test splitting produces severe data leakage. When surface paraphrases or cross-lingual translations of the same template appear in both training and test sets, models achieve artificially inflated accuracy by memorizing syntax templates rather than learning generalizable transit semantics.

To prevent leakage, the v2 benchmark enforces **Hierarchical Family-Disjoint and Semantic-Group-Disjoint Splitting**.

```
SPLIT ISOLATION HIERARCHY:

         SEMANTIC FAMILY (semantic_family_id)
      "how_to_travel_direct_route_between_two_points"
                     │
     ┌───────────────┴───────────────┐
     ▼                               ▼
FAMILY A (family_id)             FAMILY B (family_id)
"How do I get from {O} to {D}?"  "{O} se {D} kaise jau?"
(English syntactic frame)       (Hindi/Hinglish syntactic frame)
     │                               │
  SPLIT: ALLOCATED EXCLUSIVELY TO ONE SPLIT (e.g. TRAIN ONLY)
```

**Cardinal Partition Invariant**:
If a `semantic_family_id` is assigned to `train`, NO utterance belonging to that semantic family, regardless of language, script, or phrasing, may appear in `validation`, `test`, or challenge partitions.

---

## 2. Benchmark Split Partitions

### 2.1 Primary Frozen Split (70 / 15 / 15)
- **Train (70%)**: Parameter optimization and model weights learning.
- **Validation (15%)**: Early stopping monitoring, learning rate scheduling, and hyperparameter tuning.
- **Test (15%)**: Benchmark evaluation holdout. Frozen once created. Never inspected during development.
- **Stratification Constraints**:
  - Intent-stratified: Each split maintains proportional intent representation across all classes.
  - Language-aware: Each split maintains proportional representation of `EN`, `HI_DEVA`, `HI_LATN`, `HINGLISH_LATN`, and `MIXED_SCRIPT_CS`.
  - Script-aware: Devanagari, Latin, and mixed-script proportions remain constant across partitions.
- **Partition Seed**: Official Seed `42`.

### 2.2 Dedicated Challenge Partitions (Evaluated Separately)
In addition to the standard test partition, the v2 benchmark establishes two isolated diagnostic challenge sets:

1. **Unseen Entity-Combination Challenge Set (`challenge_unseen_pairs`)**:
   - Commuter queries where the origin and destination entities individual appeared in training, but the **origin-destination pair** was never seen in training.
   - Example:
     - Training contains: `Guindy → Airport` and `Tambaram → Central`
     - Challenge contains: `Guindy → Central` and `Tambaram → Airport`
   - Purpose: Disentangles linguistic intent classification from origin-destination pair memorization.

2. **Alias Holdout Challenge Set (`challenge_unseen_aliases`)**:
   - Commuter queries where the canonical entity appeared during training, but a specific surface alias, transliteration variant, or typo was strictly held out.
   - Example:
     - Training: `Guindy`, `गिंडी`
     - Challenge: `Gindi`, `Guindi`, `Gindy stn`
   - Purpose: Measures zero-shot alias generalization and entity resolver robustness.

---

## 3. Seven Automated Leakage Audit Detectors

The validation auditor (`scripts/nlp_v2/audit_split_leakage.py`) runs seven automated checks on candidate partitions. Detection of any violation causes an immediate build failure.

1. **Exact Duplicate Query Detector**:
   Checks whether any raw query string in `test` or `validation` exists in `train`.
   $$\text{ExactLeakage} = \{q \mid q \in Q_{\text{test}} \cap Q_{\text{train}}\} = \emptyset$$

2. **Normalized Query Deduplication**:
   Applies lowercase folding, whitespace collapsing, and punctuation stripping, then checks for cross-split overlap.
   $$\text{NormLeakage} = \{\text{norm}(q) \mid \text{norm}(q) \in \text{Norm}(Q_{\text{test}}) \cap \text{Norm}(Q_{\text{train}})\} = \emptyset$$

3. **Family ID Disjointness**:
   Confirms that every `family_id` belongs to exactly one partition.
   $$\text{Families}(Q_{\text{train}}) \cap \text{Families}(Q_{\text{test}}) = \emptyset$$

4. **Semantic Family Group Disjointness**:
   Confirms that cross-lingual equivalents sharing a `semantic_family_id` do not leak across splits.
   $$\text{SemanticFamilies}(Q_{\text{train}}) \cap \text{SemanticFamilies}(Q_{\text{test}}) = \emptyset$$

5. **Cross-Script Transliteration Overlap**:
   Transliterates Devanagari queries to Latin characters (via standard IAST / ISO 15919) and verifies that no Latin-script query in the test set is a phonetic duplicate of a Devanagari training query.

6. **Entity Combination Leakage in Challenge Set**:
   Verifies that 100% of origin-destination entity tuples in `challenge_unseen_pairs` are strictly absent from the training set.

7. **Near-Duplicate Lexical Similarity Audit**:
   Computes word 3-gram Jaccard similarity across test and train queries. Queries with Jaccard similarity $> 0.85$ are flagged for human inspection to ensure superficial word substitutions do not bypass family disjointness.

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
