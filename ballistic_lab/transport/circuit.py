"""Quasistatic load and cycle accounting for explicit terminal-current models.

The current provider owns its physics and internal convergence. This module
does not turn a linear or frozen-potential model into self-consistent transport.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from scipy.optimize import root


class TerminalCurrentModel(Protocol):
    """Return four currents into the device, in amperes, in L,R,T,B order.

    A model must raise if its internal physics iteration fails to converge.
    Supplies beyond these four terminals require additional power accounting.
    """

    def currents(self, voltages_v: np.ndarray) -> np.ndarray: ...


@dataclass(frozen=True, slots=True)
class CircuitTolerance:
    current_atol_a: float = 1e-15
    current_rtol: float = 1e-8
    root_xtol: float = 1e-9

    def __post_init__(self):
        if any(
            not np.isfinite(v) or v <= 0
            for v in (self.current_atol_a, self.current_rtol, self.root_xtol)
        ):
            raise ValueError("Circuit tolerances must be finite and positive")


@dataclass(frozen=True, slots=True)
class TerminalSolution:
    voltage_v: tuple[float, ...]
    current_a: tuple[float, ...]
    output_v: float
    input_power_w: float
    device_power_w: float
    load_power_w: float
    kcl_residual_a: float
    power_residual_w: float
    output_jacobian_condition: float
    root_reported_success: bool


def solve_terminal_load(
    model: TerminalCurrentModel,
    drive_v: float,
    load_ohm: float,
    *,
    initial_output_v=(0.0, 0.0),
    tolerance=CircuitTolerance(),
) -> TerminalSolution:
    """Solve output KCL for an instantaneous balanced L/R voltage drive.

    Assumes memoryless/quasistatic response; no capacitance, inductance or
    frequency claim. Multiple stable roots require a separate branch analysis.
    """
    initial = np.asarray(initial_output_v, float)
    if not np.isfinite(drive_v) or not np.isfinite(load_ohm) or load_ohm <= 0:
        raise ValueError("Finite drive and positive load required")
    if initial.shape != (2,) or not np.isfinite(initial).all():
        raise ValueError("Two finite initial output voltages required")

    def evaluate(output):
        voltage = np.array([drive_v / 2, -drive_v / 2, *output])
        current = np.asarray(model.currents(voltage), float)
        if current.shape != (4,) or not np.isfinite(current).all():
            raise ValueError("Current provider must return four finite currents")
        limit = tolerance.current_atol_a + tolerance.current_rtol * np.max(abs(current))
        if abs(current.sum()) > limit:
            raise ValueError("Current provider violates terminal conservation")
        load_current = (voltage[2] - voltage[3]) / load_ohm
        residual = current[2:] + np.array([load_current, -load_current])
        return voltage, current, residual, limit

    # Normalize root variables to the applied voltage scale for small signals.
    scale = max(abs(drive_v), float(np.max(abs(initial))), 1e-6)
    answer = root(
        lambda x: evaluate(x * scale)[2] * load_ohm / scale,
        initial / scale,
        options={"xtol": tolerance.root_xtol},
    )
    voltage, current, residual, limit = evaluate(answer.x * scale)
    if np.max(abs(residual)) > limit:
        raise RuntimeError(f"Output load did not converge: {answer.message}")
    # A library stagnation flag can occur at a valid near-zero root. Accept by
    # physical residual, but reject an undetermined floating common-mode voltage.
    step = np.sqrt(np.finfo(float).eps) * scale
    jacobian = np.column_stack(
        [
            (evaluate(voltage[2:] + axis * step)[2] - evaluate(voltage[2:] - axis * step)[2])
            / (2 * step)
            for axis in np.eye(2)
        ]
    )
    condition = float(np.linalg.cond(jacobian))
    if not np.isfinite(condition) or condition > 1e12:
        raise ValueError("Output voltages are not locally uniquely determined")
    output = float(voltage[3] - voltage[2])
    p_in = float(voltage[:2] @ current[:2])
    p_device = float(voltage @ current)
    p_load = output**2 / load_ohm
    error = p_in - p_device - p_load
    power_limit = limit * max(float(np.sum(abs(voltage))), 1e-6)
    if abs(error) > power_limit:
        raise RuntimeError("Terminal/load power balance failed")
    if p_device < -power_limit:
        raise ValueError("Negative device absorption: declare and account for additional supplies")
    return TerminalSolution(
        tuple(voltage),
        tuple(current),
        output,
        p_in,
        p_device,
        p_load,
        float(np.max(abs(residual))),
        float(error),
        condition,
        bool(answer.success),
    )


@dataclass(frozen=True, slots=True)
class CycleResult:
    samples: tuple[TerminalSolution, ...]
    dc_output_v: float
    dc_load_power_w: float
    total_load_power_w: float
    ripple_load_power_w: float
    mean_input_power_w: float
    mean_device_power_w: float
    dc_efficiency: float | None


def sinusoidal_cycle(
    model: TerminalCurrentModel,
    amplitude_v: float,
    load_ohm: float,
    phases: int = 64,
    *,
    tolerance=CircuitTolerance(),
) -> CycleResult:
    """Uniform periodic quadrature; caller must check phase-count convergence.

    DC power is mean(Vout)^2/R, not mean(Vout^2)/R. The latter also includes
    ripple heating. There is no smoothing capacitor in this load model.
    """
    if not isinstance(phases, int) or phases < 8 or phases % 2:
        raise ValueError("Use an even phase count of at least eight")
    if not np.isfinite(amplitude_v) or amplitude_v < 0:
        raise ValueError("Nonnegative finite amplitude required")
    samples = []
    for phase in 2 * np.pi * np.arange(phases) / phases:
        samples.append(
            solve_terminal_load(model, amplitude_v * np.sin(phase), load_ohm, tolerance=tolerance)
        )
    output = np.array([s.output_v for s in samples])
    dc = float(np.mean(output))
    dc_power = dc**2 / load_ohm
    total = float(np.mean(output**2)) / load_ohm
    ripple = float(np.mean((output - dc) ** 2)) / load_ohm
    p_in = float(np.mean([s.input_power_w for s in samples]))
    p_device = float(np.mean([s.device_power_w for s in samples]))
    return CycleResult(
        tuple(samples),
        dc,
        dc_power,
        total,
        ripple,
        p_in,
        p_device,
        dc_power / p_in if p_in > 0 else None,
    )
