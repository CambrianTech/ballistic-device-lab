"""Finite reservoir bias with a fixed, externally referenced scattering potential.

This is NOT self-consistent electrostatics. Voltage is electrochemical potential
shift / e; reference_v translates the entire frozen Hamiltonian energy origin.
Energy integration in eV makes the prefactor spin*e^2/h (amperes per eV).
"""

from dataclasses import dataclass

import numpy as np
from scipy.special import expit

from ballistic_lab.transport.reservoirs import KB_EV, ThermalRequest, conductance_matrix


@dataclass(frozen=True, slots=True)
class FrozenPotentialModel:
    energies_ev: np.ndarray
    matrices: np.ndarray
    request: ThermalRequest
    reference_v: float = 0.0

    @classmethod
    def from_spectrum(cls, spectrum, request: ThermalRequest, reference_v: float = 0.0):
        energies = np.array([row["energy_ev"] for row in spectrum], dtype=float)
        if (
            len(energies) < 3
            or not np.isfinite(energies).all()
            or np.any(np.diff(energies) <= 0)
            or np.max(np.diff(energies)) > KB_EV * request.temperature_k / 4
            or not np.isfinite(reference_v)
        ):
            raise ValueError("Finite increasing thermally resolved energy grid required")
        matrices = np.array(
            [
                conductance_matrix(row["transmission"], row["modes"], request.spin_degeneracy)
                for row in spectrum
            ]
        )
        if matrices.shape != (len(energies), 4, 4):
            raise ValueError("Four-terminal spectrum required")
        energies.setflags(write=False)
        matrices.setflags(write=False)
        return cls(energies, matrices, request, reference_v)

    def currents(self, voltages_v: np.ndarray) -> np.ndarray:
        voltage = np.asarray(voltages_v, dtype=float)
        if voltage.shape != (4,) or not np.isfinite(voltage).all():
            raise ValueError("Four finite terminal voltages required")
        mu = self.request.fermi_ev + voltage - self.reference_v
        kt = KB_EV * self.request.temperature_k
        if self.energies_ev[0] > min(mu) - 12 * kt or self.energies_ev[-1] < max(mu) + 12 * kt:
            raise ValueError("Spectrum must cover every biased reservoir plus/minus 12 kBT")
        occupations = expit((mu[None, :] - self.energies_ev[:, None]) / kt)
        # Remove a common occupation before matrix multiplication: equilibrium
        # is exactly zero, without subtracting large filled-band currents.
        differences = occupations - occupations[:, :1]
        integrand = np.einsum("eij,ej->ei", self.matrices, differences)
        return np.trapezoid(integrand, self.energies_ev, axis=0)
