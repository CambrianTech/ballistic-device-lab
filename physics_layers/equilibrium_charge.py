"""Equilibrium full-spectrum charge, including bound states, on Matsubara poles.

Finite-temperature contour sum with isolated-device tail subtraction. Imaginary
frequencies are quadrature poles, not a physical lifetime or damping parameter.
"""

import numpy as np
from scipy.constants import Boltzmann, elementary_charge
from scipy.special import expit

from .negf_reference import ReservoirResult


def surface_selfenergy(lead, z, *, tolerance=1e-13):
    """Principal-layer decimation for Im(z)>0; returns interface self energy."""
    if not np.isfinite(z) or z.imag <= 0:
        raise ValueError("Upper-half-plane energy required")
    cell = np.array(lead.cell_hamiltonian(), complex)
    hopping = np.array(lead.inter_cell_hopping(), complex)
    n, m = hopping.shape
    padded = np.zeros((n, n), complex)
    padded[:, :m] = hopping
    a, b = padded.conj().T, padded
    bulk, surface = cell.copy(), cell.copy()
    identity = np.eye(n)
    for _ in range(100):
        green = np.linalg.inv(z * identity - bulk)
        agb, bga = a @ green @ b, b @ green @ a
        surface += agb
        bulk += agb + bga
        a, b = a @ green @ a, b @ green @ b
        if max(np.linalg.norm(a), np.linalg.norm(b)) < tolerance:
            gsurface = np.linalg.inv(z * identity - surface)
            return hopping.conj().T @ gsurface @ hopping
    raise ArithmeticError("Surface decimation did not converge")


class EquilibriumChargeDevice:
    def __init__(self, system, *, lead_shifts_ev=None, spin=2, max_poles=32768):
        self.hamiltonian = np.array(system.hamiltonian_submatrix(), complex)
        self.leads = tuple(system.leads)
        self.interfaces = tuple(np.array(x, int) for x in system.lead_interfaces)
        self.lead_shifts = (
            np.zeros(len(self.leads)) if lead_shifts_ev is None else np.array(lead_shifts_ev, float)
        )
        self.spin, self.max_poles = spin, max_poles
        self._selfenergies = {}
        if (
            self.hamiltonian.shape != (system.graph.num_nodes,) * 2
            or spin not in (1, 2)
            or not np.isfinite(self.hamiltonian).all()
            or not np.allclose(self.hamiltonian, self.hamiltonian.conj().T)
            or self.lead_shifts.shape != (len(self.leads),)
            or not np.isfinite(self.lead_shifts).all()
            or not self.leads
            or type(max_poles) is not int
            or max_poles < 128
        ):
            raise ValueError("Finite one-orbital Hermitian system and valid leads required")

        self.hamiltonian.flags.writeable = False
        self.lead_shifts.flags.writeable = False

    def solve(self, onsite_shift_ev, chemical_potentials_ev, temperature_k, *, tolerance=1e-8):
        shift, mus = np.asarray(onsite_shift_ev, float), np.asarray(chemical_potentials_ev, float)
        n = len(self.hamiltonian)
        if (
            shift.shape != (n,)
            or mus.shape != (len(self.leads),)
            or not np.isfinite(shift).all()
            or not np.isfinite(mus).all()
            or not np.isfinite(temperature_k)
            or temperature_k <= 0
            or not np.isfinite(tolerance)
            or tolerance <= 0
        ):
            raise ValueError(
                "Finite shifts, reservoir potentials, positive temperature and tolerance required"
            )
        if np.max(abs(mus - mus[0])) > 1e-14:
            raise ValueError("Equilibrium provider requires equal reservoir chemical potentials")
        kt = Boltzmann * temperature_k / elementary_charge
        ham = self.hamiltonian + np.diag(shift)
        energies, vectors = np.linalg.eigh(ham)
        density = (abs(vectors) ** 2) @ expit((mus[0] - energies) / kt)
        identity = np.eye(n)
        correction = np.zeros(n)
        previous = None
        successes = 0
        for start in range(0, self.max_poles, 64):
            poles = np.arange(start, min(start + 64, self.max_poles))
            zs = mus[0] + 1j * (2 * poles + 1) * np.pi * kt
            sigmas = np.zeros((len(zs), n, n), complex)
            for index, z in enumerate(zs):
                for port, (lead, ids, offset) in enumerate(
                    zip(self.leads, self.interfaces, self.lead_shifts)
                ):
                    key = (port, z - offset)
                    if key not in self._selfenergies:
                        self._selfenergies[key] = surface_selfenergy(lead, z - offset)
                    sigmas[index][np.ix_(ids, ids)] += self._selfenergies[key]
            green = np.linalg.inv(zs[:, None, None] * identity - ham - sigmas)
            isolated = (1 / (zs[:, None] - energies)) @ (abs(vectors) ** 2).T
            correction += (
                2 * kt * np.sum((np.diagonal(green, axis1=1, axis2=2) - isolated).real, axis=0)
            )
            count = start + len(zs)
            if count >= 64 and count & (count - 1) == 0:
                electrons = self.spin * (density + correction)
                if previous is not None:
                    error = float(np.max(abs(electrons - previous)))
                    successes = successes + 1 if error < tolerance else 0
                    if successes >= 2:
                        if (
                            electrons.min() < -10 * tolerance
                            or electrons.max() > self.spin + 10 * tolerance
                        ):
                            raise ArithmeticError("Invalid equilibrium occupations")
                        return ReservoirResult(tuple(electrons), (0.0,) * len(mus), error)
                previous = electrons.copy()
        raise ArithmeticError(f"Equilibrium Matsubara charge did not converge: {error:g}")
