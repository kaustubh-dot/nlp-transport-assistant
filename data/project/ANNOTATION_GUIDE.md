# Nine-intent annotation guide

Use the user's requested information to choose one label. Location and mode are slots, not separate intent classes. Questions with multiple competing requests are outside this small single-intent exercise.

| Label | Requested information | Distinction |
| --- | --- | --- |
| `route_query` | How to reach a destination; travel options | “कैसे जाऊँ / kaise jaun” asks for a route |
| `service_availability` | Whether a bus/metro/rail connection exists | “मिलती है / available hai” asks about existence |
| `service_timing` | Published first/last departures, timetable, frequency | Scheduled time, rather than current delay |
| `station_information` | Station details, nearby bus stop, address, facilities | Accessibility-specific assistance has its own label |
| `accessibility` | Lift, wheelchair, ramp, barrier-free access | Ordinary cleanliness complaints are not accessibility |
| `ticketing` | Ticket purchase, reservation, fare, pass, payment | Recognizing a booking request does not imply booking capability |
| `train_status` | Current train position, delay, cancellation | Live information, rather than a published timetable |
| `railway_complaint` | Railway cleanliness, water, food, staff, broken coach facilities | Requests can describe a problem without saying “complaint” |
| `out_of_scope` | Non-transport questions | Unknown transport places are still transport intents |

Origin is where the passenger departs; destination is where they want to go. An unknown name must not be substituted with a known station. `railway station` qualifies a place and does not by itself request travel by rail. Mark `rail` only when rail/train is the requested service. A single named station can be a station context; it need not be both an origin and destination.

AI-authored examples remain `human_reviewed=false`. A human review should check natural wording, the label, and any slot annotations, and record the review separately. Do not relabel generated examples as human-authored.
