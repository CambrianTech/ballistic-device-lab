"""A working quasistatic circuit stage, independent of the transport backend."""

import json
from dataclasses import asdict, dataclass
from math import isfinite

from ballistic_lab.transport.circuit import CircuitTolerance, CycleResult, sinusoidal_cycle
from physics_layers.stages import Check, Stage


@dataclass(frozen=True)
class DCRequest:
    amplitude_v: float
    load_ohm: float
    phases: int = 32
    voltage_atol_v: float = 1e-9
    power_atol_w: float = 1e-18
    refinement_rtol: float = 1e-3
    circuit_tolerance: CircuitTolerance = CircuitTolerance()

    def __post_init__(self):
        if not isfinite(self.amplitude_v) or self.amplitude_v < 0:
            raise ValueError("Finite nonnegative peak amplitude required")
        if not isfinite(self.load_ohm) or self.load_ohm <= 0:
            raise ValueError("Finite positive load required")
        if type(self.phases) is not int or self.phases < 8 or self.phases % 2:
            raise ValueError("Even integer phase count >= 8 required")
        for value in (self.voltage_atol_v, self.power_atol_w, self.refinement_rtol):
            if not isfinite(value) or value <= 0:
                raise ValueError("Finite positive refinement tolerances required")


@dataclass(frozen=True)
class RefinedCycle:
    coarse: CycleResult
    refined: CycleResult


def dc_stage(request: DCRequest, *, current_stage: str, source_identity: str) -> Stage:
    """Consume a validated TerminalCurrentModel; double phases before acceptance.

    This verifies phase integration only. Energy/mesh convergence belongs to
    the upstream provider. Frequency response requires a different stage.
    Include this request and upstream settings in RunIdentity.operating_conditions.
    """

    def evaluate(identity, inputs):
        model = inputs[current_stage]
        kwargs = dict(tolerance=request.circuit_tolerance)
        coarse = sinusoidal_cycle(
            model, request.amplitude_v, request.load_ohm, phases=request.phases, **kwargs
        )
        refined = sinusoidal_cycle(
            model, request.amplitude_v, request.load_ohm, phases=2 * request.phases, **kwargs
        )
        return RefinedCycle(coarse, refined)

    def convergence(result):
        for field, atol in (
            ("dc_output_v", request.voltage_atol_v),
            ("dc_load_power_w", request.power_atol_w),
            ("total_load_power_w", request.power_atol_w),
            ("mean_input_power_w", request.power_atol_w),
            ("mean_device_power_w", request.power_atol_w),
        ):
            coarse, fine = getattr(result.coarse, field), getattr(result.refined, field)
            if not isfinite(coarse) or not isfinite(fine):
                raise ValueError(f"Nonfinite cycle observable: {field}")
            if abs(coarse - fine) > atol + request.refinement_rtol * abs(fine):
                raise ValueError(f"Phase refinement failed: {field}")

    return Stage(
        "quasistatic_dc",
        source_identity,
        (
            "Memoryless four-terminal current provider; peak sinusoidal drive",
            "Resistive output load; no electromagnetic or frequency-response claim",
            "Phase refinement does not validate upstream transport physics",
        ),
        (current_stage,),
        evaluate,
        (Check("phase_doubling", convergence),),
        configuration_json=json.dumps(asdict(request)),
    )
