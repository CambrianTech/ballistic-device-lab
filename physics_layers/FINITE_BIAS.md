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

[Four-terminal finite-bias charge benchmark](../results/physics-reference/four-terminal-charge/README.md)
passes tolerance refinement at 0.9 eV: maximum occupation change 3.10e-9 electrons
and current change 2.12e-21 A. One evaluation takes 12-18 s on this host. This is
fixed onsite, with pinned output reservoirs; self-consistent loaded DC is pending.

Electrode partitions now retain immutable boolean snapshots: caller array edits,
re-enabling NumPy write flags, or reassignment cannot change a prepared boundary.
The regression suite exercises those mutation paths alongside the Poisson and load
checks (five tests pass). This prevents geometry drift during repeated evaluations;
it does not change the physical contact model or historical results.

## Bounded four-terminal feedback pilot

`python -m physics_layers.four_terminal_feedback_pilot` runs one 51-site case,
with 10 mV balanced reservoir drive, pinned output reservoirs, 30 mV electrostatic
gate, 300 K and EF=0.9 eV. Reservoir V means mu=EF+V and lead onsite shift=+V eV;
contact electrostatic potential is -V and device onsite shift is -phi. This is
an electron electrochemical convention, not an inferred work-function model.
The fixed compensating background is zero-onsite equilibrium occupation at EF.

The runner caps feedback charge calls at 80, writes progress and errors under
`runs/four-terminal-feedback-pilot`, and uses an exclusive retained attempt lock.
Do not remove the lock or launch a duplicate without diagnosing process state.
Source hashes are saved before the run; do not edit those sources while it runs.
Fixture construction and finite-charge support smoke checks passed (51 sites,
13x28x27 mesh). The completed run took 860.2 seconds and 60 charge calls, with
final full-grid potential residual 2.79e-14 V and recomputed occupation residual
5.77e-15 electrons/site. [Published evidence and plot](../results/physics-reference/four-terminal-feedback/README.md).
This is a pinned-output pilot, not loaded DC
or a restarted optimization campaign. Remote box electrodes remain uncalibrated.

### Continuation support for repeated bias evaluations

`solve_accelerated(..., initial_potential_v=...)` now accepts a copied, finite
site-potential initial guess from a neighboring bias. The default remains zero.
Every solve still recomputes charge and verifies the full-grid Poisson residual;
the initial guess never substitutes for a completed evaluation. Three accelerated
solver tests pass, including changed-bias warm/cold agreement on the independent
small feedback fixture and rejection of malformed guesses. This is numerical
verification, not a measured graphene speedup. The hybrid solver still builds a
numerical Jacobian, and multiple self-consistent branches remain possible;
future bias sweeps must compare cold starts and forward/reverse continuation.

The same-bias warm-start benchmark is available with
`python -m physics_layers.four_terminal_feedback_pilot --warm-start`.
It uses the published pilot potential as its initial guess, records the seed hash,
recomputes the neutral background, and retains a separate exclusive lock and
results in `runs/four-terminal-feedback-warm`. The 80-call ceiling and final
checks are unchanged. The completed benchmark used 57 versus 60 charge calls,
and 905.7 versus 860.2 seconds: no observed wall-time improvement. Maximum
potential difference was 8.34e-15 V and current difference 1.22e-21 A.
[Evidence](../results/physics-reference/four-terminal-feedback-warm/README.md).
These individual timings do not establish a performance distribution, and the
same-bias result does not establish changed-bias or loaded-output behavior.

### Optional Broyden feedback solver

`solve_accelerated(..., method="broyden1")` now uses rank-one Jacobian updates
instead of the default hybrid solver's finite-difference startup. Its initial
Jacobian is the identity (SciPy alpha=-1), with 100 iterations maximum and
site-residual target tolerance/100. Line searches can use multiple charge calls;
this is not a 100-call budget. Experiment runners must retain their charge-call
ceilings. The same full-grid and recomputed-occupation checks remain mandatory.
Five accelerated-solver tests pass, including agreement with independent direct
mesh iteration at positive, reversed and zero bias on the small reference fixture.
The default remains hybrid. Graphene convergence and speed are unmeasured for
this new option; no physical validation or search-readiness claim follows.

The bounded graphene comparison can now be run with
`python -m physics_layers.four_terminal_feedback_pilot --method broyden1`.
It starts from zero, uses the same fixture and tolerances as the published hybrid
pilot, and retains the 80-charge-call ceiling, source manifest and exclusive lock.
Its separate directory is `runs/four-terminal-feedback-pilot-broyden1`.
The completed graphene run used 13 charge calls and 225.34 seconds, compared
with hybrid's 60 calls and 860.23 seconds. Full-grid potential residual was
8.61e-8 V and occupation residual 1.24e-8 electrons/site. Maximum potential
difference from hybrid was 3.47e-8 V; terminal-current difference was 2.91e-15 A.
The recomputed neutral backgrounds agreed within 1.56e-15 electrons/site.
[Recorded comparison](../results/physics-reference/four-terminal-feedback-broyden/README.md).
This is one numerical fixture and one timing per method; changed-bias/load
behavior remains untested. The optional method does not change search scoring.

### First loaded feedback integration (pending)

`python -m physics_layers.loaded_feedback_pilot` couples the 51-site fixture to
10 kohm at one balanced 10 mV drive. Every current callback rebuilds the contact
boundaries and shifted leads and converges internal feedback from zero using
Broyden at 1e-6 tolerance. Circuit checks use 1e-13 A absolute plus 1e-6 relative
current tolerance, and retain current conservation, output KCL, Jacobian condition
and power balance. The runner caps 24 circuit callbacks and 240 charge calls;
a one-hour deadline is checked before each charge call (not an interrupt of an
in-flight call). Completed inner evaluations survive outer failure. Exclusive
attempt lock and source hashes live under runs/loaded-feedback-pilot.
Seven bridge/feedback tests pass. The actual loaded graphene result is pending.
This is one instantaneous drive, not AC rectification, with the existing
uncalibrated electrode, charge-width and bound-occupation assumptions.

The first loaded attempt failed before an output solution: the Matsubara pole
ceiling prevented the two-consecutive-refinement convergence test at the tighter
feedback tolerance. [Failure receipt](../results/physics-reference/loaded-feedback-first-attempt/README.md).
BiasChargeDevice now exposes max_poles explicitly, retaining the default 32768.
A higher-budget retry remains pending; tolerance criteria are unchanged.

A separate retry uses `python -m physics_layers.loaded_feedback_pilot --max-poles 131072`.
The selected pole ceiling is recorded and applied to both neutral and finite-bias
charge. It writes to runs/loaded-feedback-pilot-poles-131072, retaining the original
failed attempt. All accuracy, circuit-call, charge-call and elapsed-time limits
are unchanged. Retry results remain pending.

The higher-pole run cleared the first charge failure: its first two completed
inner solves passed at about 4.38e-9 V potential residual and 6.95e-10 electrons/site
occupation residual. Both callbacks requested exactly [0.005,-0.005,0,0] V.
The outer load solution is still pending. A separate ExactCurrentCache wrapper
now supports bounded in-memory reuse of identical voltages for a frozen,
deterministic provider. It never rounds voltages or caches failed evaluations;
new model/settings require a new cache. Four cache/bridge tests pass, including
preservation of 1e-12 V Jacobian perturbations, output-copy isolation and eviction.
The active pilot has not been modified to use it; integration is deferred until
that process finishes. This is an optimization mechanism, not new physics evidence.

### Cached loaded pilot retry

The runner now accepts `--cache-currents`, creating a separate `-cached` run
folder and recording this choice in status/results. Only exact repeated voltage
vectors reuse successful currents from this one frozen model instance; distinct
Jacobian probes still execute. The existing one-hour/240-charge-call limits and
all circuit/feedback checks remain. `circuit_calls` counts expensive cache misses,
not total outer requests. The prior timed-out attempt is retained.

A fresh 131072-pole cached attempt is the next runtime experiment. Six cache and
circuit tests pass, including full-solution equality on passive reference cases.
Its graphene completion and runtime benefit remain pending.

### Completed-load publication gate

`python -m physics_layers.report_loaded_complete RUN NEW_OUTPUT_FOLDER`
requires a complete outer solve and matching status/result source manifests.
It independently recomputes terminal current balance, output KCL, load power,
input/device power and power conservation, and checks the recorded final
Jacobian condition. Incomplete runs cannot create a publication folder.
Two tests check a passive resistor oracle and rejection of incomplete or
inconsistent records. These checks verify accounting; they do not physically
validate the model or turn a single drive into rectified DC.

### Opposite-drive comparison

`--reverse-drive` runs the same loaded pilot at -10 mV, with an additional
`-reverse` folder suffix and drive recorded in status/result. All model
assumptions, tolerances, budgets and cold inner initializations stay identical.
The positive-drive result remains preserved. The even component
(Vout(+V)+Vout(-V))/2 will test polarity asymmetry at these two points;
it is not a sinusoidal-cycle average or a physical-validation claim.

### Polarity diagnostic contract

`physics_layers.polarity.polarity_components` separates even and odd output
from equal-magnitude opposite drives. Three analytic tests cover a linear
response, a mixed linear/quadratic response, and invalid pairs. The quadratic
oracle makes the limitation explicit: its two-point even response is twice
its sinusoidal mean at the same amplitude. Thus even output cannot be labelled
sinusoidal DC without phase integration. Only use completed, matched-model
loaded results as inputs; the reverse graphene solve is still pending.

The completed-load reporter additionally checks that recorded L/R voltages
exactly match the declared balanced drive. A regression rejects a mislabeled
positive result presented as negative drive. The published positive result
passes this stricter check; reverse-drive completion remains pending.
