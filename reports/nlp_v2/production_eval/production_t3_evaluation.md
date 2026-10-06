# Frozen production T3 model evaluation

Checkpoint SHA-256: `abac66fc9fa29212c7565117ae326e34f02b64e76dbb177c61e9661517803196`. Model and evaluation inputs were hash checked before scoring.

| Set | Count | Intent accuracy | Intent Macro-F1 | Ambiguity-aware accuracy | Mapped operation accuracy |
|---|---:|---:|---:|---:|---:|
| Frozen stress | 706 | 0.8300 | 0.7918 | 0.8399 | 0.8300 |
| Human reference subset | 350 | 0.8400 | 0.7777 | 0.8543 | 0.8400 |

Full per-class and language/code-switch/noise aggregates are in `production_t3_evaluation.json`.

## Limits

Stress: 187 of 706 rows share a train family, semantic family, or exact query (exact query overlaps: 0).
Human reference subset: 160 of 350 rows share a train family, semantic family, or exact query (exact query overlaps: 0).

- Scores measure T3 intent and mapped operation selection only; domain execution is not included.
- The classifier emits one label, so ambiguity-aware acceptance is retrospective; clarification behavior requires end-to-end evaluation.
- The human reference subset is 350 of the 706 stress examples, not an independent set.
- Contrast-group exact accuracy on the human subset is calculated only among subset members of each group; 17 of 73 observed groups are partial.
- The frozen stress and human-reference sets include rows sharing train families; their full-set scores are not independent family-held-out estimates.
