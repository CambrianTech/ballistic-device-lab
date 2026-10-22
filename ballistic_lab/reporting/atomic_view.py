"""Draw actual Kwant sites and hoppings, without solving transport."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy.ndimage import gaussian_filter

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system


def lattice(candidate: dict) -> dict:
    request = LatticeRequest((0.9,))
    system = build_system(SquareDevice(candidate["obstacles"], 60 * 0.246e-9), request)
    positions = np.array([s.pos for s in system.sites]) * request.lattice_constant_m * 1e9
    edges = [(i, j) for i in range(len(positions)) for j in system.graph.out_neighbors(i) if i < j]
    return dict(
        key=candidate["key"],
        positions_nm=positions.tolist(),
        bonds=edges,
        contacts=[list(map(int, x)) for x in system.lead_interfaces],
    )


def draw(ax, data: dict, title: str, bounds=(-8, 8, -8, 8)) -> None:
    """Gaussian position markers; deliberately not electron-optical contrast."""
    xy = np.array(data["positions_nm"])
    left, right, bottom, top = bounds
    pixels = 1000
    density, _, _ = np.histogram2d(
        xy[:, 1], xy[:, 0], bins=pixels, range=((bottom, top), (left, right))
    )
    sigma_nm = 0.032
    density = gaussian_filter(density, sigma_nm / ((right - left) / pixels))
    ax.imshow(
        density,
        origin="lower",
        extent=bounds,
        cmap="afmhot",
        vmin=0,
        vmax=density.max(),
        interpolation="nearest",
    )
    ax.set_title(title, loc="left", fontsize=13, pad=10)
    ax.set(xticks=[], yticks=[], aspect="equal")
    length = 5 if right - left > 5 else 0.5
    x, y = left + 0.08 * (right - left), bottom + 0.09 * (top - bottom)
    ax.plot([x, x + length], [y, y], color="white", lw=3)
    ax.text(
        x + length / 2,
        y + 0.035 * (top - bottom),
        f"{length:g} nm",
        color="white",
        ha="center",
        fontsize=11,
    )


def main(target: Path) -> None:
    rows = json.loads((target / "atomic-input.json").read_text())
    parent, child = [lattice(row) for row in rows]
    p = {tuple(np.round(x, 9)) for x in parent["positions_nm"]}
    c = {tuple(np.round(x, 9)) for x in child["positions_nm"]}
    added, removed = sorted(c - p), sorted(p - c)
    changed = np.array(added + removed)
    center = changed[0] if len(changed) else np.array([0.0, 0.0])
    if len(changed):
        counts = [np.sum(np.max(abs(changed - x), axis=1) < 1.3) for x in changed]
        center = changed[int(np.argmax(counts))]
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    draw(axes[0, 0], parent, f"a  Winner  /  {len(p):,} carbon sites")
    draw(axes[0, 1], child, f"b  Local offspring  /  {len(c):,} carbon sites")
    bounds = (center[0] - 1.3, center[0] + 1.3, center[1] - 1.3, center[1] + 1.3)
    draw(axes[1, 0], parent, "c  Winner edge  /  enlarged", bounds)
    draw(axes[1, 1], child, "d  Offspring edge  /  enlarged", bounds)
    for ax, data in zip(axes[0], (parent, child)):
        ax.add_patch(
            Rectangle(center - 1.3, 2.6, 2.6, fill=False, edgecolor="#ffbc47", linewidth=1.5)
        )
        xy = np.array(data["positions_nm"])
        for contact in data["contacts"]:
            ax.scatter(*xy[contact].T, s=2, color="#ffbc47", linewidths=0)
        ax.set(xlim=(-8, 8), ylim=(-8, 8))
    fig.suptitle("Graphene device and atomic edge detail", fontsize=18, weight="bold")
    fig.text(
        0.5,
        0.025,
        f"Bright spots: carbon positions  /  black opening: etched void  /  gold: contacts and zoom window\n"
        f"Offspring: {len(added)} sites added, {len(removed)} removed across the device.\n"
        "Position rendering (Gaussian width 0.032 nm); not simulated microscope contrast.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.10, 1, 0.95), h_pad=2, w_pad=2)
    fig.savefig(target / "atomic-lattice.png", dpi=200)
    plt.close(fig)
    (target / "atomic-lattice.json").write_text(
        json.dumps(dict(parent=parent, offspring=child, added=added, removed=removed), indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
