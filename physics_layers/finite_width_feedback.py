"""Two-grid finite-width graphene feedback fixture; uncalibrated Gaussian width."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system

from .bias_charge import BiasChargeDevice
from .gaussian_site_mesh import GaussianSiteMeshMap
from .graphene_feedback_demo import fixture
from .poisson3d import Poisson3DRequest
from .site_acceleration import solve_accelerated


def main():
    base, original, eq = fixture(0.03)
    system = build_system(SquareDevice((), 2 * 0.246e-9), LatticeRequest((0.7,)), ribbon=True)
    reference = eq.solve(
        np.zeros(len(system.sites)), [2.5, 2.5], 300, tolerance=1e-7
    ).electrons_per_site
    rows = []
    for factor in (2, 4):
        shape = tuple(factor * (n - 1) + 1 for n in original.shape)
        spacing = tuple(h / factor for h in base.spacing_m)
        fixed = np.full(shape, 0.03)
        fixed[1:-1, 1:-1, 1:-1] = np.nan
        faces = tuple(
            np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3)
        )
        mesh = Poisson3DRequest(spacing, faces, np.zeros(shape), fixed)
        mapping = GaussianSiteMeshMap(shape, spacing, (0, 0, 0), original.positions_m, 0.1e-9)
        result = solve_accelerated(
            mesh,
            mapping,
            BiasChargeDevice(system, reference_mu_ev=2.5),
            reference,
            [2.505, 2.495],
            300,
            tolerance=1e-5,
        )
        rows.append(
            dict(
                spacing_m=spacing,
                shape=shape,
                potential_v=result.site_potential_v,
                transport=asdict(result.transport),
                residual=asdict(result.history[-1]),
            )
        )
        print("Completed spacing", spacing[0], flush=True)
    record = dict(
        sigma_m=0.1e-9,
        cutoff_sigma=5,
        positions_m=original.positions_m.tolist(),
        rows=rows,
        max_potential_change_v=float(
            np.max(abs(np.array(rows[1]["potential_v"]) - rows[0]["potential_v"]))
        ),
        current_relative_change=rows[1]["transport"]["currents_a"][0]
        / rows[0]["transport"]["currents_a"][0]
        - 1,
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("physics_layers").glob("*.py")
        },
    )
    out = Path("results/physics-reference/finite-width-feedback")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ["max_potential_change_v", "current_relative_change"]}))


if __name__ == "__main__":
    main()
