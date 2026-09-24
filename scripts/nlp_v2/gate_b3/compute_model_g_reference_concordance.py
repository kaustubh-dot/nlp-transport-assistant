#!/usr/bin/env python3

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

GATE_B3 = ROOT / "data/nlp_v2/gate_b3"
GATE_B2 = ROOT / "data/nlp_v2/gate_b2"
REPORT_DIR = ROOT / "reports/nlp_v2/gate_b3"

MANIFEST = GATE_B3 / "gate_b3_annotation_manifest.json"
LOCK = GATE_B3 / "first_pass_lock_manifest.json"
REFERENCE = GATE_B2 / "human_annotation_key.json"

MODEL_FILES = {
    "T2": GATE_B3 / "model_g_t2_annotations.jsonl",
    "T3": GATE_B3 / "model_g_t3_annotations.jsonl",
}

T2_CLASSES = [
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
]

T3_CLASSES = [
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
]

T3_TO_T2 = {
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


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    records = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            aid = rec["annotation_id"]
            if aid in records:
                raise RuntimeError(f"duplicate annotation_id: {aid}")
            records[aid] = rec
    return records


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def reference_set(ref, taxonomy):
    secondary = ref.get("acceptable_secondary_labels", [])

    if taxonomy == "T3":
        out = set(secondary)
        if ref.get("gold_T3_intent"):
            out.add(ref["gold_T3_intent"])
        return out

    out = set()

    if ref.get("gold_T2_intent"):
        out.add(ref["gold_T2_intent"])

    for label in secondary:
        if label in T3_TO_T2:
            out.add(T3_TO_T2[label])
        elif label in T2_CLASSES:
            out.add(label)

    return out


def verify_lock():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))

    assert manifest["first_pass_locked"] is True
    assert manifest["reference_join_enabled"] is True
    assert manifest["primary_annotation_sources"] == ["MODEL_G"]
    assert lock["lock_status"] == "LOCKED"

    expected = {
        "model_g_t2_annotations.jsonl",
        "model_g_t3_annotations.jsonl",
    }

    assert set(lock["files"]) == expected

    for name, meta in lock["files"].items():
        path = GATE_B3 / name

        if sha256(path) != meta["sha256"]:
            raise RuntimeError(f"LOCK_INTEGRITY_VIOLATION: {name}")

        count = sum(1 for x in path.open(encoding="utf-8") if x.strip())

        if count != 350:
            raise RuntimeError(
                f"LOCK_INTEGRITY_VIOLATION: {name} has {count} records"
            )


def analyze(taxonomy, model, reference):
    gold_field = "gold_T2_intent" if taxonomy == "T2" else "gold_T3_intent"
    classes = T2_CLASSES if taxonomy == "T2" else T3_CLASSES

    exact = 0
    model_primary_in_ref = 0
    ref_primary_in_model = 0
    set_exact = 0
    jaccards = []
    clarification_match = 0

    null_primary = 0
    multi_label = 0

    confusion = defaultdict(Counter)
    disagreements = []

    per_class = {
        c: {
            "reference_primary_n": 0,
            "model_primary_n": 0,
            "primary_exact_n": 0,
        }
        for c in classes
    }

    for aid in sorted(model):
        if aid not in reference:
            raise RuntimeError(f"{aid} missing from reference key")

        rec = model[aid]
        ref = reference[aid]

        mp = rec.get("primary_label")
        rp = ref.get(gold_field)

        ma = set(rec.get("acceptable_labels", []))
        ra = reference_set(ref, taxonomy)

        mc = bool(rec.get("clarification_required", False))
        rc = parse_bool(ref.get("clarification_required", False))

        if mp is None:
            null_primary += 1
        else:
            per_class[mp]["model_primary_n"] += 1

        if len(ma) > 1:
            multi_label += 1

        if rp in per_class:
            per_class[rp]["reference_primary_n"] += 1

        if mp == rp:
            exact += 1
            if rp in per_class:
                per_class[rp]["primary_exact_n"] += 1

        if mp is not None and mp in ra:
            model_primary_in_ref += 1

        if rp in ma:
            ref_primary_in_model += 1

        if ma == ra:
            set_exact += 1

        union = ma | ra
        jaccard = len(ma & ra) / len(union) if union else 1.0
        jaccards.append(jaccard)

        if mc == rc:
            clarification_match += 1

        confusion[str(rp)][str(mp)] += 1

        flags = []

        if mp != rp:
            flags.append("primary_mismatch")
        if ma != ra:
            flags.append("acceptable_set_mismatch")
        if mc != rc:
            flags.append("clarification_mismatch")

        if flags:
            disagreements.append(
                {
                    "annotation_id": aid,
                    "taxonomy": taxonomy,
                    "query": ref.get("query", ""),
                    "reference_primary": rp,
                    "model_primary": mp,
                    "reference_acceptable": "|".join(sorted(ra)),
                    "model_acceptable": "|".join(sorted(ma)),
                    "reference_clarification": rc,
                    "model_clarification": mc,
                    "model_clarification_reasons": "|".join(
                        rec.get("clarification_reasons", [])
                    ),
                    "model_brief_justification": rec.get(
                        "brief_justification", ""
                    ),
                    "disagreement_flags": "|".join(flags),
                    "disagreement_score": len(flags),
                }
            )

    total = len(model)

    if total != 350:
        raise RuntimeError(f"{taxonomy}: expected 350 records, got {total}")

    for c in classes:
        n = per_class[c]["reference_primary_n"]
        per_class[c]["primary_exact_rate_within_reference_class"] = (
            per_class[c]["primary_exact_n"] / n if n else None
        )

    return {
        "taxonomy": taxonomy,
        "total_evaluated": total,
        "primary_exact_matches": exact,
        "primary_exact_match_rate": exact / total,
        "model_primary_in_reference_acceptable_rate": model_primary_in_ref / total,
        "reference_primary_in_model_acceptable_rate": ref_primary_in_model / total,
        "exact_acceptable_set_match_rate": set_exact / total,
        "mean_acceptable_set_jaccard": sum(jaccards) / len(jaccards),
        "clarification_agreement_rate": clarification_match / total,
        "model_null_primary_count": null_primary,
        "model_multi_label_count": multi_label,
        "primary_mismatch_count": total - exact,
        "per_class": per_class,
        "confusion_matrix": {
            k: dict(v) for k, v in confusion.items()
        },
        "design_note": (
            "Descriptive MODEL_G-reference concordance on the fixed purposive "
            "Gate B.3 challenge sample. No population confidence intervals or "
            "significance tests are reported."
        ),
    }, disagreements


def main():
    verify_lock()

    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))

    if len(reference) != 350:
        raise RuntimeError(
            f"reference key expected 350 records, got {len(reference)}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = {}
    all_disagreements = []

    for taxonomy, path in MODEL_FILES.items():
        model = load_jsonl(path)

        result, disagreements = analyze(
            taxonomy, model, reference
        )

        all_results[taxonomy] = result
        all_disagreements.extend(disagreements)

    result_path = REPORT_DIR / "model_g_reference_concordance.json"
    result_path.write_text(
        json.dumps(all_results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    csv_path = REPORT_DIR / "model_g_reference_disagreements.csv"

    fields = [
        "annotation_id",
        "taxonomy",
        "query",
        "reference_primary",
        "model_primary",
        "reference_acceptable",
        "model_acceptable",
        "reference_clarification",
        "model_clarification",
        "model_clarification_reasons",
        "model_brief_justification",
        "disagreement_flags",
        "disagreement_score",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_disagreements)

    md = [
        "# Gate B.3 MODEL_G–Reference Concordance",
        "",
        "Fixed purposive challenge sample; descriptive metrics only.",
        "",
    ]

    for taxonomy in ("T2", "T3"):
        r = all_results[taxonomy]

        md.extend(
            [
                f"## {taxonomy}",
                "",
                f"- N: {r['total_evaluated']}",
                f"- Primary exact: {r['primary_exact_match_rate']:.4f}",
                (
                    "- MODEL_G primary in reference acceptable set: "
                    f"{r['model_primary_in_reference_acceptable_rate']:.4f}"
                ),
                (
                    "- Reference primary in MODEL_G acceptable set: "
                    f"{r['reference_primary_in_model_acceptable_rate']:.4f}"
                ),
                (
                    "- Exact acceptable-set match: "
                    f"{r['exact_acceptable_set_match_rate']:.4f}"
                ),
                (
                    "- Mean acceptable-set Jaccard: "
                    f"{r['mean_acceptable_set_jaccard']:.4f}"
                ),
                (
                    "- Clarification agreement: "
                    f"{r['clarification_agreement_rate']:.4f}"
                ),
                f"- Primary mismatches: {r['primary_mismatch_count']}",
                f"- Null MODEL_G primaries: {r['model_null_primary_count']}",
                "",
            ]
        )

    md_path = REPORT_DIR / "model_g_reference_concordance.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("=" * 72)
    print("Gate B.3 MODEL_G ↔ Reference Concordance")
    print("=" * 72)

    for taxonomy in ("T2", "T3"):
        r = all_results[taxonomy]
        print()
        print(taxonomy)
        print(f"  N                           : {r['total_evaluated']}")
        print(f"  primary exact               : {r['primary_exact_match_rate']:.4f}")
        print(
            "  model primary in ref set    : "
            f"{r['model_primary_in_reference_acceptable_rate']:.4f}"
        )
        print(
            "  ref primary in model set    : "
            f"{r['reference_primary_in_model_acceptable_rate']:.4f}"
        )
        print(
            "  exact acceptable set        : "
            f"{r['exact_acceptable_set_match_rate']:.4f}"
        )
        print(
            "  mean set Jaccard            : "
            f"{r['mean_acceptable_set_jaccard']:.4f}"
        )
        print(
            "  clarification agreement     : "
            f"{r['clarification_agreement_rate']:.4f}"
        )
        print(f"  primary mismatches          : {r['primary_mismatch_count']}")

    print()
    print(f"Disagreement rows: {len(all_disagreements)}")
    print(f"JSON: {result_path}")
    print(f"CSV : {csv_path}")
    print(f"MD  : {md_path}")


if __name__ == "__main__":
    main()
