"""Independent DC-score audit: pair currents, Gaussian quadrature, least squares.

For reciprocal spectra only. This intentionally does not call the production
conductance builder, finite-bias current provider, load root, or cycle average.
It checks implementation agreement within the same fixed-potential physics.
"""

from dataclasses import dataclass
from itertools import combinations

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import least_squares
from scipy.special import expit


@dataclass(frozen=True, slots=True)
class PairCurrentOracle:
    energies: np.ndarray
    weighted_pairs: np.ndarray
    fermi_ev: float = 0.9
    temperature_k: float = 300.0

    @classmethod
    def from_spectrum(cls, spectrum, fermi_ev=0.9, temperature_k=300.0):
        energy = np.array([r["energy_ev"] for r in spectrum])
        transmission = np.array([r["transmission"] for r in spectrum])
        if np.max(abs(transmission - transmission.transpose(0, 2, 1))) > 1e-7:
            raise ValueError("Oracle requires reciprocal transport")
        nodes, weights = leggauss(8)
        fraction = (nodes + 1) / 2
        width = np.diff(energy)
        sample = (energy[:-1, None] + width[:, None] * fraction).reshape(-1)
        pairs = []
        for i, j in combinations(range(4), 2):
            t = (transmission[:, i, j] + transmission[:, j, i]) / 2
            value = t[:-1, None] * (1 - fraction) + t[1:, None] * fraction
            pairs.append((value * width[:, None] * weights / 2).reshape(-1))
        return cls(sample, np.array(pairs), fermi_ev, temperature_k)

    def currents(self, voltage):
        kt = 1.380649e-23 / 1.602176634e-19 * self.temperature_k
        f = expit((self.fermi_ev + np.asarray(voltage)[None, :] - self.energies[:, None]) / kt)
        result = np.zeros(4)
        prefactor = 2 * (1.602176634e-19) ** 2 / 6.62607015e-34
        for weight, (i, j) in zip(self.weighted_pairs, combinations(range(4), 2), strict=True):
            flow = prefactor * np.sum(weight * (f[:, i] - f[:, j]))
            result[i] += flow
            result[j] -= flow
        return result


def oracle_cycle(model, amplitude=0.01, load=1e4, phases=64):
    outputs = []
    residuals = []
    for phase in np.arange(phases) * 2 * np.pi / phases:
        drive = amplitude * np.sin(phase)

        def residual(x):
            v = np.array([drive / 2, -drive / 2, x[0] * amplitude, x[1] * amplitude])
            current = model.currents(v)
            load_current = (v[2] - v[3]) / load
            return (current[2:] + [load_current, -load_current]) * load / amplitude

        answer = least_squares(residual, [0.0, 0.0], gtol=1e-13, xtol=1e-13, ftol=1e-13)
        error = float(np.max(abs(residual(answer.x)))) * amplitude / load
        if error > 1e-15:
            raise RuntimeError("Independent load solve failed")
        residuals.append(error)
        outputs.append(float((answer.x[1] - answer.x[0]) * amplitude))
    mean = sum(outputs) / phases
    return dict(dc_v=mean, dc_power_w=mean**2 / load, max_kcl_a=max(residuals))
