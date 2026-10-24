# Finite-bias charge experiment

The fixed-potential geometry search is intentionally stopped at checkpoint round
433. Its STOP file and historical records are retained. New work tests charge
feedback before starting another search campaign.

`python -m physics_layers.finite_bias_demo` runs a bounded five-case pilot:
zero and +/-10 mV reservoir bias, plus two bound-occupation reference choices
at +10 mV, on the existing 15-site graphene/3D Poisson verification fixture.
The 30 mV gate box has relative permittivity 4 and 0.2 nm grid spacing.
The reference charge is the zero-gate equilibrium occupation at the same 2.5 eV
Fermi energy, representing a compensating background. This is deliberately a
conducting verification point, not realistic calibrated doping: the miniature
leads have no propagating modes at 0, 0.7 or 0.9 eV, and two at 2.5 eV.

The provider computes n = n_equilibrium(mu_ref) + spin * integral sum_a
[(f_a-f_ref) injectivity_a] dE. Equilibrium charge includes bound states;
continuum corrections use flux-normalized Kwant scattering states. Lead band
thresholds partition the real-energy integral; Fermi tails are truncated at at
least 40 kT. The reported integration error combines numerical estimates, not
a rigorous total error bound. Narrow resonances still require convergence study.

For a bound state, the reference chemical potential specifies its occupation.
This is an explicit model assumption, not a solution to nonequilibrium trapped
charge dynamics. Comparing reference choices diagnoses sensitivity; independence
alone is not proof that all bound states are absent. This equilibrium-plus-bias
split follows the standard NEGF construction described in the
[TranSIESTA tutorial](https://siesta-project.org/siesta/events/SIESTA_School-2024/TranSIESTA-2024.pdf).

Checks: independent full-band charge/current integration on a chain, gauge
covariance, bound-state reference occupation, current conservation, and the
existing equilibrium and full-grid Poisson residual checks. No artificial
lifetime broadening is introduced. The unscreened comparison uses the same gate
potential, bias and reference occupation as the feedback calculation.

Remaining: calibrated contact electrostatics and lead shifts, mesh/self-energy
convergence, larger four-terminal devices, phonons and dynamic charge/trap
occupation. Memory and spiking will require explicit state evolution and circuit
energy accounting; static feedback does not establish either behavior.
## Route toward a neuromorphic experiment

A proposed next experiment is a gate-coupled charge-storage node connected to a
ballistic channel. This is a hypothesis to test, not an implemented memory device.
First compute and verify the channel's I(V, gate) and charge response. Then give
the storage node an explicit capacitance and a specified charging/leakage pathway,
solve its time evolution with the circuit, and measure retention, pulse response
and energy supplied by every source. Do not manufacture hysteresis by choosing
a different static solution on each sweep, or infer memory from a static
nonlinearity. If a trap is introduced, its occupation, transition rates and
material justification must be stated and varied. If it cannot retain a state
or generate a reproducible dynamical response within plausible parameters, record
that negative result and change the proposed mechanism.

Before scaling any search: test time-step convergence, equilibrium relaxation,
charge conservation, nonnegative dissipation in passive components and the
energy cost of any reset. A circuit-created oscillation must be labeled as such;
it is not evidence of intrinsic graphene spiking. The current pilot supplies
only the static charge/transport building block.

[Completed pilot results and charts](../results/physics-reference/finite-bias-feedback/README.md).

## Mesh sensitivity finding

[The same-box 0.1 nm comparison](../results/physics-reference/finite-bias-mesh/README.md)
changes current by only 0.00660%, but local potentials by up to 3.5879 mV.
Local electrostatics remains mesh-sensitive; address finite charge extent or
self-interaction before a quantitative dynamic charge-storage prediction.

[Response-matrix diagnosis](../results/physics-reference/electrostatic-kernel/README.md)
finds on-site responses increase by 2.083–6.481 V/e on refinement.
No diagonal subtraction is applied; finite charge extent needs independent justification.

[Fixed Gaussian charge verification](../results/physics-reference/finite-charge/README.md)
shows approximately second-order convergence: 2.59%, 0.624%, 0.155% mean-potential
error at 0.2, 0.1, 0.05 nm grids. The 0.2 nm Gaussian width is a test choice,
not carbon-orbital calibration. No graphene feedback model has been replaced.

## Finite-width site coupling

`physics_layers.gaussian_site_mesh.GaussianSiteMeshMap` is an opt-in alternative
mapping with a fixed physical Gaussian standard deviation. It samples the density
at grid nodes, truncates at an explicit per-axis cutoff (default five sigma), and
normalizes each site's weights to unity. Deposition uses the transpose of the same
weights used to average potential, preserving the discrete charge/work pairing.
It rejects cutoff boxes outside the mesh, spacing larger than sigma, and nonzero
charge support on electrodes, including opposite charges that would cancel.

Verification: `python -m unittest tests.test_gaussian_site_mesh tests.test_site_mesh`
passes seven tests, including anisotropic spacing, displaced sites, signed charge
conservation, potential-offset covariance, adjoint work, reciprocal Poisson response,
positive energy and invalid-boundary rejection. These are numerical fixtures.
The mapping is not wired into the graphene pilot or historical search. Its cutoff
normalization changes the infinite Gaussian slightly; no carbon-orbital calibration,
self-interaction correction, or coupled graphene convergence is claimed. Next test:
fixed-width graphene feedback across meshes and widths, with assumptions reported.

The [Gaussian-pair reference](../results/physics-reference/gaussian-pair/README.md)
checks site averaging against an independent analytic interaction at 0.246 nm
separation. Finest-grid relative errors are below 8e-7 for both chosen widths.
Changing sigma from 0.10 to 0.15 nm changes the analytic interaction from 1.34345
to 1.10311 V per elementary source charge (about 17.9%). This model sensitivity
is much larger than mapping error, reinforcing the need for physical width
calibration. This reference uses analytic source fields, not a Poisson solve.

[Finite-width coupled feedback](../results/physics-reference/finite-width-feedback/README.md)
now compares fixed sigma 0.10 nm at 0.10/0.05 nm grid spacing: maximum site-potential
change 0.08435 mV and current change -0.000670%. Both residual checks pass.
This is a two-grid numerical fixture, with orbital width and contacts uncalibrated.

## Bound-state gauge regression

`tests.test_bias_charge.BiasChargeTests.test_bound_state_gauge_and_unshifted_reference_control`
adds an isolated 0.04 eV orbital alongside a conducting chain at 300 K and
reservoir chemical potentials +0.05/-0.05 eV. Shifting device onsite energies,
lead Hamiltonians, both reservoirs and the bound-occupation reference by +0.37 eV
preserves occupations (absolute tolerance 2e-6 electrons) and currents (1e-11 A).
A negative control deliberately leaves the reference at 0.02 eV: isolated charge
then changes by more than 0.5 electrons, agreeing with the analytic Fermi occupation,
while current stays unchanged. Thus current agreement alone cannot validate the
bound-state charge closure. This verifies the declared closure, not its physical
correctness or a relaxation mechanism for isolated states.

All five finite-bias tests passed in the isolated Kwant runtime (40.576 s):
`python -m unittest tests.test_bias_charge`. No transport implementation changed.

## Spin normalization and numerical controls

The finite-bias regression suite now checks spin degeneracy at fixed Hamiltonian
and a nonzero scattering-site shift: spin=2 doubles both occupation and nonzero
current relative to spin=1. This catches inconsistent spin factors between the
equilibrium baseline and bias correction; it is not a spin-polarized material model.
It also checks rejection of zero, negative, NaN and infinite temperature/tolerance.
All seven tests in `python -m unittest tests.test_bias_charge` passed in 47.197 s
in the isolated Kwant runtime. Existing physical assumptions remain unchanged.

## Circuit integration boundary

`FeedbackCurrentModel` now exposes a converged four-terminal feedback callback
through the existing loaded-DC current interface. Lead permutation is explicit;
the callback owns chemical potentials, contact/gate boundaries and occupation
policy and must raise on nonconvergence. No stale solution is substituted.
Two tests pass: an analytic asymmetric passive resistor network through the real
loaded-circuit solver (including permuted provider leads), and failure/invalid
input propagation. Circuit output is bottom minus top. This is an integration
fixture, not an integrated graphene device calculation. Next: implement the
four-terminal graphene callback with explicit electrode electrostatics and benchmark
its cost before a fresh campaign.

## Explicit electrode boundaries

`ElectrodeBoundary` supplies a declared-order partition of contact/gate mesh nodes.
It rejects overlapping electrodes (including ambiguous shared edges/corners),
missing outer-face assignments, empty electrodes and invalid voltages. The device
callback must choose the masks and relate electrostatic voltage to lead band shifts
and reservoir chemical potentials; no contact work function is inferred.
Four boundary/circuit tests pass, including Poisson gauge shifts, linear
superposition, the maximum principle and the prior analytic load fixture:
`python -m unittest tests.test_electrode_boundary tests.test_feedback_current`.
This establishes boundary plumbing, not calibrated graphene contact physics.

[Four-terminal preflight](../results/physics-reference/four-terminal-preflight/README.md)
now supplies a 51-site fixture, explicit remote-box electrode partition and finite
charge support checks. All four leads conduct at 0.9 eV (one mode per spin each).
The next callback must reconcile reservoir/lead shifts and contact electrostatics;
this preflight has no self-consistent or loaded-DC result yet.
