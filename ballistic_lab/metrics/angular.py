"""Infinitesimal angular-response estimator, independent of transport backend."""

from collections.abc import Sequence

import numpy as np

from ballistic_lab.models import (
    AngularResponse,
    FloatArray,
    Geometry,
    RayConfig,
    TransportBackend,
)


def angular_weights(seed: int, count: int) -> FloatArray:
    """Score-function derivative at beta=0; shares the injection RNG contract."""
    rng = np.random.default_rng(seed)
    rng.uniform(-0.3, 0.3, count)
    sine = rng.uniform(-1, 1, count)
    return 2 / 3 - 2 * sine * sine


def measure_response(
    geometries: Sequence[Geometry],
    backend: TransportBackend,
    config: RayConfig,
    seed: int,
    batch_size: int = 24,
) -> AngularResponse:
    if config.spread != 1:
        raise ValueError("The beta=0 estimator requires equilibrium angular spread=1")
    if batch_size <= 0:
        raise ValueError("Batch size must be positive")
    scores, tails = [], []
    for start in range(0, len(geometries), batch_size):
        group = geometries[start : start + batch_size]
        port_scores, port_tails = [], []
        for port in (0, 1):
            try:
                result = backend.trace(group, port, config, seed + port)
            except RuntimeError as error:
                raise RuntimeError(
                    f"batch_start={start}, port={port}, seed={seed + port}: {error}"
                ) from error
            sign = (result.destinations == 3).astype(float) - (result.destinations == 2).astype(
                float
            )
            port_scores.append(np.mean(sign * angular_weights(seed + port, config.count), axis=1))
            port_tails.append(np.quantile(result.lengths, 0.99, axis=1) / 2)
        scores.extend(np.mean(port_scores, axis=0))
        tails.extend(np.mean(port_tails, axis=0))
    return AngularResponse(np.asarray(scores), np.asarray(tails))
