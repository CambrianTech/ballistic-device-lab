"""Bounded four-terminal finite-bias charge benchmark at fixed onsite potential."""

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system

from .bias_charge import BiasChargeDevice


def main():
    system = build_system(
        SquareDevice((), 4 * 0.246e-9, contact_width_fraction=0.6), LatticeRequest((0.9,))
    )
    rows = []
    for tolerance in (1e-6, 1e-7):
        started = time.perf_counter()
        result = BiasChargeDevice(system, reference_mu_ev=0.9).solve(
            np.zeros(len(system.sites)), [0.905, 0.895, 0.9, 0.9], 300, tolerance=tolerance
        )
        rows.append(
            dict(
                tolerance=tolerance, elapsed_s=time.perf_counter() - started, result=asdict(result)
            )
        )
        print("Completed", tolerance, flush=True)
    dn = float(
        np.max(
            abs(
                np.array(rows[0]["result"]["electrons_per_site"])
                - rows[1]["result"]["electrons_per_site"]
            )
        )
    )
    di = float(
        np.max(abs(np.array(rows[0]["result"]["currents_a"]) - rows[1]["result"]["currents_a"]))
    )
    assert dn < 1e-5 and di < 1e-10
    out = Path("results/physics-reference/four-terminal-charge")
    out.mkdir(parents=True, exist_ok=True)
    record = dict(
        sites=len(system.sites),
        rows=rows,
        max_charge_change=dn,
        max_current_change_a=di,
        chemical_potentials_ev=[0.905, 0.895, 0.9, 0.9],
        temperature_k=300,
        reference_mu_ev=0.9,
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                Path("physics_layers/bias_charge.py"),
                Path("physics_layers/equilibrium_charge.py"),
                Path("physics_layers/lead_charge.py"),
                Path("ballistic_lab/transport/quantum.py"),
            ]
        },
    )
    (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(
        json.dumps(
            dict(
                max_charge_change=dn,
                max_current_change_a=di,
                rows=[
                    dict(elapsed_s=r["elapsed_s"], currents_a=r["result"]["currents_a"])
                    for r in rows
                ],
            )
        )
    )


if __name__ == "__main__":
    main()
