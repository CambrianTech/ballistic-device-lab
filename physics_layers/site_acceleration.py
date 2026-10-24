"""Reduced site-space hybrid root solve with full-grid Poisson verification."""

from dataclasses import replace

import numpy as np
from scipy.constants import elementary_charge
from scipy.optimize import root

from .poisson3d import Poisson3DStage
from .site_feedback import FeedbackFailure, FeedbackResult, FeedbackStep


def solve_accelerated(
    mesh,
    mapping,
    provider,
    reference,
    mus,
    temperature_k,
    *,
    tolerance=1e-6,
    initial_potential_v=None,
):
    """Solve feedback, optionally starting from a nearby bias's site potentials.

    A warm start is only an initial guess; full-grid and charge checks still run.
    It does not establish uniqueness or rule out bias-history dependence.
    """
    reference = np.asarray(reference, float)
    n = len(mapping.positions_m)
    if (
        reference.shape != (n,)
        or not np.isfinite(reference).all()
        or np.any(reference < 0)
        or not np.isfinite(tolerance)
        or tolerance <= 0
        or mapping.shape != mesh.charge_density_c_m3.shape
        or mapping.spacing_m != mesh.spacing_m
    ):
        raise ValueError("One finite nonnegative reference occupation per site required")
    initial = (
        np.zeros(n)
        if initial_potential_v is None
        else np.array(initial_potential_v, float, copy=True)
    )
    if initial.shape != (n,) or not np.isfinite(initial).all():
        raise ValueError("Initial potential must contain one finite voltage per site")
    poisson = Poisson3DStage()
    external = mapping.sample_potential(poisson.evaluate(mesh).potential_v)
    grounded = np.where(np.isfinite(mesh.fixed_potential_v), 0.0, np.nan)
    kernel = np.empty((n, n))
    for j in range(n):
        charge = np.zeros(n)
        charge[j] = elementary_charge
        rho = mapping.deposit_charge(charge, grounded)
        field = poisson.evaluate(replace(mesh, fixed_potential_v=grounded, charge_density_c_m3=rho))
        kernel[:, j] = mapping.sample_potential(field.potential_v)
    history = []

    def residual(phi):
        result = provider.solve(-phi, mus, temperature_k, tolerance=tolerance / 100)
        electrons = np.array(result.electrons_per_site)
        value = phi - external + kernel @ (electrons - reference)
        history.append(FeedbackStep(float(np.max(abs(value))), None))
        return value

    solved = root(
        residual, initial, method="hybr", options={"xtol": tolerance / 100, "maxfev": 300}
    )
    transport = provider.solve(-solved.x, mus, temperature_k, tolerance=tolerance / 100)
    charge = -elementary_charge * (np.array(transport.electrons_per_site) - reference)
    field = poisson.evaluate(
        replace(
            mesh,
            charge_density_c_m3=mesh.charge_density_c_m3
            + mapping.deposit_charge(charge, mesh.fixed_potential_v),
        )
    )
    phi = mapping.sample_potential(field.potential_v)
    checked = provider.solve(-phi, mus, temperature_k, tolerance=tolerance / 100)
    step = FeedbackStep(
        float(np.max(abs(phi - solved.x))),
        float(np.max(abs(np.array(checked.electrons_per_site) - transport.electrons_per_site))),
    )
    history.append(step)
    if not solved.success or max(step.potential_residual_v, step.occupation_residual) > tolerance:
        raise FeedbackFailure(history)
    return FeedbackResult(
        field,
        checked,
        tuple(phi),
        tuple(-elementary_charge * (np.array(checked.electrons_per_site) - reference)),
        tuple(history),
    )
