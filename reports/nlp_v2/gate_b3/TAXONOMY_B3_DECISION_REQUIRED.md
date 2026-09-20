# Gate B.3 Intent Taxonomy Decision Document

**Document:** `reports/nlp_v2/gate_b3/TAXONOMY_B3_DECISION_REQUIRED.md`  
**Current Decision Status:** `PENDING`  
**Date:** 2026-09-20  
**Phase:** Gate B.3 Pre-Annotation Checkpoint  
**Decision Gatekeeper:** Student Author & Project Governance  

---

## 1. Decision Status Overview

```text
============================================================
GATE B.3 TAXONOMY DECISION: PENDING
============================================================
No taxonomy selection has been performed or authorized.
Annotation study execution is not started.
```

The intent taxonomy selection between **T3 Direct Dispatch (16 Classes)** and **T2 Coarse Modular (12 Classes)** remains strictly **PENDING** until the complete Gate B.3 Annotation-Stability and Semantic-Boundary Audit is executed, locked, and reconciled.

---

## 2. Permitted Final Decision Outcomes

At the conclusion of the Gate B.3 audit, one of the following three decisions must be recorded:
1. **`T3_FREEZE`**: Adopt the 16-class T3 direct-dispatch taxonomy as the project standard for subsequent stages.
2. **`T2_FREEZE`**: Revert to the 12-class T2 coarse taxonomy at the primary intent layer.
3. **`INCONCLUSIVE`**: Findings do not definitively justify either choice under current evidence; maintain current candidate status without freezing.

---

## 3. Decision Governance Criteria

### 3.1 Conditions for `T3_FREEZE`
T3 may be frozen for this university course project **only if all of the following criteria are satisfied**:
1. The Gate B.2 model-side operational accuracy advantage ($+4.11\text{ pp}$ strict, $+4.01\text{ pp}$ ambiguity-aware, $p < 0.002$) remains methodologically relevant and is not negated by reference defects.
2. The fine-grained splits unpacked by T3 (route, stop, and timing operations) demonstrate observed coverage and positive agreement across annotators.
3. Added fine distinctions (e.g. `point_to_point_route` vs `multimodal_route`, `route_stop_sequence` vs `route_stop_membership`) have coherent, operationalizable expressed-meaning boundary rules.
4. No unresolved **structural taxonomy defect** (see Section 4) is identified in those fine distinctions during the post-lock audit.
5. Complete available contrast groups in the challenge set support the intended boundaries, or observed divergences are explicitly explained.
6. Genuine user ambiguity is reliably representable using `acceptable_labels` sets and `clarification_required`.
7. Post-lock audit findings do not invalidate the initial Gate B.2 evaluation premise.
8. The qualitative semantic granularity and downstream direct-dispatch value justify the operational complexity.

### 3.2 Conditions for `T2_FREEZE`
T2 may be frozen **only if all of the following criteria are satisfied**:
1. Coarse T2 functional boundaries remain coherent across annotators.
2. Specific fine distinctions in T3 show a documented, irreconcilable structural defect.
3. Collapsing those fine distinctions back into the coarse T2 parent class genuinely resolves that structural problem.
4. The project author explicitly accepts the operational trade-off of delegating fine operation routing to a secondary classifier.
5. **Downstream Subtype Notice:** Note that T2-H already uses a 16-class semantic subtype head; therefore, adopting T2 at the primary level does not eliminate the requirement for stable fine semantics downstream.

### 3.3 Conditions for `INCONCLUSIVE`
The outcome must be declared **`INCONCLUSIVE`** if:
1. Critical fine-grained splits lack sufficient challenge evidence or annotator coverage.
2. Shared functional boundaries fail or produce pervasive disagreement under both taxonomies.
3. Student prior exposure is found to materially undermine the validity of the human audit.
4. Unresolved reference label errors in the benchmark exceed defensible thresholds.
5. A definitive selection would require changing frozen candidate semantics mid-stream.

---

## 4. Definition of a Structural Taxonomy Defect

A disagreement or classification error is NOT automatically a structural defect. A **structural taxonomy defect** is defined strictly as a recurring, rule-level failure that:
1. Requires unavailable conversational context or physical route-solution knowledge to make a supposedly determinate classification; OR
2. Assigns incompatible, contradictory semantic meanings to the same grammatical construction; OR
3. Provides no coherent guideline policy for a recurring, natural commuter phrasing pattern; OR
4. Makes taxonomy conclusions materially dependent on arbitrary reference conventions rather than commuter intent.

---

## 5. Separation of Evidentiary Streams

Taxonomy decision tooling will **never** automatically declare a winner. The eventual final decision report must present five distinct evidentiary streams separately:
1. **Model-Side Evidence:** Gate B.2 strict ($+4.11\text{ pp}$) and ambiguity-aware ($+4.01\text{ pp}$) performance gains.
2. **Annotation-Stability Evidence:** Pairwise agreement, Jaccard similarity, and per-class positive agreement across student and model annotators.
3. **Reference-Concordance Evidence:** Post-lock alignment with the frozen reference key.
4. **Boundary-Audit Evidence:** All-350 item qualitative reconciliation and defect diagnosis.
5. **Course-Project Constraints:** Formal documentation of single-student scope, non-human IAA framing, and purposive sample limitations.

Only after each stream is fully populated will the project author record a binding decision.
