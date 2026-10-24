# Does refinement reorder screened candidates?

At generation 32, **66 of 680 candidates** have passed energy and phase convergence checks. Within that selected subset, **22 of 2145 pairs reverse order** between the shared 257-point screening power and refined 64-phase power (0 tied pairs). The largest ordinal rank shift is **6 places**. Ties use candidate keys for deterministic ordering.

Screening leader: `r1-triangle-g4-1`. Refined leader: `r1-triangle-g4-1`.

This diagnoses numerical rank stability among candidates already selected for refinement. It does not measure the false-negative rate of early screening: unrefined candidates remain unresolved. It therefore cannot justify tightening screening or establish that the search is finding all promising designs. No live scoring or selection was changed.

Reproduce: `python -m ballistic_lab.reporting.rank_stability runs/fresh-discovery-continuous-v1/round-000032.json <new-output-directory>`. The JSON includes every paired score, reversed pair, and the immutable input SHA-256. These are fixed-potential simulation results, not physical validation or novelty evidence.
