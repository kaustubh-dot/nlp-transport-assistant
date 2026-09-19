# Gate B.1 Pre-Training Lexical Shortcut Audit

**Dataset:** Gate B.1 Hard-Boundary Stress Corpus (2512 examples)  
**Target:** Evaluate token-to-label association, conditional purity $P(\text{label} \mid \text{token})$, and potential single-word lexical giveaways across candidate taxonomies T2 and T3.  

---

## T2 Taxonomy Lexical Audit

### Monitored Key Transit Terms in T2

| Term | Frequency | Dominant Label | Purity $P(\text{Label} \mid \text{Term})$ | Distributed Labels Count |
| :--- | :--- | :--- | :--- | :--- |
| `frequency` | 33 | `service_timing` | 100.00% | 1 |
| `headway` | 8 | `service_timing` | 100.00% | 1 |
| `interval` | 2 | `service_timing` | 100.00% | 1 |
| `fare` | 48 | `fare_query` | 100.00% | 1 |
| `ticket` | 33 | `fare_query` | 84.85% | 2 |
| `tariff` | 25 | `fare_query` | 100.00% | 1 |
| `cost` | 3 | `fare_query` | 100.00% | 1 |
| `charge` | 1 | `fare_query` | 100.00% | 1 |
| `live` | 81 | `realtime_status_query` | 100.00% | 1 |
| `gps` | 43 | `realtime_status_query` | 100.00% | 1 |
| `delay` | 27 | `realtime_status_query` | 100.00% | 1 |
| `tracker` | 31 | `realtime_status_query` | 100.00% | 1 |
| `interchange` | 45 | `interchange_query` | 82.22% | 2 |
| `change` | 20 | `interchange_query` | 65.00% | 2 |
| `transfer` | 19 | `interchange_query` | 100.00% | 1 |
| `switch` | 9 | `interchange_query` | 100.00% | 1 |
| `sequence` | 18 | `route_stops` | 100.00% | 1 |
| `stops` | 33 | `route_stops` | 78.79% | 2 |
| `halts` | 25 | `route_stops` | 100.00% | 1 |
| `list` | 25 | `route_stops` | 100.00% | 1 |
| `halt` | 16 | `route_stops` | 100.00% | 1 |
| `stop` | 32 | `route_stops` | 65.62% | 2 |
| `touch` | 1 | `route_stops` | 100.00% | 1 |
| `first` | 31 | `service_timing` | 100.00% | 1 |
| `early` | 16 | `service_timing` | 100.00% | 1 |
| `earliest` | 5 | `service_timing` | 100.00% | 1 |
| `last` | 56 | `service_timing` | 100.00% | 1 |
| `night` | 47 | `service_timing` | 82.98% | 2 |
| `midnight` | 3 | `service_timing` | 100.00% | 1 |
| `schedule` | 49 | `service_timing` | 100.00% | 1 |
| `timetable` | 43 | `service_timing` | 100.00% | 1 |
| `scheduled` | 62 | `service_timing` | 100.00% | 1 |

### Highly Predictive Tokens in T2 (Min Frequency 10, Purity $\ge$ 95%)

Found **498** tokens meeting extreme single-label association criteria.

| Token | Frequency | Dominant Label | Purity |
| :--- | :--- | :--- | :--- |
| `parking` | 102 | `station_facilities` | 100.00% |
| `live` | 81 | `realtime_status_query` | 100.00% |
| `kitne` | 65 | `service_timing` | 100.00% |
| `scheduled` | 62 | `service_timing` | 100.00% |
| `baje` | 57 | `service_timing` | 100.00% |
| `reach` | 56 | `route_query` | 100.00% |
| `last` | 56 | `service_timing` | 100.00% |
| `schedule` | 49 | `service_timing` | 100.00% |
| `fare` | 48 | `fare_query` | 100.00% |
| `kab` | 46 | `service_timing` | 100.00% |
| `lift` | 45 | `accessibility` | 100.00% |
| `timetable` | 43 | `service_timing` | 100.00% |
| `gps` | 43 | `realtime_status_query` | 100.00% |
| `gap` | 42 | `service_timing` | 100.00% |
| `बह` | 40 | `service_timing` | 100.00% |

---

## T3 Taxonomy Lexical Audit

### Monitored Key Transit Terms in T3

| Term | Frequency | Dominant Label | Purity $P(\text{Label} \mid \text{Term})$ | Distributed Labels Count |
| :--- | :--- | :--- | :--- | :--- |
| `frequency` | 33 | `service_frequency` | 100.00% | 1 |
| `headway` | 8 | `service_frequency` | 100.00% | 1 |
| `interval` | 2 | `service_frequency` | 100.00% | 1 |
| `fare` | 48 | `fare_calculation` | 100.00% | 1 |
| `ticket` | 33 | `fare_calculation` | 84.85% | 2 |
| `tariff` | 25 | `fare_calculation` | 100.00% | 1 |
| `cost` | 3 | `fare_calculation` | 100.00% | 1 |
| `charge` | 1 | `fare_calculation` | 100.00% | 1 |
| `live` | 81 | `realtime_status_query` | 100.00% | 1 |
| `gps` | 43 | `realtime_status_query` | 100.00% | 1 |
| `delay` | 27 | `realtime_status_query` | 100.00% | 1 |
| `tracker` | 31 | `realtime_status_query` | 100.00% | 1 |
| `interchange` | 45 | `interchange_transfer` | 82.22% | 2 |
| `change` | 20 | `interchange_transfer` | 65.00% | 2 |
| `transfer` | 19 | `interchange_transfer` | 100.00% | 1 |
| `switch` | 9 | `interchange_transfer` | 100.00% | 1 |
| `sequence` | 18 | `route_stop_sequence` | 100.00% | 1 |
| `stops` | 33 | `route_stop_sequence` | 78.79% | 2 |
| `halts` | 25 | `route_stop_sequence` | 100.00% | 1 |
| `list` | 25 | `route_stop_sequence` | 100.00% | 1 |
| `halt` | 16 | `route_stop_membership` | 100.00% | 1 |
| `stop` | 32 | `route_stop_membership` | 37.50% | 3 |
| `touch` | 1 | `route_stop_membership` | 100.00% | 1 |
| `first` | 31 | `first_and_last_service` | 100.00% | 1 |
| `early` | 16 | `first_and_last_service` | 100.00% | 1 |
| `earliest` | 5 | `first_and_last_service` | 100.00% | 1 |
| `last` | 56 | `first_and_last_service` | 100.00% | 1 |
| `night` | 47 | `first_and_last_service` | 61.70% | 3 |
| `midnight` | 3 | `first_and_last_service` | 100.00% | 1 |
| `schedule` | 49 | `scheduled_departure` | 100.00% | 1 |
| `timetable` | 43 | `scheduled_departure` | 100.00% | 1 |
| `scheduled` | 62 | `scheduled_departure` | 100.00% | 1 |

### Highly Predictive Tokens in T3 (Min Frequency 10, Purity $\ge$ 95%)

Found **464** tokens meeting extreme single-label association criteria.

| Token | Frequency | Dominant Label | Purity |
| :--- | :--- | :--- | :--- |
| `parking` | 102 | `station_facilities` | 100.00% |
| `live` | 81 | `realtime_status_query` | 100.00% |
| `scheduled` | 62 | `scheduled_departure` | 100.00% |
| `last` | 56 | `first_and_last_service` | 100.00% |
| `schedule` | 49 | `scheduled_departure` | 100.00% |
| `fare` | 48 | `fare_calculation` | 100.00% |
| `lift` | 45 | `station_accessibility` | 100.00% |
| `timetable` | 43 | `scheduled_departure` | 100.00% |
| `gps` | 43 | `realtime_status_query` | 100.00% |
| `gap` | 42 | `service_frequency` | 100.00% |
| `gap_me` | 40 | `service_frequency` | 100.00% |
| `ke_gap` | 40 | `service_frequency` | 100.00% |
| `पहल` | 39 | `first_and_last_service` | 100.00% |
| `wheelchair` | 39 | `station_accessibility` | 100.00% |
| `क_सबस` | 39 | `nearest_transport` | 100.00% |

---
