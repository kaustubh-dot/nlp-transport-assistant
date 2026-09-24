# Gate B.3 GPT-5.6 Sol Expanded Masked Audit

**Status:** FROZEN BEFORE EXPANDED REVIEW
**Date:** 2026-09-24

## Motivation

The earlier 24-judgment direct-conflict audit was useful for semantic-boundary
inspection but provided insufficient Hindi/Hinglish and broader surface-form
coverage.

This expanded audit is therefore a separate post-lock language/surface
robustness audit.

## Design

- 128 unique frozen Gate B.3 challenge queries.
- Each query independently classified under T2 and T3.
- Total GPT-5.6 Sol judgments: 256.
- Previously exposed individual queries are excluded.
- Selection does not use MODEL_G labels or frozen reference labels.

Selection is deterministic and coverage-oriented.

The selected set covers every observed available category value, where
possible, for:

- language class;
- script;
- code-switch level;
- noise level;
- noise type;
- ambiguity type;
- answerability status.

Remaining capacity maximizes semantic-family/scenario diversity while
maintaining meaningful representation of every language class.

## Sol Input

Sol sees only:

- annotation_id;
- raw query;
- taxonomy version;
- relevant frozen annotation guide;
- annotation output instructions.

Sol does not see:

- language class;
- script/noise metadata;
- MODEL_G output;
- reference/gold labels;
- disagreement metadata;
- prior concordance results.

## Interpretation

This is a stratified, purposive masked audit.

It may support descriptive analysis of language/surface robustness and
semantic-boundary behavior on the selected challenge subset.

It is not:

- a representative population estimate;
- human IAA;
- independent human validation;
- a complete second-model benchmark;
- an isolated one-query/one-context model campaign.

No population confidence intervals or significance tests will be reported.
