"""Equilibrium ideal Dirac-sheet statistics and planar gate screening.

Spin/valley degeneracy four is included. No edges, disorder or nonequilibrium
reservoir mixture: this is a reference model, not the rectifier charge closure.
See GRAPHENE_CHARGE.md for conventions and scope.
"""

from dataclasses import dataclass

import numpy as np
from scipy.constants import Boltzmann, elementary_charge, hbar
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import expit


@dataclass(frozen=True, slots=True)
class DiracSheet:
    temperature_k: float
    fermi_velocity_m_s: float

    def __post_init__(self):
        if not np.isfinite(self.temperature_k) or self.temperature_k < 0:
            raise ValueError("Temperature must be finite and nonnegative")
        if not np.isfinite(self.fermi_velocity_m_s) or self.fermi_velocity_m_s <= 0:
            raise ValueError("Fermi velocity must be finite and positive")

    def net_density_m2(self, chemical_potential_ev: float) -> float:
        """Electrons minus holes, relative to neutrality; positive for electrons."""
        if not np.isfinite(chemical_potential_ev):
            raise ValueError("Chemical potential must be finite")
        mu = chemical_potential_ev * elementary_charge
        scale = np.pi * (hbar * self.fermi_velocity_m_s) ** 2
        if self.temperature_k == 0:
            return float(np.sign(mu) * mu**2 / scale)
        if mu == 0:
            return 0.0
        kt = Boltzmann * self.temperature_k
        eta = abs(mu) / kt
        # Integrate the thermal correction around the exact zero-T sea.
        # The omitted tail begins at 50 kT; odd symmetry is imposed exactly.
        correction, error = quad(
            lambda u: (eta + u) * (expit(-u) - (1.0 if u < 0 else 0.0)),
            -min(eta, 50.0),
            50.0,
            points=[0.0],
            epsabs=1e-10,
            epsrel=1e-10,
        )
        holes, hole_error = quad(lambda x: x * expit(-x - eta), 0, 50, epsabs=1e-10, epsrel=1e-10)
        if max(error, hole_error) > 1e-7 * max(1.0, abs(correction), abs(holes)):
            raise ArithmeticError("Carrier integral failed tolerance")
        return float(np.sign(mu) * (mu**2 + 2 * kt**2 * (correction - holes)) / scale)

    def quantum_capacitance_f_m2(self, chemical_potential_ev: float) -> float:
        """Positive e² d(n-p)/dmu_J, including finite-T neutrality limit."""
        if not np.isfinite(chemical_potential_ev):
            raise ValueError("Chemical potential must be finite")
        mu = abs(chemical_potential_ev) * elementary_charge
        scale = np.pi * (hbar * self.fermi_velocity_m_s) ** 2
        if self.temperature_k == 0:
            return 2 * elementary_charge**2 * mu / scale
        kt = Boltzmann * self.temperature_k
        return float(2 * elementary_charge**2 * (mu + 2 * kt * np.log1p(np.exp(-mu / kt))) / scale)


@dataclass(frozen=True, slots=True)
class GateResult:
    potential_v: float
    chemical_potential_ev: float
    net_density_m2: float
    sheet_charge_c_m2: float
    balance_residual_c_m2: float


def solve_planar_gate(
    sheet: DiracSheet, gate_overdrive_v: float, capacitance_f_m2: float
) -> GateResult:
    """Neutral equilibrium sheet, grounded reservoir, flat-band offset removed.

    mu_eV=phi_V and Cgeo(Vg-phi)=e*n(phi). This includes quantum capacitance;
    treating graphene as a perfect metal instead would set phi=0.
    """
    if (
        not np.isfinite(gate_overdrive_v)
        or not np.isfinite(capacitance_f_m2)
        or capacitance_f_m2 <= 0
    ):
        raise ValueError("Finite gate voltage and positive capacitance required")

    def balance(phi):
        return capacitance_f_m2 * (
            gate_overdrive_v - phi
        ) - elementary_charge * sheet.net_density_m2(phi)

    phi = (
        0.0
        if gate_overdrive_v == 0
        else brentq(balance, min(0.0, gate_overdrive_v), max(0.0, gate_overdrive_v), xtol=1e-14)
    )
    density = sheet.net_density_m2(phi)
    return GateResult(phi, phi, density, -elementary_charge * density, balance(phi))
