"""One independent CPU validator; completed cases are immutable and resumable."""

import gzip
import hashlib
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from ballistic_lab.experiments.coverage import CONDITIONS, CoveragePlan
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.pipeline.dc_continuous import save, single_worker, status
from ballistic_lab.transport.circuit import sinusoidal_cycle
from ballistic_lab.transport.cpu import trace
from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
from ballistic_lab.transport.reservoirs import ThermalRequest
from followup_lab.plan import identity, leader, passes

ROOT = Path("runs/leader-validation")
SOURCE = Path("runs/dc-continuous")
FERMI = (0.75, 0.9, 1.05)
LOADS = (1e3, 1e4, 1e5)


def cycle(spectrum, fermi, load, phases):
    model = FrozenPotentialModel.from_spectrum(spectrum, ThermalRequest(fermi, 300))
    result = sinusoidal_cycle(model, 0.01, load, phases)
    return dict(
        dc_v=result.dc_output_v,
        dc_power_w=result.dc_load_power_w,
        max_kcl_a=max(s.kcl_residual_a for s in result.samples),
    )


def evaluate(candidate, condition, root=ROOT):
    name, contact, offset = condition
    folder = root / identity(candidate)
    folder.mkdir(exist_ok=True)
    target = folder / f"{name}.json"
    if target.exists():
        return
    checkpoint = folder / f"{name}-spectrum.json.gz"
    cache = {}
    if checkpoint.exists():
        with gzip.open(checkpoint, "rt", encoding="utf-8") as stream:
            cache = {round(r["energy_ev"], 12): r for r in json.load(stream)}
    elif name == "nominal":
        source = SOURCE / "spectra" / f"{candidate['key']}.json.gz"
        if not source.exists():
            source = Path("results/2026-10-22-dc-wide") / f"{candidate['key']}.json.gz"
        if source.exists():
            with gzip.open(source, "rt", encoding="utf-8") as stream:
                record = json.load(stream)
            if record["candidate"]["obstacles"] != candidate["obstacles"]:
                raise ValueError("Cached geometry mismatch")
            cache = {round(r["energy_ev"], 12): r for r in record["spectrum"]}
    device = SquareDevice(candidate["obstacles"], CoveragePlan().width_m, contact)
    request = LatticeRequest((0.9,), lattice_offset=offset)
    system = None
    levels = []
    for count in (257, 513, 1025, 2049, 4097):
        status(root, phase="validate", candidate=candidate["key"], condition=name, grid=count)
        energies = np.linspace(0.42, 1.38, count)
        missing = tuple(float(e) for e in energies if round(float(e), 12) not in cache)
        if missing:
            if system is None:
                system = build_system(device, request)
            for row in solve_spectrum(system, replace(request, energies_ev=missing)):
                cache[round(row["energy_ev"], 12)] = row
            temporary = checkpoint.with_suffix(".tmp")
            with gzip.open(temporary, "wt", encoding="utf-8") as stream:
                json.dump(list(cache.values()), stream, allow_nan=False)
            temporary.replace(checkpoint)
        spectrum = [cache[round(float(e), 12)] for e in energies]
        metrics = [
            dict(fermi_ev=f, load_ohm=load, **cycle(spectrum, f, load, 32))
            for f in FERMI
            for load in LOADS
        ]
        levels.append(dict(count=count, metrics=metrics))
        if len(levels) < 3:
            continue
        fine = [
            dict(fermi_ev=f, load_ohm=load, **cycle(spectrum, f, load, 64))
            for f in FERMI
            for load in LOADS
        ]
        for index, row in enumerate(fine):
            row["energy_converged"] = passes([level["metrics"][index]["dc_v"] for level in levels])
            row["phase_converged"] = abs(row["dc_v"] - metrics[index]["dc_v"]) <= 1e-9 + 0.01 * abs(
                row["dc_v"]
            )
        if all(r["energy_converged"] and r["phase_converged"] for r in fine):
            break
    save(
        target,
        dict(
            candidate=candidate,
            condition=name,
            contact_fraction=contact,
            lattice_offset=offset,
            levels=levels,
            results=fine,
            device_fingerprint=device.fingerprint,
        ),
    )


def rays(candidate, root=ROOT):
    folder = root / identity(candidate)
    folder.mkdir(exist_ok=True)
    target = folder / "rays.json"
    if target.exists():
        return
    polygons = [np.array(p) for p in candidate["obstacles"]]
    rows = []
    for specularity in (0.5, 0.8, 1.0):
        for mfp in (1.0, 2.0, 4.0):
            for seed in (61001, 61002, 61003):
                ports = []
                for port in (0, 1):
                    probabilities, _, paths = trace(
                        polygons, port, n=2048, specularity=specularity, mfp=mfp, seed=seed + port
                    )
                    ports.append(dict(probabilities=probabilities.tolist(), paths=paths))
                rows.append(dict(specularity=specularity, mfp=mfp, seed=seed, ports=ports))
    save(
        target,
        dict(
            candidate=candidate,
            rays_per_port=2048,
            records=rows,
            observable="Exit probabilities and illustrative paths; not DC efficiency",
        ),
    )


def run(root=ROOT):
    root.mkdir(parents=True, exist_ok=True)
    with single_worker(root):
        files = list(Path("ballistic_lab").rglob("*.py")) + list(Path("followup_lab").glob("*.py"))
        hashes = {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
            if "reporting" not in p.parts
        }
        manifest = root / "source.json"
        if manifest.exists() and json.loads(manifest.read_text()) != hashes:
            raise RuntimeError("Validation source changed; start a separate campaign")
        save(manifest, hashes)
        controls = json.loads(Path("results/2026-10-22-dc-wide/summary.json").read_text())
        controls = [
            r["candidate"] for r in controls if r["candidate"]["key"] in ("D00", "triangle-control")
        ]
        try:
            while not (root / "STOP").exists():
                snapshots = sorted(SOURCE.glob("round-*.json"))
                selected = []
                for path in snapshots:
                    candidate = leader(json.loads(path.read_text()))
                    if candidate and identity(candidate) not in {identity(c) for c in selected}:
                        selected.append(candidate)
                # Latest leader first; retain earlier leaders in the queue.
                candidates = controls + selected[::-1]
                save(
                    root / "queue.json",
                    dict(
                        candidates=candidates,
                        source_round=snapshots[-1].name if snapshots else None,
                    ),
                )
                for candidate in candidates:
                    status(root, phase="rays", candidate=candidate["key"])
                    rays(candidate, root)
                for candidate in candidates:
                    for condition in CONDITIONS:
                        if (root / "STOP").exists():
                            status(root, phase="stopped")
                            return
                        evaluate(candidate, condition, root)
                status(root, phase="waiting", candidates=len(candidates))
                time.sleep(30)
            status(root, phase="stopped")
        except Exception as error:
            status(root, phase="failed", error=repr(error))
            raise


if __name__ == "__main__":
    run()
