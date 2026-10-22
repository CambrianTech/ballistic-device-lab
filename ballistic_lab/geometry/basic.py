"""Polygon boundaries and legacy geometry fixtures."""

import numpy as np


def shapes(kind, width=0.6, height=0.6, offset=0.0):
    if kind == "straight":
        return []
    if kind == "triangle":
        return [
            np.array(
                [
                    [-width / 2, offset + height / 2],
                    [width / 2, offset + height / 2],
                    [0, offset - height / 2],
                ]
            )
        ]
    # Two wall-attached wedges: an asymmetric central constriction.
    return [
        np.array([[-1, 0.95], [-0.25, 0.55], [-1, 0.35]]),
        np.array([[1, 0.95], [0.25, 0.55], [1, 0.35]]),
    ]


def segments(polys):
    outer = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])
    starts = list(outer)
    ends = list(np.roll(outer, -1, axis=0))
    for p in polys:
        starts.extend(p)
        ends.extend(np.roll(p, -1, axis=0))
    return np.array(starts), np.array(ends)


def cross(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
