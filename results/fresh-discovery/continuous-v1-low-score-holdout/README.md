# Low-score holdout: no hidden strong result in this case

An independent refinement of **r0-islands-g0-3**, selected from the lower half
of generation 21's accumulated coarse-power scores, converges to **0.659161 µV**
DC magnitude at 2,049 energy points and 64 phase samples. Both convergence gates
pass. Its coarse estimate was about 0.66569 µV: this candidate remains weak,
rather than revealing a strong design hidden by screening error.

Selection was fixed before refinement: take the smallest SHA-256 of candidate
key among lower-half rows lacking phase64. `selection.json` records the input
snapshot hash, population, eligible pool, exact rule and original record.
`result.json` records the refined result. This side experiment uses its own
spectra directory and never writes into the campaign or changes search scoring.

One deterministic case does not estimate the population false-negative rate or
rule out missed candidates elsewhere. It is a numerical diagnostic under the
fixed-potential model, not physical validation or a novelty claim.

Reproduce from the same snapshot in a checkout without this output directory:
`python -m ballistic_lab.reporting.low_score_holdout`. The runner refuses to
replace an existing selection receipt. The main four-worker campaign continued
independently and had passed its former 20-generation limit.
