# Multimodal Multilingual Dataset Contract (Phase N5)

Document: `docs/nlp_v2/dataset_contract.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Dataset Specification

---

## 1. Core Generation Principles

1. **Language-Native Utterance Families**:
   Utterance families are authored independently in English, Hindi, and Hinglish. We strictly prohibit synthesizing the corpus by machine-translating an English template bank into Indic languages, which introduces unnatural syntax and translation artifacts.
2. **Semantic Hierarchy & Family Disjointness**:
   Utterances are organized into a strict four-tier hierarchy:
   - `semantic_family_id`: The high-level communicative meaning (e.g. `how_to_travel_direct`). Shared across language variants.
   - `family_id`: The syntactic/grammatical template family within a specific language (e.g. `how_to_travel_direct:hi_postposition`).
   - `paraphrase_group_id`: Lexical paraphrase variations of a specific syntactic template.
   - `utterance_id`: The individual populated utterance with specific entities.
3. **Controlled Entity Grounding**:
   Slots are drawn directly from canonical tables in `canonical_transport.db` (7,136 stops, 4,619 routes, 1,621 places). Entity sampling is stratified across Head (frequent transit hubs), Mid (suburban stations, arterial bus stops), and Tail (rural halts, local bus stages).
4. **Nested Size Scaling**:
   The generator produces nested, reproducible dataset slices (`5k`, `10k`, `20k`, `40k`, `80k`) sharing the exact same validation, test, and challenge partitions.

---

## 2. Definitive V2 Row Schema

Every row in the generated v2 dataset must conform to the following schema. It provides both structured JSON representations (`slots_json`, `entity_surfaces_json`, `canonical_entities_json`) for clean programmatic evaluation and flattened columns for rapid tabular analytics.

```
V2 UTTERANCE SCHEMA:

Field Name                  Type        Description
----------------------------------------------------------------------------------------------------
utterance_id                string      Unique immutable ID (e.g. V2_UTT_000001)
query                       string      Raw commuter query text (preserving casing and noise)
intent                      string      Primary intent label (from approved taxonomy T2)
intent_subtype              string      Granular subtype (e.g. first_service, stage_fare)

family_id                   string      Language-specific template family ID
semantic_family_id          string      Cross-lingual semantic concept ID (for leakage prevention)
paraphrase_group_id         string      Paraphrase group ID within family
template_id                 string      Underlying template identifier

language                    string      Formal language code (EN, HI_DEVA, HI_LATN, HINGLISH_LATN, MIXED_SCRIPT_CS)
script                      string      Script code (Latn, Deva, Mixed)
primary_language            string      Primary matrix language (en, hi)
code_switched               boolean     True if query exhibits code mixing
code_switch_level           string      Code-switch intensity tier (CS0, CS1, CS2, CS3, CS4)
romanized                   boolean     True if Indic words appear in Latin script

noise_level                 string      Spelling/noise tier (N0, N1, N2, N3, N4, N5)
noise_type                  string      Specific noise mechanism (canonical, typo, translit, chat_abbrev)

origin_id                   string      Canonical origin entity ID (or null)
destination_id              string      Canonical destination entity ID (or null)
via_id                      string      Canonical intermediate waypoint entity ID (or null)
station_id                  string      Canonical single station/stop entity ID (or null)
place_id                    string      Canonical landmark/place ID (or null)
route_number                string      Normalized operational route code (e.g. 102A, 21G)
transport_mode              string      Explicit mode (metro, bus, suburban_rail, mrts, any)
timing_type                 string      Timing subtype (first, last, frequency, departure, operating_hours)
time                        string      Normalized ISO time string (HH:MM:SS) (or null)
facility_type               string      Requested facility (parking, lift, restroom)
accessibility_feature       string      Requested accessibility feature (wheelchair, tactile_paths)
ticket_type                 string      Requested ticket/pass product (smart_card, token)

slots_json                  json        Full dictionary of extracted typed slots
entity_surfaces_json        json        List of extracted surface spans with char start/end offsets
canonical_entities_json     json        List of resolved canonical entity objects with candidate IDs

answerability_status        string      Status from answerability matrix (ANSWERABLE_NOW, etc.)
source_type                 string      Source origin (authored_template, harvested_commuter, seed_expansion)
generation_method           string      Generation algorithm version (e.g. v2_generator_rev1)

human_reviewed              boolean     True if audited by human domain expert
review_status               string      Review state (unreviewed, approved, rejected, modified)

kb_snapshot_version         string      Factual snapshot version (chennai_multimodal_v1.2.1)
dataset_version             string      NLP dataset release version (e.g. v2.0-candidate)
split                       string      Partition assignment (train, validation, test, challenge_unseen, challenge_alias)
```

---

## 3. Machine-Readable Manifest Specification

Every generated dataset artifact must be accompanied by an immutable manifest (`manifest.json`) verifying provenance, dataset distributions, and cryptographic checksums:

```json
{
  "dataset_version": "v2.0-freeze",
  "created_at": "2026-09-19T00:00:00Z",
  "taxonomy_version": "T2_MEDIUM_12",
  "slot_schema_version": "v2.0",
  "kb_snapshot_version": "chennai_multimodal_v1.2.1",
  "generation_script_version": "scripts/nlp_v2/generate_dataset.py@commit",
  "random_seed": 42,
  "sample_count": 40000,
  "split_proportions": {
    "train": 28000,
    "validation": 6000,
    "test": 6000
  },
  "intent_distribution": {
    "route_query": 5600,
    "route_stops": 3600,
    "service_timing": 4400,
    "service_availability": 3600,
    "fare_query": 3600,
    "ticketing_rules": 2800,
    "station_facilities": 2800,
    "accessibility": 2400,
    "interchange_query": 2400,
    "nearest_transport": 3200,
    "unsupported_live_status": 2800,
    "out_of_scope": 2800
  },
  "language_distribution": {
    "EN": 10000,
    "HI_DEVA": 10000,
    "HI_LATN": 6000,
    "HINGLISH_LATN": 10000,
    "MIXED_SCRIPT_CS": 4000
  },
  "code_switch_distribution": {
    "CS0": 20000,
    "CS1": 4000,
    "CS2": 8000,
    "CS3": 5000,
    "CS4": 3000
  },
  "noise_distribution": {
    "N0": 16000,
    "N1": 8000,
    "N2": 8000,
    "N3": 4000,
    "N4": 3000,
    "N5": 1000
  },
  "diversity_metrics": {
    "total_families": 420,
    "total_semantic_families": 110,
    "unique_entities_used": 1420,
    "unique_origin_destination_pairs": 8450,
    "head_entity_ratio": 0.45,
    "mid_entity_ratio": 0.35,
    "tail_entity_ratio": 0.20
  },
  "checksums": {
    "train_csv_sha256": "...",
    "validation_csv_sha256": "...",
    "test_csv_sha256": "..."
  }
}
```

---

## 4. Automated Dataset QA Verification Suite

Before any generated dataset partition is accepted or frozen, it must execute and pass an automated validation script (`scripts/nlp_v2/validate_dataset.py`).

### Mandatory QA Rules:
1. **Zero Duplicate Utterance IDs**:
   All `utterance_id` values must be globally unique.
2. **Normalized Query Deduplication**:
   No exact duplicate normalized queries within any partition.
3. **Leakage Invariant (Zero Split Contamination)**:
   - No `family_id` present in `train` may appear in `validation` or `test`.
   - No `semantic_family_id` present in `train` may appear in `validation` or `test`.
   - No `paraphrase_group_id` present in `train` may appear in `validation` or `test`.
4. **Canonical Entity Reference Integrity**:
   All entity IDs (`origin_id`, `destination_id`, `station_id`, `route_number`, `place_id`) must resolve against live tables in `data/canonical/transit/canonical_transport.db`.
5. **Contract Enforcement**:
   - `REQ` slots must be non-null.
   - `FORBIDDEN` slots must be strictly null.
   - Any query classified as `out_of_scope` must have null transit entity IDs.
6. **Valid Language & Script Metadata**:
   All language and script tags must match allowed enum values. No Latin-only string may be tagged as `HI_DEVA`.
