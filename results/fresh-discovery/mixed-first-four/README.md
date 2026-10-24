# Mixed campaign: proposal and refinement coverage

The first four completed generations contain 100 candidates and eight that pass
both convergence gates, versus five at the same candidate count in the earlier
campaign. The allocation fix is reaching pending candidates; the campaigns use
different seeds and strategies, so this is not an isolated performance comparison.

The strongest converged candidate is `r1-beveled-g0-1`, at 12.337 µV DC. It beats
the 11.205 µV synthetic control but remains below the retained 28.331 µV champion.
The fixed-potential model and operating conditions are unchanged.

`diversity.json` counts exact polygon encodings and recorded proposal origins.
Distinct encodings do not establish distinct atomic devices, distinct transport
behavior, or scientific novelty. Initial global sampling is tagged with its plan's
strategy, but it does not use a parent; the origin counts expose that distinction.
Sequential strategies share history, so their counts do not establish superiority.

Reproduce on a completed snapshot with a new output path:

```sh
python -m ballistic_lab.reporting.proposal_diversity_audit runs/fresh-discovery-mixed-v2/round-000003.json diversity-new.json
```

The running campaign and its sources were not modified during this audit.
