"""Cartesian electrostatics, invariant in z; not a graphene sheet-charge closure.

Arrays use [y, x]. Outer edges and optional internal electrodes are Dirichlet.
Permittivities live on faces so dielectric interfaces have explicit locations.
"""

from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from .electrostatics import EPSILON_0


def _snapshot(value):
    return tuple(tuple(float(v) for v in row) for row in value)


@dataclass(frozen=True, slots=True)
class Poisson2DRequest:
    spacing_x_m: float
    spacing_y_m: float
    relative_permittivity_x: tuple[tuple[float, ...], ...]
    relative_permittivity_y: tuple[tuple[float, ...], ...]
    charge_density_c_m3: tuple[tuple[float, ...], ...]
    fixed_potential_v: tuple[tuple[float, ...], ...]

    def __post_init__(self):
        for name in (
            "relative_permittivity_x",
            "relative_permittivity_y",
            "charge_density_c_m3",
            "fixed_potential_v",
        ):
            object.__setattr__(self, name, _snapshot(getattr(self, name)))
        rho = np.asarray(self.charge_density_c_m3)
        fixed = np.asarray(self.fixed_potential_v)
        ex = np.asarray(self.relative_permittivity_x)
        ey = np.asarray(self.relative_permittivity_y)
        if rho.ndim != 2 or min(rho.shape) < 3:
            raise ValueError("Mesh must have at least three nodes on each axis")
        ny, nx = rho.shape
        if fixed.shape != rho.shape or ex.shape != (ny, nx - 1) or ey.shape != (ny - 1, nx):
            raise ValueError("Charge, electrode and face arrays have incompatible shapes")
        if not all(np.isfinite(h) and h > 0 for h in (self.spacing_x_m, self.spacing_y_m)):
            raise ValueError("Mesh spacings must be finite and positive")
        if not np.isfinite(rho).all() or any(
            not np.isfinite(e).all() or np.any(e <= 0) for e in (ex, ey)
        ):
            raise ValueError("Charge must be finite and permittivity finite and positive")
        if np.isinf(fixed).any() or not all(
            np.isfinite(edge).all() for edge in (fixed[0], fixed[-1], fixed[:, 0], fixed[:, -1])
        ):
            raise ValueError("Outer boundary must be Dirichlet; NaN denotes interior unknowns")


@dataclass(frozen=True, slots=True)
class Poisson2DResult:
    potential_v: tuple[tuple[float, ...], ...]
    electric_field_x_v_m: tuple[tuple[float, ...], ...]
    electric_field_y_v_m: tuple[tuple[float, ...], ...]
    residual_c_m3: float


class Poisson2DStage:
    """Solve -div(epsilon grad(phi))=rho on non-electrode interior nodes.

    Charge specified on fixed nodes is ignored: electrodes impose potential.
    Residual measures algebraic error, not mesh convergence or model accuracy.
    """

    def evaluate(self, request: Poisson2DRequest) -> Poisson2DResult:
        phi = np.array(request.fixed_potential_v)
        unknown = np.isnan(phi)
        nodes = np.argwhere(unknown)
        index = np.full(phi.shape, -1, dtype=int)
        index[unknown] = np.arange(len(nodes))
        ax = EPSILON_0 * np.array(request.relative_permittivity_x) / request.spacing_x_m**2
        ay = EPSILON_0 * np.array(request.relative_permittivity_y) / request.spacing_y_m**2
        rhs = np.array(request.charge_density_c_m3)[unknown].copy()
        rows, cols, values = [], [], []
        for row, (y, x) in enumerate(nodes):
            diagonal = 0.0
            for yy, xx, weight in (
                (y, x - 1, ax[y, x - 1]),
                (y, x + 1, ax[y, x]),
                (y - 1, x, ay[y - 1, x]),
                (y + 1, x, ay[y, x]),
            ):
                diagonal += weight
                if unknown[yy, xx]:
                    rows.append(row)
                    cols.append(index[yy, xx])
                    values.append(-weight)
                else:
                    rhs[row] += weight * phi[yy, xx]
            rows.append(row)
            cols.append(row)
            values.append(diagonal)
        residual = 0.0
        if len(nodes):
            matrix = coo_matrix((values, (rows, cols)), shape=(len(nodes), len(nodes))).tocsr()
            solution = spsolve(matrix, rhs)
            if not np.isfinite(solution).all():
                raise ArithmeticError("Poisson solution is nonfinite")
            phi[unknown] = solution
            residual = float(np.max(abs(matrix @ solution - rhs)))
        return Poisson2DResult(
            _snapshot(phi),
            _snapshot(-np.diff(phi, axis=1) / request.spacing_x_m),
            _snapshot(-np.diff(phi, axis=0) / request.spacing_y_m),
            residual,
        )
