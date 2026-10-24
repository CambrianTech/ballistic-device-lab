"""Bounded single-drive loaded graphene feedback experiment, not an AC cycle."""

import argparse
import hashlib
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.transport.circuit import CircuitTolerance, solve_terminal_load

from .bias_charge import BiasChargeDevice
from .current_cache import ExactCurrentCache
from .equilibrium_charge import EquilibriumChargeDevice
from .feedback_current import FeedbackCurrentModel
from .four_terminal_fixture import fixture
from .site_acceleration import solve_accelerated


def main(*, max_poles=32768, cache_currents=False):
    if type(max_poles) is not int or max_poles < 128:
        raise ValueError("Pole budget must be an integer >= 128")
    out = Path("runs/loaded-feedback-pilot")
    if max_poles != 32768:
        out = out.with_name(out.name + f"-poles-{max_poles}")
    if cache_currents:
        out = out.with_name(out.name + "-cached")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "attempt.lock").open("x") as lock:
        lock.write(str(os.getpid()))
    started = time.perf_counter()
    status = dict(pid=os.getpid(), phase="reference", charge_calls=0, circuit_calls=0)
    status["max_poles"] = max_poles
    status["cache_currents"] = cache_currents
    manifest = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path("physics_layers").glob("*.py")
    }
    manifest["ballistic_lab/transport/circuit.py"] = hashlib.sha256(
        Path("ballistic_lab/transport/circuit.py").read_bytes()
    ).hexdigest()
    status["source_sha256"] = manifest
    evaluations = []

    def save():
        status["elapsed_s"] = time.perf_counter() - started
        temp = out / "status.tmp"
        temp.write_text(json.dumps(status, indent=2), encoding="utf-8")
        temp.replace(out / "status.json")

    save()
    try:
        system, _, _ = fixture(np.zeros(4))
        neutral = (
            EquilibriumChargeDevice(system, max_poles=max_poles)
            .solve(np.zeros(len(system.sites)), [0.9] * 4, 300, tolerance=1e-7)
            .electrons_per_site
        )

        def evaluate(voltage):
            if status["circuit_calls"] >= 24:
                raise RuntimeError("Circuit evaluation budget exhausted")
            status["circuit_calls"] += 1
            status["phase"] = "load"
            save()
            system, mesh, mapping = fixture(voltage)
            provider = BiasChargeDevice(
                system, reference_mu_ev=0.9, lead_shifts_ev=voltage, max_poles=max_poles
            )

            class Counted:
                def solve(self, *args, **kwargs):
                    if status["charge_calls"] >= 240 or time.perf_counter() - started > 3600:
                        raise RuntimeError("Charge/time budget exhausted")
                    status["charge_calls"] += 1
                    save()
                    return provider.solve(*args, **kwargs)

            # Cold starts avoid silently following a history-dependent branch.
            result = solve_accelerated(
                mesh,
                mapping,
                Counted(),
                neutral,
                0.9 + voltage,
                300,
                tolerance=1e-6,
                method="broyden1",
            )
            evaluations.append(dict(voltage_v=voltage.tolist(), feedback=asdict(result)))
            # Retain completed feedback evidence even if the outer solve fails.
            (out / f"evaluation-{len(evaluations):03d}.json").write_text(
                json.dumps(evaluations[-1], default=lambda x: x.tolist(), indent=2),
                encoding="utf-8",
            )
            return result

        tolerance = CircuitTolerance(current_atol_a=1e-13, current_rtol=1e-6, root_xtol=1e-6)
        model = FeedbackCurrentModel(evaluate, lead_order=(0, 1, 2, 3))
        if cache_currents:
            model = ExactCurrentCache(model)
        answer = solve_terminal_load(model, 0.01, 1e4, tolerance=tolerance)
        (out / "result.json").write_text(
            json.dumps(
                dict(
                    solution=asdict(answer),
                    circuit_tolerance=asdict(tolerance),
                    drive_v=0.01,
                    load_ohm=1e4,
                    max_poles=max_poles,
                    cache_currents=cache_currents,
                    source_sha256=manifest,
                    scope="single instantaneous drive, not rectified DC; uncalibrated fixture",
                ),
                indent=2,
            ),
            encoding="utf-8",
        )
        status["phase"] = "complete"
    except Exception as exc:
        status.update(phase="failed", error=repr(exc))
        raise
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-poles", type=int, default=32768)
    parser.add_argument("--cache-currents", action="store_true")
    args = parser.parse_args()
    main(max_poles=args.max_poles, cache_currents=args.cache_currents)
