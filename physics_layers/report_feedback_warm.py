"""Compare completed same-bias feedback runs without rerunning transport."""

import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    baseline = Path("results/physics-reference/four-terminal-feedback")
    run = Path("runs/four-terminal-feedback-warm")
    status = json.loads((run / "status.json").read_text())
    if status["phase"] != "complete":
        raise SystemExit("Warm benchmark is not complete")
    seed = (baseline / "result.json").read_bytes()
    cold = json.loads(seed)
    warm = json.loads((run / "result.json").read_text())
    assert warm["seed_sha256"] == hashlib.sha256(seed).hexdigest()
    for key in ("reservoir_voltages_v", "gate_electrostatic_v", "convention"):
        assert cold[key] == warm[key]
    for record in (cold, warm):
        assert record["history"][-1]["potential_residual_v"] < 1e-5
        assert record["history"][-1]["occupation_residual"] < 1e-5
    prior = json.loads((baseline / "completion.json").read_text())
    delta_phi = float(np.max(np.abs(np.array(warm["site_potential_v"]) - cold["site_potential_v"])))
    delta_i = float(
        np.max(np.abs(np.array(warm["transport"]["currents_a"]) - cold["transport"]["currents_a"]))
    )
    summary = dict(
        cold_calls=prior["charge_evaluations"],
        warm_calls=status["charge_evaluations"],
        cold_seconds=prior["elapsed_s"],
        warm_seconds=status["elapsed_s"],
        max_potential_difference_v=delta_phi,
        max_current_difference_a=delta_i,
    )
    out = Path("results/physics-reference/four-terminal-feedback-warm")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(warm, indent=2), encoding="utf-8")
    (out / "comparison.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "README.md").write_text(
        f"""# Same-bias warm-start benchmark

The published converged 51-site graphene potential initializes the same operating
point. Neutral background and charge are recomputed; full-grid and occupation
residual checks are retained. Source and seed hashes are in [result.json](result.json).

| Initialization | Charge evaluations | Wall seconds |
| --- | ---: | ---: |
| Zero | {summary["cold_calls"]} | {summary["cold_seconds"]:.1f} |
| Published solution | {summary["warm_calls"]} | {summary["warm_seconds"]:.1f} |

Maximum potential difference: {delta_phi:.3g} V; maximum current difference:
{delta_i:.3g} A. Wall times are individual observations, not controlled timing
statistics. The hybrid method still builds a numerical Jacobian; a converged
initial guess does not bypass that cost. This same-bias test does not establish
performance at changed bias, branch uniqueness, loaded DC or physical validation.

[Machine-readable comparison](comparison.json). Reproduce the report with
`python -m physics_layers.report_feedback_warm`.
""",
        encoding="utf-8",
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
