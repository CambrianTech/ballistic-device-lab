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
