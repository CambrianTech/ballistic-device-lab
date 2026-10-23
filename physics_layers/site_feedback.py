"""Site-resolved reservoir charge coupled to a 3D electrostatic mesh.

The provider owns quantum charge physics, energy integration and bound states.
This module owns signed charge deposition, potential feedback and outer residuals.
"""

from dataclasses import dataclass, replace
from typing import Protocol

import numpy as np
from scipy.constants import elementary_charge

from .negf_reference import ReservoirResult
from .poisson3d import Poisson3DRequest, Poisson3DResult, Poisson3DStage
from .site_mesh import SiteMeshMap


class SiteTransport(Protocol):
    def solve(
        self, onsite_shift_ev, chemical_potentials_ev, temperature_k, *, tolerance
    ) -> ReservoirResult: ...


@dataclass(frozen=True)
class FeedbackPlan:
    mixing: float = 0.2
    max_iterations: int = 300
    potential_tolerance_v: float = 1e-8
    occupation_tolerance: float = 1e-8
    quadrature_tolerance: float = 1e-10

    def __post_init__(self):
        if not np.isfinite(self.mixing) or not 0 < self.mixing <= 1:
            raise ValueError("Mixing must be in (0,1]")
        if type(self.max_iterations) is not int or self.max_iterations < 1:
            raise ValueError("Positive integer iteration limit required")
        if not all(
            np.isfinite(v) and v > 0
            for v in (
                self.potential_tolerance_v,
                self.occupation_tolerance,
                self.quadrature_tolerance,
            )
        ):
            raise ValueError("Finite positive tolerances required")


@dataclass(frozen=True)
class FeedbackStep:
    potential_residual_v: float
    occupation_residual: float


@dataclass(frozen=True)
class FeedbackResult:
    field: Poisson3DResult
    transport: ReservoirResult
    site_potential_v: tuple[float, ...]
    excess_charge_c: tuple[float, ...]
    history: tuple[FeedbackStep, ...]


class FeedbackFailure(ArithmeticError):
    def __init__(self, history):
        self.history = tuple(history)
        super().__init__(f"Site/Poisson feedback failed after {len(history)} iterations")


def solve_site_feedback(
    mesh: Poisson3DRequest,
    mapping: SiteMeshMap,
    provider: SiteTransport,
    reference_electrons,
    chemical_potentials_ev,
    temperature_k: float,
    plan: FeedbackPlan = FeedbackPlan(),
) -> FeedbackResult:
    """Iterate q=-e(n-n_ref), Poisson(phi), then U_electron[eV]=-phi[V].

    Mesh rho is an explicit fixed background, added to site excess charge. The
    reference must be calibrated by the caller; it is never inferred from current.
    The returned transport is recomputed at the returned potential. Its charge
    differs from Poisson's last RHS only by the reported occupation residual.
    This is a mesh-regularized Hartree model, not atomistic Coulomb calibration.
    """
    nsites = len(mapping.positions_m)
    reference = np.asarray(reference_electrons, dtype=float)
    if (
        reference.shape != (nsites,)
        or not np.isfinite(reference).all()
        or np.any(reference < 0)
        or mapping.shape != mesh.charge_density_c_m3.shape
        or mapping.spacing_m != mesh.spacing_m
    ):
        raise ValueError("Compatible mesh/map and finite nonnegative reference required")
    # Detect electrode overlap before the initial solve even for neutral sites.
    mapping.deposit_charge(np.full(nsites, elementary_charge), mesh.fixed_potential_v)
    poisson = Poisson3DStage()
    field = poisson.evaluate(mesh)
    phi = field.potential_v.copy()
    history = []

    def transport(potential):
        site_phi = mapping.sample_potential(potential)
        result = provider.solve(
            -site_phi,
            chemical_potentials_ev,
            temperature_k,
            tolerance=plan.quadrature_tolerance,
        )
        occupations = np.asarray(result.electrons_per_site)
        if occupations.shape != reference.shape or not np.isfinite(occupations).all():
            raise ValueError("Invalid site occupations from provider")
        return result, occupations

    current, occupations = transport(phi)
    for _ in range(plan.max_iterations):
        charge = -elementary_charge * (occupations - reference)
        rho = mesh.charge_density_c_m3 + mapping.deposit_charge(charge, mesh.fixed_potential_v)
        field = poisson.evaluate(replace(mesh, charge_density_c_m3=rho))
        proposed = field.potential_v
        next_transport, next_occupations = transport(proposed)
        step = FeedbackStep(
            float(np.max(abs(proposed - phi))),
            float(np.max(abs(next_occupations - occupations))),
        )
        history.append(step)
        if (
            step.potential_residual_v <= plan.potential_tolerance_v
            and step.occupation_residual <= plan.occupation_tolerance
        ):
            return FeedbackResult(
                field,
                next_transport,
                tuple(mapping.sample_potential(proposed)),
                tuple(-elementary_charge * (next_occupations - reference)),
                tuple(history),
            )
        phi += plan.mixing * (proposed - phi)
        current, occupations = transport(phi)
    raise FeedbackFailure(history)
