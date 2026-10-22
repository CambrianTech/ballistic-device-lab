# Determine the useful device function

The first application hypothesis is a passive electrical detector: convert an
alternating input into a DC indication. A useful detector need not recover much
power, but its signal must be distinguishable from noise. The separate hypothesis
of efficient power rectification is evaluated using actual delivered DC power and
terminal input power. A high voltage response alone qualifies neither role.

## Qualification sequence

Application requirements govern survival in future campaigns. Keep separate
archives for detection (noise-equivalent input power subject to bandwidth,
dynamic-range and robustness requirements) and power recovery (useful DC power
and efficiency subject to input/load and thermal requirements). A geometry may
survive in either archive. Missing required physics yields an unqualified result,
not a favorable score. Numeric requirements must be frozen with the reference
device and use case before optimization; do not move them after seeing results.

The first equilibrium-noise implementation and weak-excitation audit are now
available in [the detector audit](../results/physics-reference/detector-audit/README.md).
It is a partial physical model, not an application acceptance certificate.

1. Retain absolute terminal input power, loaded DC voltage, DC load power and
   conversion efficiency. These are already computed by the circuit solver and
   now published automatically beside the nominal leader and controls.
2. Sweep excitation amplitude and readout load on each frozen candidate. Report
   the response curve, differential responsivity, quadratic-response region,
   compression and output impedance. Include convergence at small signal levels.
3. Add a validated multiterminal equilibrium noise model with the actual source
   and load boundary conditions. Combine it with the readout amplifier noise;
   derive NEP from output noise density divided by the appropriate responsivity.
   A resistor-only Johnson estimate is not the complete detector noise model.
4. Establish frequency-dependent transport and parasitic/antenna coupling before
   assigning GHz/THz bandwidth or comparing optical responsivity. The current
   quasistatic solver has no carrier-frequency prediction.
5. Reproduce published detector curves using matched geometry, carrier density,
   temperature, input-power definition and readout. Shi et al. target detection at
   3 THz; their reported 100 V/W and 20 pW/√Hz are experimental optical detector
   metrics, not directly comparable with our electrical-terminal values.
6. Select candidates on the application metric only in a new versioned campaign.
   Use a frozen operating envelope and held-out conditions. Keep peak power,
   worst-condition behavior and fabrication sensitivity visible separately.

Source: [Shi et al., Small Science (2026)](https://onlinelibrary.wiley.com/doi/full/10.1002/smsc.202500654).
The existing campaign remains a fixed-potential geometry screen. Self-consistent
electrostatics is still required for device qualification; the numerical modules
under `physics_layers/` do not yet close the production graphene charge model.
