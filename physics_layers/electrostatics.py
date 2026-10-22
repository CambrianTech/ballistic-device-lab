"""1D variable-permittivity Poisson stage, Dirichlet boundaries, SI units.

Solves -d(epsilon d(phi)/dx)/dx = rho. This is a planar verification layer,
not a 2D graphene charge model or a self-consistent transport solver.
"""

from dataclasses import dataclass

import numpy as np
from scipy.linalg import solve_banded

EPSILON_0 = 8.8541878128e-12


@dataclass(frozen=True, slots=True)
class Poisson1DRequest:
    spacing_m: float
    relative_permittivity_faces: tuple[float, ...]
    charge_density_c_m3: tuple[float, ...]
    boundary_v: tuple[float, float]

    def __post_init__(self):
        for key in ("relative_permittivity_faces", "charge_density_c_m3", "boundary_v"):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        eps = np.asarray(self.relative_permittivity_faces)
        rho = np.asarray(self.charge_density_c_m3)
        if (
            rho.ndim != 1
            or len(rho) < 3
            or eps.shape != (len(rho) - 1,)
            or len(self.boundary_v) != 2
            or not np.isfinite(self.spacing_m)
            or self.spacing_m <= 0
            or not np.isfinite(eps).all()
            or np.any(eps <= 0)
            or not np.isfinite(rho).all()
            or not np.isfinite(self.boundary_v).all()
        ):
            raise ValueError("Invalid uniform mesh, face permittivity, charge or boundaries")


@dataclass(frozen=True, slots=True)
class Poisson1DResult:
    potential_v: tuple[float, ...]
    electric_field_v_m: tuple[float, ...]
    residual_c_m3: float


class Poisson1DStage:
    def evaluate(self, request: Poisson1DRequest) -> Poisson1DResult:
        eps = EPSILON_0 * np.array(request.relative_permittivity_faces)
        h = request.spacing_m
        rho = np.array(request.charge_density_c_m3)
        n = len(rho) - 2
        bands = np.zeros((3, n))
        bands[1] = (eps[:-1] + eps[1:]) / h**2
        bands[0, 1:] = -eps[1:-1] / h**2
        bands[2, :-1] = -eps[1:-1] / h**2
        rhs = rho[1:-1].copy()
        rhs[0] += eps[0] * request.boundary_v[0] / h**2
        rhs[-1] += eps[-1] * request.boundary_v[1] / h**2
        phi = np.r_[request.boundary_v[0], solve_banded((1, 1), bands, rhs), request.boundary_v[1]]
        field = -np.diff(phi) / h
        residual = np.diff(eps * field) / h - rho[1:-1]
        return Poisson1DResult(tuple(phi), tuple(field), float(np.max(abs(residual))))
