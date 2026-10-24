# Feedback roots survive independent iteration

For each of the two bound-reference choices, direct fixed-point iteration from onsite energies **0.3, 0.7 and 1.1 eV** converged to the previously bracketed root. All six runs finished in 55–67 iterations, with root disagreement below **4.1e-11 eV** and residual below **7.0e-11 eV**.

The local iteration-map slopes are approximately **-0.689 and -0.728**. Finite differences at steps 1e-4, 1e-5 and 1e-6 eV agree. Magnitudes below one support local numerical convergence; negative signs explain alternating corrections.

This is a numerical convergence check of the [synthetic scalar feedback model](../scalar-bound-feedback/README.md). It does not prove global uniqueness, physical dynamical stability, or calibrated graphene behavior. The starting-point check and slope check use the same charge integrator, while comparing two different root-finding procedures.

[Raw iterations and slopes](result.json) bind the input result by SHA-256. Reproduce with `python -m physics_layers.scalar_feedback_convergence`; output must not already exist. No worker or transport code changed.
