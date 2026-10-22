# Physics gates for device discovery

The first implemented solver is a classical, elastic trajectory screen. It conserves
particles, models boundary and bulk scattering, and passes CPU/GPU agreement,
reciprocity, symmetry, and numerical-tolerance checks. These checks validate
its implementation within its assumptions. They do not establish a material model
or electrical rectification.

## Library choices

- **Kwant**: selected starting point for coherent graphene tight-binding transport.
  Its [graphene tutorial](https://kwant-project.org/doc/latest/tutorial/graphene)
  constructs a honeycomb lattice with leads and computes transport.
- **Pybinding**: optional model construction and band-structure tooling; its
  [Kwant export](https://docs.pybinding.site/en/stable/advanced/kwant.html) allows
  transport calculations through Kwant. It is not a separate rectification proof.
- **Tkwant**: candidate for AC dynamics. Its
  [documentation](https://tkwant.kwant-project.org/doc/stable/) includes time-dependent
  potentials, self-consistent mean-field calculations, and energy/heat extensions.

Kwant 1.5.0 is integrated as the optional `LatticeStage`, with an isolated conda
environment in `environment-quantum.yml`. The clean-ribbon and four-terminal
checks are recorded in [the lattice checkpoint](../results/2026-10-22-lattice/README.md).
This stage uses a CPU sparse solver; it does not inherit the ray tracer's CUDA
acceleration. Pybinding and Tkwant remain unintegrated options.

## Required progression

The [linear reservoir/load checkpoint](../results/2026-10-22-linear-load/README.md)
implements thermal occupation averaging and linear loaded terminal equations.
It does not complete the nonlinear or loaded-rectification gates below. Its
initial candidate output-voltage integration was unresolved. The subsequent
[matched coverage study](../results/2026-10-22-coverage/README.md) passes 145 of 180
output checks in the original study. The [integration follow-up](../results/2026-10-22-convergence/README.md)
resolves 31 of the 35 flags; four remain open.

| Gate | Model and evidence required |
| --- | --- |
| Lattice | Explicit physical dimensions, carbon lattice orientation, hopping parameters, lead doping, and edge termination; reproduce a clean ribbon's mode count and transmission before adding obstacles. |
| Conservation | Hermitian Hamiltonian, unitary scattering matrix within tolerance, current conservation, reciprocity where applicable, and zero current with all reservoirs at equal electrochemical potential and temperature. |
| Device robustness | Energy/carrier-density sweeps, edge disorder realizations, finite-temperature occupation, and contact variations. A coherent elastic calculation alone does not reproduce room-temperature phonon scattering. |
| Nonlinear transport | Specify the bias convention and voltage-dependent potential; test gauge invariance and convergence of electrostatics and energy integration. Static zero-bias transmission is insufficient. |
| Loaded rectification | Solve output terminal voltages with the load and drive; report cycle-averaged DC output, input power, contact dissipation, and conservation residuals. |
| Frequency response | Validate the quasistatic approximation or use a time-dependent solver; include external circuit and parasitic effects. |
| Comparison | Reproduce a published device's trends under matched dimensions, contacts, bias, temperature, and power boundaries before comparing searched candidates. |

The search must retain multiple geometries because the ranking can change at each
gate. A failed candidate remains in the record. The electrical efficiency target is

$$
\eta=\frac{P_{\mathrm{DC,load}}}{\langle P_{\mathrm{AC,input}}\rangle}.
$$

Any additional gate or bias supply must be accounted for separately or included
in a stated total-system denominator. No geometry score is converted into watts
or efficiency by a fitted scale factor without an independently justified model.
