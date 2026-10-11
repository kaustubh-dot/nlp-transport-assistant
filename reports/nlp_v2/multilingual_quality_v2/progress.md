# Multilingual Remediation v2 — STOP

The cycle ends at a failed post-freeze regression gate. No additional behavioral work, challenge reruns, push or repository cleanup is authorized within this cycle.

Source freeze: `f738ddb3b7d63051dbd611f8087ffd7ca26d6d87`. Original production model retained; no v2 training. Pre-freeze independent English/API/UI checks and all 2,466 repository tests passed. The R8 review accepted the source before the freeze.

Exactly one 200 Hindi + 200 Hinglish real HTTP regression completed after the freeze. Final saved-response assessment: 22 bounded completed goals, 159 truthful source/scope limitations, 50 legitimate clarifications, 169 recognition failures, zero explicit wrong/unsafe answers and zero unresolved source/anchor reviews. Recognition failures are seven above v1 and six below the earlier baseline. These categories are not general multilingual accuracy.

Confirmed blocker: HG200_036 previously returned canonical Bus 27D stop lists in both directions; the frozen v2 response instead requests a missing route despite the explicit route code. R11 is complete with C0/H0/M2: false single-goal refusals and stage quantities emitted as invented route numbers. The source hold is released and no review remains pending. No patch follows these observations.

The fresh R11 reviewer audited saved responses only: all 38 changed responses reviewed, 362 identical semantic responses transparently retain historical categories, and all 28 saved ok data payloads match canonical data. Two draft clarification categories were corrected without any query rerun. The original primary draft remains preserved.

All 241 protected live files remain unchanged. The reviewer verified the committed HEAD, development/independent/behavioral manifests, original model and canonical database. The challenge was first accessed after the committed freeze and was not used for tuning. Detailed v1 evidence remains intact.

The local API is stopped. Final report changes remain in the working tree, with a separate failed checkpoint under `experiments/nlp_v2/production_runs/multilingual_v2/checkpoint_r11_failed/`. Another development cycle requires separate explicit user authorization. No completion claim, push or cleanup occurred.

On 2026-10-12, after the failed cycle closed, the user explicitly instructed “push it”. Publication of the frozen source and final failure reports to GitHub main is authorized. The failed R11 gate, behavioral freeze and no-cleanup constraint remain in force.
