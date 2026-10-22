"""Shared device identity and generic, physics-specific evaluation stages."""

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from math import isfinite
from typing import Protocol, TypeVar

import numpy as np

from ballistic_lab.models import Geometry

Vertices = tuple[tuple[tuple[float, float], ...], ...]


@dataclass(frozen=True, slots=True)
class SquareDevice:
    """Four centered contacts; obstacles in [-1,1]^2.

    Port order is left, right, top, bottom. Width is optional for normalized
    ray screening, mandatory when a solver needs physical dimensions.
    Materials belong to each solver's explicit configuration, not a default.
    """

    obstacles: Vertices
    width_m: float | None = None
    contact_width_fraction: float = 0.3

    def __post_init__(self) -> None:
        # Copy even caller-supplied mutable arrays into immutable scalar tuples.
        polygons = []
        for polygon in self.obstacles:
            values = np.asarray(polygon, dtype=float)
            if values.ndim != 2 or values.shape[1] != 2 or len(values) < 3:
                raise ValueError("Each obstacle needs at least three 2D vertices")
            if not np.isfinite(values).all() or np.any(abs(values) > 1):
                raise ValueError("Obstacle coordinates must be finite and inside [-1,1]")
            polygons.append(tuple((float(x), float(y)) for x, y in values))
        object.__setattr__(self, "obstacles", tuple(polygons))
        if self.width_m is not None and (not isfinite(self.width_m) or self.width_m <= 0):
            raise ValueError("Physical width must be finite and positive")
        if not 0 < self.contact_width_fraction < 1:
            raise ValueError("Contact width fraction must lie strictly between zero and one")

    @classmethod
    def from_geometry(cls, geometry: Geometry, width_m: float | None = None) -> "SquareDevice":
        return cls(tuple(tuple(map(tuple, polygon)) for polygon in geometry), width_m)

    def geometry(self) -> Geometry:
        """Return fresh arrays; solver mutation cannot change the device identity."""
        return [np.array(polygon, dtype=float) for polygon in self.obstacles]

    def physical_width(self) -> float:
        if self.width_m is None:
            raise ValueError("This stage requires an explicit physical device width")
        return self.width_m

    @property
    def fingerprint(self) -> str:
        payload = {"schema": "square-four-contact-v2", **asdict(self)}
        return sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


Request = TypeVar("Request", contravariant=True)
Result = TypeVar("Result", covariant=True)


class PhysicsStage(Protocol[Request, Result]):
    """Stages share orchestration, not incompatible physical observables.

    A coupled electrostatic/transport solver implements one stage and owns its
    convergence loop. A request specifies all operating conditions it supports.
    """

    def evaluate(self, device: SquareDevice, request: Request) -> Result: ...
