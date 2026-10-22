"""Render only completed validation cases; incomplete conditions remain visible."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle

from ballistic_lab.reporting.robustness import render as render_robustness
from followup_lab.plan import identity, leader


def render(snapshot, destination):
    root = Path("runs/leader-validation")
    candidate = leader(snapshot)
    if candidate is None:
        return "No converged leader is ready for broader validation."
    baseline = json.loads(Path("results/2026-10-22-dc-wide/summary.json").read_text())
    items = [
        r["candidate"] for r in baseline if r["candidate"]["key"] in ("D00", "triangle-control")
    ]
    items.append(candidate)
    labels = [c["key"] for c in items]
    data = []
    archived = destination / "validation"
    archived.mkdir(exist_ok=True)
    if (root / "source.json").exists():
        (archived / "source.json").write_bytes((root / "source.json").read_bytes())
    for item in items:
        records = {}
        for name in ("nominal", "wide-contact", "atomic-offset", "rays"):
            path = root / identity(item) / f"{name}.json"
            if path.exists():
                records[name] = json.loads(path.read_text())
                (archived / f"{identity(item)}-{name}.json").write_bytes(path.read_bytes())
        data.append(records)
    table = [
        "| Design | Completed contact/edge conditions | Converged DC cases | Ray scattering cases |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, records in zip(labels, data, strict=True):
        cases = [r for k, value in records.items() if k != "rays" for r in value["results"]]
        passed = sum(r["energy_converged"] and r["phase_converged"] for r in cases)
        table.append(
            f"| {label} | {len([k for k in records if k != 'rays'])}/3 | {passed}/{len(cases)} | {len(records.get('rays', {}).get('records', []))}/27 |"
        )
    control_data = data[labels.index("D00")]
    matched, higher = 0, 0
    for condition in ("nominal", "wide-contact", "atomic-offset"):
        controls = {
            (r["fermi_ev"], r["load_ohm"]): r
            for r in control_data.get(condition, {}).get("results", [])
        }
        for result in data[-1].get(condition, {}).get("results", []):
            reference = controls.get((result["fermi_ev"], result["load_ohm"]))
            if reference and all(
                r["energy_converged"] and r["phase_converged"] for r in (result, reference)
            ):
                matched += 1
                higher += result["dc_power_w"] > reference["dc_power_w"]
    comparison = (
        f"**Leader versus D00:** higher computed DC power in **{higher}/{matched}** "
        f"matched, numerically converged cases so far, out of 27 planned conditions. "
        "This counts the computed ordering, not statistical significance or physical validation."
    )
    # One fixed, identical illustrative injection for each geometry; no selected pretty rays.
    fig, axes = plt.subplots(1, len(items), figsize=(12, 4.5), layout="constrained")
    for ax, item, records in zip(axes, items, data, strict=True):
        ax.add_patch(
            Rectangle(
                (-1, -1),
                2,
                2,
                facecolor="#eef7f7" if item == candidate else "#eef3fa",
                edgecolor="#253a54",
            )
        )
        for poly in item["obstacles"]:
            ax.add_patch(Polygon(poly, color="#087f8c"))
        for x, y, dx, dy in (
            (-1, -0.3, 0, 0.6),
            (1, -0.3, 0, 0.6),
            (-0.3, -1, 0.6, 0),
            (-0.3, 1, 0.6, 0),
        ):
            ax.plot([x, x + dx], [y, y + dy], color="#e49b35", lw=4, zorder=5)
        rays = records.get("rays", {}).get("records", [])
        selected = next(
            (r for r in rays if r["specularity"] == 0.8 and r["mfp"] == 2 and r["seed"] == 61001),
            None,
        )
        if selected:
            for port, color in zip(selected["ports"], ("#d88224", "#7454a3"), strict=True):
                for path in port["paths"].values():
                    points = np.array(path)
                    ax.plot(points[:, 0], points[:, 1], color=color, alpha=0.45, lw=0.7)
        else:
            ax.text(0, -0.85, "Trajectories pending", ha="center")
        ax.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), aspect="equal")
        ax.set_title("Current leader" if item == candidate else item["key"])
        ax.axis("off")
    fig.suptitle(
        "Matched trajectories · synthetic controls and current leader\n16 paths per input · same seeds · specularity 0.8 · mean free path = device width"
    )
    fig.savefig(destination / "leader-trajectories.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
    for ax, name in zip(axes, ("nominal", "wide-contact", "atomic-offset"), strict=True):
        for label, records in zip(labels, data, strict=True):
            rows = records.get(name, {}).get("results", [])
            rows = [r for r in rows if r["load_ohm"] == 1e4]
            if rows:
                ax.plot(
                    [r["fermi_ev"] for r in rows],
                    [abs(r["dc_v"]) * 1e6 for r in rows],
                    label=label,
                    marker="o",
                )
                for r in rows:
                    if not (r["energy_converged"] and r["phase_converged"]):
                        ax.plot(r["fermi_ev"], abs(r["dc_v"]) * 1e6, "rx", ms=10)
        ax.set(title=name, xlabel="Fermi energy (eV)", ylabel="DC magnitude (µV), 10 kΩ")
        if ax.lines:
            ax.legend(fontsize=6)
        else:
            ax.text(0.5, 0.5, "Pending", transform=ax.transAxes, ha="center")
        ax.grid(alpha=0.2)
    fig.suptitle("Leader validation · fixed potential · red × = unresolved convergence")
    fig.savefig(destination / "leader-coverage.png", dpi=170)
    plt.close(fig)
    exported = []
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), layout="constrained")
    for ax, name in zip(axes, ("nominal", "wide-contact", "atomic-offset"), strict=True):
        matrix = np.full((len(items), 9), np.nan)
        for index, (label, records) in enumerate(zip(labels, data, strict=True)):
            for column, row in enumerate(records.get(name, {}).get("results", [])):
                passed = row["energy_converged"] and row["phase_converged"]
                matrix[index, column] = abs(row["dc_v"]) * 1e6
                exported.append(dict(design=label, condition=name, **row))
                ax.text(
                    column,
                    index,
                    f"{matrix[index, column]:.2f}" + ("" if passed else " ×"),
                    ha="center",
                    va="center",
                    fontsize=8,
                )
        cmap = plt.get_cmap("YlGnBu").copy()
        cmap.set_bad("#eeeeee")
        # Pale backgrounds keep numerical labels readable; color is within-panel only.
        finite = matrix[np.isfinite(matrix)]
        ax.imshow(
            matrix,
            cmap=cmap,
            aspect="auto",
            vmin=0,
            vmax=max(float(finite.max()) * 2, 1) if finite.size else 1,
        )
        for row, column in zip(*np.where(np.isnan(matrix)), strict=True):
            ax.text(column, row, "pending", ha="center", va="center", fontsize=7, color="#666666")
        ax.set(
            title=name,
            yticks=range(len(items)),
            yticklabels=["Triangle", "D00", "Leader"],
            xticks=range(9),
            xticklabels=[f"{f:g} eV / {load}k" for f in (0.75, 0.9, 1.05) for load in (1, 10, 100)],
        )
    fig.suptitle(
        "Full DC validation matrix · magnitude in µV\n× = unresolved convergence; grey = pending; 10 mV peak, fixed potential"
    )
    fig.savefig(destination / "leader-matrix.png", dpi=170)
    plt.close(fig)
    if exported:
        with (archived / "matrix.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(exported[0]))
            writer.writeheader()
            writer.writerows(exported)
    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    conditions = [(s, m) for s in (0.5, 0.8, 1.0) for m in (1.0, 2.0, 4.0)]
    for label, records in zip(labels, data, strict=True):
        rays = records.get("rays", {}).get("records", [])
        if not rays:
            continue
        means, deviations = [], []
        for specularity, mfp in conditions:
            values = [
                sum(p["probabilities"][3] - p["probabilities"][2] for p in r["ports"]) / 2
                for r in rays
                if r["specularity"] == specularity and r["mfp"] == mfp
            ]
            means.append(np.mean(values))
            deviations.append(np.std(values, ddof=1))
        ax.errorbar(range(9), means, yerr=deviations, marker="o", capsize=3, label=label)
    ax.set(
        xticks=range(9),
        xticklabels=[f"{s:g} / {m / 2:g}" for s, m in conditions],
        xlabel="Specularity / mean free path divided by width",
        ylabel="Mean bottom-minus-top exit probability",
        title="Classical scattering diagnostic · equal L/R injection\nThree fresh seeds; error bars = seed standard deviation, not DC uncertainty",
    )
    if ax.lines:
        ax.legend(fontsize=7)
    ax.grid(alpha=0.2)
    fig.savefig(destination / "leader-scattering.png", dpi=170)
    plt.close(fig)
    rel = destination.as_posix()
    return f"""### Current leader: broader checks

Each new converged leader enters a separate one-CPU validation queue with D00 and the synthetic triangle. Identical geometries are tested once. Search continues independently; these checks do not change its objective. Pending and unresolved results stay visible.

{chr(10).join(table)}

{comparison}

{render_robustness(destination)}

![Matched control and leader trajectories]({rel}/leader-trajectories.png)

Orange paths enter from the left; purple paths enter from the right; gold segments are contacts. Trajectory paths are a classical diagnostic, not a quantum current map or DC-efficiency measurement. Neither control is a reproduced paper device.

![Updating classical scattering comparison]({rel}/leader-scattering.png)

![Updating leader energy and contact checks]({rel}/leader-coverage.png)

<details>
<summary>All 27 DC conditions per design: loads, energies and contact cuts</summary>

![Full current validation matrix]({rel}/leader-matrix.png)

</details>

Full matrix: three Fermi energies × three loads × three contact/atomic-cut conditions, with energy and phase refinement. Ray checks cover three specularities × three mean free paths × three seeds. [Completed case data]({rel}/validation) retains all loads, raw seed results and convergence flags. Phonons, self-consistent electrostatics and finite-frequency response remain unimplemented.

"""
