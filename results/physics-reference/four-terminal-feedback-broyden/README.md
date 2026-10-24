# Cold-start Broyden comparison

Same 51-site graphene fixture, reservoir voltages, neutral background, gate,
charge width, mesh and requested tolerances as the original hybrid pilot.
Both methods start from zero potential; Broyden updates a Jacobian approximation.

| Solver | Charge calls | Wall seconds |
| --- | ---: | ---: |
| Hybrid | 60 | 860.23 |
| Broyden | 13 | 225.34 |

Maximum solution difference: 3.47e-08 V;
maximum terminal-current difference: 2.91e-15 A.
Final full-grid residual: 8.61e-08 V;
recomputed occupation residual: 1.24e-08 electrons/site.

These are single-run wall times, not controlled timing statistics or evidence
across devices. Outputs remain pinned; this is neither loaded DC nor physical
validation. Contact calibration and occupation assumptions remain unresolved.
The default solver is unchanged pending wider numerical checks.

[Result and source hashes](result.json) | [Comparison](comparison.json).
Render with `python -m physics_layers.report_feedback_broyden`.
