"""Descriptive matched-condition comparisons; never modifies search scoring."""

import json
from pathlib import Path
from statistics import median

from followup_lab.plan import identity


def compare(candidate, control):
    ratios = []
    for key in sorted(candidate.keys() & control.keys()):
        a, b = candidate[key], control[key]
        if all(r["energy_converged"] and r["phase_converged"] for r in (a, b)):
            if b["dc_power_w"] > 0:
                ratios.append(a["dc_power_w"] / b["dc_power_w"])
    return dict(
        matched=len(ratios),
        higher=sum(r > 1 for r in ratios),
        median_ratio=median(ratios) if ratios else None,
        worst_ratio=min(ratios) if ratios else None,
    )


def render(destination):
    root = Path("runs/leader-validation")
    queue = root / "queue.json"
    if not queue.exists():
        return ""
    items = json.loads(queue.read_text())["candidates"]
    rows = {}
    archive = destination / "robustness"
    archive.mkdir(exist_ok=True)
    for item in items:
        cases = {}
        for condition in ("nominal", "wide-contact", "atomic-offset"):
            path = root / identity(item) / f"{condition}.json"
            if path.exists():
                record = json.loads(path.read_text())
                (archive / f"{identity(item)}-{condition}.json").write_bytes(path.read_bytes())
                for r in record["results"]:
                    cases[condition, r["fermi_ev"], r["load_ohm"]] = r
        rows[item["key"]] = cases
    control = rows.get("D00", {})
    summary = {name: compare(cases, control) for name, cases in rows.items()}
    (archive / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    table = [
        "| Tested design | Matched cases | Higher power than D00 | Median power / D00 | Worst power / D00 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, r in summary.items():
        values = [
            f"{r[k]:.3g}×" if r[k] is not None else "Pending"
            for k in ("median_ratio", "worst_ratio")
        ]
        table.append(f"| {name} | {r['matched']}/27 | {r['higher']} | {values[0]} | {values[1]} |")
    return (
        "### Peak performance and robustness\n\n"
        + "\n".join(table)
        + "\n\nEach ratio compares DC load power at the same energy, load and contact condition. "
        "Below 1× means less power than D00. Only pairs passing both numerical convergence gates enter; "
        "partial coverage is not comparable to complete coverage. These are equally weighted descriptive "
        "summaries, not probabilities of success, efficiency or a new search objective. Historical tested "
        f"leaders remain visible. [All supporting cases]({archive.as_posix()}).\n"
    )

