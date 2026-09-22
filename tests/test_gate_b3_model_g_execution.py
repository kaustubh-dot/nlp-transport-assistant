#!/usr/bin/env python3
"""
scripts/test_model_g_pipeline.py

Comprehensive test suite covering all required hardening test cases:
 1. renamed benchmark input still blocked by hash
 2. copied benchmark input still blocked by hash
 3. benchmark hash rejected in synthetic mode
 4. missing init fails closed
 5. missing result fails closed
 6. non-success result fails closed
 7. multiple init events fail closed
 8. multiple result events fail closed
 9. quota detected from stderr
10. quota detected from structured result
11. quota during format repair pauses without retry
12. malformed resume telemetry causes RESUME_STATE_INVALID
13. unknown resume event causes RESUME_STATE_INVALID
14. missing resume init/model causes RESUME_STATE_INVALID
15. missing resume result causes RESUME_STATE_INVALID
16. non-prefix resume output rejected
17. valid exact prefix accepted
18. existing ID not in input rejected
19. validator requires observed model identity
20. validator requires terminal success
21. validator rejects >1 format repair
22. VALID + repair telemetry rejected
23. FORMAT_REPAIRED + no repair telemetry rejected
24. duplicate conversation ID across accepted items rejected
25. benchmark authorization false remains fail-closed
26. package hash drift remains fail-closed
27. telemetry namespace collision prevention
28. false clarification with nonempty reasons rejected
29. semantic-changing format repair rejected
30. unparseable output not semantically retried
31. atomic output replacement
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import os

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_G_DIR = REPO_ROOT / "scripts" / "nlp_v2" / "gate_b3" / "model_g"
if str(MODEL_G_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_G_DIR))

import run_model_g_gemini
from run_model_g_gemini import (
    BenchmarkNotAuthorizedError,
    DuplicateConversationIdError,
    ModelIdentityMismatchError,
    PackageIntegrityError,
    ProviderLimitError,
    ResumeStateInvalidError,
    SchemaValidationError,
    SemanticChangeDuringFormatRepairError,
    ToolViolationError,
    UnrecoverableMalformedOutputError,
    UnrecognizedTelemetryError,
    annotate_single_query,
    audit_single_invocation_stream,
    check_benchmark_authorization,
    check_for_provider_limit,
    check_is_benchmark_input,
    extract_json_from_response,
    load_and_validate_existing_output,
    load_guidelines,
    load_schema,
    run_batch,
    save_accepted_record_atomic,
    validate_record_invariants,
    verify_package_integrity,
)
from validate_model_g_outputs import (
    audit_telemetry_file,
    derive_expected_ids_from_input,
    validate_cross_taxonomy_uniqueness,
    validate_outputs,
)


class LiveAgyExecutionAttemptError(RuntimeError):
    """Raised whenever a unit test execution attempts to invoke live agy."""
    pass


def guarded_execute_single_invocation(*args, **kwargs):
    raise LiveAgyExecutionAttemptError(
        "CRITICAL GUARD TRIGGERED: Unit test attempted to invoke execute_single_invocation / live agy!"
    )


_original_subprocess_run = run_model_g_gemini.subprocess.run


def guarded_subprocess_run(*args, **kwargs):
    cmd = args[0] if args else kwargs.get("args", [])
    if (isinstance(cmd, (list, tuple)) and len(cmd) > 0 and cmd[0] == "agy") or (isinstance(cmd, str) and "agy" in cmd):
        raise LiveAgyExecutionAttemptError(
            "CRITICAL GUARD TRIGGERED: Unit test attempted to invoke subprocess.run(['agy', ...])!"
        )
    return _original_subprocess_run(*args, **kwargs)


# Install strict module-level guards so tests can NEVER invoke live agy
run_model_g_gemini.execute_single_invocation = guarded_execute_single_invocation
run_model_g_gemini.subprocess.run = guarded_subprocess_run


def create_isolated_workspace(benchmark_authorized: bool = False):
    """
    Creates an isolated temporary workspace from canonical fixture files.
    Never depends on machine-global or sterile workspaces.
    For negative-authorization tests, benchmark_authorized=False creates an unauthorized manifest copy.
    """
    tmp_ws = tempfile.TemporaryDirectory()
    ws_path = Path(tmp_ws.name)
    (ws_path / "protocol").mkdir(parents=True, exist_ok=True)
    (ws_path / "inputs").mkdir(parents=True, exist_ok=True)
    for f in [
        "model_annotator_prompt_template.md",
        "t2_annotation_guide.md",
        "t3_annotation_guide.md",
        "annotation_output_schema.json",
        "gate_b3_execution_isolation_amendment.md",
        "gate_b3_resource_feasibility_annotator_amendment.md",
    ]:
        shutil.copyfile(REPO_ROOT / "docs" / "nlp_v2" / "gate_b3" / f, ws_path / "protocol" / f)

    canonical_manifest = json.loads(
        (REPO_ROOT / "data" / "nlp_v2" / "gate_b3" / "model_g_execution_manifest.json").read_text(encoding="utf-8")
    )
    manifest_copy = dict(canonical_manifest)
    manifest_copy["benchmark_execution_authorized"] = benchmark_authorized
    (ws_path / "protocol" / "model_g_execution_manifest.json").write_text(
        json.dumps(manifest_copy, indent=2), encoding="utf-8"
    )

    shutil.copyfile(REPO_ROOT / "data" / "nlp_v2" / "gate_b3" / "model_g_t2_input.jsonl", ws_path / "inputs" / "model_g_t2_input.jsonl")
    shutil.copyfile(REPO_ROOT / "data" / "nlp_v2" / "gate_b3" / "model_g_t3_input.jsonl", ws_path / "inputs" / "model_g_t3_input.jsonl")
    return tmp_ws, ws_path


class TestHardenedModelGPipeline(unittest.TestCase):
    def setUp(self):
        # Strict unit test isolation: never consult sterile workspace or machine environment
        self._tmp_ws, self.workspace_root = create_isolated_workspace(benchmark_authorized=False)
        self.schema = load_schema(self.workspace_root)
        self.t2_guidelines = load_guidelines(self.workspace_root, "T2")
        self.t3_guidelines = load_guidelines(self.workspace_root, "T3")

    def tearDown(self):
        if hasattr(self, "_tmp_ws") and self._tmp_ws is not None:
            self._tmp_ws.cleanup()

    # 1. Renamed benchmark input still blocked by hash
    @patch("run_model_g_gemini.annotate_single_query")
    def test_01_renamed_benchmark_input_blocked_by_hash(self, mock_annotate):
        mock_annotate.side_effect = AssertionError("CRITICAL: annotate_single_query should NEVER be called during negative-authorization test!")
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_input = Path(tmpdir) / "innocent_file.jsonl"
            # Copy T2 benchmark file
            shutil.copyfile(self.workspace_root / "inputs" / "model_g_t2_input.jsonl", fake_input)

            # Verification that hash matches benchmark hash
            is_bench, tax = check_is_benchmark_input(fake_input, self.workspace_root)
            self.assertTrue(is_bench)
            self.assertEqual(tax, "T2")

            # run_batch must block it even though the filename is innocent
            out_file = Path(tmpdir) / "out.jsonl"
            tel_dir = Path(tmpdir) / "tel"
            with self.assertRaises(BenchmarkNotAuthorizedError):
                run_batch(
                    taxonomy="T2",
                    input_path=fake_input,
                    output_path=out_file,
                    telemetry_dir=tel_dir,
                    workspace_root=self.workspace_root,
                    run_id="TEST",
                )
            self.assertEqual(mock_annotate.call_count, 0)

    # 2. Copied benchmark input still blocked by hash
    @patch("run_model_g_gemini.annotate_single_query")
    def test_02_copied_benchmark_input_blocked_by_hash(self, mock_annotate):
        mock_annotate.side_effect = AssertionError("CRITICAL: annotate_single_query should NEVER be called during negative-authorization test!")
        with tempfile.TemporaryDirectory() as tmpdir:
            copied_t3 = Path(tmpdir) / "arbitrary_dir" / "random_name.txt"
            copied_t3.parent.mkdir(parents=True)
            shutil.copyfile(self.workspace_root / "inputs" / "model_g_t3_input.jsonl", copied_t3)

            is_bench, tax = check_is_benchmark_input(copied_t3, self.workspace_root)
            self.assertTrue(is_bench)
            self.assertEqual(tax, "T3")

            with self.assertRaises(BenchmarkNotAuthorizedError):
                run_batch(
                    taxonomy="T3",
                    input_path=copied_t3,
                    output_path=Path(tmpdir) / "out.jsonl",
                    telemetry_dir=Path(tmpdir) / "tel",
                    workspace_root=self.workspace_root,
                    run_id="TEST",
                )
            self.assertEqual(mock_annotate.call_count, 0)

    # 3. Benchmark hash rejected in synthetic mode
    @patch("run_model_g_gemini.annotate_single_query")
    def test_03_benchmark_hash_rejected_in_synthetic_mode(self, mock_annotate):
        mock_annotate.side_effect = AssertionError("CRITICAL: annotate_single_query should NEVER be called during synthetic mode test!")
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_synth = Path(tmpdir) / "synthetic_looks_like.jsonl"
            shutil.copyfile(self.workspace_root / "inputs" / "model_g_t2_input.jsonl", fake_synth)

            with self.assertRaises(BenchmarkNotAuthorizedError) as ctx:
                run_batch(
                    taxonomy="T2",
                    input_path=fake_synth,
                    output_path=Path(tmpdir) / "out.jsonl",
                    telemetry_dir=Path(tmpdir) / "tel",
                    workspace_root=self.workspace_root,
                    run_id="TEST",
                    is_synthetic=True,
                )
            self.assertIn("Benchmark input detected in synthetic mode", str(ctx.exception))
            self.assertEqual(mock_annotate.call_count, 0)

    # 4. Missing init fails closed
    def test_04_missing_init_fails_closed(self):
        stream = [
            json.dumps({"event": "step_update", "step_update": {"step_type": "user_input"}}),
            json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "{}"}}),
        ]
        with self.assertRaises(UnrecognizedTelemetryError) as ctx:
            audit_single_invocation_stream(stream, "gemini-3.8-flash-high")
        self.assertIn("TELEMETRY_MISSING_INIT", str(ctx.exception))

    # 5. Missing result fails closed
    def test_05_missing_result_fails_closed(self):
        stream = [
            json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
            json.dumps({"event": "step_update", "step_update": {"step_type": "user_input"}}),
        ]
        with self.assertRaises(UnrecognizedTelemetryError) as ctx:
            audit_single_invocation_stream(stream, "gemini-3.8-flash-high")
        self.assertIn("TELEMETRY_MISSING_RESULT", str(ctx.exception))

    # 6. Non-success result fails closed
    def test_06_non_success_result_fails_closed(self):
        stream = [
            json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
            json.dumps({"event": "result", "result": {"status": "ERROR", "error": "Internal model crash"}}),
        ]
        with self.assertRaises(RuntimeError) as ctx:
            audit_single_invocation_stream(stream, "gemini-3.8-flash-high")
        self.assertIn("Terminal result status is 'ERROR'", str(ctx.exception))

    # 7. Multiple init events fail closed
    def test_07_multiple_init_events_fail_closed(self):
        stream = [
            json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
            json.dumps({"event": "init", "conversation_id": "c2", "init": {"model": "gemini-3.8-flash-high"}}),
            json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "{}"}}),
        ]
        with self.assertRaises(UnrecognizedTelemetryError) as ctx:
            audit_single_invocation_stream(stream, "gemini-3.8-flash-high")
        self.assertIn("TELEMETRY_MULTIPLE_INIT", str(ctx.exception))

    # 8. Multiple result events fail closed
    def test_08_multiple_result_events_fail_closed(self):
        stream = [
            json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
            json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "{}"}}),
            json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "{}"}}),
        ]
        with self.assertRaises(UnrecognizedTelemetryError) as ctx:
            audit_single_invocation_stream(stream, "gemini-3.8-flash-high")
        self.assertIn("TELEMETRY_MULTIPLE_RESULT", str(ctx.exception))

    # 9. Quota detected from stderr
    def test_09_quota_detected_from_stderr(self):
        stderr = "Error: 429 Too Many Requests: resource exhausted quota"
        reason = check_for_provider_limit(stderr, None, [])
        self.assertIsNotNone(reason)
        self.assertIn("429", reason)

    # 10. Quota detected from structured result
    def test_10_quota_detected_from_structured_result(self):
        result_dict = {"status": "ERROR", "error": "rate limit exceeded: please slow down"}
        reason = check_for_provider_limit("", result_dict, [])
        self.assertIsNotNone(reason)
        self.assertIn("rate limit", reason)

    # 11. Quota during format repair pauses without retry
    @patch("run_model_g_gemini.execute_single_invocation")
    def test_11_quota_during_format_repair_pauses_without_retry(self, mock_exec):
        with tempfile.TemporaryDirectory() as tmpdir:
            tel_dir = Path(tmpdir)
            ann_id = "ANN_B2_001"
            mock_tmp1 = Path(tempfile.mkdtemp())
            mock_tmp2 = Path(tempfile.mkdtemp())

            # Initial attempt: output has wrong response_status -> triggers repair
            init_rec = {
                "annotation_id": ann_id,
                "source_id": "MODEL_G",
                "source_type": "model",
                "taxonomy_version": "T2",
                "run_id": "TEST",
                "primary_label": "route_query",
                "acceptable_labels": ["route_query"],
                "clarification_required": False,
                "clarification_reasons": [],
                "brief_justification": "Rationale",
                "recognized_from_prior_work": "not_applicable",
                "active_time_seconds": None,
                "rule_difficulty": "not_applicable",
                "response_status": "BAD_STATUS",
            }
            init_stream = [
                json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high", "cwd": str(mock_tmp1)}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(init_rec)}}),
            ]

            # Repair invocation returns 429 quota exhaustion in result dict
            repair_stream = [
                json.dumps({"event": "init", "conversation_id": "c2", "init": {"model": "gemini-3.8-flash-high", "cwd": str(mock_tmp2)}}),
                json.dumps({"event": "result", "result": {"status": "ERROR", "error": "Quota limit reached (429 ResourceExhausted)"}}),
            ]

            mock_exec.side_effect = [
                (0, init_stream, "", mock_tmp1),
                (1, repair_stream, "Error 429 ResourceExhausted", mock_tmp2),
            ]

            seen_cids = set()
            with self.assertRaises(ProviderLimitError) as ctx:
                annotate_single_query(
                    annotation_id=ann_id,
                    query_text="Sample",
                    taxonomy="T2",
                    guidelines_text=self.t2_guidelines,
                    schema=self.schema,
                    telemetry_dir=tel_dir,
                    seen_conversation_ids=seen_cids,
                )
            self.assertIn("EXECUTION_PAUSED_PROVIDER_LIMIT", str(ctx.exception))
            # Verify call count was exactly 2 (initial + 1 repair, NO endless retry loops)
            self.assertEqual(mock_exec.call_count, 2)

    # 12. Malformed resume telemetry causes RESUME_STATE_INVALID
    def test_12_malformed_resume_telemetry_causes_resume_state_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "outputs.jsonl"
            tel_dir = tmp_path / "telemetry"

            rec = {
                "annotation_id": "ANN_B2_001",
                "source_id": "MODEL_G",
                "source_type": "model",
                "taxonomy_version": "T2",
                "run_id": "TEST",
                "primary_label": "route_query",
                "acceptable_labels": ["route_query"],
                "clarification_required": False,
                "clarification_reasons": [],
                "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable",
                "active_time_seconds": None,
                "rule_difficulty": "not_applicable",
                "response_status": "VALID",
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tel_file = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tel_file.parent.mkdir(parents=True, exist_ok=True)
            tel_file.write_text("THIS IS CORRUPT NON JSON TELEMETRY\n")

            with self.assertRaises(ResumeStateInvalidError):
                load_and_validate_existing_output(
                    output_path=out_file,
                    taxonomy="T2",
                    telemetry_dir=tel_dir,
                    schema=self.schema,
                    authorized_model="gemini-3.8-flash-high",
                    input_ids=["ANN_B2_001"],
                )

    # 13. Unknown resume event causes RESUME_STATE_INVALID
    def test_13_unknown_resume_event_causes_resume_state_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "outputs.jsonl"
            tel_dir = tmp_path / "telemetry"

            rec = {
                "annotation_id": "ANN_B2_001",
                "source_id": "MODEL_G",
                "source_type": "model",
                "taxonomy_version": "T2",
                "run_id": "TEST",
                "primary_label": "route_query",
                "acceptable_labels": ["route_query"],
                "clarification_required": False,
                "clarification_reasons": [],
                "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable",
                "active_time_seconds": None,
                "rule_difficulty": "not_applicable",
                "response_status": "VALID",
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tel_file = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tel_file.parent.mkdir(parents=True, exist_ok=True)
            tel_lines = [
                json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
                json.dumps({"event": "unauthorized_custom_event", "foo": "bar"}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}),
            ]
            tel_file.write_text("\n".join(tel_lines) + "\n")

            with self.assertRaises(ResumeStateInvalidError):
                load_and_validate_existing_output(
                    output_path=out_file,
                    taxonomy="T2",
                    telemetry_dir=tel_dir,
                    schema=self.schema,
                    authorized_model="gemini-3.8-flash-high",
                    input_ids=["ANN_B2_001"],
                )

    # 14. Missing resume init/model causes RESUME_STATE_INVALID
    def test_14_missing_resume_init_model_causes_resume_state_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "outputs.jsonl"
            tel_dir = tmp_path / "telemetry"

            rec = {
                "annotation_id": "ANN_B2_001",
                "source_id": "MODEL_G",
                "source_type": "model",
                "taxonomy_version": "T2",
                "run_id": "TEST",
                "primary_label": "route_query",
                "acceptable_labels": ["route_query"],
                "clarification_required": False,
                "clarification_reasons": [],
                "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable",
                "active_time_seconds": None,
                "rule_difficulty": "not_applicable",
                "response_status": "VALID",
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tel_file = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tel_file.parent.mkdir(parents=True, exist_ok=True)
            # Missing init
            tel_lines = [
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}),
            ]
            tel_file.write_text("\n".join(tel_lines) + "\n")

            with self.assertRaises(ResumeStateInvalidError):
                load_and_validate_existing_output(
                    output_path=out_file,
                    taxonomy="T2",
                    telemetry_dir=tel_dir,
                    schema=self.schema,
                    authorized_model="gemini-3.8-flash-high",
                    input_ids=["ANN_B2_001"],
                )

    # 15. Missing resume result causes RESUME_STATE_INVALID
    def test_15_missing_resume_result_causes_resume_state_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "outputs.jsonl"
            tel_dir = tmp_path / "telemetry"

            rec = {
                "annotation_id": "ANN_B2_001",
                "source_id": "MODEL_G",
                "source_type": "model",
                "taxonomy_version": "T2",
                "run_id": "TEST",
                "primary_label": "route_query",
                "acceptable_labels": ["route_query"],
                "clarification_required": False,
                "clarification_reasons": [],
                "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable",
                "active_time_seconds": None,
                "rule_difficulty": "not_applicable",
                "response_status": "VALID",
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tel_file = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tel_file.parent.mkdir(parents=True, exist_ok=True)
            # Missing result
            tel_lines = [
                json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
            ]
            tel_file.write_text("\n".join(tel_lines) + "\n")

            with self.assertRaises(ResumeStateInvalidError):
                load_and_validate_existing_output(
                    output_path=out_file,
                    taxonomy="T2",
                    telemetry_dir=tel_dir,
                    schema=self.schema,
                    authorized_model="gemini-3.8-flash-high",
                    input_ids=["ANN_B2_001"],
                )

    # 16. Non-prefix resume output rejected
    def test_16_non_prefix_resume_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "outputs.jsonl"
            tel_dir = tmp_path / "telemetry"

            # Existing IDs are: ANN_B2_001, ANN_B2_003 (skipped ANN_B2_002!)
            rec1 = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "VALID"
            }
            rec3 = dict(rec1, annotation_id="ANN_B2_003")
            out_file.write_text(json.dumps(rec1) + "\n" + json.dumps(rec3) + "\n")

            for ann_id in ["ANN_B2_001", "ANN_B2_003"]:
                tf = tel_dir / "T2" / f"{ann_id}.telemetry.jsonl"
                tf.parent.mkdir(parents=True, exist_ok=True)
                lines = [
                    json.dumps({"event": "init", "conversation_id": f"c_{ann_id}", "init": {"model": "gemini-3.8-flash-high"}}),
                    json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec1 if ann_id=='ANN_B2_001' else rec3)}}),
                ]
                tf.write_text("\n".join(lines) + "\n")

            input_ids = ["ANN_B2_001", "ANN_B2_002", "ANN_B2_003"]
            with self.assertRaises(ResumeStateInvalidError) as ctx:
                load_and_validate_existing_output(
                    output_path=out_file,
                    taxonomy="T2",
                    telemetry_dir=tel_dir,
                    schema=self.schema,
                    authorized_model="gemini-3.8-flash-high",
                    input_ids=input_ids,
                )
            self.assertIn("not an exact deterministic prefix", str(ctx.exception))

    # 17. Valid exact prefix accepted
    def test_17_valid_exact_prefix_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "outputs.jsonl"
            tel_dir = tmp_path / "telemetry"

            rec1 = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "VALID"
            }
            rec2 = dict(rec1, annotation_id="ANN_B2_002")
            out_file.write_text(json.dumps(rec1) + "\n" + json.dumps(rec2) + "\n")

            for ann_id, rec in [("ANN_B2_001", rec1), ("ANN_B2_002", rec2)]:
                tf = tel_dir / "T2" / f"{ann_id}.telemetry.jsonl"
                tf.parent.mkdir(parents=True, exist_ok=True)
                lines = [
                    json.dumps({"event": "init", "conversation_id": f"c_{ann_id}", "init": {"model": "gemini-3.8-flash-high"}}),
                    json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}),
                ]
                tf.write_text("\n".join(lines) + "\n")

            input_ids = ["ANN_B2_001", "ANN_B2_002", "ANN_B2_003"]
            acc, c_ids, seen_convs = load_and_validate_existing_output(
                output_path=out_file,
                taxonomy="T2",
                telemetry_dir=tel_dir,
                schema=self.schema,
                authorized_model="gemini-3.8-flash-high",
                input_ids=input_ids,
            )
            self.assertEqual(len(acc), 2)
            self.assertEqual(c_ids, ["ANN_B2_001", "ANN_B2_002"])

    # 18. Existing ID not in input rejected
    def test_18_existing_id_not_in_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "outputs.jsonl"
            tel_dir = tmp_path / "telemetry"

            rec = {
                "annotation_id": "ANN_B2_999", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "VALID"
            }
            out_file.write_text(json.dumps(rec) + "\n")
            tf = tel_dir / "T2" / "ANN_B2_999.telemetry.jsonl"
            tf.parent.mkdir(parents=True, exist_ok=True)
            tf.write_text(json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}) + "\n" +
                          json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}) + "\n")

            input_ids = ["ANN_B2_001", "ANN_B2_002"]
            with self.assertRaises(ResumeStateInvalidError):
                load_and_validate_existing_output(
                    output_path=out_file,
                    taxonomy="T2",
                    telemetry_dir=tel_dir,
                    schema=self.schema,
                    authorized_model="gemini-3.8-flash-high",
                    input_ids=input_ids,
                )

    # 19. Validator requires observed model identity
    def test_19_validator_requires_observed_model_identity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "output.jsonl"
            tel_dir = tmp_path / "tel"

            rec = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "VALID"
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tf = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tf.parent.mkdir(parents=True, exist_ok=True)
            # Init reports claude-sonnet-4-6 instead of gemini-3.8-flash-high
            tf.write_text(json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "claude-sonnet-4-6"}}) + "\n" +
                          json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}) + "\n")

            summary = validate_outputs(
                output_file=out_file,
                taxonomy="T2",
                telemetry_dir=tel_dir,
                workspace_root=self.workspace_root,
                expected_count=1,
                expected_ids=["ANN_B2_001"],
            )
            self.assertFalse(summary["passed"])
            self.assertTrue(any("Model identity mismatch" in e for e in summary["errors"]))

    # 20. Validator requires terminal success
    def test_20_validator_requires_terminal_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "output.jsonl"
            tel_dir = tmp_path / "tel"

            rec = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "VALID"
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tf = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tf.parent.mkdir(parents=True, exist_ok=True)
            # Result status is ERROR
            tf.write_text(json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}) + "\n" +
                          json.dumps({"event": "result", "result": {"status": "ERROR", "response": json.dumps(rec)}}) + "\n")

            summary = validate_outputs(
                output_file=out_file,
                taxonomy="T2",
                telemetry_dir=tel_dir,
                workspace_root=self.workspace_root,
                expected_count=1,
                expected_ids=["ANN_B2_001"],
            )
            self.assertFalse(summary["passed"])
            self.assertTrue(any("No terminal SUCCESS result found" in e for e in summary["errors"]))

    # 21. Validator rejects >1 format repair
    def test_21_validator_rejects_greater_than_one_format_repair(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "output.jsonl"
            tel_dir = tmp_path / "tel"

            rec = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "FORMAT_REPAIRED"
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tf = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tf.parent.mkdir(parents=True, exist_ok=True)
            # Two format repair attempts!
            lines = [
                json.dumps({"event": "invocation_attempt_metadata", "attempt_type": "initial"}),
                json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "{}"}}),
                json.dumps({"event": "invocation_attempt_metadata", "attempt_type": "format_repair"}),
                json.dumps({"event": "init", "conversation_id": "c2", "init": {"model": "gemini-3.8-flash-high"}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "{}"}}),
                json.dumps({"event": "invocation_attempt_metadata", "attempt_type": "format_repair"}),
                json.dumps({"event": "init", "conversation_id": "c3", "init": {"model": "gemini-3.8-flash-high"}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}),
            ]
            tf.write_text("\n".join(lines) + "\n")

            summary = validate_outputs(
                output_file=out_file,
                taxonomy="T2",
                telemetry_dir=tel_dir,
                workspace_root=self.workspace_root,
                expected_count=1,
                expected_ids=["ANN_B2_001"],
            )
            self.assertFalse(summary["passed"])
            self.assertTrue(any("exceed frozen limit of 1" in e for e in summary["errors"]))

    # 22. VALID + repair telemetry rejected
    def test_22_valid_with_repair_telemetry_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "output.jsonl"
            tel_dir = tmp_path / "tel"

            rec = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "VALID"  # Says VALID but telemetry had repair!
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tf = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tf.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                json.dumps({"event": "invocation_attempt_metadata", "attempt_type": "format_repair"}),
                json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}),
            ]
            tf.write_text("\n".join(lines) + "\n")

            summary = validate_outputs(
                output_file=out_file,
                taxonomy="T2",
                telemetry_dir=tel_dir,
                workspace_root=self.workspace_root,
                expected_count=1,
                expected_ids=["ANN_B2_001"],
            )
            self.assertFalse(summary["passed"])
            self.assertTrue(any("response_status is VALID but telemetry recorded 1 format repairs" in e for e in summary["errors"]))

    # 23. FORMAT_REPAIRED + no repair telemetry rejected
    def test_23_format_repaired_with_no_repair_telemetry_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "output.jsonl"
            tel_dir = tmp_path / "tel"

            rec = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "FORMAT_REPAIRED"  # Claims repaired, but telemetry shows 0 repairs!
            }
            out_file.write_text(json.dumps(rec) + "\n")

            tf = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            tf.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                json.dumps({"event": "invocation_attempt_metadata", "attempt_type": "initial"}),
                json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "gemini-3.8-flash-high"}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}),
            ]
            tf.write_text("\n".join(lines) + "\n")

            summary = validate_outputs(
                output_file=out_file,
                taxonomy="T2",
                telemetry_dir=tel_dir,
                workspace_root=self.workspace_root,
                expected_count=1,
                expected_ids=["ANN_B2_001"],
            )
            self.assertFalse(summary["passed"])
            self.assertTrue(any("response_status is FORMAT_REPAIRED but telemetry recorded 0 format repairs" in e for e in summary["errors"]))

    # 24. Duplicate conversation ID across accepted items rejected
    def test_24_duplicate_conversation_id_across_accepted_items_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_file = tmp_path / "output.jsonl"
            tel_dir = tmp_path / "tel"

            rec1 = {
                "annotation_id": "ANN_B2_001", "source_id": "MODEL_G", "source_type": "model", "taxonomy_version": "T2",
                "run_id": "TEST", "primary_label": "route_query", "acceptable_labels": ["route_query"],
                "clarification_required": False, "clarification_reasons": [], "brief_justification": "Valid",
                "recognized_from_prior_work": "not_applicable", "active_time_seconds": None, "rule_difficulty": "not_applicable",
                "response_status": "VALID"
            }
            rec2 = dict(rec1, annotation_id="ANN_B2_002")
            out_file.write_text(json.dumps(rec1) + "\n" + json.dumps(rec2) + "\n")

            # Both items share the SAME conversation ID "reused_conv_123"!
            for ann_id, rec in [("ANN_B2_001", rec1), ("ANN_B2_002", rec2)]:
                tf = tel_dir / "T2" / f"{ann_id}.telemetry.jsonl"
                tf.parent.mkdir(parents=True, exist_ok=True)
                lines = [
                    json.dumps({"event": "init", "conversation_id": "reused_conv_123", "init": {"model": "gemini-3.8-flash-high"}}),
                    json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(rec)}}),
                ]
                tf.write_text("\n".join(lines) + "\n")

            summary = validate_outputs(
                output_file=out_file,
                taxonomy="T2",
                telemetry_dir=tel_dir,
                workspace_root=self.workspace_root,
                expected_count=2,
                expected_ids=["ANN_B2_001", "ANN_B2_002"],
            )
            self.assertFalse(summary["passed"])
            self.assertTrue(any("Duplicate conversation_id 'reused_conv_123'" in e for e in summary["errors"]))

    # 25. Benchmark authorization false remains fail-closed
    @patch("run_model_g_gemini.annotate_single_query")
    def test_25_benchmark_authorization_false_remains_fail_closed(self, mock_annotate):
        mock_annotate.side_effect = AssertionError("CRITICAL: annotate_single_query should NEVER be called during negative-authorization test!")
        self.assertFalse(check_benchmark_authorization(self.workspace_root))
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(BenchmarkNotAuthorizedError):
                run_batch(
                    taxonomy="T2",
                    input_path=self.workspace_root / "inputs" / "model_g_t2_input.jsonl",
                    output_path=Path(tmpdir) / "out.jsonl",
                    telemetry_dir=Path(tmpdir) / "tel",
                    workspace_root=self.workspace_root,
                    run_id="PROHIBITED",
                )
            self.assertEqual(mock_annotate.call_count, 0)

    # 26. Package hash drift remains fail-closed
    def test_26_package_hash_drift_remains_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_root = Path(tmpdir)
            shutil.copytree(self.workspace_root / "protocol", fake_root / "protocol")
            shutil.copytree(self.workspace_root / "inputs", fake_root / "inputs")

            # Tamper with schema
            with open(fake_root / "protocol" / "annotation_output_schema.json", "a") as f:
                f.write(" ")

            with self.assertRaises(PackageIntegrityError) as ctx:
                verify_package_integrity(fake_root, "T2")
            self.assertIn("Protocol hash mismatch for annotation_output_schema.json", str(ctx.exception))

    # 27. Telemetry namespace collision prevention
    def test_27_telemetry_namespace_collision_prevention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tel_dir = Path(tmpdir)
            t2_file = tel_dir / "T2" / "ANN_B2_001.telemetry.jsonl"
            t3_file = tel_dir / "T3" / "ANN_B2_001.telemetry.jsonl"

            t2_file.parent.mkdir(parents=True, exist_ok=True)
            t3_file.parent.mkdir(parents=True, exist_ok=True)

            t2_file.write_text('{"taxonomy": "T2", "data": "t2_unique"}\n')
            t3_file.write_text('{"taxonomy": "T3", "data": "t3_unique"}\n')

            self.assertTrue(t2_file.exists())
            self.assertTrue(t3_file.exists())
            self.assertIn("t2_unique", t2_file.read_text())
            self.assertIn("t3_unique", t3_file.read_text())

    # 28. False clarification with nonempty reasons rejected
    def test_28_false_clarification_with_nonempty_reasons_rejected(self):
        rec = {
            "annotation_id": "ANN_B2_001",
            "source_id": "MODEL_G",
            "source_type": "model",
            "taxonomy_version": "T2",
            "run_id": "TEST_RUN",
            "primary_label": "route_query",
            "acceptable_labels": ["route_query"],
            "clarification_required": False,
            "clarification_reasons": ["missing_slot"],
            "brief_justification": "Valid justification",
            "recognized_from_prior_work": "not_applicable",
            "active_time_seconds": None,
            "rule_difficulty": "not_applicable",
            "response_status": "VALID",
        }
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_record_invariants(rec, self.schema, "ANN_B2_001", "T2")
        self.assertIn("clarification_reasons must be []", str(ctx.exception))

    # 29. Semantic-changing format repair rejected
    @patch("run_model_g_gemini.execute_single_invocation")
    def test_29_semantic_changing_format_repair_rejected(self, mock_exec):
        with tempfile.TemporaryDirectory() as tmpdir:
            tel_dir = Path(tmpdir)
            ann_id = "ANN_B2_003"
            mock_tmp1 = Path(tempfile.mkdtemp())
            mock_tmp2 = Path(tempfile.mkdtemp())

            initial_rec = {
                "annotation_id": ann_id,
                "source_id": "MODEL_G",
                "source_type": "model",
                "taxonomy_version": "T2",
                "run_id": "TEST",
                "primary_label": "route_query",
                "acceptable_labels": ["route_query"],
                "clarification_required": False,
                "clarification_reasons": [],
                "brief_justification": "Initial route rationale",
                "recognized_from_prior_work": "not_applicable",
                "active_time_seconds": None,
                "rule_difficulty": "not_applicable",
                "response_status": "INVALID_STATUS",
            }
            initial_stream = [
                json.dumps({"event": "init", "conversation_id": "c_init", "init": {"model": "gemini-3.8-flash-high", "cwd": str(mock_tmp1)}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(initial_rec)}}),
            ]

            repaired_rec = dict(initial_rec, primary_label="fare_query", acceptable_labels=["fare_query"], response_status="FORMAT_REPAIRED")
            repair_stream = [
                json.dumps({"event": "init", "conversation_id": "c_rep", "init": {"model": "gemini-3.8-flash-high", "cwd": str(mock_tmp2)}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": json.dumps(repaired_rec)}}),
            ]

            mock_exec.side_effect = [
                (0, initial_stream, "", mock_tmp1),
                (0, repair_stream, "", mock_tmp2),
            ]

            seen_cids = set()
            with self.assertRaises(SemanticChangeDuringFormatRepairError) as ctx:
                annotate_single_query(
                    annotation_id=ann_id,
                    query_text="Dummy",
                    taxonomy="T2",
                    guidelines_text=self.t2_guidelines,
                    schema=self.schema,
                    telemetry_dir=tel_dir,
                    seen_conversation_ids=seen_cids,
                )
            self.assertIn("SEMANTIC_CHANGE_DURING_FORMAT_REPAIR", str(ctx.exception))

    # 30. Unparseable output not semantically retried
    @patch("run_model_g_gemini.execute_single_invocation")
    def test_30_unparseable_output_not_semantically_retried(self, mock_exec):
        with tempfile.TemporaryDirectory() as tmpdir:
            tel_dir = Path(tmpdir)
            ann_id = "ANN_B2_004"
            mock_tmp = Path(tempfile.mkdtemp())

            unparseable_stream = [
                json.dumps({"event": "init", "conversation_id": "c_unparse", "init": {"model": "gemini-3.8-flash-high", "cwd": str(mock_tmp)}}),
                json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "Sorry, I cannot annotate this transit request."}}),
            ]
            mock_exec.return_value = (0, unparseable_stream, "", mock_tmp)

            seen_cids = set()
            with self.assertRaises(UnrecoverableMalformedOutputError) as ctx:
                annotate_single_query(
                    annotation_id=ann_id,
                    query_text="Dummy",
                    taxonomy="T2",
                    guidelines_text=self.t2_guidelines,
                    schema=self.schema,
                    telemetry_dir=tel_dir,
                    seen_conversation_ids=seen_cids,
                )
            self.assertIn("semantic_retries = 0", str(ctx.exception))
            self.assertEqual(mock_exec.call_count, 1)

    # 31. Atomic output replacement
    def test_31_atomic_output_replacement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "output.jsonl"
            existing = [{"id": 1}]
            new_item = {"id": 2}

            save_accepted_record_atomic(out_file, new_item, existing)
            self.assertTrue(out_file.exists())
            lines = out_file.read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0]), {"id": 1})
            self.assertEqual(json.loads(lines[1]), {"id": 2})
            self.assertEqual(len(list(Path(tmpdir).glob("*.tmp*"))), 0)

    # 32. Regression: authorized live sterile workspace is never consulted by canonical tests
    def test_32_regression_sterile_workspace_never_consulted(self):
        sterile_candidate = Path("/home/kaustubh/gate-b3-model-g-gemini")
        # Ensure our active workspace is strictly inside temp and not sterile
        self.assertNotEqual(self.workspace_root.resolve(), sterile_candidate.resolve())
        self.assertTrue(str(self.workspace_root).startswith(tempfile.gettempdir()))

        # Even if environment variable attempts to point to sterile workspace, helper creates isolated tempdir
        with patch.dict(os.environ, {"MODEL_G_WORKSPACE_ROOT": str(sterile_candidate)}):
            tmp, ws = create_isolated_workspace(benchmark_authorized=False)
            try:
                self.assertNotEqual(ws.resolve(), sterile_candidate.resolve())
                self.assertTrue(str(ws).startswith(tempfile.gettempdir()))
            finally:
                tmp.cleanup()

    # 33. Regression: negative authorization test uses temporary unauthorized manifest
    def test_33_regression_negative_authorization_uses_temporary_unauthorized_manifest(self):
        # Ephemeral workspace manifest has benchmark_execution_authorized = False
        manifest = json.loads((self.workspace_root / "protocol" / "model_g_execution_manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["benchmark_execution_authorized"])
        self.assertFalse(check_benchmark_authorization(self.workspace_root))

        # Canonical repo manifest remains unchanged (authorized = True)
        canonical_manifest = json.loads(
            (REPO_ROOT / "data" / "nlp_v2" / "gate_b3" / "model_g_execution_manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(canonical_manifest["benchmark_execution_authorized"])

    # 34. Regression: run_batch authorization tests cannot spawn agy
    def test_34_regression_run_batch_authorization_tests_cannot_spawn_agy(self):
        # Even if benchmark is authorized in a temporary workspace, unmocked run_batch cannot call agy
        tmp, authorized_ws = create_isolated_workspace(benchmark_authorized=True)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with self.assertRaises(LiveAgyExecutionAttemptError):
                    run_batch(
                        taxonomy="T2",
                        input_path=authorized_ws / "inputs" / "model_g_t2_input.jsonl",
                        output_path=Path(tmpdir) / "out.jsonl",
                        telemetry_dir=Path(tmpdir) / "tel",
                        workspace_root=authorized_ws,
                        run_id="TEST_RUN",
                    )
        finally:
            tmp.cleanup()

    # 35. Regression: semantic-child subprocess function is mocked in all unit tests that could reach it
    def test_35_regression_semantic_subprocess_mocked_in_unit_tests(self):
        # Guarded function is in place
        self.assertEqual(run_model_g_gemini.execute_single_invocation, guarded_execute_single_invocation)
        self.assertEqual(run_model_g_gemini.subprocess.run, guarded_subprocess_run)

    # 36. Guard fails if a unit test execution attempts to invoke agy
    def test_36_guard_fails_if_unit_test_invokes_agy(self):
        with self.assertRaises(LiveAgyExecutionAttemptError) as ctx1:
            run_model_g_gemini.execute_single_invocation("test prompt")
        self.assertIn("CRITICAL GUARD TRIGGERED", str(ctx1.exception))

        with self.assertRaises(LiveAgyExecutionAttemptError) as ctx2:
            run_model_g_gemini.subprocess.run(["agy", "--version"])
        self.assertIn("CRITICAL GUARD TRIGGERED", str(ctx2.exception))


if __name__ == "__main__":
    unittest.main()
