"""Two-grid finite-width graphene feedback fixture; uncalibrated Gaussian width."""

import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sigma-nm', type=float, default=0.1)
    parser.add_argument('--factors', type=int, nargs='+', default=[2, 4])
    parser.add_argument('--output', type=Path, default=Path('results/physics-reference/finite-width-feedback'))
    args = parser.parse_args()
    if not np.isfinite(args.sigma_nm) or args.sigma_nm <= 0 or any(f < 1 for f in args.factors):
        parser.error('Positive finite width and positive integer grid factors required')
    out = args.output
    if (out / 'result.json').exists():
        raise FileExistsError(out / 'result.json')
    base, original, eq = fixture(0.03)
    system = build_system(SquareDevice((), 2 * 0.246e-9), LatticeRequest((0.7,)), ribbon=True)
    reference = eq.solve(
        np.zeros(len(system.sites)), [2.5, 2.5], 300, tolerance=1e-7
    ).electrons_per_site
    rows = []
    for factor in args.factors:
        shape = tuple(factor * (n - 1) + 1 for n in original.shape)
        spacing = tuple(h / factor for h in base.spacing_m)
        fixed = np.full(shape, 0.03)
        fixed[1:-1, 1:-1, 1:-1] = np.nan
        faces = tuple(
            np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3)
        )
        mesh = Poisson3DRequest(spacing, faces, np.zeros(shape), fixed)
        mapping = GaussianSiteMeshMap(shape, spacing, (0, 0, 0), original.positions_m, args.sigma_nm * 1e-9)
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
        sigma_m=args.sigma_nm * 1e-9,
        grid_factors=args.factors,
        cutoff_sigma=5,
        positions_m=original.positions_m.tolist(),
        rows=rows,
        max_potential_change_v=float(
            np.max(abs(np.array(rows[-1]["potential_v"]) - rows[0]["potential_v"]))
        ) if len(rows) > 1 else None,
        current_relative_change=(rows[-1]["transport"]["currents_a"][0]
        / rows[0]["transport"]["currents_a"][0]
        - 1) if len(rows) > 1 else None,
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("physics_layers").glob("*.py")
        },
    )
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps({k: record[k] for k in ["max_potential_change_v", "current_relative_change"]}))


if __name__ == "__main__":
    main()
