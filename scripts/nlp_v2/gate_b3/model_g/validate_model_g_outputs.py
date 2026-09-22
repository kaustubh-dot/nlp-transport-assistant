#!/usr/bin/env python3
"""
scripts/validate_model_g_outputs.py

Gate B.3 MODEL_G Hardened Output Validator.
Enforces:
- Exact record count (350 for full benchmark)
- Unique IDs (zero duplicates)
- Expected ID set derived from frozen input file (hash-verified) or explicit synthetic set
- Canonical JSON schema validity
- Model record invariants (MODEL_G, model, not_applicable, null)
- Semantic class invariants matching central lock validator:
  * primary_label != null -> primary_label in acceptable_labels
  * primary_label == null -> clarification_required = true
  * clarification_required = false -> clarification_reasons = []
  * clarification_required = true -> clarification_reasons non-empty
  * canonical clarification vocabulary
- Complete fail-closed telemetry audit per record (taxonomy-scoped):
  * authorized model identity observed (rejects observed_model == None or mismatch)
  * valid init event observed
  * terminal SUCCESS result observed
  * conversation ID present
  * zero prohibited tools
  * zero unknown / malformed telemetry
- Strict format-repair count enforcement:
  * response_status == VALID -> format_repairs == 0
  * response_status == FORMAT_REPAIRED -> format_repairs == 1
  * format_repairs > 1 -> FAILED
- Traces accepted output record to successful result response in telemetry
- Enforces conversation ID uniqueness across all accepted items (and cross-taxonomy)
"""

import argparse
import hashlib
import json
import re
import sys
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


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def derive_expected_ids_from_input(input_path: Path, manifest_path: Path, taxonomy: str) -> List[str]:
    """
    Derives expected IDs directly from frozen input file without printing query text.
    Verifies input file hash against manifest.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    manifest = load_json(manifest_path)

    expected_input_hash = manifest.get("input_sha256", {}).get(input_path.name)
    if not expected_input_hash:
        expected_input_hash = manifest.get("input_sha256", {}).get(f"model_g_{taxonomy.lower()}_input.jsonl")

    if expected_input_hash:
        act_hash = compute_sha256(input_path)
        if act_hash != expected_input_hash:
            raise ValueError(f"Input file hash drift for {input_path.name}: expected {expected_input_hash}, got {act_hash}")

    expected_ids = []
    seen = set()
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            ann_id = item.get("annotation_id")
            if not ann_id:
                raise ValueError(f"Input line {line_num} missing annotation_id")
            if ann_id in seen:
                raise ValueError(f"Duplicate annotation_id in input: {ann_id}")
            seen.add(ann_id)
            expected_ids.append(ann_id)

    return expected_ids


def audit_telemetry_file(
    telemetry_path: Path,
    authorized_model: str = "gemini-3.8-flash-high",
) -> Tuple[int, int, int, int, int, Optional[str], Optional[str], Optional[str], List[str]]:
    """
    Fail-closed audit of per-record telemetry file.
    Returns:
      (tool_calls, web_calls, file_reads, command_executions, format_repairs, observed_model, conv_id, accepted_response_text, telemetry_errors)
    """
    if not telemetry_path.exists():
        return 0, 0, 0, 0, 0, None, None, None, [f"Missing telemetry file: {telemetry_path}"]

    lines = []
    telemetry_errors = []
    with open(telemetry_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                lines.append(ev)
            except json.JSONDecodeError:
                telemetry_errors.append(f"Malformed non-JSON line at line {line_num} in {telemetry_path.name}")

    if not lines:
        telemetry_errors.append(f"Empty telemetry file: {telemetry_path.name}")
        return 0, 0, 0, 0, 0, None, None, None, telemetry_errors

    # Split into attempts
    attempts: List[Tuple[Dict[str, Any], List[Dict[str, Any]]]] = []
    curr_meta = None
    curr_events = []

    for ev in lines:
        if not isinstance(ev, dict):
            telemetry_errors.append(f"Non-dict JSON object in {telemetry_path.name}")
            continue

        if ev.get("event") == "invocation_attempt_metadata":
            if curr_meta is not None:
                attempts.append((curr_meta, curr_events))
            curr_meta = ev
            curr_events = []
        else:
            curr_events.append(ev)

    if curr_meta is not None:
        attempts.append((curr_meta, curr_events))
    elif curr_events:
        attempts.append(({"event": "invocation_attempt_metadata", "attempt_type": "initial"}, curr_events))

    total_tool_calls = 0
    total_web_calls = 0
    total_file_reads = 0
    total_commands = 0
    format_repairs = 0
    observed_model = None
    terminal_conv_id = None
    last_successful_response_text = None
    terminal_success_found = False

    for attempt_meta, attempt_events in attempts:
        attempt_type = attempt_meta.get("attempt_type", "initial")
        if attempt_type == "format_repair":
            format_repairs += 1

        fail_class = attempt_meta.get("failure_classification")
        if fail_class in ["TOOL_VIOLATION", "TELEMETRY_UNRECOGNIZED_EVENT", "MODEL_IDENTITY_MISMATCH"]:
            telemetry_errors.append(f"Prohibited failure classification '{fail_class}' recorded in {telemetry_path.name}")

        init_count = 0
        result_count = 0
        attempt_conv_id = None

        for ev in attempt_events:
            ename = ev.get("event")
            if ename not in BENIGN_EVENT_TYPES:
                telemetry_errors.append(f"Unrecognized event '{ename}' in {telemetry_path.name}")
                continue

            if ename == "init":
                init_count += 1
                init_data = ev.get("init", {})
                m = init_data.get("model") or ev.get("model")
                if m:
                    observed_model = m
                    if m != authorized_model:
                        telemetry_errors.append(f"Model identity mismatch: expected '{authorized_model}', got '{m}'")
                cid = ev.get("conversation_id")
                if cid:
                    attempt_conv_id = cid

            elif ename == "step_update":
                su = ev.get("step_update", {})
                st = su.get("step_type", "")
                if st not in BENIGN_STEP_TYPES:
                    telemetry_errors.append(f"Unexpected step_type '{st}' in {telemetry_path.name}")
                    if any(k in st.lower() for k in ["tool", "command", "browser", "exec"]):
                        total_tool_calls += 1

                if "tool_calls" in su and su["tool_calls"]:
                    total_tool_calls += len(su["tool_calls"])
                    for tc in su["tool_calls"]:
                        name = tc.get("name", "").lower()
                        if any(k in name for k in ["web", "search", "url", "browser"]):
                            total_web_calls += 1
                        if any(k in name for k in ["file", "read", "grep", "dir"]):
                            total_file_reads += 1
                        if any(k in name for k in ["command", "bash", "exec"]):
                            total_commands += 1
                    telemetry_errors.append(f"Prohibited tool_calls observed in {telemetry_path.name}: {su['tool_calls']}")

            elif ename == "result":
                result_count += 1
                res = ev.get("result", {})
                da = res.get("denied_actions") or ev.get("denied_actions")
                if da:
                    total_tool_calls += len(da)
                    for item in da:
                        act = item.get("action", "").lower()
                        disp = item.get("display_name", "").lower()
                        if any(k in act for k in ["web", "search", "browser"]):
                            total_web_calls += 1
                        if any(k in act for k in ["file", "read"]):
                            total_file_reads += 1
                        if any(k in act for k in ["command"]) or "runcommand" in disp:
                            total_commands += 1
                    telemetry_errors.append(f"Prohibited denied_actions observed in {telemetry_path.name}: {da}")

                if res.get("status") == "SUCCESS":
                    terminal_success_found = True
                    last_successful_response_text = res.get("response")
                    terminal_conv_id = attempt_conv_id

        # If this attempt was marked as successful or expected to succeed, check counts
        if fail_class is None:
            if init_count == 0:
                telemetry_errors.append(f"Attempt in {telemetry_path.name} lacks init event (TELEMETRY_MISSING_INIT)")
            elif init_count > 1:
                telemetry_errors.append(f"Attempt in {telemetry_path.name} has multiple init events ({init_count})")

            if result_count == 0:
                telemetry_errors.append(f"Attempt in {telemetry_path.name} lacks result event (TELEMETRY_MISSING_RESULT)")
            elif result_count > 1:
                telemetry_errors.append(f"Attempt in {telemetry_path.name} has multiple result events ({result_count})")

    if not terminal_success_found:
        telemetry_errors.append(f"No terminal SUCCESS result found in {telemetry_path.name}")

    if observed_model is None:
        telemetry_errors.append(f"No model identity observed in telemetry for {telemetry_path.name}")

    if terminal_conv_id is None:
        telemetry_errors.append(f"No conversation ID observed for successful invocation in {telemetry_path.name}")

    return (
        total_tool_calls,
        total_web_calls,
        total_file_reads,
        total_commands,
        format_repairs,
        observed_model,
        terminal_conv_id,
        last_successful_response_text,
        telemetry_errors,
    )


def extract_json_relaxed(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    try:
        return json.loads(s)
    except Exception:
        pass
    fb = s.find("{")
    lb = s.rfind("}")
    if fb != -1 and lb != -1 and lb > fb:
        try:
            return json.loads(s[fb : lb + 1])
        except Exception:
            pass
    return None


def validate_outputs(
    output_file: Path,
    taxonomy: str,
    telemetry_dir: Path,
    workspace_root: Path,
    expected_count: int = 350,
    expected_ids: Optional[List[str]] = None,
    authorized_model: str = "gemini-3.8-flash-high",
) -> Dict[str, Any]:
    schema_path = workspace_root / "protocol" / "annotation_output_schema.json"
    schema = load_json(schema_path)

    allowed_classes = set(TAXONOMY_CLASSES[taxonomy])

    if not output_file.exists():
        raise FileNotFoundError(f"Output file does not exist: {output_file}")

    records: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    duplicate_ids: List[str] = []

    with open(output_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Line {line_num} is not valid JSON: {e}")
            ann_id = rec.get("annotation_id")
            if ann_id in seen_ids:
                duplicate_ids.append(ann_id)
            seen_ids.add(ann_id)
            records.append(rec)

    total_records = len(records)
    unique_ids_count = len(seen_ids)

    errors: List[str] = []

    # 1. Exact record count & uniqueness
    if total_records != expected_count:
        errors.append(f"Record count mismatch: got {total_records}, expected {expected_count}")
    if unique_ids_count != expected_count:
        errors.append(f"Unique ID count mismatch: got {unique_ids_count}, expected {expected_count}")
    if duplicate_ids:
        errors.append(f"Duplicate IDs encountered: {duplicate_ids[:10]}")

    # 2. Expected ID set
    if expected_ids is not None:
        expected_set = set(expected_ids)
        missing_ids = expected_set - seen_ids
        unexpected_ids = seen_ids - expected_set
        if missing_ids:
            errors.append(f"Missing expected IDs ({len(missing_ids)}): {list(missing_ids)[:10]}")
        if unexpected_ids:
            errors.append(f"Unexpected IDs ({len(unexpected_ids)}): {list(unexpected_ids)[:10]}")

    # 3. Per-record schema, invariants, telemetry audit & conversation ID uniqueness
    total_tool_calls = 0
    total_web_calls = 0
    total_file_reads = 0
    total_commands = 0
    total_format_repairs = 0
    valid_status_count = 0
    repaired_status_count = 0
    seen_conversation_ids: Set[str] = set()

    for idx, rec in enumerate(records, start=1):
        ann_id = rec.get("annotation_id", f"item_{idx}")

        # JSON schema validation
        try:
            jsonschema.validate(instance=rec, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"[{ann_id}] Schema validation failed: {e.message}")

        # Fixed model metadata checks
        if rec.get("source_id") != "MODEL_G":
            errors.append(f"[{ann_id}] Invalid source_id: {rec.get('source_id')}")
        if rec.get("source_type") != "model":
            errors.append(f"[{ann_id}] Invalid source_type: {rec.get('source_type')}")
        if rec.get("taxonomy_version") != taxonomy:
            errors.append(f"[{ann_id}] Invalid taxonomy_version: {rec.get('taxonomy_version')}")
        if rec.get("recognized_from_prior_work") != "not_applicable":
            errors.append(f"[{ann_id}] recognized_from_prior_work != 'not_applicable'")
        if rec.get("active_time_seconds") is not None:
            errors.append(f"[{ann_id}] active_time_seconds must be null")
        if rec.get("rule_difficulty") != "not_applicable":
            errors.append(f"[{ann_id}] rule_difficulty != 'not_applicable'")

        resp_status = rec.get("response_status")
        if resp_status == "VALID":
            valid_status_count += 1
        elif resp_status == "FORMAT_REPAIRED":
            repaired_status_count += 1
            total_format_repairs += 1
        else:
            errors.append(f"[{ann_id}] Invalid response_status: {resp_status}")

        # Semantic class invariants
        primary = rec.get("primary_label")
        acc = rec.get("acceptable_labels", [])
        if not acc:
            errors.append(f"[{ann_id}] acceptable_labels is empty")
        for lab in acc:
            if lab not in allowed_classes:
                errors.append(f"[{ann_id}] Unknown class '{lab}' in acceptable_labels")

        if primary is not None:
            if primary not in allowed_classes:
                errors.append(f"[{ann_id}] Unknown primary_label '{primary}'")
            if primary not in acc:
                errors.append(f"[{ann_id}] primary_label '{primary}' not in acceptable_labels")

        # Clarification invariants matching central lock validator
        clar_req = rec.get("clarification_required")
        clar_reasons = rec.get("clarification_reasons", [])
        for r in clar_reasons:
            if r not in CLARIFICATION_REASONS:
                errors.append(f"[{ann_id}] Unknown clarification_reason: '{r}'")

        if primary is None:
            if clar_req is not True:
                errors.append(f"[{ann_id}] clarification_required must be True when primary_label is null")
            if not any(r in ["intent_ambiguity", "uninterpretable"] for r in clar_reasons):
                errors.append(f"[{ann_id}] clarification_reasons missing 'intent_ambiguity' or 'uninterpretable'")

        if clar_req is False and clar_reasons != []:
            errors.append(f"[{ann_id}] clarification_reasons must be [] when clarification_required is False, got: {clar_reasons}")

        if clar_req is True and not clar_reasons:
            errors.append(f"[{ann_id}] clarification_reasons empty but clarification_required is True")

        # Telemetry audit for this record (taxonomy-scoped)
        tfile = telemetry_dir / taxonomy / f"{ann_id}.telemetry.jsonl"
        tc, wc, fr, ce, rep, observed_m, cid, resp_text, tel_errs = audit_telemetry_file(tfile, authorized_model)
        total_tool_calls += tc
        total_web_calls += wc
        total_file_reads += fr
        total_commands += ce

        if tel_errs:
            for terr in tel_errs:
                errors.append(f"[{ann_id}] Telemetry error: {terr}")
        if tc > 0 or wc > 0 or fr > 0 or ce > 0:
            errors.append(
                f"[{ann_id}] Prohibited tools observed in telemetry: "
                f"tools={tc}, web={wc}, file_reads={fr}, commands={ce}"
            )
        if observed_m != authorized_model:
            errors.append(f"[{ann_id}] Telemetry model mismatch: expected '{authorized_model}', got '{observed_m}'")

        # Conversation ID uniqueness enforcement
        if cid:
            if cid in seen_conversation_ids:
                errors.append(f"[{ann_id}] Duplicate conversation_id '{cid}' observed across accepted items")
            seen_conversation_ids.add(cid)

        # Enforce format repair count consistency with response_status
        if rep > 1:
            errors.append(f"[{ann_id}] Format repairs ({rep}) exceed frozen limit of 1")
        if resp_status == "VALID" and rep != 0:
            errors.append(f"[{ann_id}] response_status is VALID but telemetry recorded {rep} format repairs")
        if resp_status == "FORMAT_REPAIRED" and rep != 1:
            errors.append(f"[{ann_id}] response_status is FORMAT_REPAIRED but telemetry recorded {rep} format repairs")

        # Tracing accepted JSON record to telemetry response text
        if resp_text:
            parsed_tel = extract_json_relaxed(resp_text)
            if parsed_tel:
                if parsed_tel.get("primary_label") != primary:
                    errors.append(
                        f"[{ann_id}] primary_label mismatch between output ({primary}) and telemetry ({parsed_tel.get('primary_label')})"
                    )
                if sorted(parsed_tel.get("acceptable_labels") or []) != sorted(acc):
                    errors.append(f"[{ann_id}] acceptable_labels mismatch between output and telemetry")
            else:
                errors.append(f"[{ann_id}] Telemetry response could not be parsed to verify accepted record")
        else:
            errors.append(f"[{ann_id}] Missing telemetry response text to trace accepted record")

    summary = {
        "taxonomy": taxonomy,
        "output_file": str(output_file),
        "total_records": total_records,
        "unique_ids": unique_ids_count,
        "expected_count": expected_count,
        "valid_count": valid_status_count,
        "repaired_count": repaired_status_count,
        "total_format_repairs": total_format_repairs,
        "tool_calls_observed": total_tool_calls,
        "web_calls_observed": total_web_calls,
        "file_reads_observed": total_file_reads,
        "command_executions_observed": total_commands,
        "unique_conversation_ids": len(seen_conversation_ids),
        "errors_count": len(errors),
        "errors": errors,
        "passed": len(errors) == 0,
    }

    return summary


def validate_cross_taxonomy_uniqueness(telemetry_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validates that conversation IDs across T2 and T3 are completely disjoint.
    """
    seen_cids: Dict[str, str] = {}
    duplicates: List[str] = []

    for tax in ["T2", "T3"]:
        tax_dir = telemetry_dir / tax
        if not tax_dir.exists():
            continue
        for tfile in tax_dir.glob("*.telemetry.jsonl"):
            with open(tfile, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        ev = json.loads(line)
                        if ev.get("event") == "init":
                            cid = ev.get("conversation_id")
                            if cid:
                                if cid in seen_cids:
                                    duplicates.append(f"Conversation ID '{cid}' in {tax}/{tfile.name} previously seen in {seen_cids[cid]}")
                                else:
                                    seen_cids[cid] = f"{tax}/{tfile.name}"
                    except Exception:
                        pass

    return len(duplicates) == 0, duplicates


def main():
    parser = argparse.ArgumentParser(description="Validate MODEL_G outputs and telemetry")
    parser.add_argument("--output", required=True, type=Path, help="Path to output JSONL file")
    parser.add_argument("--taxonomy", required=True, choices=["T2", "T3"], help="Taxonomy version")
    parser.add_argument("--telemetry-dir", required=True, type=Path, help="Directory containing telemetry")
    parser.add_argument("--expected-count", type=int, default=350, help="Expected record count (default: 350)")
    parser.add_argument("--input-file", type=Path, default=None, help="Frozen input file to derive expected IDs")
    parser.add_argument("--expected-id-range", type=str, default=None, help="Optional range e.g. ANN_B2_001..ANN_B2_350")
    parser.add_argument("--expected-ids", nargs="*", default=None, help="Explicit list of expected IDs")
    parser.add_argument("--model", default="gemini-3.8-flash-high", help="Authorized model selector")
    parser.add_argument("--check-cross-taxonomy-uniqueness", action="store_true", help="Check conversation ID uniqueness across T2+T3")
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

    expected_ids = None
    if args.input_file:
        manifest_path = workspace_root / "protocol" / "model_g_execution_manifest.json"
        expected_ids = derive_expected_ids_from_input(args.input_file, manifest_path, args.taxonomy)
    elif args.expected_ids:
        expected_ids = args.expected_ids
    elif args.expected_id_range:
        m = re.match(r"^ANN_B2_(\d+)\.\.ANN_B2_(\d+)$", args.expected_id_range)
        if m:
            start_i = int(m.group(1))
            end_i = int(m.group(2))
            expected_ids = [f"ANN_B2_{i:03d}" for i in range(start_i, end_i + 1)]
    elif args.expected_count == 350:
        input_candidate = workspace_root / "inputs" / f"model_g_{args.taxonomy.lower()}_input.jsonl"
        manifest_path = workspace_root / "protocol" / "model_g_execution_manifest.json"
        if input_candidate.exists() and manifest_path.exists():
            expected_ids = derive_expected_ids_from_input(input_candidate, manifest_path, args.taxonomy)

    summary = validate_outputs(
        output_file=args.output,
        taxonomy=args.taxonomy,
        telemetry_dir=args.telemetry_dir,
        workspace_root=workspace_root,
        expected_count=args.expected_count,
        expected_ids=expected_ids,
        authorized_model=args.model,
    )

    if args.check_cross_taxonomy_uniqueness:
        cross_ok, cross_dups = validate_cross_taxonomy_uniqueness(args.telemetry_dir)
        if not cross_ok:
            for d in cross_dups:
                summary["errors"].append(f"Cross-taxonomy duplicate: {d}")
            summary["passed"] = False
            summary["errors_count"] = len(summary["errors"])

    print("==================================================")
    print("MODEL_G OUTPUT VALIDATION SUMMARY")
    print("==================================================")
    print(f"Taxonomy:                {summary['taxonomy']}")
    print(f"Output File:             {summary['output_file']}")
    print(f"Total Records:           {summary['total_records']}")
    print(f"Unique IDs:              {summary['unique_ids']} (expected: {summary['expected_count']})")
    print(f"Status VALID:            {summary['valid_count']}")
    print(f"Status REPAIRED:         {summary['repaired_count']}")
    print(f"Tool Calls Observed:     {summary['tool_calls_observed']}")
    print(f"Web Calls Observed:      {summary['web_calls_observed']}")
    print(f"File Reads Observed:     {summary['file_reads_observed']}")
    print(f"Commands Observed:       {summary['command_executions_observed']}")
    print(f"Unique Conversation IDs: {summary['unique_conversation_ids']}")
    print(f"Validation Errors:       {summary['errors_count']}")

    if summary["errors"]:
        print("\nERRORS:")
        for err in summary["errors"][:20]:
            print(f"  - {err}")
        if len(summary["errors"]) > 20:
            print(f"  ... and {len(summary['errors']) - 20} more errors")
        print("\nRESULT: FAILED")
        sys.exit(1)
    else:
        print("\nRESULT: PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
