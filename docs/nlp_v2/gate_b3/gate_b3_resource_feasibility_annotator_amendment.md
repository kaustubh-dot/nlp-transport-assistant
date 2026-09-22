# Gate B.3 Resource-Feasibility / Annotator-Design Amendment

**Status:** ADOPTED  
**Date:** 2026-09-22  
**Authority:** NLP v2 Methodological Lead  
**Scope:** NLP v2 Gate B.3 Annotation-Stability and Semantic-Boundary Framework  
**Document Identifier:** `gate_b3_resource_feasibility_annotator_amendment.md`

---

## 1. Executive Summary

This formal methodology and provenance amendment modifies the Gate B.3 model-annotator design. The originally authorized two-heavy-model execution design (`MODEL_A` = GPT-6 Astra and `MODEL_B` = Claude Opus 4.6) proved operationally infeasible under external provider usage limits. 

This amendment retires bulk annotation by Astra and Claude, establishes **`MODEL_G` (Gemini 3.8 Flash)** as the sole active primary model annotator to pair with **`STUDENT_R1`**, preserves all historical pre-amendment execution telemetry and partial artifacts, and resets model-execution readiness and benchmark authorization.

---

## 2. Section A: Original Design

The originally frozen Gate B.3 model design called for two distinct frontier model families performing whole-sample blind annotation:

```text
MODEL_A = GPT-6 Astra (OpenAI / Codex)
MODEL_B = Claude Opus 4.6 (Anthropic / Antigravity isolated backend)

Workload per model:
- 350 T2 annotations
- 350 T3 annotations
Total planned per model: 700 annotations
Total planned model annotations: 1,400 annotations
```

The execution protocol required strict per-item behavioral isolation:
- Exactly **one query** per invocation;
- Exactly **one fresh model context** per query/taxonomy item;
- Total destruction of conversation state between items (`cross_query_history_allowed = false`);
- Behavioral tool restriction (`EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`).

---

## 3. Section B: Trigger for Amendment

The amendment was triggered by an operational resource constraint encountered during authorized benchmark execution:

1. **Usage-Limit Rejection:** During real authorized benchmark execution of `MODEL_A` (GPT-6 Astra) in the sterile workspace, the provider/Codex execution service rejected requests at query `ANN_B2_024` due to hard rate/quota limits.
2. **Execution Summary:** Prior to rejection, `MODEL_A` successfully completed 23 T2 benchmark queries with zero tool violations, zero semantic retries, and zero format repairs.
3. **Resource Constraint, Not Model Quality:** This amendment is strictly caused by external provider quota and rate-limit infeasibility under the required 1-query/1-fresh-context protocol. It does **not** reflect semantic failure, model quality degradation, or guideline inadequacy.

---

## 4. Section C: Timing of Amendment

The timing of this amendment is critical to methodological integrity:

```text
Timing Anchor:
Occurs AFTER partial real MODEL_A execution (23 items)
but strictly BEFORE:
- Gold or reference label access;
- Pairwise agreement or concordance analysis;
- Adjudication or reconciliation;
- First-pass lock declaration;
- Taxonomy selection (T2 vs T3);
- Gate C advancement.
```

Because the study remains completely blind to gold/reference truth and no agreement metrics or taxonomy comparisons were calculated, replacing the model annotator preserves valid scientific independence.

---

## 5. Section D: Replacement Design

The bulk model-annotation portion of Gate B.3 is reconstituted as follows:

```text
Primary Blind First-Pass Sources:
1. STUDENT_R1 (Human Student Reviewer)
   - 350 T2 annotations
   - 350 T3 annotations
   - Total: 700 annotations (counterbalanced 175/175 split)

2. MODEL_G (Gemini 3.8 Flash)
   - 350 T2 annotations
   - 350 T3 annotations
   - Total: 700 annotations (fresh context per item)

Total Primary Blind Annotation Judgments:
student = 700
Gemini  = 700
Total   = 1,400 judgments
```

Following first-pass locking of these 1,400 judgments and explicit reference-join authorization:
1. **Post-lock reference concordance:** computed programmatically after lock and explicit reference-join authorization.
2. **All-item gold-boundary audit:** author-led reconciliation by the student author over all 350 items.

---

## 6. Section E: Revised Role for GPT-6 Astra

`MODEL_A` (GPT-6 Astra) is **no longer a primary bulk annotator**:
- Astra does not contribute labels to the primary annotation dataset;
- Astra is **not** a third annotator in agreement metrics;
- The 23 partial T2 Astra annotations are excluded from final Gate B.3 metrics;
- Astra is reserved exclusively for occasional, high-level supervisory methodology review:
  1. Methodological review of this resource-feasibility amendment;
  2. Final qualitative review of locked Gate B.3 evidence and proposed taxonomy decisions.

---

## 7. Section F: Revised Role for Claude Opus 4.6

`MODEL_B` (Claude Opus 4.6) is **retired from primary bulk annotation**:
- Complete-sample whole-study annotation cannot be reliably supported under available provider quota;
- No real benchmark execution occurred for `MODEL_B` (`MODEL_B real benchmark output: NONE`);
- `MODEL_B` is formally archived as `RETIRED_PRE_COMPLETION` and excluded from primary Gate B.3 analysis.

---

## 8. Section G: Claims That Remain Permissible

The revised Gate B.3 empirical study supports rigorous, evidence-based scientific claims regarding:

1. **Student–Model Annotation Concordance:** Concordance between a human student annotator and an advanced instruction-following model (`STUDENT_R1 ↔ MODEL_G`).
2. **Annotation Stability:** Sensitivity of semantic intent classifications to taxonomy granularity (T2 12 classes vs T3 16 classes).
3. **Semantic-Boundary Behavior:** Comparative clarity and friction across boundary panels (e.g., sequence vs membership, p2p vs multimodal).
4. **Acceptable-Label Overlap & Jaccard:** Set-theoretic agreement over permissible multi-label interpretations.
5. **Clarification Concordance:** Invariant adherence and agreement on queries requiring clarifying dialogue.
6. **Contrast-Group Behavior:** Consistency of classification shifts across minimally distinct query variants.
7. **Post-Lock Reference Concordance:** Discrepancy decomposition (annotator error, guideline ambiguity, reference gap) against frozen reference truth.

---

## 9. Section H: Claims That Are No Longer Permissible

To prevent overclaiming or mischaracterization of the amended design, the following assertions are **explicitly forbidden**:

1. **NO Claim of Human Inter-Annotator Agreement (IAA):** The study employs one student and one model. This is not human IAA.
2. **NO Claim of Two-Model-Family Agreement:** Because Claude Opus 4.6 and GPT-6 Astra are not primary annotators, cross-model-family concordance cannot be asserted.
3. **NO Claim of Independent Dual-Model Validation:** There is only one active model annotator (`MODEL_G`).
4. **NO Claim of Statistical Independence between Student and Model:** The model and student operate under identical guidelines and schemas, but cannot be treated as statistically independent identically distributed raters.

---

## 10. Section I: MODEL_G Execution Protocol & Isolation Policy

`MODEL_G` must be executed under the exact behavioral-isolation protocol established by the Gate B.3 Execution-Isolation Amendment:

1. **One-Query / One-Fresh-Context:**
   - `fresh_context_per_item_required = true`
   - `cross_query_history_allowed = false`
   - Each query is annotated in a brand new, isolated context with zero memory of prior queries. Microbatching is strictly prohibited.
2. **Workspace Isolation:**
   - Canonical class: `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
   - `empty_workdir_required = true`
   - `benchmark_paths_provided_to_child = false`
3. **Tool Restriction & Audit:**
   - `actual_tool_use_allowed = false`
   - `zero_tool_use_audit_required = true`
   - Zero web calls, zero file access outside prompt input, zero command execution.
4. **Deterministic Error Handling:**
   - `semantic_retries = 0` (no retrying valid semantic output)
   - `format_repair_attempts = 1` (strict syntax recovery only)
   - `tool_violation_retry_attempts = 0`
   - `tool_violation_mode = HARD_FAIL_BATCH`
   - Transport/network execution failures may be retried only when no valid semantic response was accepted.

---

## 11. Section J: Reset of Benchmark Authorization

All previous benchmark authorizations granted to `MODEL_A` and `MODEL_B` are revoked and do **not** transfer to `MODEL_G`.

The active status of `MODEL_G` is initialized to:
- `configuration_frozen = true`
- `execution_isolation_verified = false`
- `synthetic_smoke_test_passed = false`
- `benchmark_execution_authorized = false`
- `execution_timestamp = null`

Overall Gate B.3 state returns to:
```text
STATUS: WAITING FOR MODEL_G PREFLIGHT / SMOKE TEST
```
No real benchmark queries may be submitted to `MODEL_G` until sterile-workspace isolation is verified and synthetic smoke testing passes.
