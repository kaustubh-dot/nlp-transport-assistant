# Implementation roadmap

Use PRD.md as the scope and acceptance contract. Keep evaluation alongside each milestone rather than postponing it to the end. Milestones are dependency ordered, not promised calendar dates.

1. **Reliable demo (current):** correct missing-data responses, remove fabricated fare/time/facility answers, mark fixtures unverified, document single-turn limitations and add regression tests.
2. **Verified Metro slice:** choose a small explicit station/route inventory; obtain exact official source artifacts and terms; record retrieval/effective dates, separate station identities and validate every released fact. Do not add broad bus/rail coverage yet.
3. **Baseline and independent evaluation:** generate family-disjoint synthetic intent data; train TF-IDF; create and manually review at least 140 independent questions; measure intent, all applicable slots, response facts and latency against PRD gates. Preserve MASSIVE's original partitions if it is later integrated, and explicitly map its labels.
4. **Usable text UI:** display scope/data limitations, hide developer details by default, verify missing-slot and unsupported-request flows. No nonfunctional translation/audio buttons.
5. **Optional research comparison:** build a separately pinned MuRIL training environment and compare on the same frozen acceptance set. Promote only if measured benefits justify the dependency/runtime cost.
6. **Later extensions:** additional verified modes, graph routing, calendar-aware timetable and fare models, followed by translation/speech. Each needs its own data and acceptance criteria.

Release requires all PRD acceptance gates; a passing synthetic benchmark alone is insufficient.
