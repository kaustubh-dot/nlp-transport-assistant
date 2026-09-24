# Gate B.3 Final Intent Taxonomy Decision

**Document Status:** Formal Decision Record (`FROZEN`)  
**Decision Outcome:** `T3_FREEZE` — Adopt T3 Direct Dispatch (16 Classes) as Production Intent Taxonomy  
**Date:** 2026-09-24  
**Scope:** NLP v2 Multimodal Transport Assistant  
**Evaluated Candidates:**  
* **T2:** Coarse Modular Taxonomy (12 Classes)  
* **T3:** Direct Dispatch Taxonomy (16 Classes)  

---

## 1. Formal Decision Statement

```text
================================================================================
GATE B.3 TAXONOMY DECISION: T3_FREEZE (ADOPTED & FROZEN)
================================================================================
Selected Taxonomy:             T3 (Direct Dispatch)
Number of Intent Classes:      16
Status:                        FROZEN / PRODUCTION
Prior Candidate Status:        T2 (12 Classes) retired to historical comparator
Gate B.3 Lifecycle Status:     COMPLETE / CLOSED
================================================================================
```

Effective immediately, the 16-class **T3 Direct Dispatch** taxonomy is formally adopted and frozen as the canonical intent classification schema for the NLP v2 transport assistant. The 12-class T2 candidate is retired from active development and retained solely for historical provenance and comparative evaluation.

---

## 2. Multi-Evidence Synthesis & Rationale

This decision synthesizes three distinct, pre-authorized empirical evaluations conducted under strict governance guardrails:
1. **Gate B.2 Downstream/Model Benchmark:** Multi-seed fine-tuned MuRIL sequence classification and operation dispatch evaluation ($N=706$).
2. **Gate B.3 Full MODEL_G Reference Concordance:** 350-query first-pass challenge evaluation against the human reference benchmark.
3. **Gate B.3 Expanded Sol Audit:** 128-query (256-judgment) masked blind-to-label secondary model audit across linguistic and surface stress dimensions.

### 2.1 Gate B.2 Downstream Operational Advantage

In Gate B.2 multi-seed confirmatory evaluation (seeds 42, 101, 777), direct 16-class T3 classification consistently outperformed the capacity-matched 12-class multitask architecture (T2-H) on operational routing:

* **Downstream Operation Accuracy:** T3 achieved `0.7941 ± 0.0291` vs T2-H `0.7531 ± 0.0024`, representing an advantage of **+4.11 pp** (empirical $p < 0.002$, 95% CI: `[+0.0245, +0.0581]`).
* **Audited Ambiguity-Aware Accuracy:** T3 achieved `0.8069 ± 0.0306` vs T2-H `0.7668 ± 0.0084` (**+4.01 pp**).
* **Ambiguous-Only Subset ($N=98$):** T3 achieved `0.6531 ± 0.0464` vs T2-H `0.5952 ± 0.0585` (**+5.78 pp**).
* **Downstream Operation Macro-F1:** T3 achieved `0.7420 ± 0.0376` vs T2-H `0.7105 ± 0.0098` (**+0.0315**).
* **Contrast Group Exact:** T3 reached **93.9%** vs T2-H 92.1% (**+1.8 pp**).

T3 eliminates the error propagation inherent in two-stage coarse-to-fine routing by predicting atomic dispatch operations directly.

### 2.2 Gate B.3 Full 350-Query MODEL_G Concordance

When evaluated against the locked human reference key across the full 350-query challenge set, MODEL_G (Google Gemini 3.8 Flash) exhibited superior concordance under T3 across nearly every primary and set metric:

| Metric | T2 (350 queries) | T3 (350 queries) | T3 − T2 Delta |
|:---|---:|---:|---:|
| **Primary Exact Match** | 78.57% (275/350) | **81.14% (284/350)** | **+2.57 pp** |
| **MODEL_G Primary in Ref Acceptable Set** | 79.43% (278/350) | **84.29% (295/350)** | **+4.86 pp** |
| **Exact Acceptable-Set Match** | 56.57% (198/350) | **66.86% (234/350)** | **+10.29 pp** |
| **Mean Acceptable-Set Jaccard** | 77.64% | **81.52%** | **+3.88 pp** |
| **Clarification Judgment Agreement** | 80.57% (282/350) | **82.86% (290/350)** | **+2.29 pp** |
| **Reference Primary in MODEL_G Acceptable Set** | **99.71% (349/350)** | 97.14% (340/350) | -2.57 pp |

T3 achieved +9 additional primary exact matches, +17 items with primary intent inside the acceptable reference set, and +36 items with exact acceptable-set identity (+10.29 pp).

### 2.3 Explicit Trade-Off: Reference Primary in Model Set

T2 retains one clear empirical advantage:
* **Reference primary in MODEL_G acceptable set:** 99.71% under T2 vs 97.14% under T3 (-2.57 pp, 9 queries).

This is acknowledged as an authentic design tradeoff rather than an anomaly. Because T2 classes are broader (e.g., umbrella `route_query` merging point-to-point and multimodal routes; `route_stops` merging sequence and membership), an acceptable set under T2 casts a wider net. However, this broadness substantially degrades precision: exact acceptable-set match under T2 is only 56.57% compared to 66.86% under T3. T3's acceptable sets are more specific, operationally actionable, and better aligned with the gold acceptable boundaries.

### 2.4 Expanded 128-Query Audit Parity & Model Alignment

The secondary masked blind-to-label audit using GPT-5.6 Sol across 128 purposively selected challenge queries (256 judgments) confirmed high baseline stability:

* **Primary Exact Parity:**
  * GPT-5.6 Sol: 92.2% (T2) vs 91.4% (T3), a net change of -0.8 pp (1 single query: `ANN_B2_097`).
  * MODEL_G: 89.8% (T2) vs 90.6% (T3), a net change of +0.8 pp (+1 query net).
* **Strengthened Cross-Model Semantic Alignment Under T3:**
  * Primary Intent Agreement: rises from 90.6% (T2) to **93.0% (T3)** (+2.3 pp).
  * Acceptable-Set Exact Agreement: rises sharply from 75.8% (T2) to **82.8% (T3)** (**+7.0 pp**).
  * Clarification Agreement: rises from 82.8% (T2) to **85.9% (T3)** (+3.1 pp).

The slight Sol primary reversal on the 128-query sample is bounded to a single item and is accompanied by a substantial increase in cross-model semantic consensus under T3.

### 2.5 Invariance Across Indic Languages and Surface Variations

Crucially, the expanded audit confirmed that T3 introduces no penalty on challenging linguistic or surface features:

1. **Indic and Mixed-Script Stability:** Across all 98 non-English queries (`HINGLISH_LATN` $N=29$, `HI_DEVA` $N=30$, `HI_LATN` $N=29$, `MIXED_SCRIPT_CS` $N=10$), both Sol and MODEL_G exhibited exactly **0.0 pp delta** between T2 and T3. All observed label shifts were restricted to the 30 English queries.
2. **Code-Switching Invariance:** Tiers CS1 through CS4 ($N=77$) showed **0.0 pp delta** across both models.
3. **Script Invariance:** Devanagari ($N=30$) and Mixed-script ($N=10$) queries showed **0.0 pp delta** across both models.
4. **No Concurrent Degradation:** Across all 6 noise levels/types, 9 ambiguity types, and 5 answerability statuses, there is no category in which both models degraded under T3.

---

## 3. Scope of Claims & Interpretation Guardrails

In accordance with project governance standards:
* **Purposive Sample:** Metrics from the 350-query baseline and 128-query audit are derived from purposive challenge distributions enriched for stress phenomena and do not represent random population samples.
* **No Generalization Assertions:** Findings are descriptive of the evaluated test suites; no broad population superiority or external generalization is claimed.
* **Model Audit Provenance:** GPT-5.6 Sol served as a secondary masked model auditor where reference and peer labels were withheld; its findings represent model-based audit evidence rather than human inter-annotator agreement.

---

## 4. Final Governance Conclusion

The totality of empirical evidence decisively supports the adoption of T3:
1. T3 demonstrated a statistically significant +4.11 pp advantage on downstream operation accuracy in Gate B.2.
2. T3 demonstrated superior primary concordance (+2.57 pp) and dramatically improved acceptable-set concordance (+10.29 pp) on the full 350-query Gate B.3 reference join.
3. T3 improved inter-model agreement (+7.0 pp on acceptable sets) in the expanded audit.
4. T3 demonstrated complete robustness across Hindi, Hinglish, code-switching, and noise tiers.

Therefore, **T3 Direct Dispatch (16 Classes) is officially frozen as the production taxonomy.**
