# Charge feedback under mesh refinement

Halving the electrostatic mesh spacing from **0.10 to 0.05 nm** at fixed **0.11 nm charge-cloud width** changes lead-0 current by **−0.0006325% (−9.778 pA)**. The largest site-potential change is **0.06977 mV**.

| Mesh spacing | Lead-0 current | Potential residual | Occupation residual |
|---|---:|---:|---:|
| 0.10 nm | 1.545974453 µA | 5.33e-13 V | 1.33e-13 |
| 0.05 nm | 1.545964675 µA | 5.35e-13 V | 1.33e-13 |

The same 15-site graphene fixture, domain, 30 mV boundary potential, dielectric 4, 300 K, lead chemical potentials 2.505/2.495 eV, bound-occupation reference and neutral background are retained. The comparison checks identical coordinates, Gaussian width/cutoff and physics_layers source manifests, and identical physical box dimensions. Both feedback solves completed their recomputed occupation and full-grid Poisson residual checks.

The observed mesh effect is smaller than the previously measured 0.10-to-0.11 nm width effect (−56.92 pA on the coarse grid). This is a two-grid sensitivity measurement, not an asymptotic error bound, calibrated charge-cloud width, physical validation or new rectifier result. Energy integration and external dependency provenance are not independently tightened by this experiment. The live evolutionary search uses its existing fixed-potential model unchanged.

Reproduce with single-thread BLAS in the Kwant environment; choose fresh output paths:

```powershell
python -m physics_layers.finite_width_feedback --sigma-nm 0.11 --factors 4 --output results/physics-reference/width-sensitivity-011-fine
python -m ballistic_lab.reporting.compare_width_mesh results/physics-reference/width-sensitivity-011/result.json results/physics-reference/width-sensitivity-011-fine/result.json results/physics-reference/width-sensitivity-011-fine/comparison.json
```

The saved comparison includes SHA-256 hashes of both input records. The source manifest covers physics_layers, not external libraries or ballistic_lab transport sources.
