"""Existing ray model behind the physics-stage boundary; no new physics."""

from dataclasses import dataclass

import numpy as np

from ballistic_lab.metrics.angular import measure_response
from ballistic_lab.models import RayConfig, TransportBackend
from ballistic_lab.pipeline.contracts import SquareDevice


@dataclass(frozen=True, slots=True)
class RayRequest:
    config: RayConfig
    seeds: tuple[int, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "seeds", tuple(self.seeds))
        if len(self.seeds) < 2 or any(not isinstance(s, int) or s < 0 for s in self.seeds):
            raise ValueError("Use at least two nonnegative integer seed bases")
        # Each evaluation consumes seed and seed+1 for its two injection ports.
        expanded = [s + port for s in self.seeds for port in (0, 1)]
        if len(set(expanded)) != len(expanded):
            raise ValueError("Repeated evaluations must not share injection seeds")
        if self.config.spread != 1:
            raise ValueError("Angular-response stage requires equilibrium spread=1")


@dataclass(frozen=True, slots=True)
class RayResult:
    device_fingerprint: str
    request: RayRequest
    backend: str
    angular_response_by_seed: tuple[float, ...]
    p99_path_over_width_by_seed: tuple[float, ...]
    observable: str = "angular-response derivative, dimensionless (not efficiency)"

    @property
    def mean(self) -> float:
        return float(np.mean(self.angular_response_by_seed))

    @property
    def standard_error(self) -> float:
        """Monte Carlo sampling only; excludes model and fabrication uncertainty."""
        return float(
            np.std(self.angular_response_by_seed, ddof=1) / np.sqrt(len(self.request.seeds))
        )


@dataclass(frozen=True, slots=True)
class RayStage:
    backend: TransportBackend

    def evaluate(self, device: SquareDevice, request: RayRequest) -> RayResult:
        if device.contact_width_fraction != 0.3:
            raise ValueError("Ray backend supports only contact width 0.3W")
        scores, tails = [], []
        for seed in request.seeds:
            response = measure_response([device.geometry()], self.backend, request.config, seed)
            score, tail = float(response.derivative[0]), float(response.p99_path_over_width[0])
            if not np.isfinite([score, tail]).all() or tail < 0:
                raise RuntimeError("Invalid ray result; candidate cannot advance")
            scores.append(score)
            tails.append(tail)
        backend_type = type(self.backend)
        return RayResult(
            device.fingerprint,
            request,
            f"{backend_type.__module__}.{backend_type.__qualname__}",
            tuple(scores),
            tuple(tails),
        )
