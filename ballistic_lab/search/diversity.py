"""Geometry niches for search survival; screening scores are not validation."""

import math
from dataclasses import dataclass

import numpy as np
from matplotlib.path import Path


@dataclass(frozen=True, slots=True)
class ShapeDescriptor:
    blocked_fraction: float
    vertical_asymmetry: float

    def niche(self) -> tuple[int, int]:
        """Fixed bins, independent of observed candidates and their scores."""
        return min(9, int(self.blocked_fraction * 10)), min(9, int(self.vertical_asymmetry * 10))


def describe(obstacles: list, resolution: int = 96) -> ShapeDescriptor:
    """Rasterize polygon union in normalized [-1,1] device coordinates.

    Asymmetry is occupied-area mismatch under top/bottom reflection, divided
    by occupied area. It measures geometry, not transport or literature novelty.
    """
    axis = -1 + (np.arange(resolution) + 0.5) * 2 / resolution
    x, y = np.meshgrid(axis, axis)
    points = np.column_stack((x.ravel(), y.ravel()))
    mask = np.zeros(len(points), dtype=bool)
    for polygon in obstacles:
        vertices = np.asarray(polygon)
        mask |= Path(np.vstack((vertices, vertices[0]))).contains_points(points)
    mask = mask.reshape(resolution, resolution)
    union = mask | mask[::-1]
    mismatch = mask ^ mask[::-1]
    return ShapeDescriptor(float(mask.mean()), float(mismatch.sum() / max(1, union.sum())))


def archive(rows: list[dict]) -> list[dict]:
    """Keep highest finite screening DC power in each occupied geometry niche.

    Callers partition by family/repeat before selection. Immutable historic
    records remain the source; this only chooses future mutation parents.
    """
    cells = {}
    for row in rows:
        power = row["levels"][0]["dc_power_w"]
        if not math.isfinite(power) or power < 0:
            continue
        cell = describe(row["candidate"]["obstacles"]).niche()
        incumbent = cells.get(cell)
        rank = (-power, row["candidate"]["key"])
        if incumbent is None or rank < (
            -incumbent["levels"][0]["dc_power_w"],
            incumbent["candidate"]["key"],
        ):
            cells[cell] = row
    return [cells[cell] for cell in sorted(cells)]
