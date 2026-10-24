# Completed fresh campaign: 20 generations

420 designs were screened: 230 fresh samples and 190 mutations. Nine candidates
passed energy and phase convergence. The strongest was `r0-triangle-g8-1`, a
mutation of `r0-triangle-g5-0`, at 12.694 µV DC. It exceeded synthetic D00 by
28.3% in DC load power but did not beat the retained 28.331 µV champion.
These counts are unequal and refinement is selective; this is not evidence that
mutation is generally better than fresh sampling.

## Refinement allocation finding

The completed implementation selected the top two screening records globally,
then skipped either record if it was already converged. Consequently, converged
leaders could occupy both slots and prevent other candidates from being refined.
The completed run's nine qualified candidates do not imply the other 411 failed
convergence; most were not tested at that level.

The corrected pipeline selects the strongest two **unqualified** records first.
A regression test uses two converged leaders above three pending candidates and
checks that the next two pending candidates receive the slots. This applies to
future campaigns only. The finished source manifest and snapshots are preserved;
resuming that directory with changed source is intentionally refused.

All twenty snapshot champion checks passed. Numerical results remain fixed-
potential simulations, not physical validation or novelty. The README publisher
continues to display this completed campaign automatically; no new worker was
started during this audit.
