# Winner-neighborhood experiment

Run `python -m local_lab.worker` in the Kwant environment with single-thread
BLAS. One CPU, bounded to 24 children around the converged overall leader from
the latest completed snapshot at initialization. The frozen plan records the
parent, seed, source snapshot hash and all proposals before computation.

Eight Gaussian mutations at each 0.5%, 1% and 2% of parameter range are reflected
at parameter bounds. These are normalized parameter scales, not literal edge
displacements. Different parameters can produce identical discrete lattices.
This pilot does not deduplicate atomic realizations or claim a unique-design count.

The parent and children are freshly evaluated on 257 energy points. The parent
and four strongest screened children then receive 513/1025 points, extending to
2049/4097 if needed. The existing DC evaluator supplies identical physical and
convergence rules to the main campaign. Failed solves remain unresolved. Only
converged parent/child pairs support a comparison; selection bias and held-out
robustness remain separate concerns. This is local search, not a proof of optimality.

`runs/winner-local/` holds an exclusive OS lock, immutable source manifest and
plan, atomic result checkpoints, spectra, status and worker logs. Create `STOP`
for a graceful stop between grid evaluations; remove it and rerun to resume.
An in-flight grid may finish before stopping. Do not edit loaded `local_lab/`
or transport/search sources. Source changes reject resumption; unresolved cases
are retained rather than silently retried. A completed run exits.

This experiment never writes the continuous search checkpoint, changes parent
selection there, or contributes to its equal-candidate method comparison.
Reporting may read completed result rows independently.
