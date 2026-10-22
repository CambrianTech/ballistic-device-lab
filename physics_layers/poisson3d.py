"""SI Cartesian electrostatics; arrays and spacings follow (z, y, x)."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from .electrostatics import EPSILON_0

Array = NDArray[np.float64]


def frozen_array(value) -> Array:
    """Own an immutable snapshot, including protection against setflags."""
    array = np.asarray(value, dtype=float)
    return np.frombuffer(array.tobytes(), dtype=float).reshape(array.shape)


@dataclass(frozen=True, slots=True)
class Poisson3DRequest:
    spacing_m: tuple[float, float, float]
    relative_permittivity_faces: tuple[Array, Array, Array]
    charge_density_c_m3: Array
    fixed_potential_v: Array

    def __post_init__(self):
        spacing = tuple(float(h) for h in self.spacing_m)
        rho = frozen_array(self.charge_density_c_m3)
        fixed = frozen_array(self.fixed_potential_v)
        faces = tuple(frozen_array(e) for e in self.relative_permittivity_faces)
        if len(spacing) != 3 or not all(np.isfinite(h) and h > 0 for h in spacing):
            raise ValueError("Three positive finite spacings required")
        if rho.ndim != 3 or min(rho.shape) < 3 or fixed.shape != rho.shape:
            raise ValueError("Compatible 3D arrays with at least three nodes per axis required")
        if len(faces) != 3 or not np.isfinite(rho).all() or np.isinf(fixed).any():
            raise ValueError("Finite charge, finite-or-NaN potentials and three face maps required")
        for axis, epsilon in enumerate(faces):
            shape = list(rho.shape)
            shape[axis] -= 1
            if (
                epsilon.shape != tuple(shape)
                or not np.isfinite(epsilon).all()
                or np.any(epsilon <= 0)
            ):
                raise ValueError("Face permittivity must have matching shape and be positive")
            if not np.isfinite(np.take(fixed, [0, -1], axis=axis)).all():
                raise ValueError("All outer faces must specify Dirichlet potentials")
        if np.any(rho[np.isfinite(fixed)] != 0):
            raise ValueError("Prescribed charge on electrodes would be discarded")
        object.__setattr__(self, "spacing_m", spacing)
        object.__setattr__(self, "charge_density_c_m3", rho)
        object.__setattr__(self, "fixed_potential_v", fixed)
        object.__setattr__(self, "relative_permittivity_faces", faces)


@dataclass(frozen=True, slots=True)
class Poisson3DResult:
    potential_v: Array
    electric_field_faces_v_m: tuple[Array, Array, Array]
    residual_c_m3: float


class Poisson3DStage:
    """Solve -div(epsilon grad(phi)) = rho; finite-volume seven-point stencil."""

    def evaluate(self, request: Poisson3DRequest) -> Poisson3DResult:
        phi = request.fixed_potential_v.copy()
        unknown = np.isnan(phi)
        nodes = np.argwhere(unknown)
        indices = np.full(phi.shape, -1, dtype=int)
        indices[unknown] = np.arange(len(nodes))
        rhs = request.charge_density_c_m3[unknown].copy()
        rows, cols, values = [], [], []
        for row, node in enumerate(nodes):
            diagonal = 0.0
            for axis, h in enumerate(request.spacing_m):
                for direction in (-1, 1):
                    neighbor = node.copy()
                    neighbor[axis] += direction
                    face = node.copy()
                    if direction < 0:
                        face[axis] -= 1
                    weight = (
                        EPSILON_0 * request.relative_permittivity_faces[axis][tuple(face)] / h**2
                    )
                    diagonal += weight
                    location = tuple(neighbor)
                    if unknown[location]:
                        rows.append(row)
                        cols.append(indices[location])
                        values.append(-weight)
                    else:
                        rhs[row] += weight * phi[location]
            rows.append(row)
            cols.append(row)
            values.append(diagonal)
        residual = 0.0
        if len(nodes):
            matrix = coo_matrix((values, (rows, cols)), shape=(len(nodes), len(nodes))).tocsr()
            solution = spsolve(matrix, rhs)
            if not np.isfinite(solution).all():
                raise ArithmeticError("Nonfinite Poisson solution")
            phi[unknown] = solution
            residual = float(np.max(abs(matrix @ solution - rhs)))
        fields = tuple(
            frozen_array(-np.diff(phi, axis=a) / h) for a, h in enumerate(request.spacing_m)
        )
        return Poisson3DResult(frozen_array(phi), fields, residual)


def deposit_sheet(
    sigma_c_m2: Array, plane: int, spacing_m: tuple[float, float, float], fixed_potential_v: Array
) -> Array:
    """Deposit an xy sheet on a z node plane: rho=sigma/dz.

    Each nonzero sheet entry represents area dx*dy. No charge may land on
    an electrode. Sum(rho)*dx*dy*dz equals sum(sigma)*dx*dy.
    This is a mesh-aligned sheet, not an atomistic charge interpolation.
    """
    fixed = np.asarray(fixed_potential_v)
    sigma = np.asarray(sigma_c_m2, dtype=float)
    if fixed.ndim != 3 or sigma.shape != fixed.shape[1:] or not np.isfinite(sigma).all():
        raise ValueError("Finite sheet array must match the xy mesh")
    if not isinstance(plane, (int, np.integer)) or not 0 < plane < fixed.shape[0] - 1:
        raise ValueError("Sheet plane must be an interior integer index")
    if len(spacing_m) != 3 or not all(np.isfinite(h) and h > 0 for h in spacing_m):
        raise ValueError("Positive finite spacings required")
    if np.any((sigma != 0) & ~np.isnan(fixed[plane])):
        raise ValueError("Sheet charge overlaps a fixed-potential node")
    rho = np.zeros(fixed.shape)
    rho[plane] = sigma / spacing_m[0]
    return frozen_array(rho)
