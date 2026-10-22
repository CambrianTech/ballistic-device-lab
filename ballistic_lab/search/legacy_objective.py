"""Original four-parameter, large-collimation objective."""

import numpy as np

from ballistic_lab.transport.gpu import trace_gpu

BOUNDS = np.array([[0.25, 1.5], [0.25, 1.1], [-0.35, 0.35], [-0.6, 0.6]])


def polygon(x):
    width, height, offset, skew = x
    return [
        np.array(
            [
                [-width / 2, offset + height / 2],
                [width / 2, offset + height / 2],
                [skew * width / 2, offset - height / 2],
            ]
        )
    ]


def sample(rng, n):
    return rng.uniform(BOUNDS[:, 0], BOUNDS[:, 1], (n, 4))


def evaluate(x, n=4096, seed=123):
    """Mean collimation response at specularity 1 and .8; same rays across geometries."""
    x = np.asarray(x)
    all_scores = []
    for start in range(0, len(x), 32):
        polys = [polygon(z) for z in x[start : start + 32]]
        scores = []
        for spec in [1.0, 0.8]:
            conditions = []
            for spread in [1.0, 0.35]:
                p = np.mean(
                    [trace_gpu(polys, k, n, spread, spec, seed + k) for k in (0, 1)],
                    axis=0,
                )
                conditions.append(p[:, 3] - p[:, 2])
            scores.append(conditions[1] - conditions[0])
        all_scores.extend(np.mean(scores, axis=0).tolist())
    return np.array(all_scores)
