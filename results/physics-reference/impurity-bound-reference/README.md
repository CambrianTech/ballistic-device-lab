# Bound-state-complete chain reference

All eight comparisons passed: maximum charge error **3.61e-10 electrons**, maximum current error **1.36e-20 A**. The continuum-plus-pole spectral sum rule also passed within 1e-9.

For a single onsite impurity U in an infinite chain with hopping magnitude 1 eV, the local resolvent is `1 / (sqrt(z²-4)-U)` with the retarded branch. Its continuum density is `sqrt(4-E²) / [pi (4-E²+U²)]`; the bound pole is at `sign(U) sqrt(4+U²)` with local weight `abs(U)/sqrt(4+U²)`.

The independent reference integrates the continuum against the mean reservoir Fermi occupation, then adds the pole with the explicit reference occupation (spin degeneracy two). Current is independently integrated using `T(E)=(4-E²)/(4-E²+U²)`.

Cases: onsite shifts ±0.7 eV, temperatures 150 and 600 K, reference chemical potentials -0.1 and +0.2 eV, reservoir chemical potentials +0.2 and -0.1 eV. Assertions require charge error below 2e-6 electrons and current error below 1e-11 A.

This resolves the [earlier continuum-only reference rejection](../off-resonant-reference/README.md) for this fixture. That historical rejection remains intact. The calculation verifies numerical accounting under a chosen bound-state occupation; it does not establish physical validity, graphene performance, or Poisson feedback convergence.

[Raw results](result.json). Reproduce with `python -m physics_layers.impurity_bound_reference` in the Kwant environment. The fixed output file must not already exist.
