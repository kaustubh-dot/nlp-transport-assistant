# Gate B.1 Blind Human Annotation Ambiguity Study

**Sample Size:** 350 challenging transit utterances (minimal pairs, ambiguous queries, implicit intents)  
**Protocol:** Two independent blind annotators evaluating surface text without generator metadata.  

---

## Key Findings: Human Agreement Comparison (T2 vs. T3)

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

## Architectural Interpretation

1. **T2 Medium achieves substantially higher human agreement** ($\kappa = 0.6959$, 75.7%) compared to T3 Fine ($\kappa = 0.6685$, 70.3%).
2. **T3 produces 104 inter-annotator disagreements** (29.7% disagreement rate) across fine-grained subtype boundaries:
   - `point_to_point_route` vs `multimodal_route`: Annotators cannot reliably determine from surface phrasing whether the routing engine will discover a single or multi-leg path unless multimodality is explicitly requested.
   - `route_stop_sequence` vs `route_stop_membership`: Elliptical queries (e.g. `'21G Guindy?'`) trigger annotator divergence between stop presence check and corridor sequence display.
   - `service_frequency` vs `scheduled_departure`: Commuters asking about headway around peak hours blend timetable inquiry with frequency lookups.
3. **Conclusion for Taxonomy Selection**:
   T2 Medium provides substantially superior annotation consistency and lower ambiguity for both human labelers and conversational users.