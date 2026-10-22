"""Small dense wide-band NEGF reference with site-resolved reservoir charge.

Energies in eV; one orbital/site and explicit spin multiplicity. Positive
definite total broadening is required, excluding unoccupied bound-state ambiguity.
This verification backend is deliberately not the graphene-lead production model.
"""

from dataclasses import dataclass

import numpy as np
from scipy.constants import Boltzmann, elementary_charge, h
from scipy.integrate import quad_vec
from scipy.special import expit


@dataclass(frozen=True)
class ReservoirResult:
    electrons_per_site: tuple[float, ...]
    currents_a: tuple[float, ...]
    integration_error: float


class WideBandDevice:
    def __init__(self, hamiltonian_ev, broadenings_ev, spin=2):
        self.hamiltonian = np.array(hamiltonian_ev, dtype=complex, copy=True)
        self.gammas = np.array(broadenings_ev, dtype=complex, copy=True)
        n = self.hamiltonian.shape[0] if self.hamiltonian.ndim == 2 else 0
        if (
            not n
            or self.hamiltonian.shape != (n, n)
            or self.gammas.ndim != 3
            or self.gammas.shape[1:] != (n, n)
        ):
            raise ValueError("Square Hamiltonian and matching reservoir matrices required")
        if not len(self.gammas) or spin not in (1, 2):
            raise ValueError("Reservoirs and explicit spin multiplicity 1 or 2 required")
        for matrix in (self.hamiltonian, *self.gammas):
            if not np.isfinite(matrix).all() or not np.allclose(
                matrix, matrix.conj().T, atol=1e-13, rtol=0
            ):
                raise ValueError("Finite Hermitian matrices required")
        if any(np.linalg.eigvalsh(gamma).min() < -1e-13 for gamma in self.gammas):
            raise ValueError("Reservoir broadenings must be positive semidefinite")
        if np.linalg.eigvalsh(self.gammas.sum(axis=0)).min() <= 1e-12:
            raise ValueError("Reference requires positive definite total broadening")
        self.hamiltonian.flags.writeable = False
        self.gammas.flags.writeable = False
        self.spin = spin

    def solve(self, onsite_shift_ev, chemical_potentials_ev, temperature_k, *, tolerance=1e-8):
        shift = np.asarray(onsite_shift_ev, dtype=float)
        mus = np.asarray(chemical_potentials_ev, dtype=float)
        n = len(self.hamiltonian)
        if (
            shift.shape != (n,)
            or mus.shape != (len(self.gammas),)
            or not np.isfinite(shift).all()
            or not np.isfinite(mus).all()
        ):
            raise ValueError("Finite site shifts and one chemical potential per reservoir required")
        if (
            not np.isfinite(temperature_k)
            or temperature_k <= 0
            or not np.isfinite(tolerance)
            or tolerance <= 0
        ):
            raise ValueError("Positive finite temperature and quadrature tolerance required")
        ham = self.hamiltonian + np.diag(shift)
        gamma = self.gammas.sum(axis=0)
        kt = Boltzmann * temperature_k / elementary_charge

        def integrand(energy):
            green = np.linalg.inv(energy * np.eye(n) - ham + 0.5j * gamma)
            occupations = expit((mus - energy) / kt)
            spectral = np.array([green @ g @ green.conj().T for g in self.gammas])
            density = self.spin * np.einsum("a,aii->i", occupations, spectral).real / (2 * np.pi)
            transmission = np.array([[np.trace(g @ a).real for a in spectral] for g in self.gammas])
            # Spectral current in eV; scale to amperes after integration so the
            # quadrature norm does not discard currents relative to occupations.
            current = np.sum(transmission * (occupations[:, None] - occupations[None, :]), axis=1)
            return np.r_[density, current]

        points = sorted(set([*mus, *np.linalg.eigvalsh(ham)]))
        values, error, info = quad_vec(
            integrand,
            -np.inf,
            np.inf,
            points=points,
            epsabs=tolerance,
            epsrel=tolerance,
            full_output=True,
        )
        if not info.success or not np.isfinite(values).all():
            raise ArithmeticError("NEGF quadrature failed")
        if np.any(values[:n] < -10 * tolerance) or np.any(values[:n] > self.spin + 10 * tolerance):
            raise ArithmeticError("Occupation outside allowed range")
        currents = values[n:] * self.spin * elementary_charge**2 / h
        if abs(currents.sum()) > 10 * tolerance * self.spin * elementary_charge**2 / h:
            raise ArithmeticError("Terminal current conservation failed")
        return ReservoirResult(tuple(values[:n]), tuple(currents), float(error))


@dataclass(frozen=True)
class HartreeResult:
    onsite_shift_ev: tuple[float, ...]
    transport: ReservoirResult
    residual_history_ev: tuple[float, ...]


def solve_hartree(
    device,
    chemical_potentials_ev,
    temperature_k,
    reference_electrons,
    interaction_ev,
    external_shift_ev,
    *,
    mixing=0.2,
    tolerance_ev=1e-7,
    max_iterations=300,
    quadrature_tolerance=1e-9,
):
    """U=U_external+K(n-n_reference); K is an explicit capacitance surrogate.

    Positive K raises electron energy on electron accumulation (screening).
    It must ultimately be replaced by the device's electrostatic Green operator.
    """
    n = len(device.hamiltonian)
    kernel = np.asarray(interaction_ev, float)
    reference = np.asarray(reference_electrons, float)
    external = np.asarray(external_shift_ev, float)
    if kernel.shape != (n, n) or reference.shape != (n,) or external.shape != (n,):
        raise ValueError("Hartree arrays must match sites")
    if not all(np.isfinite(v).all() for v in (kernel, reference, external)) or not np.allclose(
        kernel, kernel.T
    ):
        raise ValueError("Finite arrays and symmetric interaction required")
    if (
        np.linalg.eigvalsh(kernel).min() < -1e-13
        or np.any(reference < 0)
        or np.any(reference > device.spin)
    ):
        raise ValueError("Positive interaction and valid reference occupations required")
    if (
        not np.isfinite(mixing)
        or not 0 < mixing <= 1
        or not np.isfinite(tolerance_ev)
        or tolerance_ev <= 0
    ):
        raise ValueError("Invalid iteration settings")
    if type(max_iterations) is not int or max_iterations < 1:
        raise ValueError("Positive integer iteration limit required")
    shift = external.copy()
    history = []
    for _ in range(max_iterations):
        result = device.solve(
            shift, chemical_potentials_ev, temperature_k, tolerance=quadrature_tolerance
        )
        proposed = external + kernel @ (np.array(result.electrons_per_site) - reference)
        residual = float(np.max(abs(proposed - shift)))
        history.append(residual)
        if residual <= tolerance_ev:
            return HartreeResult(tuple(shift), result, tuple(history))
        shift += mixing * (proposed - shift)
    raise ArithmeticError(f"Hartree iteration failed; final residual {history[-1]:.6g} eV")
