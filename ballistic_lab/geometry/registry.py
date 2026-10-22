"""Declarative geometry families with parameter bounds and checked construction."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from ballistic_lab.models import FloatArray, Geometry

GeometryFactory = Callable[[FloatArray], Geometry]


@dataclass(frozen=True, slots=True)
class GeometryFamily:
    name: str
    bounds: tuple[tuple[float, float], ...]
    factory: GeometryFactory

    def sample(self, rng: np.random.Generator, count: int) -> FloatArray:
        limits = np.asarray(self.bounds)
        return rng.uniform(limits[:, 0], limits[:, 1], (count, len(limits)))

    def build(self, parameters: FloatArray) -> Geometry:
        values = np.asarray(parameters, dtype=np.float64)
        if values.shape != (len(self.bounds),) or not np.isfinite(values).all():
            raise ValueError(f"{self.name}: expected {len(self.bounds)} finite parameters")
        # Bounds define the search region, not a hard construction boundary:
        # tolerance studies may deliberately perturb outside the search box.
        return self.factory(values)


FAMILIES: dict[str, GeometryFamily] = {}


def geometry_family(
    name: str, bounds: tuple[tuple[float, float], ...]
) -> Callable[[GeometryFactory], GeometryFactory]:
    """Register a factory while preserving its signature and callable identity."""

    def register(factory: GeometryFactory) -> GeometryFactory:
        if name in FAMILIES:
            raise ValueError(f"Geometry family already registered: {name}")
        FAMILIES[name] = GeometryFamily(name, bounds, factory)
        return factory

    return register
