"""Generate the README feature and complete ranking from declared DC gates."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

FOLDER = Path("results/2026-10-22-dc-search")


def promoted(rows):
    """No visual/editorial preference: require both gates, sort by DC power."""
    eligible = [r for r in rows if r.get("energy_converged") and r.get("phase_converged")]
    return sorted(eligible, key=lambda r: (-r["phase64"]["dc_power_w"], r["candidate"]["key"]))


def main():
    rows = json.loads((FOLDER / "summary.json").read_text(encoding="utf-8"))
    selection = json.loads((FOLDER / "selection.json").read_text(encoding="utf-8"))
    lookup = {r["candidate"]["key"]: r for r in rows}
    ranking = [lookup[key] for key in selection["ranking"]]
    eligible = promoted(rows)
    headline = (
        f"Best converged candidate in this pilot: **{eligible[0]['candidate']['key']}**."
        if eligible
        else "**No finalist passed both convergence gates; no winner promoted.**"
    )
    shown = [lookup[key] for key in selection["selected"]]
    fig, axes = plt.subplots(1, len(shown), figsize=(4 * len(shown), 4.4), squeeze=False)
    for ax, row in zip(axes[0], shown, strict=True):
        item = row["candidate"]
        ax.add_patch(Rectangle((-1, -1), 2, 2, facecolor="white", edgecolor="#253a54"))
        for poly in item["obstacles"]:
            ax.add_patch(Polygon(poly, facecolor="#087f8c"))
        for x, y, dx, dy in (
            (-1, -0.3, 0, 0.6),
            (1, -0.3, 0, 0.6),
            (-0.3, -1, 0.6, 0),
            (-0.3, 1, 0.6, 0),
        ):
            ax.plot([x, x + dx], [y, y + dy], color="#e49b35", lw=5)
        passed = row.get("energy_converged") and row.get("phase_converged")
        voltage = row["levels"][-1]["dc_v"] * 1e6
        ax.set_title(
            f"{item['key']}\n{voltage:+.3f} µV DC · {'passed' if passed else 'unresolved'}",
            fontsize=11,
        )
        ax.set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1), aspect="equal")
        ax.axis("off")
    fig.suptitle("Direct DC search · automatically selected finalists", fontweight="bold")
    fig.text(
        0.5,
        0.025,
        "Same 14.76 nm footprint · 10 mV peak drive · 10 kΩ · fixed-potential model",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.9))
    fig.savefig(FOLDER / "finalists.png", dpi=180)
    plt.close(fig)
    table = [
        "| Candidate | Origin | Screen DC (µV) | Refined DC (µV) | Status |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in ranking:
        item = row["candidate"]
        refined = len(row["levels"]) > 1
        status = ("Passed" if row in eligible else "Unresolved") if refined else "Screen only"
        value = f"{row['levels'][-1]['dc_v'] * 1e6:+.4f}" if refined else "—"
        table.append(
            f"| {item['key']} | {item['origin']} | {row['levels'][0]['dc_v'] * 1e6:+.4f} | {value} | {status} |"
        )
    report = (
        "# Direct DC search pilot\n\n"
        + headline
        + "\n\n![Automatically selected finalists](finalists.png)\n\n"
        + "\n".join(table)
        + """

## Predeclared method

One seeded pilot: eight global proposals across triangle, profile, islands and radial families; one DC-selected parent per family produces one bounded mutation. Three controls (plain triangle, archived D00 bevel, archived D14 islands) give **15 candidates total**. Controls are not parents. This is a small exploratory search, not evidence of a global optimum or superiority of a search algorithm.

Objective: maximize the DC component power into 10 kΩ, using 10 mV peak sinusoidal balanced drive, 0.9 eV Fermi energy, 300 K reservoir occupations, nominal atomic origin, 14.76 nm width and 0.3-width contacts. The plain triangle is an explicit synthetic control (normalized width 1, height 0.7, centered, no skew), not a reconstruction of a paper.

Every candidate is screened at 257 energies and 32 phases. The top two by DC power plus the fixed triangle receive 513/1025-energy refinement. A candidate is promoted only if both successive DC-voltage changes meet 1 nV + 1% and 32→64 phases meet that same tolerance. An automatic follow-up applies to every unresolved selected finalist: 2049, then at most 4097 energies, stopping when both gates pass. Its separate manifest preserves the initial results and records this extension before refinement. Screen-only candidates remain unvalidated. Promotion ranks only validated finalists; it does not establish an exhaustive ranking over unrefined candidates. No candidate is manually selected for the README.

The reported DC is from the frozen-potential reservoir-bias model. It excludes charge-induced potential changes, scattering, frequency response and fabrication disorder. The objective is DC power at fixed voltage/load, not maximum efficiency or matched input power. Further operating-point and geometric robustness tests are required before feeding these results into a larger search.

## Artifacts and reproduction

`manifest.json` freezes initial geometry, seeds, selection policy and source hashes before simulation. `feedback-proposals.json` records the DC-selected mutations; `selection.json` records the entire screening order and chosen finalists. `summary.json` contains refinement levels and phase gates. Per-candidate gzip files preserve full spectra and device fingerprints.

```powershell
# In the isolated Kwant environment, with single-thread BLAS and a fresh output directory:
python -m ballistic_lab.experiments.dc_search
python -m ballistic_lab.experiments.dc_refine
# After archiving runs/dc-search into this results directory:
python -m ballistic_lab.reporting.dc_search
```

Kwant calculations run on CPU, with two workers. This pilot does not use the GPU ray score to rank candidates.
"""
    )
    (FOLDER / "README.md").write_text(report, encoding="utf-8")
    root = Path("README.md")
    text = root.read_text(encoding="utf-8")
    start = (
        text.index("## A shape worth testing further")
        if "## A shape worth testing further" in text
        else text.index("## Direct DC search")
    )
    end = text.index("## Current findings", start)
    block = (
        "## Direct DC search\n\n"
        + headline
        + "\n\n![Automatically selected DC finalists](results/2026-10-22-dc-search/finalists.png)\n\nThe pipeline selects this result by DC load power and convergence gates. A triangle win, another shape winning, or no qualified winner are all valid outcomes. This 15-candidate pilot uses a fixed internal potential; self-consistent electrostatics remains open.\n\n[Full ranking, controls and selection rules](results/2026-10-22-dc-search/README.md) · [Earlier bevel/island DC test](results/2026-10-22-finite-bias/README.md)\n\n"
    )
    root.write_text(text[:start] + block + text[end:], encoding="utf-8")


if __name__ == "__main__":
    main()
