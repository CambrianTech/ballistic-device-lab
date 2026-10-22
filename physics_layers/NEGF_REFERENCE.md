# Site-resolved nonequilibrium charge reference

The dense `negf_reference` backend computes reservoir-resolved occupations and
terminal currents for a small open tight-binding system. It uses constant
wide-band reservoir self-energies, explicit spin multiplicity and finite
temperature. Positive-definite total contact broadening is required; it does
not silently omit bound states. This restriction is unsuitable for a production
graphene cavity with contacts only at its boundaries.

With energies consistently in eV:

$$G^r=[EI-H-U+i\sum_a\Gamma_a/2]^{-1},\qquad
n_i=\frac{s}{2\pi}\int dE\sum_a f_a(E)[G^r\Gamma_aG^a]_{ii}.$$

Current uses the matching Landauer transmission trace and the eV-to-joule
conversion. Numerical integration extends over the full real energy axis;
the reported quadrature error combines occupation and unscaled current-integral
components, not amperes. Analytic resonant-level occupations and an independent
scalar current integral test normalization. Equilibrium, gauge shift and current
conservation tests check consistency. General quantum-transport context:
[Kwant methods paper](https://arxiv.org/abs/1309.2926).

The Hartree loop solves `U = U_external + K @ (n - n_reference)`. The caller
supplies a symmetric positive-semidefinite interaction matrix in eV/electron.
It is a capacitance surrogate, **not** a Poisson solution for the paper geometry.
The reference population is explicitly computed at equilibrium for the demo.
Unmixed residuals control acceptance; inner solve failures propagate.

Run `python -m physics_layers.negf_demo` for a two-site, nine-bias comparison.
It records fixed-potential and charge-feedback currents, local populations,
onsite shifts, iteration residuals and tighter-quadrature/iteration checks.
The demo is not graphene, a fabricated device reconstruction, a loaded AC/DC
efficiency result, or a prediction of the current search winner's performance.

Next integration requires graphene lead self-energies/local charge including
bound-state treatment, a physical electrostatic operator with conservative
site-to-mesh mapping, and convergence at every applied terminal bias. The live
search remains on its original frozen-potential source manifest.
