# Finite-width graphene feedback: two-grid comparison

The 15-site graphene fixture uses a fixed Gaussian sigma of 0.10 nm, a five-sigma
per-axis cutoff, and adjoint charge deposition/potential averaging. The atom
positions and physical gate box are identical across 0.10 and 0.05 nm grids.
Other assumptions: dielectric constant 4, uniform 30 mV gate boundary, 300 K,
Fermi level 2.5 eV, reservoir chemical potentials 2.505/2.495 eV, bound-occupation
reference 2.5 eV, and zero-onsite equilibrium occupations as compensating background.

Halving grid spacing changes the maximum site potential by **0.08435 mV** and
current by **-0.000670%**. Both solutions pass independent full-grid Poisson and
recomputed charge residual checks. Exact currents and residuals are in the receipt.

The earlier point-charge comparison changed site potentials by 3.5879 mV, but
used 0.20/0.10 nm grids and a different charge model. These are not matched
comparisons establishing a reduction factor. The present pair shows small remaining
sensitivity for this chosen finite-width model; two grids do not prove an
asymptotic limit. Width calibration, contact electrostatics, and further refinement
remain unresolved. The high Fermi level is a numerical fixture choice, not a
calibrated physical device. No self-interaction subtraction is applied.

Reproduce in the isolated Kwant runtime with single-thread BLAS:
`python -m physics_layers.finite_width_feedback`.
[Results and source hashes](result.json). Historical campaign scoring is unchanged.
