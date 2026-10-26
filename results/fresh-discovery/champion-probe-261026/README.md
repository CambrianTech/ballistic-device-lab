# Champion descendants: local sensitivity probe

Four deterministic Gaussian mutations test the retained champion's local neighborhood, with reflection at parameter bounds. Two use standard deviation 0.02 and two use 0.08 in normalized parameter coordinates. These are not percentages of physical edge displacement.

Three completed descendants currently pass both energy and phase convergence:

| Child | Mutation sigma | Signed DC voltage (µV) |
|---|---:|---:|
| 0 | 0.02 | -24.12885 |
| 1 | 0.02 | +2.81029 |
| 2 | 0.08 | -8.19731 |

The fourth child's refinement remains pending in this publication. All three completed descendants have lower DC power than the retained champion (28.33077 µV magnitude). The polarity change in child 1 shows local shape sensitivity; it does not establish a new mechanism. Four samples cannot estimate an optimal offspring allocation or establish that this neighborhood is exhausted.

Selection, original parent, generated geometries, seed and source hashes are recorded in selection.json. Each completed child has its own result JSON. This independent fixed-potential experiment does not alter live search scores, the champion archive or the proposed 25% allocation. Physical stack calibration and charge feedback remain separate validation work.

Reproduce with single-thread BLAS in the Kwant environment, using a fresh output directory:

```powershell
python -m ballistic_lab.reporting.champion_probe --snapshot runs/fresh-discovery-continuous-v1/round-000955.json --output results/fresh-discovery/champion-probe-261026
```
