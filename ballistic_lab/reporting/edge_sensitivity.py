"""Publish completed edge receipts without importing the quantum runtime."""

import json
import shutil
from pathlib import Path


def render(destination, source=Path("runs/edge-sensitivity")):
    queue = source / "queue.json"
    if not queue.exists():
        return "\n### Atomic-edge sensitivity\n\nPilot ensemble pending.\n"
    results = [json.loads(p.read_text()) for p in source.glob("*/result.json")]
    lines = [
        "\n### Atomic-edge sensitivity\n",
        "One- and three-atom edge-vacancy pilot; three fixed seeds per damage level. "
        "Intact baselines use the same convergence gates. Unresolved cases remain visible.\n",
        "| Design | Missing atoms | Completed / planned | Converged | DC magnitude range (µV) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    cases = json.loads(queue.read_text())["cases"]
    groups = sorted({(c["key"], n) for c, n, s in cases})
    for key, n in groups:
        rows = [r for r in results if r["candidate"]["key"] == key and r["vacancies"] == n]
        good = [abs(r["dc_v"]) * 1e6 for r in rows if r["status"] == "converged"]
        planned = sum(c["key"] == key and count == n for c, count, s in cases)
        span = f"{min(good):.3f}–{max(good):.3f}" if good else "Pending / unresolved"
        lines.append(f"| {key} | {n} | {len(rows)} / {planned} | {len(good)} | {span} |")
    archive = destination / "edge-sensitivity"
    archive.mkdir(exist_ok=True)
    shutil.copy2(queue, archive / "queue.json")
    shutil.copy2(source / "source.json", archive / "source.json")
    for path in source.glob("*/result.json"):
        folder = archive / path.parent.name
        folder.mkdir(exist_ok=True)
        shutil.copy2(path, folder / path.name)
        for name in ("geometry.json",):
            if (path.parent / name).exists():
                shutil.copy2(path.parent / name, folder / name)
    lines.append(
        "\nSmall pilot, not a fabrication-yield estimate. See [model and restart contract](edge_lab/README.md). Self-consistent electrostatics remains pending.\n"
    )
    return "\n".join(lines)
