"""Bounded follow-up of unresolved coverage outputs; preserve the original study."""

import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from ballistic_lab.experiments.coverage import CoveragePlan, evaluate_loads, output_convergence
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
from ballistic_lab.validation.receipts import model_fingerprint

SOURCE = Path("results/2026-10-22-coverage")
OUTPUT = Path("runs/convergence")
COUNTS = (2049, 4097)


def refine(key: str) -> dict:
    with gzip.open(SOURCE / f"{key}.json.gz", "rt") as stream:
        original = json.load(stream)
    case = original["case"]
    plan = CoveragePlan()
    device = SquareDevice(case["obstacles"], plan.width_m, case["contact_fraction"])
    if device.fingerprint != original["device_fingerprint"]:
        raise ValueError("Source device identity changed")
    request = LatticeRequest(**original["request"])
    system = build_system(device, request)
    if len(system.sites) != original["site_count"]:
        raise ValueError("Source lattice changed")
    cache = {round(row["energy_ev"], 12): row for row in original["spectrum"]}
    levels = [original["levels"][-1]]
    for count in COUNTS:
        energies = np.linspace(plan.energy_min_ev, plan.energy_max_ev, count)
        missing = tuple(float(e) for e in energies if round(float(e), 12) not in cache)
        for row in solve_spectrum(system, replace(request, energies_ev=missing)):
            cache[round(row["energy_ev"], 12)] = row
        spectrum = [cache[round(float(e), 12)] for e in energies]
        loads = evaluate_loads(spectrum, plan)
        checks = output_convergence(levels[-1]["loads"], loads, plan)
        levels.append(dict(count=count, loads=loads, convergence=checks))
        # Save each finished grid, including unresolved values.
        record = dict(
            case=case,
            device_fingerprint=device.fingerprint,
            original_converged=original["observable_converged"],
            levels=levels,
            spectrum=spectrum,
            status="completed" if count == COUNTS[-1] else "partial",
            observable_converged=[
                len(levels) == 3 and all(level["convergence"][i]["passed"] for level in levels[1:])
                for i in range(len(loads))
            ],
        )
        temporary = OUTPUT / f"{key}.tmp"
        with gzip.open(temporary, "wt") as stream:
            json.dump(record, stream, allow_nan=False)
        temporary.replace(OUTPUT / f"{key}.json.gz")
        print(f"{key}: {count} energies completed", flush=True)
    return {k: v for k, v in record.items() if k != "spectrum"}


def main():
    if OUTPUT.exists():
        raise RuntimeError("Use a fresh convergence directory; preserve earlier results")
    source_manifest = json.loads((SOURCE / "manifest.json").read_text())
    current = model_fingerprint()
    for path in ("transport/quantum.py", "transport/reservoirs.py", "pipeline/contracts.py"):
        if current[path] != source_manifest["source"][path]:
            raise RuntimeError(f"Cannot reuse spectra after physics source change: {path}")
    rows = json.loads((SOURCE / "summary.json").read_text())
    keys = [r["case"]["key"] for r in rows if not all(r["observable_converged"])]
    manifest = dict(
        keys=keys,
        grid_counts=COUNTS,
        plan=asdict(CoveragePlan()),
        source=current,
        inputs={
            key: hashlib.sha256((SOURCE / f"{key}.json.gz").read_bytes()).hexdigest()
            for key in keys
        },
    )
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    summaries = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        pending = {pool.submit(refine, key): key for key in keys}
        for future in as_completed(pending):
            key = pending[future]
            try:
                result = future.result()
            except Exception as error:
                result = dict(key=key, status="failed", error=f"{type(error).__name__}: {error}")
            summaries.append(result)
            (OUTPUT / "summary.json").write_text(json.dumps(summaries, indent=2))
    if any(r["status"] == "failed" for r in summaries):
        raise RuntimeError("One or more cases failed; retained in summary")


if __name__ == "__main__":
    main()
