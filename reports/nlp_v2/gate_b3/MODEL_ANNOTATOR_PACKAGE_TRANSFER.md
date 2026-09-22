# NLP v2 Gate B.3 — Model Annotator Sterile Package Transfer Guide

> [!WARNING]
> **FOR HUMAN OPERATOR USE ONLY — DO NOT INGEST INTO MODEL PROMPTS**
>
> **Strict Operational Isolation Rules:**
> 1. **DO NOT copy the original repository** into any sterile workspace.
> 2. **DO NOT copy Git history** (`.git/`) into any sterile workspace.
> 3. **DO NOT copy reports** other than these transfer instructions for the human user.
> 4. **DO NOT copy gold/reference data** (`human_annotation_key.json`, gold labels, etc.).
> 5. **DO NOT copy predictions** (prior model outputs, Gate B.2 predictions).
> 6. **DO NOT copy student annotations** or templates.
> 7. **DO NOT cross-copy model files** or partial pre-amendment outputs into active workspaces.
> 8. **DO NOT run benchmark annotations automatically** until sterile preflight checks pass.

---

## 1. Overview

Under the *Gate B.3 Resource-Feasibility / Annotator-Design Amendment*, **MODEL_G (Gemini 3.8 Flash)** is the active primary model annotator. Historical models `MODEL_A` (GPT-6 Astra) and `MODEL_B` (Claude Opus 4.6) are retired from bulk annotation.

| Annotator | Model | Target Environment | Sterile Workspace Directory | Status |
| :--- | :--- | :--- | :--- | :--- |
| **MODEL_G** | Gemini 3.8 Flash | Antigravity | `gate-b3-model-g-gemini` | **ACTIVE PRIMARY** |
| **MODEL_A** | GPT-6 Astra | Codex | `Astra_testing` | RETIRED / PROVENANCE (23 T2 items) |
| **MODEL_B** | Claude Opus 4.6 | Antigravity / Isolated Claude backend | `gate-b3-model-b-claude` | RETIRED / PROVENANCE (0 items) |

Each workspace must receive **only** its own sanitized protocol files, execution manifest, and blind challenge query inputs.

---

## 2. ACTIVE PRIMARY: MODEL_G Transfer Instructions

**Destination Folder:**
```text
gate-b3-model-g-gemini
```

**Target Model Identity:**
- **Source ID:** `MODEL_G`
- **Provider:** `Google`
- **Model:** `Gemini 3.8 Flash`
- **Version:** `Gemini 3.8 Flash (High)`
- **Execution Model Selector:** `gemini-3.8-flash-high`
- **Exact Revision:** `NOT_EXPOSED_BY_PROVIDER`
- **Execution Environment:** `Antigravity`
- **Reasoning Configuration:** `mode = high, selection_mechanism = gemini-3.8-flash-high selector, effort_control_exposed = true`
- **Execution Isolation Class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **Web Isolation:** `ZERO_CALL_AUDITED`

### Exact File Copy Mapping for MODEL_G:

```text
docs/nlp_v2/gate_b3/model_annotator_prompt_template.md
→ gate-b3-model-g-gemini/protocol/model_annotator_prompt_template.md

docs/nlp_v2/gate_b3/t2_annotation_guide.md
→ gate-b3-model-g-gemini/protocol/t2_annotation_guide.md

docs/nlp_v2/gate_b3/t3_annotation_guide.md
→ gate-b3-model-g-gemini/protocol/t3_annotation_guide.md

docs/nlp_v2/gate_b3/annotation_output_schema.json
→ gate-b3-model-g-gemini/protocol/annotation_output_schema.json

docs/nlp_v2/gate_b3/gate_b3_execution_isolation_amendment.md
→ gate-b3-model-g-gemini/protocol/gate_b3_execution_isolation_amendment.md

docs/nlp_v2/gate_b3/gate_b3_resource_feasibility_annotator_amendment.md
→ gate-b3-model-g-gemini/protocol/gate_b3_resource_feasibility_annotator_amendment.md

data/nlp_v2/gate_b3/model_g_execution_manifest.json
→ gate-b3-model-g-gemini/protocol/model_g_execution_manifest.json

data/nlp_v2/gate_b3/model_g_t2_input.jsonl
→ gate-b3-model-g-gemini/inputs/model_g_t2_input.jsonl

data/nlp_v2/gate_b3/model_g_t3_input.jsonl
→ gate-b3-model-g-gemini/inputs/model_g_t3_input.jsonl
```

### Preflight Checksum Verification for MODEL_G:

Verify bitwise file integrity inside `gate-b3-model-g-gemini` using `sha256sum`:

| File | Target for `sha256sum` (Actual File Byte SHA-256) |
| :--- | :--- |
| `protocol/model_annotator_prompt_template.md` | `6d37c2646de761c0530f6fe99403e6e1f12a56880da66c8406b8b63ca828da57` |
| `protocol/t2_annotation_guide.md` | `f1b538c0c141738ada760f52ea93640c9ae91fa9c9e6d7ac13089559d9f3cfac` |
| `protocol/t3_annotation_guide.md` | `0256b4b27b02e04c6948e85d0c33e81e75c8f38b090d1ac37770bcb0ad57599d` |
| `protocol/annotation_output_schema.json` | `0fb81d7cfb9520f19e87797ad774e6f9cd8d8dbe1946cb3dab0f7b7c201954a4` |
| `protocol/gate_b3_execution_isolation_amendment.md` | `a48b732a9373a8e2d65ab3963b1920a658ada1e3c703687b8d2d072f46e87f19` |
| `protocol/gate_b3_resource_feasibility_annotator_amendment.md` | `7eaab180555f94956a4d9737bf98d2fba8477b847c9fd79136ab0e6329b39b40` |
| `protocol/model_g_execution_manifest.json` | `54420aef23e895afb38528411d05c204338d43f81b6c9009a672a82dffd06707` |
| `inputs/model_g_t2_input.jsonl` | `85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0` (350 lines) |
| `inputs/model_g_t3_input.jsonl` | `51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55` (350 lines) |

**Manifest Content Verification:**
- **Manifest file SHA-256:** `54420aef23e895afb38528411d05c204338d43f81b6c9009a672a82dffd06707` (actual SHA-256 of execution-manifest file bytes via `sha256sum`)
- **Canonical model configuration SHA stored inside manifest:** `128e0736aa4a259d48b0c078d242212b71932a73f0af726fa2a14e0ad2f08d9c` (verifies canonical model configuration encoded inside manifest; not file byte hash)
- **Active global configuration SHA:** `564501dc456ecb25ce661a439de68b2a31924844be3f19037afb130992fa0490`
- **Historical preflight MODEL_G config SHA:** `d4a359b72779ec15f42ffa0ba72beb57ff20ff765de901783082caee0deda1dd`
- **Historical pre-readiness global config SHA:** `b2aac9ceec68c906387a1e8521bf8538e5fd23f36b1c4e65a2f75f3a74e638df`
- **Canonical runner SHA-256:** `932c567790f94b3b69a866520071c75174e35de0f59007d9a54ea603ddc5be4c`
- **Canonical validator SHA-256:** `7b50f7b505338097107db9c8704ecc286f65680ed8721113c8555cea9f92d4dc`
- **Execution isolation class:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **Initial authorization status:** `benchmark_execution_authorized = false`
- **Post-Readiness Transfer Note:** The next transfer to the sterile workspace will involve the updated sanitized manifest only after this commit is externally verified.

---

## 3. HISTORICAL PROVENANCE: MODEL_A Transfer Archive

> [!NOTE]
> `MODEL_A` is retired from primary bulk annotation. The details below are retained strictly for forensic reference.

**Destination Folder:** `Astra_testing`  
**Target Model Identity:** `MODEL_A` (GPT-6 Astra, Codex)  
**Historical Authorized Manifest File SHA-256:** `17f30bb2178ceb6eda72c5b713c4c1938d5bf0147642fa931d6491a3a7bdd057`  
**Current Retired / Revoked Manifest File SHA-256:** `e838082ee386d4ac4c2840ea2f7daf3dfda5c71f54ff21ac68b5a16c4c520db7` (operator must copy to `Astra_testing` for fail-closed state)  
**Canonical model configuration SHA stored inside manifest:** `5db1c4aeae9e8cabb98a5b20637488c6812a826d27cbf4ed4cd578d28038fe5c`  
**Inputs:** `model_a_t2_input.jsonl` (`85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0`), `model_a_t3_input.jsonl` (`51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55`)  
**Execution Status:** Aborted after 23 items due to provider rate/quota limits. Excluded from primary Gate B.3 analysis. Authorization revoked (`benchmark_execution_authorized = false`).

---

## 4. HISTORICAL PROVENANCE: MODEL_B Transfer Archive

> [!NOTE]
> `MODEL_B` is retired from primary bulk annotation. The details below are retained strictly for forensic reference.

**Destination Folder:** `gate-b3-model-b-claude`  
**Target Model Identity:** `MODEL_B` (Claude Opus 4.6, Antigravity)  
**Historical Authorized Manifest File SHA-256:** `607df806d33fb77194d64b741ed424697f05d0d64c9188512eebd8104930627a`  
**Current Retired / Revoked Manifest File SHA-256:** `1837a6854cb3c1d60c2b4fd910ba160c8807505e49b1fb5b9e0e517d4d835573` (operator must copy to `gate-b3-model-b-claude` for fail-closed state)  
**Canonical model configuration SHA stored inside manifest:** `3d9264b1172878ed07080d1ca4e087170aa83fd366f8695effbf32297318020c`  
**Inputs:** `model_b_t2_input.jsonl` (`85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0`), `model_b_t3_input.jsonl` (`51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55`)  
**Execution Status:** Retired pre-completion due to provider quota feasibility. Zero benchmark runs executed. Excluded from primary Gate B.3 analysis. Authorization revoked (`benchmark_execution_authorized = false`).

---

## 5. Next Step: Explicit MODEL_G Benchmark Authorization

MODEL_G sterile preflight, synthetic smoke testing, and zero-tool-use auditing are complete and externally reviewed under `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`:
- tool calls observed = 0
- web calls observed = 0
- external file reads observed = 0
- command executions observed = 0

Current state:
- execution ready: YES
- benchmark authorized: NO
- real benchmark invocations: 0

Before benchmark execution:
1. create and externally verify a separate canonical authorization commit;
2. copy ONLY the newly authorized MODEL_G execution manifest into the sterile MODEL_G workspace;
3. verify the authorized manifest file SHA;
4. run annotation-start QA;
5. only then execute the frozen benchmark through the canonical hardened runner.
