"""Report the follow-up without rewriting original coverage acceptance."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm


def main():
    output = Path("results/2026-10-22-convergence")
    rows = sorted(json.loads((output / "summary.json").read_text()), key=lambda r: r["case"]["key"])
    if len(rows) != 7 or any(r["status"] != "completed" for r in rows):
        raise ValueError("Report requires the complete seven-case follow-up")
    ratios = np.array(
        [
            [
                max(
                    level["convergence"][i]["change_v"] / level["convergence"][i]["tolerance_v"]
                    for level in row["levels"][1:]
                )
                for i in range(12)
            ]
            for row in rows
        ]
    )
    fig, axis = plt.subplots(figsize=(13, 6))
    mesh = axis.imshow(
        np.maximum(ratios, 1e-4),
        norm=LogNorm(0.01, max(10, ratios.max())),
        cmap="viridis",
        aspect="auto",
    )
    axis.set_yticks(range(7), [r["case"]["key"] for r in rows])
    axis.set_xticks(
        range(12),
        [f"{mu:.2f} eV\n{load:g} kΩ" for mu in (0.75, 0.90, 1.05) for load in (1, 10, 100, 1000)],
    )
    for (i, j), value in np.ndenumerate(ratios):
        axis.text(
            j,
            i,
            f"{value:.2g}" + (" *" if value > 1 else ""),
            ha="center",
            va="center",
            color="black" if mesh.norm(max(value, 1e-4)) > 0.7 else "white",
            fontsize=8,
        )
    fig.colorbar(mesh, ax=axis, label="Worst output change / allowed change (≤1 passes)")
    axis.set_title(
        "Follow-up: both 1025→2049 and 2049→4097 refinements\n"
        "* remains unresolved; all 84 outputs of the seven selected devices shown"
    )
    fig.tight_layout()
    fig.savefig(output / "convergence-ratios.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
