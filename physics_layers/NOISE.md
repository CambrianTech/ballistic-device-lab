# Equilibrium output noise

The stage implements the low-frequency fluctuation-dissipation relation
`S_I = 2 k_B T (G + Gᵀ)` with a one-sided spectral density per Hz. For reciprocal
conductance this is `4 k_B T G`. Off-diagonal current correlations are retained.
This is the equilibrium limit, not finite-drive shot noise or carrier bandwidth.

Input L/R potentials are clamped by ideal noiseless voltage sources. The T/B
output has a resistor at the device temperature. Its correlated Johnson-current
source is added to the output block. Solving the two-node nodal equation yields
the differential voltage PSD, separately attributed to device and load. The total
equals `4 k_B T R_equivalent` for the passive network. No independent noise is
invented for each terminal, and the load is not counted twice.

Analytic tests cover two grounded resistors plus a differential load, a correlated
transverse branch, temperature scaling, terminal exchange, and invalid/floating
networks. Thermal energy-grid convergence remains a separate device-level gate.

Reference: [Büttiker, Scattering theory of current and intensity noise correlations
in conductors and wave guides (1992)](https://doi.org/10.1103/PhysRevB.46.12485).

This can supply an equilibrium electrical NEP estimate when combined with a
converged weak-signal responsivity. It cannot certify optical NEP, excess driven
noise, flicker noise, amplifier noise, antenna efficiency or THz bandwidth.
