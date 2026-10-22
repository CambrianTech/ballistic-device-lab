"""Draw actual Kwant sites and hoppings, without solving transport."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle

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


def draw(ax, data: dict, title: str) -> None:
    xy = np.array(data["positions_nm"])
    ax.add_collection(
        LineCollection(xy[np.array(data["bonds"])], colors="#a8c4c8", linewidths=0.35)
    )
    ax.scatter(*xy.T, s=1.2, color="#087f8c", linewidths=0)
    for contact in data["contacts"]:
        ax.scatter(*xy[contact].T, s=4, color="#e3a039", linewidths=0)
    ax.set(xlim=(-8, 8), ylim=(-8, 8), title=title, aspect="equal")
    ax.set_axis_off()


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
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.6))
    draw(axes[0], parent, f"Frozen winner · {len(p):,} carbon sites")
    draw(axes[1], child, f"Best local offspring · {len(c):,} carbon sites")
    draw(axes[2], parent, "Atomic edge changes · magnified")
    for ax in axes[:2]:
        ax.add_patch(
            Rectangle(center - 1.3, 2.6, 2.6, fill=False, edgecolor="#b72f65", linewidth=1.4)
        )
        ax.plot([-6.6, -1.6], [-7.5, -7.5], color="#283747", lw=3)
        ax.text(-4.1, -7.1, "5 nm", ha="center", fontsize=10)
    ax = axes[2]
    for points, color, marker, label in [
        (added, "#3676d1", "o", "Added carbon"),
        (removed, "#cb345b", "x", "Removed carbon"),
    ]:
        if points:
            xy = np.array(points)
            ax.scatter(*xy.T, s=25, color=color, marker=marker, label=label, zorder=5)
    ax.set(xlim=(center[0] - 1.3, center[0] + 1.3), ylim=(center[1] - 1.3, center[1] + 1.3))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.14), frameon=False, fontsize=9)
    ax.text(0.5, -0.02, "Window width: 2.6 nm", transform=ax.transAxes, ha="center", fontsize=10)
    fig.suptitle(
        "Simulated graphene lattice · actual transport geometry", fontsize=17, weight="bold"
    )
    fig.text(
        0.5,
        0.02,
        f"White opening = etched void · gold = lead interface atoms · {len(added)} added / {len(removed)} removed sites in whole device\nIdeal unrelaxed lattice; not a microscope image. Bonds show Hamiltonian connectivity, not electron trajectories.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.10, 1, 0.93))
    fig.savefig(target / "atomic-lattice.png", dpi=220)
    plt.close(fig)
    (target / "atomic-lattice.json").write_text(
        json.dumps(dict(parent=parent, offspring=child, added=added, removed=removed), indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
