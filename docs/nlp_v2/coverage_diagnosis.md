# Phase 11 — operational coverage diagnosis

Date: 2026-10-07. Audited source: `9c9f707199ad210878baa08ff536358da9386c03`.
Local `main` and remote `refs/heads/main` match that revision; initial working
tree clean. Baseline verification: 368 tests pass in 13.18 s using `.venv`,
the repository-local pinned Hugging Face cache, and two CPU threads.

## Boundary and evidence

This diagnosis uses production code, product contracts, database schema and
aggregate SQL queries, ingestion code, and newly authored synthetic probes.
No individual stress/reference rows, annotations, or failed predictions were
read for diagnosis. Historical aggregate results motivate the work but cannot
attribute its causes quantitatively. No evaluator or research study was rerun.
The older task/slot/answerability specifications describe candidate T2 contracts
and intended capabilities; the frozen 16-label T3 production contracts and actual
snapshot determine executable behavior. Historical reports remain untouched.

The checkpoint hash matches
`abac66fc9fa29212c7565117ae326e34f02b64e76dbb177c61e9661517803196`.
Canonical DB hash:
`583fd400bb3ee0d5af312e03ec78116de88ce162d6c33c2b87fd93df4da48791`.
Frozen B.2/B.3 paths have no Git differences from `c7576a9`.

## Pipeline findings

1. **Intent:** MuRIL receives the raw query with fixed labels/revision/length.
   It always returns its top label; classifier confidence does not trigger a
   clarification threshold. Explicit conjoined goals have a separate
   clarification-only guard. Therefore high clarification cannot simply be
   attributed to a confidence threshold. Preserve this model contract.
2. **Slots and resolution:** exact longest-span matching uses canonical names,
   `stop_names`, `place_names`, and an existing curated multilingual gazetteer.
   Mode filtering and journey hub preference already exist. Stop-name rows are
   English (7,149) or Tamil (422); Hindi coverage relies on the reused gazetteer.
   Multiple exact physical nodes legitimately remain ambiguous. Route context
   is used only for the membership `stop` role, and route index keys use upper
   case without the domain's whitespace/hyphen normalization. Audit safe route
   context for timing stations and deterministic qualified names; never merge
   duplicate nodes by name alone or guess an unknown typo.
   Entity kinds also exceed execution coverage: journey resolution accepts
   place IDs, but `_physical_stops` supports only stops/hubs. No verified
   place-to-stop access mapping exists. Nearest extraction conversely only
   assigns place candidates, although exact stop coordinates could anchor a
   bounded geometric lookup. Audit anchor reachability without inventing
   pedestrian links or converting a landmark into an arbitrary station.
3. **Requirements:** first/last and frequency have no required location rule,
   yet `_scheduled_rows` needs station/stop/origin. A route-only request reaches
   unavailable despite having a recognized route. Frequency additionally needs
   a route/line. Scheduled departures require station/stop even though their
   handler also accepts origin. Route-only bounds must not silently aggregate
   departures from every intermediate stop; a clearly scoped terminal/direction
   interpretation or a useful station prompt is needed. These are inconsistent
   execution contracts, not evidence that journey endpoints should always be
   removed. Fare already accepts a stage without endpoints.
4. **Clarification ordering:** entity and temporal uncertainty stop dispatch
   before capability checks. A synthetic monthly-pass query mentioning generic
   Guindy asks which physical stop, although the policy handler is unavailable
   for every station. Facilities, accessibility, transfers, and multimodal
   planning similarly ask for details that may not change capability. Add a
   narrowly defined capability preflight where unsupported scope is certain;
   preserve semantic/multiple-goal ambiguity and actionable missing inputs.
5. **Domain:** mode-consistency guards protect against corrupt canonical links.
   Existing useful data are already exposed for bus sequences/membership,
   directional sequence candidates, dated fares, published bus timetables, and
   geometric proximity. Static connectivity is underexposed: availability
   always returns unavailable with a candidate count, even for an evidenced
   connection. A bounded published-connectivity answer must distinguish a
   positive static connection from current operation; absence is not proof
   that no service exists.
   Explicit constraints also need integrity checks: multiple requested modes
   are retained only in extraction metadata (except interchange mode pairs),
   then discarded by the assistant; `_plan_route` accepts date/time but does
   not use them. Thus a gold-intent route request can return bus-only static
   candidates despite combined-mode or future date/time constraints. Add
   development probes for preserving these constraints; clarify/refuse
   unsupported scope or explicitly disclose which requested constraints the
   bounded static response cannot honor. Increasing OK coverage must not
   silently widen the user's request.
6. **Response/API/UI:** statuses and clarification reasons already cross the
   public API, with confidence/raw queries/internal exceptions excluded.
   Missing-slot prompts mechanically render internal names. Improve actionable
   wording and unavailable reasons without changing the five public statuses.

## Actual source coverage

| Area | Actual snapshot evidence | Engineering classification |
|---|---|---|
| Bus topology | 95,061 bus-route/bus-stop sequence rows; 952 bus-route/metro-stop rows filtered out | Partially supported; preserve mode checks |
| Metro topology | 12 metro-route sequence rows all reference bus-mode stops; no mode-consistent metro sequence | Verification-required; do not bypass guards or infer official topology from fares |
| Schedules | 1,348,982 bus-route/bus-stop rows; 11,461 bus-route/metro-stop and 192 metro-route/bus-stop rows excluded | Partially supported published bus schedules; no usable metro schedule |
| Calendar | Nine calendars, overall 20240501–20300501 bounds; zero exceptions | Date-specific schedule evidence must check the relevant service, weekday and dates |
| Fares | 1,681 dated CMRL pair records; 305 MTC tariff rows, 11 service strings | Partially supported; inspect ticket discount provenance and exact service strings before expansion |
| Fare stages | 1,562 stage names, 579 linked stage rows (573 distinct stops); no route-relative stage ordinal column | Verification-required for OD stage arithmetic; ID/name positions are not fare distances |
| Facilities/accessibility | 41 accessibility rows; all seven availability columns entirely null | Unsupported in this snapshot; null means unknown, not false |
| Transfers | 211 hub members unverified; 45 interchanges unconfirmed; 151 walking candidates | Verification-required; no confirmed multimodal graph |
| Names/geography | 7,136 stops, including 157 metro nodes from several sources; 1,621 places | Partially supported exact resolution and straight-line proximity; same-name duplicate nodes remain distinct |
| Policy/live data | No policy or telemetry table/source | Unsupported policy; realtime-only live queries |

The ingestion code confirms that fare-stage links are name matches, including
same-name clusters, and accessibility loads nullable source fields. Neither
supports fabricating tariffs, facilities, or verified transfers. The tariff
table spells `Night services` differently from the canonical enum `Night
Services`; exact SQL comparison currently misses that recorded category. The
enum `Air Conditioned Services` has no identically named tariff category, so
mapping it to any one A/C tariff requires evidence and cannot be assumed.

## Recommended order

1. Create and version a development-only contract suite for all 16 intents,
   covering all five language classes plus ambiguity, missing inputs, noise,
   answerable data, explicit mode/time constraints, endpoint kinds and honest
   refusals. Use new phrasing and canonical entities.
   An opaque normalized-query fingerprint check may detect held-out duplication
   without exposing held-out text. Separate real-model results from gold-intent
   downstream diagnostics; label any injected classifier explicitly.
2. Use that suite to align execution requirements and safe exact resolution,
   and avoid non-actionable questions for universally absent capabilities.
3. Expose positive static connectivity with evidence/caveats; normalize tariff
   category casing deterministically. Investigate other existing source-backed
   paths independently, retaining unavailable where evidence is insufficient.
4. Refine structured clarification/unavailability, then bounded multilingual
   extraction. Keep raw model tokenization and historical assets unchanged.
5. Attribute remaining development failures before considering retraining.
   No model replacement is justified by this structural audit alone.

All 16 labels and handler mappings exist. Reachability by real development
utterances and the size of each improvement remain to be measured in Phase 12;
this audit does not claim a coverage increase or classifier error distribution.

## Review

Independent GPT-6.1 Sol xhigh review passed after documenting two medium
omissions: explicit constraint loss and entity-kind/execution mismatch. The
linked-stage count precision was corrected. Focused re-review closed with
unresolved critical/high/medium/low = 0. No production code changed.
