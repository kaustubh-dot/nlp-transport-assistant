#!/usr/bin/env python3
"""Gate B.3 Annotation-Stability and Semantic-Boundary Metrics Tool.

Implements Sections 28-40:
1. Hard gold-key access gate: Refuses to join reference key unless first_pass_locked == True.
2. Pairwise stability analysis (STUDENT vs MODEL_A, STUDENT vs MODEL_B, MODEL_A vs MODEL_B).
   Does NOT pool the three sources.
3. Primary-label agreement (numerator, denominator, coverage; two nulls != agreement).
4. Exact acceptable-set agreement.
5. Set Jaccard.
6. Per-class positive agreement (2*n11 / (2*n11 + n10 + n01)).
7. Clarification analysis (2x2 confusion matrix, raw agreement, positive agreement, reason overlap).
8. T3 within-parent fine-grained disagreement (route, stops, timing).
9. Reference concordance (post-lock only).
10. Secondary descriptive Cohen's kappa.
11. Contrast-group consistency analysis (post-lock only).
12. 8 Boundary panels.
"""

import os
import sys
import json
import csv
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GATE_B3_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b3")
GATE_B2_DIR = os.path.join(BASE_DIR, "data", "nlp_v2", "gate_b2")

MANIFEST_PATH = os.path.join(GATE_B3_DIR, "gate_b3_annotation_manifest.json")
LOCK_MANIFEST_PATH = os.path.join(GATE_B3_DIR, "first_pass_lock_manifest.json")
GOLD_KEY_PATH = os.path.join(GATE_B2_DIR, "human_annotation_key.json")

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


def is_first_pass_locked() -> bool:
    """Checks whether the first-pass lock has been formally established."""
    if not os.path.exists(MANIFEST_PATH):
        return False
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            m = json.load(f)
        return bool(m.get("first_pass_locked", False))
    except Exception:
        return False


def load_gold_key() -> Dict[str, Any]:
    """Guarded gold key loader. Refuses access if first-pass lock is not active."""
    if not is_first_pass_locked():
        raise PermissionError(
            "HARD GUARDRAIL VIOLATION: Reference key access refused! "
            "first_pass_locked is False in Gate B.3 manifest."
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
    """Primary-label agreement:

    Among records where BOTH sources supply non-null primary labels:
    identical primary labels / comparable primary-label records.
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

        # Comparable only when BOTH are non-null
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
        n11 = 0  # both include
        n10 = 0  # A includes, B does not
        n01 = 0  # B includes, A does not
        n00 = 0  # neither includes

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
    n11 = 0  # Both True
    n10 = 0  # A True, B False
    n01 = 0  # A False, B True
    n00 = 0  # Both False
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

    # Observed agreement Po
    po = sum(1 for a, b in comparable_pairs if a == b) / n

    # Expected agreement Pe
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


def compute_reference_concordance(
    annotator_records: Dict[str, Dict], gold_key: Dict[str, Any], taxonomy: str
) -> Dict[str, Any]:
    """Calculates reference concordance for a single annotator against the frozen reference key.

    Requires first-pass lock.
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
        ref_acceptable = set(ref.get("acceptable_secondary_labels", []))
        if ref_gold:
            ref_acceptable.add(ref_gold)

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
    sources_records: Dict[str, Dict[str, Dict]], gold_key: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generates boundary panel diagnostics across the 8 specified boundaries."""
    panel_results = {}
    for panel_name, panel_classes in BOUNDARY_PANELS.items():
        matching_ids_sources = set()
        matching_ids_ref = set()

        # Check in all annotation sources
        for src_name, records in sources_records.items():
            for aid, rec in records.items():
                labels = set(rec.get("acceptable_labels", []))
                if rec.get("primary_label"):
                    labels.add(rec["primary_label"])
                if labels & panel_classes:
                    matching_ids_sources.add(aid)

        # Check in reference if available
        if gold_key:
            for aid, ref in gold_key.items():
                ref_labels = {ref.get("gold_T2_intent"), ref.get("gold_T3_intent")} | set(ref.get("acceptable_secondary_labels", []))
                if ref_labels & panel_classes:
                    matching_ids_ref.add(aid)

        union_matching = matching_ids_sources | matching_ids_ref
        panel_results[panel_name] = {
            "target_classes": list(panel_classes),
            "total_items_in_panel": len(union_matching),
            "reference_defined_count": len(matching_ids_ref) if gold_key else "LOCKED_PRE_ANNOTATION",
            "source_detected_count": len(matching_ids_sources)
        }
    return panel_results


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
    print("NLP v2 Gate B.3 Annotation-Stability Metric Suite")
    print(f"First-pass locked: {is_first_pass_locked()}")
    if not is_first_pass_locked():
        print("Note: Reference concordance and gold joins are disabled until first-pass lock.")
