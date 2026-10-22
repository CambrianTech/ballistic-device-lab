# Physics extension layers

This package is separate while the continuous workers hold immutable source manifests. It does not change their physics or rankings. The existing generic `PhysicsStage` remains the device-level orchestration interface; field subsolvers take their own meshes rather than pretending every mesh is a four-contact square.

Implemented:

- `electrostatics.Poisson1DStage`: uniform-grid finite-volume planar electrostatics with face permittivity, volumetric charge and Dirichlet boundaries. Returns potential, face electric field and charge-equation residual, in SI units. Analytic uniform-charge and layered-dielectric tests check sign, scale and displacement continuity.
- `coupling.TerminalPhasor`: explicit peak/RMS convention, frequency, reference plane and current-into-device sign. Computes real average terminal power, including reactive-phase rejection.
- `coupling.PassiveOpticalBudget`: checks nonnegative passive channel powers and energy balance with caller-specified tolerances. It does not calculate electromagnetic fields.

Next implementations, in dependency order:

1. Geometry-aware 2D/3D Poisson and charge-density interfaces, tested on manufactured solutions and interface conditions.
2. Self-consistent transport/Poisson iteration with charge closure, mixing, gauge tests and convergence failure propagation. The current 1D solver is a verification building block, not a substitute for that calculation.
3. Explicit disorder/scattering models with matched ensemble seeds; phonon temperature is distinct from reservoir occupation temperature.
4. Maxwell backend with dispersive materials, ports, mesh convergence and calibrated field-to-terminal coupling.
5. Driven transport and readout/noise stage, then electrical and optical efficiency with explicit input-power boundaries.

Every result needs the geometry/material/operating-condition identity, solver source identity, numerical convergence and declared model omissions before search promotion. New modules remain unused by the running campaign until an explicit validated integration. No placeholder solver emits a score.

Run: `python -m unittest discover -s tests -p test_physics_layers.py`.
