# Gate B.3 GPT-5.6 Sol Targeted Audit Protocol

**Status:** FROZEN BEFORE SOL REVIEW
**Date:** 2026-09-24

## Purpose

GPT-5.6 Sol is used only for a small targeted qualitative audit after the
MODEL_G first pass was cryptographically locked and reference concordance was
computed.

It is not a human annotator, not a replacement for STUDENT_R1, and not a
complete second-model benchmark.

## Deterministic Selection Rule

Include every Gate B.3 taxonomy judgment satisfying both conditions:

1. MODEL_G supplied a non-null primary label.
2. MODEL_G primary label differed from the frozen reference primary label.

MODEL_G null-primary/abstention cases are excluded from the Sol workload.

This produces:

- T2: 13 judgments
- T3: 11 judgments
- Total: 24 judgments

No further manual selection or ranking is performed.

## Sol Blindness

For each judgment Sol may see only:

- opaque annotation ID;
- query;
- taxonomy version;
- relevant frozen T2 or T3 annotation guide;
- required annotation response format.

Sol must not see:

- MODEL_G labels;
- frozen reference/gold labels;
- disagreement type;
- prior analysis results;
- contrast metadata.

## Interpretation

Sol results are a targeted qualitative disagreement audit.

They must not be described as:

- human IAA;
- representative second-model concordance;
- independent validation of the full 350-item sample;
- population-level evidence.
