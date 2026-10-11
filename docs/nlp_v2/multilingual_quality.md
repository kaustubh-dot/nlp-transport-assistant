# Multilingual remediation evidence — acceptance not passed

As of 2026-10-09, development is frozen and the production MuRIL checkpoint is retained. L0–L6 passed fresh GPT-6.1 Sol xhigh review. Post-freeze evaluation found acceptance failures; this work is **not approved as completed remediation**. No behavior was changed after the challenge rerun, and repository cleanup has not begun.

## Corpus and implementation

The new versioned corpus has 694 independently authored/reviewed rows, 95 construction families and 65 semantic families. Families were allocated before expansion: TRAIN 466, validation 124, development-test 104; classifier-applicable counts are 458/108/96. Hindi Devanagari, Roman Hindi, Hinglish and English cover all 16 frozen T3 intents. Literal entity, slot, constraint and clarification expectations were authored independently of production output. Internal family isolation does not imply new intent meanings absent from original TRAIN.

Extraction uses a separate NFC representation preserving Hindi combining marks; the classifier still receives raw text. Reviewed canonical transliterations and spacing preserve competing physical IDs. Clarifications expose actual names/modes/candidates. Extraction adds bounded clocks/native digits, endpoint/via ordering, mode precedence/negation and conservative handling of invalid fare-stage counts. Walking-network distance and unsupported temporal scopes remain unavailable. Incomplete qualified names and unverified locality anchors require confirmation.

The source audit separately classified 162 previous limitations: 44 absent records, 30 unverified mappings/capabilities, 54 incomplete topology, six realtime requirements, five external requirements and 23 unavailable policy cases. No verified unused capability was established. Explicit Metro nearest results use the verified CMRL subset with incomplete-coverage disclosure; authoritative Rail/MRTS classification is absent. Source tables and historical evidence remain unchanged.

## Model decision

One seed-42 MuRIL warm-start candidate used original legitimate TRAIN plus the new reviewed TRAIN. Only legitimate original and new family-disjoint validation selected epoch/promotion; development-test received integrity-hash reads but no semantic use during training. The observed 400 and historical stress/reference sets were excluded.

New validation Macro-F1 improved from 0.4348 to 0.7606, but original Roman-Hindi accuracy fell from 98.92% to 93.55%, and multimodal validation true positives fell from 10/11 to 8/11. Four predeclared regression guards failed. The candidate was rejected; original weights/manifest and pinned label order/input semantics remain intact.

## Frozen evaluation

The clean development-test informed the earlier L4 training-need diagnosis, never candidate selection. Final evaluation therefore describes a reviewed development set, not an untouched external acceptance test.

| Language | Applicable queries | Intent accuracy | 16-class Macro-F1 |
|---|---:|---:|---:|
| Hindi Devanagari | 24 | 45.83% | 0.4063 |
| Roman Hindi | 24 | 29.17% | 0.2792 |
| Hinglish | 24 | 54.17% | 0.4531 |
| English | 24 | 50.00% | 0.3889 |
| Overall | 96 | 44.79% | 0.4306 |

With intended intent injected directly, authored-slot recall was 205/236 (86.86%), entity correctness 67/80 (83.75%), and constraint preservation 117/148 (79.05%). Exact slot rows were 64/96; slot recall alone does not certify absence of extra slots. Clarification matched 18/33 assessed states; 23 additional cases were masked by documented capability preflight. There were zero `ok` responses or conservatively completed goals among 104 rows. Small class/language supports and restrictive source coverage limit these measures.

All 45 legitimate English validation queries received baseline/final semantic review using identical fresh retained-model predictions: 24 unchanged, 20 safe changes and **one material new regression**. Classifier accuracy stayed 37/45 (82.22%); unchanged classifier accuracy does not establish unchanged product behavior. A named Metro line followed by “train” can incorrectly introduce a suburban-rail mode and needless clarification.

The observed Hindi/Hinglish challenge was rerun once through the real API after a 326-file development freeze. A durable journal confirms 400 unique IDs, one request per ID, all HTTP 200; no retries or post-rerun tuning occurred. Detailed replies and manual assessments remain outside the tracked submission. Final manual review of all 400 gives the following descriptive comparison. Some differences include rubric reassessment; these counts do not prove 13 individual product recoveries. Capability-wide refusals can mask unexercised extraction.

| Outcome | Previous | Frozen rerun |
|---|---:|---:|
| Completed bounded goal | 22 | 23 |
| Correct limitation | 162 | 164 |
| Legitimate clarification | 38 | 50 |
| Recognition failure | 175 | 162 |
| Wrong/unsafe answer | 0 | 1 |
| Needs source/anchor review | 3 | 0 |

Recognition failures decreased by 13 (7.43%), which does not establish the requested substantial improvement. All 23 credited factual successes received read-only source verification. The aggregate evidence is in `reports/nlp_v2/multilingual_quality/l7_challenge_regression.json`.

## Outstanding gates

A Hindi response confidently selects an explicitly excluded route variant, introducing a wrong answer. Recognition improvement is modest and the no-increase-in-wrong-answers criterion fails. The English mode regression also fails its acceptance gate. Separate new guard regressions treat one frequency question as multiple goals and an availability question’s negative polarity as a mode-exclusion instruction. L7 has one high and three medium unresolved finding groups. Bounded real API/browser checks verify rendering, mode precedence, drafts/history, canonical clarification tables, source/error states and fare typography, but independent UI review confirmed that toggling a control during submission can interrupt reply persistence and leave a user-only history entry (L8: one medium finding).

The full suite passed 1,481 tests at freeze; dependency and compilation checks passed. Tests do not cancel the semantic/UI findings. Fresh L9 review independently reproduced the evidence, passed 175 focused tests, checked all 326 freeze hashes, and confirmed the final gate **FAIL: zero critical, one high, four medium unresolved groups**. No additional critical/high/medium leakage, source, promotion or reporting issue was established. Final reviewer gates, rather than test count, control release readiness. Commit/push and cleanup are deferred. Further implementation requires an explicitly authorized new development cycle using independent material; the completed observed-challenge run must remain frozen regression evidence.
