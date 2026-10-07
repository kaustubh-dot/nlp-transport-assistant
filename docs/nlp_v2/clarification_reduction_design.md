# Phase 13 clarification reduction design

Use the reviewed v1 development suite and canonical contracts. Preserve T3,
checkpoint, raw inference, snapshot and all historical research. Implement only
safe execution requirements, exact context resolution and known unavailable
capability behavior. No fuzzy matching or new entity aliases in this phase.

## Execution requirements

All three schedule operations consume station/stop/origin. A request naming only
a route cannot mean a particular boarding station safely, so ask for the station
rather than aggregate every intermediate stop. Frequency also needs a route or
line; prompt for it when absent. Scheduled departure must accept an already
supplied origin. First/last does not require a route because a station-wide
published schedule is legitimate when no corridor is requested. Slot allowlists
remain operation-specific and all 16 intent mappings stay fixed.

## Exact resolution

Normalize route-context index keys exactly as canonical domain lookup (case,
spaces and delimiters), preserving suffixes. Only operational, mode-consistent
route-stop links can constrain ambiguous membership stops or timing stations.
A single on-route exact candidate may resolve; multiple candidates must clarify.
An explicit off-route or incompatible stop remains explicit and cannot be
substituted. No coordinate/name proximity merge or guessed access connection.

## Non-actionable questions

Add `CanonicalTransitService.preflight(operation: str) -> ServiceResult | None`
for capability scopes whose unavailability is certain independent of input:
policy absent, facilities unimplemented/unknown, no confirmed multimodal graph,
no confirmed interchange, accessibility entirely null. Source inspection must
be read-only; a DB error returns a safe error, never an unavailable success.
Specific supported operations continue extraction and ordinary dispatch.

Assistant invokes preflight after validated semantic intent and explicit
multiple-goal guard, before asking entity/temporal/missing-slot questions. The
method is optional for injected services, so existing test/service integrations
without capability inspection retain their dispatch path. A preflight result
carries the selected operation and explicit unavailable reason without asking
for an irrelevant station. Intent ambiguity/multiple goals still clarify.

## Verification

TDD catches missing frequency/schedule inputs, origin acceptance, route-context
casing/spaces, ambiguous and incompatible nodes, absent-policy Guindy questions,
and preservation of multiple-goal ambiguity. Run actual suite before/after with
real classifier plus labeled gold-intent diagnostics. Track both false-positive
clarification and total clarification; accept no silent candidate selection.
Remaining unsupported time/mode constraints and new static answer paths belong
to later reviewed phases. Fresh Sol xhigh reviews before commit/push.
