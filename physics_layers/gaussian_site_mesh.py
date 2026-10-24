"""Opt-in finite Gaussian site charge; not a calibrated carbon orbital model."""

from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix

from .site_mesh import SiteMeshMap


@dataclass(frozen=True, slots=True)
class GaussianSiteMeshMap(SiteMeshMap):
    """Node-sampled Gaussian, cut off per axis and normalized per site.

    The complete cutoff box must fit inside the mesh: no boundary clipping.
    Deposition and averaging share weights, preserving charge and adjoint work.
    Width and cutoff are explicit model assumptions; no self-energy subtraction.
    """

    sigma_m: float
    cutoff_sigma: float = 5.0

    def __post_init__(self):
        SiteMeshMap.__post_init__(self)
        if not np.isfinite(self.sigma_m) or self.sigma_m <= 0:
            raise ValueError("Positive finite Gaussian width required")
        if not np.isfinite(self.cutoff_sigma) or self.cutoff_sigma < 3:
            raise ValueError("Finite cutoff of at least three sigma required")
        if max(self.spacing_m) > self.sigma_m:
            raise ValueError("Resolve Gaussian width with spacing no larger than sigma")
        radius = self.sigma_m * self.cutoff_sigma
        lower = self.positions_m - radius
        upper = self.positions_m + radius
        boundary = np.asarray(self.origin_m) + (np.asarray(self.shape) - 1) * self.spacing_m
        if np.any(lower < self.origin_m) or np.any(upper > boundary):
            raise ValueError("Complete Gaussian cutoff support must fit inside mesh")

    def weights(self):
        rows, columns, values = [], [], []
        for site, position in enumerate(self.positions_m):
            coordinate = (position - self.origin_m) / self.spacing_m
            radius = self.cutoff_sigma * self.sigma_m / np.asarray(self.spacing_m)
            axes = [
                np.arange(int(np.ceil(c - r)), int(np.floor(c + r)) + 1)
                for c, r in zip(coordinate, radius)
            ]
            indices = np.array(np.meshgrid(*axes, indexing="ij")).reshape(3, -1)
            displacement = (indices.T - coordinate) * self.spacing_m / self.sigma_m
            weight = np.exp(-0.5 * np.sum(displacement**2, axis=1))
            weight /= weight.sum()
            rows.extend([site] * len(weight))
            columns.extend(np.ravel_multi_index(indices, self.shape))
            values.extend(weight)
        return coo_matrix(
            (values, (rows, columns)), shape=(len(self.positions_m), np.prod(self.shape))
        ).tocsr()
