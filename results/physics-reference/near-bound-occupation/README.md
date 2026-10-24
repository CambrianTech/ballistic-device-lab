# Sensitivity near a bound-state occupation transition

This synthetic chain holds its Hamiltonian and reservoir chemical potentials fixed while moving the explicit bound-occupation reference from 20 meV below to 20 meV above the bound pole. The eight cases cover onsite impurities ±0.7 eV and temperatures 150 and 600 K.

The analytic reference includes both continuum and discrete-pole weight, as derived in the [complete chain reference](../impurity-bound-reference/README.md). With fixed onsite potential the bound occupation can change charge without changing transmission or current. In a self-consistent electrostatic model that changed charge could alter potential; this experiment does not solve that feedback.

This tests the chosen closure numerically, not whether a physical isolated state equilibrates to that reference. The reference is deliberately near the pole, far from the transport reservoirs, to expose assumption sensitivity rather than represent a calibrated device.

Reproduce with:

```sh
python -m physics_layers.impurity_bound_reference --near-bound --output new-output-directory
```

The result file must not already exist. [Raw cases](result.json) include charge, current, analytic errors and spectral sum-rule checks. Historical results are preserved.

Measured charge changes: 0.428819895184748 electrons at 150 K and 0.126215384979774 electrons at 600 K. All eight analytic comparisons passed; maximum charge error 1.14e-10 electrons and maximum current error 4.75e-20 A.

## Reproduction metadata

New runs record Python and NumPy/SciPy/Kwant versions, source SHA-256 hashes, reservoir potentials, spin, reference mode and numerical tolerances in the result. Existing historical result files remain unchanged and do not acquire retrospective provenance. An existing result is rejected before numerical work; exclusive creation at write time also prevents replacement if another process creates it during the calculation.
