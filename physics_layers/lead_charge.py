"""Dense finite-band NEGF charge using actual Kwant lead self energies.

Verification-scale backend: one orbital per site, static noninteracting leads.
Continuum spectral weight must close on every site. Missing bound states or an
inadequate energy interval fail closed; no fictitious broadening fills the gap.
"""

import numpy as np
from scipy.constants import Boltzmann, elementary_charge, h
from scipy.integrate import quad_vec
from scipy.optimize import minimize_scalar
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
        self.system = system
        self.thresholds = self._band_thresholds()

    def _band_thresholds(self):
        """Locate lead subband extrema to partition real-energy quadrature.

        Dense momentum sampling seeds bounded scalar refinement. Completeness
        still relies on the integrated spectral sum rule, not this locator.
        """
        import kwant

        values = list(self.bounds)
        momenta = np.linspace(-np.pi, np.pi, 257)
        for lead, offset in zip(self.leads, self.lead_shifts):
            bands = kwant.physics.Bands(lead)
            sampled = np.array([bands(k) for k in momenta])
            values.extend(sampled[0] + offset)
            values.extend(sampled[128] + offset)
            for band in range(sampled.shape[1]):
                for i in range(1, len(momenta) - 1):
                    left, middle, right = sampled[i - 1 : i + 2, band]
                    if (middle < left and middle <= right) or (middle > left and middle >= right):
                        sign = 1 if middle < left else -1
                        result = minimize_scalar(
                            lambda k: sign * bands(k)[band],
                            bounds=(momenta[i - 1], momenta[i + 1]),
                            method="bounded",
                            options={"xatol": 1e-13},
                        )
                        values.append(sign * result.fun + offset)
        ordered = sorted(
            0.0 if abs(v) < 1e-12 else v for v in values if self.bounds[0] <= v <= self.bounds[1]
        )
        unique = [ordered[0]]
        for value in ordered[1:]:
            if value - unique[-1] > 1e-8:
                unique.append(value)
        return tuple(unique)

    def spectral(self, energy_ev, onsite_shift_ev):
        """Flux-normalized scattering states avoid surface self-energy poles."""
        import kwant

        shift = np.asarray(onsite_shift_ev, float)
        if shift.shape != (len(self.hamiltonian),) or not np.isfinite(shift).all():
            raise ValueError("One finite shift per site required")
        original = self.system

        class ShiftedLead(kwant.system.InfiniteSystem):
            def __init__(self, source, offset):
                self.__dict__.update(source.__dict__)
                self.source, self.offset = source, offset

            def hamiltonian(self, i, j, *args, params=None):
                return self.source.hamiltonian(i, j, *args, params=params) + (
                    self.offset if i == j else 0
                )

        class ShiftedSystem(kwant.system.FiniteSystem):
            def __init__(self):
                self.__dict__.update(original.__dict__)

            def hamiltonian(self, i, j, *args, params=None):
                return original.hamiltonian(i, j, *args, params=params) + (
                    shift[i] if i == j else 0
                )

        system = ShiftedSystem()
        system.leads = [
            ShiftedLead(lead, offset) for lead, offset in zip(self.leads, self.lead_shifts)
        ]
        waves = kwant.wave_function(system, energy_ev)
        density = np.array(
            [np.sum(abs(waves(a)) ** 2, axis=0) / (2 * np.pi) for a in range(len(self.leads))]
        )
        scattering = kwant.smatrix(system, energy_ev)
        transmission = np.array(
            [
                [scattering.transmission(a, b) for b in range(len(self.leads))]
                for a in range(len(self.leads))
            ]
        )
        if not np.isfinite(density).all() or not np.isfinite(transmission).all():
            raise ArithmeticError("Nonfinite scattering-state charge")
        return density, transmission

    def spectral_dense(self, energy_ev, onsite_shift_ev):
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

        values = np.zeros(2 * n + len(mus))
        error = 0.0
        for low, high in zip(self.thresholds[:-1], self.thresholds[1:]):
            center, radius = (low + high) / 2, (high - low) / 2

            def transformed(theta):
                # Resolve each subband edge without fictitious lifetime broadening.
                return integrand(center + radius * np.sin(theta)) * radius * np.cos(theta)

            part, err, info = quad_vec(
                transformed,
                -np.pi / 2,
                np.pi / 2,
                epsabs=tolerance / (len(self.thresholds) - 1),
                epsrel=tolerance,
                points=[
                    np.arcsin((m - center) / radius) for m in mus if low + 1e-8 < m < high - 1e-8
                ],
                full_output=True,
                limit=2000,
            )
            if not info.success or not np.isfinite(part).all():
                raise ArithmeticError("Finite-band charge integration failed")
            values += part
            error += err
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
