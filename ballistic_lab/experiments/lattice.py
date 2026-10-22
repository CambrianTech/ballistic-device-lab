"""Reference gates followed by a frozen, diverse lattice shortlist."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import (
    LatticeRequest,
    LatticeStage,
    build_system,
    solve_spectrum,
)
from ballistic_lab.validation.receipts import model_fingerprint


def reference_gate(request, width_m):
    device = SquareDevice((), width_m)
    system = build_system(device, request, ribbon=True)
    rows = solve_spectrum(system, request)
    if not any(row["modes"][0] for row in rows):
        raise RuntimeError("Reference has no conducting modes")
    for row in rows:
        if abs(row["transmission"][1][0] - row["modes"][0]) > request.tolerance:
            raise RuntimeError("Matched ribbon is not perfectly transmitting")
    shifted = replace(
        request, onsite_ev=0.137, energies_ev=tuple(e + 0.137 for e in request.energies_ev)
    )
    shifted_rows = solve_spectrum(build_system(device, shifted, ribbon=True), shifted)
    gauge_error = max(
        float(np.max(abs(np.array(a["transmission"]) - b["transmission"])))
        for a, b in zip(rows, shifted_rows, strict=True)
    )
    if gauge_error > request.tolerance:
        raise RuntimeError("Uniform energy-offset invariance failed")
    return dict(site_count=len(system.sites), spectrum=rows, gauge_residual=gauge_error)


def main():
    output = Path("runs/lattice")
    output.mkdir(parents=True, exist_ok=True)
    target = output / "lattice.json"
    if target.exists():
        raise FileExistsError(target)
    request = LatticeRequest(tuple(np.linspace(0.15, 1.35, 9)))
    catalog = json.loads(Path("results/2026-10-22-discovery/designs.json").read_text())
    selected = [dict(id="empty", excluded_polygons=[])] + [
        row for row in catalog if row["id"] in ("D00", "D12", "D14", "D16")
    ]
    records, references = [], []
    for cells in (40, 60):
        width = cells * request.lattice_constant_m
        references.append(dict(width_m=width, **reference_gate(request, width)))
        print(f"Reference passed: {width * 1e9:.2f} nm", flush=True)
        for row in selected:
            device = SquareDevice.from_geometry(row["excluded_polygons"], width)
            result = LatticeStage().evaluate(device, request)
            records.append(dict(id=row["id"], width_m=width, **asdict(result)))
            print(f"{row['id']}: {result.site_count} sites", flush=True)
    target.write_text(
        json.dumps(
            dict(
                model_fingerprint=model_fingerprint(),
                reference=references,
                devices=records,
                scope="Coherent elastic static transmission; no efficiency or rectification inference",
            ),
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
