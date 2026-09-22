# Gate B.3 MODEL_G Execution Readiness Evidence Report

## Executive Summary

This report documents verified external evidence for **MODEL_G** (`Gemini 3.8 Flash (High)` via Antigravity selector `gemini-3.8-flash-high`) establishing formal execution readiness under the prospectively amended `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` protocol in the sterile workspace `/home/kaustubh/gate-b3-model-g-gemini`.

> [!IMPORTANT]
> **Governance Notice:**
> - **Benchmark Authorization:** **NO** (`benchmark_execution_authorized = false`).
> - **Real Benchmark Invocations:** **0**.
> - **Real Benchmark Outputs Created:** **NONE**.
> - **Architectural Web / Tool Disablement Claimed:** **NO**. Hard architectural/config-level tool disablement was NOT verified. The supported web isolation claim is strictly `ZERO_CALL_AUDITED`.
> - **Execution Isolation Class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`. Compliance is enforced by spawning fresh child processes in brand-new empty temporary working directories with zero observed semantic-child tool use, audited from execution telemetry.

---

## 1. Verified Execution Identity & Provenance

| Parameter | Observed / Verified Value | Provenance & Rationale |
| :--- | :--- | :--- |
| **Source ID** | `MODEL_G` | Active primary model annotator replacing retired MODEL_A and MODEL_B |
| **Provider** | `Google` | Model API provider |
| **Visible Model Identity** | `Gemini 3.8 Flash (High)` | Visible in Antigravity model selection interface |
| **Actual Execution Selector** | `gemini-3.8-flash-high` | Explicitly controllable execution variant selector |
| **Exact Immutable Revision** | `NOT_EXPOSED_BY_PROVIDER` | Provider does not expose an immutable snapshot checkpoint; documented truthfully |
| **Execution Surface** | `Antigravity` | Local agentic runtime interface |
| **Reasoning Configuration** | `mode = high, selection_mechanism = gemini-3.8-flash-high selector, effort_control_exposed = true` | High reasoning effort variant selected via selector/effort control |
| **Execution Isolation Class** | `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` | Process isolation with fresh context and empty working directory per query |
| **Web Isolation Claim** | `ZERO_CALL_AUDITED` | Behavioral verification: 0 web calls observed across all preflight and smoke invocations |
| **Architectural Web Disablement**| `NOT VERIFIED` | Not verifiable at config level; behavioral audit enforced |

---

## 2. Provenance Correction on Benchmark Inputs

> [!NOTE]
> **Clarification on Benchmark Input Handling During Preflight:**
> Frozen benchmark inputs were accessed only for byte-level integrity verification and structural annotation-ID validation. Benchmark query text/semantic contents were not inspected, sampled for meaning, or submitted to MODEL_G during preflight.

Benchmark input files (`model_g_t2_input.jsonl` and `model_g_t3_input.jsonl`) were:
- Byte-read to verify bitwise SHA-256 integrity against `data/nlp_v2/gate_b3/model_g_execution_manifest.json`;
- Structurally parsed to extract and validate the expected 350 `annotation_id` sequence (`ANN_B2_001` through `ANN_B2_350`).

At no point were benchmark query texts printed, reviewed by the operator, sampled for semantic interpretation, or used as model prompts. Real benchmark execution remains strictly zero (`0`).

---

## 3. Sterile Preflight & Hardening Evidence

Preflight verification conducted in sterile workspace `/home/kaustubh/gate-b3-model-g-gemini`:

```text
actual execution selector:
gemini-3.8-flash-high

visible identity:
Gemini 3.8 Flash (High)

provider:
Google

execution surface:
Antigravity

exact immutable revision:
NOT_EXPOSED_BY_PROVIDER

reasoning:
High execution variant / explicitly controllable via Antigravity model selector and --effort interface

architectural web/tool disablement:
NOT VERIFIED

supported web-isolation claim:
ZERO_CALL_AUDITED

fresh context per synthetic invocation:
VERIFIED

empty workdir per synthetic invocation:
VERIFIED

zero prohibited semantic-child tool use:
VERIFIED

execution isolation:
VERIFIED under EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION

synthetic smoke:
PASSED

real benchmark invocations:
0
```

Final hardened runner test evidence:
```text
runner tests:
31 / 31 PASS

final T2 synthetic smoke:
PASS (ANN_B2_994 -> response_status = VALID)

final T3 synthetic smoke:
PASS (ANN_B2_995 -> response_status = VALID)

format repairs:
0

semantic retries:
0

tool violations:
0

web calls:
0

external file reads:
0

command executions:
0
```

---

## 4. Invocation Accounting

Invocation logs from the sterile preflight and hardening phase were reconciled into mutually exclusive categories:

| Invocation Category | Count | Scope & Details |
| :--- | :--- | :--- |
| **Probe Invocations** | 8 | Antigravity CLI flags, model selector discovery (`gemini-3.8-flash-high`), stream-json format verification, raw telemetry parsing validation |
| **Formal / Synthetic Smoke Invocations** | 6 | Three rounds of 2 synthetic queries (T2 + T3): Round 1 (`ANN_B2_998`/`ANN_B2_999`), Round 2 (`ANN_B2_996`/`ANN_B2_997`), and Final Smoke (`ANN_B2_994`/`ANN_B2_995`) |
| **Benchmark Invocations** | **0** | Zero benchmark queries submitted to MODEL_G or executed as semantic annotation prompts.<br>Benchmark files were accessed only for byte-level hash verification and structural annotation-ID validation; query text/semantic contents were not inspected for meaning. |

**Critical Invariant:**
```text
REAL BENCHMARK INVOCATIONS = 0
```

---

## 5. Synthetic Smoke Test Summary

Final synthetic smoke testing executed under exact production runtime flags:
- `agy --model gemini-3.8-flash-high --new-project --disable-slash-commands --output-format stream-json --print <prompt>`
- Spawned in fresh, empty temp working directories (`/tmp/agy_empty_workdir_*`).
- Both T2 and T3 synthetic queries executed with zero format repairs, zero semantic retries, and terminal `SUCCESS` telemetry status.

| Test Item | Taxonomy | Annotation ID | Output Status | Format Repairs | Tool Calls | Result Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Synthetic Final T2 | T2 | `ANN_B2_994` | `VALID` | 0 | 0 | `SUCCESS` |
| Synthetic Final T3 | T3 | `ANN_B2_995` | `VALID` | 0 | 0 | `SUCCESS` |

Telemetry records preserved in:
- `telemetry/T2/ANN_B2_994.telemetry.jsonl`
- `telemetry/T3/ANN_B2_995.telemetry.jsonl`

Audit verified:
- `init_count == 1`
- `result_count == 1`
- `status == SUCCESS`
- `model == gemini-3.8-flash-high`
- `cwd == empty temp dir`
- Prohibited tools observed: 0
- Web calls observed: 0

---

## 6. Canonical Codebase Artifacts & SHA-256 Checksums

The hardened execution pipeline was copied into the canonical repository with path discovery mechanically adapted for canonical and fallback execution environments:

### Execution Pipeline Artifacts:
- **Canonical MODEL_G Runner:**
  `scripts/nlp_v2/gate_b3/model_g/run_model_g_gemini.py`  
  SHA-256: `932c567790f94b3b69a866520071c75174e35de0f59007d9a54ea603ddc5be4c`
- **Canonical MODEL_G Validator:**
  `scripts/nlp_v2/gate_b3/model_g/validate_model_g_outputs.py`  
  SHA-256: `7b50f7b505338097107db9c8704ecc286f65680ed8721113c8555cea9f92d4dc`
- **Canonical MODEL_G Execution Tests:**
  `tests/test_gate_b3_model_g_execution.py`  
  SHA-256: `36fe6fec32a531a18c552e571f3911f873dd2805653ab505ca419911e27133ba`  
  Test Result: **31 / 31 PASS**

### Canonical Configuration & Manifest Hashes:
- **Canonical MODEL_G Configuration SHA-256:**  
  `128e0736aa4a259d48b0c078d242212b71932a73f0af726fa2a14e0ad2f08d9c`
- **Historical Preflight MODEL_G Configuration SHA-256:**  
  `d4a359b72779ec15f42ffa0ba72beb57ff20ff765de901783082caee0deda1dd`
- **New Active Global Configuration SHA-256:**  
  `564501dc456ecb25ce661a439de68b2a31924844be3f19037afb130992fa0490`
- **Historical Pre-Readiness Active Global Configuration SHA-256:**  
  `b2aac9ceec68c906387a1e8521bf8538e5fd23f36b1c4e65a2f75f3a74e638df`
- **Canonical Sanitized Manifest File-Byte SHA-256 (`model_g_execution_manifest.json`):**  
  `54420aef23e895afb38528411d05c204338d43f81b6c9009a672a82dffd06707`

---

## 7. Readiness Checklist & Gate Status

```text
sterile workspace:
/home/kaustubh/gate-b3-model-g-gemini

actual selector:
gemini-3.8-flash-high

visible identity:
Gemini 3.8 Flash (High)

immutable revision:
NOT_EXPOSED_BY_PROVIDER

execution isolation:
EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION

web isolation:
ZERO_CALL_AUDITED

fresh context:
VERIFIED

empty workdir:
VERIFIED

zero-tool audit:
VERIFIED

synthetic smoke:
PASS

hardened execution tests:
31 / 31 PASS

real benchmark invocations:
0

real benchmark outputs:
NONE

benchmark authorization:
NO
```

**Status:**
`MODEL_G EXECUTION READY — WAITING FOR EXPLICIT BENCHMARK AUTHORIZATION`
