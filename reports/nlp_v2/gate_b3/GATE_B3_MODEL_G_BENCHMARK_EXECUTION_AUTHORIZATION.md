# Gate B.3 MODEL_G Benchmark Execution Authorization

## 1. Executive Authorization Summary

This document records formal benchmark-execution authorization for **MODEL_G** (`Gemini 3.8 Flash (High)` via Antigravity selector `gemini-3.8-flash-high`) as the active primary model annotator for the NLP v2 Gate B.3 study under the `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION` protocol.

> [!IMPORTANT]
> **Supersession Notice:**
> The historical dual-model authorization recorded in `reports/nlp_v2/gate_b3/GATE_B3_BENCHMARK_EXECUTION_AUTHORIZATION.md` (authorizing MODEL_A and MODEL_B) has been formally superseded for primary Gate B.3 execution by the *Gate B.3 Resource-Feasibility / Annotator-Design Amendment* (`docs/nlp_v2/gate_b3/gate_b3_resource_feasibility_annotator_amendment.md`).
> MODEL_A (aborted pre-amendment after 23 items) and MODEL_B (retired pre-completion) are revoked and preserved strictly for forensic provenance. **MODEL_G is the sole authorized primary model annotator.**

---

## 2. Authorized Model Identity & Verification Status

```text
source:
MODEL_G

provider:
Google

model:
Gemini 3.8 Flash

visible identity:
Gemini 3.8 Flash (High)

execution selector:
gemini-3.8-flash-high

execution environment:
Antigravity

isolation:
EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION

web isolation:
ZERO_CALL_AUDITED

architectural tool disablement claimed:
NO

execution ready:
YES

synthetic smoke:
PASS

hardened runner tests:
31/31 PASS

benchmark authorization:
YES

real benchmark invocations at authorization:
0

real benchmark outputs at authorization:
NONE
```

---

## 3. Cryptographic Scope & Invariant Hashes

This authorization applies strictly to the exact bitwise artifacts listed below. Any modification to these digests immediately voids this authorization:

```text
MODEL_G CONFIG:
128e0736aa4a259d48b0c078d242212b71932a73f0af726fa2a14e0ad2f08d9c

ACTIVE GLOBAL CONFIG:
564501dc456ecb25ce661a439de68b2a31924844be3f19037afb130992fa0490

RUNNER:
932c567790f94b3b69a866520071c75174e35de0f59007d9a54ea603ddc5be4c

VALIDATOR:
7b50f7b505338097107db9c8704ecc286f65680ed8721113c8555cea9f92d4dc

T2 INPUT:
85b5c3bf3cccd3cdf1ebab289e6ac6c513387006ce9f04ac2c0c2e33c123dab0

T3 INPUT:
51a90d81ac2be0370b287c95bcab6e8861a5565e68082958f2229918521e5d55

PRE-AUTHORIZATION MANIFEST:
54420aef23e895afb38528411d05c204338d43f81b6c9009a672a82dffd06707

AUTHORIZED MANIFEST:
f0ea0535164e2a06db1c357d68b7ec3624b11815e78da1c5b06bc749f5472609
```

> [!NOTE]
> Authorization permits future execution only after this authorization commit is externally verified and the exact authorized manifest plus canonical runner/validator are transferred into the sterile MODEL_G workspace and hash-verified.

---

## 4. Frozen Execution Scope & Prohibitions

This authorization is **strictly bounded**:
- **Permitted Scope:**
  - `MODEL_G` (`gemini-3.8-flash-high`)
  - Frozen T2 benchmark input (`model_g_t2_input.jsonl`, 350 items)
  - Frozen T3 benchmark input (`model_g_t3_input.jsonl`, 350 items)
  - Canonical hardened runner (`scripts/nlp_v2/gate_b3/model_g/run_model_g_gemini.py`)
  - Canonical output validator (`scripts/nlp_v2/gate_b3/model_g/validate_model_g_outputs.py`)

- **Explicitly Forbidden Actions:**
  - DO NOT run on any regenerated, sampled, or modified inputs.
  - DO NOT alter prompts, guidelines, or schema.
  - DO NOT change model selector, reasoning effort, or runtime flags.
  - DO NOT run or reactivate MODEL_A or MODEL_B.
  - DO NOT access gold/reference keys or enable reference join.
  - DO NOT compute concordance, inter-annotator agreement, or Cohen's kappa.
  - DO NOT initiate gold-boundary auditing or lock first-pass annotations prematurely.

Any hash, model, or protocol drift voids authorization and must fail closed.

---

## 5. Frozen Execution Order & Operational Discipline

To guarantee complete operational reproducibility, execution must proceed in the following fixed sequence:

```text
1. T2 — ANN_B2_001 through frozen input order
2. validate complete T2
3. T3 — ANN_B2_001 through frozen input order
4. validate complete T3
5. cross-taxonomy telemetry/conversation-ID uniqueness validation
```

### Resume & Interruption Protocol:
- Resume is permitted **only** through the hardened deterministic-prefix mechanism.
- If provider quota or rate limits interrupt execution:
  ```text
  pause
  preserve accepted records + telemetry
  resume later from validated exact prefix
  ```
- **Strict Prohibition:** Zero semantic retries (`semantic_retries = 0`). Zero resampling. Format repairs permitted up to 1 attempt strictly for schema conformance.

---

## 6. Execution Non-Commencement Confirmation

At the time of this authorization commit:
- `annotation_started` = **false**
- `real benchmark invocations` = **0**
- `real benchmark outputs` = **NONE**
- `first_pass_locked` = **false**
- `reference_join_enabled` = **false**
- `gold_boundary_audit_started` = **false**
- `taxonomy_decision_status` = **PENDING**
