# GATE B.3 AMENDED METHODOLOGY REVIEW

**OVERALL STATUS: PROCEED WITH DOCUMENTED LIMITATIONS**

**BLOCKERS: 0**

The amended design is defensible for a **descriptive, single-student–single-model concordance study on the frozen 350-item challenge sample**. It does not establish general annotation reliability, repeatability, or independent validation of either taxonomy.

This is a review of the supplied methodology, not verification of its implementation. The reported hashes, quarantine controls, execution history, and access restrictions are taken as supplied. No benchmark items, annotations, or reference labels were inspected.

## MAJOR NONBLOCKING LIMITATIONS: 6

### 1. Amendment after partial execution
**Classification: MAJOR_NONBLOCKING_LIMITATION**

**Issue:** The replacement occurred after 23 Astra judgments existed. Absence of gold access and agreement analysis substantially reduces outcome-driven selection risk, but does not establish that nobody saw or informally interpreted those judgments. Exclusion prevents direct analytical mixing; it cannot undo prior exposure.

The stated quota failure supplies a credible operational justification. Nothing supplied establishes unacceptable post-hoc bias.

**Affected claim:** That the final source configuration was selected entirely before benchmark exposure.

**Exact limitation wording recommended:**

> “The annotator configuration was amended following a documented provider usage-limit failure after 23 Astra T2 judgments. The amendment preceded reference access and agreement analysis. Historical judgments were excluded from all primary analyses. This was a post-start resource-feasibility amendment, not a wholly prospective selection of the final annotator configuration.”

Also disclose who could access the partial outputs and whether any such exposure informed replacement-source selection or protocol changes. Do not assert absence of influence without supporting provenance.

### 2. One student and repeated exposure to the same items
**Classification: MAJOR_NONBLOCKING_LIMITATION**

**Issue:** One student cannot establish variation across human annotators. Counterbalancing reduces systematic order imbalance, but does not remove memory, learning, fatigue, or transfer between taxonomies. “T3 later” needs an operational scheduling definition.

**Affected claim:** Human labelability, human reliability, and attribution of T2/T3 differences solely to taxonomy structure.

**Exact limitation wording recommended:**

> “Human evidence comes from one student and reflects that individual’s language competence, training, interpretation, and workload. Counterbalanced taxonomy order reduces order imbalance but does not eliminate carry-over, learning, or fatigue. No human inter-annotator or within-annotator repeatability estimate is available.”

### 3. One model source, one execution campaign, and an unpinned revision
**Classification: MAJOR_NONBLOCKING_LIMITATION**

**Issue:** The model evidence is specific to the supplied model identity, execution surface, prompt, configuration, and execution period. Fresh contexts prevent intended conversational carry-over; they do not make judgments statistically independent or eliminate shared systematic errors. A configuration hash does not pin hidden provider behavior.

**Affected claim:** Model-family robustness, repeated-run stability, and exact reproducibility.

**Exact limitation wording recommended:**

> “Model evidence reflects one MODEL_G execution campaign under the recorded configuration and execution surface. The provider did not expose an immutable model revision, so exact reproduction and within-campaign revision constancy cannot be guaranteed. Fresh contexts provide procedural separation, not statistical independence or evidence of repeated-run stability.”

### 4. Purposive sample and related contrast items
**Classification: MAJOR_NONBLOCKING_LIMITATION**

**Issue:** The sample limitations are correctly recognized. Enrichment affects overall agreement and class frequencies; related contrast items can also create dependence. The 700 judgments per source are two judgments on each of 350 items, not 700 independent observations.

**Affected claim:** Population agreement rates, prevalence, deployment performance, and inferential precision.

**Exact limitation wording recommended:**

> “Results describe the fixed, purposively enriched 350-item challenge sample. They do not estimate agreement, ambiguity prevalence, or labelability in general commuter traffic. The two taxonomy judgments per item and related contrast-group items are not independent observations.”

No sample replacement or additional sampling is needed for the stated descriptive objective.

### 5. Agreement metrics do not establish correctness or neutral comparisons of granularity
**Classification: MAJOR_NONBLOCKING_LIMITATION**

**Issue:** Pairwise acceptable-set and clarification metrics remain useful with two sources. However, concordant judgments can share errors, large acceptable sets can produce high overlap, and clarification agreement can be dominated by agreement that clarification is unnecessary.

T2 and T3 differ in granularity. Their raw agreement or κ values cannot alone identify the better taxonomy. Interpretation of agreement coefficients depends on their assumptions and label distributions; a single coefficient is insufficient. [Artstein and Poesio, 2008](https://aclanthology.org/J08-4004/)

**Affected claim:** Semantic validity, comprehensive capture of ambiguity, and taxonomy superiority.

**Exact limitation wording recommended:**

> “Agreement measures quantify concordance between these two sources, not correctness or exhaustive identification of acceptable interpretations. Acceptable-set overlap depends on set size and annotation policy. Differences between T2 and T3 also reflect their label inventories and granularity; higher agreement alone does not establish taxonomy superiority.”

### 6. Author-led interpretation and Astra review are not independent validation
**Classification: MAJOR_NONBLOCKING_LIMITATION**

**Issue:** Auditing every item avoids examining disagreements alone, but an author-led audit remains interpretive and potentially influenced by knowledge of the taxonomy and reference construction. Astra methodology review is compatible with the design, but adds no independent annotation replication.

**Affected claim:** Independent adjudication, objectively established taxonomy defects, and external validation.

**Exact limitation wording recommended:**

> “The post-lock boundary audit is author-led interpretive analysis, not an independent adjudicated reference. Audit findings and proposed reference corrections remain separate from the locked first-pass evidence. Astra methodology review evaluates the study’s reasoning and does not constitute an additional annotation source or independent empirical validation.”

## MINOR CLEANUPS: 6

### 1. Freeze metric definitions and reporting rules
**Classification: MINOR_CLEANUP**

**Issue:** Metric names leave several analytical choices unspecified.

**Recommended correction:** Before inspecting agreement results, freeze:

- Acceptable-set rules, including empty sets, duplicates, and primary-label membership.
- Jaccard treatment when both sets are empty, if permitted.
- Whether per-class positive agreement concerns primary labels or acceptable-set membership; report supporting counts and undefined denominators.
- Clarification coding and the full agreement/disagreement table.
- T3 within-parent disagreement denominators and any justified T3→T2 mapping.
- Operation-level eligibility rules and excluded/not-applicable counts.
- Complete contrast-group reporting and treatment of undefined κ.

Report acceptable-set sizes alongside overlap. Describe uncertainty, if included, without implying population representativeness or independent contrast items.

### 2. Specify student scheduling and preparation
**Classification: MINOR_CLEANUP**

**Issue:** Deterministic shuffling and “later” are not fully reproducible scheduling rules.

**Recommended correction:** Record the shuffle seed/algorithm, assignment to order conditions, session arrangement, intended separation, and realized timing. Document student language competence, training, and any involvement in taxonomy or reference development. Define whether earlier judgments remain visible during subsequent annotation.

### 3. Bound validation and repair
**Classification: MINOR_CLEANUP**

**Issue:** “Semantic validation” could mean structural consistency checking or substantive reconsideration of a judgment. A format repair could inadvertently become a semantic retry.

**Recommended correction:** Define pre-lock validation as compliance with frozen schema and consistency rules, not author reassessment of plausibility or correctness. Preserve raw and repaired outputs; permit only format changes that preserve the decision. Log transport failures and attempts without choosing among completed answers. Unrecoverable failures must pause completion rather than produce silent item exclusions or replacement-source labels.

### 4. Make lock verification operational
**Classification: MINOR_CLEANUP**

**Issue:** Hashes establish integrity relative to a trusted record; they do not themselves prevent replacement of both files and their recorded hashes.

**Recommended correction:** Preserve a dated, independently retained or write-protected lock manifest. Validate exact equality with the frozen ID universe, not just 350 unique IDs. Recompute hashes before downstream access, bind authorization to that lock, and retain audit findings and reference revisions in separate versioned artifacts.

### 5. Define preflight acceptance evidence
**Classification: MINOR_CLEANUP**

**Issue:** All execution-verification flags are currently false, appropriately reflecting an untested implementation.

**Recommended correction:** Use sterile inspection and synthetic smoke testing to establish fresh-context creation, empty-workdir state, benchmark-path omission, and absence of actual tool calls. Record the available telemetry and its coverage. An absence of visible tool calls is evidence only to the extent that telemetry captures them.

Document exposed model identity, execution dates, configuration, and settings. Any inability to establish the required controls prevents **benchmark authorization**, not the diagnostic preflight intended to test them.

### 6. Clarify phase order and review exposure
**Classification: MINOR_CLEANUP**

**Issue:** The reference state machine omits the stability-analysis step that appears in the final decision sequence.

**Recommended correction:** State that blind concordance outputs are generated and preserved from the verified lock before reference access. Document who verifies the lock and enables the reference join. Keep Astra methodology-review context outside annotation contexts; disclose any earlier partial-label exposure relevant to the later review.

## ASSESSMENT — RESOURCE-FEASIBILITY AMENDMENT
**MAJOR_NONBLOCKING_LIMITATION.** Defensible on the supplied chronology. The documented operational trigger, early amendment, and complete exclusion of historical judgments make unacceptable outcome-driven bias unlikely on the stated facts. Preserve the amendment and exposure history.

## ASSESSMENT — SINGLE STUDENT
**MAJOR_NONBLOCKING_LIMITATION.** Sufficient for this individual’s blind audit, with no human IAA or general human-labelability claim.

## ASSESSMENT — SINGLE MODEL_G
**MAJOR_NONBLOCKING_LIMITATION.** Sufficient as one comparison source. It cannot support cross-model validation, repeated-run reliability, or immutable-revision reproducibility.

## ASSESSMENT — STUDENT ↔ MODEL_G CONCORDANCE
**ACCEPTABLE_AS_DESIGNED.** Two sources suffice to calculate the proposed pairwise descriptive metrics. Disagreement identifies cases for examination; it does not identify which source is wrong or establish a taxonomy defect.

## ASSESSMENT — PROCEDURAL INDEPENDENCE
**ACCEPTABLE_AS_DESIGNED.** The proposed isolation meaningfully limits cross-query information transfer if verified. Describe it as procedural separation of model annotation calls. Statistical independence and hidden provider isolation are not established.

## ASSESSMENT — PURPOSIVE 350 SAMPLE
**MAJOR_NONBLOCKING_LIMITATION.** Appropriate for challenge-sample boundary analysis. Generalization and precision claims must respect enrichment, repeated items, and contrast-group dependence.

## ASSESSMENT — PARTIAL ASTRA QUARANTINE
**ACCEPTABLE_AS_DESIGNED.** Provenance retention with exclusion from active loaders and metrics is appropriate. Historical judgments must not become tie-breakers, selective supplementary evidence, or annotation guidance.

## ASSESSMENT — FIRST-PASS LOCK
**ACCEPTABLE_AS_DESIGNED.** The four-file lock is coherent and protects the identity of first-pass evidence when coupled with trusted manifest retention and hash revalidation. It cannot retrospectively prove blindness or prevent undocumented pre-lock editing.

## ASSESSMENT — EXPLICIT REFERENCE JOIN
**ACCEPTABLE_AS_DESIGNED.** Separating lock creation from reference authorization is a meaningful safeguard. Every reference-loading path must enforce both conditions.

## ASSESSMENT — AUTHOR-LED GOLD-BOUNDARY AUDIT
**ACCEPTABLE_AS_DESIGNED.** All-item review, explicit unresolved outcomes, and rejection of automatic majority adjudication are appropriate. Audit conclusions must remain distinguishable from frozen reference concordance and first-pass measurements.

## ASSESSMENT — ASTRA REVIEW ROLE
**ACCEPTABLE_AS_DESIGNED.** Using the same model family for methodology review does not itself create circularity. Circularity would arise if its review were counted as empirical confirmation, or historical labels influenced active annotations or adjudication. This review supplies no third annotation vote.

## CLAIMS THAT ARE SUPPORTABLE

- Descriptive student–MODEL_G primary-label concordance on the frozen sample.
- Exact acceptable-set agreement, overlap, and clarification concordance for this pair.
- Observed class, parent-boundary, operation, and contrast-group behavior under predefined rules.
- Student-reported burden and difficulty under the recorded schedule.
- Post-authorization concordance with the frozen reference.
- Author-identified candidate guideline, reference, and taxonomy issues, with unresolved explanations retained.
- “Annotation stability” only when explicitly defined as **observed cross-source concordance in this execution**.

## CLAIMS THAT MUST NOT BE MADE

- Human inter-annotator agreement or population-level human labelability.
- Independent dual-model or cross-model-family validation.
- Within-student, within-model, or temporal repeatability.
- Statistical independence of judgments because contexts were fresh.
- Representative commuter-traffic agreement, ambiguity, or performance estimates.
- Correctness inferred solely from concordance.
- Taxonomy defects inferred automatically from disagreement.
- T2/T3 superiority inferred solely from raw agreement, Jaccard, or κ.
- Independent gold adjudication from the author-led audit.
- Exact reproducibility established by configuration hashes.
- Astra review as independent empirical corroboration.

## REQUIRED CHANGES BEFORE MODEL_G PREFLIGHT

**None to the substantive study design.**

Preflight may establish and document the outstanding controls. Benchmark execution remains contingent on successful preflight/smoke verification and separate authorization. Freeze the relevant scheduling, validation, repair, and analysis rules before benchmark execution or exposure to the corresponding results.

## RECOMMENDED DISCLOSURES FOR FINAL REPORT

- Original and amended source configurations, amendment timing, and quota-failure provenance.
- The 23 excluded Astra T2 judgments, zero Astra T3 judgments, and absence of real MODEL_B annotations.
- Access to partial historical outputs and any influence on subsequent design.
- Student competence, training, project involvement, scheduling, and burden.
- Purposive enrichment, fixed sample size, and contrast-group dependencies.
- MODEL_G identity as exposed, execution surface/dates, unavailable immutable revision, and configuration hashes.
- Preflight evidence, telemetry coverage, failures, transport retries, and format repairs.
- Metric definitions, denominators, set sizes, and undefined results.
- Lock verification and separate reference authorization provenance.
- Separation of frozen reference comparisons, author audit findings, and any revised reference.
- The non-empirical role of Astra review.

## MODEL_G PREFLIGHT/SMOKE TEST MAY PROCEED

**YES**

## FINAL REVIEW CONCLUSION

The amendment preserves a scientifically useful but narrower study. Proceed with sterile preflight and synthetic smoke testing. Subject to successful execution verification, the resulting evidence can support descriptive student–model concordance and boundary analysis on this fixed challenge sample. It cannot establish general annotation reliability or independently settle the T2/T3 decision.
