# Manual assessment rubric

The 200 authored cases were fixed before baseline predictions. Assess every result against its original query and independently authored intent/operation/explicit slot subset. Expected factual names, amounts, membership answers, facility flags and departure values were deliberately not guessed.

- `goal_correct`: The actual family and operation match, the explicit requested scope is retained, and a grounded answer satisfies the single goal. For `out_of_scope`, a correct domain rejection fulfills the supported rejection contract.
- `safe_limitation`: The actual family and goal are understood but an explicit unsupported-source, external-source or supported-scope limitation prevents goal fulfillment. Correct live refusals belong here, not `goal_correct`.
- `legitimate_clarification`: The actual goal is understood and the response asks for genuinely missing, ambiguous or conflicting inputs without silently discarding supplied scope. Multiple distinct goals must be retained in clarification/candidates.
- `recognition_failure`: Wrong family/operation, missed supplied input, wrong location role, negation failure, irrelevant clarification, or a refusal/answer that covers only one of multiple explicit goals. A safe message under the wrong family remains a recognition failure.
- `unsafe_or_wrong_answer`: The response makes an unsupported/wrong factual assertion, silently answers narrower/different scope as fulfillment, invents current status, or claims an invalid/ambiguous input has an executable answer.
- `needs_review`: Available result/evidence does not determine scope preservation, source grounding or interpretation confidently. This is not counted as goal fulfillment.

Precedence: unsafe assertions over recognition failures; wrong-family refusals/clarifications are recognition failures; a correct family does not alone prove correctness. Manual evidence and rationale are recorded per ID. Aggregates are descriptive custom product QA, not frozen-benchmark accuracy or a representative language performance estimate.
