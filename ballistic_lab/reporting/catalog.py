"""Publish traceable design cards and geometry exports from committed experiments."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

from ballistic_lab.geometry.families import geometry

BACKGROUND = "#0b1426"
INK = "#e2eaf4"
ACCENTS = {"triangle": "#51d6ca", "beveled": "#ffa857", "cross": "#aab0ff"}


def records(root: Path) -> list[dict]:
    """Retain every frozen evaluation record, including repeated anchor geometries."""
    catalog = []
    for cohort, folder, filename in (
        ("F", "2026-10-22-families", "families-results.json"),
        ("R", "2026-10-22-refinement", "refinement-results.json"),
    ):
        source = f"results/{folder}/{filename}"
        result = json.loads((root / source).read_text())
        nominal = next(
            v for v in result["validation"] if v["ratio"] == 1 and v["specularity"] == 0.8
        )
        for i, candidate in enumerate(result["finalists"]):
            catalog.append(
                dict(
                    id=f"{cohort}{i:02d}",
                    **candidate,
                    source=source,
                    score=nominal["score_mean"][i],
                    seed_std=nominal["seed_std"][i],
                    p99_path_over_width=nominal["mean_p99_path_over_width"][i],
                    excluded_polygons=[
                        p.tolist() for p in geometry(candidate["family"], candidate["x"])
                    ],
                )
            )
    return catalog


def card(ax, record: dict) -> None:
    color = ACCENTS[record["family"]]
    ax.set_facecolor(BACKGROUND)
    for polygon in record["excluded_polygons"]:
        ax.add_patch(Polygon(polygon, facecolor="#26364f", edgecolor=color, lw=1.7))
    ax.plot([-1, 1, 1, -1, -1], [-1, -1, 1, 1, -1], color="#687992", lw=0.8)
    for x, y in (
        ([-1, -1], [-0.3, 0.3]),
        ([1, 1], [-0.3, 0.3]),
        ([-0.3, 0.3], [-1, -1]),
        ([-0.3, 0.3], [1, 1]),
    ):
        ax.plot(x, y, color=INK, lw=4)
    ax.set(xlim=(-1.07, 1.07), ylim=(-1.07, 1.07), aspect="equal")
    ax.axis("off")
    ax.set_title(f"{record['id']}  {record['name']}", color=INK, fontsize=11, pad=10)
    ax.text(
        0.5,
        -0.06,
        f"Steering {record['score']:.5f}  |  path tail {record['p99_path_over_width']:.2f} W",
        transform=ax.transAxes,
        ha="center",
        color=color,
        fontsize=10,
    )


def gallery(selected: list[dict], output: Path, title: str) -> None:
    rows = (len(selected) + 2) // 3
    fig, axes = plt.subplots(rows, 3, figsize=(12, rows * 4.0 + 0.8), facecolor=BACKGROUND)
    for ax, record in zip(np.asarray(axes).flat, selected):
        card(ax, record)
    for ax in list(np.asarray(axes).flat)[len(selected) :]:
        ax.axis("off")
    fig.suptitle(title, fontsize=21, color=INK, weight="bold", y=0.98)
    fig.text(
        0.5,
        0.012,
        "Normalized geometry · shaded: excluded material · white: contacts\n"
        "Angular steering proxy, not electrical efficiency · F and R use different holdout seeds",
        ha="center",
        color=INK,
        fontsize=10,
    )
    fig.subplots_adjust(top=0.91, bottom=0.09, hspace=0.35, wspace=0.18)
    fig.savefig(output, dpi=180, facecolor=BACKGROUND)
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    output = root / "designs"
    output.mkdir(exist_ok=True)
    catalog = records(root)
    by_id = {record["id"]: record for record in catalog}
    payload = dict(
        scope="Classical angular-response candidates, not validated electrical devices",
        units="Normalized; square cavity [-1,1]^2, side width W=2",
        contacts="Centered width 0.6 on all four sides; absorbing",
        evaluation="Mean free path/W=1; wall specularity=0.8; four holdout seeds",
        records=catalog,
    )
    (output / "catalog.json").write_text(json.dumps(payload, indent=2))
    gallery(
        [by_id[key] for key in ("R09", "R05", "R13", "R00", "R07", "F04")],
        output / "highlights.png",
        "DESIGNS DISCOVERED BY THE SEARCH",
    )
    # Show every distinct finalist geometry, preserving first occurrence order.
    seen, unique = set(), []
    for record in catalog:
        key = (record["family"], tuple(record["x"]))
        if key not in seen:
            seen.add(key)
            unique.append(record)
    gallery(unique, output / "all-designs.png", "THE DESIGN COLLECTION")
    lines = [
        "# Design catalog",
        "",
        "Every frozen evaluation record is published below, including anchors and repeated "
        "geometries. The collection contains " + str(len(unique)) + " distinct shapes.",
        "",
        "![Search highlights](highlights.png)",
        "",
        "## What the search found",
        "",
        "The beveled mutation family is the clearest refinement result: R05, R09, and R13 "
        "all beat their common anchor R01 on fresh seeds. R09 has the highest training "
        "score among these repeats and also the highest observed nominal holdout score. "
        "It is a proxy-score leader, not a proven best physical rectifier.",
        "",
        "R00 is the learned triangle anchor; R07 is the strongest training-selected "
        "triangle refinement. F04 is the strongest training-selected cross candidate "
        "in the family experiment. Cross layouts have shorter long-path tails but weaker "
        "steering in this screen, which makes them useful alternatives to retain.",
        "",
        "The highlights are a retrospective presentation, not an additional independent "
        "validation. All finalists remain available, including unsuccessful refinements.",
        "",
        "## Read the cards",
        "",
        "Steering is the dimensionless angular-response derivative. Path tail is the "
        "99th-percentile traveled distance divided by cavity width, averaged over input "
        "ports and seeds; it is not a measured delay or bandwidth. Every card uses mean "
        "free path/width = 1 and wall specularity = 0.8. F and R identify different "
        "experiments with different holdout seeds, so tiny cross-cohort differences "
        "should not be interpreted as improvements.",
        "",
        "![All distinct frozen designs](all-designs.png)",
        "",
        "## Reuse the geometry",
        "",
        "[Download the JSON catalog](catalog.json). Each record contains family parameters, "
        "explicit excluded-polygon vertices, scores, seed variability, path tails, and "
        "its source result file. Coordinates are normalized, not fabrication dimensions. "
        "The reference cross approximates a literature topology; it is not an exact "
        "published-device reconstruction. Geometry exports are MIT licensed.",
        "",
        "Regenerate from the repository root with `python -m ballistic_lab.reporting.catalog`.",
        "",
        "| ID | Candidate | Steering | Seed SD | Path tail / W | Source |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for r in catalog:
        lines.append(
            f"| {r['id']} | {r['name']} | {r['score']:.6f} | {r['seed_std']:.6f} "
            f"| {r['p99_path_over_width']:.3f} | [JSON](../{r['source']}) |"
        )
    (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Published {len(catalog)} evaluation records and {len(unique)} distinct geometries.")


if __name__ == "__main__":
    main()
