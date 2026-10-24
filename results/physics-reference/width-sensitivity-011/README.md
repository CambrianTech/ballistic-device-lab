# Current sensitivity to charge-cloud width

Widening the Gaussian charge cloud by 10%, from **0.10 to 0.11 nm**, changes the current by **−0.003682% (−56.92 pA)** in this 15-site graphene fixture. The largest site-potential change is **0.42782 mV**.

| Width | Lead-0 current | Potential residual | Occupation residual |
|---|---:|---:|---:|
| 0.10 nm | 1.546031374 µA | 5.89e-13 V | 1.47e-13 |
| 0.11 nm | 1.545974453 µA | 5.33e-13 V | 1.33e-13 |

Both cases use the same 0.10 nm mesh spacing, atoms, gate box, 30 mV boundary potential, dielectric 4, 300 K, lead chemical potentials 2.505/2.495 eV, bound-state reference 2.5 eV and neutral zero-onsite background. Full-grid Poisson and recomputed occupation checks passed. Recorded physics_layers source hashes match exactly across the pair.

The historical baseline had different solver source hashes, so a new baseline was computed in `../width-sensitivity-010-replay/`; the historical result was preserved. The comparison script checks coordinates, cutoff, mesh and baseline source hashes before reporting differences. The source manifest does not cover external dependencies or ballistic_lab transport code.

Reproduce in the single-thread Kwant environment (use fresh output directories when rerunning):

```powershell
python -m physics_layers.finite_width_feedback --sigma-nm 0.10 --factors 2 --output results/physics-reference/width-sensitivity-010-replay
python -m physics_layers.finite_width_feedback --sigma-nm 0.11 --factors 2 --output results/physics-reference/width-sensitivity-011
python -m ballistic_lab.reporting.compare_width
```

This is a single-grid sensitivity result for an uncalibrated numerical fixture. Small current sensitivity at these two widths does not establish width calibration, mesh convergence, rectification, or physical validation. Refinement of the 0.11 nm case remains unresolved.
