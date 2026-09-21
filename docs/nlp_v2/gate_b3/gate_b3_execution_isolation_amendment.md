# Gate B.3 Execution-Isolation Prospective Methodology Amendment

**Study:** Gate B.3 Annotation-Stability and Semantic-Boundary Audit  
**Amendment Type:** Prospective Protocol & Tool-Isolation Amendment  
**Date:** 2026-09-20  
**Status:** PROSPECTIVE AMENDMENT ADOPTED BEFORE BENCHMARK ANNOTATION  
**Benchmark Invocations Prior to Amendment:** 0 (Zero benchmark queries annotated)  

---

## 1. Context & Reason for Amendment

The prospective methodology amendment for Gate B.3 originally designed an annotation protocol under the assumption of **hard operational isolation**:
1. Zero repository or host file-reading capability;
2. Zero web search or URL retrieval capability;
3. Exactly one query per fresh stateless process context without cross-query memory or tool availability.

Prior to executing any benchmark annotation, empirical synthetic pre-execution probes were conducted on the selected non-API execution surfaces. These probes yielded the following empirical evidence:

### MODEL_A — GPT-6 Astra / Codex
- **Requested Model:** `gpt-6-astra` (selection accepted: YES)
- **Reasoning Effort:** `medium` (accepted: YES)
- **Context Isolation:** Ephemeral execution, ignore user config, ignore rules, fresh empty temporary working directory, web search disabled (observed web calls: 0).
- **Sandbox Status:** Read-only host sandbox.
- **Empirical Host File Access:** During capability discovery, an authorized synthetic canary located outside the empty temporary working directory was successfully read by the execution environment when requested.
- **Benchmark Exposure:** 0. No benchmark queries, benchmark paths, or reference labels were provided.

### MODEL_B — Claude Opus 4.6 / Antigravity
- **Requested Model:** `Claude Opus 4.6`
- **Context Isolation:** One fresh process/context per item (`--new-project` / fresh session), fresh empty temporary working directory, prior annotation history excluded, project context excluded.
- **Rules & Tools:** Antigravity global generic rules are inherited by default (audited to verify zero project-specific, Chennai, or Gate B.3 taxonomy content). Web and filesystem inspection tools technically remain available on the platform surface, though zero tool calls were made during synthetic classification.
- **Reasoning State:** Model surface operates as `Claude Opus 4.6 (Thinking)`. A controllable fixed thinking effort parameter is `NOT_EXPOSED_BY_EXECUTION_SURFACE`.

### Conclusion
Neither Codex nor Antigravity provides hard architectural tool or filesystem exclusion on the available non-API execution surfaces. Claiming "hard tool isolation" or "zero tool availability" would be methodologically false.

---

## 2. Methodological Decision: Empty-Workdir Behavioral Tool Restriction

Because real benchmark annotation has not commenced (benchmark model invocations = 0, first-pass lock = NO, reference join = DISABLED, taxonomy decision = PENDING, Gate C = NO), this amendment formally and prospectively establishes the execution isolation class:

```text
EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION
```

We explicitly make **NO claim** of:
- Hard architectural tool isolation;
- Architectural filesystem exclusion;
- Architectural no-web capability;
- Zero tool availability on the harness.

Instead, isolation is enforced via:
1. **Procedural Containerization:** Every single item executes in a fresh, independent process/context with an empty temporary working directory.
2. **Contextual Quarantine:** No project paths, repository paths, input JSONL paths, prior model responses, other annotator outputs, or gold/reference data are ever provided to the child execution context.
3. **Strict Behavioral Prohibition:** Actual tool use during benchmark semantic annotation is strictly forbidden.
4. **Zero-Tool-Use Audit:** Raw execution telemetry must be preserved for every query to empirically verify zero tool calls.

---

## 3. Revised Execution Design

For both MODEL_A and MODEL_B, per-item execution must adhere to:
- **One Query per Fresh Context:** Each benchmark query is executed in a dedicated, newly spawned process/context.
- **Empty Temporary Working Directory:** Execution cwd is an empty temporary folder (`tmpdir`) containing zero repository files.
- **Zero Ingestion of External Paths:** The child context is never supplied with source file paths, git paths, or workspace directories.
- **Self-Contained Prompt Structure:** The semantic child receives strictly:
  1. Frozen annotation instructions;
  2. The relevant neutral taxonomy guide (T2 or T3);
  3. The canonical JSON output schema;
  4. Exactly one `annotation_id` and one `query`.
- **Zero Cross-Query History:** No previous response or conversation turn is carried forward.
- **Zero Multi-Annotator Visibility:** MODEL_A never sees MODEL_B; MODEL_B never sees MODEL_A; neither model ever sees student annotations or gold labels.

---

## 4. Tool-Use Policy

While platform harnesses may technically possess tools (e.g. bash, file reading, web search), actual tool use during benchmark semantic annotation is **STRICTLY FORBIDDEN**.

Prohibited semantic-child actions include:
- Filesystem reads or searches (`cat`, `ls`, `grep`, `find`, file-reading tools);
- Shell command execution;
- Web search or URL retrieval;
- External database or API queries;
- MCP tool or plugin invocations;
- Inspection of the parent repository or sibling workspaces.

The model must generate its classification schema strictly through in-context reasoning over the prompt text.

---

## 5. Zero-Tool-Use Audit Requirement

Every per-item invocation must capture and persist sufficient raw execution telemetry (event streams, tool invocation logs, process stdout/stderr) to verify that no tool action was executed.

For every benchmark query record, the audit requires:
```text
tool_calls_observed = 0
web_calls_observed = 0
external_file_reads_observed = 0
command_exec_observed = 0
```

If execution telemetry is missing, truncated, or unable to definitively confirm whether a tool was invoked, the execution backend is **NOT READY** and the batch is invalidated. Zero tool use cannot be inferred solely from the final textual response.

---

## 6. Tool-Violation Policy

If execution telemetry reveals that a semantic child executed any prohibited tool action:
1. The annotation for that item is immediately declared **INVALID**;
2. Its semantic label is discarded and must never enter the dataset;
3. No retry is permitted based on the generated label;
4. **Tool-Violation Policy:** `tool_violation_retry_attempts = 0`, `tool_violation_mode = HARD_FAIL_BATCH`;
5. The entire execution batch must be halted for root-cause operational review.

Tool violations represent execution-protocol failures, not semantic disagreements.

---

## 7. Amended Retry Policy

The frozen retry policy for both models is formally amended as:

```json
{
  "semantic_retries": 0,
  "format_repair_attempts": 1,
  "transport_retry_policy": "PERMITTED_FOR_EXECUTION_FAILURE_ONLY",
  "semantic_retry_mode": "FORBIDDEN",
  "tool_violation_retry_attempts": 0,
  "tool_violation_mode": "HARD_FAIL_BATCH"
}
```

- **Semantic Disagreement:** 0 retries (strictly forbidden).
- **Malformed Structured Output:** Exactly 1 fixed format-repair attempt (re-prompting with syntax validation errors only).
- **Transport / Timeout Failure:** Retries permitted for execution/connectivity failure only.
- **Tool Violation:** 0 retries; hard batch stop.

---

## 8. Model Profiles & Surface Controls

### MODEL_A: OpenAI GPT-6 Astra / Codex
- **Model Identity:** `GPT-6 Astra` (user-attested surface identity)
- **Revision:** `NOT_EXPOSED_BY_PROVIDER`
- **Execution Environment:** `Codex`
- **Reasoning Configuration:** `{"effort": "medium"}`
- **Filesystem Isolation:** `BEHAVIORAL_NO_USE_WITH_EMPTY_WORKDIR`
- **Web Isolation:** `CONFIG_DISABLED_AND_ZERO_CALL_AUDITED`
- **Execution Controls:** Ephemeral mode, ignore user config, ignore rules, fresh empty temp directory, web disabled, read-only sandbox, structured output enforcement, raw event log preservation.

### MODEL_B: Anthropic Claude Opus 4.6 / Antigravity
- **Model Identity:** `Claude Opus 4.6` (user-attested surface identity)
- **Revision:** `NOT_EXPOSED_BY_PROVIDER`
- **Execution Environment:** `Antigravity / isolated Claude execution backend`
- **Model Surface:** `Claude Opus 4.6 (Thinking)`
- **Thinking Effort Control:** `NOT_EXPOSED_BY_EXECUTION_SURFACE`
- **Filesystem Isolation:** `BEHAVIORAL_NO_USE_WITH_EMPTY_WORKDIR`
- **Web Isolation:** `ZERO_CALL_AUDITED`
- **Execution Controls:** Fresh process per item, `--new-project` fresh context, empty temp directory, slash/skill expansion disabled where supported, no source file paths supplied, raw JSON wrapper retained, zero tool-call audit.

---

## 9. Synthetic Smoke Test Acceptance Criteria

Before benchmark execution authorization, both sterile workspaces (`Astra_testing` and `gate-b3-model-b-claude`) must independently execute a fresh synthetic smoke test on a non-benchmark query meeting the following criteria:
1. Model identity and configuration match frozen parameters;
2. Fresh ephemeral process and empty working directory verified;
3. Zero project or benchmark paths supplied;
4. Valid JSON structured output produced conforming to `annotation_output_schema.json`;
5. Raw execution telemetry captured and verified;
6. Machine-audited tool calls = 0, web calls = 0, external file reads = 0, commands = 0.

*(Note: The earlier exploratory canary probe in Codex was for capability discovery and does NOT constitute the formal smoke test under this amended protocol.)*

---

## 10. Methodology Language Standards

In all future Gate B.3 reporting, the following terminology is strictly mandated:

**Permitted Terminology:**
- *procedurally isolated model annotation*
- *fresh-context execution*
- *empty-workdir behavioral tool restriction*
- *zero-tool-use audited annotation*
- *cross-model annotation stability*

**Forbidden Terminology:**
- *architecturally tool-free annotation*
- *filesystem-inaccessible model*
- *fully sandboxed annotator*
- *statistically independent model annotators*
- *human inter-annotator agreement (IAA)*
