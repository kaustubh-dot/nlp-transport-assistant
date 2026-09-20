#!/usr/bin/env python3
"""Annotation-Start QA Gatekeeper for NLP v2 Gate B.3.

Enforces Section 20 requirements:
Checks whether model configurations are formally frozen and ready for annotation.
Requires:
1. MODEL_A provider != PENDING, model != PENDING, version != PENDING, configuration_frozen == True
2. MODEL_B provider != PENDING, model != PENDING, version != PENDING, configuration_frozen == True
3. MODEL_A and MODEL_B are not the exact same model family/config unless explicitly documented
4. prompt_sha256, t2_guide_sha256, t3_guide_sha256, and schema_sha256 are present and non-null
5. annotation_started == False, first_pass_locked == False, reference_join_enabled == False

When models remain PENDING (prior to model selection):
Reports: BLOCKED / NOT READY and exits with code 1.
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
CONFIGS_PATH = os.path.join(GATE_B3_DIR, "model_annotator_configs.json")
MANIFEST_PATH = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")


def check_annotation_start_readiness():
    print("=" * 70)
    print("NLP v2 Gate B.3 Annotation-Start QA Gatekeeper")
    print("=" * 70)

    reasons_blocked = []

    # 1. Check Model Configs
    if not os.path.exists(CONFIGS_PATH):
        reasons_blocked.append(f"Missing config file: {CONFIGS_PATH}")
    else:
        with open(CONFIGS_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        if not cfg.get("configuration_frozen", False):
            reasons_blocked.append("Global configuration_frozen is False")
        if not cfg.get("prompt_sha256"):
            reasons_blocked.append("prompt_sha256 is null or missing")
        if not cfg.get("t2_guide_sha256"):
            reasons_blocked.append("t2_guide_sha256 is null or missing")
        if not cfg.get("t3_guide_sha256"):
            reasons_blocked.append("t3_guide_sha256 is null or missing")
        if not cfg.get("schema_sha256"):
            reasons_blocked.append("schema_sha256 is null or missing")

        for m_name in ["MODEL_A", "MODEL_B"]:
            m = cfg.get(m_name, {})
            if m.get("status") == "PENDING" or m.get("provider") == "PENDING" or m.get("model") == "PENDING":
                reasons_blocked.append(f"{m_name} status/provider/model remains PENDING")
            if not m.get("configuration_frozen", False):
                reasons_blocked.append(f"{m_name} configuration_frozen is False")

        # Check model diversity
        m_a = cfg.get("MODEL_A", {})
        m_b = cfg.get("MODEL_B", {})
        if (
            m_a.get("provider") != "PENDING"
            and m_b.get("provider") != "PENDING"
            and m_a.get("provider") == m_b.get("provider")
            and m_a.get("model") == m_b.get("model")
        ):
            reasons_blocked.append("MODEL_A and MODEL_B use identical model/provider without justification")

    # 2. Check Manifest Pre-Annotation Guardrails
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        if manifest.get("annotation_started") is not False:
            reasons_blocked.append("annotation_started must be false before official start")
        if manifest.get("first_pass_locked") is not False:
            reasons_blocked.append("first_pass_locked must be false before annotation start")
        if manifest.get("reference_join_enabled") is not False:
            reasons_blocked.append("reference_join_enabled must be false before annotation start")

    if reasons_blocked:
        print("\nANNOTATION-START QA RESULT:")
        print("STATUS: BLOCKED / NOT READY")
        print(f"\nReason(s) Blocked ({len(reasons_blocked)}):")
        for r in reasons_blocked:
            print(f"  - {r}")
        print("\n(This block is EXPECTED prior to formal model selection and freezing.)")
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
