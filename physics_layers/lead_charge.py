"""Dense finite-band NEGF charge using actual Kwant lead self energies.

Verification-scale backend: one orbital per site, static noninteracting leads.
Continuum spectral weight must close on every site. Missing bound states or an
inadequate energy interval fail closed; no fictitious broadening fills the gap.
"""

import numpy as np
from scipy.constants import Boltzmann, elementary_charge, h
from scipy.integrate import quad_vec
from scipy.special import expit

from .negf_reference import ReservoirResult


class LeadChargeDevice:
    def __init__(self, system, energy_bounds_ev, *, lead_shifts_ev=None, spin=2):
        self.hamiltonian = np.array(system.hamiltonian_submatrix(), dtype=complex)
        self.leads = tuple(system.leads)
        self.interfaces = tuple(np.array(x, dtype=int) for x in system.lead_interfaces)
        self.bounds = tuple(energy_bounds_ev)
        self.lead_shifts = (
            np.zeros(len(self.leads))
            if lead_shifts_ev is None
            else np.array(lead_shifts_ev, dtype=float, copy=True)
        )
        n = len(self.hamiltonian)
        if (
            not n
            or self.hamiltonian.shape != (n, n)
            or n != system.graph.num_nodes
            or not np.isfinite(self.hamiltonian).all()
            or not np.allclose(self.hamiltonian, self.hamiltonian.conj().T)
            or not self.leads
            or spin not in (1, 2)
            or len(self.bounds) != 2
            or not np.isfinite(self.bounds).all()
            or self.bounds[0] >= self.bounds[1]
            or self.lead_shifts.shape != (len(self.leads),)
            or not np.isfinite(self.lead_shifts).all()
        ):
            raise ValueError(
                "Finite one-orbital Hermitian device, leads and energy interval required"
            )
        self.spin = spin
        self.hamiltonian.flags.writeable = False
        self.lead_shifts.flags.writeable = False

    def spectral(self, energy_ev, onsite_shift_ev):
        """Return injectivity per eV/site/lead and T[outgoing,incoming], per spin."""
        n = len(self.hamiltonian)
        shift = np.asarray(onsite_shift_ev, float)
        if shift.shape != (n,) or not np.isfinite(shift).all() or not np.isfinite(energy_ev):
            raise ValueError("Finite energy and one onsite shift per site required")
        sigmas = []
        for lead, interface, offset in zip(self.leads, self.interfaces, self.lead_shifts):
            local = lead.selfenergy(energy_ev - offset)
            sigma = np.zeros((n, n), complex)
            sigma[np.ix_(interface, interface)] = local
            sigmas.append(sigma)
        gammas = np.array([1j * (s - s.conj().T) for s in sigmas])
        minimum = min(np.linalg.eigvalsh(g).min() for g in gammas)
        if minimum < -1e-9:
            raise ArithmeticError(
                f"Non-passive lead self energy at {energy_ev:.16g} eV: "
                f"minimum broadening eigenvalue {minimum:.6g} eV"
            )
        green = np.linalg.inv(
            energy_ev * np.eye(n) - self.hamiltonian - np.diag(shift) - sum(sigmas)
        )
        spectral = np.array([green @ g @ green.conj().T for g in gammas])
        density = np.diagonal(spectral, axis1=1, axis2=2).real / (2 * np.pi)
        transmission = np.array([[np.trace(g @ a).real for a in spectral] for g in gammas])
        if not np.isfinite(density).all() or density.min() < -1e-9:
            raise ArithmeticError("Invalid continuum spectral density")
        return density, transmission

    def solve(self, onsite_shift_ev, chemical_potentials_ev, temperature_k, *, tolerance=1e-8):
        mus = np.asarray(chemical_potentials_ev, float)
        if (
            mus.shape != (len(self.leads),)
            or not np.isfinite(mus).all()
            or not np.isfinite(temperature_k)
            or temperature_k <= 0
            or not np.isfinite(tolerance)
            or not 0 < tolerance < 1e-2
        ):
            raise ValueError(
                "Finite reservoir potentials, positive temperature and tolerance required"
            )
        n = len(self.hamiltonian)
        kt = Boltzmann * temperature_k / elementary_charge

        def integrand(energy):
            density, transmission = self.spectral(energy, onsite_shift_ev)
            f = expit((mus - energy) / kt)
            # Incoming minus outgoing, allowing nonreciprocal T conventions.
            current = transmission.sum(axis=0) * f - transmission @ f
            return np.r_[f @ density, density.sum(axis=0), current]

        center = sum(self.bounds) / 2
        radius = (self.bounds[1] - self.bounds[0]) / 2

        def transformed(theta):
            # Remove square-root endpoint singularities without adding lifetime
            # broadening or deleting occupied band-edge spectral weight.
            return integrand(center + radius * np.sin(theta)) * radius * np.cos(theta)

        values, error, info = quad_vec(
            transformed,
            -np.pi / 2,
            np.pi / 2,
            epsabs=tolerance,
            epsrel=tolerance,
            points=[
                np.arcsin((m - center) / radius) for m in mus if self.bounds[0] < m < self.bounds[1]
            ],
            full_output=True,
            limit=2000,
        )
        if not info.success or not np.isfinite(values).all():
            raise ArithmeticError("Finite-band charge integration failed")
        if np.max(abs(values[n : 2 * n] - 1)) > 10 * tolerance:
            raise ArithmeticError(
                "Incomplete continuum spectral weight: bound states or energy window"
            )
        electrons = self.spin * values[:n]
        if electrons.min() < -10 * tolerance or electrons.max() > self.spin + 10 * tolerance:
            raise ArithmeticError("Invalid integrated occupation")
        currents = values[2 * n :] * self.spin * elementary_charge**2 / h
        if abs(currents.sum()) > 10 * tolerance * self.spin * elementary_charge**2 / h:
            raise ArithmeticError("Current conservation failed")
        return ReservoirResult(tuple(electrons), tuple(currents), float(error))
