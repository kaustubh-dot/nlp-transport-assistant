# Gate B.3 MODEL_G Post-Authorization Test Invocation Incident Report

## 1. Incident Provenance & Scope

* **Execution-Start Commit**: `2d1e61038514ef082ddb971647b81112938442a2`
* **Authorization Commit**: `ef9d85d56182b22e7cd3e650d935db728b53c9bf`
* **Triggering Event**: Pre-commit test verification command (`pytest tests/test_gate_b3_annotation_framework.py tests/test_gate_b3_model_g_execution.py`) executed from canonical repository `/home/kaustubh/projects/NLP`.
* **Execution Timestamp**: `2026-09-22T22:59:33+05:30` (start) to `2026-09-22T23:16:42+05:30` (killed via task management cancellation).
* **Incident Classification**: **`ACCEPTED_RECORD_EXISTS`**

---

## 2. Root Cause Analysis

In `tests/test_gate_b3_model_g_execution.py`, the test class `TestHardenedModelGPipeline.setUp()` previously inspected the environment and filesystem to resolve `self.workspace_root`:

```python
sterile_candidate = Path("/home/kaustubh/gate-b3-model-g-gemini")
if env_ws and (Path(env_ws) / "protocol").exists() and (Path(env_ws) / "inputs").exists():
    self.workspace_root = Path(env_ws)
elif sterile_candidate.exists() and (sterile_candidate / "protocol").exists() and (sterile_candidate / "inputs").exists():
    self.workspace_root = sterile_candidate
```

Prior to benchmark authorization, `/home/kaustubh/gate-b3-model-g-gemini/protocol/model_g_execution_manifest.json` contained `benchmark_execution_authorized = false`. Under that pre-authorization state, negative authorization tests such as:
- `test_01_renamed_benchmark_input_blocked_by_hash`
- `test_02_copied_benchmark_input_blocked_by_hash`
- `test_25_benchmark_authorization_false_remains_fail_closed`

called `run_batch()` on benchmark-hashed inputs and verified that `BenchmarkNotAuthorizedError` was raised.

However, once benchmark execution was authorized and the authorized manifest was transferred to the sterile workspace, `benchmark_execution_authorized` became `true` in `/home/kaustubh/gate-b3-model-g-gemini`. Consequently, when `test_01` ran against `self.workspace_root`:
1. `check_benchmark_authorization(workspace_root)` evaluated to `True`.
2. `run_batch()` bypassed the negative-authorization exception and proceeded to execute batch items sequentially.
3. `run_batch()` invoked `annotate_single_query()`, spawning fresh `agy` subprocesses in `/tmp/agy_empty_workdir_*`.
4. Items `ANN_B2_001` through `ANN_B2_030` were annotated, schema-validated, accepted, and recorded atomically to the test output file `/tmp/tmpkg1xcg52/out.jsonl`.
5. At item `ANN_B2_031`, the test task was observed running and killed via SIGTERM/SIGKILL before item 31 could complete.

---

## 3. Forensic Evidence Audit (Read-Only)

Inspection of task logs (`task-642.log`) and `/tmp` filesystem state revealed:

```text
ACTIVE TEST WHEN TERMINATED:
test_01_renamed_benchmark_input_blocked_by_hash

RUN_BATCH REACHED ANNOTATE_SINGLE_QUERY:
YES

AGY PROCESS SPAWNED:
YES (ephemeral working directories /tmp/agy_empty_workdir_* created)

TAXONOMY INVOLVED:
T2

ANNOTATION IDS INVOLVED:
ANN_B2_001 through ANN_B2_030 (completed and accepted)
ANN_B2_031 (active / interrupted when killed)

INIT EVENT OBSERVED:
YES for ANN_B2_001 .. ANN_B2_030
UNRESOLVED for ANN_B2_031 (process killed while subprocess.run buffered in memory)

CONVERSATION IDS:
YES, unique conversation IDs observed for each of ANN_B2_001 .. ANN_B2_030
(e.g., ANN_B2_001: b35b2a53-9f41-426c-8264-5260402e2ea6, ANN_B2_030: 033361e0-64dd-47df-be4b-c94652ca5767)
UNRESOLVED for ANN_B2_031

TERMINAL RESULT:
SUCCESS for ANN_B2_001 .. ANN_B2_030
NONE / INTERRUPTED for ANN_B2_031

TOOL CALLS / DENIED ACTIONS:
0 (zero observed tool calls across all 30 completed items)

ACCEPTED RECORDS WRITTEN:
YES (30 records in /tmp/tmpkg1xcg52/out.jsonl)

TELEMETRY PERSISTED:
YES (30 files in /tmp/tmpkg1xcg52/tel/T2/ANN_B2_*.telemetry.jsonl)

INVOCATION INTERRUPTED BEFORE SEMANTIC COMPLETION:
YES (specifically for active item ANN_B2_031)
```

---

## 4. Invocation Accounting Breakdown

To ensure absolute audit transparency, invocations are strictly distinguished:

```text
Intentional Official Benchmark Invocations:
0

Test-Triggered Benchmark Invocation Attempts:
31 (ANN_B2_001 through ANN_B2_031)

Completed Semantic Responses:
30 (ANN_B2_001 through ANN_B2_030)

Accepted Records Produced:
30 (in test temporary directory /tmp/tmpkg1xcg52/out.jsonl)
0 (in official sterile workspace or canonical repository)
```

---

## 5. Official Workspace & Canonical Integrity Audit

The live sterile workspace and canonical repository were verified completely unpolluted:

* **Official Sterile Workspace (`/home/kaustubh/gate-b3-model-g-gemini`)**:
  - `outputs/`: strictly contains historical synthetic preflight outputs; zero benchmark records written.
  - `telemetry/`: strictly contains historical synthetic preflight telemetry; zero benchmark telemetry files written.
  - Official output modified: **NO**
  - Official telemetry modified: **NO**
* **Canonical Repository (`/home/kaustubh/projects/NLP`)**:
  - `data/nlp_v2/gate_b3/`: zero benchmark outputs written.
  - All configuration and manifest files intact.

### Preservation of Test Artifacts
In accordance with classification `ACCEPTED_RECORD_EXISTS`, all 30 accepted records and 30 telemetry files generated in `/tmp/tmpkg1xcg52` have been preserved to:
`/home/kaustubh/.gemini/antigravity/brain/fe0d234d-9317-4b66-9458-01ff41fe1c9f/scratch/incident_test_01_artifacts/`

---

## 6. Corrective Test-Isolation Patch

`tests/test_gate_b3_model_g_execution.py` was patched with 5 independent defense-in-depth layers:

1. **Elimination of Sterile Workspace Dependency**:
   Removed automatic lookup of `/home/kaustubh/gate-b3-model-g-gemini` and `MODEL_G_WORKSPACE_ROOT`. The test harness now constructs an isolated ephemeral workspace via `create_isolated_workspace(benchmark_authorized=False)` from canonical fixture files for every test run.
2. **Explicit Test-Controlled Authorization State**:
   Negative-authorization tests operate strictly against temporary manifest copies where `benchmark_execution_authorized` is explicitly set to `false`. The canonical manifest in `data/nlp_v2/gate_b3/` remains untouched (`true`).
3. **Semantic Boundary Mocking**:
   Negative authorization tests (`test_01`, `test_02`, `test_03`, `test_25`) explicitly `@patch("run_model_g_gemini.annotate_single_query")` with `side_effect = AssertionError(...)`. If the negative-authorization guard fails, the test fails immediately without reaching semantic execution.
4. **Runner-Level Execution Guard**:
   `run_model_g_gemini.execute_single_invocation` is patched at module import to `guarded_execute_single_invocation`, which raises `LiveAgyExecutionAttemptError` on any unmocked call.
5. **Subprocess-Level Process Guard**:
   `run_model_g_gemini.subprocess.run` is guarded to intercept any command list or string containing `"agy"` and immediately raise `LiveAgyExecutionAttemptError`.

### Regression Test Suite
Five regression tests were added (tests 32–36):
- `test_32_regression_sterile_workspace_never_consulted`: verifies active workspace is always in tempdir, never sterile workspace.
- `test_33_regression_negative_authorization_uses_temporary_unauthorized_manifest`: verifies test uses unauthorized manifest copy while canonical manifest remains authorized.
- `test_34_regression_run_batch_authorization_tests_cannot_spawn_agy`: verifies `run_batch` cannot launch `agy` even under authorized workspace.
- `test_35_regression_semantic_subprocess_mocked_in_unit_tests`: verifies guard interceptors are active.
- `test_36_guard_fails_if_unit_test_invokes_agy`: verifies direct attempt to invoke `agy` raises `LiveAgyExecutionAttemptError`.

Test execution verification:
- `pytest tests/test_gate_b3_model_g_execution.py`: 36 passed in 0.10s (zero subprocess/network calls).
- Ordinary non-model framework tests: 89 passed in 7.97s.

---

## 7. Cryptographic Invariant Baseline Verification

The authorized Gate B.3 execution surface remains 100% bitwise intact:

```text
MODEL_G CONFIG:
128e0736aa4a259d48b0c078d242212b71932a73f0af726fa2a14e0ad2f08d9c (EXACT MATCH)

ACTIVE GLOBAL CONFIG:
564501dc456ecb25ce661a439de68b2a31924844be3f19037afb130992fa0490 (EXACT MATCH)

AUTHORIZED MANIFEST:
f0ea0535164e2a06db1c357d68b7ec3624b11815e78da1c5b06bc749f5472609 (EXACT MATCH)

RUNNER:
932c567790f94b3b69a866520071c75174e35de0f59007d9a54ea603ddc5be4c (EXACT MATCH)

VALIDATOR:
7b50f7b505338097107db9c8704ecc286f65680ed8721113c8555cea9f92d4dc (EXACT MATCH)
```

---

## 8. Finalized Recovery Determination

```text
SAFE TO BEGIN OFFICIAL T2 FROM ANN_B2_001:
NO

OFFICIAL RECOVERY START:
ANN_B2_031

ANN_B2_001..030:
ADOPT AS FIRST-PASS PREFIX
```

> The validated records `ANN_B2_001..ANN_B2_030` are the first successful MODEL_G responses to those frozen benchmark items under the already-authorized execution configuration. They are preserved as the official first-pass MODEL_G T2 prefix and MUST NOT be regenerated. Official execution will resume at `ANN_B2_031`.

### Rationale:
* **Pre-existing Authorization**: Benchmark authorization (`benchmark_execution_authorized = true`) had already been formally executed and verified at commit `ef9d85d56182b22e7cd3e650d935db728b53c9bf` prior to this execution.
* **Exact Model Selector**: The exact authorized selector `gemini-3.8-flash-high` (`Gemini 3.8 Flash (High)`) was used under the required Antigravity execution environment.
* **Exact Frozen Protocol**: All 30 items were processed using the canonical frozen prompt template, guidelines, schema, and purposive challenge inputs without modification.
* **Strict Behavioral Isolation**: Each item executed in a brand-new empty temporary working directory (`/tmp/agy_empty_workdir_*`) with fresh context (`--new-project`, `--disable-slash-commands`).
* **Zero Prohibited Activity**: Audit of all 30 telemetry streams confirmed 0 tool calls, 0 web searches, 0 command executions, and 0 denied actions.
* **Hardened Validator Passing**: All 30 output records pass 100% of canonical schema and invariant checks with zero format repairs (`response_status: VALID`, `format_repairs: 0`, 30 unique conversation IDs).
* **First-Pass Methodological Integrity**: Regenerating `ANN_B2_001..030` would replace genuine blind first-pass model judgments with secondary subsequent judgments, violating the core first-pass non-retry protocol.

Therefore, rerunning `ANN_B2_001..030` is strictly **FORBIDDEN**. The 30 preserved records are established as the official first-pass T2 prefix, and official benchmark execution commences at `ANN_B2_031`.
