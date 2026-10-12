# Name recognition and transport-data coverage

The academic UI reads the original canonical name index. The small seven-location JSON file supplies curated demo facts; it is not a whitelist of recognizable names. No new classifier or data-import system was added for this correction.

## Records in the existing snapshot

| Category | Name records |
| --- | ---: |
| Bus stops | 6,870 |
| Metro | 157 |
| Suburban rail | 107 |
| MRTS | 2 |
| Places / landmarks | 1,621 |

These are database records, including duplicate names and physical-stop variants. They are not counts of unique operational stations or proof of complete Chennai coverage.

`CanonicalResolver` loads canonical names, stored name variants, the existing Hindi gazetteer and alias catalog. Exact names and these aliases are recognized. Other spellings can still fail; this is not a learned general-purpose NER model. Additional project aliases for Mambalam and Park refer to existing records and are development-authored spellings.

## Why a known name may still need clarification

Guindy has bus, Metro and railway records. A bare name does not always select the physical boarding stop. Park station has Chennai Park, Park Town and bus-stop candidates. Candidate names and modes are displayed; the app asks for the full name and mode rather than selecting a different station silently.

Open route questions can return published options with explicit boarding/alighting names, instead of requiring a mode first. An explicit mode is preserved: missing Metro coverage is not replaced with a bus or MRTS answer. Dates, clock constraints, fastest/cheapest requests and unknown waypoints cannot be discarded by a curated example.

Nearby-stop requests keep the anchor and target separate: in `Velachery station ke paas bus stop kaunsa h?`, Velachery is the station anchor and bus is the requested nearby target. Existing coordinate lookup returns stop options and straight-line distances; these do not verify a walking route. Equivalent Hindi wording uses the same operation. Where station coordinates conflict across sources, distances stay unknown rather than asking the user to repeat an already explicit mode. Guindy Metro has such a conflict: its [official station page](https://chennaimetrorail.org/station-information/guindy/) supplies associated bus-stop names that can still be returned without a distance estimate. Without a published fallback, the result states the location-data gap.

For example, `Chennai Park railway station` and `Park Town railway station` resolve different records. `Velachery MRTS station` resolves the MRTS record. `Marina Beach` is recognized as a landmark and can also collide with nearby bus-stop names.

## Recognition is separate from an answer

The SQLite snapshot contains bus route sequences and limited Metro sequences. It has suburban-rail station names but **no suburban-rail or MRTS route sequences or departure schedules**. Therefore Central and Mambalam can both be recognized while their train route or first departure remains unavailable.

Two supplementary Central/Velachery journey-guidance records use Southern Railway's [published MRTS table](https://sr.indianrailways.gov.in/uploads/files/1345106736152-MRTS%20WEEK.pdf), which places Park Town and Velachery on the same line. They name Park Town as the separate boarding/alighting station near the Central context. They do not verify the access path from Central, current operation, departure times or an optimized journey. The document's current timetable validity is unverified; no times were imported. Canonical Park Town's provisional mode bucket is not relabeled in SQLite.

The app reuses the existing read-only route and timetable service when physical entities are sufficiently clear. Returned bus records are published community GTFS snapshots, not live service confirmations. Missing records do not prove a real service is absent. Accessibility facts, walking access, current timings, booking and train tracking remain limited or unavailable as described in [known limitations](KNOWN_LIMITATIONS.md).

Intent classification is another separate stage. Both models still make wording errors, especially on unfamiliar Hindi/Hinglish phrasing. The default TF-IDF baseline has stronger validation results; the UI shows the actual selected model and its prediction without overriding the intent using station names.
