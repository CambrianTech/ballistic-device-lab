# Same-bias warm-start benchmark

The published converged 51-site graphene potential initializes the same operating
point. Neutral background and charge are recomputed; full-grid and occupation
residual checks are retained. Source and seed hashes are in [result.json](result.json).

| Initialization | Charge evaluations | Wall seconds |
| --- | ---: | ---: |
| Zero | 60 | 860.2 |
| Published solution | 57 | 905.7 |

Maximum potential difference: 8.34e-15 V; maximum current difference:
1.22e-21 A. Wall times are individual observations, not controlled timing
statistics. The hybrid method still builds a numerical Jacobian; a converged
initial guess does not bypass that cost. This same-bias test does not establish
performance at changed bias, branch uniqueness, loaded DC or physical validation.

[Machine-readable comparison](comparison.json). Reproduce the report with
`python -m physics_layers.report_feedback_warm`.
