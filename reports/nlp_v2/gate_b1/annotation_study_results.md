# Gate B.1 Simulated Annotation-Boundary Stress Indicators

> [!WARNING]
> **SIMULATED ANNOTATION NOTICE (Gate B.2 Pre-Freeze Audit)**:
> Previous Gate B.1 agreement numbers below were produced by a deterministic annotation-boundary simulation (`scripts/nlp_v2/gate_b1/annotation_study.py`) and do **not** represent real human inter-annotator agreement. Reviewer 1 emitted gold labels while Reviewer 2 applied deterministic heuristic perturbations. These numbers are preserved purely as a diagnostic benchmark of boundary brittleness under synthetic persona stress, NOT as human consensus metrics. Real human annotation must be conducted in Gate B.2.

**Sample Size:** 350 challenging transit utterances (minimal pairs, ambiguous queries, implicit intents)  
**Protocol:** Deterministic dual-persona simulation evaluating surface text under heuristic perturbation rules.  

---

## Key Findings: Simulated Boundary Stress Indicators (T2 vs. T3)

| Metric | T2 Medium (12 Intents) | T3 Fine (16 Intents) | Difference (T2 - T3) |
| :--- | :--- | :--- | :--- |
| **Raw Agreement** | **75.71%** (265/350) | **70.29%** (246/350) | **+5.43%** |
| **Cohen's Kappa ($\kappa$)** | **0.6959** | **0.6685** | **+0.0273** |
| Disagreement Count | 85 | 104 | -19 |

---

## Disagreement Breakdown

### T2 Medium Disagreements

- `route_query vs service_availability`: 17 cases
- `service_timing vs route_stops`: 15 cases
- `route_query vs service_timing`: 15 cases
- `route_query vs route_stops`: 12 cases
- `service_availability vs service_timing`: 12 cases

### T3 Fine Disagreements

- `point_to_point_route vs mode_availability`: 17 cases
- `scheduled_departure vs route_stop_sequence`: 15 cases
- `point_to_point_route vs scheduled_departure`: 15 cases
- `point_to_point_route vs route_stop_sequence`: 12 cases
- `mode_availability vs first_and_last_service`: 12 cases
- `route_stop_sequence vs scheduled_departure`: 12 cases
- `scheduled_departure vs first_and_last_service`: 12 cases
- `route_stop_membership vs route_stop_sequence`: 6 cases

---

## Architectural Interpretation (Heuristic Boundary Simulation)

1. **T2 Medium achieves higher simulated persona agreement** ($\kappa = 0.6959$, 75.7%) compared to T3 Fine ($\kappa = 0.6685$, 70.3%) under the deterministic heuristic rules.
2. **T3 produces 104 simulated disagreements** (29.7% disagreement rate) across fine-grained subtype boundaries:
   - `point_to_point_route` vs `multimodal_route`: Heuristic rules flag divergence when surface phrasing lacks explicit multimodality keywords.
   - `route_stop_sequence` vs `route_stop_membership`: Elliptical queries (e.g. `'21G Guindy?'`) trigger divergent heuristics between stop presence check and corridor sequence display.
   - `service_frequency` vs `scheduled_departure`: Heuristics for peak hour headway queries blend timetable inquiry with frequency lookups.
3. **Conclusion & Mandatory Next Step**:
   While the simulated stress test suggests T2 boundaries are less brittle under heuristic perturbation, this does **not** substitute for real human consensus. Gate B.2 must execute a genuine blind study with two independent human annotators before any final taxonomy decision.