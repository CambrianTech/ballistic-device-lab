"""Independent and metamorphic checks required before a topology search."""

import json

import numpy as np

from ballistic_lab.geometry.families import REFERENCE, geometry, sample
from ballistic_lab.metrics.angular import measure_response
from ballistic_lab.models import RayConfig
from ballistic_lab.paths import OUT
from ballistic_lab.transport.backend import CudaBackend
from ballistic_lab.transport.cpu import trace
from ballistic_lab.validation.receipts import model_fingerprint
from ballistic_lab.validation.registry import CHECKS, validation_check


def fixtures() -> list:
    return [
        [],
        geometry("triangle", [1.2, 0.6, 0, 0]),
        geometry("beveled", [1.2, 0.6, 0, 0.1, 0.5, 0.5]),
        geometry("cross", REFERENCE),
    ]


def regression_geometry() -> list:
    return geometry("triangle", sample("triangle", np.random.default_rng(14000), 256)[37])


@validation_check("grazing-reflection regression")
def check_grazing_regression() -> dict:
    backend = CudaBackend()
    result = backend.trace([regression_geometry()], 0, RayConfig(), 15000)
    return dict(
        ray=8034,
        destination=int(result.destinations[0, 8034]),
        path_length=float(result.lengths[0, 8034]),
    )


@validation_check("CPU parity and mixed-topology batching")
def check_cpu_parity() -> dict:
    backend = CudaBackend()
    geometries = fixtures()
    reports = []
    config = RayConfig(count=4096, specularity=1, mean_free_path=None)
    for port in range(4):
        mixed = backend.trace(geometries, port, config, 933)
        for index, polygons in enumerate(geometries):
            cpu = trace(polygons, port, n=config.count, return_dest=True, seed=933)
            single = backend.trace([polygons], port, config, 933)
            np.testing.assert_array_equal(mixed.destinations[index], single.destinations[0])
            np.testing.assert_array_equal(mixed.destinations[index], cpu[3])
            np.testing.assert_allclose(mixed.lengths[index], cpu[1], atol=1e-7)
            reports.append(dict(port=port, geometry=index, mismatches=0))
    return dict(cases=reports)


@validation_check("bulk scattering and reciprocity")
def check_bulk_scattering() -> dict:
    backend = CudaBackend()
    config = RayConfig(count=65536)
    reports = []
    for index, polygons in enumerate(fixtures()):
        cpu = trace(polygons, 0, n=config.count, mfp=2, specularity=0.8, seed=934)[0]
        gpu = backend.trace([polygons], 0, config, 934).probabilities[0]
        error = float(np.max(abs(cpu - gpu)))
        if error >= 0.015:
            raise AssertionError(f"Bulk probability error: {error}")
        matrix = np.array(
            [
                backend.trace([polygons], port, config, 935 + port).probabilities[0]
                for port in range(4)
            ]
        )
        reciprocal = float(np.max(abs(matrix - matrix.T)))
        if reciprocal >= 0.015:
            raise AssertionError(f"Reciprocity error: {reciprocal}")
        reports.append(dict(geometry=index, bulk_cpu_gpu_error=error, reciprocity_error=reciprocal))
    return dict(cases=reports)


@validation_check("mirror symmetry and empty control")
def check_mirror() -> dict:
    polygons = geometry("cross", REFERENCE)
    mirror = [polygon * np.array([1, -1]) for polygon in polygons]
    response = measure_response([polygons, mirror, []], CudaBackend(), RayConfig(count=131072), 980)
    scores = response.derivative
    if abs(scores[0] + scores[1]) >= 0.006 or abs(scores[2]) >= 0.004:
        raise AssertionError(f"Mirror or empty-control failure: {scores}")
    return dict(scores=scores.tolist())


@validation_check("intersection-tolerance convergence")
def check_tolerance() -> dict:
    import cupy as cp

    from ballistic_lab.transport import gpu

    original = gpu.KERNEL
    values = []
    try:
        for epsilon in ["1e-10", "1e-12", "1e-14"]:
            source = gpu.SOURCE.replace("1e-12", epsilon)
            gpu.KERNEL = cp.RawKernel(source, "rays", options=("--std=c++11", "--fmad=false"))
            response = measure_response(
                fixtures() + [regression_geometry()],
                CudaBackend(),
                RayConfig(count=32768),
                15000,
            )
            values.append(response.derivative.tolist())
    finally:
        gpu.KERNEL = original
    if np.max(np.ptp(values, axis=0)) >= 0.001:
        raise AssertionError(f"Intersection tolerance changes scores: {values}")
    return dict(epsilon=["1e-10", "1e-12", "1e-14"], scores=values)


def main() -> None:
    checks = []
    for check in CHECKS:
        details = check.run()
        checks.append(dict(name=check.name, details=details))
        print(f"PASS: {check.name}", flush=True)
    receipt = dict(model_fingerprint=model_fingerprint(), checks=checks)
    (OUT / "families-validation.json").write_text(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
