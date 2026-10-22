# Physics extension layers

This package is separate while the continuous workers hold immutable source manifests. It does not change their physics or rankings. The existing generic `PhysicsStage` remains the device-level orchestration interface; field subsolvers take their own meshes rather than pretending every mesh is a four-contact square.

Implemented:

- `stages.run_stages`: dependency-ordered execution, configuration/source receipts and executable validation gates; missing dependencies and failed checks block downstream work. `dc_stage` connects the existing quasistatic circuit solver with phase-doubling acceptance. See [stage architecture and build sequence](STAGES.md). These are opt-in and do not modify the running search.

- `self_consistent.solve_charge_field`: damped iteration between an explicit `ChargeProvider` and the 2D Poisson solver. Checks the unmixed potential residual and re-evaluates charge at the proposed field before accepting; returns iteration history or raises `ConvergenceError`. Inner solver failures propagate. Tested against a manufactured screened-charge solution, including a joint potential/reference shift and tiny-mixing false-convergence regression. This is a working coordinator, not an implemented graphene charge model.
- `poisson2d.Poisson2DStage`: sparse Cartesian field solver with independent x/y spacing, face dielectric maps, volumetric charge and fixed outer/internal electrode potentials. Unknown nodes are explicit NaNs in the potential input; result arrays are immutable snapshots. Supports electrode geometry without imposing a particular device topology. Tests cover second-order mesh convergence, dielectric displacement continuity, gauge invariance and an internal electrode. This z-invariant model does not represent graphene sheet charge or its surrounding 3D dielectric stack.
- `electrostatics.Poisson1DStage`: uniform-grid finite-volume planar electrostatics with face permittivity, volumetric charge and Dirichlet boundaries. Returns potential, face electric field and charge-equation residual, in SI units. Analytic uniform-charge and layered-dielectric tests check sign, scale and displacement continuity.
- `coupling.TerminalPhasor`: explicit peak/RMS convention, frequency, reference plane and current-into-device sign. Computes real average terminal power, including reactive-phase rejection.
- `coupling.PassiveOpticalBudget`: checks nonnegative passive channel powers and energy balance with caller-specified tolerances. It does not calculate electromagnetic fields.

Next implementations, in dependency order:

1. Map the rectifier's actual dielectric/contact stack into a suitable electrostatic domain, including 3D or a justified reduced sheet-charge model. The Cartesian 2D solver is implemented and verified; a graphene device mapping is still required. Etched transport obstacles must not silently become fixed-potential metal electrodes.
2. Supply the coordinator with a physically justified graphene charge provider and conservative mesh/site charge mapping. Account for reference/background charge and reservoir occupations; verify charge integration, gauge consistency and inner solver convergence. Existing transmission matrices alone do not provide local charge. The current manufactured linear screening fixture is solely a numerical test.
3. Explicit disorder/scattering models with matched ensemble seeds; phonon temperature is distinct from reservoir occupation temperature.
4. Maxwell backend with dispersive materials, ports, mesh convergence and calibrated field-to-terminal coupling.
5. Driven transport and readout/noise stage, then electrical and optical efficiency with explicit input-power boundaries.

Every result needs the geometry/material/operating-condition identity, solver source identity, numerical convergence and declared model omissions before search promotion. New modules remain unused by the running campaign until an explicit validated integration. No placeholder solver emits a score.

Run: `python -m unittest discover -s tests -p test_physics_layers.py`.

For the 2D field solver: `python -m unittest discover -s tests -p test_poisson2d.py`.
Its algebraic residual checks the discrete equation; mesh refinement is a separate test.
Build device-specific mesh adapters outside the solver so later geometries reuse the
same numerical implementation. Keep physical units, boundaries and material maps
explicit; integration with search waits for charge closure and transport validation.
