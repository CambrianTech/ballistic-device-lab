# Bound occupation can affect current through feedback

In this synthetic scalar Hartree model, moving the bound-occupation reference across the pole changes the self-consistent onsite energy by **53.60 meV** and terminal current by **-0.3468 µA**. The zero-coupling control has exactly zero potential and current spread.

The closure is `U = 0.7 eV + g (n(U, reference) - n0)`, with g = 0 or 0.2 eV per electron. The neutral reference n0 is the charge at U = 0.7 eV with the reference exactly at its bound pole. Temperature is 150 K; reservoirs stay at +0.2 and -0.1 eV. The two reference choices are 20 meV below and above the original pole. The pole itself moves with U during feedback.

Charge and current use the previously checked analytic impurity-chain expressions, including the discrete bound-state occupation. A bracketed root solve enforces the closure; residuals must be below 1e-9 eV. Each case is repeated with quadrature tolerances 1e-8 and 1e-10.

This deliberately uncalibrated capacitance model demonstrates why fixed-potential insensitivity does not settle occupation-model uncertainty once charge feeds back. It is not a graphene Poisson calculation, device-performance prediction, or novelty claim. No search scoring changed. Root finding establishes a stationary solution, not dynamical stability or a global uniqueness proof.

[Raw cases and source fingerprint](result.json). Reproduce with `python -m physics_layers.scalar_bound_feedback`; the output result must not already exist.
