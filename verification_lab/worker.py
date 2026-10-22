"""One-CPU fresh spectral replay of controls and each completed-round leader."""

import argparse
import gzip
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.sparse.csgraph import connected_components

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.pipeline.dc_continuous import save, single_worker
from ballistic_lab.reporting.dc_search import promoted
from ballistic_lab.transport.circuit import sinusoidal_cycle
from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
from ballistic_lab.transport.reservoirs import ThermalRequest

ROOT = Path("runs/falsification")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sources():
    paths = [p for p in Path("ballistic_lab").rglob("*.py") if "reporting" not in p.parts]
    paths += list(Path("verification_lab").glob("*.py"))
    paths += [Path("ballistic_lab/reporting/dc_search.py")]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def selected():
    snapshots = sorted(Path("runs/dc-continuous").glob("round-*.json"))
    base = json.loads(Path("results/2026-10-22-dc-wide/summary.json").read_text())
    rows = [r for r in base if r["candidate"]["key"] in ("D00", "triangle-control")]
    if snapshots:
        snapshot = json.loads(snapshots[-1].read_text())
        leaders = promoted([r for history in snapshot["histories"].values() for r in history])
        if leaders:
            rows.append(leaders[0])
    return rows


def status(**fields):
    save(
        ROOT / "status.json",
        dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat(), **fields),
    )


def cycle(spectrum):
    return sinusoidal_cycle(
        FrozenPotentialModel.from_spectrum(spectrum, ThermalRequest(0.9, 300)), 0.01, 1e4, 64
    )


def verify(row, folder):
    candidate = row["candidate"]
    count = row["levels"][-1]["count"]
    device = SquareDevice(candidate["obstacles"], 60 * 0.246e-9)
    system = build_system(device, LatticeRequest((0.9,)))
    graph = system.hamiltonian_submatrix(sparse=True).tocsr()
    graph.setdiag(0)
    graph.eliminate_zeros()
    components = connected_components(graph, directed=False, return_labels=False)
    # This checkpoint belongs only to this fresh replay, never to the search cache.
    checkpoint = folder / "fresh.json.gz"
    spectrum = []
    if checkpoint.exists():
        spectrum = json.loads(gzip.decompress(checkpoint.read_bytes()))
    energies = np.linspace(0.42, 1.38, count)
    if any(abs(r["energy_ev"] - energies[i]) > 1e-12 for i, r in enumerate(spectrum)):
        raise ValueError("Replay checkpoint energy mismatch")
    for start in range(len(spectrum), count, 32):
        if (ROOT / "STOP").exists():
            return None
        spectrum.extend(solve_spectrum(system, LatticeRequest(tuple(energies[start : start + 32]))))
        temporary = checkpoint.with_suffix(".tmp")
        temporary.write_bytes(gzip.compress(json.dumps(spectrum).encode(), mtime=0))
        temporary.replace(checkpoint)
        status(phase="fresh_replay", candidate=candidate["key"], solved=len(spectrum), total=count)
    fresh = cycle(spectrum)
    # Exact terminal exchange tests circuit/readout covariance, not a physical
    # atomistic reflection. It must reverse transverse output and preserve power.
    order = np.array([0, 1, 3, 2])
    exchanged = [
        dict(
            r,
            modes=np.array(r["modes"])[order].tolist(),
            transmission=np.array(r["transmission"])[np.ix_(order, order)].tolist(),
        )
        for r in spectrum
    ]
    swapped = cycle(exchanged)
    path = Path("runs/dc-continuous/spectra") / f"{candidate['key']}.json.gz"
    if not path.exists():
        path = Path("results/2026-10-22-dc-wide") / path.name
    archive = json.loads(gzip.decompress(path.read_bytes()))
    if archive["candidate"]["obstacles"] != candidate["obstacles"]:
        raise ValueError("Original geometry mismatch")
    cache = {round(r["energy_ev"], 12): r for r in archive["spectrum"]}
    matrix_error = max(
        float(
            np.max(
                abs(np.array(r["transmission"]) - cache[round(r["energy_ev"], 12)]["transmission"])
            )
        )
        for r in spectrum
    )
    voltage_error = abs(fresh.dc_output_v - row["phase64"]["dc_v"])
    swap_error = abs(fresh.dc_output_v + swapped.dc_output_v)
    checks = dict(
        connected_graph=components == 1,
        fresh_transmission=matrix_error <= 1e-8,
        fresh_dc=voltage_error <= 1e-10 + 0.001 * abs(fresh.dc_output_v),
        terminal_exchange=swap_error <= 1e-10 + 0.001 * abs(fresh.dc_output_v),
    )
    return dict(
        candidate=candidate,
        status="pass" if all(checks.values()) else "fail",
        checks=checks,
        energy_count=count,
        fresh_dc_v=fresh.dc_output_v,
        previous_dc_v=row["phase64"]["dc_v"],
        voltage_difference_v=voltage_error,
        transmission_difference=matrix_error,
        terminal_exchange_error_v=swap_error,
        unresolved=[
            "exact atomistic reflection",
            "controlled atomic edge ensemble",
            "self-consistent graphene electrostatics",
            "phonons and realistic contacts",
            "frequency response",
            "matched published-device comparison",
        ],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    with single_worker(ROOT):
        manifest = sources()
        source_path = ROOT / "source.json"
        if source_path.exists() and json.loads(source_path.read_text()) != manifest:
            raise RuntimeError("Verification source changed; use a new campaign")
        save(source_path, manifest)
        while not (ROOT / "STOP").exists():
            for row in selected():
                identity = digest(dict(row=row, source=manifest))
                folder = ROOT / identity
                folder.mkdir(exist_ok=True)
                if (folder / "result.json").exists():
                    continue
                save(folder / "input.json", row)
                try:
                    result = verify(row, folder)
                except Exception as error:
                    result = dict(
                        candidate=row["candidate"], status="unresolved", error=repr(error)
                    )
                if result is None:
                    break
                result["identity"] = identity
                save(folder / "result.json", result)
            if args.once:
                break
            status(phase="waiting")
            time.sleep(15)
        status(phase="stopped")


if __name__ == "__main__":
    main()
