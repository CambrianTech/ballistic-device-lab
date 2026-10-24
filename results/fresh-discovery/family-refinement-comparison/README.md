# Broader qualification, unchanged best score

Across five completed generations, the two policies evaluated **the same 120 candidate records**. Each qualified ten candidates. Rotating a family slot increased qualified coverage from **four to all five families**, without changing the best converged voltage magnitude (12.337 µV).

| Family | Score-only qualified | Rotating-family qualified |
| --- | ---: | ---: |
| Triangle | 2 | 2 |
| Beveled | 3 | 2 |
| Profile | 4 | 3 |
| Islands | 0 | 1 |
| Radial | 1 | 2 |

This is evidence that allocation broadens accurate evaluation, not that it improves performance. The retained champion remains unbeaten. Both runs use seed 241027, mixed proposal scheduling, unchanged fixed-potential scoring and identical convergence gates. Two candidate-refinement slots per generation do not imply equal CPU time. This is one seed and a five-generation horizon, not a general superiority claim.

[Raw matched snapshots, hashes and winning records](result.json) preserve the comparison. The family worker completed normally at 20:29 UTC on October 24. Historical campaigns and the original STOP are intact.

Reproduce:

```sh
python -m ballistic_lab.reporting.compare_refinement runs/fresh-discovery-mixed-v2/round-000004.json runs/fresh-discovery-family-v1/round-000004.json new-comparison.json
```

Numerical qualification is not physical validation or literature novelty.
