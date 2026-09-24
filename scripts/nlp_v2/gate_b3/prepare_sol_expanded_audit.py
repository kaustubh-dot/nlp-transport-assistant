#!/usr/bin/env python3

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

BLIND = ROOT / "data/nlp_v2/gate_b2/human_annotation_blind.csv"
STRESS = ROOT / "data/nlp_v2/gate_b2/gate_b2_stress_eval.csv"

OUTDIR = ROOT / "data/nlp_v2/gate_b3/sol_expanded_audit"
OUTDIR.mkdir(parents=True, exist_ok=True)

N_UNIQUE = 128
MIN_PER_LANGUAGE = 20
SEED = "GATE_B3_SOL_EXPANDED_256_V1"

# Exclude anything already individually exposed to Sol in this conversation.
PRIOR_EXPOSURE_IDS = {
    # Earlier blind-file/tool exposure
    *{f"ANN_B2_{i:03d}" for i in range(1, 28)},

    # Earlier package examples
    "ANN_B2_091",
    "ANN_B2_092",
    "ANN_B2_154",
    "ANN_B2_155",
    "ANN_B2_186",
    "ANN_B2_304",
    "ANN_B2_313",
    "ANN_B2_314",
    "ANN_B2_334",

    # Previously completed 24-judgment targeted Sol audit
    "ANN_B2_029",
    "ANN_B2_064",
    "ANN_B2_084",
    "ANN_B2_099",
    "ANN_B2_112",
    "ANN_B2_120",
    "ANN_B2_130",
    "ANN_B2_149",
    "ANN_B2_150",
    "ANN_B2_229",
    "ANN_B2_281",
    "ANN_B2_288",
    "ANN_B2_304",
    "ANN_B2_305",
    "ANN_B2_319",
    "ANN_B2_324",
    "ANN_B2_337",
}

# Every observed value of these fields should be represented if possible.
COVERAGE_FIELDS = [
    "language_class",
    "script",
    "code_switch_level",
    "noise_level",
    "noise_type",
    "ambiguity_type",
    "answerability_status",
]

# Used for diversity, not mandatory exhaustive coverage.
DIVERSITY_FIELDS = [
    "semantic_family_id",
    "semantic_scenario_id",
    "generation_method",
]


def h(text):
    return hashlib.sha256(
        f"{SEED}|{text}".encode("utf-8")
    ).hexdigest()


def clean(v):
    v = (v or "").strip()
    return v if v else "<EMPTY>"


def row_features(row, fields):
    return {
        f"{field}={clean(row.get(field))}"
        for field in fields
    }


# ------------------------------------------------------------------
# Load frozen 350 challenge set
# ------------------------------------------------------------------

with BLIND.open(encoding="utf-8", newline="") as f:
    blind_rows = list(csv.DictReader(f))

assert len(blind_rows) == 350

with STRESS.open(encoding="utf-8", newline="") as f:
    stress_rows = list(csv.DictReader(f))

stress_by_utt = {
    r["utterance_id"]: r
    for r in stress_rows
}

candidates = []

for b in blind_rows:
    aid = b["annotation_id"]

    if aid in PRIOR_EXPOSURE_IDS:
        continue

    utt = b["utterance_id"]

    if utt not in stress_by_utt:
        raise RuntimeError(
            f"Missing stress metadata for {aid} / {utt}"
        )

    meta = stress_by_utt[utt]

    row = {
        "annotation_id": aid,
        "utterance_id": utt,
        "query": b["query"],
    }

    for k, v in meta.items():
        if k not in row:
            row[k] = v

    candidates.append(row)

print(f"Frozen challenge rows     : {len(blind_rows)}")
print(f"Prior-exposure exclusions : {len(set(PRIOR_EXPOSURE_IDS))}")
print(f"Eligible fresh candidates : {len(candidates)}")

assert len(candidates) >= N_UNIQUE


# ------------------------------------------------------------------
# Availability summary
# ------------------------------------------------------------------

language_counts = Counter(
    clean(r["language_class"])
    for r in candidates
)

print("\nAvailable language classes:")
for k, v in sorted(language_counts.items()):
    print(f"  {k:24s} {v}")


# ------------------------------------------------------------------
# Mandatory category coverage
# ------------------------------------------------------------------

all_coverage_tokens = set()

for r in candidates:
    all_coverage_tokens |= row_features(r, COVERAGE_FIELDS)

token_frequency = Counter()

for r in candidates:
    for token in row_features(r, COVERAGE_FIELDS):
        token_frequency[token] += 1


selected = []
selected_ids = set()
covered = set()


def add(row):
    aid = row["annotation_id"]

    if aid in selected_ids:
        return

    selected.append(row)
    selected_ids.add(aid)
    covered.update(row_features(row, COVERAGE_FIELDS))


# First: greedy set-cover over all observed categorical variation.
while covered != all_coverage_tokens:
    best = None
    best_score = None

    for r in candidates:
        if r["annotation_id"] in selected_ids:
            continue

        new_tokens = row_features(r, COVERAGE_FIELDS) - covered

        if not new_tokens:
            continue

        # Rare categories have more weight.
        score = sum(
            1.0 / token_frequency[t]
            for t in new_tokens
        )

        key = (
            score,
            len(new_tokens),
            h(r["annotation_id"]),
        )

        if best is None or key > best_score:
            best = r
            best_score = key

    if best is None:
        break

    add(best)

if covered != all_coverage_tokens:
    missing = sorted(all_coverage_tokens - covered)
    raise RuntimeError(
        f"Could not cover mandatory variation values: {missing}"
    )


# ------------------------------------------------------------------
# Ensure meaningful representation of every language class
# ------------------------------------------------------------------

def current_language_counts():
    return Counter(
        clean(r["language_class"])
        for r in selected
    )


for lang in sorted(language_counts):
    target = min(
        MIN_PER_LANGUAGE,
        language_counts[lang],
    )

    while current_language_counts()[lang] < target:
        pool = [
            r for r in candidates
            if r["annotation_id"] not in selected_ids
            and clean(r["language_class"]) == lang
        ]

        if not pool:
            break

        existing_families = {
            clean(r.get("semantic_family_id"))
            for r in selected
        }

        def lang_score(r):
            fam = clean(r.get("semantic_family_id"))

            novelty = 1 if fam not in existing_families else 0

            diversity = sum(
                1
                for field in DIVERSITY_FIELDS
                if clean(r.get(field)) not in {
                    clean(x.get(field))
                    for x in selected
                }
            )

            return (
                novelty,
                diversity,
                h(r["annotation_id"]),
            )

        add(max(pool, key=lang_score))


# ------------------------------------------------------------------
# Fill to 128 maximizing semantic diversity
# ------------------------------------------------------------------

while len(selected) < N_UNIQUE:
    remaining = [
        r for r in candidates
        if r["annotation_id"] not in selected_ids
    ]

    if not remaining:
        raise RuntimeError("Candidate pool exhausted")

    existing_by_field = {
        field: {
            clean(x.get(field))
            for x in selected
        }
        for field in DIVERSITY_FIELDS
    }

    lang_now = current_language_counts()

    def fill_score(r):
        diversity = sum(
            1
            for field in DIVERSITY_FIELDS
            if clean(r.get(field))
            not in existing_by_field[field]
        )

        # Slight preference for currently underrepresented languages.
        lang = clean(r["language_class"])
        balance = -lang_now[lang]

        return (
            diversity,
            balance,
            h(r["annotation_id"]),
        )

    add(max(remaining, key=fill_score))


assert len(selected) == N_UNIQUE
assert len(selected_ids) == N_UNIQUE


# ------------------------------------------------------------------
# Verify mandatory category coverage
# ------------------------------------------------------------------

selected_tokens = set()

for r in selected:
    selected_tokens |= row_features(r, COVERAGE_FIELDS)

missing = sorted(all_coverage_tokens - selected_tokens)

if missing:
    raise RuntimeError(
        "Expanded audit failed mandatory coverage: "
        + repr(missing)
    )


# ------------------------------------------------------------------
# Write blind T2/T3 packages
# ------------------------------------------------------------------

def blind_record(r, taxonomy):
    return {
        "annotation_id": r["annotation_id"],
        "query": r["query"],
        "taxonomy_version": taxonomy,
    }


for taxonomy in ("T2", "T3"):
    # Independent deterministic ordering for each taxonomy.
    ordered = sorted(
        selected,
        key=lambda r: hashlib.sha256(
            f"{SEED}|{taxonomy}|{r['annotation_id']}".encode()
        ).hexdigest()
    )

    path = OUTDIR / f"sol_expanded_{taxonomy.lower()}_128.jsonl"

    with path.open("w", encoding="utf-8") as f:
        for r in ordered:
            f.write(
                json.dumps(
                    blind_record(r, taxonomy),
                    ensure_ascii=False,
                )
                + "\n"
            )

    digest = hashlib.sha256(path.read_bytes()).hexdigest()

    print(
        f"\n{path}\n"
        f"  records: 128\n"
        f"  SHA256 : {digest}"
    )


# ------------------------------------------------------------------
# Provenance manifest — NOT supplied to Sol
# ------------------------------------------------------------------

selected_language_counts = Counter(
    clean(r["language_class"])
    for r in selected
)

coverage_summary = {}

for field in COVERAGE_FIELDS:
    available = sorted({
        clean(r.get(field))
        for r in candidates
    })

    chosen = sorted({
        clean(r.get(field))
        for r in selected
    })

    coverage_summary[field] = {
        "available_values": available,
        "selected_values": chosen,
        "coverage_complete": set(available) == set(chosen),
    }


manifest = {
    "audit": "GPT-5.6 Sol expanded masked language/surface audit",
    "selection_seed": SEED,
    "unique_query_count": N_UNIQUE,
    "taxonomy_count": 2,
    "total_judgments": N_UNIQUE * 2,
    "selection_used_model_g_labels": False,
    "selection_used_reference_labels": False,
    "prior_exposure_ids_excluded": sorted(PRIOR_EXPOSURE_IDS),
    "language_counts": dict(sorted(selected_language_counts.items())),
    "mandatory_coverage": coverage_summary,
    "selected_annotation_ids": sorted(selected_ids),
}

manifest_path = OUTDIR / "selection_manifest.json"

manifest_path.write_text(
    json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)


print("\nSelected language counts:")
for k, v in sorted(selected_language_counts.items()):
    print(f"  {k:24s} {v}")

print("\nMandatory coverage:")
for field, info in coverage_summary.items():
    print(
        f"  {field:24s} "
        f"{len(info['selected_values'])}/"
        f"{len(info['available_values'])} "
        f"{'PASS' if info['coverage_complete'] else 'FAIL'}"
    )

print("\nPASS: 128 fresh queries / 256 blind judgments prepared")
