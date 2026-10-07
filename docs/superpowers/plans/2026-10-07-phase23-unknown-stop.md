# Phase23 follow-up: unknown coordinated timetable locations

User instruction: “Fix it.” This authorizes the residual third-stop correctness
repair and its tests/reviews/commits. It does not explicitly authorize a second
post-fix evaluation. Preserve both valid completed evaluations unchanged. The
final corrected source will be a separate freeze, with no matching aggregate
measurement unless the user separately authorizes another run.

Root cause: timetable cardinality counts canonical spans; unknown coordinated
location text disappears before the count. Correct only this timetable scope
boundary, using syntax around recognized locations. Never resolve an unknown
name or add aliases. Decline unrepresentable coordinated location lists through
the existing multiple_goals clarification before domain execution.

- [x] Synthetic regressions across all3 intents: unknown endpoint before/after a
  recognized name, source/destination coordination, Hindi/Roman/noisy inputs,
  comma lists, unknown single-token names, and ordinary time/date/route/first-
  last conjunctions, canonical names containing conjunctions/punctuation.
- [x] Observe reds on committed e008c047; implement the timetable-only guard.
- [x] Focused and complete verification, compile/pip/diff and preserved hashes.
- [x] Fresh GPT-6.1 Sol xhigh scoped review, resolve all material findings.
  267 independent tests and300 synthetic probes; zero unresolved findings.
- [ ] Commit behavioral correction separately and record full final freeze.
- [ ] Update limitations/sequence/acceptance docs, preserving both evaluations
  as historical for their recorded sources. No evaluator rerun or metric tuning.
- [ ] Fresh final whole-project Sol xhigh review, final verification, commit/push
  clean main. Report any remaining original acceptance condition honestly.
