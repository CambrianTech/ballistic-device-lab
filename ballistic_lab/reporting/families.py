"""Scientific figures from saved results; no transport or selection occurs here."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from ballistic_lab.geometry.families import geometry


def plot_results(result: dict, output: Path) -> None:
    validation = result["validation"]
    finalists = result["finalists"]
    polys = [geometry(f["family"], f["x"]) for f in finalists]
    nominal = next(v for v in validation if v["ratio"] == 1 and v["specularity"] == 0.8)
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    ax.barh([f["name"] for f in finalists], nominal["score_mean"], xerr=nominal["seed_std"])
    ax.set_xlabel("Angular response derivative per beta (not per volt)")
    ax.set_title("Fresh-seed validation: mean free path / width = 1; specularity = 0.8")
    ax.invert_yaxis()
    fig.savefig(output / "families-comparison.png", dpi=170)
    plt.close(fig)
    # Show all frozen finalists, not a post-holdout cherry-picked subset.
    fig, axes = plt.subplots(3, 4, figsize=(12, 9), layout="constrained")
    for ax, f, p in zip(axes.flat, finalists, polys):
        ax.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), aspect="equal", title=f["name"])
        for shape in p:
            ax.add_patch(Polygon(shape, color="slategray"))
        ax.plot([-1, 1, 1, -1, -1], [-1, -1, 1, 1, -1], color="black", lw=0.7)
        for a, b in [
            ([-0.3, 0.3], [-1, -1]),
            ([-0.3, 0.3], [1, 1]),
            ([-1, -1], [-0.3, 0.3]),
            ([1, 1], [-0.3, 0.3]),
        ]:
            ax.plot(a, b, color="darkorange", lw=4)
        ax.set_xticks([])
        ax.set_yticks([])
    for ax in list(axes.flat)[len(finalists) :]:
        ax.axis("off")
    fig.savefig(output / "families-geometries.png", dpi=170)
    plt.close(fig)
