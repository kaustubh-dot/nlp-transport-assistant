# Gate B.3 Annotation-Methodology Amendment

**Document:** `docs/nlp_v2/gate_b3/gate_b3_annotation_methodology_amendment.md`  
**Status:** Approved Prospective Methodology Amendment  
**Date:** 2026-09-20  
**Repository:** `https://github.com/kaustubh-dot/nlp-transport-assistant`  
**Base Commit:** `51c7d74d6e38fef8795b5a04b711e8a17b7e2608`  
**Active Knowledge Base:** `chennai_multimodal_v1.2.2`  

---

## 1. Executive Summary

This document establishes a **prospective annotation-methodology amendment** for the intent taxonomy evaluation phase of NLP v2.

In Gate B.2, model-side taxonomy confirmation demonstrated empirical gains for the fine-grained T3 taxonomy over the hierarchical T2-H architecture:
- **T2-H strict exact operation accuracy:** $0.7531 \pm 0.0024$
- **T3 strict exact operation accuracy:** $0.7941 \pm 0.0291$
- **Strict difference ($T3 - T2\text{-}H$):** $+4.11\text{ pp}$ ($95\%\text{ CI } [+0.0245, +0.0581]$, empirical $p < 0.002$)
- **Corrected ambiguity-aware accuracy:**
  - T2-H: $0.7668 \pm 0.0084$
  - T3: $0.8069 \pm 0.0306$
  - Difference: $+4.01\text{ pp}$

The next evaluation phase originally contemplated an external human inter-annotator agreement study. Following methodology review, that protocol has been superseded due to university course-project resource constraints.

---

## 2. Original Plan and Rationale for Amendment

### 2.1 Original Plan
The original Gate B.2 planning documents specified recruiting **two external independent human reviewers** (R1 and R2) completely unfamiliar with the project to annotate the 350-query challenge sample under both T2 and T3 taxonomies, followed by standard human inter-annotator agreement (Cohen's $\kappa$) and third-party adjudication.

### 2.2 Why Amended
Recruiting, onboarding, and training two qualified external bilingual (English + Tamil/Hindi/code-switched) human annotators is **infeasible within the time, operational, and budgetary scope of this university/course project**.

Attempting a token or simulated external human study would introduce artificial credibility claims. Therefore, an explicit, Astra-approved methodology amendment has been adopted.

---

## 3. Replacement Study Design

The amended protocol is formally designated:
$$\textbf{Gate B.3 Annotation-Stability and Semantic-Boundary Audit}$$

The replacement design consists of four interlocking, reproducible components:
1. **One Student Blind Annotation Audit (`STUDENT_R1`):**
   - The student author annotates all 350 queries under both T2 and T3.
   - To reduce immediate carry-over effects, the 350 queries are deterministically divided into two halves (175/175). Half A receives T2 first, then T3 later; Half B receives T3 first, then T2 later.
   - First-pass and second-pass presentation orders are independently shuffled using deterministic SHA-256 logic.
   - The interface records a mandatory descriptive diagnostic: `recognized_from_prior_work` (`true`, `false`, `unsure`).
2. **Two Isolated Model Annotator Configurations (`MODEL_A` and `MODEL_B`):**
   - Two distinct model configurations annotate the identical 350 queries under T2 and T3 in complete isolation (zero repo access, zero cross-query conversational memory, zero gold labels, zero performance information).
   - Preferentially drawn from different model families.
3. **Post-Lock Reference Concordance:**
   - Evaluated strictly *after* all first-pass student and model annotations are validated, hashed, and cryptographically locked.
   - Compares primary and acceptable-set alignments against the frozen benchmark reference.
4. **All-Item Gold-Boundary Audit (Author-Led Reconciliation):**
   - A systematic qualitative audit of all 350 items (not merely disagreement cases) by the student author to diagnose root causes across 10 structured categories.

---

## 4. Critical Methodological Limitations

> [!CAUTION]
> ### Crucial Limitation: This Study Does NOT Estimate Human IAA
> This study does **NOT** measure independent human inter-annotator agreement. It cannot and must not be used to claim that "two independent humans validated the taxonomy."
>
> All historical documentation referencing "human IAA" is strictly superseded.

### 4.1 Permitted vs. Forbidden Terminology

| Permitted Terminology | Strictly Forbidden Terminology |
| :--- | :--- |
| student blind review | human inter-annotator agreement (IAA) |
| model annotator | human agreement |
| model-annotator agreement | independent human agreement |
| cross-model annotation stability | two-human validation |
| student-model agreement | human labelability score |
| reference concordance | verified human truth |
| gold-boundary audit | independent human adjudication |
| author-led reconciliation | objective external benchmark |
| semantic-boundary audit | human consensus score |

Historical documents (such as `docs/nlp_v2/gate_b2_human_annotation_guide.md`) remain in the repository as immutable historical artifacts of the Gate B.2 planning stage, but are explicitly superseded by this document for all Gate B.3 and subsequent work.

### 4.2 Purposive / Enriched Challenge Sample Limitation
The 350-query blind set (`data/nlp_v2/gate_b2/human_annotation_blind.csv`) is a **purposive, enriched challenge sample** sampled from the Gate B.2 stress-evaluation set. It is deliberately biased toward:
- Ambiguous and multi-intent expressions
- Code-switched and transliterated phrasing
- Boundary-defining contrast queries
- Complex route and timing subtypes

Therefore:
- It must **NOT** be characterized as a representative random sample of commuter traffic.
- It must **NOT** be characterized as a balanced population sample.
- It does **NOT** guarantee complete minimal-pair or contrast-group coverage (individual challenge queries were sampled without enforcing that every partner query from a multi-utterance contrast group was selected).

Under no circumstances will the 350 queries be resampled to artificially "fix" this property; the sample is frozen and its exact structure is documented as an empirical scope limitation.

---

## 5. Timing Disclosure

This prospective methodology amendment was formalized:
- **After** the aggregate Gate B.2 model-side confirmation results ($T3 - T2\text{-}H = +4.11\text{ pp}$) were produced and verified;
- **Before** any replacement student or model annotator labeling began.

This amendment is a **prospective annotation-methodology amendment**, not a full pre-study preregistration of the entire multi-phase research effort.

---

## 6. Model Independence and Provenance Principles

1. `MODEL_A` and `MODEL_B` represent separate model-annotator configurations executed independently.
2. Separate execution does **not** imply statistically independent annotator populations: different LLM architectures and API services may share pre-training corpora, common RLHF priors, and synthetic training data.
3. Consequently, model-model agreement measures **cross-model annotation stability under explicit operational guidelines**, rather than human conceptual clarity.
4. **Astra-Specific Provenance Guardrail:** If an Astra / Gemini model configuration is selected as `MODEL_A` or `MODEL_B`, the context/conversation used for methodology discussion or project planning must **NEVER** be reused for annotation. Any model run must occur in a sterile, isolated context receiving only the approved annotation guide, the schema, and a single blind query.
