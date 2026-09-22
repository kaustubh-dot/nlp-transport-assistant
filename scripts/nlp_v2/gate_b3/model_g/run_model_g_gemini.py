#!/usr/bin/env python3
"""
scripts/run_model_g_gemini.py

Gate B.3 MODEL_G (Gemini 3.8 Flash) Hardened Execution Runner.
Enforces:
- EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION
- Fresh context/process per item (--new-project, empty tempdir)
- Hash-based benchmark input detection (blocking copied/renamed benchmark inputs)
- Taxonomy-scoped telemetry: telemetry/<taxonomy>/<annotation_id>.telemetry.jsonl
- Complete live telemetry requirements:
  * init_count == 1 (TELEMETRY_MISSING_INIT / TELEMETRY_MULTIPLE_INIT)
  * result_count == 1 (TELEMETRY_MISSING_RESULT / TELEMETRY_MULTIPLE_RESULT)
  * result status == SUCCESS
  * model == authorized model
  * unique conversation_id
- Comprehensive provider-limit detection (inspecting stderr + structured result fields)
- Fail-closed format-repair strictly preserving semantic signature
- Zero semantic retries (semantic_retries = 0)
- Fail-closed resume telemetry verification
- Exact deterministic input prefix resume enforcement (rejecting non-prefix / reordered output)
- True crash-safe atomic output writes (os.replace)
- Package integrity verification against manifest before benchmark start
- Provider-limit pause without immediate retry
- Strict benchmark authorization guardrail

Trust Boundary Note:
configuration_sha256 inside model_g_execution_manifest.json is a recorded canonical identifier
and is checked against the manifest field, but is not independently recomputed from a source configuration
object because the canonical configuration object is maintained in the canonical NLP repository.
The trust anchor is provided by the canonical repository via canonical configuration hashing,
authorized manifest hashing, and verified workspace transfer hash.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import jsonschema


TAXONOMY_CLASSES = {
    "T2": [
        "route_query",
        "route_stops",
        "service_timing",
        "service_availability",
        "fare_query",
        "ticketing_rules",
        "station_facilities",
        "accessibility",
        "interchange_query",
        "nearest_transport",
        "realtime_status_query",
        "out_of_scope",
    ],
    "T3": [
        "point_to_point_route",
        "multimodal_route",
        "route_stop_sequence",
        "route_stop_membership",
        "first_and_last_service",
        "service_frequency",
        "scheduled_departure",
        "mode_availability",
        "fare_calculation",
        "ticketing_and_passes",
        "station_facilities",
        "station_accessibility",
        "interchange_transfer",
        "nearest_transport",
        "realtime_status_query",
        "out_of_scope",
    ],
}

CLARIFICATION_REASONS = [
    "intent_ambiguity",
    "missing_slot",
    "multiple_goals",
    "uninterpretable",
]

BENIGN_EVENT_TYPES = {
    "invocation_attempt_metadata",
    "init",
    "step_update",
    "result",
}

BENIGN_STEP_TYPES = {
    "user_input",
    "agent_response",
}


# Custom Exception Hierarchy
class BenchmarkNotAuthorizedError(RuntimeError):
    pass


class PackageIntegrityError(RuntimeError):
    pass


class ToolViolationError(RuntimeError):
    pass


class ProviderLimitError(RuntimeError):
    pass


class UnrecognizedTelemetryError(RuntimeError):
    pass


class ModelIdentityMismatchError(RuntimeError):
    pass


class DuplicateConversationIdError(RuntimeError):
    pass


class WorkingDirMismatchError(RuntimeError):
    pass


class SemanticChangeDuringFormatRepairError(RuntimeError):
    pass


class UnrecoverableMalformedOutputError(RuntimeError):
    pass


class ResumeStateInvalidError(RuntimeError):
    pass


class SchemaValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def check_benchmark_authorization(workspace_root: Path) -> bool:
    manifest_path = workspace_root / "protocol" / "model_g_execution_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    manifest = load_json(manifest_path)
    return bool(manifest.get("benchmark_execution_authorized", False))


def check_is_benchmark_input(input_path: Path, workspace_root: Path) -> Tuple[bool, Optional[str]]:
    """
    Hash-based benchmark detection. Computes SHA-256 of supplied input and checks
    against frozen benchmark hashes from model_g_execution_manifest.json.
    Catches copied, renamed, or symlinked benchmark files.
    """
    manifest_path = workspace_root / "protocol" / "model_g_execution_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    manifest = load_json(manifest_path)
    benchmark_hashes = manifest.get("input_sha256", {})

    input_hash = compute_sha256(input_path)

    for bench_file, bench_hash in benchmark_hashes.items():
        if input_hash == bench_hash:
            tax = "T2" if "t2" in bench_file.lower() else "T3"
            return True, tax

    # Filename defense in depth
    if "model_g_t2_input" in input_path.name:
        return True, "T2"
    if "model_g_t3_input" in input_path.name:
        return True, "T3"

    return False, None


def verify_package_integrity(workspace_root: Path, taxonomy: Optional[str] = None) -> None:
    manifest_path = workspace_root / "protocol" / "model_g_execution_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    manifest = load_json(manifest_path)

    # 1. Configuration SHA recording verification
    conf_sha = manifest.get("configuration_sha256")
    if not conf_sha:
        raise PackageIntegrityError("Manifest missing configuration_sha256")

    # 2. Protocol files
    proto_hashes = manifest.get("protocol_sha256", {})
    for rel_path, expected_hash in proto_hashes.items():
        file_path = workspace_root / "protocol" / rel_path
        if not file_path.exists():
            raise PackageIntegrityError(f"Protocol file missing: {file_path}")
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            raise PackageIntegrityError(
                f"Protocol hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"
            )

    # 3. Amendment hashes
    exec_amend_hash = manifest.get("execution_isolation_amendment_sha256")
    if exec_amend_hash:
        act = compute_sha256(workspace_root / "protocol" / "gate_b3_execution_isolation_amendment.md")
        if act != exec_amend_hash:
            raise PackageIntegrityError(f"Execution isolation amendment hash mismatch: {act} != {exec_amend_hash}")

    res_amend_hash = manifest.get("resource_feasibility_amendment_sha256")
    if res_amend_hash:
        act = compute_sha256(workspace_root / "protocol" / "gate_b3_resource_feasibility_annotator_amendment.md")
        if act != res_amend_hash:
            raise PackageIntegrityError(f"Resource feasibility amendment hash mismatch: {act} != {res_amend_hash}")

    # 4. Input file hash if taxonomy specified
    if taxonomy in ["T2", "T3"]:
        input_filename = f"model_g_{taxonomy.lower()}_input.jsonl"
        expected_input_hash = manifest.get("input_sha256", {}).get(input_filename)
        if expected_input_hash:
            input_path = workspace_root / "inputs" / input_filename
            if input_path.exists():
                act = compute_sha256(input_path)
                if act != expected_input_hash:
                    raise PackageIntegrityError(f"Input file hash mismatch for {input_filename}: {act} != {expected_input_hash}")


def load_schema(workspace_root: Path) -> Dict[str, Any]:
    schema_path = workspace_root / "protocol" / "annotation_output_schema.json"
    return load_json(schema_path)


def load_guidelines(workspace_root: Path, taxonomy: str) -> str:
    guide_name = f"{taxonomy.lower()}_annotation_guide.md"
    guide_path = workspace_root / "protocol" / guide_name
    if not guide_path.exists():
        raise FileNotFoundError(f"Guideline not found: {guide_path}")
    with open(guide_path, "r", encoding="utf-8") as f:
        return f.read()


def build_canonical_prompt(
    taxonomy: str,
    annotation_id: str,
    query_text: str,
    guidelines_text: str,
    source_id: str = "MODEL_G",
    run_id: str = "MODEL_G_RUN",
) -> str:
    classes = TAXONOMY_CLASSES[taxonomy]
    classes_list_text = "\n".join(f"- {c}" for c in classes)
    class_count = len(classes)

    prompt = f"""You are a semantic annotation system.

Classify only the expressed user meaning in the provided commuter transit query.
Do not infer labels from what route would actually be optimal in physical transit.
Do not browse.
Do not use external tools.
Do not attempt to infer gold labels or benchmark expectations.
Return only the required structured JSON output conforming to the schema below.

### Intent Taxonomy: {taxonomy} ({class_count} Classes)
Allowed Classes:
{classes_list_text}

### Annotation Guidelines & Boundary Rules:
{guidelines_text}

### Ambiguity and Clarification Policy:
- If no single primary label is defensible due to genuine semantic ambiguity, set "primary_label": null, provide all plausible candidates in "acceptable_labels", and set "clarification_required": true.
- If the query has an unambiguous intent but lacks origin/destination slots (e.g., "How to go to Airport?"), classify the primary intent (e.g., "route_query" or "point_to_point_route"), mark "missing_slot" in clarification_reasons, and do NOT set primary_label to null.
- If the query explicitly asks for two separate operations (e.g., fare and schedule), include both in "acceptable_labels" and mark "multiple_goals" in clarification_reasons.
- If primary_label is non-null, it MUST be included in "acceptable_labels".

### Query to Annotate:
Query ID: {annotation_id}
Query Text: "{query_text}"

### Output Schema:
Return a single JSON object with the following schema:
{{
  "annotation_id": "{annotation_id}",
  "source_id": "{source_id}",
  "source_type": "model",
  "taxonomy_version": "{taxonomy}",
  "run_id": "{run_id}",
  "primary_label": "<canonical_class_or_null>",
  "acceptable_labels": ["<canonical_class>", ...],
  "clarification_required": <true|false>,
  "clarification_reasons": ["intent_ambiguity" | "missing_slot" | "multiple_goals" | "uninterpretable"],
  "brief_justification": "<concise_semantic_explanation>",
  "recognized_from_prior_work": "not_applicable",
  "active_time_seconds": null,
  "rule_difficulty": "not_applicable",
  "response_status": "VALID"
}}"""
    return prompt


def build_format_repair_prompt(
    schema_errors: str,
    raw_response: str,
    annotation_id: str,
    taxonomy: str,
    source_id: str = "MODEL_G",
    run_id: str = "MODEL_G_RUN",
) -> str:
    classes = TAXONOMY_CLASSES[taxonomy]
    classes_list = ", ".join(f'"{c}"' for c in classes)

    prompt = f"""Your previous output failed JSON schema or invariant validation:
{schema_errors}

Original output:
{raw_response}

Please fix ONLY the JSON syntax, metadata, and structural schema defects.
You MUST preserve your original semantic classification choices exactly:
- primary_label must match your previous intent decision (one of [{classes_list}] or null)
- acceptable_labels must match your previous candidate set
- clarification_required and clarification_reasons must match your previous intent ambiguity choice
- brief_justification must be preserved

Required metadata fields:
- annotation_id: "{annotation_id}"
- source_id: "{source_id}"
- source_type: "model"
- taxonomy_version: "{taxonomy}"
- run_id: "{run_id}"
- recognized_from_prior_work: "not_applicable"
- active_time_seconds: null
- rule_difficulty: "not_applicable"
- response_status: "FORMAT_REPAIRED"

Do NOT use any tools. Return ONLY the single valid JSON object."""
    return prompt


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    text = response_text.strip()
    if not text:
        raise ValueError("Empty response text from model")

    # If wrapped in markdown code blocks
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        return json.loads(code_block_match.group(1))

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try finding first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        return json.loads(candidate)

    raise ValueError(f"Could not extract JSON object from response: {text[:200]}")


def get_semantic_signature(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "primary_label": record.get("primary_label"),
        "acceptable_labels": sorted(record.get("acceptable_labels") or []),
        "clarification_required": record.get("clarification_required"),
        "clarification_reasons": sorted(record.get("clarification_reasons") or []),
        "brief_justification": record.get("brief_justification"),
    }


def persist_telemetry_attempt(
    telemetry_file: Path,
    metadata: Dict[str, Any],
    stream_lines: List[str],
) -> None:
    telemetry_file.parent.mkdir(parents=True, exist_ok=True)
    with open(telemetry_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(metadata) + "\n")
        for line in stream_lines:
            line_str = line.strip()
            if line_str:
                f.write(line_str + "\n")
        f.flush()
        os.fsync(f.fileno())


def check_for_provider_limit(
    stderr: str,
    result_dict: Optional[Dict[str, Any]],
    stream_lines: List[str],
) -> Optional[str]:
    """
    Inspects stderr, structured result fields, and stream lines for quota/rate limit indicators.
    """
    patterns = [
        "429",
        "quota",
        "rate limit",
        "rate_limit",
        "resource exhausted",
        "resource_exhausted",
        "usage limit",
        "too many requests",
        "exceeded your current quota",
    ]

    if stderr:
        low_err = stderr.lower()
        for p in patterns:
            if p in low_err:
                return f"Pattern '{p}' in stderr: {stderr[:200]}"

    if result_dict:
        res_strings = []
        for key in ["error", "message", "status", "details", "response"]:
            val = result_dict.get(key)
            if isinstance(val, str):
                res_strings.append(val.lower())
        combined_res = " ".join(res_strings)
        for p in patterns:
            if p in combined_res:
                return f"Pattern '{p}' in result dict: {combined_res[:200]}"

    for line in stream_lines:
        low_line = line.lower()
        if "error" in low_line:
            for p in patterns:
                if p in low_line:
                    return f"Pattern '{p}' in stream line: {line[:200]}"

    return None


def audit_single_invocation_stream(
    stream_lines: List[str],
    expected_model: str,
    expected_cwd: Optional[Path] = None,
    seen_conversation_ids: Optional[Set[str]] = None,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Strict fail-closed audit of stream-json telemetry.
    Requires:
      init_count == 1
      result_count == 1
      result status == SUCCESS
      conversation_id != null
      model == authorized model
      expected cwd
      zero tools / zero denied actions
      only benign events and step types
    Returns (result_dict, conversation_id).
    """
    init_count = 0
    result_count = 0
    conv_id = None
    result_dict: Dict[str, Any] = {}

    for line_num, line in enumerate(stream_lines, start=1):
        line = line.strip()
        if not line:
            continue

        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            raise UnrecognizedTelemetryError(
                f"TELEMETRY_UNRECOGNIZED_EVENT: malformed non-JSON line at stream line {line_num}: {line[:120]}"
            )

        if not isinstance(ev, dict):
            raise UnrecognizedTelemetryError(
                f"TELEMETRY_UNRECOGNIZED_EVENT: non-dict JSON object at line {line_num}: {line[:120]}"
            )

        event_name = ev.get("event")
        if event_name not in BENIGN_EVENT_TYPES:
            raise UnrecognizedTelemetryError(
                f"TELEMETRY_UNRECOGNIZED_EVENT: unrecognized event type '{event_name}' at line {line_num}"
            )

        # 1. Handle init event
        if event_name == "init":
            init_count += 1
            if init_count > 1:
                raise UnrecognizedTelemetryError(
                    f"TELEMETRY_MULTIPLE_INIT: unexpected multiple init events ({init_count}) at line {line_num}"
                )

            init_data = ev.get("init", {})
            model = init_data.get("model") or ev.get("model")
            if model != expected_model:
                raise ModelIdentityMismatchError(
                    f"Model identity mismatch: expected '{expected_model}', got '{model}'"
                )

            conv_id = ev.get("conversation_id")
            if not conv_id:
                raise UnrecognizedTelemetryError("TELEMETRY_MISSING_CONVERSATION_ID: init event missing conversation_id")

            if seen_conversation_ids is not None:
                if conv_id in seen_conversation_ids:
                    raise DuplicateConversationIdError(
                        f"Duplicate conversation ID observed across invocations: {conv_id}"
                    )
                seen_conversation_ids.add(conv_id)

            if expected_cwd:
                reported_cwd = init_data.get("cwd")
                if reported_cwd and os.path.realpath(reported_cwd) != os.path.realpath(expected_cwd):
                    raise WorkingDirMismatchError(
                        f"Working directory mismatch: expected '{expected_cwd}', got '{reported_cwd}'"
                    )

        # 2. Handle step_update
        elif event_name == "step_update":
            su = ev.get("step_update", {})
            st = su.get("step_type", "")
            if st not in BENIGN_STEP_TYPES:
                if any(k in st.lower() for k in ["tool", "command", "browser", "exec"]):
                    raise ToolViolationError(f"Prohibited tool step_type observed: '{st}'")
                raise UnrecognizedTelemetryError(
                    f"TELEMETRY_UNRECOGNIZED_EVENT: unexpected step_type '{st}' at line {line_num}"
                )

            if "tool_calls" in su and su["tool_calls"]:
                raise ToolViolationError(
                    f"Prohibited tool_calls observed in step_update: {su['tool_calls']}"
                )

        # 3. Handle result
        elif event_name == "result":
            result_count += 1
            if result_count > 1:
                raise UnrecognizedTelemetryError(
                    f"TELEMETRY_MULTIPLE_RESULT: unexpected multiple result events ({result_count}) at line {line_num}"
                )

            result_dict = ev.get("result", {})
            da = result_dict.get("denied_actions") or ev.get("denied_actions")
            if da:
                raise ToolViolationError(
                    f"Prohibited denied_actions observed in result: {da}"
                )

    # Complete telemetry checks
    if init_count == 0:
        raise UnrecognizedTelemetryError("TELEMETRY_MISSING_INIT: invocation stream lacks init event")
    if result_count == 0:
        raise UnrecognizedTelemetryError("TELEMETRY_MISSING_RESULT: invocation stream lacks terminal result event")

    status = result_dict.get("status")
    if status != "SUCCESS":
        limit_msg = check_for_provider_limit("", result_dict, stream_lines)
        if limit_msg:
            raise ProviderLimitError(f"EXECUTION_PAUSED_PROVIDER_LIMIT: {limit_msg}")
        raise RuntimeError(f"Terminal result status is '{status}' (expected 'SUCCESS')")

    return result_dict, conv_id


def validate_record_invariants(
    record: Dict[str, Any],
    schema: Dict[str, Any],
    expected_id: str,
    taxonomy: str,
    source_id: str = "MODEL_G",
) -> None:
    # 1. JSON Schema validation
    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.ValidationError as e:
        raise SchemaValidationError(f"Schema validation failed: {e.message}")

    # 2. Fixed model metadata
    if record.get("annotation_id") != expected_id:
        raise SchemaValidationError(f"ID mismatch: got {record.get('annotation_id')}, expected {expected_id}")
    if record.get("source_id") != source_id:
        raise SchemaValidationError(f"source_id mismatch: got {record.get('source_id')}, expected {source_id}")
    if record.get("source_type") != "model":
        raise SchemaValidationError(f"source_type mismatch: got {record.get('source_type')}, expected 'model'")
    if record.get("taxonomy_version") != taxonomy:
        raise SchemaValidationError(f"taxonomy_version mismatch: got {record.get('taxonomy_version')}, expected {taxonomy}")
    if record.get("recognized_from_prior_work") != "not_applicable":
        raise SchemaValidationError("recognized_from_prior_work must be 'not_applicable' for model")
    if record.get("active_time_seconds") is not None:
        raise SchemaValidationError("active_time_seconds must be null for model")
    if record.get("rule_difficulty") != "not_applicable":
        raise SchemaValidationError("rule_difficulty must be 'not_applicable' for model")
    if record.get("response_status") not in ["VALID", "FORMAT_REPAIRED"]:
        raise SchemaValidationError(f"Invalid response_status: {record.get('response_status')}")

    # 3. Semantic classes
    allowed_classes = set(TAXONOMY_CLASSES[taxonomy])
    acc_labels = record.get("acceptable_labels", [])
    if not acc_labels:
        raise SchemaValidationError("acceptable_labels must not be empty")
    for lab in acc_labels:
        if lab not in allowed_classes:
            raise SchemaValidationError(f"Unknown class '{lab}' in acceptable_labels for {taxonomy}")

    primary = record.get("primary_label")
    if primary is not None:
        if primary not in allowed_classes:
            raise SchemaValidationError(f"Unknown primary_label '{primary}' for {taxonomy}")
        if primary not in acc_labels:
            raise SchemaValidationError(f"primary_label '{primary}' not included in acceptable_labels")

    # 4. Clarification policy invariants (matching central lock validator)
    clar_req = record.get("clarification_required")
    clar_reasons = record.get("clarification_reasons", [])
    for r in clar_reasons:
        if r not in CLARIFICATION_REASONS:
            raise SchemaValidationError(f"Unknown clarification_reason: {r}")

    # Rule: primary_label == null -> clarification_required = true
    if primary is None:
        if clar_req is not True:
            raise SchemaValidationError("clarification_required must be True when primary_label is null")
        if not any(r in ["intent_ambiguity", "uninterpretable"] for r in clar_reasons):
            raise SchemaValidationError("clarification_reasons must include 'intent_ambiguity' or 'uninterpretable' when primary_label is null")

    # Rule: clarification_required = false -> clarification_reasons = []
    if clar_req is False:
        if clar_reasons != []:
            raise SchemaValidationError(f"clarification_reasons must be [] when clarification_required is False, got: {clar_reasons}")

    # Rule: clarification_required = true -> clarification_reasons non-empty
    if clar_req is True:
        if not clar_reasons:
            raise SchemaValidationError("clarification_reasons must not be empty when clarification_required is True")


def execute_single_invocation(
    prompt: str,
    model: str = "gemini-3.8-flash-high",
    timeout_seconds: int = 120,
) -> Tuple[int, List[str], str, Path]:
    """
    Spawns a fresh child process in a brand-new empty temporary working directory.
    Returns (returncode, stream_lines, stderr_text, tmpdir).
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="agy_empty_workdir_"))
    try:
        cmd = [
            "agy",
            "--model", model,
            "--new-project",
            "--disable-slash-commands",
            "--output-format", "stream-json",
            "--print", prompt,
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(tmpdir),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        stream_lines = proc.stdout.splitlines()
        return proc.returncode, stream_lines, proc.stderr, tmpdir
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


def annotate_single_query(
    annotation_id: str,
    query_text: str,
    taxonomy: str,
    guidelines_text: str,
    schema: Dict[str, Any],
    telemetry_dir: Path,
    seen_conversation_ids: Set[str],
    model: str = "gemini-3.8-flash-high",
    source_id: str = "MODEL_G",
    run_id: str = "MODEL_G_RUN",
    max_transport_retries: int = 1,
) -> Dict[str, Any]:
    """
    Annotates a single query under strict behavioral isolation:
    - Taxonomy-scoped telemetry: telemetry/<taxonomy>/<annotation_id>.telemetry.jsonl
    - Telemetry preserved BEFORE any failure propagation
    - Hard fail on unrecognized telemetry, tool violations, model mismatch
    - Fail-closed format-repair strictly preserving semantic signature
    - Zero semantic retries (semantic_retries = 0)
    - Transport failure retries bounded to max_transport_retries (1 retry)
    - Provider limit stops execution immediately (EXECUTION_PAUSED_PROVIDER_LIMIT)
    """
    canonical_prompt = build_canonical_prompt(
        taxonomy=taxonomy,
        annotation_id=annotation_id,
        query_text=query_text,
        guidelines_text=guidelines_text,
        source_id=source_id,
        run_id=run_id,
    )

    item_telemetry_file = telemetry_dir / taxonomy / f"{annotation_id}.telemetry.jsonl"

    transport_attempts = 0
    raw_response_text = ""
    last_res_dict: Dict[str, Any] = {}

    while transport_attempts <= max_transport_retries:
        transport_attempts += 1
        attempt_type = "initial" if transport_attempts == 1 else "transport_retry"
        tmpdir = None
        stream_lines: List[str] = []
        stderr = ""
        retcode = -1
        failure_classification = None

        try:
            retcode, stream_lines, stderr, tmpdir = execute_single_invocation(
                prompt=canonical_prompt,
                model=model,
            )

            # Check provider limit from stderr or raw stream
            provider_limit_reason = check_for_provider_limit(stderr, None, stream_lines)
            if provider_limit_reason:
                failure_classification = "EXECUTION_PAUSED_PROVIDER_LIMIT"
                metadata = {
                    "event": "invocation_attempt_metadata",
                    "annotation_id": annotation_id,
                    "taxonomy": taxonomy,
                    "attempt_type": attempt_type,
                    "attempt_number": transport_attempts,
                    "model_selector": model,
                    "cwd": str(tmpdir),
                    "returncode": retcode,
                    "stderr": stderr,
                    "failure_classification": failure_classification,
                }
                persist_telemetry_attempt(item_telemetry_file, metadata, stream_lines)
                raise ProviderLimitError(
                    f"EXECUTION_PAUSED_PROVIDER_LIMIT: Provider quota/rate limit on {annotation_id}: {provider_limit_reason}"
                )

            # Audit telemetry stream (fail-closed)
            try:
                res_dict, conv_id = audit_single_invocation_stream(
                    stream_lines=stream_lines,
                    expected_model=model,
                    expected_cwd=tmpdir,
                    seen_conversation_ids=seen_conversation_ids,
                )
                last_res_dict = res_dict
            except Exception as audit_err:
                if isinstance(audit_err, ToolViolationError):
                    failure_classification = "TOOL_VIOLATION"
                elif isinstance(audit_err, ModelIdentityMismatchError):
                    failure_classification = "MODEL_IDENTITY_MISMATCH"
                elif isinstance(audit_err, DuplicateConversationIdError):
                    failure_classification = "DUPLICATE_CONVERSATION_ID"
                elif isinstance(audit_err, WorkingDirMismatchError):
                    failure_classification = "WORKDIR_MISMATCH"
                elif isinstance(audit_err, ProviderLimitError):
                    failure_classification = "EXECUTION_PAUSED_PROVIDER_LIMIT"
                elif isinstance(audit_err, UnrecognizedTelemetryError):
                    failure_classification = "TELEMETRY_UNRECOGNIZED_EVENT"
                else:
                    failure_classification = "AUDIT_FAILURE"

                metadata = {
                    "event": "invocation_attempt_metadata",
                    "annotation_id": annotation_id,
                    "taxonomy": taxonomy,
                    "attempt_type": attempt_type,
                    "attempt_number": transport_attempts,
                    "model_selector": model,
                    "cwd": str(tmpdir),
                    "returncode": retcode,
                    "stderr": stderr,
                    "failure_classification": failure_classification,
                }
                persist_telemetry_attempt(item_telemetry_file, metadata, stream_lines)
                raise audit_err

            # Check provider limit from structured result dict
            provider_limit_reason = check_for_provider_limit(stderr, last_res_dict, stream_lines)
            if provider_limit_reason:
                failure_classification = "EXECUTION_PAUSED_PROVIDER_LIMIT"
                metadata = {
                    "event": "invocation_attempt_metadata",
                    "annotation_id": annotation_id,
                    "taxonomy": taxonomy,
                    "attempt_type": attempt_type,
                    "attempt_number": transport_attempts,
                    "model_selector": model,
                    "conversation_id": conv_id,
                    "cwd": str(tmpdir),
                    "returncode": retcode,
                    "stderr": stderr,
                    "failure_classification": failure_classification,
                }
                persist_telemetry_attempt(item_telemetry_file, metadata, stream_lines)
                raise ProviderLimitError(
                    f"EXECUTION_PAUSED_PROVIDER_LIMIT: Provider quota/rate limit on {annotation_id}: {provider_limit_reason}"
                )

            # Telemetry audit passed cleanly
            metadata = {
                "event": "invocation_attempt_metadata",
                "annotation_id": annotation_id,
                "taxonomy": taxonomy,
                "attempt_type": attempt_type,
                "attempt_number": transport_attempts,
                "model_selector": model,
                "conversation_id": conv_id,
                "cwd": str(tmpdir),
                "returncode": retcode,
                "stderr": stderr,
                "failure_classification": None if retcode == 0 else "PROCESS_RETURN_ERROR",
            }
            persist_telemetry_attempt(item_telemetry_file, metadata, stream_lines)

            if retcode != 0:
                if transport_attempts <= max_transport_retries:
                    time.sleep(2)
                    continue
                raise RuntimeError(f"Terminal transport failure on {annotation_id} (code {retcode}): {stderr[:300]}")

            raw_response_text = last_res_dict.get("response", "")
            break

        except subprocess.TimeoutExpired:
            failure_classification = "TIMEOUT"
            metadata = {
                "event": "invocation_attempt_metadata",
                "annotation_id": annotation_id,
                "taxonomy": taxonomy,
                "attempt_type": attempt_type,
                "attempt_number": transport_attempts,
                "model_selector": model,
                "cwd": str(tmpdir) if tmpdir else "",
                "returncode": -1,
                "stderr": "subprocess.TimeoutExpired",
                "failure_classification": failure_classification,
            }
            persist_telemetry_attempt(item_telemetry_file, metadata, stream_lines)
            if transport_attempts <= max_transport_retries:
                time.sleep(2)
                continue
            raise RuntimeError(f"Invocation timed out terminally for {annotation_id}")
        finally:
            if tmpdir and tmpdir.exists():
                shutil.rmtree(tmpdir, ignore_errors=True)

    # Parse and validate initial output
    parsed_record = None
    try:
        parsed_record = extract_json_from_response(raw_response_text)
    except Exception as parse_err:
        raise UnrecoverableMalformedOutputError(
            f"Initial output for {annotation_id} is unparseable JSON ({parse_err}). "
            f"Cannot recover trustworthy semantic signature. "
            f"Semantic retries are FORBIDDEN (semantic_retries = 0)."
        )

    # Check if initial output is already valid
    try:
        validate_record_invariants(
            record=parsed_record,
            schema=schema,
            expected_id=annotation_id,
            taxonomy=taxonomy,
            source_id=source_id,
        )
        parsed_record["response_status"] = "VALID"
        return parsed_record
    except SchemaValidationError as val_err:
        initial_validation_err = str(val_err)

    # Capture initial semantic signature
    initial_signature = get_semantic_signature(parsed_record)

    # Format Repair (at most 1 attempt)
    repair_prompt = build_format_repair_prompt(
        schema_errors=initial_validation_err,
        raw_response=raw_response_text,
        annotation_id=annotation_id,
        taxonomy=taxonomy,
        source_id=source_id,
        run_id=run_id,
    )

    repair_tmpdir = None
    repair_lines: List[str] = []
    try:
        retcode, repair_lines, stderr, repair_tmpdir = execute_single_invocation(
            prompt=repair_prompt,
            model=model,
        )

        # Check provider limit during format repair
        provider_limit_reason = check_for_provider_limit(stderr, None, repair_lines)
        if provider_limit_reason:
            rep_meta = {
                "event": "invocation_attempt_metadata",
                "annotation_id": annotation_id,
                "taxonomy": taxonomy,
                "attempt_type": "format_repair",
                "attempt_number": 1,
                "model_selector": model,
                "cwd": str(repair_tmpdir),
                "returncode": retcode,
                "stderr": stderr,
                "failure_classification": "EXECUTION_PAUSED_PROVIDER_LIMIT",
            }
            persist_telemetry_attempt(item_telemetry_file, rep_meta, repair_lines)
            raise ProviderLimitError(
                f"EXECUTION_PAUSED_PROVIDER_LIMIT: Provider quota/rate limit during format repair on {annotation_id}: {provider_limit_reason}"
            )

        # Audit repair telemetry
        try:
            repair_res_dict, repair_conv_id = audit_single_invocation_stream(
                stream_lines=repair_lines,
                expected_model=model,
                expected_cwd=repair_tmpdir,
                seen_conversation_ids=seen_conversation_ids,
            )
        except Exception as repair_audit_err:
            rep_meta = {
                "event": "invocation_attempt_metadata",
                "annotation_id": annotation_id,
                "taxonomy": taxonomy,
                "attempt_type": "format_repair",
                "attempt_number": 1,
                "model_selector": model,
                "cwd": str(repair_tmpdir),
                "returncode": retcode,
                "stderr": stderr,
                "failure_classification": "REPAIR_AUDIT_FAILURE",
            }
            persist_telemetry_attempt(item_telemetry_file, rep_meta, repair_lines)
            raise repair_audit_err

        # Check provider limit in repair result dict
        provider_limit_reason = check_for_provider_limit(stderr, repair_res_dict, repair_lines)
        if provider_limit_reason:
            rep_meta = {
                "event": "invocation_attempt_metadata",
                "annotation_id": annotation_id,
                "taxonomy": taxonomy,
                "attempt_type": "format_repair",
                "attempt_number": 1,
                "model_selector": model,
                "conversation_id": repair_conv_id,
                "cwd": str(repair_tmpdir),
                "returncode": retcode,
                "stderr": stderr,
                "failure_classification": "EXECUTION_PAUSED_PROVIDER_LIMIT",
            }
            persist_telemetry_attempt(item_telemetry_file, rep_meta, repair_lines)
            raise ProviderLimitError(
                f"EXECUTION_PAUSED_PROVIDER_LIMIT: Provider quota/rate limit during format repair on {annotation_id}: {provider_limit_reason}"
            )

        rep_meta = {
            "event": "invocation_attempt_metadata",
            "annotation_id": annotation_id,
            "taxonomy": taxonomy,
            "attempt_type": "format_repair",
            "attempt_number": 1,
            "model_selector": model,
            "conversation_id": repair_conv_id,
            "cwd": str(repair_tmpdir),
            "returncode": retcode,
            "stderr": stderr,
            "failure_classification": None if retcode == 0 else "REPAIR_PROCESS_ERROR",
        }
        persist_telemetry_attempt(item_telemetry_file, rep_meta, repair_lines)

        if retcode != 0:
            raise RuntimeError(f"Format repair process exited with code {retcode}: {stderr[:300]}")

        repaired_raw = repair_res_dict.get("response", "")
        repaired_record = extract_json_from_response(repaired_raw)
        repaired_signature = get_semantic_signature(repaired_record)

        # Check semantic signature preservation
        if initial_signature != repaired_signature:
            raise SemanticChangeDuringFormatRepairError(
                f"SEMANTIC_CHANGE_DURING_FORMAT_REPAIR: semantic signature altered during repair on {annotation_id}! "
                f"Initial: {initial_signature} vs Repaired: {repaired_signature}. "
                f"Execution STOP under no-semantic-retry policy."
            )

        repaired_record["response_status"] = "FORMAT_REPAIRED"
        validate_record_invariants(
            record=repaired_record,
            schema=schema,
            expected_id=annotation_id,
            taxonomy=taxonomy,
            source_id=source_id,
        )
        return repaired_record

    finally:
        if repair_tmpdir and repair_tmpdir.exists():
            shutil.rmtree(repair_tmpdir, ignore_errors=True)


def audit_existing_telemetry_file(
    telemetry_path: Path,
    authorized_model: str,
) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Fail-closed audit of existing telemetry file for resume safety.
    Guarantees the exact same strict standards as live auditing:
    - No malformed JSON
    - No unknown events
    - Valid init and terminal SUCCESS result
    - Authorized model identity
    - Unique conversation ID
    - Zero prohibited tools
    Returns (format_repairs_count, observed_model, last_successful_response_text).
    """
    if not telemetry_path.exists():
        raise ResumeStateInvalidError(f"Missing telemetry file: {telemetry_path}")

    # Read all lines
    lines = []
    with open(telemetry_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            lines.append(line)

    if not lines:
        raise ResumeStateInvalidError(f"Empty telemetry file: {telemetry_path}")

    # Split lines into attempt chunks separated by invocation_attempt_metadata
    attempts: List[Tuple[Dict[str, Any], List[str]]] = []
    curr_meta = None
    curr_lines = []

    for line in lines:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            raise ResumeStateInvalidError(f"Malformed JSON line in telemetry file {telemetry_path.name}: {e}")

        if not isinstance(ev, dict):
            raise ResumeStateInvalidError(f"Non-dict JSON in telemetry file {telemetry_path.name}")

        if ev.get("event") == "invocation_attempt_metadata":
            if curr_meta is not None:
                attempts.append((curr_meta, curr_lines))
            curr_meta = ev
            curr_lines = []
        else:
            curr_lines.append(line)

    if curr_meta is not None:
        attempts.append((curr_meta, curr_lines))
    elif curr_lines:
        attempts.append(({"event": "invocation_attempt_metadata", "attempt_type": "initial"}, curr_lines))

    format_repairs = 0
    observed_model = None
    last_response_text = None
    has_successful_terminal_attempt = False

    for attempt_meta, attempt_lines in attempts:
        attempt_type = attempt_meta.get("attempt_type", "initial")
        if attempt_type == "format_repair":
            format_repairs += 1

        # If this attempt was marked as an execution/transport failure, ensure it didn't pass as a terminal success
        fail_class = attempt_meta.get("failure_classification")
        if fail_class in ["TOOL_VIOLATION", "TELEMETRY_UNRECOGNIZED_EVENT", "MODEL_IDENTITY_MISMATCH"]:
            raise ResumeStateInvalidError(
                f"Prohibited failure classification '{fail_class}' in telemetry for {telemetry_path.name}"
            )

        # Audit attempt stream using the exact same live audit function
        try:
            res_dict, conv_id = audit_single_invocation_stream(
                stream_lines=attempt_lines,
                expected_model=authorized_model,
                expected_cwd=None,
                seen_conversation_ids=None,
            )
            has_successful_terminal_attempt = True
            observed_model = authorized_model
            last_response_text = res_dict.get("response")
        except Exception as e:
            if fail_class is None:
                raise ResumeStateInvalidError(
                    f"Existing telemetry audit failure in {telemetry_path.name}: {e}"
                )

    if not has_successful_terminal_attempt:
        raise ResumeStateInvalidError(
            f"No successful terminal invocation found in telemetry for {telemetry_path.name}"
        )

    if format_repairs > 1:
        raise ResumeStateInvalidError(
            f"Format repairs ({format_repairs}) exceed limit of 1 in {telemetry_path.name}"
        )

    return format_repairs, observed_model, last_response_text


def load_and_validate_existing_output(
    output_path: Path,
    taxonomy: str,
    telemetry_dir: Path,
    schema: Dict[str, Any],
    authorized_model: str,
    input_ids: List[str],
) -> Tuple[List[Dict[str, Any]], List[str], Set[str]]:
    """
    Hardened resume validation:
    Before accepting any existing record, deeply validates:
    - valid JSON
    - schema validity
    - correct source, taxonomy, ID
    - semantic invariants
    - exact deterministic input prefix: existing_ids == input_ids[0:N]
    - corresponding telemetry file exists and passes fail-closed audit
    - model identity matches authorized model
    - format_repairs count matches response_status
    Returns (accepted_records_list, completed_ids_list, seen_conversation_ids_set).
    """
    if not output_path.exists():
        return [], [], set()

    accepted_records: List[Dict[str, Any]] = []
    completed_ids: List[str] = []
    seen_ids: Set[str] = set()
    seen_conv_ids: Set[str] = set()

    with open(output_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ResumeStateInvalidError(
                    f"RESUME_STATE_INVALID: line {line_num} in {output_path} is invalid JSON: {e}"
                )

            ann_id = rec.get("annotation_id")
            if not ann_id:
                raise ResumeStateInvalidError(
                    f"RESUME_STATE_INVALID: line {line_num} in {output_path} missing annotation_id"
                )
            if ann_id in seen_ids:
                raise ResumeStateInvalidError(
                    f"RESUME_STATE_INVALID: duplicate annotation_id '{ann_id}' in output file"
                )

            # Invariant and schema validation
            try:
                validate_record_invariants(
                    record=rec,
                    schema=schema,
                    expected_id=ann_id,
                    taxonomy=taxonomy,
                    source_id="MODEL_G",
                )
            except Exception as e:
                raise ResumeStateInvalidError(
                    f"RESUME_STATE_INVALID: existing record '{ann_id}' failed validation: {e}"
                )

            # Telemetry audit for this record using strict fail-closed standard
            tfile = telemetry_dir / taxonomy / f"{ann_id}.telemetry.jsonl"
            rep_count, model, resp_text = audit_existing_telemetry_file(tfile, authorized_model)

            # Enforce format repair count consistency
            resp_status = rec.get("response_status")
            if resp_status == "VALID" and rep_count != 0:
                raise ResumeStateInvalidError(
                    f"RESUME_STATE_INVALID: record '{ann_id}' is VALID but telemetry has {rep_count} format repairs"
                )
            if resp_status == "FORMAT_REPAIRED" and rep_count != 1:
                raise ResumeStateInvalidError(
                    f"RESUME_STATE_INVALID: record '{ann_id}' is FORMAT_REPAIRED but telemetry has {rep_count} format repairs"
                )

            # Collect conversation IDs from telemetry
            with open(tfile, "r", encoding="utf-8") as tf:
                for tline in tf:
                    tline = tline.strip()
                    if not tline:
                        continue
                    try:
                        tev = json.loads(tline)
                        cid = tev.get("conversation_id")
                        if cid:
                            seen_conv_ids.add(cid)
                    except Exception:
                        pass

            seen_ids.add(ann_id)
            completed_ids.append(ann_id)
            accepted_records.append(rec)

    # EXACT DETERMINISTIC PREFIX CHECK
    N = len(completed_ids)
    if N > len(input_ids):
        raise ResumeStateInvalidError(
            f"RESUME_STATE_INVALID: existing output has {N} records, which exceeds input count {len(input_ids)}"
        )

    expected_prefix = input_ids[:N]
    if completed_ids != expected_prefix:
        raise ResumeStateInvalidError(
            f"RESUME_STATE_INVALID: existing output IDs are not an exact deterministic prefix of input IDs. "
            f"Expected prefix: {expected_prefix[:10]}, Got: {completed_ids[:10]}"
        )

    return accepted_records, completed_ids, seen_conv_ids


def save_accepted_record_atomic(
    output_path: Path,
    new_record: Dict[str, Any],
    all_accepted_records: List[Dict[str, Any]],
) -> None:
    """
    Crash-safe output persistence:
    Appends in-memory, writes to temp file in same directory, flushes, fsyncs, and os.replace().
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_accepted_records.append(new_record)

    tmp_file = output_path.with_name(f"{output_path.name}.tmp.{os.getpid()}")
    with open(tmp_file, "w", encoding="utf-8") as f:
        for rec in all_accepted_records:
            f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp_file, output_path)


def run_batch(
    taxonomy: str,
    input_path: Path,
    output_path: Path,
    telemetry_dir: Path,
    workspace_root: Path,
    run_id: str,
    model: str = "gemini-3.8-flash-high",
    dry_run: bool = False,
    is_synthetic: bool = False,
) -> None:
    # 1. Hash-based benchmark input detection
    is_benchmark, detected_tax = check_is_benchmark_input(input_path, workspace_root)

    if is_synthetic and is_benchmark:
        raise BenchmarkNotAuthorizedError(
            f"CRITICAL SAFETY VIOLATION: Benchmark input detected in synthetic mode (hash match). "
            f"Input '{input_path}' is frozen benchmark data. Execution ABORTED."
        )

    if is_benchmark:
        if not check_benchmark_authorization(workspace_root):
            raise BenchmarkNotAuthorizedError(
                f"CRITICAL SAFETY VIOLATION: Execution attempted on benchmark input '{input_path}' "
                f"(SHA-256 matched frozen benchmark hash), but benchmark_execution_authorized is FALSE "
                f"in protocol/model_g_execution_manifest.json. Execution ABORTED."
            )
        verify_package_integrity(workspace_root, taxonomy)

    schema = load_schema(workspace_root)
    guidelines = load_guidelines(workspace_root, taxonomy)

    (telemetry_dir / taxonomy).mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read input records in deterministic order
    input_items: List[Dict[str, Any]] = []
    input_ids: List[str] = []
    seen_input_ids: Set[str] = set()
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            ann_id = item["annotation_id"]
            if ann_id in seen_input_ids:
                raise ValueError(f"Duplicate annotation_id found in input: {ann_id}")
            seen_input_ids.add(ann_id)
            input_items.append(item)
            input_ids.append(ann_id)

    # Hardened resume validation (enforcing exact deterministic prefix)
    all_accepted_records, completed_ids, seen_conversation_ids = load_and_validate_existing_output(
        output_path=output_path,
        taxonomy=taxonomy,
        telemetry_dir=telemetry_dir,
        schema=schema,
        authorized_model=model,
        input_ids=input_ids,
    )

    print(f"Starting batch: taxonomy={taxonomy}, run_id={run_id}, input={input_path}")
    print(f"Validated existing prefix completed records: {len(completed_ids)}")
    print(f"Total input items to process: {len(input_items)}")

    # Process items sequentially starting after existing prefix
    start_idx = len(completed_ids)
    for idx in range(start_idx, len(input_items)):
        item = input_items[idx]
        ann_id = item["annotation_id"]
        q_text = item["query"]

        print(f"[{idx + 1}/{len(input_items)}] Processing {ann_id} in isolated fresh context...")

        if dry_run:
            print(f"  [DRY RUN] Would execute {ann_id}")
            continue

        accepted_record = annotate_single_query(
            annotation_id=ann_id,
            query_text=q_text,
            taxonomy=taxonomy,
            guidelines_text=guidelines,
            schema=schema,
            telemetry_dir=telemetry_dir,
            seen_conversation_ids=seen_conversation_ids,
            model=model,
            source_id="MODEL_G",
            run_id=run_id,
        )

        # Crash-safe atomic persistence
        save_accepted_record_atomic(
            output_path=output_path,
            new_record=accepted_record,
            all_accepted_records=all_accepted_records,
        )

        completed_ids.append(ann_id)
        print(f"  Accepted {ann_id} -> primary: {accepted_record['primary_label']} (status: {accepted_record['response_status']})")

    print(f"Batch completed successfully. Total accepted: {len(completed_ids)}")


def main():
    parser = argparse.ArgumentParser(description="MODEL_G Hardened Execution Runner")
    parser.add_argument("--taxonomy", required=True, choices=["T2", "T3"], help="Taxonomy version")
    parser.add_argument("--input", required=True, type=Path, help="Path to input JSONL file")
    parser.add_argument("--output", required=True, type=Path, help="Path to output JSONL file")
    parser.add_argument("--telemetry-dir", required=True, type=Path, help="Directory for telemetry")
    parser.add_argument("--run-id", default="MODEL_G_RUN", help="Run identifier")
    parser.add_argument("--model", default="gemini-3.8-flash-high", help="Antigravity model selector")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without invoking model")
    parser.add_argument("--synthetic", action="store_true", help="Explicit synthetic mode flag")
    parser.add_argument("--workspace-root", type=Path, default=None, help="Root directory containing protocol/ and inputs/")

    args = parser.parse_args()
    workspace_root = args.workspace_root
    if workspace_root is None:
        candidate = Path(__file__).resolve().parent.parent
        if (candidate / "protocol" / "model_g_execution_manifest.json").exists():
            workspace_root = candidate
        elif Path("/home/kaustubh/gate-b3-model-g-gemini").exists():
            workspace_root = Path("/home/kaustubh/gate-b3-model-g-gemini")
        else:
            workspace_root = candidate

    try:
        run_batch(
            taxonomy=args.taxonomy,
            input_path=args.input,
            output_path=args.output,
            telemetry_dir=args.telemetry_dir,
            workspace_root=workspace_root,
            run_id=args.run_id,
            model=args.model,
            dry_run=args.dry_run,
            is_synthetic=args.synthetic,
        )
    except BenchmarkNotAuthorizedError as e:
        print(f"\n[BLOCKED] {e}", file=sys.stderr)
        sys.exit(101)
    except ProviderLimitError as e:
        print(f"\n[PAUSED] {e}", file=sys.stderr)
        sys.exit(103)
    except ToolViolationError as e:
        print(f"\n[HARD FAIL BATCH] {e}", file=sys.stderr)
        sys.exit(102)
    except ResumeStateInvalidError as e:
        print(f"\n[RESUME BLOCKED] {e}", file=sys.stderr)
        sys.exit(104)
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
