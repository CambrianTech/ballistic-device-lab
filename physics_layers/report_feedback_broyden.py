"""Publish the completed cold-start graphene solver comparison."""

import json
from pathlib import Path

import numpy as np


def main():
    base = Path("results/physics-reference/four-terminal-feedback")
    run = Path("runs/four-terminal-feedback-pilot-broyden1")
    status = json.loads((run / "status.json").read_text())
    if status["phase"] != "complete":
        raise SystemExit("Broyden benchmark is not complete")
    cold = json.loads((base / "result.json").read_text())
    result = json.loads((run / "result.json").read_text())
    timing = json.loads((base / "completion.json").read_text())
    assert result["method"] == "broyden1" and result["initialization"] == "zero"
    for key in (
        "reservoir_voltages_v",
        "gate_electrostatic_v",
        "convention",
    ):
        assert result[key] == cold[key]
    np.testing.assert_allclose(
        result["reference_occupations"], cold["reference_occupations"], rtol=0, atol=1e-12
    )
    residual = result["history"][-1]
    assert residual["potential_residual_v"] < 1e-5
    assert residual["occupation_residual"] < 1e-5
    summary = dict(
        hybrid_calls=timing["charge_evaluations"],
        broyden_calls=status["charge_evaluations"],
        hybrid_seconds=timing["elapsed_s"],
        broyden_seconds=status["elapsed_s"],
        potential_difference_v=float(
            np.max(np.abs(np.array(result["site_potential_v"]) - cold["site_potential_v"]))
        ),
        current_difference_a=float(
            np.max(
                np.abs(
                    np.array(result["transport"]["currents_a"]) - cold["transport"]["currents_a"]
                )
            )
        ),
        final_residual=residual,
    )
    out = Path("results/physics-reference/four-terminal-feedback-broyden")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "comparison.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "README.md").write_text(
        f"""# Cold-start Broyden comparison

Same 51-site graphene fixture, reservoir voltages, neutral background, gate,
charge width, mesh and requested tolerances as the original hybrid pilot.
Both methods start from zero potential; Broyden updates a Jacobian approximation.

| Solver | Charge calls | Wall seconds |
| --- | ---: | ---: |
| Hybrid | {summary["hybrid_calls"]} | {summary["hybrid_seconds"]:.2f} |
| Broyden | {summary["broyden_calls"]} | {summary["broyden_seconds"]:.2f} |

Maximum solution difference: {summary["potential_difference_v"]:.3g} V;
maximum terminal-current difference: {summary["current_difference_a"]:.3g} A.
Final full-grid residual: {residual["potential_residual_v"]:.3g} V;
recomputed occupation residual: {residual["occupation_residual"]:.3g} electrons/site.

These are single-run wall times, not controlled timing statistics or evidence
across devices. Outputs remain pinned; this is neither loaded DC nor physical
validation. Contact calibration and occupation assumptions remain unresolved.
The default solver is unchanged pending wider numerical checks.

[Result and source hashes](result.json) | [Comparison](comparison.json).
Render with `python -m physics_layers.report_feedback_broyden`.
""",
        encoding="utf-8",
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
