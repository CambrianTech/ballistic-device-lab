"""Linear Landauer-Buettiker reservoirs and a passive output resistor.

    I_i = (spin * e^2/h) sum_j (N_i delta_ij - T_ij) V_j

Currents are positive into the device. T[out, in] includes reflection.
Temperature broadens reservoir occupations only; it adds no phonon scattering.
"""

from dataclasses import dataclass

import numpy as np

E_CHARGE = 1.602176634e-19
PLANCK = 6.62607015e-34
KB_EV = 1.380649e-23 / E_CHARGE
G_QUANTUM = E_CHARGE**2 / PLANCK


def conductance_matrix(transmission, modes, spin_degeneracy=2):
    t, n = np.asarray(transmission, float), np.asarray(modes, float)
    if n.ndim != 1 or t.shape != (len(n), len(n)) or len(n) < 2:
        raise ValueError("Transmission must be a square terminal matrix")
    if not np.isfinite(t).all() or not np.isfinite(n).all() or np.any(t < 0) or np.any(n < 0):
        raise ValueError("Transmission and mode counts must be finite and nonnegative")
    if spin_degeneracy not in (1, 2):
        raise ValueError("Declare one spin species or two identical spin species")
    if not np.allclose(t.sum(axis=0), n, atol=1e-7, rtol=0) or not np.allclose(
        t.sum(axis=1), n, atol=1e-7, rtol=0
    ):
        raise ValueError("Transmission violates current conservation or equilibrium")
    return spin_degeneracy * G_QUANTUM * (np.diag(n) - t)


@dataclass(frozen=True, slots=True)
class ThermalRequest:
    fermi_ev: float
    temperature_k: float
    spin_degeneracy: int = 2

    def __post_init__(self):
        if not np.isfinite(self.fermi_ev):
            raise ValueError("Fermi energy must be finite")
        if not np.isfinite(self.temperature_k) or self.temperature_k <= 0:
            raise ValueError("Thermal integration requires positive temperature")
        if self.spin_degeneracy not in (1, 2):
            raise ValueError("Spin degeneracy must be 1 or 2")


def thermal_conductance(spectrum, request: ThermalRequest):
    energies = np.array([row["energy_ev"] for row in spectrum])
    kt = KB_EV * request.temperature_k
    if len(energies) < 3 or not np.isfinite(energies).all() or np.any(np.diff(energies) <= 0):
        raise ValueError("Use an increasing energy grid")
    if energies[0] > request.fermi_ev - 12 * kt or energies[-1] < request.fermi_ev + 12 * kt:
        raise ValueError("Energy window must cover at least +/-12 kBT")
    if np.max(np.diff(energies)) > kt / 4:
        raise ValueError("Grid too coarse for thermal averaging; refine and check convergence")
    x = (energies - request.fermi_ev) / kt
    z = np.exp(-np.abs(x))
    weight = z / (kt * (1 + z) ** 2)
    matrices = np.array(
        [
            conductance_matrix(row["transmission"], row["modes"], request.spin_degeneracy)
            for row in spectrum
        ]
    )
    # Do not normalize away omitted tails; retain the integrated thermal weight.
    mass = float(np.trapezoid(weight, energies))
    return np.trapezoid(matrices * weight[:, None, None], energies, axis=0), mass


@dataclass(frozen=True, slots=True)
class LinearLoadResult:
    terminal_voltages_v: tuple[float, ...]
    terminal_currents_a: tuple[float, ...]
    output_voltage_v: float
    load_power_w: float
    input_power_w: float
    device_power_w: float
    kcl_residual_a: float
    power_residual_w: float


def solve_load(conductance, drive_v: float, load_ohm: float) -> LinearLoadResult:
    """Four contacts L,R,T,B; L/R clamped to +/-drive/2; resistor between B/T.

    This is a linear, quasistatic response. Under sinusoidal drive the output
    voltage is AC, average voltage is zero, and resistor heating is not DC power.
    """
    g = np.asarray(conductance, float)
    if g.shape != (4, 4) or not np.isfinite(g).all():
        raise ValueError("Expected a finite 4x4 conductance matrix in siemens")
    if not np.isfinite(drive_v) or not np.isfinite(load_ohm) or load_ohm <= 0:
        raise ValueError("Finite drive and positive finite load required")
    scale = max(float(np.max(abs(g))), 1e-30)
    if max(np.max(abs(g.sum(axis=0))), np.max(abs(g.sum(axis=1)))) > 1e-7 * scale:
        raise ValueError("Conductance violates conservation or voltage-reference invariance")
    if np.min(np.linalg.eigvalsh((g + g.T) / 2)) < -1e-7 * scale:
        raise ValueError("Nonpassive conductance matrix")
    load = np.array([[1.0, -1.0], [-1.0, 1.0]]) / load_ohm
    block = g[2:, 2:] + load
    if np.linalg.cond(block) > 1e12:
        raise ValueError("Floating output potentials are not uniquely determined")
    voltage = np.zeros(4)
    voltage[:2] = (drive_v / 2, -drive_v / 2)
    voltage[2:] = np.linalg.solve(block, -g[2:, :2] @ voltage[:2])
    current = g @ voltage
    output = voltage[3] - voltage[2]
    p_load = output**2 / load_ohm
    p_input = float(voltage[:2] @ current[:2])
    p_device = float(voltage @ current)
    kcl = float(np.max(abs(current[2:] + load @ voltage[2:])))
    residual = p_input - p_device - p_load
    if abs(residual) > 1e-10 * max(abs(p_input), 1e-30):
        raise RuntimeError("Power balance failed")
    return LinearLoadResult(
        tuple(voltage),
        tuple(current),
        float(output),
        float(p_load),
        p_input,
        p_device,
        kcl,
        float(residual),
    )
