"""Stage compatibility, immutable identity, and uncertainty safeguards."""

import unittest

import numpy as np
from test_contracts import AnalyticBackend

from ballistic_lab.metrics.angular import measure_response
from ballistic_lab.models import RayConfig
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.pipeline.ray import RayRequest, RayStage


class PipelineChecks(unittest.TestCase):
    def test_device_snapshot_and_explicit_scale(self):
        polygon = np.array([[-0.5, 0.5], [0.5, 0.5], [0, -0.5]])
        device = SquareDevice.from_geometry([polygon])
        identity = device.fingerprint
        polygon[:] = 0
        device.geometry()[0][:] = 0
        self.assertEqual(device.fingerprint, identity)
        self.assertEqual(device.obstacles[0][0], (-0.5, 0.5))
        with self.assertRaises(ValueError):
            device.physical_width()
        scaled = SquareDevice(device.obstacles, width_m=100e-9)
        self.assertNotEqual(scaled.fingerprint, identity)
        self.assertEqual(scaled.physical_width(), 100e-9)

    def test_stage_preserves_existing_estimator_exactly(self):
        backend = AnalyticBackend()
        request = RayRequest(RayConfig(count=4096), (100, 200, 300))
        device = SquareDevice(())
        result = RayStage(backend).evaluate(device, request)
        expected = [
            measure_response([[]], backend, request.config, seed).derivative[0]
            for seed in request.seeds
        ]
        np.testing.assert_array_equal(result.angular_response_by_seed, expected)
        self.assertEqual(result.device_fingerprint, device.fingerprint)
        self.assertAlmostEqual(result.standard_error, np.std(expected, ddof=1) / np.sqrt(3))
        self.assertEqual(result.p99_path_over_width_by_seed, (1, 1, 1))

    def test_invalid_requests_fail_before_simulation(self):
        for seeds in ((1,), (1, 1), (1, 2), (-1, 4)):
            with self.assertRaises(ValueError):
                RayRequest(RayConfig(), seeds)
        with self.assertRaises(ValueError):
            RayRequest(RayConfig(spread=0.5), (10, 20))
        for width in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                SquareDevice((), width)

    def test_failure_never_becomes_a_score(self):
        class BrokenBackend:
            def trace(self, *args):
                raise RuntimeError("unresolved trajectory")

        with self.assertRaisesRegex(RuntimeError, "unresolved trajectory"):
            RayStage(BrokenBackend()).evaluate(SquareDevice(()), RayRequest(RayConfig(), (10, 20)))
