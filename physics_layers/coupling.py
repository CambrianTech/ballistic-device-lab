"""SI-unit interfaces for layered electrostatics and electronic/optical coupling."""

import math
from dataclasses import dataclass
from enum import Enum


class PhasorConvention(Enum):
    PEAK = "peak"
    RMS = "rms"


@dataclass(frozen=True, slots=True)
class TerminalPhasor:
    """Current points INTO the device; voltage and current share a reference plane."""

    voltage_v: complex
    current_a: complex
    frequency_hz: float
    convention: PhasorConvention
    reference_plane: str

    def __post_init__(self):
        values = (
            self.voltage_v.real,
            self.voltage_v.imag,
            self.current_a.real,
            self.current_a.imag,
            self.frequency_hz,
        )
        if not all(math.isfinite(v) for v in values) or self.frequency_hz <= 0:
            raise ValueError("Finite phasors and positive frequency required")
        if not isinstance(self.convention, PhasorConvention) or not self.reference_plane:
            raise ValueError("Explicit convention and reference plane required")

    @property
    def average_power_w(self):
        factor = 0.5 if self.convention is PhasorConvention.PEAK else 1.0
        return factor * (self.voltage_v * self.current_a.conjugate()).real


@dataclass(frozen=True, slots=True)
class PassiveOpticalBudget:
    """One passive optical stage; absorbed includes power delivered to its detector."""

    incident_w: float
    reflected_w: float
    transmitted_w: float
    absorbed_w: float

    def validate(self, *, absolute_tolerance_w: float, relative_tolerance: float):
        values = (
            self.incident_w,
            self.reflected_w,
            self.transmitted_w,
            self.absorbed_w,
            absolute_tolerance_w,
            relative_tolerance,
        )
        if not all(math.isfinite(v) and v >= 0 for v in values):
            raise ValueError("Finite nonnegative powers and tolerances required")
        error = abs(self.incident_w - self.reflected_w - self.transmitted_w - self.absorbed_w)
        if error > absolute_tolerance_w + relative_tolerance * self.incident_w:
            raise ValueError("Optical power balance failed")
        return error
