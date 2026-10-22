"""Render completed falsification receipts; never run transport here."""

import json
import shutil
from pathlib import Path


def render(rows, destination, source=Path("runs/falsification")):
    receipts = []
    for path in sorted(source.glob("*/result.json")):
        receipts.append((path, json.loads(path.read_text())))
    table = [
        "### Automated falsification checks",
        "",
        "| Design | Fresh spectrum/DC replay | Terminal exchange |",
        "| --- | --- | --- |",
    ]
    output = destination / "falsification"
    output.mkdir(exist_ok=True)
    for row in rows:
        candidate = row["candidate"]
        matches = [
            (p, r) for p, r in receipts if r["candidate"]["obstacles"] == candidate["obstacles"]
        ]
        # Receipts are valid only for exactly the input row being reported.
        matches = [
            (p, r) for p, r in matches if json.loads((p.parent / "input.json").read_text()) == row
        ]
        if not matches:
            table.append(f"| {candidate['key']} | Pending | Pending |")
            continue
        path, result = matches[-1]
        folder = output / result["identity"]
        folder.mkdir(exist_ok=True)
        for name in ("result.json", "input.json", "fresh.json.gz"):
            if (path.parent / name).exists():
                shutil.copyfile(path.parent / name, folder / name)
        checks = result.get("checks", {})
        replay = (
            "Pass"
            if checks.get("fresh_transmission")
            and checks.get("fresh_dc")
            and checks.get("connected_graph")
            else result["status"].upper()
        )
        exchange = "Pass" if checks.get("terminal_exchange") else result["status"].upper()
        table.append(f"| {candidate['key']} | {replay} | {exchange} |")
    if (source / "source.json").exists():
        shutil.copyfile(source / "source.json", output / "source.json")
    return (
        "\n".join(table)
        + f"""

Fresh replay rebuilds the lattice and recomputes every energy on the accepted grid,
independently of the search spectrum cache. Terminal exchange checks readout sign
conventions; it is **not** a physical mirror-geometry test. These numerical passes
do not validate missing physics. Exact atomic reflection, controlled edge ensembles,
self-consistent graphene electrostatics, realistic scattering/contacts, frequency
response and matched paper-device comparison remain **unresolved**.
[Completed receipts and fresh spectra]({output.as_posix()}).

"""
    )
