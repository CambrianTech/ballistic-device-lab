"""Publish the complete broader-family screen, including losses and search plateaus."""

import gzip
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ballistic_lab.geometry.families import geometry
from ballistic_lab.reporting.catalog import gallery


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    raw = args.directory / "discovery-results.json"
    if raw.exists():
        result = json.loads(raw.read_text())
    else:
        with gzip.open(str(raw) + ".gz", "rt") as stream:
            result = json.load(stream)
    nominal = next(v for v in result["validation"] if v["ratio"] == 1 and v["specularity"] == 0.8)
    records = []
    for i, candidate in enumerate(result["finalists"]):
        records.append(
            dict(
                id=f"D{i:02d}",
                **candidate,
                score=nominal["score_mean"][i],
                seed_std=nominal["seed_std"][i],
                p99_path_over_width=nominal["mean_p99_path_over_width"][i],
                excluded_polygons=[
                    p.tolist() for p in geometry(candidate["family"], candidate["x"])
                ],
                tolerance=result["tolerances"][i],
            )
        )
    (args.directory / "designs.json").write_text(json.dumps(records, indent=2))
    gallery(
        [r for r in records if "population" in r["name"]],
        args.directory / "discovery-gallery.png",
        "BEYOND TRIANGLES",
        note="All population finalists · same holdout seeds",
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    for ax, family in zip(axes.flat, result["plan"]["families"]):
        for method, color in (("random", "#358a94"), ("population", "#ca7133")):
            for repeat in range(result["plan"]["repeats"]):
                rows = [
                    r
                    for r in result["training"]
                    if r["family"] == family and r["method"] == method and r["repeat"] == repeat
                ]
                best = np.maximum.accumulate([max(r["scores"]) for r in rows])
                ax.plot(
                    [(r["round"] + 1) * result["plan"]["batch"] for r in rows],
                    best,
                    color=color,
                    alpha=0.65,
                    label=method if repeat == 0 else None,
                )
        ax.set(title=family, xlabel="Candidate evaluations", ylabel="Best training steering")
        ax.legend()
        ax.grid(alpha=0.2)
    fig.savefig(args.directory / "discovery-progress.png", dpi=170)
    plt.close(fig)
    lines = [
        "# Expanded geometry discovery",
        "",
        "![Population finalists](discovery-gallery.png)",
        "",
        "Every population finalist is shown, including losing families. Shaded polygons "
        "are excluded material. Coordinates are normalized, not a fabrication layout.",
        "",
        "![Search progress](discovery-progress.png)",
        "",
        "Each line is one repeat. Selection used training scores only. The table uses "
        "four fresh holdout seeds at mean free path/width = 1 and specularity = 0.8. "
        "Scores are angular derivatives, not electrical efficiency. Seed SD is "
        "Monte Carlo variability, not model or experimental uncertainty.",
        "",
        "[Geometry exports](designs.json) include explicit vertices and all finalists. "
        "[Full compressed experiment](discovery-results.json.gz) includes every proposal, "
        "score, scattering condition, and normalized tolerance perturbation.",
        "",
        "| ID | Candidate | Holdout score | Seed SD | Perturbed mean |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for r in records:
        lines.append(
            f"| {r['id']} | {r['name']} | {r['score']:.6f} | {r['seed_std']:.6f} "
            f"| {r['tolerance']['mean']:.6f} |"
        )
    (args.directory / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
