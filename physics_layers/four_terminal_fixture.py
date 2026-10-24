"""Explicit small four-terminal fixture for a bounded feedback pilot."""

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system

from .electrode_boundary import ElectrodeBoundary
from .gaussian_site_mesh import GaussianSiteMeshMap
from .poisson3d import Poisson3DRequest


def fixture(reservoir_voltages_v, gate_v=0.03):
    """Reservoir V means mu=EF+V eV; electrostatic phi=-V at contacts.

    Lead onsite bands shift by +V eV in the caller. Gate uses electrostatic volts.
    Remote full-side box electrodes are a surrogate, not calibrated contacts.
    """
    reservoir_voltages_v = np.asarray(reservoir_voltages_v, float)
    if reservoir_voltages_v.shape != (4,) or not np.isfinite(reservoir_voltages_v).all():
        raise ValueError("Four finite reservoir voltages required")
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
    fixed = boundary.potentials([-v for v in reservoir_voltages_v] + [gate_v])
    mapping = GaussianSiteMeshMap(shape, (h,) * 3, (0, 0, 0), positions, 0.1e-9)
    faces = tuple(np.full(tuple(n - (i == a) for i, n in enumerate(shape)), 4.0) for a in range(3))
    mesh = Poisson3DRequest((h,) * 3, faces, np.zeros(shape), fixed)
    return system, mesh, mapping
