"""One bounded four-terminal feedback evaluation; status persists between check-ins."""

import hashlib
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .bias_charge import BiasChargeDevice
from .equilibrium_charge import EquilibriumChargeDevice
from .four_terminal_fixture import fixture
from .site_acceleration import solve_accelerated


def main():
    out = Path("runs/four-terminal-feedback-pilot")
    out.mkdir(parents=True, exist_ok=True)
    # A retained lock is intentional: diagnose a stopped attempt before rerunning.
    with (out / "attempt.lock").open("x") as f:
        f.write(str(os.getpid()))
    started = time.perf_counter()
    status = dict(
        pid=os.getpid(),
        phase="reference",
        charge_evaluations=0,
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("physics_layers").glob("*.py")
        },
    )

    def save():
        status["elapsed_s"] = time.perf_counter() - started
        temporary = out / "status.tmp"
        temporary.write_text(json.dumps(status, indent=2), encoding="utf-8")
        temporary.replace(out / "status.json")

    save()
    try:
        voltage = np.array([0.005, -0.005, 0, 0])
        system, mesh, mapping = fixture(voltage)
        neutral = (
            EquilibriumChargeDevice(system)
            .solve(np.zeros(len(system.sites)), [0.9] * 4, 300, tolerance=1e-7)
            .electrons_per_site
        )
        provider = BiasChargeDevice(system, reference_mu_ev=0.9, lead_shifts_ev=voltage)

        class Counted:
            def solve(self, *args, **kwargs):
                if status["charge_evaluations"] >= 80:
                    raise RuntimeError("Bounded pilot reached 80 charge evaluations")
                status["charge_evaluations"] += 1
                status["phase"] = "feedback"
                save()
                return provider.solve(*args, **kwargs)

        result = solve_accelerated(
            mesh, mapping, Counted(), neutral, 0.9 + voltage, 300, tolerance=1e-5
        )
        record = dict(
            transport=asdict(result.transport),
            site_potential_v=result.site_potential_v,
            history=[asdict(step) for step in result.history],
            reference_occupations=neutral,
            reservoir_voltages_v=voltage.tolist(),
            gate_electrostatic_v=0.03,
            convention="mu=0.9+V, lead onsite=+V, contact phi=-V, device onsite=-phi",
            source_sha256=status["source_sha256"],
        )
        (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        status["phase"] = "complete"
    except Exception as exc:
        status["phase"] = "failed"
        status["error"] = repr(exc)
        raise
    finally:
        save()


if __name__ == "__main__":
    main()
