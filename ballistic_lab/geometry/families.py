"""Matched-contact families; the cross is an approximation of published topology."""

import numpy as np

from ballistic_lab.geometry.registry import FAMILIES, geometry_family
from ballistic_lab.models import FloatArray, Geometry

TRIANGLE_BOUNDS = ((0.25, 1.5), (0.25, 1.1), (-0.25, 0.25), (-0.6, 0.6))
REFERENCE = np.array([0.18, 0.40, 0.06, -0.18, 0.55, 0.50])


def triangle_vertices(
    parameters: FloatArray,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    width, height, offset, skew = parameters[:4]
    left = np.array([-width / 2, offset + height / 2])
    right = np.array([width / 2, offset + height / 2])
    tip = np.array([skew * width / 2, offset - height / 2])
    return left, right, tip


@geometry_family("triangle", TRIANGLE_BOUNDS)
def triangle(parameters: FloatArray) -> Geometry:
    return [np.array(triangle_vertices(parameters))]


@geometry_family("beveled", TRIANGLE_BOUNDS + ((0.15, 0.85), (0.15, 0.85)))
def beveled(parameters: FloatArray) -> Geometry:
    width, height, offset, _ = parameters[:4]
    level, shoulder = parameters[4:]
    left, right, tip = triangle_vertices(parameters)
    shoulder_y = offset + height / 2 - level * height
    shoulder_left = (1 - shoulder) * (-width / 2) + shoulder * tip[0]
    shoulder_right = (1 - shoulder) * (width / 2) + shoulder * tip[0]
    return [
        np.array(
            [
                left,
                right,
                [shoulder_right, shoulder_y],
                tip,
                [shoulder_left, shoulder_y],
            ]
        )
    ]


@geometry_family(
    "cross",
    (
        (0.10, 0.55),
        (0.25, 0.75),
        (0.02, 0.25),
        (-0.30, -0.02),
        (0.35, 0.8),
        (0.35, 0.8),
    ),
)
def cross_junction(parameters: FloatArray) -> Geometry:
    upper_neck, lower_neck, upper_y, lower_y, top_flare, bottom_flare = parameters
    upper = np.array([[-1, 0.3], [-upper_neck, upper_y], [-top_flare, 0.65], [-0.3, 1], [-1, 1]])
    lower = np.array(
        [
            [-1, -1],
            [-0.3, -1],
            [-bottom_flare, -0.65],
            [-lower_neck, lower_y],
            [-1, -0.3],
        ]
    )
    reflection = np.array([-1, 1])
    return [upper, upper * reflection, lower, lower * reflection]


def geometry(family: str, parameters: FloatArray) -> Geometry:
    return FAMILIES[family].build(parameters)


def sample(family: str, rng: np.random.Generator, count: int) -> FloatArray:
    return FAMILIES[family].sample(rng, count)
