# Product requirements: Hindi Chennai transport assistant

## Goal and users
Help Hindi/Hinglish-speaking visitors ask about a small, documented set of Chennai Metro journeys and station facilities using local text input and Hindi responses.

## MVP boundary
- Seven intent labels remain useful for classification, including unsupported requests.
- Support only explicitly stored origin/destination routes and individual facility lookups. No shortest-path search, arbitrary transfers, or complete network coverage.
- First verified release targets Metro. Existing bus/suburban records are unverified demo fixtures, not supported passenger guidance.
- Timetables, exact fares, ticket rules, live status, speech, Tamil translation, and cross-mode journey planning are deferred. Respond with an explicit limitation.
- Single-turn input only. On missing information, ask the user to submit the complete question again; no conversation memory.
- Absence from the database means unknown, not that a service does not exist. Facility values are 1 (recorded available), 0 (recorded unavailable), or NULL (unknown). Availability does not establish current working status.

## Acceptance gates (targets, not achieved results)
1. Data: every released factual record has a source URL, retrieval date, source version/effective date where available, and verification entry in DATA_SOURCES.md. Remove or exclude unverified records before calling the release verified.
2. Intent quality: Macro-F1 >= 0.85 on an independently authored and manually reviewed set of at least 140 questions (at least 20 per intent). Include formal/colloquial Hindi, Roman Hindi, code mixing and typos; report counts and per-intent results.
3. Slots: >= 0.90 exact match over all applicable slots, counting unwanted extracted slots as errors. Manually label station, origin, destination, mode and requested facility. Do not use current synthetic slot hints as gold.
4. End-to-end: >= 0.85 on that reviewed set, requiring correct intent, applicable slots, retrieval facts and response; use expected clarification/refusal for unsupported cases. No invented fares, times or facilities in regression cases.
5. Performance: warm p95 latency <= 1 second over 100 local baseline queries; record CPU, memory, package versions and sample set.
6. Reproducibility: clean install, database generation, dataset generation, baseline training and tests succeed. Benchmarking must refuse missing trained weights and leaking/missing test splits.

## Release decision
Proceed with prototype development. Passenger-facing release remains blocked on source verification and the independent acceptance set. Synthetic holdout metrics are development diagnostics only. Compare MuRIL only after the baseline and data gates are established.
