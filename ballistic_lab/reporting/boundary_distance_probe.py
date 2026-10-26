"""Symmetric top/bottom boundary-distance sweep; synthetic dielectric box."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system

from physics_layers.bias_charge import BiasChargeDevice
from physics_layers.gaussian_site_mesh import GaussianSiteMeshMap
from physics_layers.graphene_feedback_demo import fixture
from physics_layers.poisson3d import Poisson3DRequest
from physics_layers.site_acceleration import solve_accelerated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sigma-nm', type=float, default=0.1)
    parser.add_argument('--padding', type=int, nargs='+', default=[0, 3, 6])
    parser.add_argument('--output', type=Path, default=Path('results/physics-reference/finite-width-feedback'))
    args = parser.parse_args()
    if not np.isfinite(args.sigma_nm) or args.sigma_nm <= 0 or any(f < 0 for f in args.padding):
        parser.error('Positive finite width and nonnegative padding required')
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    base, original, eq = fixture(0.03)
    system = build_system(SquareDevice((), 2 * 0.246e-9), LatticeRequest((0.7,)), ribbon=True)
    prepared = []
    for padding in args.padding:
        factor = 2
        shape = tuple(factor * (n - 1) + 1 for n in original.shape)
        spacing = tuple(h / factor for h in base.spacing_m)
        shape = (shape[0] + 2*padding, *shape[1:])
        positions = original.positions_m.copy()
        positions[:, 0] += padding*spacing[0]
        fixed = np.full(shape, 0.03)
        fixed[1:-1, 1:-1, 1:-1] = np.nan
        faces = tuple(
            np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3)
        )
        mesh = Poisson3DRequest(spacing, faces, np.zeros(shape), fixed)
        mapping = GaussianSiteMeshMap(shape, spacing, (0, 0, 0), positions, args.sigma_nm * 1e-9)
        # Check every site's support, including sites with zero excess charge
        # at equilibrium, before any occupation or feedback solve.
        mapping.deposit_charge(np.ones(len(system.sites)), fixed)
        prepared.append((mesh, mapping, padding))
    reference = eq.solve(
        np.zeros(len(system.sites)), [2.5, 2.5], 300, tolerance=1e-7
    ).electrons_per_site
    rows = []
    for mesh, mapping, padding in prepared:
        shape, spacing = mapping.shape, mapping.spacing_m
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
                padding_nodes=padding,
                normal_boundary_distance_m=float(mapping.positions_m[0, 0]),
                spacing_m=spacing,
                shape=shape,
                potential_v=result.site_potential_v,
                transport=asdict(result.transport),
                residual=asdict(result.history[-1]),
            )
        )
        (out / f'padding-{padding}.json').write_text(json.dumps(rows[-1], indent=2))
        print('Completed padding', padding, flush=True)
    record = dict(
        sigma_m=args.sigma_nm * 1e-9,
        padding_nodes=args.padding,
        limitation='Synthetic uniform dielectric box; only normal boundaries move, lateral boundaries fixed. Not a calibrated stack or champion validation.',
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
