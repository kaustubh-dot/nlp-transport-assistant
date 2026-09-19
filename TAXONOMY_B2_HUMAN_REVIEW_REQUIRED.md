# GATE B.2 MODEL CONFIRMATION COMPLETE

MODEL RESULTS COMMIT:
9345a246d44534e7aa002f7535f1cadae8c2b086

AUDIT CORRECTION COMMIT:
29740e7f5a8ee86171885a0c4bd19220f0aa99f6

FINAL CLEANUP COMMIT:
PENDING_FINAL_COMMIT

ACTIVE KB:
chennai_multimodal_v1.2.2

T2-H IMPLEMENTATION:
shared encoder
12-class intent head
global 16-class semantic-subtype head
joint loss lambda = 1.0 (multitask supervision)

T3 IMPLEMENTATION:
direct 16-class MuRIL classifier

STRICT EXACT OPERATION:
T2-H: 0.7531 ± 0.0024
T3: 0.7941 ± 0.0291
difference: +0.0411 (+4.11 pp)

MULTI-SEED EVIDENCE:
seed 42: T3 wins significantly (p = 7.22e-10, chi2 = 37.96)
seed 101: T3 wins significantly (p = 1.56e-3, chi2 = 10.01)
seed 777: no significant difference / near tie (p = 0.822, chi2 = 0.05)
hierarchical bootstrap: mean diff = +0.0412, 95% CI: [+0.0245, +0.0581], empirical p < 0.002

AMBIGUITY-AWARE RESULT:
corrected T2-H: 0.7668 ± 0.0084
corrected T3: 0.8069 ± 0.0306
difference: +0.0401 (+4.01 pp)
ambiguous-only subset: T2-H 0.5952 ± 0.0585, T3 0.6531 ± 0.0464 (+5.78 pp)
non-ambiguous subset: T2-H 0.7944 ± 0.0036, T3 0.8317 ± 0.0298 (+3.73 pp)

ENTITY GROUNDING & TOPOLOGY RECONCILIATION:
rows with entities: 665 / 706 stress eval (1,286 train, 374 validation)
corrected mapping failures: 1 (Egmore previously mapped to Central)
corrected mappings: Egmore -> HUB_EGMORE (METRO_EGMORE, CMRL)
unresolved: 0
fact-grounding caveats: entity grounding status separated from fact grounding status; realtime queries marked REQUIRES_REALTIME_DATA, unsupported amenities marked NOT_CURRENTLY_SUPPORTED, representative route patterns marked PROVISIONAL_REPRESENTATIVE_PATTERN
topology candidates: 217
canonical matches: 67 (train: 35, validation: 4, stress_eval: 28)
provisional non-matches: 150
topology invariant pass: YES (217 == 67 + 150)

HUMAN REVIEW PACKAGE:
sample size: 350
blind CSV: data/nlp_v2/gate_b2/human_annotation_blind.csv (350 rows, reviewer fields blank, no gold labels)
guide: docs/nlp_v2/gate_b2_human_annotation_guide.md
gold key: data/nlp_v2/gate_b2/human_annotation_key.json (INTERNAL — FORBIDDEN TO REVIEWERS DURING STUDY)
manifest: data/nlp_v2/gate_b2/human_annotation_manifest.json
procedural blinding required: YES

MANUAL / EXTERNAL ANNOTATION METHODOLOGY:
PENDING DESIGN REVIEW

REAL HUMAN ANNOTATION:
PENDING

T2 AGREEMENT:
PENDING

T3 AGREEMENT:
PENDING

TAXONOMY FREEZE:
NO

GATE C:
NO

STATUS:
STOPPED FOR ANNOTATION-METHODOLOGY REVIEW
