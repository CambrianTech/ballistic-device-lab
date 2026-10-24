# Family-refinement comparison (running; outcomes pending)

A bounded campaign started with seed 241027, mixed proposals, four workers, single-thread BLAS, five generations, and `--refinement-policy family`. Its 40 generation-zero proposals were checked for exact JSON equality against the prior mixed campaign: all match.

Compare completed generations 0–4 against `runs/fresh-discovery-mixed-v2`. The new run is `runs/fresh-discovery-family-v1`. Both allocate two candidate-refinement slots per generation, with the same physical objective and convergence gates. This is a candidate-count comparison, not equal CPU time. Subsequent adaptive histories may diverge; compare full-policy outcomes rather than assuming later populations match.

The intervention keeps one top-score slot and rotates the other across shape families. Questions: does it increase qualified family coverage, and does any newly qualified design improve the matched control or retained champion? Outcomes are pending. No improvement is claimed from launch or initial-population equality.

The original `runs/dc-continuous/STOP` and all completed campaign checkpoints remain intact. No live transport sources were edited. The experiment exits after five generations; it does not restart the original search.

Completed outcome: both policies evaluated the same 120 candidate records and qualified ten candidates; rotating refinement covered five families versus four, with unchanged best score. See [completed comparison](../results/fresh-discovery/family-refinement-comparison/README.md). The pending statements above record the original experiment plan.
