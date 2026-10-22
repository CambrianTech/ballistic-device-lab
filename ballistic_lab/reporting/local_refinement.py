"""Publish isolated local-search progress without changing matched rankings."""

import json
from pathlib import Path


def render(destination: Path) -> str:
    root = Path("runs/winner-local")
    if not (root / "plan.json").exists():
        return ""
    plan = json.loads((root / "plan.json").read_text())
    results = (
        json.loads((root / "results.json").read_text()) if (root / "results.json").exists() else {}
    )
    parent_key = plan["parent"]["key"]
    completed = [r for k, r in results.items() if k != parent_key]
    converged = [r for r in completed if r.get("energy_converged") and r.get("phase_converged")]
    parent = results.get(parent_key, {})
    target = destination / "winner-local"
    target.mkdir(exist_ok=True)
    for name in ("plan.json", "source.json"):
        (target / name).write_bytes((root / name).read_bytes())
    (target / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    lines = [
        "### Winner-neighborhood experiment",
        "",
        f"Separate budget: **{len(completed)}/{len(plan['children'])} offspring evaluated**, {len(converged)} numerically converged so far. Parent: `{parent_key}`. These evaluations do not enter the three-method comparison.",
        "",
    ]
    if converged and parent.get("energy_converged") and parent.get("phase_converged"):
        best = max(converged, key=lambda r: r["phase64"]["dc_power_w"])
        lines += [
            "| Local experiment | Converged DC power (pW) |",
            "| --- | ---: |",
            f"| Parent | {parent['phase64']['dc_power_w'] * 1e12:.5f} |",
            f"| Best converged offspring: {best['candidate']['key']} | {best['phase64']['dc_power_w'] * 1e12:.5f} |",
            "",
        ]
    else:
        lines += ["Parent/offspring converged comparison pending.", ""]
    lines += [
        f"[Frozen plan and completed rows]({target.as_posix()}) · [Protocol](local_lab/README.md).",
        "",
    ]
    return "\n".join(lines)
