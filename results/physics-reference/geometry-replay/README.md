# Geometry adapter replay and small-shape experiment

The completed replay (`status.json`) reproduced the saved 51-site pilot in
317.9 seconds. Maximum differences were 4.13e-15 V in site potential,
5.83e-22 A in terminal current, and 1.12e-15 electrons per site. All three
predeclared tolerances passed. This verifies adapter parity, not physical validity.

The bounded experiment runs an empty control and up/down triangular obstacles
at 0.984 nm width, 0.6 contact fraction, with both signs of 10 mV longitudinal
bias and grounded transverse terminals. It retains the existing uncalibrated
charge/Poisson assumptions. Atomic-lattice duplicates fail explicitly.

```sh
python -m ballistic_lab.pipeline.small_feedback_experiment --output runs/my-small-shapes
```

Use a new output directory and single-thread BLAS. Each geometry permits two
feedback evaluations, 80 charge calls and a 3600-second cooperative time budget
(checked between numerical calls). One CPU worker evaluates cases sequentially.
Create `STOP` inside its output directory to stop between bias evaluations.
Partial evaluations and failures remain recorded. The even transverse current
difference is a screening observable, not delivered load power or cycle-averaged
DC. This is a three-case experiment, not an evolutionary campaign. Its results
cannot replace the full-size retained champion; refinement and matched loaded
comparisons are still required before promotion.
