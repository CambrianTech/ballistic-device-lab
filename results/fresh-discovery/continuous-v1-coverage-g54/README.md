# Which shape families receive refinement?

Generation 54 has **224 screened candidates in each of five families**, but convergence-qualified coverage differs by almost threefold:

| Family | Screened | Converged | Coverage |
|---|---:|---:|---:|
| Beveled | 224 | 25 | 11.2% |
| Islands | 224 | 14 | 6.3% |
| Profile | 224 | 34 | 15.2% |
| Radial | 224 | 12 | 5.4% |
| Triangle | 224 | 25 | 11.2% |

Every family receives follow-up, so none is completely excluded. However, equal proposal counts do not mean equal refinement coverage or equal CPU budgets. Profile candidates account for 34 of 110 converged results; radial candidates account for 12. The rotating family slot provides a floor while the score-selected slot remains selective.

This is a coverage diagnosis, not evidence that radial or island designs are intrinsically inferior. Most candidates in every family remain screened-only. Independent holdouts from under-covered families would help assess missed winners; the counts alone cannot establish that rate. Selection, live worker sources and scoring were left unchanged.

The result JSON includes all candidate identifiers, shared 257-point responses, qualification flags and immutable snapshot SHA-256. Coarse response extrema are not converged performance claims. All measurements use the existing fixed-potential simulation; none establishes physical validation or literature novelty.

Reproduce with a fresh output filename:

```powershell
python -m ballistic_lab.reporting.response_diversity_audit runs/fresh-discovery-continuous-v1/round-000054.json results/fresh-discovery/continuous-v1-coverage-g54/result.json
```
