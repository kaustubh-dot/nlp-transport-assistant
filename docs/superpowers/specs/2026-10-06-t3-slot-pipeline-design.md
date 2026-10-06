# T3 slot extraction and canonical resolution design

**Intent:** Convert English, Hindi, Roman Hindi, Hinglish, and mixed-script commuter text into the typed canonical slots consumed by the T3 dispatcher, while preserving uncertainty instead of inventing IDs or times.

## Boundary and data

The production extractor is separate from the old seven-label `EntityExtractor`. It reads the canonical `data/canonical/transit/canonical_transport.db` only. The frozen 23-slot ontology and `docs/nlp_v2/entity_resolution_contract.md` define types, mode qualification, hubs, route numbers, and temporal ambiguity. No Gate B.2/B.3 evaluation rows or labels are used.

`CanonicalResolver` loads names from `transport_stops`, `stop_names`, `transport_hubs`, `places`, and `place_names`. It augments those English/Tamil records with curated Hindi/Roman aliases from the existing production gazetteer, resolving each alias to current database IDs by name rather than using the legacy IDs. A match retains the surface and candidate IDs. Exact names and aliases take precedence; no fuzzy guess becomes a canonical ID. Generic open journey locations prefer a matching hub; mode-qualified station requests select the matching physical stop; unresolved duplicate physical nodes produce candidate IDs and an `entity_ambiguity` state. A route-constrained stop can use the route's actual `route_stops` membership to disambiguate.

## Extraction

`T3SlotExtractor.extract(query, intent)` returns `ExtractionResult(slots, spans, unresolved, clarification_reason, requested_modes, normalized_query)`. Normalization preserves the raw query and uses the existing Unicode/whitespace normalizer for matching. Longest non-overlapping names are matched first. Directional cues assign origin/destination; one named location is never silently used as both. Station, stop, landmark, and locality roles depend on the T3 intent. Route codes preserve letters, suffixes, `#`, and `-ET`; official modes, ticket/fare/facility/accessibility enums, preferences, line names, stage numbers, dates, and time are extracted only when explicit in the utterance.

Explicit clock periods yield ISO time. Bare `8 baje` or `8 o'clock` yields two candidates and `temporal_ambiguity`. Overnight `raat 12` is midnight and `raat 1` is 01:00; uncertain night hours remain candidates. Bare `kal`/`कल` remains unresolved unless an explicit date is supplied or tense proves past/future; the current phase retains it and asks for clarification. Multiple physical matches produce `entity_ambiguity` and no arbitrary slot ID. Requested modes are separately retained for later multimodal service constraints without changing the canonical slot ontology. Explicit `via` waypoints are assigned by marker whether they occur before or after the destination.

## Verification

Tests use a tiny temporary canonical-shaped SQLite database and synthetic queries. They cover hub vs mode-specific resolution, duplicate station names, route-constrained stop resolution, Hindi/Roman/mixed text, route suffix preservation, mode and amenity enums, explicit vs ambiguous times, `kal`, and unknown entities. A read-only smoke check against the shipped canonical DB verifies the actual schema connection.
