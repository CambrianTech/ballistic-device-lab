"""Publish immutable completed rounds; never read a partial worker state."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.ticker import MaxNLocator

from ballistic_lab.reporting.dc_search import promoted
from ballistic_lab.reporting.device_role import render as render_role
from ballistic_lab.reporting.diversity_gallery import render as render_gallery
from ballistic_lab.reporting.edge_sensitivity import render as render_edges
from ballistic_lab.reporting.falsification import render as render_falsification
from ballistic_lab.reporting.leader_evidence import render as render_evidence
from ballistic_lab.reporting.leader_validation import render as render_validation

ARMS = ("elite", "diversity", "random")
LABELS = {
    "elite": "Top-score selection",
    "diversity": "Diversity archive",
    "random": "Random search",
}


def winners(snapshot: dict) -> dict:
    return {
        arm: (promoted(rows)[0] if promoted(rows) else None)
        for arm, rows in snapshot["histories"].items()
    }


def main(source: Path = Path("runs/dc-continuous")) -> None:
    paths = sorted(source.glob("round-*.json"))
    if not paths:
        raise ValueError("No completed matched round to publish")
    snapshots = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    snapshot = snapshots[-1]
    index = snapshot["round"]
    published = datetime.now(timezone.utc)
    destination = Path("results/continuous-dc") / f"round-{index:06d}"
    destination.mkdir(parents=True, exist_ok=True)
    # Frozen receipts: conflicting contents are rejected, not overwritten.
    artifacts = paths + [source / "source.json"] + sorted(source.glob("*-proposals.json"))
    artifacts = [
        p
        for p in artifacts
        if not p.name.endswith("-proposals.json") or int(p.name.split("-")[0]) <= index
    ]
    for path in artifacts:
        target = destination / path.name
        if target.exists() and target.read_bytes() != path.read_bytes():
            raise ValueError(f"Archive conflict: {target}")
        shutil.copyfile(path, target)
    baseline = json.loads(
        Path("results/2026-10-22-dc-wide/summary.json").read_text(encoding="utf-8")
    )
    control = next(r for r in baseline if r["candidate"]["key"] == "D00")
    best = winners(snapshot)
    leader = max((row for row in best.values() if row), key=lambda r: r["phase64"]["dc_power_w"])
    evidence_block = render_evidence([control, leader], destination)
    render_gallery(snapshot, control, destination)
    validation_block = render_role([control, leader], destination)
    broader_checks = render_validation(snapshot, destination)
    summary = re.search(r"\*\*Leader versus D00:\*\*[^\n]+", broader_checks)
    if summary:
        validation_block += "\n\n" + summary.group(0) + "\n\n"
    validation_block += "<details>\n<summary>Validation dashboard: robustness, trajectories, edge damage and numerical checks</summary>\n\n"
    validation_block += broader_checks
    validation_block += render_falsification(
        [control, leader] + [r for r in baseline if r["candidate"]["key"] == "triangle-control"],
        destination,
    )
    validation_block += render_edges(destination)
    panels = [("Frozen control D00", control)] + [(LABELS[a], best[a]) for a in ARMS]
    fig, axes = plt.subplots(1, 4, figsize=(13, 4))
    for ax, (label, row) in zip(axes, panels, strict=True):
        ax.add_patch(Rectangle((-1, -1), 2, 2, facecolor="white", edgecolor="#253a54"))
        if row:
            for polygon in row["candidate"]["obstacles"]:
                ax.add_patch(Polygon(polygon, facecolor="#087f8c"))
            title = f"{label}\n{abs(row['phase64']['dc_v']) * 1e6:.3f} µV DC"
            ax.text(0, -1.2, row["candidate"]["key"], ha="center", fontsize=7)
        else:
            title = f"{label}\nNo converged finalist"
        for x, y, dx, dy in (
            (-1, -0.3, 0, 0.6),
            (1, -0.3, 0, 0.6),
            (-0.3, -1, 0.6, 0),
            (-0.3, 1, 0.6, 0),
        ):
            ax.plot([x, x + dx], [y, y + dy], color="#e49b35", lw=4)
        ax.set_title(title, fontsize=11)
        ax.set(xlim=(-1.15, 1.15), ylim=(-1.35, 1.15), aspect="equal")
        ax.axis("off")
    fig.suptitle(f"Graphene rectifier search · completed round {index}", fontweight="bold")
    fig.text(
        0.5,
        0.025,
        "Simulation · 14.76 nm · 10 mV peak · 10 kΩ · fixed internal potential",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    fig.savefig(destination / "comparison.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    for arm in ARMS:
        values = [winners(s)[arm] for s in snapshots]
        ax.plot(
            [s["round"] for s in snapshots],
            [abs(r["phase64"]["dc_v"]) * 1e6 if r else float("nan") for r in values],
            marker="o",
            label=LABELS[arm],
        )
    ax.axhline(
        abs(control["phase64"]["dc_v"]) * 1e6,
        linestyle="--",
        color="#253a54",
        label="Frozen control D00",
    )
    ax.set(
        xlabel="Completed matched round",
        ylabel="Best converged DC magnitude (µV)",
    )
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8, integer=True))
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(destination / "progress.png", dpi=180)
    plt.close(fig)
    table = [
        "| Method | Best converged design | DC magnitude (µV) | DC power (pW) |",
        "| --- | --- | ---: | ---: |",
    ]
    for label, row in panels:
        if row:
            table.append(
                f"| {label} | {row['candidate']['key']} | {abs(row['phase64']['dc_v']) * 1e6:.3f} | {row['phase64']['dc_power_w'] * 1e12:.5f} |"
            )
        else:
            table.append(f"| {label} | None | — | — |")
    counts = {arm: len(snapshot["histories"][arm]) for arm in ARMS}
    report = f"""# Continuous DC search — completed round {index}

![Control and automatically selected winners](comparison.png)

{chr(10).join(table)}

![Converged progress](progress.png)

Each method starts from the same 40 archived candidates and receives 20 new proposals per round: **{counts["elite"]} candidate evaluations per method** through this snapshot. The initial population is shared, and some proposals match across methods; counts are not counts of unique geometries. Controls do not become parents. Two seed streams contribute to each method, but finalists are selected across both, so this is not yet a per-seed statistical comparison.

Each round refines the two strongest screening candidates per method, retaining previous results. Both energy-grid and phase checks must pass for this table. The grids are 257/513/1025, extended to 2049/4097 as needed; the last two DC changes must each satisfy 1 nV + 1% of the finer magnitude. Phase averaging compares 32 and 64 samples with the same tolerance. Equal proposal and finalist-count budgets do not imply equal CPU time or quantum-solver work. Near ties do not establish a superior method.

## What the feedback does

Top-score selection chooses mutation parents from the best two in each family and seed stream. Diversity selection keeps the best screening performer in each geometry neighborhood and samples those neighborhoods uniformly. Its descriptors are blocked area and top/bottom reflection mismatch on a 96×96 raster, with ten bins per axis. Random search replaces the mutation slot with a fresh random candidate. All three retain matched fresh global proposals. Five geometry families are available; this cannot discover arbitrary topologies outside those parameterizations.

All historical candidates remain in the checkpoint. Diversity preserves eligibility to reproduce; it is not a literature novelty detector. The global winner remains performance-ranked after convergence checks. These methods do not train a neural model or learn missing physics. The archive descriptors and search benefits still need sensitivity and repeat testing.

## Physics and evidence

Four-terminal coherent graphene transport at 0.9 eV Fermi level and 300 K reservoir occupations, with balanced 10 mV peak sinusoidal input and a 10 kΩ output load. DC power is mean(Vout)²/R, excluding ripple heating. The device internal potential is fixed. Charge response, phonons, disorder, noise and frequency limits are not included. D00 is our synthetic bevel control, not a reproduced experimental paper device.

`round-*.json` contains complete per-method histories, candidate polygons, screening/refinement metrics and convergence flags. `*-proposals.json` records frozen proposal batches. `source.json` records the running implementation hashes. Full spectra remain checkpointed locally in `runs/dc-continuous/spectra`; these report snapshots archive metrics and geometry rather than duplicating all spectra on each round. Historical controls and their spectra are in [the wider search archive](../../2026-10-22-dc-wide/README.md).

Regenerate with `python -m ballistic_lab.reporting.dc_continuous`. The reporter reads only completed matched rounds and leaves live worker state untouched.
"""
    (destination / "README.md").write_text(report, encoding="utf-8")
    root = Path("README.md")
    text = root.read_text(encoding="utf-8")
    start, end = text.index("## Direct DC search"), text.index("## Current findings")
    rel = destination.as_posix()
    block = f"""## Direct DC search

**Continuous search: {index} completed matched rounds.** Three methods explore the same five geometry families: top-score selection, a diversity archive, and random search. Each has evaluated {counts["elite"]} candidates, including the same 40 starting designs.*

![Automatically selected representatives from every shape family]({rel}/diversity.png)

**An evolving experiment:** the worker continuously proposes, solves and refines geometries. This gallery regenerates from completed rounds, showing the control plus a leading candidate in each family. Blue highlights the frozen control; teal highlights the best converged search candidate, which always occupies its family's panel. Other families show their strongest screening result. Labels distinguish converged results from screening-only estimates; the table below includes converged method winners only.

Last published: **{published:%Y-%m-%d %H:%M UTC}**, through matched round **{index}**. The 15-minute check-in publishes completed rounds while simulation continues independently.

{chr(10).join(table)}

\\* Fixed-potential simulations at 10 mV peak into 10 kΩ. Candidate counts include shared starting designs and matching proposals. Equal candidate budgets are not equal CPU budgets. Differences this small do not establish a better search method. D00 is our synthetic control. Winners are selected automatically after numerical convergence checks; incomplete rounds do not update this table.

[Completed-round data and progress]({rel}/README.md) · [Wider search archive](results/2026-10-22-dc-wide/README.md) · [Independent scoring audit](results/2026-10-22-dc-audit/README.md)

{validation_block}

### Independent numerical check

{evidence_block}

</details>

<details>
<summary>Earlier six-design gallery</summary>

![Six automatically selected wider-search finalists](results/2026-10-22-dc-wide/finalists.png)

Frozen wider-search snapshot, retained for comparison with the evolving gallery above.

</details>

"""
    findings = text[end:].split("\n", 1)[1]
    findings = re.sub(
        r"!\[Feedback-guided search progress\]\([^\n]+\)",
        f"![Feedback-guided search progress]({rel}/progress.png)",
        findings,
    )
    findings = findings.replace(
        "Historical **trajectory-proxy** training curves; these are not the current direct-DC campaign. Fresh-seed results test whether those proxy gains survive evaluation. [Refinement methods and results](docs/REFINEMENT.md).",
        "Current direct-DC progress: best converged result retained after each completed matched round. Flat sections mean no better converged design was found; exploration continues. [Earlier trajectory-proxy study](docs/REFINEMENT.md).",
    )
    root.write_text(
        text[:start] + block + "## Current findings and targets\n" + findings,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
