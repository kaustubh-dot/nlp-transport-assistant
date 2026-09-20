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

data/nlp_v2/gate_b3/model_a_execution_manifest.json
→ Astra_testing/protocol/model_a_execution_manifest.json

data/nlp_v2/gate_b3/model_a_t2_input.jsonl
→ Astra_testing/inputs/model_a_t2_input.jsonl

data/nlp_v2/gate_b3/model_a_t3_input.jsonl
→ Astra_testing/inputs/model_a_t3_input.jsonl
```

### Preflight Checksum Verification for MODEL_A:

Verify bitwise integrity inside `Astra_testing` using `sha256sum`:

| File | Expected SHA-256 Checksum |
| :--- | :--- |
| `protocol/model_annotator_prompt_template.md` | `6d37c2646de761c0530f6fe99403e6e1f12a56880da66c8406b8b63ca828da57` |
| `protocol/t2_annotation_guide.md` | `f1b538c0c141738ada760f52ea93640c9ae91fa9c9e6d7ac13089559d9f3cfac` |
| `protocol/t3_annotation_guide.md` | `0256b4b27b02e04c6948e85d0c33e81e75c8f38b090d1ac37770bcb0ad57599d` |
| `protocol/annotation_output_schema.json` | `0fb81d7cfb9520f19e87797ad774e6f9cd8d8dbe1946cb3dab0f7b7c201954a4` |
| `protocol/model_a_execution_manifest.json` | Stored canonical hash: `7861de9a0071fab99885411cc3ad3bd0378e98924c01980f2c1957a24e68091e` |
| `inputs/model_a_t2_input.jsonl` | `85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0` (350 lines) |
| `inputs/model_a_t3_input.jsonl` | `51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55` (350 lines) |

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

data/nlp_v2/gate_b3/model_b_execution_manifest.json
→ gate-b3-model-b-claude/protocol/model_b_execution_manifest.json

data/nlp_v2/gate_b3/model_b_t2_input.jsonl
→ gate-b3-model-b-claude/inputs/model_b_t2_input.jsonl

data/nlp_v2/gate_b3/model_b_t3_input.jsonl
→ gate-b3-model-b-claude/inputs/model_b_t3_input.jsonl
```

### Preflight Checksum Verification for MODEL_B:

Verify bitwise integrity inside `gate-b3-model-b-claude` using `sha256sum`:

| File | Expected SHA-256 Checksum |
| :--- | :--- |
| `protocol/model_annotator_prompt_template.md` | `6d37c2646de761c0530f6fe99403e6e1f12a56880da66c8406b8b63ca828da57` |
| `protocol/t2_annotation_guide.md` | `f1b538c0c141738ada760f52ea93640c9ae91fa9c9e6d7ac13089559d9f3cfac` |
| `protocol/t3_annotation_guide.md` | `0256b4b27b02e04c6948e85d0c33e81e75c8f38b090d1ac37770bcb0ad57599d` |
| `protocol/annotation_output_schema.json` | `0fb81d7cfb9520f19e87797ad774e6f9cd8d8dbe1946cb3dab0f7b7c201954a4` |
| `protocol/model_b_execution_manifest.json` | Stored canonical hash: `8f90c8207b7309e72ce5c33a787d102a70ca5f421e36db90625384e419d525a5` |
| `inputs/model_b_t2_input.jsonl` | `85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0` (350 lines) |
| `inputs/model_b_t3_input.jsonl` | `51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55` (350 lines) |

---

## 4. Next Step: Sterile Preflight Verification

In each sterile workspace:
1. Verify per-item request isolation (`ONE_QUERY_ONE_FRESH_CONTEXT_REQUIRED`).
2. Run synthetic smoke test on non-benchmark sample query.
3. Ensure tools (web, retrieval, code execution) remain completely disabled.
4. Only when sterile bootstrap verification reports `PASS` may execution readiness be authorized.
