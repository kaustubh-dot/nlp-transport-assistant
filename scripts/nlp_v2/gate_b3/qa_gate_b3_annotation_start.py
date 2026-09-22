#!/usr/bin/env python3
"""Annotation-Start QA Gatekeeper for NLP v2 Gate B.3.

Enforces Section 20, as amended by Gate B.3 Resource-Feasibility / Annotator-Design Amendment:
Checks whether active model configurations are formally frozen and ready for annotation.
Requires:
1. MODEL_G Configuration (Active Primary Model Annotator):
   - status != PENDING
   - provider != PENDING
   - model != PENDING
   - version != PENDING and version != "" and version is not None
   - configuration_frozen == True
   - exact_version_or_revision not in (None, "", "PENDING")
     (Note: 'NOT_EXPOSED_BY_PROVIDER' is accepted as valid provenance)
   - execution_isolation_class == "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION"
   - actual_tool_use_allowed == False
   - zero_tool_use_audit_required == True
   - fresh_context_per_item_required == True
   - empty_workdir_required == True
   - retry_policy.tool_violation_retry_attempts == 0
   - retry_policy.tool_violation_mode == "HARD_FAIL_BATCH"
2. Methodology Hash Recomputation:
   - prompt_sha256, t2_guide_sha256, t3_guide_sha256, schema_sha256,
     execution_isolation_amendment_sha256, and resource_feasibility_amendment_sha256 present.
   - Computed SHA-256 for prompt, T2 guide, T3 guide, schema, and amendments must match stored hashes.
   - Any mismatch reports: FROZEN_ANNOTATION_CONFIGURATION_DRIFT
3. Canonical Model Configuration Hash Recomputation:
   - Reconstruct canonical frozen configuration object for MODEL_G.
   - Deterministic SHA-256 must match stored configuration_sha256 exactly.
   - Global configuration_sha256 recomputed over protocol and active model hash must match.
   - Any mismatch reports: FROZEN_MODEL_CONFIGURATION_DRIFT
4. Execution-Readiness Gate:
   - Behavioral isolation verified (fresh_context, empty_workdir, zero_tool_use_audit)
   - execution_isolation_verified == True (denoting verified compliance with the
     EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION protocol)
   - synthetic_smoke_test_passed == True
   - benchmark_execution_authorized == True
   - When execution readiness is unverified (expected prior to synthetic smoke test completion),
     reports: BLOCKED / NOT READY and exits with code 1.
5. Historical Retired Models:
   - MODEL_A and MODEL_B preserved in provenance with primary_analysis_included == False.
   - Retired models do NOT act as active blockers.
6. Pre-Annotation Guardrails:
   - annotation_started == False, first_pass_locked == False, reference_join_enabled == False.
"""

import os
import sys
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
DOCS_B3_DIR = os.path.join(BASE_DIR, "docs", "nlp_v2", "gate_b3")

CONFIGS_PATH = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
MANIFEST_PATH = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")

METHODOLOGY_ARTIFACTS = {
    "prompt_sha256": ("model_annotator_prompt_template.md", os.path.join(DOCS_B3_DIR, "model_annotator_prompt_template.md")),
    "t2_guide_sha256": ("t2_annotation_guide.md", os.path.join(DOCS_B3_DIR, "t2_annotation_guide.md")),
    "t3_guide_sha256": ("t3_annotation_guide.md", os.path.join(DOCS_B3_DIR, "t3_annotation_guide.md")),
    "schema_sha256": ("annotation_output_schema.json", os.path.join(DOCS_B3_DIR, "annotation_output_schema.json")),
    "execution_isolation_amendment_sha256": ("gate_b3_execution_isolation_amendment.md", os.path.join(DOCS_B3_DIR, "gate_b3_execution_isolation_amendment.md")),
    "resource_feasibility_amendment_sha256": ("gate_b3_resource_feasibility_annotator_amendment.md", os.path.join(DOCS_B3_DIR, "gate_b3_resource_feasibility_annotator_amendment.md")),
}

CANONICAL_MODEL_FIELDS = (
    "source_id",
    "provider",
    "model",
    "version",
    "exact_version_or_revision",
    "execution_environment",
    "execution_model_selector",
    "execution_isolation_class",
    "fresh_context_per_item_required",
    "empty_workdir_required",
    "benchmark_paths_provided_to_child",
    "cross_query_history_allowed",
    "actual_tool_use_allowed",
    "zero_tool_use_audit_required",
    "tool_violation_retry_attempts",
    "reasoning_configuration",
    "tool_policy",
    "request_isolation",
    "retry_policy",
)


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def extract_canonical_model_config(model_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts only frozen semantic/execution requirements for canonical hashing."""
    return {k: model_dict[k] for k in CANONICAL_MODEL_FIELDS if k in model_dict}


def compute_canonical_hash(canonical_obj: Any) -> str:
    """Computes deterministic SHA-256 over canonical JSON object."""
    raw = json.dumps(
        canonical_obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def compute_model_config_hash(model_dict: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 for a model's canonical configuration."""
    canonical_obj = extract_canonical_model_config(model_dict)
    return compute_canonical_hash(canonical_obj)


def compute_global_config_hash(cfg: Dict[str, Any], *args, **kwargs) -> str:
    """Computes deterministic SHA-256 for global configuration.
    
    Supports amended MODEL_G single primary configuration as well as
    historical dual-model configurations for backward compatibility in tests.
    """
    primary_id = cfg.get("primary_model_annotator_source_id")
    if primary_id == "MODEL_G" or "model_g_hash" in kwargs or (len(args) == 1 and primary_id == "MODEL_G"):
        g_hash = kwargs.get("model_g_hash")
        if g_hash is None and len(args) >= 1:
            g_hash = args[0]
        if g_hash is None:
            g_hash = compute_model_config_hash(cfg.get("MODEL_G", {}))
        canonical_global = {
            "study": cfg.get("study", "Gate B.3 Annotation-Stability Framework"),
            "primary_model_annotator_source_id": "MODEL_G",
            "prompt_sha256": cfg.get("prompt_sha256"),
            "t2_guide_sha256": cfg.get("t2_guide_sha256"),
            "t3_guide_sha256": cfg.get("t3_guide_sha256"),
            "schema_sha256": cfg.get("schema_sha256"),
            "execution_isolation_amendment_sha256": cfg.get("execution_isolation_amendment_sha256"),
            "resource_feasibility_amendment_sha256": cfg.get("resource_feasibility_amendment_sha256"),
            "model_g_configuration_sha256": g_hash,
        }
    else:
        m_a_hash = kwargs.get("model_a_hash", args[0] if len(args) > 0 else "")
        m_b_hash = kwargs.get("model_b_hash", args[1] if len(args) > 1 else "")
        canonical_global = {
            "study": cfg.get("study", "Gate B.3 Annotation-Stability Framework"),
            "prompt_sha256": cfg.get("prompt_sha256"),
            "t2_guide_sha256": cfg.get("t2_guide_sha256"),
            "t3_guide_sha256": cfg.get("t3_guide_sha256"),
            "schema_sha256": cfg.get("schema_sha256"),
            "execution_isolation_amendment_sha256": cfg.get("execution_isolation_amendment_sha256"),
            "model_a_configuration_sha256": m_a_hash,
            "model_b_configuration_sha256": m_b_hash,
        }
    return compute_canonical_hash(canonical_global)


def evaluate_annotation_start_readiness(
    configs_path: str = CONFIGS_PATH,
    manifest_path: str = MANIFEST_PATH,
    artifacts_map: Optional[Dict[str, Tuple[str, str]]] = None
) -> Tuple[bool, List[str]]:
    """Evaluates readiness to commence model annotation."""
    reasons_blocked = []
    if artifacts_map is None:
        artifacts_map = METHODOLOGY_ARTIFACTS

    # 1. Check Model Configs File
    if not os.path.exists(configs_path):
        reasons_blocked.append(f"Missing config file: {configs_path}")
        return False, reasons_blocked

    with open(configs_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Global configuration freeze check
    is_globally_frozen = bool(cfg.get("configuration_frozen", False))
    if not is_globally_frozen:
        reasons_blocked.append("Global configuration_frozen is False")

    # If configuration is frozen, require configuration_sha256
    stored_global_sha = cfg.get("configuration_sha256")
    if is_globally_frozen and not stored_global_sha:
        reasons_blocked.append("Global configuration_sha256 missing while configuration_frozen is True")

    # 2. Methodology Hashes Recomputation and Verification
    for key, (artifact_name, artifact_path) in artifacts_map.items():
        stored_hash = cfg.get(key)
        if not stored_hash:
            reasons_blocked.append(f"{key} ({artifact_name}) is null or missing")
        else:
            if not os.path.exists(artifact_path):
                reasons_blocked.append(f"Methodology artifact file missing: {artifact_path}")
            else:
                current_sha = compute_sha256(artifact_path)
                if current_sha != stored_hash:
                    reasons_blocked.append(
                        f"FROZEN_ANNOTATION_CONFIGURATION_DRIFT: {artifact_name} drifted! "
                        f"Stored: {stored_hash}, Computed: {current_sha}"
                    )

    # 3. Active Primary Model Specifications Verification
    primary_source_id = cfg.get("primary_model_annotator_source_id", "MODEL_G")
    active_model_names = [primary_source_id] if primary_source_id in cfg else ["MODEL_G"]

    for m_name in active_model_names:
        m = cfg.get(m_name, {})
        status = m.get("status")
        provider = m.get("provider")
        model = m.get("model")
        version = m.get("version")
        is_frozen = m.get("configuration_frozen", False)
        exact_rev = m.get("exact_version_or_revision")

        if status == "PENDING":
            reasons_blocked.append(f"{m_name} status remains PENDING")
        if provider == "PENDING" or not provider:
            reasons_blocked.append(f"{m_name} provider remains PENDING or empty")
        if model == "PENDING" or not model:
            reasons_blocked.append(f"{m_name} model remains PENDING or empty")
        if version == "PENDING" or not version:
            reasons_blocked.append(f"{m_name} version remains PENDING or empty")
        if m.get("execution_model_selector") in (None, "", "PENDING"):
            reasons_blocked.append(f"{m_name} execution_model_selector remains PENDING or empty")
        if not is_frozen:
            reasons_blocked.append(f"{m_name} configuration_frozen is False")
        else:
            # When frozen, require configuration_sha256 and verify against recomputed canonical hash
            stored_model_sha = m.get("configuration_sha256")
            if not stored_model_sha:
                reasons_blocked.append(f"{m_name} configuration_sha256 missing while configuration_frozen is True")
            else:
                computed_model_sha = compute_model_config_hash(m)
                if computed_model_sha != stored_model_sha:
                    reasons_blocked.append(
                        f"FROZEN_MODEL_CONFIGURATION_DRIFT: {m_name} configuration drifted! "
                        f"Stored: {stored_model_sha}, Computed: {computed_model_sha}"
                    )
            # When frozen, exact_version_or_revision must be specified
            if exact_rev in (None, "", "PENDING"):
                reasons_blocked.append(
                    f"{m_name} exact_version_or_revision must be provided when frozen "
                    f"(got '{exact_rev}'; use 'NOT_EXPOSED_BY_PROVIDER' if provider exposes no revision)"
                )

        # Canonical isolation class requirement
        isolation_class = m.get("execution_isolation_class")
        if isolation_class != "EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION":
            reasons_blocked.append(
                f"{m_name} execution_isolation_class must be 'EMPTY_WORKDIR_BEHAVIORAL_TOOL_RESTRICTION' (got '{isolation_class}')"
            )

        # Behavioral tool restriction policy requirements
        if m.get("actual_tool_use_allowed") is not False:
            reasons_blocked.append(f"{m_name} actual_tool_use_allowed must be False")
        if m.get("zero_tool_use_audit_required") is not True:
            reasons_blocked.append(f"{m_name} zero_tool_use_audit_required must be True")
        if m.get("fresh_context_per_item_required") is not True:
            reasons_blocked.append(f"{m_name} fresh_context_per_item_required must be True")
        if m.get("empty_workdir_required") is not True:
            reasons_blocked.append(f"{m_name} empty_workdir_required must be True")

        # Retry policy requirements: tool violation retry attempts must be 0
        retry_pol = m.get("retry_policy", {})
        if retry_pol.get("tool_violation_retry_attempts") != 0:
            reasons_blocked.append(f"{m_name} retry_policy.tool_violation_retry_attempts must be 0")
        if retry_pol.get("tool_violation_mode") != "HARD_FAIL_BATCH":
            reasons_blocked.append(f"{m_name} retry_policy.tool_violation_mode must be 'HARD_FAIL_BATCH'")

        # Execution-readiness gate for active model:
        if not m.get("fresh_context_per_item_verified", False):
            reasons_blocked.append(f"{m_name} fresh context per item not verified")
        if not m.get("empty_workdir_verified", False):
            reasons_blocked.append(f"{m_name} empty workdir not verified")
        if not m.get("zero_tool_use_audit_verified", False):
            reasons_blocked.append(f"{m_name} zero-tool-use audit not verified")
        if not m.get("execution_isolation_verified", False):
            reasons_blocked.append(f"{m_name} behavioral execution isolation not verified")
        else:
            if not (m.get("fresh_context_per_item_verified", False) and m.get("empty_workdir_verified", False) and m.get("zero_tool_use_audit_verified", False)):
                reasons_blocked.append(
                    f"{m_name} execution_isolation_verified cannot be True before fresh_context, empty_workdir, and zero_tool_use_audit are verified"
                )
        if not m.get("synthetic_smoke_test_passed", False):
            reasons_blocked.append(f"{m_name} synthetic smoke test not passed")
        if not m.get("benchmark_execution_authorized", False):
            reasons_blocked.append(f"{m_name} benchmark execution not authorized")

    # Check that retired models are preserved in provenance and not included in primary analysis
    retired_sources = cfg.get("retired_primary_model_sources", ["MODEL_A", "MODEL_B"])
    for ret_name in retired_sources:
        if ret_name in cfg:
            ret_m = cfg[ret_name]
            if ret_m.get("primary_analysis_included") is not False:
                reasons_blocked.append(f"{ret_name} must have primary_analysis_included == False")

    # Recompute and verify global configuration hash if frozen
    if is_globally_frozen and stored_global_sha:
        if primary_source_id == "MODEL_G":
            m_g = cfg.get("MODEL_G", {})
            sha_g = compute_model_config_hash(m_g) if m_g.get("configuration_frozen") else m_g.get("configuration_sha256", "")
            computed_global_sha = compute_global_config_hash(cfg, sha_g)
        else:
            m_a = cfg.get("MODEL_A", {})
            m_b = cfg.get("MODEL_B", {})
            sha_a = compute_model_config_hash(m_a) if m_a.get("configuration_frozen") else m_a.get("configuration_sha256", "")
            sha_b = compute_model_config_hash(m_b) if m_b.get("configuration_frozen") else m_b.get("configuration_sha256", "")
            computed_global_sha = compute_global_config_hash(cfg, sha_a, sha_b)

        if computed_global_sha != stored_global_sha:
            reasons_blocked.append(
                f"FROZEN_MODEL_CONFIGURATION_DRIFT: Global configuration drifted! "
                f"Stored: {stored_global_sha}, Computed: {computed_global_sha}"
            )

    # 4. Manifest Pre-Annotation Guardrails
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        if manifest.get("annotation_started") is not False:
            reasons_blocked.append("annotation_started must be false before official start")
        if manifest.get("first_pass_locked") is not False:
            reasons_blocked.append("first_pass_locked must be false before annotation start")
        if manifest.get("reference_join_enabled") is not False:
            reasons_blocked.append("reference_join_enabled must be false before annotation start")

    is_ready = (len(reasons_blocked) == 0)
    return is_ready, reasons_blocked


def check_annotation_start_readiness():
    print("=" * 70)
    print("NLP v2 Gate B.3 Annotation-Start QA Gatekeeper")
    print("=" * 70)

    is_ready, reasons_blocked = evaluate_annotation_start_readiness()

    if not is_ready:
        print("\nANNOTATION-START QA RESULT:")
        print("STATUS: BLOCKED / NOT READY")
        print(f"\nReason(s) Blocked ({len(reasons_blocked)}):")
        for r in reasons_blocked:
            print(f"  - {r}")
        if reasons_blocked == ["MODEL_G benchmark execution not authorized"]:
            print("\n(This block is EXPECTED: MODEL_G is execution-ready but benchmark execution is NOT authorized.)")
        else:
            print("\n(This block is EXPECTED prior to sterile workspace execution readiness verification.)")
        print("=" * 70)
        sys.exit(1)
    else:
        print("\nANNOTATION-START QA RESULT:")
        print("STATUS: READY FOR ANNOTATION EXECUTION")
        print("All model configurations and prompt hashes verified frozen.")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    check_annotation_start_readiness()
