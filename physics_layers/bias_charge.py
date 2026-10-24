"""Finite-bias correction to equilibrium charge; explicit bound-state reference.

Verification backend only. Bound states retain Fermi occupation at reference_mu;
this is a chosen closure, not a uniquely determined nonequilibrium occupation.
"""

import numpy as np
from scipy.constants import Boltzmann, elementary_charge, h
from scipy.integrate import quad_vec
from scipy.special import expit

from .equilibrium_charge import EquilibriumChargeDevice
from .lead_charge import LeadChargeDevice
from .negf_reference import ReservoirResult


class BiasChargeDevice:
    def __init__(self, system, *, reference_mu_ev, lead_shifts_ev=None, spin=2):
        if not np.isfinite(reference_mu_ev):
            raise ValueError("Explicit finite bound-state reference required")
        self.reference_mu = float(reference_mu_ev)
        self.equilibrium = EquilibriumChargeDevice(system, lead_shifts_ev=lead_shifts_ev, spin=spin)
        self.continuum = LeadChargeDevice(
            system, (-100, 100), lead_shifts_ev=lead_shifts_ev, spin=spin
        )
        self.spin = spin

    def solve(self, onsite_shift_ev, chemical_potentials_ev, temperature_k, *, tolerance=1e-8):
        mus = np.asarray(chemical_potentials_ev, float)
        ports = len(self.equilibrium.leads)
        if mus.shape != (ports,) or not np.isfinite(mus).all():
            raise ValueError("One finite chemical potential per lead required")
        baseline = self.equilibrium.solve(
            onsite_shift_ev, [self.reference_mu] * ports, temperature_k, tolerance=tolerance / 4
        )
        n = len(baseline.electrons_per_site)
        if np.all(mus == self.reference_mu):
            return baseline
        kt = Boltzmann * temperature_k / elementary_charge
        # Omitted Fermi differences are exponentially small; the occupation tail
        # is bounded using the per-site spectral sum rule. No lifetime broadening.
        margin = max(40.0, np.log(100 * self.spin / tolerance)) * kt
        low, high = min(*mus, self.reference_mu) - margin, max(*mus, self.reference_mu) + margin
        points = sorted(
            set(
                [
                    low,
                    high,
                    *mus,
                    self.reference_mu,
                    *(x for x in self.continuum.thresholds if low < x < high),
                ]
            )
        )

        def integrand(energy):
            density, transmission = self.continuum.spectral(energy, onsite_shift_ev)
            f = expit((mus - energy) / kt)
            delta = f - expit((self.reference_mu - energy) / kt)
            current = transmission.sum(axis=0) * delta - transmission @ delta
            return np.r_[self.spin * (delta @ density), self.spin * current]

        value = np.zeros(n + ports)
        error = 0.0
        for a, b in zip(points[:-1], points[1:]):
            center, radius = (a + b) / 2, (b - a) / 2
            part, err, info = quad_vec(
                lambda theta: integrand(center + radius * np.sin(theta)) * radius * np.cos(theta),
                -np.pi / 2,
                np.pi / 2,
                epsabs=tolerance / (4 * len(points)),
                epsrel=tolerance / 4,
                full_output=True,
                limit=1000,
            )
            if not info.success or not np.isfinite(part).all():
                raise ArithmeticError("Bias-window quadrature failed")
            value += part
            error += err
        electrons = np.asarray(baseline.electrons_per_site) + value[:n]
        currents = value[n:] * elementary_charge**2 / h
        if electrons.min() < -10 * tolerance or electrons.max() > self.spin + 10 * tolerance:
            raise ArithmeticError("Invalid finite-bias occupation")
        if abs(currents.sum()) > 10 * tolerance * elementary_charge**2 / h:
            raise ArithmeticError("Current conservation failed")
        return ReservoirResult(
            tuple(electrons), tuple(currents), float(error + baseline.integration_error)
        )
