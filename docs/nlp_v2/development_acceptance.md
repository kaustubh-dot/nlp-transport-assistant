# Development acceptance and coverage — Phase 19

On unchanged development v1, source state `393cdce`, the complete assistant achieves **93/120 terminal contracts**, **42/50 answerable contracts** and **3/104 false-positive clarifications**. Baseline Phase 12 was 64/120, 24/50, 30/104 respectively. More OK statuses alone are not accepted as correct coverage. These are observed engineering contracts, not independent generalization or factual travel-answer estimates.

| Intent | Dev cases | OK | Clarification | Unavailable | Out of scope | Correct terminal | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| point_to_point_route | 9 | 1 | 0 | 8 | 0 | 2/9 | Ordered published connectivity; dated/time-specific planning refused. |
| multimodal_route | 6 | 0 | 0 | 6 | 0 | 6/6 | No confirmed transfer graph; verified plan unavailable. |
| first_and_last_service | 6 | 5 | 1 | 0 | 0 | 4/6 | Published bus calendars/times; clock-scope/metro limitations. |
| service_frequency | 7 | 6 | 1 | 0 | 0 | 2/7 | One route/direction/physical-stop group; no live headways. |
| scheduled_departure | 10 | 5 | 3 | 2 | 0 | 9/10 | Published bus schedule only; metro evidence unavailable. |
| route_stop_sequence | 11 | 8 | 1 | 2 | 0 | 11/11 | Published sequences with partial topology caveats. |
| route_stop_membership | 7 | 7 | 0 | 0 | 0 | 6/7 | Bounded positives; negatives require complete variants. |
| mode_availability | 6 | 4 | 0 | 2 | 0 | 5/6 | Positive published connectivity; no current/dated-operation assertion. |
| fare_calculation | 10 | 7 | 1 | 2 | 0 | 10/10 | Dated metro token or explicit bus stage/class; constrained scopes refused. |
| ticketing_and_passes | 7 | 0 | 0 | 7 | 0 | 7/7 | No authoritative ticket/pass policy source. |
| station_facilities | 7 | 0 | 0 | 7 | 0 | 5/7 | No verified facility values. |
| station_accessibility | 6 | 0 | 0 | 6 | 0 | 6/6 | Snapshot availability fields are null. |
| interchange_transfer | 6 | 0 | 0 | 6 | 0 | 1/6 | No confirmed interchange links. |
| nearest_transport | 8 | 5 | 3 | 0 | 0 | 7/8 | Exact coordinates and straight-line distance; no verified walking access. |
| realtime_status_query | 6 | 0 | 0 | 6 | 0 | 6/6 | No authorized live telemetry. |
| out_of_scope | 6 | 0 | 1 | 0 | 5 | 5/6 | Transport scope rejection. |
| Structured ambiguity / multiple goals | 2 | 0 | 2 | 0 | 0 | 1/2 | Null-intent guard contracts, excluded from raw classifier accuracy. |

Counts group cases by **gold development intent**, not predicted class. All 120 rows are included, with zero error statuses. The unchanged raw trace observes all 16 predicted labels; canonical contract tests and intended-intent cases exercise all 16 operations. Reachability does not imply current-data answerability.

## Improvements and remaining failures

- Legitimate answerable coverage: 24/50 → 42/50 (48%→84%); intended-intent downstream 28/50 → 50/50.
- False-positive clarification: 30/104 → 3/104 (28.85%→2.88%). Clarification statuses: 43 → 13.
- Intended-intent terminal coverage: 119/120. The sole failure is frozen v1-098: entity clarification gold versus an actionable refusal of absent metro schedules. This documented policy divergence stays visible; gold is not edited.
- Raw accuracy 92/118 and Macro-F1 0.75675 are distinct from reply-intent accuracy 93/120. Twenty-five terminal failures have wrong raw class and become correct in the counterfactual; one structured intent-ambiguity contract remains beyond argmax; one residual policy/gold divergence remains. Raw classification and residual downstream flags may co-occur.
- Intended-intent slot extraction/entity/domain-code failure counts are zero on this suite; this does not prove absence outside it. No further suite-specific implementation defect was identified.
- Under intended-intent diagnosis, all 48 gold-unavailable contracts are correct source/scope refusals (42) or external realtime refusals (6). Production has 38/48 correct terminal refusals; ten fail their intent contract. These source limitations are distinct from classifier failures. No fabricated live, accessibility, facility, transfer or discount claims were added.

The one full replacement candidate failed its **validation-only** gate (0.84658 versus existing 0.85122 Macro-F1) and was not evaluated on development or historical data. Existing checkpoint is retained; no adaptive training retry or arbitrary confidence threshold was introduced.

## Acceptance interpretation

The substantial gains come from exposing bounded canonical evidence, correct execution inputs, exact multilingual names and actionable clarification policy. Ambiguous physical nodes remain candidates; partial topology and dated evidence retain caveats. Unsupported operations stay explicit and tested. The classifier still limits observed coverage, and this suite has small/noise-skewed strata. Do not call this perfection or present the conditional 50/50 downstream score as model capability.

## Reproduction and evidence

```bash
HF_HOME="$PWD/.cache/huggingface" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  .venv/bin/python -m scripts.nlp_v2.evaluate_development_coverage \
  --output-dir /tmp/nlp-v2-development-new
```

Use `--gold-intent` in a different new/empty directory for the downstream diagnostic. It bypasses model inference and cannot be called classifier accuracy.

- [Actual development report](../../reports/nlp_v2/development_coverage/phase19_model/coverage.json)
- [Intended-intent downstream report](../../reports/nlp_v2/development_coverage/phase19_downstream/coverage.json)
- [Raw classifier attribution and validation decision](training_decision.md)
- [Domain capability matrix](domain_coverage_design.md)

Reports lock suite/model/DB/source hashes and Chennai reference date 2026-10-07; normalized held-out overlap is zero through an opaque fingerprint guard. Zero exact overlap is not proof of semantic independence. No historical evaluator or individual held-out failure inspection was performed.
