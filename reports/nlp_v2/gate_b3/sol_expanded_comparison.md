# Gate B.3 Expanded Sol Audit Comparison

128 purposively selected frozen challenge queries; 256 Sol judgments.

Descriptive results only. No population confidence intervals or significance tests.

## Overall

| Source | T2 primary exact | T3 primary exact | T3−T2 | T2 primary in reference set | T3 primary in reference set |
|---|---:|---:|---:|---:|---:|
| GPT-5.6 Sol | 92.2% | 91.4% | -0.8 pp | 93.8% | 93.0% |
| MODEL_G | 89.8% | 90.6% | +0.8 pp | 89.8% | 90.6% |

## Sol–MODEL_G Agreement

| Taxonomy | Primary agreement | Acceptable-set agreement | Clarification agreement |
|---|---:|---:|---:|
| T2 | 90.6% | 75.8% | 82.8% |
| T3 | 93.0% | 82.8% | 85.9% |

## By Language Class

| Language | N | Sol T2 | Sol T3 | Sol Δ | MODEL_G T2 | MODEL_G T3 | MODEL_G Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| EN | 30 | 83.3% | 80.0% | -3.3 pp | 80.0% | 83.3% | +3.3 pp |
| HINGLISH_LATN | 29 | 93.1% | 93.1% | +0.0 pp | 89.7% | 89.7% | +0.0 pp |
| HI_DEVA | 30 | 93.3% | 93.3% | +0.0 pp | 93.3% | 93.3% | +0.0 pp |
| HI_LATN | 29 | 96.6% | 96.6% | +0.0 pp | 93.1% | 93.1% | +0.0 pp |
| MIXED_SCRIPT_CS | 10 | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp |
