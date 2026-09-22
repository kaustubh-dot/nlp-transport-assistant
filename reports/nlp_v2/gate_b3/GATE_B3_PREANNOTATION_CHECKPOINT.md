# GATE B.3 ANNOTATION-STABILITY FRAMEWORK

## PRE-ANNOTATION CHECKPOINT REPORT (AMENDED DESIGN)

**BASE COMMIT:**  
`2a2228d1762768af5994fc112710681a808262c6`

**ACTIVE KB:**  
`chennai_multimodal_v1.2.2`

**METHODOLOGY:**  
single-student blind audit  
+  
single isolated primary model annotator (Gemini 3.8 Flash)  
+  
post-lock gold-boundary audit  

**HUMAN IAA CLAIMED:**  
NO  

**TWO-MODEL-FAMILY AGREEMENT CLAIMED:**  
NO  

**SOURCE 350 SAMPLE:**  
rows: 350  
SHA: `94fd8bb3e7f2e3bdaf274c4ee5bcf7e083e9ef2a66322fbcf7bee2cadf231999`  
unchanged: YES  

**SAMPLE TYPE:**  
purposive enriched challenge sample  

**PRIMARY STUDENT ANNOTATOR:**  
`STUDENT_R1`  
READY / existing frozen student package  

**PRIMARY MODEL ANNOTATOR:**  
`MODEL_G` = Gemini 3.8 Flash (Google / Antigravity)  

**MODEL_G CONFIGURATION:**  
FROZEN  

**MODEL_G EXECUTION ISOLATION:**  
NOT YET VERIFIED  

**MODEL_G SYNTHETIC SMOKE TEST:**  
NOT YET RUN  

**MODEL_G BENCHMARK AUTHORIZED:**  
NO  

**PRIMARY ANNOTATION STARTED:**  
NO  

**FIRST-PASS LOCK:**  
NO  

**REFERENCE JOIN:**  
DISABLED  

**GOLD BOUNDARY AUDIT:**  
NOT STARTED  

**TAXONOMY DECISION:**  
PENDING  

**STATUS:**  
WAITING FOR MODEL_G STERILE PREFLIGHT / SMOKE TEST  

**HISTORICAL MODEL DESIGNS:**  
```text
MODEL_A / MODEL_B primary design:
RETIRED BY RESOURCE-FEASIBILITY AMENDMENT

MODEL_A (GPT-6 Astra):
23 T2 accepted / 0 T3 accepted
Aborted pre-amendment execution due to provider usage-limit rejection
Excluded from primary Gate B.3 analysis
Reserved for supervisory methodology review only

MODEL_B (Claude Opus 4.6):
Real benchmark execution: NONE
Retired pre-completion due to provider quota infeasibility
Excluded from primary Gate B.3 analysis
```

**GOVERNANCE PRINCIPLE:**  
> The originally authorized two-heavy-model execution design proved operationally infeasible under external provider usage limits.
> The prospective resource-feasibility amendment was adopted before any gold/reference access, before agreement calculations, and before first-pass lock.
> Benchmark authorization granted to previous models does NOT transfer to MODEL_G.
> MODEL_G must independently complete sterile preflight and synthetic smoke testing before benchmark execution may be authorized.

---

## Technical Summary of Framework Artifacts

### 1. Documentation & Guidelines
- Prospective methodology amendment: `docs/nlp_v2/gate_b3/gate_b3_annotation_methodology_amendment.md`
- Prospective execution-isolation amendment: `docs/nlp_v2/gate_b3/gate_b3_execution_isolation_amendment.md`
- Resource-feasibility / annotator-design amendment: `docs/nlp_v2/gate_b3/gate_b3_resource_feasibility_annotator_amendment.md`
- Neutral T2 annotation guide (12 classes): `docs/nlp_v2/gate_b3/t2_annotation_guide.md`
- Neutral T3 annotation guide (16 classes): `docs/nlp_v2/gate_b3/t3_annotation_guide.md`
- Isolated model prompt template & protocol: `docs/nlp_v2/gate_b3/model_annotator_prompt_template.md`
- Bootstrap interpretation clarification note: `reports/nlp_v2/gate_b3/gate_b2_bootstrap_interpretation_note.md`
- Pre-amendment model execution provenance: `reports/nlp_v2/gate_b3/GATE_B3_PRE_AMENDMENT_MODEL_EXECUTION_PROVENANCE.md`
- Model annotator sterile package transfer guide: `reports/nlp_v2/gate_b3/MODEL_ANNOTATOR_PACKAGE_TRANSFER.md`

### 2. Blind Annotation Packages & Sanitized Manifests
- Student order manifest: `data/nlp_v2/gate_b3/student_order_manifest.json` (deterministic 175/175 split, counterbalanced order)
- Student blind CSVs:
  - `data/nlp_v2/gate_b3/student_t2_first_pass.csv` (175 queries)
  - `data/nlp_v2/gate_b3/student_t3_first_pass.csv` (175 queries)
  - `data/nlp_v2/gate_b3/student_t2_second_pass.csv` (175 queries)
  - `data/nlp_v2/gate_b3/student_t3_second_pass.csv` (175 queries)
- Model annotator blind JSONLs (Active Primary):
  - `data/nlp_v2/gate_b3/model_g_t2_input.jsonl` (350 queries)
  - `data/nlp_v2/gate_b3/model_g_t3_input.jsonl` (350 queries)
- Model annotator sanitized execution manifests:
  - `data/nlp_v2/gate_b3/model_g_execution_manifest.json` (Google / Gemini 3.8 Flash, Active)
  - `data/nlp_v2/gate_b3/model_a_execution_manifest.json` (OpenAI / GPT-6 Astra, Historical)
  - `data/nlp_v2/gate_b3/model_b_execution_manifest.json` (Anthropic / Claude Opus 4.6, Historical)
- Canonical output schema: `docs/nlp_v2/gate_b3/annotation_output_schema.json`

### 3. Tooling & Guardrails
- First-pass locking mechanism: `scripts/nlp_v2/gate_b3/lock_first_pass_annotations.py`
- Pairwise annotation stability suite: `scripts/nlp_v2/gate_b3/compute_annotation_stability.py`
- Package validator: `scripts/nlp_v2/gate_b3/validate_annotation_package.py`
- Pre-annotation QA gatekeeper: `scripts/nlp_v2/gate_b3/qa_gate_b3_preannotation.py`
- Annotation-start QA gatekeeper: `scripts/nlp_v2/gate_b3/qa_gate_b3_annotation_start.py` (runtime canonical configuration hash verification)
- Gold-boundary audit template: `data/nlp_v2/gate_b3/gold_boundary_audit_template.csv` (350 rows, blank annotations)
- Taxonomy decision document: `reports/nlp_v2/gate_b3/TAXONOMY_B3_DECISION_REQUIRED.md` (status: PENDING)
