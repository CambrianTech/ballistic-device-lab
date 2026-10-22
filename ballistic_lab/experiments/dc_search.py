"""Bounded direct-DC pilot: frozen controls, global proposals, then feedback."""

import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

from ballistic_lab.experiments.coverage import CoveragePlan
from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.circuit import sinusoidal_cycle
from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
from ballistic_lab.transport.reservoirs import ThermalRequest

OUTPUT = Path("runs/dc-search")
FAMILY_NAMES = ("triangle", "profile", "islands", "radial")


def candidate(key, family, parameters, origin):
    return dict(
        key=key,
        family=family,
        parameters=list(parameters),
        origin=origin,
        obstacles=[p.tolist() for p in geometry(family, np.array(parameters))],
    )


def initial_candidates(seed=221026):
    rng = np.random.default_rng(seed)
    result = [candidate("triangle-control", "triangle", [1.0, 0.7, 0.0, 0.0], "fixed control")]
    for family in FAMILY_NAMES:
        for i, values in enumerate(FAMILIES[family].sample(rng, 2)):
            result.append(candidate(f"{family}-global-{i}", family, values, "global proposal"))
    catalog = json.loads(
        Path("results/2026-10-22-discovery/designs.json").read_text(encoding="utf-8")
    )
    for key in ("D00", "D14"):
        row = next(r for r in catalog if r["id"] == key)
        result.append(candidate(key, row["family"], row["x"], "archived control"))
    return result


def offspring(rows, seed=221027):
    rng = np.random.default_rng(seed)
    result = []
    for family in FAMILY_NAMES:
        parent = max(
            (
                r
                for r in rows
                if r["candidate"]["family"] == family
                and r["candidate"]["origin"] == "global proposal"
            ),
            key=lambda r: r["levels"][-1]["dc_power_w"],
        )
        bounds = np.array(FAMILIES[family].bounds)
        values = np.clip(
            np.array(parent["candidate"]["parameters"])
            + rng.normal(0, 0.12, len(bounds)) * (bounds[:, 1] - bounds[:, 0]),
            bounds[:, 0],
            bounds[:, 1],
        )
        result.append(
            candidate(
                f"{family}-feedback",
                family,
                values,
                f"DC feedback from {parent['candidate']['key']}",
            )
        )
    return result


def cycle_metrics(spectrum, phases=32):
    model = FrozenPotentialModel.from_spectrum(spectrum, ThermalRequest(0.9, 300))
    result = sinusoidal_cycle(model, 0.01, 1e4, phases)
    return dict(
        dc_v=result.dc_output_v,
        dc_power_w=result.dc_load_power_w,
        input_power_w=result.mean_input_power_w,
        efficiency=result.dc_efficiency,
        max_kcl_a=max(s.kcl_residual_a for s in result.samples),
    )


def evaluate(item, counts=(257,), output: Path = OUTPUT):
    path = output / f"{item['key']}.json.gz"
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            record = json.load(stream)
        if record["candidate"] != item:
            raise ValueError("Checkpoint candidate changed")
    else:
        record = dict(candidate=item, levels=[], spectrum=[])
    device = SquareDevice(item["obstacles"], CoveragePlan().width_m, 0.3)
    request = LatticeRequest((0.9,))
    system = None
    cache = {round(r["energy_ev"], 12): r for r in record["spectrum"]}
    if not cache and item["key"] in ("D00", "D14"):
        folder = "convergence" if item["key"] == "D00" else "coverage"
        source = Path(f"results/2026-10-22-{folder}/{item['key']}-nominal.json.gz")
        with gzip.open(source, "rt", encoding="utf-8") as stream:
            prior = json.load(stream)
        if prior["device_fingerprint"] != device.fingerprint:
            raise ValueError("Archived geometry mismatch")
        cache = {round(r["energy_ev"], 12): r for r in prior["spectrum"]}
    for count in counts:
        if any(level["count"] == count for level in record["levels"]):
            continue
        energies = np.linspace(0.42, 1.38, count)
        missing = tuple(float(e) for e in energies if round(float(e), 12) not in cache)
        if missing:
            if system is None:
                system = build_system(device, request)
            cache.update(
                {
                    round(r["energy_ev"], 12): r
                    for r in solve_spectrum(system, replace(request, energies_ev=missing))
                }
            )
        selected = [cache[round(float(e), 12)] for e in energies]
        metrics = cycle_metrics(selected)
        record["levels"].append(dict(count=count, **metrics))
        record["spectrum"] = sorted(cache.values(), key=lambda r: r["energy_ev"])
        record["device_fingerprint"] = device.fingerprint
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            json.dump(record, stream, allow_nan=False)
        print(f"{item['key']} {count}: {metrics['dc_v'] * 1e6:.5g} uV", flush=True)
    levels = record["levels"]
    checks = (
        [
            abs(b["dc_v"] - a["dc_v"]) <= 1e-9 + 0.01 * abs(b["dc_v"])
            for a, b in zip(levels[-3:], levels[-2:])
        ]
        if len(levels) >= 3
        else []
    )
    record["energy_converged"] = len(checks) == 2 and all(checks)
    if len(levels) >= 3:
        selected = [
            cache[round(float(e), 12)] for e in np.linspace(0.42, 1.38, levels[-1]["count"])
        ]
        fine = cycle_metrics(selected, 64)
        record["phase64"] = fine
        record["phase_converged"] = abs(fine["dc_v"] - levels[-1]["dc_v"]) <= 1e-9 + 0.01 * abs(
            fine["dc_v"]
        )
    return {k: v for k, v in record.items() if k != "spectrum"}


def main():
    if OUTPUT.exists():
        raise RuntimeError("Use a fresh output directory")
    items = initial_candidates()
    OUTPUT.mkdir(parents=True)
    manifest = dict(
        seed=221026,
        feedback_seed=221027,
        initial=items,
        objective="maximize DC component power into 10 kohm at 10 mV peak, 0.9 eV, 300 K",
        screening_grid=257,
        refinement_grids=[513, 1025],
        selection="fixed triangle plus top two screened candidates; no manual promotion",
        source={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("ballistic_lab").rglob("*.py")
        },
    )
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(evaluate, items))
        proposals = offspring(rows)
        (OUTPUT / "feedback-proposals.json").write_text(
            json.dumps(proposals, indent=2), encoding="utf-8"
        )
        rows += list(pool.map(evaluate, proposals))
        ranking = sorted(
            rows, key=lambda r: (-r["levels"][-1]["dc_power_w"], r["candidate"]["key"])
        )
        selected = {r["candidate"]["key"] for r in ranking[:2]} | {"triangle-control"}
        (OUTPUT / "selection.json").write_text(
            json.dumps(
                dict(ranking=[r["candidate"]["key"] for r in ranking], selected=sorted(selected)),
                indent=2,
            ),
            encoding="utf-8",
        )
        refined = list(
            pool.map(
                evaluate,
                [r["candidate"] for r in rows if r["candidate"]["key"] in selected],
                [(513, 1025)] * len(selected),
            )
        )
    lookup = {r["candidate"]["key"]: r for r in refined}
    rows = [lookup.get(r["candidate"]["key"], r) for r in rows]
    (OUTPUT / "summary.json").write_text(
        json.dumps(rows, indent=2, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
