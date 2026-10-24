"""Small four-terminal graphene/electrode preflight, not a completed DC solve."""

import hashlib
import json
from pathlib import Path

import kwant
import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system

from .electrode_boundary import ElectrodeBoundary
from .gaussian_site_mesh import GaussianSiteMeshMap
from .poisson3d import Poisson3DRequest, Poisson3DStage


def main():
    system = build_system(
        SquareDevice((), 4 * 0.246e-9, contact_width_fraction=0.6), LatticeRequest((2.5,))
    )
    xy = np.array([site.pos for site in system.sites]) * 0.246e-9
    positions = np.c_[np.zeros(len(xy)), xy[:, 1], xy[:, 0]]
    positions -= positions.min(axis=0)
    positions += 0.6e-9
    h = 0.1e-9
    shape = tuple((np.ceil((positions.max(axis=0) + 0.6e-9) / h).astype(int) + 1).tolist())
    z, y, x = np.indices(shape)
    left = (x == 0) & (z > 0) & (z < shape[0] - 1) & (y > 0) & (y < shape[1] - 1)
    right = (x == shape[2] - 1) & (z > 0) & (z < shape[0] - 1) & (y > 0) & (y < shape[1] - 1)
    top = (y == shape[1] - 1) & (z > 0) & (z < shape[0] - 1) & (x > 0) & (x < shape[2] - 1)
    bottom = (y == 0) & (z > 0) & (z < shape[0] - 1) & (x > 0) & (x < shape[2] - 1)
    outer = (
        (z == 0)
        | (z == shape[0] - 1)
        | (y == 0)
        | (y == shape[1] - 1)
        | (x == 0)
        | (x == shape[2] - 1)
    )
    gate = outer & ~(left | right | top | bottom)
    boundary = ElectrodeBoundary((left, right, top, bottom, gate))
    fixed = boundary.potentials([0.005, -0.005, 0, 0, 0.03])
    mapping = GaussianSiteMeshMap(shape, (h,) * 3, (0, 0, 0), positions, 0.1e-9)
    rho = mapping.deposit_charge(np.ones(len(positions)) * 1e-19, fixed)
    np.testing.assert_allclose(rho.sum() * h**3, len(positions) * 1e-19, rtol=1e-12)
    faces = tuple(np.full(tuple(n - (i == a) for i, n in enumerate(shape)), 4.0) for a in range(3))
    field = Poisson3DStage().evaluate(Poisson3DRequest((h,) * 3, faces, np.zeros(shape), fixed))
    spectrum = []
    for energy in (0.9, 2.5, 3.0):
        scattering = kwant.smatrix(system, energy)
        spectrum.append(
            dict(energy_ev=energy, modes=[int(scattering.num_propagating(i)) for i in range(4)])
        )
    out = Path("results/physics-reference/four-terminal-preflight")
    out.mkdir(parents=True, exist_ok=True)
    record = dict(
        sites=len(positions),
        shape=shape,
        positions_m=positions.tolist(),
        terminal_order=["L", "R", "T", "B"],
        spectrum=spectrum,
        uncharged_site_potential_v=mapping.sample_potential(field.potential_v).tolist(),
        electrode_nodes=[int(m.sum()) for m in boundary.masks],
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                Path("ballistic_lab/transport/quantum.py"),
                Path("physics_layers/electrode_boundary.py"),
                Path("physics_layers/gaussian_site_mesh.py"),
            ]
        },
    )
    (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    main()

