# Gate B.3 Student-Arm Retirement Amendment

**Status:** ADOPTED
**Date:** 2026-09-24

## Change

The planned `STUDENT_R1` annotation arm is retired and excluded from Gate B.3.

No student-derived agreement, human IAA, annotation-stability, or
student-model concordance claims will be made.

Any partial student annotations, if present, are archived and excluded from
all analysis.

## Timing

This amendment occurs:

- after completion of the blind MODEL_G campaign;
- before first-pass lock;
- before reference/gold join;
- before reference concordance analysis;
- before the T2 vs T3 taxonomy decision.

## Active Gate B.3 Evidence

The active first-pass source is:

- `MODEL_G` / Gemini 3.8 Flash
- 350 T2 judgments
- 350 T3 judgments

After cryptographic first-pass locking, MODEL_G may be compared against the
frozen reference labels.

A small GPT-5.6 Sol review may later be used as a targeted qualitative audit
of selected difficult or disagreement cases. It is not a replacement human
annotator and is not a complete second-model benchmark.

## Permitted Claims

- MODEL_G-reference concordance on the fixed purposive challenge sample;
- T2 vs T3 error and semantic-boundary analysis;
- targeted qualitative review of selected difficult cases.

## Prohibited Claims

- human inter-annotator agreement;
- student-model concordance;
- population labelability;
- independent human validation.
