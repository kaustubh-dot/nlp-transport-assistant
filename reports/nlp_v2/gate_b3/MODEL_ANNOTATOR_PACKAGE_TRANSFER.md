# NLP v2 Gate B.3 — Model Annotator Sterile Package Transfer Guide

> [!WARNING]
> **FOR HUMAN OPERATOR USE ONLY — DO NOT INGEST INTO MODEL PROMPTS**
>
> **Strict Operational Isolation Rules:**
> 1. **DO NOT copy the original repository** into either sterile workspace.
> 2. **DO NOT copy Git history** (`.git/`) into either sterile workspace.
> 3. **DO NOT copy reports** other than these transfer instructions for the human user.
> 4. **DO NOT copy gold/reference data** (`human_annotation_key.json`, gold labels, etc.).
> 5. **DO NOT copy predictions** (prior model outputs, Gate B.2 predictions).
> 6. **DO NOT copy student annotations** or templates.
> 7. **DO NOT cross-copy MODEL_A and MODEL_B files** under any circumstances.
> 8. **DO NOT run benchmark annotations automatically** until sterile preflight checks pass.

---

## 1. Overview

This document provides explicit transfer instructions for populating the two isolated, sterile workspaces created by the user for Gate B.3 model annotation:

| Annotator | Model | Target Environment | Sterile Workspace Directory |
| :--- | :--- | :--- | :--- |
| **MODEL_A** | GPT-6 Astra | Codex | `Astra_testing` |
| **MODEL_B** | Claude Opus 4.6 | Antigravity / Isolated Claude backend | `gate-b3-model-b-claude` |

Each workspace must receive **only** its own sanitized protocol files, execution manifest, and blind challenge query inputs.

---

## 2. MODEL_A Transfer Instructions

**Destination Folder:**
```text
Astra_testing
```

**Target Model Identity:**
- **Source ID:** `MODEL_A`
- **Provider:** `OpenAI`
- **Model:** `GPT-6 Astra`
- **Execution Environment:** `Codex`
- **Reasoning Effort:** `medium`

### Exact File Copy Mapping:

```text
docs/nlp_v2/gate_b3/model_annotator_prompt_template.md
→ Astra_testing/protocol/model_annotator_prompt_template.md

docs/nlp_v2/gate_b3/t2_annotation_guide.md
→ Astra_testing/protocol/t2_annotation_guide.md

docs/nlp_v2/gate_b3/t3_annotation_guide.md
→ Astra_testing/protocol/t3_annotation_guide.md

docs/nlp_v2/gate_b3/annotation_output_schema.json
→ Astra_testing/protocol/annotation_output_schema.json

docs/nlp_v2/gate_b3/gate_b3_execution_isolation_amendment.md
→ Astra_testing/protocol/gate_b3_execution_isolation_amendment.md

data/nlp_v2/gate_b3/model_a_execution_manifest.json
→ Astra_testing/protocol/model_a_execution_manifest.json

data/nlp_v2/gate_b3/model_a_t2_input.jsonl
→ Astra_testing/inputs/model_a_t2_input.jsonl

data/nlp_v2/gate_b3/model_a_t3_input.jsonl
→ Astra_testing/inputs/model_a_t3_input.jsonl
```

### Preflight Checksum Verification for MODEL_A:

Verify bitwise file integrity inside `Astra_testing` using `sha256sum`:

| File | Target for `sha256sum` (Actual File Byte SHA-256) |
| :--- | :--- |
| `protocol/model_annotator_prompt_template.md` | `6d37c2646de761c0530f6fe99403e6e1f12a56880da66c8406b8b63ca828da57` |
| `protocol/t2_annotation_guide.md` | `f1b538c0c141738ada760f52ea93640c9ae91fa9c9e6d7ac13089559d9f3cfac` |
| `protocol/t3_annotation_guide.md` | `0256b4b27b02e04c6948e85d0c33e81e75c8f38b090d1ac37770bcb0ad57599d` |
| `protocol/annotation_output_schema.json` | `0fb81d7cfb9520f19e87797ad774e6f9cd8d8dbe1946cb3dab0f7b7c201954a4` |
| `protocol/gate_b3_execution_isolation_amendment.md` | `a48b732a9373a8e2d65ab3963b1920a658ada1e3c703687b8d2d072f46e87f19` |
| `protocol/model_a_execution_manifest.json` | `b46ab59e85db11712736ded8ba95cc7b8979d1fcd09282c08badc3d37f56ba8d` |
| `inputs/model_a_t2_input.jsonl` | `85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0` (350 lines) |
| `inputs/model_a_t3_input.jsonl` | `51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55` (350 lines) |

**Manifest Content Verification:**
- **Manifest file SHA-256:** `b46ab59e85db11712736ded8ba95cc7b8979d1fcd09282c08badc3d37f56ba8d` (actual SHA-256 of the execution-manifest file bytes via `sha256sum`)
- **Canonical model configuration SHA stored inside manifest:** `5db1c4aeae9e8cabb98a5b20637488c6812a826d27cbf4ed4cd578d28038fe5c` (verifies the canonical model configuration encoded inside the manifest; not the file byte hash)
- **Execution isolation class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`

---

## 3. MODEL_B Transfer Instructions

**Destination Folder:**
```text
gate-b3-model-b-claude
```

**Target Model Identity:**
- **Source ID:** `MODEL_B`
- **Provider:** `Anthropic`
- **Model:** `Claude Opus 4.6`
- **Execution Environment:** `Antigravity / isolated Claude execution backend`
- **Reasoning Configuration:** `mode: TO_BE_VERIFIED_DURING_EXECUTION_BACKEND_PREFLIGHT`

### Exact File Copy Mapping:

```text
docs/nlp_v2/gate_b3/model_annotator_prompt_template.md
→ gate-b3-model-b-claude/protocol/model_annotator_prompt_template.md

docs/nlp_v2/gate_b3/t2_annotation_guide.md
→ gate-b3-model-b-claude/protocol/t2_annotation_guide.md

docs/nlp_v2/gate_b3/t3_annotation_guide.md
→ gate-b3-model-b-claude/protocol/t3_annotation_guide.md

docs/nlp_v2/gate_b3/annotation_output_schema.json
→ gate-b3-model-b-claude/protocol/annotation_output_schema.json

docs/nlp_v2/gate_b3/gate_b3_execution_isolation_amendment.md
→ gate-b3-model-b-claude/protocol/gate_b3_execution_isolation_amendment.md

data/nlp_v2/gate_b3/model_b_execution_manifest.json
→ gate-b3-model-b-claude/protocol/model_b_execution_manifest.json

data/nlp_v2/gate_b3/model_b_t2_input.jsonl
→ gate-b3-model-b-claude/inputs/model_b_t2_input.jsonl

data/nlp_v2/gate_b3/model_b_t3_input.jsonl
→ gate-b3-model-b-claude/inputs/model_b_t3_input.jsonl
```

### Preflight Checksum Verification for MODEL_B:

Verify bitwise file integrity inside `gate-b3-model-b-claude` using `sha256sum`:

| File | Target for `sha256sum` (Actual File Byte SHA-256) |
| :--- | :--- |
| `protocol/model_annotator_prompt_template.md` | `6d37c2646de761c0530f6fe99403e6e1f12a56880da66c8406b8b63ca828da57` |
| `protocol/t2_annotation_guide.md` | `f1b538c0c141738ada760f52ea93640c9ae91fa9c9e6d7ac13089559d9f3cfac` |
| `protocol/t3_annotation_guide.md` | `0256b4b27b02e04c6948e85d0c33e81e75c8f38b090d1ac37770bcb0ad57599d` |
| `protocol/annotation_output_schema.json` | `0fb81d7cfb9520f19e87797ad774e6f9cd8d8dbe1946cb3dab0f7b7c201954a4` |
| `protocol/gate_b3_execution_isolation_amendment.md` | `a48b732a9373a8e2d65ab3963b1920a658ada1e3c703687b8d2d072f46e87f19` |
| `protocol/model_b_execution_manifest.json` | `152df7d510aa18e0a713af8451a7f6ff92febed016559c43b6e5afe1b85a17d0` |
| `inputs/model_b_t2_input.jsonl` | `85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0` (350 lines) |
| `inputs/model_b_t3_input.jsonl` | `51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55` (350 lines) |

**Manifest Content Verification:**
- **Manifest file SHA-256:** `152df7d510aa18e0a713af8451a7f6ff92febed016559c43b6e5afe1b85a17d0` (actual SHA-256 of the execution-manifest file bytes via `sha256sum`)
- **Canonical model configuration SHA stored inside manifest:** `3d9264b1172878ed07080d1ca4e087170aa83fd366f8695effbf32297318020c` (verifies the canonical model configuration encoded inside the manifest; not the file byte hash)
- **Execution isolation class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`

---

## 4. Next Step: Amended Sterile Smoke-Test Verification

In each sterile workspace:

1. Verify one-query-one-fresh-context execution (`ONE_QUERY_ONE_FRESH_CONTEXT_REQUIRED`).

2. Verify every semantic child runs from a fresh empty temporary working directory with no benchmark/repository paths supplied.

3. Run exactly one synthetic non-benchmark smoke test under the prospectively amended `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` protocol.

4. Preserve raw execution telemetry and verify:
   - tool calls observed = 0
   - web calls observed = 0
   - external file reads observed = 0
   - command executions observed = 0

5. For MODEL_A, web search must additionally be configured disabled where supported by Codex.

6. Do NOT claim that filesystem or other tool capabilities are architecturally unavailable merely because no tool call occurred.

7. Execution readiness may be considered for authorization only after the amended synthetic smoke test passes and fresh-context, empty-workdir, and zero-tool-use auditing have all been verified.

8. Benchmark execution remains unauthorized until the original repository readiness state is explicitly updated after external review.
