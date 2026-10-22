"""Conservative trilinear site/grid coupling in SI units, using (z, y, x)."""

from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.sparse import coo_matrix

from .poisson3d import frozen_array


@dataclass(frozen=True, slots=True)
class SiteMeshMap:
    shape: tuple[int, int, int]
    spacing_m: tuple[float, float, float]
    origin_m: tuple[float, float, float]
    positions_m: np.ndarray

    def __post_init__(self):
        shape = tuple(self.shape)
        spacing = tuple(self.spacing_m)
        origin = tuple(self.origin_m)
        sites = frozen_array(self.positions_m)
        if len(shape) != 3 or any(int(n) != n or n < 3 for n in shape):
            raise ValueError("Three integer grid dimensions of at least three required")
        if len(spacing) != 3 or not np.isfinite(spacing).all() or min(spacing) <= 0:
            raise ValueError("Three positive finite spacings required")
        if len(origin) != 3 or not np.isfinite(origin).all():
            raise ValueError("Three finite origin coordinates required")
        if sites.ndim != 2 or sites.shape[1] != 3 or not np.isfinite(sites).all():
            raise ValueError("Finite N-by-3 site coordinates in (z,y,x) required")
        coordinate = (sites - origin) / spacing
        if np.any(coordinate < 0) or np.any(coordinate > np.array(shape) - 1):
            raise ValueError("Sites must lie within the mesh; no extrapolation")
        object.__setattr__(self, "shape", tuple(map(int, shape)))
        object.__setattr__(self, "spacing_m", spacing)
        object.__setattr__(self, "origin_m", origin)
        object.__setattr__(self, "positions_m", sites)

    def weights(self):
        """Rows interpolate mesh potentials to sites; transpose deposits charge."""
        coordinate = (self.positions_m - self.origin_m) / self.spacing_m
        base = np.minimum(np.floor(coordinate).astype(int), np.array(self.shape) - 2)
        fraction = coordinate - base
        rows, columns, values = [], [], []
        for offset in product((0, 1), repeat=3):
            weight = np.prod(np.where(offset, fraction, 1 - fraction), axis=1)
            keep = weight > 0
            rows.extend(np.flatnonzero(keep))
            columns.extend(np.ravel_multi_index((base[keep] + offset).T, self.shape))
            values.extend(weight[keep])
        return coo_matrix(
            (values, (rows, columns)), shape=(len(coordinate), np.prod(self.shape))
        ).tocsr()

    def sample_potential(self, potential_v):
        potential = np.asarray(potential_v, dtype=float)
        if potential.shape != self.shape or not np.isfinite(potential).all():
            raise ValueError("Finite mesh potential required")
        return frozen_array(self.weights() @ potential.ravel())

    def deposit_charge(self, charge_c, fixed_potential_v):
        """Signed excess charge per site, in coulombs; returns rho in C/m^3.

        Reject any nonzero site's support on an electrode, even when opposite
        charges would cancel there. Reference ionic/background subtraction is
        the caller's physical responsibility. This does not compute occupations.
        """
        charge = np.asarray(charge_c, dtype=float)
        fixed = np.asarray(fixed_potential_v, dtype=float)
        if charge.shape != (len(self.positions_m),) or not np.isfinite(charge).all():
            raise ValueError("One finite signed charge per site required")
        if fixed.shape != self.shape or np.isinf(fixed).any():
            raise ValueError("Fixed-potential map must match the mesh")
        weights = self.weights()
        support = weights[:, np.isfinite(fixed).ravel()].sum(axis=1).A1
        if np.any((charge != 0) & (support > 0)):
            raise ValueError("Charge deposition overlaps a fixed-potential node")
        rho = (weights.T @ charge).reshape(self.shape) / np.prod(self.spacing_m)
        return frozen_array(rho)
