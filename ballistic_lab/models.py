"""Typed contracts shared by geometry, transport, and experiments."""

from dataclasses import dataclass
from typing import Protocol, Sequence, TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]
Polygon: TypeAlias = FloatArray
Geometry: TypeAlias = Sequence[Polygon]


@dataclass(frozen=True, slots=True)
class RayConfig:
    """Normalized square cavity; mean free path is in side/2 units."""

    count: int = 8192
    specularity: float = 0.8
    mean_free_path: float | None = 2.0
    spread: float = 1.0

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("Ray count must be positive")
        if not 0 <= self.specularity <= 1 or not 0 <= self.spread <= 1:
            raise ValueError("Specularity and angular spread must lie in [0, 1]")
        if self.mean_free_path is not None and (
            not np.isfinite(self.mean_free_path) or self.mean_free_path <= 0
        ):
            raise ValueError("Mean free path must be finite and positive, or None")


@dataclass(frozen=True, slots=True)
class TraceBatch:
    probabilities: FloatArray
    lengths: FloatArray
    destinations: IntArray
    scatter_counts: IntArray


class TransportBackend(Protocol):
    """Metrics consume this contract, independently of the implementation."""

    def trace(
        self, geometries: Sequence[Geometry], port: int, config: RayConfig, seed: int
    ) -> TraceBatch: ...


@dataclass(frozen=True, slots=True)
class AngularResponse:
    derivative: FloatArray
    p99_path_over_width: FloatArray


@dataclass(frozen=True, slots=True)
class Candidate:
    name: str
    family: str
    parameters: tuple[float, ...]

    def to_record(self) -> dict:
        return {"name": self.name, "family": self.family, "x": list(self.parameters)}


@dataclass(frozen=True, slots=True)
class SearchPlan:
    budget: int = 256
    repeats: int = 3
    training_rays: int = 8192
    validation_rays: int = 65536
    validation_seeds: int = 4
    scattering_ratios: tuple[float, ...] = (0.5, 1.0, 2.0)
    specularities: tuple[float, ...] = (0.5, 0.8, 1.0)

    def __post_init__(self) -> None:
        if min(self.budget, self.repeats, self.training_rays, self.validation_rays) <= 0:
            raise ValueError("Search budgets and ray counts must be positive")
        if self.validation_seeds < 2:
            raise ValueError("At least two validation seeds are required")
        for ratio in self.scattering_ratios:
            for specularity in self.specularities:
                RayConfig(specularity=specularity, mean_free_path=2 * ratio)
