"""Frozen matched coverage study; cached nested grids and explicit failures."""

import gzip
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
from ballistic_lab.transport.reservoirs import ThermalRequest, solve_load, thermal_conductance
from ballistic_lab.validation.receipts import model_fingerprint


@dataclass(frozen=True, slots=True)
class CoveragePlan:
    candidate_ids: tuple[str, ...] = ("empty", "D00", "D12", "D14", "D16")
    fermi_ev: tuple[float, ...] = (0.75, 0.9, 1.05)
    loads_ohm: tuple[float, ...] = (1e3, 1e4, 1e5, 1e6)
    grid_counts: tuple[int, ...] = (257, 513, 1025)
    energy_min_ev: float = 0.42
    energy_max_ev: float = 1.38
    temperature_k: float = 300
    width_m: float = 60 * 0.246e-9
    output_atol_v: float = 1e-9
    output_rtol: float = 0.01


CONDITIONS = (
    ("nominal", 0.3, (0.0, 0.0)),
    ("wide-contact", 0.4, (0.0, 0.0)),
    ("atomic-offset", 0.3, (0.25, 0.25)),
)


def evaluate_loads(spectrum, plan: CoveragePlan):
    records = []
    for fermi in plan.fermi_ev:
        g, mass = thermal_conductance(spectrum, ThermalRequest(fermi, plan.temperature_k))
        for load in plan.loads_ohm:
            result = solve_load(g, 0.001, load)
            records.append(dict(fermi_ev=fermi, load_ohm=load, thermal_mass=mass, **asdict(result)))
    return records


def output_convergence(previous, current, plan: CoveragePlan):
    """Absolute+relative test on the observable, never the matrix alone."""
    if len(previous) != len(current):
        raise ValueError("Refinement conditions differ")
    checks = []
    for old, new in zip(previous, current, strict=True):
        if (old["fermi_ev"], old["load_ohm"]) != (new["fermi_ev"], new["load_ohm"]):
            raise ValueError("Refinement conditions differ")
        change = abs(new["output_voltage_v"] - old["output_voltage_v"])
        tolerance = plan.output_atol_v + plan.output_rtol * abs(new["output_voltage_v"])
        checks.append(dict(change_v=change, tolerance_v=tolerance, passed=change <= tolerance))
    return checks


def run_case(case):
    plan = CoveragePlan()
    output = Path("runs/coverage")
    name = case["key"]
    checkpoint = output / f"{name}.json.gz"
    if checkpoint.exists():
        with gzip.open(checkpoint, "rt") as stream:
            return json.load(stream)
    device = SquareDevice(case["obstacles"], plan.width_m, case["contact_fraction"])
    request = LatticeRequest((plan.energy_min_ev,), lattice_offset=case["offset"])
    system = build_system(device, request)
    levels, cache = [], {}
    for count in plan.grid_counts:
        energies = np.linspace(plan.energy_min_ev, plan.energy_max_ev, count)
        missing = tuple(float(e) for e in energies if round(float(e), 12) not in cache)
        for row in solve_spectrum(system, replace(request, energies_ev=missing)):
            cache[round(row["energy_ev"], 12)] = row
        spectrum = [cache[round(float(e), 12)] for e in energies]
        results = evaluate_loads(spectrum, plan)
        checks = output_convergence(levels[-1]["loads"], results, plan) if levels else []
        levels.append(dict(count=count, loads=results, convergence=checks))
    # Two successive refinements must satisfy each observable's tolerance.
    eligible = [
        all(level["convergence"][i]["passed"] for level in levels[1:])
        for i in range(len(levels[-1]["loads"]))
    ]
    record = dict(
        case=case,
        device_fingerprint=device.fingerprint,
        site_count=len(system.sites),
        request=asdict(request),
        levels=levels,
        observable_converged=eligible,
        all_observables_converged=all(eligible),
        spectrum=spectrum,
        status="completed",
    )
    temporary = checkpoint.with_suffix(".tmp")
    with gzip.open(temporary, "wt") as stream:
        json.dump(record, stream, allow_nan=False)
    temporary.replace(checkpoint)
    return record


def main():
    output = Path("runs/coverage")
    output.mkdir(parents=True, exist_ok=True)
    plan = CoveragePlan()
    catalog = json.loads(Path("results/2026-10-22-discovery/designs.json").read_text())
    polygons = {row["id"]: row["excluded_polygons"] for row in catalog}
    polygons["empty"] = []
    cases = [
        dict(
            key=f"{candidate}-{condition}",
            candidate=candidate,
            condition=condition,
            contact_fraction=contact,
            offset=offset,
            obstacles=polygons[candidate],
        )
        for candidate in plan.candidate_ids
        for condition, contact, offset in CONDITIONS
    ]
    manifest = dict(plan=asdict(plan), cases=cases, source=model_fingerprint())
    frozen = output / "manifest.json"
    encoded = json.dumps(manifest, sort_keys=True, indent=2)
    if frozen.exists() and frozen.read_text() != encoded:
        raise RuntimeError("Frozen run differs from this source/plan; use a fresh output directory")
    frozen.write_text(encoded)
    summaries = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        tasks = {pool.submit(run_case, case): case for case in cases}
        for task in as_completed(tasks):
            case = tasks[task]
            try:
                result = task.result()
                summary = {key: value for key, value in result.items() if key != "spectrum"}
                count = sum(result["observable_converged"])
                print(f"{case['key']}: {count}/12 observable convergence checks passed", flush=True)
            except Exception as error:
                summary = dict(case=case, status="failed", error=f"{type(error).__name__}: {error}")
                print(f"{case['key']}: FAILED {error}", flush=True)
            summaries.append(summary)
            (output / "summary.json").write_text(json.dumps(summaries, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
