# Small academic project datasets

These files support the original Hindi transport NLP case study. They are generated teaching material and a limited sourced lookup catalog, not a population-level evaluation corpus.

| File | Purpose |
| --- | --- |
| [hindi_intents.csv](hindi_intents.csv) | 1,652 rows: 1,452 template variants, twenty short railway seeds and 180 varied AI-authored training examples |
| [entity_slots.csv](entity_slots.csv) | 320 linked synthetic route/availability examples with origin, destination and mode annotations |
| [development_examples.json](development_examples.json) | Ninety paired Hindi/Hinglish development scenarios replacing repetitive training rows |
| [academic_checks.json](academic_checks.json) | Ninety AI-authored diagnostic questions, never literal training inputs; development-exposed, not a blind holdout |
| [user_questions.json](user_questions.json) | Four user-authored qualitative checks; exact questions excluded from training |
| [development_history.json](development_history.json) | Original user-check failures retained before the general training-data correction |
| [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md) | Nine-intent definitions and slot-labeling conventions |
| [chennai_case_study.json](chennai_case_study.json) | Seven locations, eight directed Metro links, two bus snapshot connections, two Central Metro accessibility facts and one historical terminal window |
| [communication_phrases.json](communication_phrases.json) | Five fixed Hindi–Tamil transport phrases; not a translation training corpus |

Intent rows have `text`, `intent`, `family_id`, `split`, `source`, `human_reviewed` and `language`. Every generated row is explicitly `human_reviewed=false`. Related Hindi/Hinglish template families and all their slot/politeness variants stay in one split. Short seeds and varied AI-authored development examples belong only to training. The split contains 1,112 training, 216 validation and 324 test rows. Six classes have 180 rows each; train status and railway complaint have 190 each; accessibility has 192. Input-language counts are 1,090 Hindi and 562 Hinglish rows.

The 320 slot rows are linked to intent questions; they are not an independent corpus. Their 72 test rows measure only origin/destination/mode extraction. The separate 90-question diagnostic additionally checks complaint type, accessibility feature, response status and catalog record IDs. Its bilingual pairs are related scenarios, not independent passengers.

Regenerate with `python -m scripts.nlp_v2.build_project_dataset`. Train with `python -m scripts.nlp_v2.train_project`; run diagnostics with `python -m scripts.nlp_v2.evaluate_project`. MuRIL epoch selection uses validation only. The supplied brief and diagnostic failures informed development data; no frozen 400-query challenge was used. The user's exact questions are not training examples. Their failures did inform varied route wording and scheduled-rail development examples, so their final outcomes are not independent accuracy evidence.

These are declared template-family splits, not proof of linguistic independence: similar vocabulary, sentence structures and locations appear across different templates. The reused encoder also has prior transport training. Treat results as an academic component comparison, with a small known-domain test set, rather than evidence of real-passenger reliability.

The catalog references the existing canonical snapshot and official CMRL station/map sources. It supplies curated examples, not a seven-name recognition whitelist: the app recognizes all canonical station/stop/place names and stored aliases, and reuses the existing read-only service for additional route/timetable lookups. Name collisions require clarification. Railway name records do not supply the absent rail routes or schedules. A nearby bus-stop record does not verify a particular bus trip or walking route. Central accessibility facts refer to **Metro**, not Railway Station. Empty or absent facts must remain unknown.

The Tamil phrases are prototype drafts, including the airport-bus example from the supplied project brief. Have a Tamil speaker review them before using them for passenger communication. General translation, audio and additional phrases are optional enhancements.
