# Completed self-consistent loaded operating point

The cached 51-site graphene charge/Poisson pilot completed its outer load solve
and final circuit checks in **3048.69 seconds (50.8 minutes)**, using 126 charge
calls and nine expensive current evaluations. The prior uncached attempt
exhausted its one-hour budget before final conditioning checks. This establishes
completion within the same budget, not an exact end-to-end speedup ratio against
an uncached completed run.

| Quantity | Result |
| --- | ---: |
| Balanced input drive | +10 mV |
| Load | 10 kohm |
| Output VB-VT | -2.236321536 microvolts |
| Instantaneous load power | 5.001134e-16 W |
| Input power | 2.737132644e-9 W |
| Device absorption | 2.737132144e-9 W |
| Maximum output KCL residual | 3.54e-21 A |
| Power balance residual | -2.20e-26 W |
| Final output Jacobian condition | 8.83017 |

The root solver reports success. Independent recomputation from terminal
voltages and currents passed via `physics_layers.report_loaded_complete`.
[result.json](result.json) preserves the solution, numerical tolerances and
source hashes; [completion.json](completion.json) records worker completion;
[accounting.json](accounting.json) contains independently recomputed checks.

This is **one instantaneous operating point, not rectified DC power**. The
chosen Gaussian charge width, surrogate contact/gate geometry, occupation
closure, EF=0.9 eV and 300 K remain model assumptions. Numerical convergence
and circuit accounting are not physical validation or evidence of novelty.
Historical fixed-potential rankings cannot be compared directly to this tiny
fixture's power.

The next physics experiment is opposite drive under identical assumptions,
followed by phase sampling if both signs pass. Model sensitivity, numerical
refinement and matched controls are required before a fresh geometry search.
The stopped historical campaign and prior unsuccessful attempts are preserved.

Reproduce publication into a new directory:

```powershell
python -m physics_layers.report_loaded_complete runs/loaded-feedback-pilot-poles-131072-cached NEW_OUTPUT_FOLDER
```
