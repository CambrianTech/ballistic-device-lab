# Electrical response diversity through generation 15

The 340 screened candidates (68 per family) produce both output polarities in
all five families at the common 257-energy-point resolution. Median absolute
screening voltages range from **1.40 µV (islands)** to **3.16 µV (profile)**.
Different atomic shapes are producing varied values of the target observable;
this does not establish independent response mechanisms or physical novelty.

Of these candidates, 32 passed both convergence checks. Refined power differs
from the coarse estimate by **−5.46% to +8.63%**. The endpoints are
`r0-beveled-g9-1` and `r1-profile-g13-1`, respectively. This is a selected subset,
so it cannot estimate false negatives among unrefined candidates or prove coarse
screening harmless. Unrefined records remain unresolved.

The converged campaign best remains `r1-triangle-g4-1`, **15.034078 µV** magnitude.
The fixed-potential champion is not beaten. No scoring or live worker code changed.

`result.json` records the immutable snapshot hash, all coarse observations and
family summaries. `refinement.json` records coarse and converged powers for
all 32 qualified candidates, with percent change defined as
100 × (converged power / coarse power − 1).

```sh
python -m ballistic_lab.reporting.response_diversity_audit runs/fresh-discovery-continuous-v1/round-000015.json results/fresh-discovery/continuous-v1-response-g15/result.json
```

Use a fresh output path when reproducing. This audit concerns fixed-potential
simulation and numerical refinement, not charge-feedback validation.
