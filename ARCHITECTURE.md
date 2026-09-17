# Architecture and implemented contract

## Pipeline
`normalize → classify → extract slots → SQLite lookup → Hindi response`

Keep the existing modules. The baseline uses word/character TF-IDF and logistic regression; the UI falls back to heuristics if weights are absent. Evaluation requires actual trained weights. MuRIL loading exists but training/comparison are deferred.

## SQLite tables
- `stations`: canonical ID, English/Hindi/Tamil names, type, coordinates.
- `station_aliases`: alias and language/script mapped to a station.
- `connections`: origin, destination, mode, display line description, optional travel time/distance, direct flag. Each row describes a stored journey, not a graph edge for general routing.
- `facilities`: station and nullable 0/1 attributes for wheelchair assistance, lift, tactile paths, accessible toilet and parking.
- `service_info`: legacy demo line-level hours/fare ranges. Retained for development; these fields cannot answer station/day/direction-specific questions and are not used to state passenger timetable or fare answers.

There is no separate ROUTES table, fare table, service calendar or transfer planner. Do not infer exact fares from distance or infer journeys from nearby stops. Split conflated station/terminal identities when verifying the Metro dataset.

## Query contract
Intents: route_query, service_availability, service_timing, station_information, accessibility, ticketing, out_of_scope.

Slots: origin, destination and station use canonical IDs; transport_mode is metro/bus/suburban_rail/railway; information_type identifies the requested facility. Route/availability queries need both endpoints. Facility questions need a station and a recognized facility; unknown facilities receive an unknown response.

Normalization uses NFC and Roman case folding. Gazetteer matching uses longest aliases and fuzzy matching with cutoff 85. Two station names without directional cues use mention order. These are prototype heuristics; validate reversed phrasing, ambiguous aliases and typos on the independent acceptance set.

## Response rules
- Demo responses about records carry an unverified-data warning, including old/custom databases until a verified-data release is implemented.
- Route lookup uses stored pairs only. Missing pair means no recorded answer, never proof of no service.
- Availability distinguishes direct records from recorded journeys requiring changes.
- Facilities check only the requested column: 1, 0, or unknown. A wheelchair does not imply a ramp; a lift does not imply an escalator. No live working-status claim.
- Station information returns recorded identity only; it does not invent amenities.
- Timetables and ticketing remain unsupported even when legacy line-level demo rows exist.
- Clarification is single-turn: users resubmit a complete question. Live status is unsupported.

## Evaluation
Authored template-family IDs keep related Hindi/Hinglish patterns in one split. Fractions are approximate for small inventories. Deduplicate query text; verify family/query disjointness before training/evaluation. Synthetic slot hints are not benchmark gold. Report intent classification and language breakdown on held-out families; independent reviewed cases are required for factual end-to-end results. See PRD.md for release targets.
