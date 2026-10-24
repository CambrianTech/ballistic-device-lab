"""Publish only completed four-terminal feedback pilot evidence."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    run = Path("runs/four-terminal-feedback-pilot")
    status = json.loads((run / "status.json").read_text())
    if status["phase"] != "complete":
        raise SystemExit(f"Not publishing incomplete pilot: {status['phase']}")
    record = json.loads((run / "result.json").read_text())
    preflight = json.loads(
        Path("results/physics-reference/four-terminal-preflight/result.json").read_text()
    )
    positions = np.array(preflight["positions_m"])
    phi = np.array(record["site_potential_v"])
    excess = np.array(record["transport"]["electrons_per_site"]) - record["reference_occupations"]
    assert len(positions) == len(phi) == len(excess)
    assert record["history"][-1]["potential_residual_v"] < 1e-5
    assert record["history"][-1]["occupation_residual"] < 1e-5
    out = Path("results/physics-reference/four-terminal-feedback")
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for ax, values, title in zip(
        axes, [phi * 1000, excess], ["Self-consistent potential (mV)", "Excess electrons per site"]
    ):
        dots = ax.scatter(
            positions[:, 2] * 1e9, positions[:, 1] * 1e9, c=values, s=65, cmap="coolwarm"
        )
        fig.colorbar(dots, ax=ax, label=title)
        ax.set(xlabel="x (nm)", ylabel="y (nm)", aspect="equal")
    fig.suptitle("Four-terminal numerical fixture | pinned outputs | uncalibrated contacts")
    fig.savefig(out / "charge-potential.png", dpi=170)
    (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    summary = {k: status[k] for k in ["phase", "charge_evaluations", "elapsed_s"]}
    (out / "completion.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    residual = record["history"][-1]
    text = f"""# Four-terminal self-consistent feedback pilot

The 51-site, 0.984 nm nominal cavity uses EF 0.9 eV, 300 K, balanced 10 mV
reservoir drive, pinned output reservoirs and a 30 mV electrostatic gate.
The Gaussian charge width is 0.10 nm on a 0.10 nm mesh, dielectric constant 4.
The compensating background is the zero-onsite equilibrium occupation at EF.

Completed in {status["elapsed_s"]:.1f} s with {status["charge_evaluations"]} charge calls.
Final full-grid potential residual: {residual["potential_residual_v"]:.3g} V;
recomputed occupation residual: {residual["occupation_residual"]:.3g} electrons/site.
Potential range: {phi.min() * 1000:.4f} to {phi.max() * 1000:.4f} mV.

![Charge and potential](charge-potential.png)

Reservoir V means mu=EF+V and lead onsite shift=+V eV; contact electrostatic
potential is -V and device onsite shift is -phi. Remote box faces are surrogate
contacts, not a calibrated metal/graphene interface. Width, gate geometry and
bound-state occupation policy remain assumptions. This is one converged numerical
case, not a mesh study, physical validation or device-improvement claim.
Output reservoirs are pinned: these currents are not a loaded DC result.

[Result and solver source hashes](result.json) | [Completion receipt](completion.json).
Reproduce solver: `python -m physics_layers.four_terminal_feedback_pilot` (exclusive
attempt lock requires deliberate recovery before rerunning). Render completed data:
`python -m physics_layers.report_four_terminal_feedback`.
"""
    (out / "README.md").write_text(text, encoding="utf-8")
    print(
        json.dumps(
            dict(summary=summary, residual=residual, currents=record["transport"]["currents_a"])
        )
    )


if __name__ == "__main__":
    main()
