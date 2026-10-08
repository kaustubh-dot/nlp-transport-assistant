# Hinglish route diagnosis — 2026-10-08

User reproduction: `guindy se central kaise jau`.

Source: `12a0b1f3802dd34711c1649435c3db1b70637e48`; real local API http://127.0.0.1:8875/api/v2/query. Three manual diagnostic POSTs were made. This is a user-reported product diagnosis, not an evaluator, benchmark, training or model-selection run. No production changes were made.

## Observed responses

| Question | Intent | Status/reason | Relevant result |
|---|---|---|---|
| guindy se central kaise jau | point_to_point_route | clarification / entity_ambiguity | origin=HUB_GUINDY; destination unresolved between two Central hubs; operation=null |
| How do I get from Guindy to Chennai Central? | point_to_point_route | clarification / entity_ambiguity | Same origin and same two unresolved Central hubs |
| guindy metro se chennai central metro kaise jau | point_to_point_route | unavailable / unsupported_source | PLAN_ROUTE; transport_mode=metro; published_mode_topology_absent |

The first two responses say “Please clarify which stop or location you mean.” The third says “No mode-consistent published topology is available for the requested transport mode.”

## Root cause for this example

The real retained classifier selected the requested route intent for all three questions. Read-only extraction of the exact user query recognizes Guindy, the Roman-Hindi source marker `se`, and Central; it assigns Guindy as origin. The failure occurs during canonical destination resolution, after intent recognition.

`Central` maps to both `HUB_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL` and `HUB_PURATCHI_THALAIVAR_DR__M__G__RAMACHANDRAN_CENTRAL`. They have similar canonical names but different member stations: the former contains a metro station and the latter a suburban-rail station. Both hubs have null coordinates and unverified memberships. They cannot simply be declared interchangeable or collapsed from their similar names. The Guindy hub contains bus/suburban-rail members, with unverified memberships; explicit Guindy metro resolves separately.

The English comparison reaches exactly the same destination ambiguity. Thus this particular failure does not justify retraining or a Hinglish intent override. Separate Hinglish answer-selection failures remain documented in the browser QA report; this example does not invalidate them.

When metro is explicit, the domain's mode preflight refuses route execution because this snapshot has no usable mode-consistent metro topology. That reply does not establish that no metro service exists in the real world; it describes unavailable repository evidence. The metro comparison's returned slots contain the origin only, so no complete destination resolution is claimed from that preflight refusal.

## Product work indicated

The generic clarification gives the user little help even though the location names were understood. Better clarification should identify Central as the unresolved destination and present meaningful station/mode choices, preserving physical-node distinctions and verified provenance. Actual metro directions additionally require a usable, sourced metro route graph. Changing spelling or language alone cannot supply that missing evidence.

These are recommendations, not implemented or verified fixes. The prior Phase23 exception prohibited unrelated alias, classifier and domain changes. This diagnosis preserves that source and all frozen research/data/evaluation artifacts; no model, alias, canonical DB or inference contract was changed. A new scoped product task would need to explicitly establish the allowed clarification/data-integration work before changing those boundaries.

Evidence inspected: `src/nlp_v2/assistant.py`, `model.py`, `entities.py`, `slots.py`, `domain.py`; read-only canonical `transport_hubs`, `hub_members` and relevant `transport_stops` rows. No held-out rows or failures were inspected. Existing multilingual assistant unit tests inject a fixed intent and therefore test downstream behavior, rather than proving broad real-model Hinglish accuracy.
