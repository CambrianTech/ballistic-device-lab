# Staged implementation and acceptance

`stages.run_stages` executes a dependency graph. Before any solver starts it
rejects missing dependencies, duplicate names and cycles. Each stage supplies
its source identity, configuration, assumptions and executable checks. A solver
exception or failed check prevents downstream execution. Completed-stage receipts
are retained on the failure; a failed stage supplies no accepted output.

Stages consume only their declared dependencies. Keep payloads immutable. The
manifest records run identity, sources, configuration and passed checks; its hash
is provenance, not a result checksum or a cache key. There is no automatic search
promotion and no claim that arbitrary user-supplied validators certify physics.

## Build sequence

| Stage | Implementation now | Acceptance before device claims |
| --- | --- | --- |
| Geometry, materials and domain | Existing SquareDevice; explicit run identities | Physical scale, dielectric/contact stack, etched-boundary interpretation |
| Transport screening | Existing ray/lattice and frozen-potential models | Conservation, equilibrium, reciprocity where applicable, energy/mesh refinement |
| Coupled charge and transport | Poisson solvers and charge iteration coordinator | Physical graphene charge, conservative mapping, reference charge, gauge consistency; convergence at each applied bias |
| Quasistatic circuit/readout | `dc_stage` wraps the existing load/cycle solver | KCL/passivity/power checks in circuit solver plus phase doubling; keep DC and ripple power separate |
| Scattering and robustness | Extension point | Matched disorder ensembles, contact/edge perturbations, physical phonon model; occupation temperature alone is insufficient |
| Electromagnetic drive | Phasor and power-budget contracts only | Dispersive Maxwell solver, mesh/port checks, calibrated coupling, back-action if relevant |
| Frequency/noise/system efficiency | Extension point | Dynamic transport and noise model, explicit incident/absorbed/bias power boundaries |

This is a dependency graph, not a requirement to feed ray scores into quantum
transport. Geometry/material preparation is shared. Coupled electrostatics and
transport form one stage with an internal iteration, not a cycle in the graph.
An electromagnetic drive is a separate branch joining transport through a
validated coupling adapter. Unsupported stages are omitted or required as missing
dependencies, never replaced by identity transforms or fabricated scores.

## Calling the implemented path

Construct an upstream `Stage` named `transport` whose evaluator returns a
`TerminalCurrentModel`. Its checks must validate that particular physical model;
record energy grid, temperature, reference and geometry settings in its
`configuration_json`. Its source identity must cover the implementation and checks.
Then construct `dc_stage(DCRequest(amplitude_v=0.01, load_ohm=10000),
current_stage="transport", source_identity=<circuit and adapter source digest>)`.
Pass both to `run_stages(RunIdentity(device, materials, operating_conditions), stages)`.

The DC result contains coarse and refined cycles. Use `.refined` only after the
run succeeds. The adapter checks phase doubling for DC voltage, useful DC power,
total load power, mean input and device power. A pair of grids agreeing is a
numerical check, not proof against all aliasing or physical-model error. Tighter
tolerances and additional refinements are needed where the waveform demands them.

The executable example is `tests/test_physics_stages.py`: a passive linear
four-terminal network passes the circuit stage and produces zero DC. Additional
tests inject refinement failure and inner-solver failure and verify downstream
work never executes. These fixtures do not model graphene.

Run `python -m unittest tests.test_physics_stages`. Integration into a new search
campaign requires explicit source manifests and matched baseline validation;
the currently running search remains on its existing model.
