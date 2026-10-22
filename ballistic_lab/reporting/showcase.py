"""Render real CPU trajectories and saved search outcomes without selecting winners."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

from ballistic_lab.geometry.families import geometry
from ballistic_lab.transport.cpu import trace

BACKGROUND = "#0b1426"
INK = "#e2eaf4"
COLORS = ("#51d6ca", "#ffa857")


def trajectories(candidate: dict, output: Path) -> None:
    """Show first 16 rays from each input, fixed seed, in both scattering regimes."""
    polygons = geometry(candidate["family"], candidate["x"])
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), facecolor=BACKGROUND)
    for ax, mfp, specularity, title in zip(
        axes,
        (None, 2.0),
        (1.0, 0.8),
        ("Ballistic paths", "Bulk + boundary scattering"),
    ):
        ax.set_facecolor(BACKGROUND)
        for port, color in enumerate(COLORS):
            _, _, paths = trace(polygons, port, n=16, seed=314159, specularity=specularity, mfp=mfp)
            for path in paths.values():
                points = np.asarray(path)
                ax.plot(points[:, 0], points[:, 1], color=color, alpha=0.4, lw=0.8)
        for polygon in polygons:
            ax.add_patch(Polygon(polygon, facecolor="#26364f", edgecolor=INK, lw=1.3))
        ax.plot([-1, 1, 1, -1, -1], [-1, -1, 1, 1, -1], color="#7789a4", lw=1)
        for x, y in (
            ([-1, -1], [-0.3, 0.3]),
            ([1, 1], [-0.3, 0.3]),
            ([-0.3, 0.3], [-1, -1]),
            ([-0.3, 0.3], [1, 1]),
        ):
            ax.plot(x, y, color=INK, lw=4)
        ax.set(xlim=(-1.08, 1.08), ylim=(-1.08, 1.08), aspect="equal")
        ax.set_title(title, color=INK, fontsize=16, pad=15)
        ax.axis("off")
    fig.suptitle("GEOMETRY STEERS TRANSPORT", color=INK, fontsize=23, weight="bold")
    fig.text(
        0.5,
        0.035,
        "32 classical trajectories per panel · cyan: left input · amber: right input\n"
        "Same geometry and launch seed · right: mean free path = cavity width, specularity 0.8",
        ha="center",
        color=INK,
        fontsize=10,
    )
    fig.subplots_adjust(top=0.84, bottom=0.13, wspace=0.12)
    fig.savefig(output / "trajectories.png", dpi=180, facecolor=BACKGROUND)
    plt.close(fig)


def search_progress(result: dict, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    for ax, family in zip(axes, ("triangle", "beveled")):
        for method, color in zip(("global", "mutation"), COLORS):
            for repeat in range(result["plan"]["repeats"]):
                rows = [
                    r
                    for r in result["training"]
                    if r["family"] == family and r["method"] == method and r["repeat"] == repeat
                ]
                ax.plot(
                    [(r["round"] + 1) * result["plan"]["batch"] for r in rows],
                    [r["best"] for r in rows],
                    color=color,
                    marker="o",
                    alpha=0.8,
                    label=method if repeat == 0 else None,
                )
        ax.set(
            title=family.title(),
            xlabel="Candidate evaluations per repeat",
            ylabel="Best training angular-response proxy",
        )
        ax.legend()
        ax.grid(alpha=0.2)
    fig.suptitle("Feedback-guided mutation versus equal-budget global sampling")
    fig.savefig(output / "search-progress.png", dpi=180)
    plt.close(fig)
    nominal = next(v for v in result["validation"] if v["ratio"] == 1)
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    ax.barh(
        [c["name"] for c in result["finalists"]],
        nominal["score_mean"],
        xerr=nominal["seed_std"],
        color="#287e8b",
    )
    ax.invert_yaxis()
    ax.set(title="All frozen candidates: four fresh seeds", xlabel="Angular-response derivative")
    fig.savefig(output / "refinement-validation.png", dpi=180)
    plt.close(fig)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = json.loads((args.directory / "refinement-results.json").read_text())
    # Predetermined incumbent, not a visually selected or holdout-selected shape.
    trajectories(result["finalists"][0], args.directory)
    search_progress(result, args.directory)


if __name__ == "__main__":
    main()
