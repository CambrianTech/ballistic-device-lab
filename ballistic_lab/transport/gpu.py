"""Double precision CUDA billiards. One independent ray per thread; small batches."""

from pathlib import Path

import cupy as cp
import numpy as np

from ballistic_lab.geometry.basic import segments

cp.get_default_memory_pool().set_limit(size=512 * 1024**2)
SOURCE = Path(__file__).with_name("rays.cu").read_text()

KERNEL = cp.RawKernel(SOURCE, "rays", options=("--std=c++11", "--fmad=false"))


def trace_gpu(polygons, port, n=8192, spread=1.0, specularity=1.0, seed=123, raw=False, mfp=None):
    seg = []
    for poly in polygons:
        a, b = segments(poly)
        seg.append(np.concatenate([a, b], axis=1))
    # Zero-length padding edges cannot intersect a ray (denominator is zero).
    # This permits mixed topologies without adding fictitious reflecting walls.
    max_segments = max(len(s) for s in seg)
    seg = np.stack([np.pad(s, ((0, max_segments - len(s)), (0, 0))) for s in seg]).astype(
        np.float64
    )
    rng = np.random.default_rng(seed)
    u = rng.uniform(-0.3, 0.3, n)
    theta = np.arcsin(rng.uniform(-spread, spread, n))
    count = n * len(polygons)
    dest = cp.empty(count, dtype=cp.int32)
    lengths = cp.empty(count, dtype=cp.float64)
    scatters = cp.empty(count, dtype=cp.int32)
    KERNEL(
        ((count + 127) // 128,),
        (128,),
        (
            cp.asarray(seg),
            np.int32(seg.shape[1]),
            np.int32(len(polygons)),
            cp.asarray(u),
            cp.asarray(theta),
            np.int32(n),
            np.int32(port),
            np.float64(specularity),
            np.uint64(seed),
            np.float64(-1 if mfp is None else mfp),
            dest,
            lengths,
            scatters,
        ),
    )
    d = dest.reshape(len(polygons), n)
    bad = int(cp.sum(d < 0).get())
    if bad:
        codes, counts = np.unique(cp.asnumpy(d[d < 0]), return_counts=True)
        indices = cp.asnumpy(cp.argwhere(d < 0))[:8].tolist()
        bad_lengths = cp.asnumpy(lengths.reshape(len(polygons), n)[d < 0])[:8].tolist()
        raise RuntimeError(
            f"{bad} unresolved rays {dict(zip(codes.tolist(), counts.tolist()))}; "
            f"(geometry, ray)={indices}, lengths={bad_lengths}; no score accepted"
        )
    probabilities = cp.asnumpy(cp.stack([(d == k).mean(axis=1) for k in range(4)], axis=1))
    if raw:
        return (
            probabilities,
            cp.asnumpy(lengths).reshape(len(polygons), n),
            cp.asnumpy(d),
            cp.asnumpy(scatters).reshape(len(polygons), n),
        )
    return probabilities
