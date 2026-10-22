"""Automatically selected family representatives from a completed snapshot."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from ballistic_lab.reporting.dc_search import promoted


def render(snapshot: dict, control: dict, destination: Path) -> None:
    rows = [r for history in snapshot["histories"].values() for r in history]
    finalists = promoted(rows)
    best = finalists[0] if finalists else None
    selected = [control]
    for family in ("triangle", "beveled", "profile", "islands", "radial"):
        pool = [r for r in rows if r["candidate"]["family"] == family]
        selected.append(
            min(
                pool,
                key=lambda r: (
                    -r["levels"][0]["dc_power_w"],
                    -int(bool(r.get("energy_converged") and r.get("phase_converged"))),
                    r["candidate"]["key"],
                ),
            )
        )
    if best:
        for index, row in enumerate(selected[1:], start=1):
            if row["candidate"]["family"] == best["candidate"]["family"]:
                selected[index] = best
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for ax, row in zip(axes.flat, selected, strict=True):
        item = row["candidate"]
        passed = row.get("energy_converged") and row.get("phase_converged")
        metric = row["phase64"] if passed else row["levels"][0]
        label = "converged" if passed else "screening only"
        ax.add_patch(Rectangle((-1, -1), 2, 2, facecolor="white", edgecolor="#253a54"))
        for polygon in item["obstacles"]:
            ax.add_patch(Polygon(polygon, facecolor="#087f8c"))
        for x, y, dx, dy in (
            (-1, -0.3, 0, 0.6),
            (1, -0.3, 0, 0.6),
            (-0.3, -1, 0.6, 0),
            (-0.3, 1, 0.6, 0),
        ):
            ax.plot([x, x + dx], [y, y + dy], color="#e49b35", lw=4)
        title = "Frozen control D00" if item["key"] == "D00" else item["family"].capitalize()
        is_best = best is not None and item["key"] == best["candidate"]["key"]
        highlight = "#315fa3" if item["key"] == "D00" else "#087f8c" if is_best else None
        if is_best:
            title = f"Best converged search · {item['family']}"
        if highlight:
            ax.add_patch(Rectangle((-1, -1), 2, 2, fill=False, edgecolor=highlight, lw=3))
        ax.set_title(
            f"{title}\n{metric['dc_v'] * 1e6:+.3f} µV DC · {label}",
            fontsize=11,
            fontweight="bold" if highlight else "normal",
            color=highlight or "black",
        )
        ax.text(0, -1.18, item["key"], ha="center", fontsize=7)
        ax.set(xlim=(-1.1, 1.1), ylim=(-1.3, 1.1), aspect="equal")
        ax.axis("off")
    fig.suptitle(
        f"Continuously exploring geometry · completed round {snapshot['round']}", fontweight="bold"
    )
    fig.text(
        0.5,
        0.015,
        "Simulation · 14.76 nm · 10 mV peak · 10 kΩ · fixed internal potential",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.95))
    fig.savefig(destination / "diversity.png", dpi=180)
    plt.close(fig)
    (destination / "gallery-selection.json").write_text(
        json.dumps(
            dict(
                rule="Frozen D00 plus highest 257-grid DC power in each family across methods; ties prefer convergence then key. The best converged search candidate replaces its family representative. Display refined voltage only when both gates pass.",
                best_converged_search=best["candidate"]["key"] if best else None,
                candidates=[r["candidate"]["key"] for r in selected],
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
