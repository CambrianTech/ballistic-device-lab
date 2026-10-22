"""Checkpointed single-CPU edge-vacancy ensemble, independent of search scoring."""

import gzip
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.pipeline.dc_continuous import save, single_worker
from ballistic_lab.transport.circuit import sinusoidal_cycle
from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
from ballistic_lab.transport.reservoirs import ThermalRequest
from edge_lab.lattice import VacancySystem, edge_sites
from verification_lab.worker import selected, sources

ROOT = Path("runs/edge-sensitivity")


def status(**fields):
    save(
        ROOT / "status.json",
        dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat(), **fields),
    )


def cycle(spectrum, phases=64):
    return sinusoidal_cycle(
        FrozenPotentialModel.from_spectrum(spectrum, ThermalRequest(0.9, 300)), 0.01, 1e4, phases
    )


def evaluate(candidate, vacancies, seed, folder):
    original = build_system(
        SquareDevice(candidate["obstacles"], 60 * 0.246e-9), LatticeRequest((0.9,))
    )
    eligible = edge_sites(original, candidate["obstacles"], 30)
    removed = np.random.default_rng(seed).choice(eligible, vacancies, replace=False)
    system = VacancySystem(original, removed)
    geometry = dict(
        candidate=candidate,
        seed=seed,
        vacancies=vacancies,
        eligible_sites=len(eligible),
        removed_indices=removed.tolist(),
        removed_positions=[list(original.sites[i].pos) for i in removed],
        components=system.components(),
    )
    save(folder / "geometry.json", geometry)
    if geometry["components"] != 1:
        return dict(**geometry, status="disconnected", levels=[])
    levels = []
    for count in (1025, 2049, 4097):
        energies = np.linspace(0.42, 1.38, count)
        path = folder / f"spectrum-{count}.json.gz"
        spectrum = json.loads(gzip.decompress(path.read_bytes())) if path.exists() else []
        if len(spectrum) > count or any(
            abs(r["energy_ev"] - energies[i]) > 1e-12 for i, r in enumerate(spectrum)
        ):
            raise ValueError("Checkpoint energy mismatch")
        for start in range(len(spectrum), count, 32):
            if (ROOT / "STOP").exists():
                return None
            spectrum.extend(
                solve_spectrum(system, LatticeRequest(tuple(energies[start : start + 32])))
            )
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(gzip.compress(json.dumps(spectrum).encode(), mtime=0))
            temporary.replace(path)
            status(
                phase="spectrum",
                candidate=candidate["key"],
                vacancies=vacancies,
                seed=seed,
                count=count,
                solved=len(spectrum),
            )
        result = cycle(spectrum)
        levels.append(dict(count=count, dc_v=result.dc_output_v, dc_power_w=result.dc_load_power_w))
    doubled = cycle(spectrum, 128)
    limit = 1e-9 + 0.01 * abs(doubled.dc_output_v)
    # Require both successive energy refinements and phase doubling to agree.
    energy_ok = all(abs(a["dc_v"] - b["dc_v"]) <= limit for a, b in zip(levels, levels[1:]))
    phase_ok = abs(levels[-1]["dc_v"] - doubled.dc_output_v) <= limit
    return dict(
        **geometry,
        status="converged" if energy_ok and phase_ok else "unresolved",
        levels=levels,
        energy_converged=energy_ok,
        phase_converged=phase_ok,
        dc_v=doubled.dc_output_v,
        dc_power_w=doubled.dc_load_power_w,
    )


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = sources()
    manifest.update(
        {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in Path("edge_lab").glob("*.py")}
    )
    with single_worker(ROOT):
        path = ROOT / "source.json"
        if path.exists() and json.loads(path.read_text()) != manifest:
            raise RuntimeError("Source changed; use a new validated campaign")
        save(path, manifest)
        while not (ROOT / "STOP").exists():
            rows = selected()
            plan = [
                (r["candidate"], n, seed)
                for n in (0, 1, 3)
                for seed in ((0,) if n == 0 else (101, 202, 303))
                for r in rows
            ]
            save(
                ROOT / "queue.json",
                dict(
                    cases=plan,
                    note="Equal vacancy counts, not equal damaged-edge fractions; three seeds are a pilot ensemble.",
                ),
            )
            for candidate, n, seed in plan:
                identity = hashlib.sha256(
                    json.dumps([candidate, n, seed, manifest], sort_keys=True).encode()
                ).hexdigest()
                folder = ROOT / identity
                folder.mkdir(exist_ok=True)
                if (folder / "result.json").exists():
                    continue
                if (ROOT / "STOP").exists():
                    break
                try:
                    result = evaluate(candidate, n, seed, folder)
                except Exception as error:
                    result = dict(
                        candidate=candidate,
                        vacancies=n,
                        seed=seed,
                        status="unresolved",
                        error=repr(error),
                    )
                if result is None:
                    break
                save(folder / "result.json", result)
            if not (ROOT / "STOP").exists():
                status(phase="waiting", cases=len(plan))
                time.sleep(15)
        status(phase="stopped")


if __name__ == "__main__":
    main()
