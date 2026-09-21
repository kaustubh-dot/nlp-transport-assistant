# Gate B.3 Benchmark Execution Authorization

## Authorization Record

This document records formal benchmark execution authorization for the frozen and execution-ready Gate B.3 model annotator pair: **MODEL_A** (`GPT-6 Astra` / Codex) and **MODEL_B** (`Claude Opus 4.6` / Antigravity isolated backend) under the `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` protocol.

---

## 1. Model Authorization Status

### MODEL_A:
- **Model:** `GPT-6 Astra` (OpenAI)
- **Execution Surface:** Codex
- **Isolation Class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **Execution Ready:** YES
- **Synthetic Smoke Test:** PASS
- **Runner:** READY
- **Validator:** READY
- **Authorized:** YES

### MODEL_B:
- **Model:** `Claude Opus 4.6` (Anthropic)
- **Execution Surface:** Antigravity / isolated Claude execution backend
- **Isolation Class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **Execution Ready:** YES
- **Synthetic Smoke Test:** PASS
- **Runner:** READY
- **Validator:** READY
- **Authorized:** YES

---

## 2. Authorization Governance & Provenance

This authorization was granted after:
- prospective execution-isolation amendment (`EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`),
- sterile execution preflights in isolated workspaces (`Astra_testing` and `gate-b3-model-b-claude`),
- amended synthetic smoke tests with full telemetry inspection,
- zero-tool-use audit verification (0 tool calls, 0 web calls, 0 external file reads, 0 command executions observed),
- runner/validator readiness review and automated unit-test validation.

No real benchmark model invocation had occurred before authorization.

Hard architectural tool isolation is not claimed.

---

## 3. Strict Execution Non-Commencement Boundaries

> [!IMPORTANT]
> **Authorization does not constitute annotation execution.**
>
> At authorization commit:
> - `annotation_started` = false
> - `real benchmark invocations` = 0
> - `annotation output files` = none
> - `first_pass_locked` = false
> - `reference_join_enabled` = false
> - `taxonomy decision` = PENDING
> - `gold_boundary_audit_started` = false
> - `execution_timestamp` = null

Actual benchmark execution occurs only after external verification of this authorization commit and after the newly authorized manifests are recopied into both sterile workspaces.

---

## 4. Cryptographic Checksums at Authorization

- **MODEL_A Configuration SHA-256:** `5db1c4aeae9e8cabb98a5b20637488c6812a826d27cbf4ed4cd578d28038fe5c` (invariant)
- **MODEL_B Configuration SHA-256:** `3d9264b1172878ed07080d1ca4e087170aa83fd366f8695effbf32297318020c` (invariant)
- **Global Configuration SHA-256:** `2a7c82b9297f65f750f5f72685d329d2e65e40c0691b09546802d8cd727afc8e` (invariant)
- **Amendment SHA-256:** `a48b732a9373a8e2d65ab3963b1920a658ada1e3c703687b8d2d072f46e87f19` (invariant)
- **MODEL_A Authorized Manifest File Byte SHA-256:** `17f30bb2178ceb6eda72c5b713c4c1938d5bf0147642fa931d6491a3a7bdd057`
- **MODEL_B Authorized Manifest File Byte SHA-256:** `607df806d33fb77194d64b741ed424697f05d0d64c9188512eebd8104930627a`
