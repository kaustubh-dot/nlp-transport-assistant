#!/usr/bin/env python3

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

B2 = ROOT / "data/nlp_v2/gate_b2"
B3 = ROOT / "data/nlp_v2/gate_b3"
SOL = B3 / "sol_expanded_audit"
REPORT = ROOT / "reports/nlp_v2/gate_b3"

BLIND = B2 / "human_annotation_blind.csv"
STRESS = B2 / "gate_b2_stress_eval.csv"
REFERENCE = B2 / "human_annotation_key.json"

MODEL_FILES = {
    "T2": B3 / "model_g_t2_annotations.jsonl",
    "T3": B3 / "model_g_t3_annotations.jsonl",
}

SOL_FILES = {
    "T2": SOL / "sol_expanded_t2_annotations.jsonl",
    "T3": SOL / "sol_expanded_t3_annotations.jsonl",
}

SELECTION_MANIFEST = SOL / "selection_manifest.json"
SOL_OUTPUT_MANIFEST = SOL / "sol_output_manifest.json"
LOCK_MANIFEST = B3 / "first_pass_lock_manifest.json"
GATE_MANIFEST = B3 / "gate_b3_annotation_manifest.json"

GROUP_FIELDS = [
    "language_class",
    "script",
    "code_switch_level",
    "noise_level",
    "noise_type",
    "ambiguity_type",
    "answerability_status",
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
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            aid = r["annotation_id"]
            if aid in out:
                raise RuntimeError(f"Duplicate annotation_id in {path}: {aid}")
            out[aid] = r
    return out


def parse_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() == "true"


def clean(v):
    v = (v or "").strip()
    return v if v else "<EMPTY>"


def ref_acceptable(ref, taxonomy):
    secondary = ref.get("acceptable_secondary_labels", []) or []

    if taxonomy == "T3":
        result = set(secondary)
        result.add(ref["gold_T3_intent"])
        return result

    result = {ref["gold_T2_intent"]}

    for label in secondary:
        if label in T3_TO_T2:
            result.add(T3_TO_T2[label])
        else:
            # Allows already-T2 secondary labels if present.
            result.add(label)

    return result


def verify_frozen_inputs():
    gate = json.loads(GATE_MANIFEST.read_text(encoding="utf-8"))
    assert gate["first_pass_locked"] is True
    assert gate["reference_join_enabled"] is True

    # Verify MODEL_G first-pass lock.
    lock = json.loads(LOCK_MANIFEST.read_text(encoding="utf-8"))

    for filename, meta in lock["files"].items():
        p = B3 / filename
        actual = sha256(p)
        if actual != meta["sha256"]:
            raise RuntimeError(
                f"MODEL_G lock hash mismatch for {filename}: "
                f"{actual} != {meta['sha256']}"
            )

    # Verify Sol output hashes.
    sol_manifest = json.loads(
        SOL_OUTPUT_MANIFEST.read_text(encoding="utf-8")
    )

    for filename, meta in sol_manifest["files"].items():
        p = SOL / filename
        actual = sha256(p)
        if actual != meta["sha256"]:
            raise RuntimeError(
                f"Sol output hash mismatch for {filename}: "
                f"{actual} != {meta['sha256']}"
            )

        count = sum(
            1 for line in p.open(encoding="utf-8")
            if line.strip()
        )
        if count != meta["records"]:
            raise RuntimeError(
                f"Sol record count mismatch for {filename}"
            )

    print("PASS: MODEL_G + Sol frozen hashes verified")


def build_metadata():
    with BLIND.open(encoding="utf-8", newline="") as f:
        blind = {
            r["annotation_id"]: r
            for r in csv.DictReader(f)
        }

    with STRESS.open(encoding="utf-8", newline="") as f:
        stress = {
            r["utterance_id"]: r
            for r in csv.DictReader(f)
        }

    meta = {}

    for aid, b in blind.items():
        utt = b["utterance_id"]

        if utt not in stress:
            raise RuntimeError(
                f"Missing stress metadata for {aid}/{utt}"
            )

        meta[aid] = {
            "annotation_id": aid,
            "utterance_id": utt,
            "query": b["query"],
            **stress[utt],
        }

    return meta


def item_metrics(source, ref, taxonomy):
    sp = source.get("primary_label")
    sa = set(source.get("acceptable_labels", []))

    gold_field = (
        "gold_T2_intent"
        if taxonomy == "T2"
        else "gold_T3_intent"
    )

    rp = ref[gold_field]
    ra = ref_acceptable(ref, taxonomy)

    sc = bool(source.get("clarification_required", False))
    rc = parse_bool(ref.get("clarification_required", False))

    return {
        "primary_exact": int(sp == rp),
        "primary_in_ref_set": int(
            sp is not None and sp in ra
        ),
        "ref_primary_in_source_set": int(rp in sa),
        "acceptable_set_exact": int(sa == ra),
        "clarification_match": int(sc == rc),
        "null_primary": int(sp is None),
    }


def pair_metrics(sol, model):
    return {
        "sol_model_primary_agreement": int(
            sol.get("primary_label") == model.get("primary_label")
        ),
        "sol_model_set_agreement": int(
            set(sol.get("acceptable_labels", []))
            == set(model.get("acceptable_labels", []))
        ),
        "sol_model_clarification_agreement": int(
            bool(sol.get("clarification_required", False))
            == bool(model.get("clarification_required", False))
        ),
    }


def summarize(items):
    n = len(items)

    if n == 0:
        raise RuntimeError("Cannot summarize empty group")

    keys = [
        "sol_primary_exact",
        "model_primary_exact",
        "sol_primary_in_ref_set",
        "model_primary_in_ref_set",
        "sol_ref_primary_in_source_set",
        "model_ref_primary_in_source_set",
        "sol_acceptable_set_exact",
        "model_acceptable_set_exact",
        "sol_clarification_match",
        "model_clarification_match",
        "sol_null_primary",
        "model_null_primary",
        "sol_model_primary_agreement",
        "sol_model_set_agreement",
        "sol_model_clarification_agreement",
    ]

    out = {"n": n}

    for key in keys:
        out[key] = sum(x[key] for x in items) / n

    return out


def pct(x):
    return f"{100*x:.1f}%"


def pp(x):
    return f"{100*x:+.1f} pp"


def main():
    verify_frozen_inputs()

    selection = json.loads(
        SELECTION_MANIFEST.read_text(encoding="utf-8")
    )
    selected_ids = set(selection["selected_annotation_ids"])

    assert len(selected_ids) == 128

    reference = json.loads(
        REFERENCE.read_text(encoding="utf-8")
    )
    metadata = build_metadata()

    all_items = {}

    for taxonomy in ("T2", "T3"):
        sol = load_jsonl(SOL_FILES[taxonomy])
        model = load_jsonl(MODEL_FILES[taxonomy])

        if set(sol) != selected_ids:
            raise RuntimeError(
                f"{taxonomy}: Sol IDs do not match frozen selection"
            )

        missing_model = selected_ids - set(model)
        missing_ref = selected_ids - set(reference)

        if missing_model:
            raise RuntimeError(
                f"{taxonomy}: MODEL_G missing IDs: "
                f"{sorted(missing_model)}"
            )

        if missing_ref:
            raise RuntimeError(
                f"{taxonomy}: reference missing IDs: "
                f"{sorted(missing_ref)}"
            )

        items = []

        for aid in sorted(selected_ids):
            sm = item_metrics(
                sol[aid], reference[aid], taxonomy
            )
            mm = item_metrics(
                model[aid], reference[aid], taxonomy
            )
            pm = pair_metrics(sol[aid], model[aid])

            row = {
                "annotation_id": aid,
                "taxonomy": taxonomy,
                **metadata[aid],
                **{f"sol_{k}": v for k, v in sm.items()},
                **{f"model_{k}": v for k, v in mm.items()},
                **pm,
            }

            items.append(row)

        all_items[taxonomy] = items

    # --------------------------------------------------------------
    # Summary rows
    # --------------------------------------------------------------

    summary_rows = []

    dimensions = [None] + GROUP_FIELDS

    for taxonomy in ("T2", "T3"):
        items = all_items[taxonomy]

        for dimension in dimensions:
            groups = defaultdict(list)

            if dimension is None:
                groups["ALL"] = items
                dimension_name = "overall"
            else:
                dimension_name = dimension

                for r in items:
                    groups[clean(r.get(dimension))].append(r)

            for group, rows in sorted(groups.items()):
                s = summarize(rows)

                summary_rows.append({
                    "taxonomy": taxonomy,
                    "dimension": dimension_name,
                    "group": group,
                    **s,
                })

    REPORT.mkdir(parents=True, exist_ok=True)

    csv_path = REPORT / "sol_expanded_comparison_summary.csv"

    with csv_path.open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(summary_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    # --------------------------------------------------------------
    # Human-readable markdown
    # --------------------------------------------------------------

    overall = {
        r["taxonomy"]: r
        for r in summary_rows
        if r["dimension"] == "overall"
    }

    md = [
        "# Gate B.3 Expanded Sol Audit Comparison",
        "",
        "128 purposively selected frozen challenge queries; "
        "256 Sol judgments.",
        "",
        "Descriptive results only. No population confidence "
        "intervals or significance tests.",
        "",
        "## Overall",
        "",
        "| Source | T2 primary exact | T3 primary exact | T3−T2 | "
        "T2 primary in reference set | T3 primary in reference set |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for source, key in [
        ("GPT-5.6 Sol", "sol"),
        ("MODEL_G", "model"),
    ]:
        t2 = overall["T2"]
        t3 = overall["T3"]

        md.append(
            f"| {source} "
            f"| {pct(t2[f'{key}_primary_exact'])} "
            f"| {pct(t3[f'{key}_primary_exact'])} "
            f"| {pp(t3[f'{key}_primary_exact'] - t2[f'{key}_primary_exact'])} "
            f"| {pct(t2[f'{key}_primary_in_ref_set'])} "
            f"| {pct(t3[f'{key}_primary_in_ref_set'])} |"
        )

    md += [
        "",
        "## Sol–MODEL_G Agreement",
        "",
        "| Taxonomy | Primary agreement | Acceptable-set agreement | "
        "Clarification agreement |",
        "|---|---:|---:|---:|",
    ]

    for taxonomy in ("T2", "T3"):
        r = overall[taxonomy]

        md.append(
            f"| {taxonomy} "
            f"| {pct(r['sol_model_primary_agreement'])} "
            f"| {pct(r['sol_model_set_agreement'])} "
            f"| {pct(r['sol_model_clarification_agreement'])} |"
        )

    md += [
        "",
        "## By Language Class",
        "",
        "| Language | N | Sol T2 | Sol T3 | Sol Δ | "
        "MODEL_G T2 | MODEL_G T3 | MODEL_G Δ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    lang = defaultdict(dict)

    for r in summary_rows:
        if r["dimension"] == "language_class":
            lang[r["group"]][r["taxonomy"]] = r

    for group in sorted(lang):
        if "T2" not in lang[group] or "T3" not in lang[group]:
            continue

        t2 = lang[group]["T2"]
        t3 = lang[group]["T3"]

        md.append(
            f"| {group} "
            f"| {t2['n']} "
            f"| {pct(t2['sol_primary_exact'])} "
            f"| {pct(t3['sol_primary_exact'])} "
            f"| {pp(t3['sol_primary_exact'] - t2['sol_primary_exact'])} "
            f"| {pct(t2['model_primary_exact'])} "
            f"| {pct(t3['model_primary_exact'])} "
            f"| {pp(t3['model_primary_exact'] - t2['model_primary_exact'])} |"
        )

    md_path = REPORT / "sol_expanded_comparison.md"
    md_path.write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    # --------------------------------------------------------------
    # Console summary
    # --------------------------------------------------------------

    print()
    print("=" * 78)
    print("Gate B.3 Expanded Sol Audit — Comparison")
    print("=" * 78)

    print("\nOVERALL PRIMARY EXACT")

    for source, key in [
        ("GPT-5.6 Sol", "sol"),
        ("MODEL_G", "model"),
    ]:
        t2 = overall["T2"][f"{key}_primary_exact"]
        t3 = overall["T3"][f"{key}_primary_exact"]

        print(
            f"{source:14s} "
            f"T2={pct(t2):>7s}  "
            f"T3={pct(t3):>7s}  "
            f"delta={pp(t3-t2)}"
        )

    print("\nBY LANGUAGE CLASS")

    for group in sorted(lang):
        t2 = lang[group]["T2"]
        t3 = lang[group]["T3"]

        print(
            f"{group:20s} N={t2['n']:3d} | "
            f"Sol {pct(t2['sol_primary_exact'])} -> "
            f"{pct(t3['sol_primary_exact'])} "
            f"({pp(t3['sol_primary_exact'] - t2['sol_primary_exact'])}) | "
            f"MODEL_G {pct(t2['model_primary_exact'])} -> "
            f"{pct(t3['model_primary_exact'])} "
            f"({pp(t3['model_primary_exact'] - t2['model_primary_exact'])})"
        )

    print("\nSOL ↔ MODEL_G PRIMARY AGREEMENT")

    for taxonomy in ("T2", "T3"):
        r = overall[taxonomy]
        print(
            f"{taxonomy}: "
            f"{pct(r['sol_model_primary_agreement'])}"
        )

    print()
    print(f"CSV: {csv_path}")
    print(f"MD : {md_path}")
    print()
    print(
        "NOTE: fixed purposive challenge subset; descriptive "
        "comparisons only."
    )


if __name__ == "__main__":
    main()
