# NLP v2 Developer Handoff

**Status:** Production Baseline Frozen  
**Active Taxonomy:** T3 Direct Dispatch (16 Classes)  
**Date:** 2026-09-24  

---

## 1. Frozen Decision

* **Production Intent Taxonomy:** **T3 Direct Dispatch (16 Classes)** is the frozen, canonical intent classification schema for NLP v2.
* **T2 Disposition:** The 12-class T2 candidate is retired from active implementation and retained strictly as a historical comparator and baseline.
* **Decision Authority:** Formally established in [`reports/nlp_v2/gate_b3/GATE_B3_TAXONOMY_DECISION.md`](file:///home/kaustubh/projects/NLP/reports/nlp_v2/gate_b3/GATE_B3_TAXONOMY_DECISION.md) and recorded in [`data/nlp_v2/gate_b3/gate_b3_annotation_manifest.json`](file:///home/kaustubh/projects/NLP/data/nlp_v2/gate_b3/gate_b3_annotation_manifest.json).

---

## 2. Immutable Assets (Do NOT Rerun or Re-Annotate)

The following components are cryptographically locked and must **not** be rerun, modified, or overwritten:
1. **Gate B.2 Frozen Benchmark:** MuRIL 3-seed evaluation artifacts and results.
2. **Gate B.3 MODEL_G Annotation Campaign:** Frozen first-pass annotations (`model_g_t2_annotations.jsonl`, `model_g_t3_annotations.jsonl`).
3. **Gate B.3 Sol Audits:** Targeted and expanded 256-judgment audits (`sol_expanded_t2_annotations.jsonl`, `sol_expanded_t3_annotations.jsonl`).
4. **Frozen Dataset & Splits:** The family-disjoint train, validation, and stress-eval sets.
5. **Existing Taxonomy Decision Experiments:** Taxonomy candidate evaluation is closed; do not reopen T2 vs T3 comparisons.

---

## 3. Canonical Repository Paths

| Component | Path | Description |
|:---|:---|:---|
| **T3 Taxonomy Guidelines** | [`docs/nlp_v2/gate_b3/t3_annotation_guide.md`](file:///home/kaustubh/projects/NLP/docs/nlp_v2/gate_b3/t3_annotation_guide.md) | Official definitions, operational boundaries, and rules for all 16 T3 classes. |
| **Taxonomy Semantic Mapping** | [`data/nlp_v2/taxonomy/taxonomy_semantic_mapping.json`](file:///home/kaustubh/projects/NLP/data/nlp_v2/taxonomy/taxonomy_semantic_mapping.json) | Cross-taxonomy mapping between T1, T2, and T3 classes. |
| **Frozen Dataset Splits** | `data/nlp_v2/gate_b2/` | `gate_b2_train.csv`, `gate_b2_validation.csv`, `gate_b2_stress_eval.csv`. |
| **Split & Leakage Policy** | [`docs/nlp_v2/split_and_leakage_policy.md`](file:///home/kaustubh/projects/NLP/docs/nlp_v2/split_and_leakage_policy.md) | Formal family-disjoint split contract and leakage guarantees. |
| **Human Reference Benchmark** | [`data/nlp_v2/gate_b2/human_annotation_key.json`](file:///home/kaustubh/projects/NLP/data/nlp_v2/gate_b2/human_annotation_key.json) | Frozen reference gold labels with secondary acceptable sets. |
| **Gate B.2 Benchmark Reports** | `reports/nlp_v2/gate_b2/` | `gate_b2_confirmation_results_v2.md`, `gate_b2_confirmation_results_v2.json`. |
| **Gate B.3 Final Decision** | [`reports/nlp_v2/gate_b3/GATE_B3_TAXONOMY_DECISION.md`](file:///home/kaustubh/projects/NLP/reports/nlp_v2/gate_b3/GATE_B3_TAXONOMY_DECISION.md) | Final evidence synthesis and formal T3 freeze declaration. |
| **Gate B.3 Annotation Manifest** | [`data/nlp_v2/gate_b3/gate_b3_annotation_manifest.json`](file:///home/kaustubh/projects/NLP/data/nlp_v2/gate_b3/gate_b3_annotation_manifest.json) | Canonical study state manifest (`taxonomy_decision_status: FROZEN`). |
| **MODEL_G Annotations** | `data/nlp_v2/gate_b3/` | `model_g_t3_annotations.jsonl`, `model_g_t2_annotations.jsonl`, `first_pass_lock_manifest.json`. |
| **Sol Expanded Audit** | `data/nlp_v2/gate_b3/sol_expanded_audit/` | `sol_expanded_t3_annotations.jsonl`, `sol_expanded_t2_annotations.jsonl`, `sol_output_manifest.json`. |
| **Sol Comparison Reports** | `reports/nlp_v2/gate_b3/` | `sol_expanded_comparison_summary.csv`, `sol_expanded_comparison.md`, `GATE_B3_EXPANDED_SOL_FINDINGS.md`. |

---

## 4. Instructions for Next Engineering Phase

Developers proceeding with implementation should observe the following practical instructions:
1. **Target T3 Exclusively:** Train, fine-tune, and integrate conversational and dispatch models solely against the 16-class T3 intent schema. Do not generate or maintain parallel T2 heads in production pipelines.
2. **Preserve Family-Disjoint Splits:** Maintain the existing partition boundaries (`gate_b2_train.csv`, `gate_b2_validation.csv`, `gate_b2_stress_eval.csv`). No template or entity family present in train may leak into validation or test.
3. **Immutable Test Labels:** Do not edit, patch, or regenerate benchmark or test set labels.
4. **Evaluation-Only Test Set:** `gate_b2_stress_eval.csv` and `human_annotation_key.json` must be strictly reserved for final offline evaluation; do not incorporate them into training, model selection, or prompt tuning.
5. **Downstream Dispatch Integration:** Map T3 intents directly into the multimodal routing engine, slot extraction modules, and knowledge base query builders according to the contracts defined in [`docs/nlp_v2/slot_schema.md`](file:///home/kaustubh/projects/NLP/docs/nlp_v2/slot_schema.md) and [`docs/nlp_v2/nlp_v2_task_spec.md`](file:///home/kaustubh/projects/NLP/docs/nlp_v2/nlp_v2_task_spec.md).
