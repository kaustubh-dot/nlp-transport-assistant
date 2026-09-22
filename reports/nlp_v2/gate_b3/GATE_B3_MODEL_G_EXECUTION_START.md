# Gate B.3 MODEL_G Benchmark Execution Start Record

## 1. Campaign Start Summary

This document formally records the execution commencement provenance for the **MODEL_G** (`Gemini 3.8 Flash (High)` via Antigravity selector `gemini-3.8-flash-high`) primary benchmark annotation campaign under the `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` protocol.

```text
MODEL_G execution campaign:
STARTED

execution start timestamp (UTC):
2026-09-22T17:27:56Z

authorization commit:
ef9d85d56182b22e7cd3e650d935db728b53c9bf

authorized manifest:
f0ea0535164e2a06db1c357d68b7ec3624b11815e78da1c5b06bc749f5472609

execution order:
T2 complete → validate → T3 complete → validate

benchmark invocations before this start record:
0

MODEL_G configuration:
unchanged

reference join:
disabled

first-pass lock:
false

taxonomy decision:
PENDING
```

---

## 2. Cryptographic Scope Baseline

The authorized execution campaign is governed strictly by the following verified digests:

```text
MODEL_G CONFIG:
128e0736aa4a259d48b0c078d242212b71932a73f0af726fa2a14e0ad2f08d9c

ACTIVE GLOBAL CONFIG:
564501dc456ecb25ce661a439de68b2a31924844be3f19037afb130992fa0490

AUTHORIZED MANIFEST:
f0ea0535164e2a06db1c357d68b7ec3624b11815e78da1c5b06bc749f5472609

RUNNER:
932c567790f94b3b69a866520071c75174e35de0f59007d9a54ea603ddc5be4c

VALIDATOR:
7b50f7b505338097107db9c8704ecc286f65680ed8721113c8555cea9f92d4dc

T2 INPUT:
85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0

T3 INPUT:
51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55
```

---

## 3. Strict Execution Non-Commencement Confirmation

At the creation of this start record:
- Primary annotation status: **STARTED** (`annotation_started = true` recorded in `gate_b3_annotation_manifest.json`)
- Model execution timestamp: **2026-09-22T17:27:56Z** (recorded in `model_annotator_configs.json`)
- Real benchmark model invocations executed: **0**
- Real benchmark output records created: **NONE**
- Gemini execution from canonical repository: **PROHIBITED** (execution authorized exclusively within sterile workspace `/home/kaustubh/gate-b3-model-g-gemini`)
- Gold reference join: **DISABLED** (`reference_join_enabled = false`)
- First-pass lock: **FALSE** (`first_pass_locked = false`)
- Taxonomy decision: **PENDING**
