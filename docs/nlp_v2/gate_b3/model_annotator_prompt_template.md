# Gate B.3 Model Annotator Prompt Template & Execution Protocol

**Document:** `docs/nlp_v2/gate_b3/model_annotator_prompt_template.md`  
**Purpose:** Canonical prompt template and procedural protocol for isolated LLM annotators (`MODEL_A` and `MODEL_B`).  
**Status:** Approved Framework Specification — NO EXECUTION AUTHORIZED  

---

## 1. Core Operating Principles for Model Annotators

Every model annotator evaluation must adhere to strict procedural isolation:
1. **Single Isolated Request per Query/Taxonomy:** Each query classification request is completely stateless. It must NOT contain conversational history, previous query classifications, or chain-of-thought from other queries.
2. **Zero Repository Access:** The model must NOT have access to repository tools, file reading, code execution, web search, or database browsing.
3. **Zero Performance or Gold Context:** The prompt must NEVER mention Gate B.2 model accuracy, MuRIL performance, benchmark evaluation results, candidate winner statuses, or gold labels.
4. **Strict Schema Conformance:** Output must strictly adhere to `docs/nlp_v2/gate_b3/annotation_output_schema.json`.

---

## 2. Canonical Prompt Template

```markdown
You are a semantic annotation system.

Classify only the expressed user meaning in the provided commuter transit query.
Do not infer labels from what route would actually be optimal in physical transit.
Do not browse.
Do not use external tools.
Do not attempt to infer gold labels or benchmark expectations.
Return only the required structured JSON output conforming to the schema below.

### Intent Taxonomy: {TAXONOMY_VERSION} ({TAXONOMY_CLASS_COUNT} Classes)
Allowed Classes:
{TAXONOMY_CLASSES_LIST}

### Annotation Guidelines & Boundary Rules:
{TAXONOMY_GUIDELINES_TEXT}

### Ambiguity and Clarification Policy:
- If no single primary label is defensible due to genuine semantic ambiguity, set "primary_label": null, provide all plausible candidates in "acceptable_labels", and set "clarification_required": true.
- If the query has an unambiguous intent but lacks origin/destination slots (e.g., "How to go to Airport?"), classify the primary intent (e.g., "route_query" or "point_to_point_route"), mark "missing_slot" in clarification_reasons, and do NOT set primary_label to null.
- If the query explicitly asks for two separate operations (e.g., fare and schedule), include both in "acceptable_labels" and mark "multiple_goals" in clarification_reasons.
- If primary_label is non-null, it MUST be included in "acceptable_labels".

### Query to Annotate:
Query ID: {ANNOTATION_ID}
Query Text: "{QUERY_TEXT}"

### Output Schema:
Return a single JSON object with the following schema:
{
  "annotation_id": "{ANNOTATION_ID}",
  "source_id": "{SOURCE_ID}",
  "source_type": "model",
  "taxonomy_version": "{TAXONOMY_VERSION}",
  "run_id": "{RUN_ID}",
  "primary_label": "<canonical_class_or_null>",
  "acceptable_labels": ["<canonical_class>", ...],
  "clarification_required": <true|false>,
  "clarification_reasons": ["intent_ambiguity" | "missing_slot" | "multiple_goals" | "uninterpretable"],
  "brief_justification": "<concise_semantic_explanation>",
  "recognized_from_prior_work": "not_applicable",
  "response_status": "VALID"
}
```

---

## 3. Model Retry and Error Handling Policy

1. **Transport / Connection / Timeout Failure:**
   - Automatic retry is permitted.
2. **Malformed Structured Output (Schema Validation Failure):**
   - Exactly **one** fixed format-repair attempt is allowed: the malformed output is supplied back to the model with the schema error and instruction to return valid JSON.
   - If repaired, `response_status` is recorded as `"FORMAT_REPAIRED"`.
   - If second attempt fails, `response_status` is recorded as `"FAILED"`.
3. **Semantic Disagreement with Expected Result:**
   - **STRICTLY FORBIDDEN:** Under no circumstances may a query be retried because the assigned label differs from gold, differs from the student annotator, looks surprising, or yields lower agreement.
   - Original raw responses and parsed outputs must be preserved.

---

## 4. Model Independence and Provenance Language

- `MODEL_A` and `MODEL_B` must represent distinct model configurations, ideally from separate foundational model families (e.g., Gemini and Anthropic/OpenAI).
- Separate API execution does NOT guarantee cognitive independence: models share pretraining distribution mass, synthetic web text, and alignment objectives.
- Agreement between models is explicitly designated **cross-model annotation stability**, not human labelability.

---

## 5. Astra-Specific Provenance Guardrail

If Astra / Gemini is utilized as a model annotator (`MODEL_A` or `MODEL_B`):
- The conversational context used for methodology review, experimental planning, or code generation must **NEVER** be reused.
- A fresh, sterile API request context must be created for every single item, ensuring no contamination from project history or discussions.
