# Gate B.3 Pre-Amendment Model Execution Provenance Report

**Status:** ARCHIVED EXECUTION EVIDENCE (PRE-AMENDMENT)  
**Date:** 2026-09-22  
**Framework:** NLP v2 Gate B.3 Annotation-Stability and Semantic-Boundary Audit  
**Document Identifier:** `GATE_B3_PRE_AMENDMENT_MODEL_EXECUTION_PROVENANCE.md`

---

## 1. Executive Summary

This report documents the empirical provenance, execution telemetry, and verified termination facts for the initial authorized execution attempt of the two-heavy-model design (`MODEL_A` = GPT-6 Astra and `MODEL_B` = Claude Opus 4.6).

Authorized benchmark execution was halted following provider rate and usage limit rejections on `MODEL_A`. In accordance with the *Gate B.3 Resource-Feasibility / Annotator-Design Amendment* (`gate_b3_resource_feasibility_annotator_amendment.md`), all pre-amendment execution outputs are preserved for forensic provenance but formally classified as **aborted and excluded from primary Gate B.3 analysis**.

> [!IMPORTANT]
> **Strict Analytical Prohibition:**  
> No partial pre-amendment Astra or Claude annotations may be used in final primary stability metrics, pairwise agreement rates, acceptable-set calculations, boundary panels, or taxonomy decisions.

---

## 2. MODEL_A (GPT-6 Astra) Verified Partial Facts

| Attribute | Verified Value | Notes |
| :--- | :--- | :--- |
| **Model Source ID** | `MODEL_A` | OpenAI / GPT-6 Astra |
| **Execution Environment** | `Codex` | Sterile workspace `Astra_testing` |
| **Authorized Manifest File SHA-256** | `17f30bb2178ceb6eda72c5b713c4c1938d5bf0147642fa931d6491a3a7bdd057` | Bitwise match to authorization commit |
| **Canonical Configuration SHA-256** | `5db1c4aeae9e8cabb98a5b20637488c6812a826d27cbf4ed4cd578d28038fe5c` | Frozen config specification |
| **Isolation Class** | `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` | Fresh context per item |
| **T2 Accepted Annotations** | `23 / 350` | `ANN_B2_001` through `ANN_B2_023` |
| **T3 Accepted Annotations** | `0 / 350` | Not started |
| **Total Accepted Benchmark Items** | `23` | |
| **Next Attempted Item** | `ANN_B2_024` | Request rejected by provider |
| **Termination Cause** | Provider / Codex usage-limit rejection | Quota exhaustion under 1-query/1-fresh-context protocol |
| **Tool Violations Observed** | `0` | Zero web calls, zero file accesses, zero commands |
| **Semantic Retries** | `0` | Zero invalid semantic retries |
| **Format Repair Attempts** | `0` | All 23 accepted outputs met schema on first pass |
| **Partial T2 Output SHA-256** | `f7f58fe8670262f9ab41c3477aa527db417aae87e2cd1a9eb31dea8760edc988` | From sterile workspace `Astra_testing` |
| **Gold / Reference Accessed** | `NO` | Execution remained strictly blind |
| **MODEL_B Outputs Accessed** | `NO` | Total annotator isolation maintained |
| **Student Outputs Accessed** | `NO` | Total annotator isolation maintained |
| **Status Classification** | `ABORTED_PRE_AMENDMENT_EXECUTION` | Formally excluded from primary analysis |
| **Primary Analysis Inclusion** | `NO` | Excluded from primary Gate B.3 dataset |

---

## 3. MODEL_B (Claude Opus 4.6) Verified Facts

| Attribute | Verified Value | Notes |
| :--- | :--- | :--- |
| **Model Source ID** | `MODEL_B` | Anthropic / Claude Opus 4.6 |
| **Execution Environment** | `Antigravity / isolated Claude backend` | Sterile workspace `gate-b3-model-b-claude` |
| **Authorized Manifest File SHA-256** | `607df806d33fb77194d64b741ed424697f05d0d64c9188512eebd8104930627a` | Bitwise match to authorization commit |
| **Canonical Configuration SHA-256** | `3d9264b1172878ed07080d1ca4e087170aa83fd366f8695effbf32297318020c` | Frozen config specification |
| **Real Benchmark Execution** | `NOT COMPLETED / NONE RECORDED` | Execution not commenced |
| **Real Benchmark Output** | `NONE` | No benchmark outputs generated |
| **T2 Accepted Annotations** | `0 / 350` | None |
| **T3 Accepted Annotations** | `0 / 350` | None |
| **Gold / Reference Accessed** | `NO` | Isolation preserved |
| **Status Classification** | `RETIRED_PRE_COMPLETION` | Retired due to provider quota infeasibility |
| **Primary Analysis Inclusion** | `NO` | Excluded from primary Gate B.3 dataset |

---

## 4. Preservation and Data Handling Protocol

1. **Non-Destruction of Sterile Artifacts:**  
   The partial annotation outputs, raw telemetry, failure logs, and execution manifests in the sterile workspaces (`Astra_testing` and `gate-b3-model-b-claude`) are preserved as empirical audit evidence. They must **not** be deleted or overwritten.
2. **Strict Quarantine from Active Pipeline:**  
   The partial 23 Astra annotations will not be merged, concatenated, or ingested into any active dataset or analysis script.
3. **No Metric Contamination:**  
   The primary agreement calculations for Gate B.3 will evaluate exclusively the amended active pair: `STUDENT_R1` ↔ `MODEL_G` (Gemini 3.8 Flash).
