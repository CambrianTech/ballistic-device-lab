"""Damped charge/field iteration; charge physics is supplied explicitly.

This coordinator does not supply a graphene density approximation. Providers
must return net volumetric charge on the same mesh, including their declared
reference/background charge, and raise on failed inner solves.
"""

from dataclasses import dataclass, replace
from typing import Protocol

import numpy as np

from .poisson2d import Poisson2DRequest, Poisson2DResult, Poisson2DStage, _snapshot

Grid = tuple[tuple[float, ...], ...]


class ChargeProvider(Protocol):
    def charge_density_c_m3(self, potential_v: Grid) -> Grid: ...


@dataclass(frozen=True, slots=True)
class IterationPlan:
    mixing: float = 0.2
    max_iterations: int = 500
    potential_tolerance_v: float = 1e-8
    charge_tolerance_c_m3: float = 1e-5

    def __post_init__(self):
        if not np.isfinite(self.mixing) or not 0 < self.mixing <= 1:
            raise ValueError("Mixing must lie in (0, 1]")
        if isinstance(self.max_iterations, bool) or not isinstance(self.max_iterations, int):
            raise ValueError("Iteration limit must be an integer")
        if self.max_iterations < 1 or not all(
            np.isfinite(v) and v > 0
            for v in (self.potential_tolerance_v, self.charge_tolerance_c_m3)
        ):
            raise ValueError("Iteration limit and tolerances must be positive")


@dataclass(frozen=True, slots=True)
class IterationRecord:
    iteration: int
    unmixed_potential_residual_v: float
    charge_residual_c_m3: float


@dataclass(frozen=True, slots=True)
class CoupledResult:
    field: Poisson2DResult
    charge_density_c_m3: Grid
    history: tuple[IterationRecord, ...]


class ConvergenceError(RuntimeError):
    def __init__(self, history):
        self.history = tuple(history)
        super().__init__(f"Charge/field iteration failed after {len(history)} iterations")


def solve_charge_field(
    mesh: Poisson2DRequest,
    charge: ChargeProvider,
    initial_potential_v: Grid,
    plan: IterationPlan,
) -> CoupledResult:
    """Return only a converged field, retaining all outer residuals.

    Stop on the UNMIXED update and a second charge evaluation at the proposed
    field. Small mixing alone cannot produce false convergence. Charge mismatch
    plus the Poisson residual bounds the charge-equation residual of the result.
    Fixed-potential nodes are excluded from both outer residual norms.
    The mesh's charge array defines shape only; the provider supplies total rho.
    """
    phi = np.array(initial_potential_v, dtype=float, copy=True)
    fixed = np.array(mesh.fixed_potential_v)
    free = np.isnan(fixed)
    if phi.shape != fixed.shape or not np.isfinite(phi).all():
        raise ValueError("Initial potential must be finite and match the mesh")
    phi[~free] = fixed[~free]
    stage = Poisson2DStage()
    history = []

    def density(potential):
        result = np.array(charge.charge_density_c_m3(_snapshot(potential)), dtype=float)
        if result.shape != phi.shape or not np.isfinite(result).all():
            raise ValueError("Charge provider returned invalid density")
        return result

    rho = density(phi)
    for iteration in range(1, plan.max_iterations + 1):
        field = stage.evaluate(replace(mesh, charge_density_c_m3=_snapshot(rho)))
        proposed = np.array(field.potential_v)
        proposed_rho = density(proposed)
        voltage_error = float(np.max(abs(proposed[free] - phi[free]), initial=0))
        charge_error = float(np.max(abs(proposed_rho[free] - rho[free]), initial=0))
        history.append(IterationRecord(iteration, voltage_error, charge_error))
        if (
            voltage_error <= plan.potential_tolerance_v
            and charge_error <= plan.charge_tolerance_c_m3
        ):
            return CoupledResult(field, _snapshot(proposed_rho), tuple(history))
        phi[free] += plan.mixing * (proposed[free] - phi[free])
        rho = density(phi)
    raise ConvergenceError(history)
