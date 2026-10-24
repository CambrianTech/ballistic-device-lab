# Gaussian pair averaging reference

Two spherical Gaussian distributions separated by 0.246 nm in dielectric 4 have
charge-averaged potential q erf(d/(2 sigma))/(4 pi epsilon d). This independent
closed form tests the mapping against an analytic source potential, without a
Poisson solve. Both widths are chosen numerical assumptions, not carbon orbital fits.
The mapping uses its default five-sigma per-axis cutoff and normalized weights.

| Width sigma (nm) | Grid (nm) | Averaged potential (V per +e source) | Relative error |
| --- | --- | --- | --- |
| 0.10 | 0.100 | 1.34345969 | 3.58e-06 |
| 0.10 | 0.050 | 1.34345564 | 5.68e-07 |
| 0.10 | 0.025 | 1.34345569 | 6.03e-07 |
| 0.15 | 0.100 | 1.10311171 | 1.07e-06 |
| 0.15 | 0.050 | 1.10311127 | 6.75e-07 |
| 0.15 | 0.025 | 1.10311140 | 7.89e-07 |

The finest-grid error must be below 3e-6 for both widths. The residual at fine
spacing includes finite cutoff/normalization and quadrature effects; monotonic
convergence is not assumed. Width dependence remains a model uncertainty.
This checks site averaging, not the Poisson solver, finite-bias transport or
physical validity. No historical campaign or transport source is changed.

Reproduce: `python -m physics_layers.gaussian_pair_demo`.
[Machine-readable receipt](result.json).
