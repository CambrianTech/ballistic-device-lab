"""README comparison from frozen geometry and converged nominal load results."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle


def main():
    catalog_path = Path("results/2026-10-22-discovery/designs.json")
    catalog = {r["id"]: r for r in json.loads(catalog_path.read_text(encoding="utf-8"))}
    sources = {
        "D00": Path("results/2026-10-22-convergence/summary.json"),
        "D14": Path("results/2026-10-22-coverage/summary.json"),
    }
    records = {}
    for candidate, path in sources.items():
        record = next(
            r
            for r in json.loads(path.read_text(encoding="utf-8"))
            if r["case"]["key"] == f"{candidate}-nominal"
        )
        loads = []
        for i, row in enumerate(record["levels"][-1]["loads"]):
            if row["load_ohm"] == 1e4:
                if not record["observable_converged"][i]:
                    raise ValueError("Do not promote an unconverged comparison")
                loads.append(
                    dict(fermi_ev=row["fermi_ev"], output_uv=row["output_voltage_v"] * 1e6)
                )
        records[candidate] = dict(loads=loads, grid_count=record["levels"][-1]["count"])

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.7))
    fig.patch.set_facecolor("#f5f7fb")
    half = 14.76 / 2
    titles = ("D00 · Our bevel reference", "D14 · Search-discovered split islands")
    for ax, candidate, title, color in zip(
        axes, sources, titles, ("#516580", "#087f8c"), strict=True
    ):
        ax.set_aspect("equal")
        ax.add_patch(
            Rectangle(
                (-half, -half), 2 * half, 2 * half, facecolor="white", edgecolor="#17283d", lw=2
            )
        )
        for poly in catalog[candidate]["excluded_polygons"]:
            ax.add_patch(Polygon(np.array(poly) * half, facecolor=color, edgecolor=color))
        contact = 0.3 * half
        for x, y, dx, dy in (
            (-half, -contact, 0, 2 * contact),
            (half, -contact, 0, 2 * contact),
            (-contact, -half, 2 * contact, 0),
            (-contact, half, 2 * contact, 0),
        ):
            ax.plot([x, x + dx], [y, y + dy], color="#e49b35", lw=6, solid_capstyle="butt")
        ax.text(-half - 0.4, 0, "L", ha="right", va="center", color="#17283d")
        ax.text(half + 0.4, 0, "R", ha="left", va="center", color="#17283d")
        ax.text(0, half + 0.5, "T", ha="center", color="#17283d")
        ax.text(0, -half - 1.0, "B", ha="center", color="#17283d")
        ax.annotate(
            "",
            xy=(half, -half - 1.8),
            xytext=(-half, -half - 1.8),
            arrowprops=dict(arrowstyle="|-|", color="#516580"),
        )
        ax.text(0, -half - 2.4, "14.76 nm", ha="center", color="#516580", fontsize=10)
        ax.set_xlim(-half - 2, half + 2)
        ax.set_ylim(-half - 2.8, half + 1.5)
        ax.set_title(title, fontsize=13, fontweight="bold", color=color, pad=14)
        ax.axis("off")
    fig.suptitle(
        "Different geometry. Stronger transverse signal.",
        fontsize=19,
        fontweight="bold",
        color="#17283d",
        y=0.98,
    )
    fig.text(
        0.5,
        0.035,
        "Same footprint and contacts · shaded regions are etched obstacles\n"
        "Frozen simulated designs; nominal outlines shown, not individual carbon atoms",
        ha="center",
        fontsize=10,
        color="#516580",
    )
    fig.subplots_adjust(top=0.84, bottom=0.13, wspace=0.25)
    fig.savefig("designs/quantum-comparison.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    payload = dict(
        records=records,
        conditions=dict(
            width_nm=14.76,
            contact_fraction=0.3,
            drive_mv=1,
            load_kohm=10,
            reservoir_temperature_k=300,
            lattice_offset=[0, 0],
        ),
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in {catalog_path, *sources.values()}
        },
    )
    Path("designs/quantum-comparison.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
