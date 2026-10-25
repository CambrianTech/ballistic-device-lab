# Independent radial holdout

Candidate **r1-radial-g39-1** refined from **1.7506 to 1.7410 µV**, passing energy and phase convergence checks at 1,025 energy points and 64 phases. This low-scoring radial example did not reveal a hidden strong response under finer numerical resolution.

| Energy points | DC voltage |
|---|---:|
| 257 | 1.7506 µV |
| 513 | 1.7434 µV |
| 1,025 | 1.7410 µV |

Final DC power is 3.03114e-16 W and maximum current-balance residual is 1.956e-20 A. The fixed-potential objective remains 10 mV peak drive into 10 kohm.

Selection was fixed before refinement: filter generation-54 snapshot to radial candidates, take the lower half by coarse power, exclude candidates already carrying phase64, then choose the lowest SHA-256 of candidate key. The saved selection receipt records the input snapshot hash, pool size and original result. The experiment used its own spectra directory and did not update live checkpoints or scores.

This is one deterministic diagnostic, not a random population sample or an estimate of the screening false-negative rate. It does not establish physical validation or novelty. Historical controls and champions remain unchanged.

Reproduce with a fresh output directory in the single-thread Kwant environment:

```powershell
python -m ballistic_lab.reporting.low_score_holdout --snapshot runs/fresh-discovery-continuous-v1/round-000054.json --family radial --output results/fresh-discovery/continuous-v1-radial-holdout-g54
```
