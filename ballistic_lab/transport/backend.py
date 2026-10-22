"""Typed CUDA adapter; importing contracts does not initialize CUDA."""

from collections.abc import Sequence

from ballistic_lab.models import Geometry, RayConfig, TraceBatch


class CudaBackend:
    def trace(
        self, geometries: Sequence[Geometry], port: int, config: RayConfig, seed: int
    ) -> TraceBatch:
        from ballistic_lab.transport.gpu import trace_gpu

        if port not in range(4):
            raise ValueError("Port must be 0, 1, 2, or 3")
        values = trace_gpu(
            geometries,
            port,
            n=config.count,
            spread=config.spread,
            specularity=config.specularity,
            seed=seed,
            raw=True,
            mfp=config.mean_free_path,
        )
        return TraceBatch(*values)
