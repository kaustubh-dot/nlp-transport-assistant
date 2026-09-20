# Gate B.2 Bootstrap Methodology & Interpretation Note

**Document:** `reports/nlp_v2/gate_b3/gate_b2_bootstrap_interpretation_note.md`  
**Applies to:** `reports/nlp_v2/gate_b2/gate_b2_confirmation_results_v2.md` and `gate_b2_confirmation_results_v2.json`  
**Status:** Prospective Methodological Clarification  
**Date:** 2026-09-20  

---

## 1. Context and Objective

In Gate B.2 model-side confirmation, an evaluation bootstrap was executed across 1,000 resamples to evaluate the statistical significance of the performance delta between the direct-dispatch T3 taxonomy and the hierarchical T2-H architecture.

The Gate B.2 report referred to this procedure as a:
$$\text{"hierarchical query } \times \text{ seed bootstrap"}$$

This note provides a formal methodological clarification regarding the precise sampling mechanics and valid statistical interpretation of that bootstrap.

---

## 2. Sampling Mechanics Clarification

In the Gate B.2 implementation (`scripts/nlp_v2/gate_b2/evaluate_gate_b2.py`), the bootstrap procedure operates by:
1. Resampling query indices with replacement from the 706 stress-evaluation items ($N = 706$ queries);
2. Retaining predictions from all three evaluated training seeds ($\{42, 101, 777\}$) for each resampled query index;
3. Calculating the mean macro operational accuracy for T2-H and T3 across those three seeds on each resampled query slice.

Because new model training runs with freshly sampled random seeds are **not** retrained inside each bootstrap iteration, the sampling variation captured is exclusively over the **query population**, conditional on the three fixed, evaluated training checkpoints.

### Correct Prospective Designation
Going forward, this procedure should be formally described as:
$$\textbf{query bootstrap over fixed evaluated seeds}$$
or
$$\textbf{query-resampling bootstrap conditional on the three evaluated training seeds}$$

---

## 3. Valid Statistical Interpretation

- **What the Confidence Interval Reflects:**  
  The 95% bootstrap confidence interval ($[+0.0245, +0.0581]$) captures **query-sample uncertainty** conditional on the three evaluated model checkpoints trained under seeds 42, 101, and 777.
- **What the Confidence Interval Does NOT Reflect:**  
  The interval does **not** estimate model performance variability over hypothetical newly sampled training seeds or newly trained weights.

---

## 4. Preservation of Quantitative Findings

The underlying calculations and empirical results remain completely valid under this clarified interpretation:
- **T2-H strict exact operation accuracy:** $0.7531 \pm 0.0024$
- **T3 strict exact operation accuracy:** $0.7941 \pm 0.0291$
- **Strict mean difference ($T3 - T2\text{-}H$):** $+0.0412$ ($+4.11\text{ pp}$)
- **95% Bootstrap Confidence Interval:** $[+0.0245, +0.0581]$
- **Empirical bootstrap $p$-value:** $p < 0.002$ ($0 / 1000$ iterations had $T3 \le T2\text{-}H$)
- **Corrected ambiguity-aware accuracy:**
  - T2-H: $0.7668 \pm 0.0084$
  - T3: $0.8069 \pm 0.0306$
  - Difference: $+4.01\text{ pp}$

No recomputation or modification of the Gate B.2 model prediction files or numerical outputs is warranted. This clarification amends the methodological interpretation while maintaining full historical integrity.
