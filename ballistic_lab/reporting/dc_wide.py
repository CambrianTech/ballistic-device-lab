"""Data-selected wider-search findings, finalist gallery and full ranking."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from ballistic_lab.reporting.dc_search import promoted

FOLDER = Path("results/2026-10-22-dc-wide")


def main(folder: Path = FOLDER):
    rows = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    selection = json.loads((folder / "selection.json").read_text(encoding="utf-8"))
    lookup = {r["candidate"]["key"]: r for r in rows}
    eligible = promoted(rows)
    new = [r for r in rows if "repeat" in r["candidate"]]
    n_families = len({r["candidate"]["family"] for r in new})
    n_seeds = len({r["candidate"]["repeat"] for r in new})
    mutations = [r for r in new if r["candidate"]["origin"].startswith("mutation of ")]
    improvements = sum(
        r["levels"][0]["dc_power_w"]
        > lookup[r["candidate"]["origin"].removeprefix("mutation of ")]["levels"][0]["dc_power_w"]
        for r in mutations
    )
    feedback = (
        f"**Feedback check:** {improvements}/{len(mutations)} mutations improved their parent "
        "on the shared screening grid. Parents are selected by descending DC power, "
        "independent of voltage polarity. This run does not establish an advantage over "
        "equal-budget random search."
    )
    headline = (
        f"Best converged candidate: **{eligible[0]['candidate']['key']}**."
        if eligible
        else "**No candidate passed both convergence gates.**"
    )
    fresh = [r for r in eligible if "repeat" in r["candidate"]]
    if fresh and lookup["D00"] in eligible:
        best = fresh[0]
        voltage = abs(best["phase64"]["dc_v"])
        reference = abs(lookup["D00"]["phase64"]["dc_v"])
        headline += (
            f" Best new design: **{best['candidate']['key']}**, "
            f"{voltage * 1e6:.3f} µV versus D00’s {reference * 1e6:.3f} µV "
            f"({voltage / reference:.1%} of its DC voltage)."
        )
    selected = [lookup[key] for key in selection["selected"]]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for ax, row in zip(axes.flat, selected, strict=True):
        item = row["candidate"]
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
        passed = row.get("energy_converged") and row.get("phase_converged")
        ax.set_title(
            f"{item['key']}\n{row['levels'][-1]['dc_v'] * 1e6:+.3f} µV DC · {'passed' if passed else 'unresolved'}",
            fontsize=10,
        )
        ax.set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1), aspect="equal")
        ax.axis("off")
    fig.suptitle("Wider direct-DC search · automatic finalists", fontweight="bold")
    fig.text(
        0.5,
        0.015,
        "14.76 nm · 10 mV peak · 10 kΩ · 300 K occupations · fixed internal potential",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.96))
    fig.savefig(folder / "finalists.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), sharey=True)
    colors = {
        "triangle": "#3274a1",
        "beveled": "#e1812c",
        "profile": "#3a923a",
        "islands": "#c03d3e",
        "radial": "#9372b2",
    }
    for repeat, ax in enumerate(axes):
        for family, color in colors.items():
            subset = [
                r
                for r in rows
                if r["candidate"].get("repeat") == repeat and r["candidate"]["family"] == family
            ]
            # Fixed display offsets keep overlapping candidates visible; no randomness in rendering.
            for round_index in (0, 1, 2):
                points = [r for r in subset if r["candidate"]["round"] == round_index]
                for index, row in enumerate(points):
                    offset = (index - (len(points) - 1) / 2) * 0.025 + (
                        list(colors).index(family) - 2
                    ) * 0.12
                    ax.scatter(
                        round_index + offset,
                        abs(row["levels"][0]["dc_v"]) * 1e6,
                        color=color,
                        label=family if round_index == 0 and index == 0 else None,
                        s=32,
                    )
        ax.axhline(
            abs(lookup["D00"]["levels"][0]["dc_v"]) * 1e6,
            color="#253a54",
            linestyle="--",
            label="D00 control",
        )
        ax.set(
            title=f"Independent seed {repeat + 1}",
            xlabel="Proposal round",
            xticks=[0, 1, 2],
            yscale="log",
        )
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Screening DC magnitude (µV)")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=8, loc="lower center", ncol=6)
    fig.suptitle("Every proposal, including unsuccessful designs")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(folder / "search-coverage.png", dpi=180)
    plt.close(fig)
    table = [
        "| Candidate | Family | Screen DC (µV) | Refined DC (µV) | DC power (pW)* | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for key in selection["ranking"]:
        row = lookup[key]
        refined = key in selection["selected"]
        status = ("Passed" if row in eligible else "Unresolved") if refined else "Screen only"
        value = f"{row['levels'][-1]['dc_v'] * 1e6:+.4f}" if refined else "—"
        power = f"{row['phase64']['dc_power_w'] * 1e12:.5f}" if row in eligible else "—"
        table.append(
            f"| {key} | {row['candidate']['family']} | {row['levels'][0]['dc_v'] * 1e6:+.4f} | {value} | {power} | {status} |"
        )
    report = (
        "# Wider direct-DC search\n\n"
        + headline
        + "\n\n"
        + feedback
        + "\n\n![Automatic finalists](finalists.png)\n\n![All search proposals](search-coverage.png)\n\n"
        + "\n".join(table)
        + """

\\* DC component power = mean(Vout)² / 10 kΩ. Signed output is B minus T; ranking is polarity-independent. Fixed 10 mV peak voltage does not imply equal input power. This is not a maximum-efficiency objective.

## Search and validation

**80 new designs plus three controls.** Two independently seeded runs each begin with four Latin-hypercube proposals in each of five families (triangle, bevel, profile, islands, radial). Each of two subsequent rounds adds one fresh global proposal and one mutation per family. Mutation parents come from the top two prior candidates in that same family and repeat; controls are excluded. Thus global exploration persists throughout. This is a bounded exploratory comparison, not a global optimum or an equal-budget proof that mutations outperform random search.

The pilot did not search the bevel family. This run includes it explicitly. D00, D14 and the plain synthetic triangle remain frozen controls; none is labeled as a reproduced published device. No candidate was chosen for its appearance.

All scores use the same nominal 14.76 nm width, 0.3-width contacts, 0.9 eV Fermi level, 300 K occupations, 10 mV peak balanced sinusoidal drive, and 10 kΩ output load. Screening uses 257 energies and 32 phases. The top two new candidates per repeat, plus D00 and the fixed triangle, receive automatic 513/1025/2049/4097 refinement, stopping when the last two changes each satisfy 1 nV + 1% of the finer DC magnitude. A separate 32/64 phase check must also pass. All unresolved and screen-only results remain visible. Selection is based on a coarse grid and may miss candidates that need denser integration.

The generator uses these gates to select the README result. “Best converged” refers to validated finalists in this run, not all possible shapes or operating conditions. New candidates need independent operating-point, edge, and size robustness tests before promotion to a device-performance claim.

## Scoring audit

The preceding [independent audit](../2026-10-22-dc-audit/README.md) uses reciprocal pair currents, Gaussian integration of piecewise-linear transmission, and a least-squares load solver instead of the production matrix/trapezoid/root implementation. It agrees with the three pilot finalists within 0.13 nV. A fresh anonymous rebuild of D00 reproduces the cached screening score; closed-form energy-linear transmission and ranking/mean-square checks pass. These checks test software within the frozen-potential model, not self-consistent electrostatics.

## Reproduction and artifacts

`manifest.json` records the plan, controls, source hashes and audit hash. `proposals-*.json` freezes every batch before evaluation; `selection.json` records the screening order and automatic shortlist. Full per-candidate spectra are archived as gzip JSON. The report is generated from these records.

```powershell
# Single-thread BLAS, isolated Kwant environment; four CPU workers:
python -m ballistic_lab.experiments.dc_audit
python -m ballistic_lab.experiments.dc_wide
# Archive a completed run and regenerate its charts, ranking and README:
python -m ballistic_lab.pipeline.dc_publish
# Or run the entire fresh workflow with a timestamped archive:
python -m ballistic_lab.pipeline.dc_workflow
```

Use fresh output directories. This run uses CPU quantum transport, not GPU trajectory scoring. Charge-induced potential response, phonons, finite-frequency dynamics, and fabrication disorder remain outside the model.
"""
    )
    (folder / "README.md").write_text(report, encoding="utf-8")
    root = Path("README.md")
    text = root.read_text(encoding="utf-8")
    start = text.index("## Direct DC search")
    end = text.index("## Current findings", start)
    block = (
        "## Direct DC search\n\n"
        + headline
        + "\n\n![Automatically selected wider-search finalists](results/2026-10-22-dc-wide/finalists.png)\n\n**80 new designs, five families, two seeds.** DC power and convergence gates select the displayed result automatically. The full ranking includes every unsuccessful and unresolved candidate. These remain fixed-potential simulations.\n\n[Full ranking and search coverage](results/2026-10-22-dc-wide/README.md) · [Independent scoring audit](results/2026-10-22-dc-audit/README.md) · [Earlier pilot](results/2026-10-22-dc-search/README.md)\n\n"
    )
    block = block.replace("results/2026-10-22-dc-wide", folder.as_posix())
    block = block.replace(
        "80 new designs, five families, two seeds",
        f"{len(new)} new designs, {n_families} families, {n_seeds} seeds",
    )
    root.write_text(text[:start] + block + text[end:], encoding="utf-8")


if __name__ == "__main__":
    main()
