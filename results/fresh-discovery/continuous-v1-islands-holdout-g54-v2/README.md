# Independent island holdout

Candidate **r0-islands-g12-0** converged at **−0.24454 µV**, compared with **−0.24627 µV** in coarse screening. Both energy and phase checks passed at 2,049 energy points and 64 phases. This candidate did not hide a large response under coarse resolution.

| Energy points | DC voltage |
|---|---:|
| 257 | −0.24627 µV |
| 513 | −0.24141 µV |
| 1,025 | −0.24349 µV |
| 2,049 | −0.24454 µV |

Final power is 5.97982e-18 W; maximum current-balance residual is 2.49366e-20 A. The fixed-potential objective remains 10 mV peak drive into 10 kohm.

Selection was recorded before solving: take the lower half of island candidates by coarse power from generation 54, exclude rows with phase64 and previously tested `r0-islands-g0-3`, then select the lowest SHA-256 of candidate key. The selection receipt preserves the snapshot hash, exclusion and original row. Results and spectra were written outside the live campaign; search scoring and checkpoints were not changed.

This is a single deterministic diagnostic, not a representative sample, screening miss-rate estimate, physical validation or novelty evidence. The earlier directory without the `-v2` suffix contains an interrupted redundant attempt and is not a new completed experiment.

Reproduce in the single-thread Kwant environment using a fresh output path:

```powershell
python -m ballistic_lab.reporting.low_score_holdout --snapshot runs/fresh-discovery-continuous-v1/round-000054.json --family islands --exclude-key r0-islands-g0-3 --output results/fresh-discovery/continuous-v1-islands-holdout-g54-v2
```
