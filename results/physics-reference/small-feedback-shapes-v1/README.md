# First small-geometry charge-feedback comparison

The completed opposite-bias solves give the following even transverse-current
difference, `(I_top - I_bottom)` averaged over the two bias signs:

| Geometry | Sites | Even current difference | Magnitude / control |
| --- | ---: | ---: | ---: |
| Empty synthetic control | 51 | -525.969 pA | 1.000 |
| Triangle | 49 | -130.705 pA | 0.249 |

The triangle did not improve this screening observable. Reversing its nominal
outline produced the same atomic lattice and was rejected, not scored twice.

Conditions: 0.984 nm width, 0.6 contact fraction, longitudinal reservoir voltages
±5 mV (10 mV difference), grounded transverse terminals, 300 K, 0.9 eV reference
Fermi energy, and the existing surrogate charge/Poisson boundary model. These
are two static bias points, not a sinusoidal cycle average or delivered load
power. The full-size champion is not comparable and remains preserved.

Both triangle feedback residuals were below 5.7e-9 V, and its current-sum residual
was 2.04e-23 A or smaller. These establish solver consistency, not calibrated
physical accuracy. Integration diagnostics are retained in `summary.json`;
mesh, energy, occupation assumptions and bias refinement remain unresolved.

Raw evaluations, terminal run status (including the duplicate failure), and
source hashes are preserved alongside this report. Reproduce the summary with:

```sh
python -m ballistic_lab.reporting.small_feedback_report runs/small-feedback-shapes-v1 new-summary.json
```

The command requires a new output file. This completed experiment establishes a
baseline for distinct atomic geometries; it does not demonstrate novel physics.
