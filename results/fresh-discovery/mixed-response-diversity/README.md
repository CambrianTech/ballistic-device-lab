# Different structures, different electrical responses

The first 16 completed generations contain 340 candidates, with 68 per shape family. At the common 257-energy-point screening resolution, every family produces both voltage polarities:

| Family | Minimum DC (µV) | Maximum DC (µV) | Median magnitude (µV) |
| --- | ---: | ---: | ---: |
| Beveled | -19.712 | 8.854 | 2.752 |
| Islands | -8.492 | 6.583 | 1.712 |
| Profile | -13.709 | 9.090 | 2.338 |
| Radial | -6.277 | 8.069 | 2.055 |
| Triangle | -10.457 | 9.401 | 2.813 |

These are coarse screening distributions, not converged rankings. Adaptive proposals share ancestry and are not independent random samples; the table does not establish that one search strategy is superior.

## Strongest qualified candidate

32 candidates pass both energy and phase convergence checks. The strongest, `r0-beveled-g5-0`, gives **19.699 µV magnitude** and **0.03880 pW** delivered load power. The matched control gives 11.205 µV and 0.01256 pW: about **3.09× control power**. The preserved champion still leads at 28.331 µV and 0.08026 pW.

[Qualified comparison](qualified-comparison.json) retains complete candidate and numerical records. [Response audit](audit.json) retains all screening values and the source snapshot hash. These are fixed-potential simulations, not calibrated physical validation or evidence of literature novelty.

Reproduce the distribution from an immutable completed snapshot:

```sh
python -m ballistic_lab.reporting.response_diversity_audit runs/fresh-discovery-mixed-v2/round-000015.json new-audit.json
```

This read-only audit performs no new transport solves and does not change search scoring or champion selection.
