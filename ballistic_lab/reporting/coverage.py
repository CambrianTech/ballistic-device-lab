"""Full matched matrix with conspicuous convergence failures and controls."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ballistic_lab.experiments.coverage import CONDITIONS, CoveragePlan


def main():
    output = Path("results/2026-10-22-coverage")
    records = json.loads((output / "summary.json").read_text())
    plan = CoveragePlan()
    lookup = {row["case"]["key"]: row for row in records}
    shape = (len(plan.candidate_ids), len(CONDITIONS) * len(plan.fermi_ev))
    voltage = np.full(shape, np.nan)
    passed = np.zeros(shape, dtype=bool)
    convergence = np.zeros((len(plan.candidate_ids) * len(CONDITIONS), 12), dtype=int)
    labels = []
    for i, candidate in enumerate(plan.candidate_ids):
        for j, (condition, _, _) in enumerate(CONDITIONS):
            key = f"{candidate}-{condition}"
            labels.append(key)
            record = lookup[key]
            if record["status"] != "completed":
                continue
            convergence[i * len(CONDITIONS) + j] = np.array(record["observable_converged"], int)
            for k, fermi in enumerate(plan.fermi_ev):
                index = next(
                    n
                    for n, row in enumerate(record["levels"][-1]["loads"])
                    if row["fermi_ev"] == fermi and row["load_ohm"] == 1e4
                )
                voltage[i, j * len(plan.fermi_ev) + k] = (
                    record["levels"][-1]["loads"][index]["output_voltage_v"] * 1e6
                )
                passed[i, j * len(plan.fermi_ev) + k] = record["observable_converged"][index]
    fig, axis = plt.subplots(figsize=(14, 5))
    limit = max(float(np.nanmax(abs(voltage))), 1e-9)
    plot = axis.imshow(voltage, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
    axis.set_yticks(range(len(plan.candidate_ids)), plan.candidate_ids)
    columns = [
        f"{condition}\nEF={fermi:.2f} eV"
        for condition, _, _ in CONDITIONS
        for fermi in plan.fermi_ev
    ]
    axis.set_xticks(range(len(columns)), columns, fontsize=9)
    for (i, j), value in np.ndenumerate(voltage):
        label = (
            "FAILED" if not np.isfinite(value) else f"{value:.2f}" + ("" if passed[i, j] else " ×")
        )
        axis.text(
            j,
            i,
            label,
            ha="center",
            va="center",
            color="white" if np.isfinite(value) and abs(value) > 0.55 * limit else "black",
        )
    fig.colorbar(plot, ax=axis, label="Signed linear output (µV)")
    axis.set_title(
        "Matched coverage: 1 mV drive, 10 kΩ load, 300 K occupations\n× = output has not passed both grid refinements; color is not evidence of superiority"
    )
    fig.tight_layout()
    fig.savefig(output / "coverage-voltage.png", dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(12, 8))
    axis.imshow(convergence, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    axis.set_yticks(range(len(labels)), labels, fontsize=9)
    axis.set_xticks(
        range(12),
        [f"{mu:.2f} eV\n{load / 1e3:g} kΩ" for mu in plan.fermi_ev for load in plan.loads_ohm],
    )
    for (i, j), value in np.ndenumerate(convergence):
        axis.text(j, i, "PASS" if value else "NO", ha="center", va="center", fontsize=8)
    axis.set_title(
        "Observable convergence: two successive refinements\nPASS = change ≤ 1 nV + 1% of output on both 257→513 and 513→1025 grids"
    )
    fig.tight_layout()
    fig.savefig(output / "coverage-convergence.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
