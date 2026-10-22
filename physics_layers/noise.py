"""Low-frequency equilibrium multiterminal thermal noise, one-sided per Hz."""

from dataclasses import dataclass

import numpy as np

KB = 1.380649e-23


@dataclass(frozen=True, slots=True)
class OutputNoise:
    device_v2_per_hz: float
    load_v2_per_hz: float
    total_v2_per_hz: float
    equivalent_resistance_ohm: float

    @property
    def voltage_v_per_root_hz(self):
        return float(np.sqrt(self.total_v2_per_hz))


def equilibrium_output_noise(conductance, temperature_k, load_ohm):
    """L/R ideally voltage clamped; T/B read differentially across a warm load.

    S_I = 2 k_B T (G + G.T). Includes correlated terminal noise and load
    Johnson noise. Excludes amplifier, source impedance, excess driven noise,
    1/f noise and finite-frequency admittance. All elements share temperature.
    """
    g = np.asarray(conductance, dtype=float)
    if g.shape != (4, 4) or not np.isfinite(g).all():
        raise ValueError("Finite four-terminal conductance required")
    if not np.isfinite([temperature_k, load_ohm]).all() or temperature_k <= 0 or load_ohm <= 0:
        raise ValueError("Positive temperature and load required")
    scale = max(float(np.max(abs(g))), 1e-30)
    if max(np.max(abs(g.sum(axis=0))), np.max(abs(g.sum(axis=1)))) > 1e-7 * scale:
        raise ValueError("Conductance must conserve current and be gauge invariant")
    if np.max(abs(g - g.T)) > 1e-7 * scale:
        raise ValueError("This stage requires reciprocal zero-field conductance")
    symmetric = (g + g.T) / 2
    if np.min(np.linalg.eigvalsh(symmetric)) < -1e-7 * scale:
        raise ValueError("Nonpassive conductance")
    difference = np.array([-1.0, 1.0])
    load = np.outer(difference, difference) / load_ohm
    admittance = symmetric[2:, 2:] + load
    if np.min(np.linalg.eigvalsh(admittance)) <= 0 or np.linalg.cond(admittance) > 1e12:
        raise ValueError("Output common mode is ungrounded or ill conditioned")
    transfer = np.linalg.solve(admittance, difference)
    device = float(transfer @ (4 * KB * temperature_k * symmetric[2:, 2:]) @ transfer)
    resistor = float(transfer @ (4 * KB * temperature_k * load) @ transfer)
    resistance = float(difference @ transfer)
    if device < 0 or resistor < 0:
        raise ArithmeticError("Negative noise spectrum")
    return OutputNoise(device, resistor, device + resistor, resistance)
