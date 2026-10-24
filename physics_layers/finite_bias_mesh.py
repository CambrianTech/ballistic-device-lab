"""Same physical box and carbon positions, twice the electrostatic resolution."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system

from .bias_charge import BiasChargeDevice
from .graphene_feedback_demo import fixture
from .poisson3d import Poisson3DRequest
from .site_acceleration import solve_accelerated
from .site_mesh import SiteMeshMap


def main():
    base, mapping, eq = fixture(0.03)
    shape = tuple(2 * (n - 1) + 1 for n in mapping.shape)
    spacing = tuple(x / 2 for x in base.spacing_m)
    fixed = np.full(shape, 0.03)
    fixed[1:-1, 1:-1, 1:-1] = np.nan
    faces = tuple(np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3))
    mesh = Poisson3DRequest(spacing, faces, np.zeros(shape), fixed)
    fine = SiteMeshMap(shape, spacing, (0, 0, 0), mapping.positions_m)
    assert np.allclose(
        (np.array(shape) - 1) * spacing,
        (np.array(mapping.shape) - 1) * base.spacing_m,
        rtol=0,
        atol=1e-24,
    )
    system = build_system(SquareDevice((), 2 * 0.246e-9), LatticeRequest((0.7,)), ribbon=True)
    neutral = eq.solve(
        np.zeros(len(system.sites)), [2.5, 2.5], 300, tolerance=1e-7
    ).electrons_per_site
    result = solve_accelerated(
        mesh,
        fine,
        BiasChargeDevice(system, reference_mu_ev=2.5),
        neutral,
        [2.505, 2.495],
        300,
        tolerance=1e-5,
    )
    baseline = Path("results/physics-reference/finite-bias-feedback/result.json")
    old = json.loads(baseline.read_text())["rows"][1]
    record = dict(
        spacing_m=spacing,
        shape=shape,
        positions_m=mapping.positions_m.tolist(),
        baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("physics_layers").glob("*.py")
        },
        transport=asdict(result.transport),
        potential_v=result.site_potential_v,
        residual=asdict(result.history[-1]),
        current_relative_change=result.transport.currents_a[0] / old["screened"]["currents_a"][0]
        - 1,
        max_site_potential_change_v=float(
            np.max(abs(np.array(result.site_potential_v) - old["potential_v"]))
        ),
        limitation="Two meshes only. Point-charge deposition changes atomic self interaction with grid spacing; no physical mesh convergence claim.",
    )
    out = Path("results/physics-reference/finite-bias-mesh")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(record, indent=2))
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    ax.plot(np.array(old["potential_v"]) * 1000, "o-", label="0.2 nm grid")
    ax.plot(np.array(result.site_potential_v) * 1000, "s-", label="0.1 nm grid")
    ax.set(
        xlabel="Carbon site index",
        ylabel="Screened potential (mV)",
        title="Same physical gate box: electrostatic mesh sensitivity",
    )
    ax.legend()
    fig.savefig(out / "mesh.png", dpi=160)
    print(
        json.dumps(
            {
                k: record[k]
                for k in ["current_relative_change", "max_site_potential_change_v", "residual"]
            }
        )
    )


if __name__ == "__main__":
    main()
