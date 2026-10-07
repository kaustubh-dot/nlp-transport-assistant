# Phase 17 training decision evidence

Measure the actual frozen raw-query classifier, rather than infer classifier
quality from final reply intent (which includes multiple-goal guards). On the
unchanged development v1 suite, capture one prediction per query, replay it
through the complete assistant, and compare against an intended-intent
counterfactual through the same extraction/resolver/domain path. Exclude the two
null-intent semantic/multiple-goal contracts from single-label model accuracy;
report their assistant guard contracts separately.

Partition terminal failures into those corrected by the intended intent with an
incorrect raw class, ambiguity/guard cases corrected by structured gold ambiguity,
and residual downstream failures. Report overlapping downstream slot, entity,
policy and domain-code flags separately; successful expected unsupported and
external-source refusals are limitations, not failures. A counterfactual estimates
reachability under correct intent, not the likely effect of new training.

Re-evaluate only allowed train-disjoint validation (family, semantic-family and
exact-query exclusions), retaining all 16 labels. Emit aggregate validation
metrics/confusion and development case IDs, never held-out queries/labels or
validation query examples. Validate train/validation/suite/DB/model hashes and
dedicated empty report destinations. No fitting, model mutation or promotion.

The replacement proposal, if justified, must change the selection procedure to
train-disjoint validation relative to the original overlapping-validation model.
Keep the existing raw preprocessing, fixed labels, pinned MuRIL revision and
reproducible optimizer/configuration. A candidate can fail to improve and must
remain unpromoted until validation-only comparison and complete contracts pass.
Stop after a reviewed decision/proposal if full training is justified and no GPU
is available, as explicitly requested. Never substitute full CPU training.
