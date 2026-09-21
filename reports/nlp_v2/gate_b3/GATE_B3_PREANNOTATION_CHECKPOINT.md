# GATE B.3 ANNOTATION-STABILITY FRAMEWORK

## PRE-ANNOTATION CHECKPOINT REPORT

**BASE COMMIT:**  
`4d8320e7f46574c2d9bd419ce1b48ecfb32c84d8`

**ACTIVE KB:**  
`chennai_multimodal_v1.2.2`

**METHODOLOGY:**  
single-student blind audit  
+  
two isolated model annotators  
+  
post-lock gold-boundary audit  

**HUMAN IAA CLAIMED:**  
NO  

**SOURCE 350 SAMPLE:**  
rows: 350  
SHA: `94fd8bb3e7f2e3bdaf274c4ee5bcf7e083e9ef2a66322fbcf7bee2cadf231999`  
unchanged: YES  

**SAMPLE TYPE:**  
purposive enriched challenge sample  

**STUDENT PACKAGE:**  
generated: YES  

**MODEL_A:**  
- **Model:** `GPT-6 Astra` (OpenAI / Codex)
- **CONFIGURATION:** FROZEN
- **ISOLATION CLASS:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **STERILE BOOTSTRAP:** PASS
- **PER-ITEM ISOLATION:** NOT VERIFIED
- **AMENDED SMOKE TEST:** NOT RUN
- **BENCHMARK EXECUTION AUTHORIZED:** NO
- **ANNOTATION EXECUTED:** NO

**MODEL_B:**  
- **Model:** `Claude Opus 4.6` (Anthropic / Antigravity isolated backend)
- **CONFIGURATION:** FROZEN
- **ISOLATION CLASS:** `EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION`
- **STERILE BOOTSTRAP:** PASS
- **PER-ITEM ISOLATION:** NOT VERIFIED
- **AMENDED SMOKE TEST:** NOT RUN
- **BENCHMARK EXECUTION AUTHORIZED:** NO
- **ANNOTATION EXECUTED:** NO

**GOVERNANCE PRINCIPLE:**  
> Configuration frozen does not mean execution authorized.
>
> Hard architectural tool exclusion was empirically unavailable on the selected non-API execution surfaces.
> The prospective amendment was adopted before any real benchmark annotation invocation.

**ANNOTATION-START QA:**  
BLOCKED / NOT READY (Expected: per-item behavioral isolation, smoke tests, and execution authorization remain unverified)

**ANNOTATION:**  
NOT STARTED  

**FIRST-PASS LOCK:**  
NO  

**REFERENCE JOIN:**  
DISABLED  

**GOLD BOUNDARY AUDIT:**  
NOT STARTED  

**BOOTSTRAP INTERPRETATION:**  
query bootstrap conditional on fixed seeds  

**MODEL RESULTS:**  
unchanged  

**TAXONOMY DECISION:**  
PENDING  

**GATE C:**  
NO  

**STATUS:**  
READY FOR AMENDED SYNTHETIC SMOKE TESTS  


---

## Technical Summary of Framework Artifacts

### 1. Documentation & Guidelines
- Prospective methodology amendment: `docs/nlp_v2/gate_b3/gate_b3_annotation_methodology_amendment.md`
- Prospective execution-isolation amendment: `docs/nlp_v2/gate_b3/gate_b3_execution_isolation_amendment.md`
- Neutral T2 annotation guide (12 classes): `docs/nlp_v2/gate_b3/t2_annotation_guide.md`
- Neutral T3 annotation guide (16 classes): `docs/nlp_v2/gate_b3/t3_annotation_guide.md`
- Isolated model prompt template & protocol: `docs/nlp_v2/gate_b3/model_annotator_prompt_template.md`
- Bootstrap interpretation clarification note: `reports/nlp_v2/gate_b3/gate_b2_bootstrap_interpretation_note.md`
- Model annotator sterile package transfer guide: `reports/nlp_v2/gate_b3/MODEL_ANNOTATOR_PACKAGE_TRANSFER.md`

### 2. Blind Annotation Packages & Sanitized Manifests
- Student order manifest: `data/nlp_v2/gate_b3/student_order_manifest.json` (deterministic 175/175 split, counterbalanced order)
- Student blind CSVs:
  - `data/nlp_v2/gate_b3/student_t2_first_pass.csv` (175 queries)
  - `data/nlp_v2/gate_b3/student_t3_first_pass.csv` (175 queries)
  - `data/nlp_v2/gate_b3/student_t2_second_pass.csv` (175 queries)
  - `data/nlp_v2/gate_b3/student_t3_second_pass.csv` (175 queries)
- Model annotator blind JSONLs:
  - `data/nlp_v2/gate_b3/model_a_t2_input.jsonl` (350 queries)
  - `data/nlp_v2/gate_b3/model_a_t3_input.jsonl` (350 queries)
  - `data/nlp_v2/gate_b3/model_b_t2_input.jsonl` (350 queries)
  - `data/nlp_v2/gate_b3/model_b_t3_input.jsonl` (350 queries)
- Model annotator sanitized execution manifests:
  - `data/nlp_v2/gate_b3/model_a_execution_manifest.json` (OpenAI / GPT-6 Astra)
  - `data/nlp_v2/gate_b3/model_b_execution_manifest.json` (Anthropic / Claude Opus 4.6)
- Canonical output schema: `docs/nlp_v2/gate_b3/annotation_output_schema.json`

### 3. Tooling & Guardrails
- First-pass locking mechanism: `scripts/nlp_v2/gate_b3/lock_first_pass_annotations.py`
- Pairwise annotation stability suite: `scripts/nlp_v2/gate_b3/compute_annotation_stability.py`
- Package validator: `scripts/nlp_v2/gate_b3/validate_annotation_package.py`
- Pre-annotation QA gatekeeper: `scripts/nlp_v2/gate_b3/qa_gate_b3_preannotation.py`
- Annotation-start QA gatekeeper: `scripts/nlp_v2/gate_b3/qa_gate_b3_annotation_start.py` (runtime canonical configuration hash verification)
- Gold-boundary audit template: `data/nlp_v2/gate_b3/gold_boundary_audit_template.csv` (350 rows, blank annotations)
- Taxonomy decision document: `reports/nlp_v2/gate_b3/TAXONOMY_B3_DECISION_REQUIRED.md` (status: PENDING)
