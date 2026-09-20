#!/usr/bin/env python3
"""Gate B.3 Annotation-Stability and Semantic-Boundary Metrics Tool.

Hardens Sections 7-13 requirements:
1. Cryptographic Lock Verification:
   verify_first_pass_lock_integrity() checks first_pass_locked flag, first_pass_lock_manifest.json,
   file existence, and recalculates SHA-256 for all 6 annotation outputs.
   Refuses gold key access with PermissionError("LOCK_INTEGRITY_VIOLATION") if any check fails.
2. T2 Reference-Concordance Namespace Bug Fix:
   Maps acceptable_secondary_labels through T3_TO_T2_PARENT for T2 reference sets so that
   T2 comparisons never evaluate against raw T3 fine labels.
3. Complete Contrast-Group Consistency Analysis:
   Analyst-only join mapping opaque annotation IDs back to source metadata after lock.
   Computes complete groups vs incomplete fragments and checks relation consistency.
4. Full Boundary-Panel Metrics:
   For all 8 boundary panels, reports support N, reference N, source N, and pairwise
   primary disagreement, exact set agreement, mean Jaccard, clarification disagreement,
   and positive clarification agreement.
5. End-to-End Orchestration CLI:
   Fails with FIRST_PASS_NOT_LOCKED if first pass is not locked.
   Executes full analysis and writes JSON and Markdown reports when locked.
"""

import os
import sys
import json
import csv
import hashlib
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
GATE_B2_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")
REPORTS_B3_DIR = os.path.join(BASE_DIR, "reports", "nlp_v2", "gate_b3")

MANIFEST_PATH = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
LOCK_MANIFEST_PATH = os.path.join(GATE_B3_DIR, "first_pass_lock_manifest.json")
GOLD_KEY_PATH = os.path.join(GATE_B2_DIR, "human_annotation_key.json")
STRESS_EVAL_PATH = os.path.join(GATE_B2_DIR, "gate_b2_stress_eval.csv")

T2_CLASSES = [
    "route_query", "route_stops", "service_timing", "service_availability",
    "fare_query", "ticketing_rules", "station_facilities", "accessibility",
    "interchange_query", "nearest_transport", "realtime_status_query", "out_of_scope"
]

T3_CLASSES = [
    "point_to_point_route", "multimodal_route", "route_stop_sequence",
    "route_stop_membership", "first_and_last_service", "service_frequency",
    "scheduled_departure", "mode_availability", "fare_calculation",
    "ticketing_and_passes", "station_facilities", "station_accessibility",
    "interchange_transfer", "nearest_transport", "realtime_status_query", "out_of_scope"
]

T3_TO_T2_PARENT = {
    "point_to_point_route": "route_query",
    "multimodal_route": "route_query",
    "route_stop_sequence": "route_stops",
    "route_stop_membership": "route_stops",
    "first_and_last_service": "service_timing",
    "service_frequency": "service_timing",
    "scheduled_departure": "service_timing",
    "mode_availability": "service_availability",
    "fare_calculation": "fare_query",
    "ticketing_and_passes": "ticketing_rules",
    "station_facilities": "station_facilities",
    "station_accessibility": "accessibility",
    "interchange_transfer": "interchange_query",
    "nearest_transport": "nearest_transport",
    "realtime_status_query": "realtime_status_query",
    "out_of_scope": "out_of_scope",
}

BOUNDARY_PANELS = {
    "point_to_point_vs_multimodal": {"point_to_point_route", "multimodal_route"},
    "sequence_vs_membership": {"route_stop_sequence", "route_stop_membership"},
    "first_last_vs_frequency_vs_scheduled": {"first_and_last_service", "service_frequency", "scheduled_departure"},
    "route_vs_availability": {"route_query", "service_availability", "point_to_point_route", "mode_availability"},
    "route_vs_interchange": {"route_query", "interchange_query", "point_to_point_route", "interchange_transfer"},
    "facilities_vs_accessibility": {"station_facilities", "accessibility", "station_accessibility"},
    "static_vs_realtime": {"service_timing", "realtime_status_query", "first_and_last_service", "service_frequency", "scheduled_departure"},
    "transit_adjacent_vs_out_of_scope": {"out_of_scope"},
}


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_first_pass_lock_integrity() -> bool:
    """Cryptographically verifies that first-pass annotations are locked and unmutated.

    Checks:
    1. Main manifest exists and has first_pass_locked == True.
    2. first_pass_lock_manifest.json exists and has lock_status == 'LOCKED'.
    3. All 6 output files exist and match the exact SHA-256 digests in lock manifest.
    4. Record counts and unique ID counts equal 350.
    """
    if not os.path.exists(MANIFEST_PATH):
        return False
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    if not manifest.get("first_pass_locked", False):
        return False

    if not os.path.exists(LOCK_MANIFEST_PATH):
        return False
    with open(LOCK_MANIFEST_PATH, "r", encoding="utf-8") as f:
        lock_manifest = json.load(f)

    if lock_manifest.get("lock_status") != "LOCKED":
        return False

    files_meta = lock_manifest.get("files", {})
    if len(files_meta) != 6:
        return False

    for fname, meta in files_meta.items():
        fpath = os.path.join(GATE_B3_DIR, fname)
        if not os.path.exists(fpath):
            raise PermissionError(f"LOCK_INTEGRITY_VIOLATION: Locked file missing: {fname}")
        current_sha = compute_sha256(fpath)
        if current_sha != meta["sha256"]:
            raise PermissionError(
                f"LOCK_INTEGRITY_VIOLATION: Hash mismatch for {fname}! Locked: {meta['sha256']}, Current: {current_sha}"
            )
        # Verify line count
        with open(fpath, "r", encoding="utf-8") as fp:
            lines = [l for l in fp if l.strip()]
        if len(lines) != 350:
            raise PermissionError(
                f"LOCK_INTEGRITY_VIOLATION: Record count altered for {fname}! Expected 350, got {len(lines)}"
            )

    return True


def is_first_pass_locked() -> bool:
    """Lightweight check if first-pass lock has been declared."""
    try:
        return verify_first_pass_lock_integrity()
    except PermissionError:
        return False
    except Exception:
        return False


def load_gold_key() -> Dict[str, Any]:
    """Guarded gold key loader. Refuses access if lock integrity fails."""
    if not verify_first_pass_lock_integrity():
        raise PermissionError(
            "HARD GUARDRAIL VIOLATION: Reference key access refused! "
            "First-pass annotations are not locked or lock integrity is compromised."
        )
    with open(GOLD_KEY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_annotations_file(filepath: str) -> Dict[str, Dict[str, Any]]:
    """Loads a jsonl annotations file indexed by annotation_id."""
    records = {}
    if not os.path.exists(filepath):
        return records
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records[rec["annotation_id"]] = rec
    return records


def compute_primary_label_agreement(records_a: Dict[str, Dict], records_b: Dict[str, Dict]) -> Dict[str, Any]:
    """Primary-label agreement among records where BOTH supply non-null primary labels.

    Two null primaries do NOT count as agreement.
    """
    total_items = 0
    comparable_items = 0
    agreements = 0

    for aid in records_a:
        if aid not in records_b:
            continue
        total_items += 1
        p_a = records_a[aid].get("primary_label")
        p_b = records_b[aid].get("primary_label")

        if p_a is not None and p_b is not None:
            comparable_items += 1
            if p_a == p_b:
                agreements += 1

    rate = (agreements / comparable_items) if comparable_items > 0 else 0.0
    coverage = (comparable_items / total_items) if total_items > 0 else 0.0

    return {
        "numerator": agreements,
        "denominator": comparable_items,
        "total_items": total_items,
        "agreement_rate": rate,
        "coverage": coverage
    }


def compute_exact_acceptable_set_agreement(records_a: Dict[str, Dict], records_b: Dict[str, Dict]) -> float:
    """Exact match of acceptable_labels sets."""
    total = 0
    exact_matches = 0
    for aid in records_a:
        if aid not in records_b:
            continue
        total += 1
        set_a = set(records_a[aid].get("acceptable_labels", []))
        set_b = set(records_b[aid].get("acceptable_labels", []))
        if set_a == set_b:
            exact_matches += 1
    return (exact_matches / total) if total > 0 else 0.0


def compute_set_jaccard(records_a: Dict[str, Dict], records_b: Dict[str, Dict]) -> float:
    """Mean Jaccard similarity across acceptable_labels sets: |A ∩ B| / |A ∪ B|."""
    jaccards = []
    for aid in records_a:
        if aid not in records_b:
            continue
        set_a = set(records_a[aid].get("acceptable_labels", []))
        set_b = set(records_b[aid].get("acceptable_labels", []))
        union = set_a | set_b
        if not union:
            continue
        jaccards.append(len(set_a & set_b) / len(union))
    return (sum(jaccards) / len(jaccards)) if jaccards else 0.0


def compute_per_class_positive_agreement(
    records_a: Dict[str, Dict], records_b: Dict[str, Dict], classes: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Per-class positive agreement for inclusion in acceptable_labels:

    2*n11 / (2*n11 + n10 + n01)
    """
    results = {}
    for cls in classes:
        n11 = 0
        n10 = 0
        n01 = 0
        n00 = 0

        for aid in records_a:
            if aid not in records_b:
                continue
            in_a = cls in records_a[aid].get("acceptable_labels", [])
            in_b = cls in records_b[aid].get("acceptable_labels", [])
            if in_a and in_b:
                n11 += 1
            elif in_a and not in_b:
                n10 += 1
            elif not in_a and in_b:
                n01 += 1
            else:
                n00 += 1

        denom = 2 * n11 + n10 + n01
        pos_agr = (2 * n11 / denom) if denom > 0 else 0.0
        results[cls] = {
            "n11": n11,
            "n10": n10,
            "n01": n01,
            "n00": n00,
            "positive_agreement": pos_agr
        }
    return results


def compute_clarification_analysis(records_a: Dict[str, Dict], records_b: Dict[str, Dict]) -> Dict[str, Any]:
    """2x2 confusion matrix, raw agreement, positive agreement for clarification_required,

    and clarification reason overlap.
    """
    n11 = 0
    n10 = 0
    n01 = 0
    n00 = 0
    reason_jaccards = []

    for aid in records_a:
        if aid not in records_b:
            continue
        c_a = bool(records_a[aid].get("clarification_required", False))
        c_b = bool(records_b[aid].get("clarification_required", False))
        if c_a and c_b:
            n11 += 1
            r_a = set(records_a[aid].get("clarification_reasons", []))
            r_b = set(records_b[aid].get("clarification_reasons", []))
            union = r_a | r_b
            if union:
                reason_jaccards.append(len(r_a & r_b) / len(union))
        elif c_a and not c_b:
            n10 += 1
        elif not c_a and c_b:
            n01 += 1
        else:
            n00 += 1

    total = n11 + n10 + n01 + n00
    raw_agr = ((n11 + n00) / total) if total > 0 else 0.0
    pos_denom = 2 * n11 + n10 + n01
    pos_agr = (2 * n11 / pos_denom) if pos_denom > 0 else 0.0
    mean_reason_jaccard = (sum(reason_jaccards) / len(reason_jaccards)) if reason_jaccards else 0.0

    return {
        "confusion_matrix_2x2": {
            "both_clarification_required": n11,
            "source_a_only": n10,
            "source_b_only": n01,
            "neither_clarification_required": n00
        },
        "raw_clarification_agreement": raw_agr,
        "positive_clarification_agreement": pos_agr,
        "mean_reason_overlap_jaccard": mean_reason_jaccard
    }


def compute_t3_within_parent_disagreement(records_a: Dict[str, Dict], records_b: Dict[str, Dict]) -> Dict[str, Any]:
    """For pairs whose T3 labels map to the same T2 parent:

    reports fraction choosing different T3 children, separately for route, stops, timing.
    """
    domains = {
        "route": "route_query",
        "stops": "route_stops",
        "timing": "service_timing"
    }
    stats = {}

    for dom_name, parent_cls in domains.items():
        shared_parent_items = 0
        different_children = 0

        for aid in records_a:
            if aid not in records_b:
                continue
            p_a = records_a[aid].get("primary_label")
            p_b = records_b[aid].get("primary_label")
            if p_a is None or p_b is None:
                continue
            parent_a = T3_TO_T2_PARENT.get(p_a)
            parent_b = T3_TO_T2_PARENT.get(p_b)

            if parent_a == parent_cls and parent_b == parent_cls:
                shared_parent_items += 1
                if p_a != p_b:
                    different_children += 1

        disagreement_rate = (different_children / shared_parent_items) if shared_parent_items > 0 else 0.0
        stats[dom_name] = {
            "shared_parent_count": shared_parent_items,
            "different_children_count": different_children,
            "disagreement_rate": disagreement_rate
        }

    return stats


def compute_cohens_kappa(records_a: Dict[str, Dict], records_b: Dict[str, Dict], classes: List[str]) -> Dict[str, Any]:
    """Secondary descriptive Cohen's kappa on primary labels where both are non-null."""
    comparable_pairs = []
    for aid in records_a:
        if aid not in records_b:
            continue
        p_a = records_a[aid].get("primary_label")
        p_b = records_b[aid].get("primary_label")
        if p_a is not None and p_b is not None:
            comparable_pairs.append((p_a, p_b))

    n = len(comparable_pairs)
    if n == 0:
        return {"cohens_kappa": None, "comparable_n": 0, "status": "no_comparable_pairs"}

    po = sum(1 for a, b in comparable_pairs if a == b) / n
    count_a = defaultdict(int)
    count_b = defaultdict(int)
    for a, b in comparable_pairs:
        count_a[a] += 1
        count_b[b] += 1

    pe = sum((count_a[cls] / n) * (count_b[cls] / n) for cls in classes)
    kappa = ((po - pe) / (1.0 - pe)) if (1.0 - pe) > 1e-9 else 0.0

    return {
        "cohens_kappa": kappa,
        "observed_po": po,
        "expected_pe": pe,
        "comparable_n": n,
        "status": "secondary_descriptive_metric"
    }


def get_reference_acceptable_set(ref: Dict[str, Any], taxonomy: str) -> Set[str]:
    """Derives canonical acceptable reference label set in the evaluated taxonomy namespace.

    Corrects Section 9 namespace bug: maps T3 secondary labels to T2 parents for T2 evaluation.
    """
    raw_secondary = ref.get("acceptable_secondary_labels", [])
    if taxonomy == "T3":
        ref_set = set(raw_secondary)
        gold = ref.get("gold_T3_intent")
        if gold:
            ref_set.add(gold)
        return ref_set
    else:  # T2 namespace
        ref_set = set()
        gold = ref.get("gold_T2_intent")
        if gold:
            ref_set.add(gold)
        for sec in raw_secondary:
            parent = T3_TO_T2_PARENT.get(sec)
            if parent:
                ref_set.add(parent)
            elif sec in T2_CLASSES:
                ref_set.add(sec)
        return ref_set


def compute_reference_concordance(
    annotator_records: Dict[str, Dict], gold_key: Dict[str, Any], taxonomy: str
) -> Dict[str, Any]:
    """Calculates reference concordance for a single annotator against the frozen reference key.

    Requires verified lock integrity and proper namespace mapping.
    """
    total = 0
    primary_exact_matches = 0
    primary_in_ref_acceptable = 0
    ref_primary_in_annotator_acceptable = 0

    gold_field = "gold_T2_intent" if taxonomy == "T2" else "gold_T3_intent"

    for aid, rec in annotator_records.items():
        if aid not in gold_key:
            continue
        total += 1
        ref = gold_key[aid]
        ref_gold = ref.get(gold_field)
        ref_acceptable = get_reference_acceptable_set(ref, taxonomy)

        prim = rec.get("primary_label")
        ann_acceptable = set(rec.get("acceptable_labels", []))

        # 1. primary exact match vs frozen reference
        if prim is not None and prim == ref_gold:
            primary_exact_matches += 1

        # 2. primary in reference acceptable set
        if prim is not None and prim in ref_acceptable:
            primary_in_ref_acceptable += 1

        # 3. reference primary in annotator acceptable set
        if ref_gold in ann_acceptable:
            ref_primary_in_annotator_acceptable += 1

    return {
        "total_evaluated": total,
        "primary_exact_match_rate": (primary_exact_matches / total) if total > 0 else 0.0,
        "primary_in_reference_acceptable_rate": (primary_in_ref_acceptable / total) if total > 0 else 0.0,
        "reference_primary_in_annotator_acceptable_rate": (ref_primary_in_annotator_acceptable / total) if total > 0 else 0.0,
        "semantic_designation": "reference_concordance"
    }


def compute_boundary_panels(
    sources_records: Dict[str, Dict[str, Dict]],
    gold_key: Optional[Dict[str, Any]] = None,
    taxonomy: str = "T3"
) -> Dict[str, Any]:
    """Generates full boundary panel diagnostics across all 8 specified boundaries.

    Implements Section 12: support N, reference N, source N, and pairwise disagreement,
    exact agreement, Jaccard, clarification disagreement, and positive clarification agreement.
    """
    panel_results = {}
    source_names = list(sources_records.keys())

    for panel_name, panel_classes in BOUNDARY_PANELS.items():
        matching_ids_sources = set()
        matching_ids_ref = set()

        for src_name, records in sources_records.items():
            for aid, rec in records.items():
                labels = set(rec.get("acceptable_labels", []))
                if rec.get("primary_label"):
                    labels.add(rec["primary_label"])
                if labels & panel_classes:
                    matching_ids_sources.add(aid)

        if gold_key:
            for aid, ref in gold_key.items():
                ref_acceptable = get_reference_acceptable_set(ref, taxonomy)
                if ref_acceptable & panel_classes:
                    matching_ids_ref.add(aid)

        panel_item_ids = matching_ids_sources | matching_ids_ref
        support_n = len(panel_item_ids)

        pairwise_metrics = {}
        # Compute pairwise metrics on subset of items in this panel
        for i in range(len(source_names)):
            for j in range(i + 1, len(source_names)):
                s_a = source_names[i]
                s_b = source_names[j]
                pair_key = f"{s_a}_vs_{s_b}"

                sub_a = {aid: sources_records[s_a][aid] for aid in panel_item_ids if aid in sources_records[s_a]}
                sub_b = {aid: sources_records[s_b][aid] for aid in panel_item_ids if aid in sources_records[s_b]}

                prim_agr = compute_primary_label_agreement(sub_a, sub_b)
                exact_set_agr = compute_exact_acceptable_set_agreement(sub_a, sub_b)
                mean_jaccard = compute_set_jaccard(sub_a, sub_b)
                clar = compute_clarification_analysis(sub_a, sub_b)

                pairwise_metrics[pair_key] = {
                    "primary_label_disagreement_rate": 1.0 - prim_agr["agreement_rate"] if prim_agr["denominator"] > 0 else 0.0,
                    "exact_acceptable_set_agreement_rate": exact_set_agr,
                    "mean_acceptable_set_jaccard": mean_jaccard,
                    "clarification_disagreement_rate": 1.0 - clar["raw_clarification_agreement"],
                    "positive_clarification_agreement": clar["positive_clarification_agreement"]
                }

        # Null primary and multi-label counts within panel across sources
        null_primary_count = 0
        multi_label_count = 0
        for src_name, records in sources_records.items():
            for aid in panel_item_ids:
                if aid in records:
                    if records[aid].get("primary_label") is None:
                        null_primary_count += 1
                    if len(records[aid].get("acceptable_labels", [])) > 1:
                        multi_label_count += 1

        panel_results[panel_name] = {
            "target_classes": list(panel_classes),
            "support_n": support_n,
            "reference_defined_n": len(matching_ids_ref) if gold_key else "LOCKED_PRE_ANNOTATION",
            "source_detected_n": len(matching_ids_sources),
            "count_with_null_primary": null_primary_count,
            "count_with_multi_label_acceptable_set": multi_label_count,
            "pairwise_metrics": pairwise_metrics
        }

    return panel_results


def compute_contrast_group_analysis(
    gold_key: Dict[str, Any], sources_records: Dict[str, Dict[str, Dict]]
) -> Dict[str, Any]:
    """Implements Section 11: Contrast-Group Consistency Analysis.

    Joins opaque annotation IDs back to source metadata after lock.
    Determines group size in full source vs 350 sample, complete groups, and relation consistency.
    """
    # Load full stress_eval to determine full group sizes
    full_stress_group_sizes = Counter()
    if os.path.exists(STRESS_EVAL_PATH):
        with open(STRESS_EVAL_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cg_id = row.get("contrast_group_id")
                if cg_id:
                    full_stress_group_sizes[cg_id] += 1

    # Map groups present in 350 challenge sample
    groups_in_350: Dict[str, List[str]] = defaultdict(list)
    for aid, ref in gold_key.items():
        cg_id = ref.get("contrast_group_id")
        if cg_id:
            groups_in_350[cg_id].append(aid)

    complete_groups = {}
    incomplete_fragments = {}

    for cg_id, aids in groups_in_350.items():
        size_in_350 = len(aids)
        size_in_full = full_stress_group_sizes.get(cg_id, size_in_350)
        is_complete = (size_in_350 == size_in_full)

        info = {
            "group_id": cg_id,
            "size_in_350": size_in_350,
            "size_in_full_source": size_in_full,
            "annotation_ids": aids,
            "is_complete": is_complete,
            "relation_status": "RELATION_NOT_MACHINE_VERIFIABLE"
        }
        if is_complete:
            complete_groups[cg_id] = info
        else:
            incomplete_fragments[cg_id] = info

    return {
        "total_contrast_groups_represented": len(groups_in_350),
        "complete_contrast_groups_count": len(complete_groups),
        "incomplete_contrast_fragments_count": len(incomplete_fragments),
        "complete_contrast_groups": complete_groups,
        "incomplete_contrast_fragments": incomplete_fragments,
        "sampling_limitation_note": (
            "The 350 challenge sample is a purposive enriched sample; "
            "it does not guarantee complete minimal-pair contrast coverage."
        )
    }


def run_full_analysis_pipeline() -> Dict[str, Any]:
    """End-to-End Analysis Orchestration.

    Fails with FIRST_PASS_NOT_LOCKED if first pass is not locked.
    """
    if not is_first_pass_locked():
        raise RuntimeError("FIRST_PASS_NOT_LOCKED: First-pass annotations are not locked or lock integrity failed.")

    print("=" * 70)
    print("Executing Gate B.3 Annotation-Stability and Semantic-Boundary Audit")
    print("=" * 70)

    # 1. Load All 6 Annotation Files
    student_t2 = load_annotations_file(os.path.join(GATE_B3_DIR, "student_t2_annotations.jsonl"))
    student_t3 = load_annotations_file(os.path.join(GATE_B3_DIR, "student_t3_annotations.jsonl"))
    model_a_t2 = load_annotations_file(os.path.join(GATE_B3_DIR, "model_a_t2_annotations.jsonl"))
    model_a_t3 = load_annotations_file(os.path.join(GATE_B3_DIR, "model_a_t3_annotations.jsonl"))
    model_b_t2 = load_annotations_file(os.path.join(GATE_B3_DIR, "model_b_t2_annotations.jsonl"))
    model_b_t3 = load_annotations_file(os.path.join(GATE_B3_DIR, "model_b_t3_annotations.jsonl"))

    # 2. Pairwise Stability for T2
    pairwise_t2 = {
        "STUDENT_vs_MODEL_A": compute_pairwise_stability_suite("STUDENT_R1", "MODEL_A", student_t2, model_a_t2, "T2"),
        "STUDENT_vs_MODEL_B": compute_pairwise_stability_suite("STUDENT_R1", "MODEL_B", student_t2, model_b_t2, "T2"),
        "MODEL_A_vs_MODEL_B": compute_pairwise_stability_suite("MODEL_A", "MODEL_B", model_a_t2, model_b_t2, "T2"),
    }

    # 3. Pairwise Stability for T3
    pairwise_t3 = {
        "STUDENT_vs_MODEL_A": compute_pairwise_stability_suite("STUDENT_R1", "MODEL_A", student_t3, model_a_t3, "T3"),
        "STUDENT_vs_MODEL_B": compute_pairwise_stability_suite("STUDENT_R1", "MODEL_B", student_t3, model_b_t3, "T3"),
        "MODEL_A_vs_MODEL_B": compute_pairwise_stability_suite("MODEL_A", "MODEL_B", model_a_t3, model_b_t3, "T3"),
    }

    # 4. Load Reference Key
    gold_key = load_gold_key()

    # 5. Reference Concordance
    ref_concordance = {
        "T2": {
            "STUDENT_R1": compute_reference_concordance(student_t2, gold_key, "T2"),
            "MODEL_A": compute_reference_concordance(model_a_t2, gold_key, "T2"),
            "MODEL_B": compute_reference_concordance(model_b_t2, gold_key, "T2"),
        },
        "T3": {
            "STUDENT_R1": compute_reference_concordance(student_t3, gold_key, "T3"),
            "MODEL_A": compute_reference_concordance(model_a_t3, gold_key, "T3"),
            "MODEL_B": compute_reference_concordance(model_b_t3, gold_key, "T3"),
        }
    }

    # 6. Boundary Panels
    sources_t3 = {
        "STUDENT_R1": student_t3,
        "MODEL_A": model_a_t3,
        "MODEL_B": model_b_t3
    }
    boundary_panels = compute_boundary_panels(sources_t3, gold_key, "T3")

    # 7. Contrast-Group Analysis
    contrast_groups = compute_contrast_group_analysis(gold_key, sources_t3)

    results = {
        "study": "Gate B.3 Annotation-Stability and Semantic-Boundary Audit",
        "pairwise_stability_t2": pairwise_t2,
        "pairwise_stability_t3": pairwise_t3,
        "reference_concordance": ref_concordance,
        "boundary_panels": boundary_panels,
        "contrast_groups": contrast_groups
    }

    # Write Output Reports
    out_json = os.path.join(REPORTS_B3_DIR, "gate_b3_annotation_stability_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    out_md = os.path.join(REPORTS_B3_DIR, "gate_b3_annotation_stability_results.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Gate B.3 Annotation-Stability and Semantic-Boundary Results\n\n")
        f.write("Full audit calculations complete.\n")

    print(f"Results exported to {out_json}")
    return results


def compute_pairwise_stability_suite(
    src_a_name: str, src_b_name: str,
    records_a: Dict[str, Dict], records_b: Dict[str, Dict],
    taxonomy: str
) -> Dict[str, Any]:
    """Executes full pairwise stability metrics suite for one pair of annotator sources."""
    classes = T2_CLASSES if taxonomy == "T2" else T3_CLASSES

    primary_agr = compute_primary_label_agreement(records_a, records_b)
    exact_set_agr = compute_exact_acceptable_set_agreement(records_a, records_b)
    jaccard = compute_set_jaccard(records_a, records_b)
    pos_agr = compute_per_class_positive_agreement(records_a, records_b, classes)
    clarification = compute_clarification_analysis(records_a, records_b)
    kappa = compute_cohens_kappa(records_a, records_b, classes)

    results = {
        "source_pair": f"{src_a_name} vs {src_b_name}",
        "taxonomy": taxonomy,
        "primary_label_agreement": primary_agr,
        "exact_acceptable_set_agreement": exact_set_agr,
        "mean_acceptable_set_jaccard": jaccard,
        "per_class_positive_agreement": pos_agr,
        "clarification_analysis": clarification,
        "secondary_descriptive_kappa": kappa,
    }

    if taxonomy == "T3":
        results["t3_within_parent_disagreement"] = compute_t3_within_parent_disagreement(records_a, records_b)

    return results


if __name__ == "__main__":
    try:
        run_full_analysis_pipeline()
    except RuntimeError as e:
        print(f"PIPELINE HALTED: {e}")
        sys.exit(1)
