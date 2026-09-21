# Gate B.3 Model Execution Readiness Evidence Report

## Overview

This report documents verified external evidence for **MODEL_A** (`GPT-6 Astra` / Codex) and **MODEL_B** (`Claude Opus 4.6` / Antigravity isolated backend) demonstrating execution readiness under the prospectively amended `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` protocol.

> [!IMPORTANT]
> **Governance Notice:**
> This readiness record is based on sterile-workspace execution evidence reviewed before benchmark authorization.
>
> Hard architectural tool isolation is not claimed.
>
> Benchmark execution remains strictly unauthorized (`benchmark_execution_authorized = false`). Real benchmark model invocations remain 0. No benchmark queries have been annotated, and no annotation output files exist.

---

## 1. Verified Evidence Summary

### MODEL_A — GPT-6 Astra / Codex

- **Model:** `gpt-6-astra`
- **Provider:** OpenAI
- **Execution Surface:** Codex
- **Reasoning Effort:** Medium verified
- **Isolation Class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **Amended Synthetic Smoke Test:** PASS
- **Fresh Context per Item:** VERIFIED
- **Empty Workdir per Item:** VERIFIED
- **User Config Excluded:** VERIFIED
- **Rules Excluded:** VERIFIED
- **Web Search Config:** DISABLED VERIFIED
- **Structured Output:** PASS
- **Format Repair Used:** NO (Format repair invocations: 0)
- **Semantic Invocations:** 1 (smoke test item only)
- **Raw Telemetry Preserved:** YES
- **Tool Calls Observed:** 0
- **Web Calls Observed:** 0
- **External File Reads Observed:** 0
- **Command Executions Observed:** 0
- **Benchmark Path Provided to Child:** NO
- **Benchmark Content Provided to Child:** NO
- **Gold/Reference Data Accessed:** NO
- **MODEL_B Content Accessed:** NO
- **Student Content Accessed:** NO
- **Runner Status:** READY
- **Validator Status:** READY
- **Local Runner/Validator Tests:** 33/33 PASS
- **Real Benchmark Invocations:** 0
- **Benchmark Outputs Created:** NONE

### MODEL_B — Claude Opus 4.6 / Antigravity

- **Model:** `Claude Opus 4.6 (Thinking)`
- **Provider:** Anthropic
- **Execution Surface:** Antigravity / isolated Claude execution backend
- **Thinking Control:** `NOT_EXPOSED_BY_EXECUTION_SURFACE` (fixed thinking effort not exposed)
- **Isolation Class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **Amended Synthetic Smoke Test:** PASS
- **Fresh Context per Item:** VERIFIED
- **Empty Workdir per Item:** VERIFIED
- **Inherited Generic Rules:** YES — DOCUMENTED
- **Global Rules Project-Specific:** NO VERIFIED
- **Rules Excluded:** NO — generic global rules remain inherited
- **Web Isolation:** ZERO_CALL_AUDITED
- **Structured Output:** PASS
- **Format Repair Used:** NO (Format repair invocations: 0)
- **Semantic Invocations:** 1 (smoke test item only)
- **Raw Telemetry Preserved:** YES
- **Tool Calls Observed:** 0
- **Web Calls Observed:** 0
- **External File Reads Observed:** 0
- **Command Executions Observed:** 0
- **Benchmark Path Provided to Child:** NO
- **Benchmark Content Provided to Child:** NO
- **Gold/Reference Data Accessed:** NO
- **MODEL_A Content Accessed:** NO
- **Student Content Accessed:** NO
- **Runner Status:** READY
- **Validator Status:** READY
- **Local Runner/Validator Test Count:** NOT SEPARATELY REPORTED
- **Real Benchmark Invocations:** 0
- **Benchmark Outputs Created:** NONE

---

## 2. External Evidence Verification Detail

### MODEL_A Formal Amended Smoke Test Evidence

```text
PACKAGE HASHES: PASS
ISOLATION CLASS: EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION
MODEL: gpt-6-astra
MODEL SELECTION: VERIFIED
REASONING: MEDIUM VERIFIED
FRESH CONTEXT PER ITEM: VERIFIED
EMPTY WORKDIR: VERIFIED
USER CONFIG EXCLUDED: VERIFIED
RULES EXCLUDED: VERIFIED
WEB SEARCH CONFIG: DISABLED VERIFIED
STRUCTURED OUTPUT: PASS
FORMAT REPAIR USED: NO
SEMANTIC INVOCATIONS: 1
FORMAT REPAIR INVOCATIONS: 0
RAW TELEMETRY PRESERVED: YES
TOOL CALLS OBSERVED: 0
WEB CALLS OBSERVED: 0
EXTERNAL FILE READS OBSERVED: 0
COMMAND EXECUTIONS OBSERVED: 0
BENCHMARK PATH PROVIDED TO CHILD: NO
BENCHMARK CONTENT PROVIDED TO CHILD: NO
GOLD/REFERENCE ACCESSED: NO
MODEL_B CONTENT ACCESSED: NO
STUDENT CONTENT ACCESSED: NO
REAL BENCHMARK INVOCATIONS: 0
BENCHMARK OUTPUT FILES CREATED: NO
SYNTHETIC SMOKE TEST: PASS
FRESH_CONTEXT_PER_ITEM_VERIFIED: YES
EMPTY_WORKDIR_VERIFIED: YES
ZERO_TOOL_USE_AUDIT_VERIFIED: YES
RECOMMEND EXECUTION_ISOLATION_VERIFIED: YES
```

### MODEL_A Runner/Validator Finalization

```text
MODEL INVOCATIONS DURING FINALIZATION: 0
REAL BENCHMARK INVOCATIONS: 0
BENCHMARK INPUT SEMANTIC INSPECTION: NO

RUNNER: READY
VALIDATOR: READY

AUTHORIZATION FALSE BLOCKS EXECUTION: PASS
EMPTY WORKDIR PER ITEM: ENFORCED
FRESH CONTEXT PER ITEM: ENFORCED
MODEL: gpt-6-astra
REASONING: medium
WEB SEARCH: DISABLED BY RUNNER
ZERO-TOOL AUDIT: ENFORCED
TOOL VIOLATION: HARD_FAIL_BATCH
TOOL VIOLATION RETRIES: 0
SEMANTIC RETRIES: 0
FORMAT REPAIR MAX: 1
RAW TELEMETRY: REQUIRED
RESUME SAFETY: PASS
VALIDATOR EXACT 350: ENFORCED
VALIDATOR EXACT ID SET: ENFORCED
VALIDATOR ZERO-TOOL EVIDENCE: ENFORCED
MOCK/UNIT TESTS: 33/33 PASS
BENCHMARK OUTPUT FILES CREATED: NO
FROZEN MANIFEST MODIFIED: NO
PROTOCOL FILES MODIFIED: NO
```

### MODEL_B Formal Amended Smoke Test Evidence

```text
PACKAGE HASHES: PASS
ISOLATION CLASS: EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION
MODEL: Claude Opus 4.6 (Thinking)
MODEL IDENTITY: VERIFIED
THINKING CONTROL: NOT_EXPOSED_BY_EXECUTION_SURFACE
FRESH CONTEXT PER ITEM: VERIFIED
EMPTY WORKDIR: VERIFIED
GLOBAL GENERIC RULES: INHERITED
GLOBAL RULES PROJECT-SPECIFIC: NO VERIFIED
STRUCTURED OUTPUT: PASS
FORMAT REPAIR USED: NO
SEMANTIC INVOCATIONS: 1
FORMAT REPAIR INVOCATIONS: 0
RAW TELEMETRY PRESERVED: YES
TOOL CALLS OBSERVED: 0
WEB CALLS OBSERVED: 0
EXTERNAL FILE READS OBSERVED: 0
COMMAND EXECUTIONS OBSERVED: 0
BENCHMARK PATH PROVIDED TO CHILD: NO
BENCHMARK CONTENT PROVIDED TO CHILD: NO
GOLD/REFERENCE ACCESSED: NO
MODEL_A CONTENT ACCESSED: NO
STUDENT CONTENT ACCESSED: NO
REAL BENCHMARK INVOCATIONS: 0
BENCHMARK OUTPUT FILES CREATED: NO
RUNNER: READY
VALIDATOR: READY
FROZEN MANIFEST MODIFIED: NO
SYNTHETIC SMOKE TEST: PASS
FRESH_CONTEXT_PER_ITEM_VERIFIED: YES
EMPTY_WORKDIR_VERIFIED: YES
ZERO_TOOL_USE_AUDIT_VERIFIED: YES
RECOMMEND EXECUTION_ISOLATION_VERIFIED: YES
```

---

## 3. Protocol and Integrity Verification

- **MODEL_A Configuration SHA-256:** `5db1c4aeae9e8cabb98a5b20637488c6812a826d27cbf4ed4cd578d28038fe5c` (intact)
- **MODEL_B Configuration SHA-256:** `3d9264b1172878ed07080d1ca4e087170aa83fd366f8695effbf32297318020c` (intact)
- **Global Configuration SHA-256:** `2a7c82b9297f65f750f5f72685d329d2e65e40c0691b09546802d8cd727afc8e` (intact)
- **Amendment SHA-256:** `a48b732a9373a8e2d65ab3963b1920a658ada1e3c703687b8d2d072f46e87f19` (intact)
- **MODEL_A Sanitized Manifest File Byte SHA-256:** `14883117c1caa39269493d2f16a78031c3454a84ac075d87dbbd4fb8dc4841cf`
- **MODEL_B Sanitized Manifest File Byte SHA-256:** `aabe3e255f1d1d770ffbc2ec29f32acb52f9c4c47c4a32a4c95ee380932aecfb`

---

## 4. Current Execution Status

```text
STATUS: READY FOR FINAL BENCHMARK AUTHORIZATION REVIEW
BENCHMARK EXECUTION AUTHORIZED: NO
ANNOTATION STARTED: NO
REAL BENCHMARK INVOCATIONS: 0
BENCHMARK OUTPUT FILES: NONE
```
